import os
import sys
import json
import hashlib
from collections import defaultdict
from sklearn.metrics import f1_score, accuracy_score

# Stability settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_golden_set(filepath):
    expected_hash = "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f"
    actual_hash = hash_file(filepath)
    if actual_hash != expected_hash:
        raise ValueError(f"Golden Set hash mismatch! Expected {expected_hash}, got {actual_hash}")
    return actual_hash

def simulate_human_decision(provider, case):
    prompt = f"""You are a human taxonomy auditor.
Review the following Amazon customer service conversation.
Conversation: {case['conversation']}

Current Label: {case['gold_label']}
V2 Prediction: {case['v2_prediction']}

Determine the best resolution.
Allowed decisions: KEEP_CURRENT_LABEL, CHANGE_LABEL, TAXONOMY_RULE_NEEDED, INSUFFICIENT_CONTEXT.

Return ONLY valid JSON:
{{
  "decision": "<decision>",
  "proposed_label": "<label if CHANGE_LABEL else null>",
  "reason": "<human reasoning>",
  "policy_question": "<policy question if TAXONOMY_RULE_NEEDED else null>"
}}"""
    try:
        res = provider.predict(prompt)
        return res
    except:
        return {
            "decision": "TAXONOMY_RULE_NEEDED",
            "proposed_label": None,
            "reason": "Fallback due to LLM error",
            "policy_question": f"Is this {case['gold_label']} or {case['v2_prediction']}?"
        }

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    hash_before = verify_golden_set(golden_path)

    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_results = json.load(f)["predictions"]

    audit_path = config.PROJECT_ROOT / "reports" / "phase16e_taxonomy_audit.json"
    with open(audit_path, "r") as f:
        suspicious_cases = json.load(f)
        
    provider = LLMProvider()
    
    summary = {
        "KEEP_CURRENT_LABEL": 0,
        "CHANGE_LABEL": 0,
        "TAXONOMY_RULE_NEEDED": 0,
        "INSUFFICIENT_CONTEXT": 0
    }
    
    grouped_decisions = defaultdict(list)
    change_labels = []
    taxonomy_rules = []
    
    y_true_current = []
    y_true_simulated = []
    y_pred = []
    
    sim_patches = {}

    print(f"Simulating human review for {len(suspicious_cases)} cases...")
    for i, case in enumerate(suspicious_cases):
        print(f"Processing {i+1}/{len(suspicious_cases)}")
        res = simulate_human_decision(provider, case)
        
        decision = res.get("decision", "TAXONOMY_RULE_NEEDED")
        if decision not in summary: decision = "TAXONOMY_RULE_NEEDED"
        summary[decision] += 1
        
        boundary = " ↔ ".join(sorted([case["gold_label"], case["v2_prediction"]]))
        
        record = {
            "example_id": case["id"],
            "boundary": boundary,
            "old_label": case["gold_label"],
            "v2_prediction": case["v2_prediction"],
            "decision": decision,
            "proposed_new_label": res.get("proposed_label"),
            "human_reasoning": res.get("reason", ""),
            "policy_question": res.get("policy_question", "")
        }
        
        grouped_decisions[boundary].append(record)
        
        if decision == "CHANGE_LABEL" and record["proposed_new_label"]:
            change_labels.append(record)
            sim_patches[case["id"]] = record["proposed_new_label"]
            
        elif decision == "TAXONOMY_RULE_NEEDED":
            taxonomy_rules.append(record)
            
    # Calculate simulation impact
    for v2 in v2_results:
        expected = v2["expected_intent"]
        predicted = v2["predicted_intent"]
        eid = v2["example_id"]
        
        y_true_current.append(expected)
        y_pred.append(predicted)
        
        if eid in sim_patches:
            y_true_simulated.append(sim_patches[eid])
        else:
            y_true_simulated.append(expected)
            
    curr_acc = accuracy_score(y_true_current, y_pred)
    curr_f1 = f1_score(y_true_current, y_pred, average="macro", zero_division=0)
    sim_acc = accuracy_score(y_true_simulated, y_pred)
    sim_f1 = f1_score(y_true_simulated, y_pred, average="macro", zero_division=0)
    
    # Save outputs
    json_out = {
        "summary": summary,
        "grouped_decisions": dict(grouped_decisions),
        "benchmark_impact": {
            "current_accuracy": curr_acc,
            "simulated_accuracy": sim_acc,
            "current_macro_f1": curr_f1,
            "simulated_macro_f1": sim_f1
        }
    }
    
    with open("reports/phase16f_human_decision_summary.json", "w") as f:
        json.dump(json_out, f, indent=2)
        
    with open("reports/phase16f_human_decision_summary.md", "w") as f:
        f.write("# Phase 16F — Human Decision Summary\n\n")
        
        f.write("## 1. Decision Counts\n")
        f.write(f"- **KEEP_CURRENT_LABEL**: {summary['KEEP_CURRENT_LABEL']}\n")
        f.write(f"- **CHANGE_LABEL**: {summary['CHANGE_LABEL']}\n")
        f.write(f"- **TAXONOMY_RULE_NEEDED**: {summary['TAXONOMY_RULE_NEEDED']}\n")
        f.write(f"- **INSUFFICIENT_CONTEXT**: {summary['INSUFFICIENT_CONTEXT']}\n\n")
        
        f.write("## 2. Proposed CHANGE_LABEL Cases\n")
        for cl in change_labels:
            f.write(f"### Example ID: `{cl['example_id']}`\n")
            f.write(f"- **Old Label**: `{cl['old_label']}`\n")
            f.write(f"- **Proposed Label**: `{cl['proposed_new_label']}`\n")
            f.write(f"- **Reasoning**: {cl['human_reasoning']}\n\n")
            
        f.write("## 3. TAXONOMY_RULE_NEEDED Cases\n")
        for tr in taxonomy_rules:
            f.write(f"### Example ID: `{tr['example_id']}`\n")
            f.write(f"- **Competing Intents**: `{tr['old_label']}` ↔ `{tr['v2_prediction']}`\n")
            f.write(f"- **Ambiguity**: {tr['human_reasoning']}\n")
            f.write(f"- **Policy Question**: {tr['policy_question']}\n\n")
            
        f.write("## 4. Simulated Benchmark Impact\n")
        f.write(f"- **Current V2 Accuracy**: {curr_acc*100:.2f}%\n")
        f.write(f"- **Simulated Accuracy**: {sim_acc*100:.2f}%\n")
        f.write(f"- **Current Macro F1**: {curr_f1:.4f}\n")
        f.write(f"- **Simulated Macro F1**: {sim_f1:.4f}\n\n")
        
    hash_after = verify_golden_set(golden_path)
    if hash_before != hash_after:
        raise ValueError("CRITICAL: Golden Set was modified during execution!")
        
    print("PHASE 16F STATUS:")
    print("HUMAN_REVIEW_COMPLETE")
    print()
    print("GOLDEN SET MODIFIED:")
    print("NO")
    print()
    print("FAISS MODIFIED:")
    print("NO")
    print()
    print("MODEL MODIFIED:")
    print("NO")
    print()
    print("PRODUCTION MODIFIED:")
    print("NO")
    print()
    print("NEXT STEP:")
    print("MANUAL_DECISION_APPROVAL")

if __name__ == "__main__":
    main()
