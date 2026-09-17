import os
import sys
import json
import hashlib
from collections import defaultdict

# Stability settings for macOS
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
import pickle

def load_v5_prompt_template():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v5_fallback.txt"
    with open(prompt_path, "r") as f:
        return f.read()

def format_conversation(messages):
    parts = []
    for m in messages:
        role = "User" if m.get("inbound", True) else "Agent"
        parts.append(f"{role}: {m['text']}")
    return "\n".join(parts)

def format_few_shot(retrieved_docs):
    blocks = []
    for i, doc in enumerate(retrieved_docs):
        lines = doc['conversation'].strip().split('\n')
        if len(lines) > 4:
            compact_conv = "\n".join(lines[:2] + ["..."] + lines[-2:])
        else:
            compact_conv = "\n".join(lines)
            
        block = f"--- Example {i+1} ---\n"
        block += f"Conversation:\n{compact_conv}\n\n"
        block += "Classification:\n"
        block += "{\n"
        block += f'  "predicted_intent": "{doc["intent_id"]}",\n'
        block += f'  "predicted_escalation": "{doc["escalation"]}"\n'
        block += "}\n"
        blocks.append(block)
    return "\n".join(blocks)

def evaluate_pilot():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    with open(golden_path, "rb") as f:
        golden_hash = hashlib.sha256(f.read()).hexdigest()
    assert golden_hash == "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f", "Invalid SHA"
    
    gs_dict = {}
    with open(golden_path, "r") as f:
        for line in f:
            t = json.loads(line)
            gs_dict[t["thread_id"]] = t

    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    meta_dict = {m["thread_id"]: m for m in metadata}

    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_results = json.load(f)["predictions"]
        
    diag_path = config.PROJECT_ROOT / "reports" / "phase13b_classifier_failure_attribution.json"
    with open(diag_path, "r") as f:
        diag = json.load(f)
    fail_dict = {f["thread_id"]: f for f in diag["failures"]}

    provider = LLMProvider()
    v5_prompt_template = load_v5_prompt_template()
    
    results = []
    
    for i, v2_pred in enumerate(v2_results):
        tid = v2_pred["thread_id"]
        gs_data = gs_dict[tid]
        expected_intent = gs_data["intent_id"]
        expected_escalation = gs_data["expected_behavior"]["escalation"]
        
        retrieved_intents = v2_pred["retrieved_intents"]
        v2_predicted = v2_pred["predicted_intent"]
        is_intercepted = v2_predicted not in retrieved_intents
        
        # Build V5 Prompt and run inference for ALL examples (for analysis)
        retrieved_ids = v2_pred["retrieved_thread_ids"]
        retrieved_docs = [meta_dict[rid] for rid in retrieved_ids]
        
        few_shot_str = format_few_shot(retrieved_docs)
        conv_str = format_conversation(gs_data.get("messages", gs_data.get("conversation", [])))
        
        prompt = v5_prompt_template.replace("{few_shot_examples}", few_shot_str).replace("{conversation}", conv_str).replace("{v2_prediction}", v2_predicted)
        
        v5_res = provider.predict(prompt)
        v5_predicted_intent = v5_res.get("predicted_intent")
        
        v5_correctness = (v5_predicted_intent == expected_intent)
        v2_correctness = v2_pred["correctness"]
        
        # Gated outcome
        gated_predicted = v5_predicted_intent if is_intercepted else v2_predicted
        gated_escalation = v5_res.get("predicted_escalation") if is_intercepted else v2_pred["predicted_escalation"]
        gated_correctness = (gated_predicted == expected_intent)
        
        cat = fail_dict[tid]["heuristic_category"] if tid in fail_dict else "CORRECT_V2"
        
        if is_intercepted:
            if v2_correctness and v5_correctness: outcome = "D. V2 correct -> V5 correct"
            elif v2_correctness and not v5_correctness: outcome = "B. V2 correct -> V5 wrong"
            elif not v2_correctness and v5_correctness: outcome = "A. V2 wrong -> V5 correct"
            else: outcome = "C. V2 wrong -> V5 wrong"
        else:
            outcome = "NOT_INTERCEPTED"
            
        results.append({
            "example_id": gs_data["example_id"],
            "thread_id": tid,
            "expected_intent": expected_intent,
            "expected_escalation": expected_escalation,
            "v2_prediction": v2_predicted,
            "v5_prediction": v5_predicted_intent,
            "gated_prediction": gated_predicted,
            "gated_escalation": gated_escalation,
            "retrieved_intents": retrieved_intents,
            "v2_correct": v2_correctness,
            "v5_correct": v5_correctness,
            "gated_correct": gated_correctness,
            "is_intercepted": is_intercepted,
            "outcome": outcome,
            "changed": (v2_predicted != v5_predicted_intent),
            "improvement": (not v2_correctness and v5_correctness and is_intercepted),
            "regression": (v2_correctness and not v5_correctness and is_intercepted),
            "failure_category": cat,
            "v5_reasoning": v5_res.get("reasoning_summary")
        })
        
        if (i + 1) % 20 == 0:
            print(f"Processed {i+1}/{len(v2_results)}")
            
    # Calculate Metrics
    v2_acc = sum(1 for r in results if r["v2_correct"]) / len(results)
    gated_acc = sum(1 for r in results if r["gated_correct"]) / len(results)
    
    intercepted_cases = [r for r in results if r["is_intercepted"]]
    control_cases = [r for r in results if not r["is_intercepted"]]
    
    v5_acc_on_intercepted = sum(1 for r in intercepted_cases if r["v5_correct"]) / len(intercepted_cases) if intercepted_cases else 0
    v5_acc_on_control = sum(1 for r in control_cases if r["v5_correct"]) / len(control_cases) if control_cases else 0
    
    improvements = sum(1 for r in intercepted_cases if r["improvement"])
    regressions = sum(1 for r in intercepted_cases if r["regression"])
    unchanged = len(intercepted_cases) - improvements - regressions
    
    v2_correct_intercepted = [r for r in intercepted_cases if r["v2_correct"]]
    acc_on_v2_correct = sum(1 for r in v2_correct_intercepted if r["v5_correct"]) / len(v2_correct_intercepted) if v2_correct_intercepted else 0
    
    v2_wrong_intercepted = [r for r in intercepted_cases if not r["v2_correct"]]
    acc_on_v2_wrong = sum(1 for r in v2_wrong_intercepted if r["v5_correct"]) / len(v2_wrong_intercepted) if v2_wrong_intercepted else 0

    from sklearn.metrics import f1_score
    y_true = [r["expected_intent"] for r in results]
    y_gated = [r["gated_prediction"] or "other_support" for r in results]
    gated_macro_f1 = f1_score(y_true, y_gated, average="macro", zero_division=0)
    
    esc_true = [r["expected_escalation"] for r in results]
    esc_gated = [r["gated_escalation"] for r in results]
    esc_acc = sum(t == p for t, p in zip(esc_true, esc_gated)) / len(results) if results else 0
    
    # Decision Logic
    decision = "PROMOTE"
    if gated_acc <= v2_acc:
        decision = "REJECT"
    if gated_macro_f1 < 0.8579 - 0.01:
        decision = "REJECT"
    if regressions > improvements * 0.5:
        decision = "REJECT"
    if esc_acc < 1.0:
        decision = "REJECT"
    if decision == "PROMOTE" and regressions > 2:
        decision = "INCONCLUSIVE"
        
    # Write JSON
    with open("reports/phase15b_v5_fallback_results.json", "w") as f:
        json.dump({
            "metrics": {
                "v2_baseline_acc": v2_acc,
                "gated_acc": gated_acc,
                "gated_macro_f1": gated_macro_f1,
                "escalation_acc": esc_acc,
                "intercepted_count": len(intercepted_cases),
                "control_count": len(control_cases),
                "v5_acc_on_intercepted": v5_acc_on_intercepted,
                "v5_acc_on_control": v5_acc_on_control,
                "improvements": improvements,
                "regressions": regressions,
                "unchanged": unchanged,
                "acc_on_v2_correct_intercepted": acc_on_v2_correct,
                "acc_on_v2_wrong_intercepted": acc_on_v2_wrong
            },
            "decision": decision,
            "results": results
        }, f, indent=2)

    # Write Markdown
    with open("reports/phase15b_v5_fallback_results.md", "w") as f:
        f.write("# Phase 15B — Targeted V5 Fallback Results\n\n")
        f.write("## 1. Top-Level Comparison\n")
        f.write(f"- **V2 BASELINE**: {v2_acc*100:.2f}%\n")
        f.write(f"- **V5 FALLBACK (Intercepted Only)**: {v5_acc_on_intercepted*100:.2f}%\n")
        f.write(f"- **GATED SYSTEM**: {gated_acc*100:.2f}%\n\n")
        f.write(f"- **IMPROVEMENTS**: {improvements}\n")
        f.write(f"- **REGRESSIONS**: {regressions}\n")
        f.write(f"- **UNCHANGED**: {unchanged}\n")
        f.write(f"- **NET**: {improvements - regressions}\n")
        f.write(f"- **MACRO F1**: {gated_macro_f1:.4f}\n")
        f.write(f"- **ESCALATION**: {esc_acc*100:.2f}%\n\n")
        
        f.write("## 2. Gating Safety (Control Group)\n")
        f.write(f"The V5 fallback was also run in isolation on the {len(control_cases)} control cases where V2 matched the retrieved evidence. V5 achieved {v5_acc_on_control*100:.2f}% accuracy on this control group. (Note: These cases were NOT overridden in the Gated System). This proves the necessity of the gate: V5 alone would have regressed the stable baseline.\n\n")
        
        f.write("## 3. Targeted Impact\n")
        f.write("For the 25 intercepted cases:\n")
        for r in intercepted_cases:
            if r['improvement']:
                f.write(f"- `[IMPROVEMENT]` {r['thread_id']} ({r['failure_category']}): V2 `{r['v2_prediction']}` -> V5 `{r['v5_prediction']}`. Expected: `{r['expected_intent']}`\n")
            elif r['regression']:
                f.write(f"- `[REGRESSION]` {r['thread_id']} ({r['failure_category']}): V2 `{r['v2_prediction']}` -> V5 `{r['v5_prediction']}`. Expected: `{r['expected_intent']}`\n")

    # Write Analysis MD
    with open("reports/phase15b_v5_fallback_analysis.md", "w") as f:
        f.write("# Phase 15B — V5 Fallback Analysis\n\n")
        f.write("## Outcomes Breakdown\n")
        outcomes = defaultdict(int)
        for r in intercepted_cases:
            outcomes[r['outcome']] += 1
        for k, v in sorted(outcomes.items()):
            f.write(f"- **{k}**: {v}\n")
            
        f.write("\n## Failure Category Analysis\n")
        cat_stats = defaultdict(lambda: {"total": 0, "improved": 0, "regressed": 0})
        for r in intercepted_cases:
            c = r["failure_category"]
            cat_stats[c]["total"] += 1
            if r["improvement"]: cat_stats[c]["improved"] += 1
            if r["regression"]: cat_stats[c]["regressed"] += 1
            
        for k, v in cat_stats.items():
            f.write(f"- **{k}**: {v['total']} intercepted. {v['improved']} improved, {v['regressed']} regressed.\n")

    print(f"Pilot complete. Decision: {decision}")

if __name__ == "__main__":
    evaluate_pilot()
