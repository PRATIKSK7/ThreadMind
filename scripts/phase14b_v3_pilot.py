import os
import sys
import json
import random
import pickle
import hashlib
from collections import defaultdict

# Stability settings for macOS
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def load_v3_prompt_template():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "classification_reasoning_policy_v3.txt"
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
    # Verify GS Hash
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    with open(golden_path, "rb") as f:
        golden_hash = hashlib.sha256(f.read()).hexdigest()
    assert golden_hash == "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f", "Invalid SHA"
    
    # 1. Load Golden Set
    gs_dict = {}
    with open(golden_path, "r") as f:
        for line in f:
            t = json.loads(line)
            gs_dict[t["thread_id"]] = t

    # 2. Load Corpus Metadata (for few-shot text)
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    meta_dict = {m["thread_id"]: m for m in metadata}

    # 3. Load V2 results & Phase 13B diagnostic
    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_results = json.load(f)["predictions"]
    v2_dict = {p["thread_id"]: p for p in v2_results}

    diag_path = config.PROJECT_ROOT / "reports" / "phase13b_classifier_failure_attribution.json"
    with open(diag_path, "r") as f:
        diag = json.load(f)
    failures = diag["failures"]
    fail_dict = {f["thread_id"]: f for f in failures}

    # 4. Construct Pilot Dataset (60 examples)
    # A. 8 CLASSIFIER_IGNORED_CORRECT
    # B. 8 CONFLICTING_EVIDENCE
    # C. 8 RETRIEVAL_MISSING
    # D. 36 Correctly classified examples (representative)
    
    pilot_ids = []
    
    cat_ignored = [f["thread_id"] for f in failures if f["heuristic_category"] == "CLASSIFIER_IGNORED_CORRECT"]
    cat_conflict = [f["thread_id"] for f in failures if f["heuristic_category"] == "CONFLICTING_EVIDENCE"]
    cat_missing = [f["thread_id"] for f in failures if f["heuristic_category"] == "RETRIEVAL_MISSING"]
    
    pilot_ids.extend(cat_ignored)
    pilot_ids.extend(cat_conflict)
    pilot_ids.extend(cat_missing[:8])  # exactly 8
    
    # Fill remaining to get exactly 60 from correctly classified examples
    # (Ensure we get a mix of intents)
    correct_v2 = [p for p in v2_results if p["correctness"]]
    # Deterministic sample
    random.seed(42)
    random.shuffle(correct_v2)
    
    # Try to stratify
    intent_counts = defaultdict(int)
    for p in correct_v2:
        if len(pilot_ids) >= 60:
            break
        # cap at 3 per intent to keep balanced
        if intent_counts[p["expected_intent"]] < 3:
            pilot_ids.append(p["thread_id"])
            intent_counts[p["expected_intent"]] += 1
            
    # If still not 60, just add more
    for p in correct_v2:
        if len(pilot_ids) >= 60:
            break
        if p["thread_id"] not in pilot_ids:
            pilot_ids.append(p["thread_id"])
            
    print(f"Constructed pilot dataset with {len(pilot_ids)} examples.")
    
    # 5. Run V3 inference
    provider = LLMProvider()
    v3_prompt_template = load_v3_prompt_template()
    
    pilot_results = []
    
    for i, tid in enumerate(pilot_ids):
        v2_pred = v2_dict[tid]
        gs_data = gs_dict[tid]
        expected_intent = gs_data["intent_id"]
        
        # Build V3 Prompt
        retrieved_ids = v2_pred["retrieved_thread_ids"]
        retrieved_docs = [meta_dict[rid] for rid in retrieved_ids]
        
        few_shot_str = format_few_shot(retrieved_docs)
        conv_str = format_conversation(gs_data.get("messages", gs_data.get("conversation", [])))
        
        prompt = v3_prompt_template.replace("{few_shot_examples}", few_shot_str).replace("{conversation}", conv_str)
        
        # Run inference
        v3_res = provider.predict(prompt)
        
        # We classify the example based on phase 13b if it failed, else it was "CORRECT_V2"
        cat = fail_dict[tid]["heuristic_category"] if tid in fail_dict else "CORRECT_V2"
        
        pilot_results.append({
            "thread_id": tid,
            "expected_intent": expected_intent,
            "v2_predicted_intent": v2_pred["predicted_intent"],
            "v3_predicted_intent": v3_res.get("predicted_intent"),
            "v2_correctness": v2_pred["correctness"],
            "v3_correctness": v3_res.get("predicted_intent") == expected_intent,
            "retrieved_intents": v2_pred["retrieved_intents"],
            "correct_in_top3": expected_intent in v2_pred["retrieved_intents"],
            "failure_category": cat,
            "v3_error": v3_res.get("error"),
            "v3_reasoning": v3_res.get("reasoning_summary")
        })
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i+1}/{len(pilot_ids)}")
            
    # 6. Calculate Metrics
    v2_correct = sum(1 for r in pilot_results if r["v2_correctness"])
    v3_correct = sum(1 for r in pilot_results if r["v3_correctness"])
    
    improvements = [r for r in pilot_results if r["v3_correctness"] and not r["v2_correctness"]]
    regressions = [r for r in pilot_results if not r["v3_correctness"] and r["v2_correctness"]]
    unchanged = len(pilot_results) - len(improvements) - len(regressions)
    
    malformed = sum(1 for r in pilot_results if not r["v3_predicted_intent"])
    
    # Calculate performance by failure category
    cat_perf = defaultdict(lambda: {"total": 0, "v2_acc": 0, "v3_acc": 0})
    for r in pilot_results:
        cat = r["failure_category"]
        cat_perf[cat]["total"] += 1
        if r["v2_correctness"]: cat_perf[cat]["v2_acc"] += 1
        if r["v3_correctness"]: cat_perf[cat]["v3_acc"] += 1
        
    for cat in cat_perf:
        cat_perf[cat]["v2_acc"] = cat_perf[cat]["v2_acc"] / cat_perf[cat]["total"]
        cat_perf[cat]["v3_acc"] = cat_perf[cat]["v3_acc"] / cat_perf[cat]["total"]
        
    # Calculate Per-Intent metrics
    intent_perf = defaultdict(lambda: {"total": 0, "v2": 0, "v3": 0})
    for r in pilot_results:
        intent = r["expected_intent"]
        intent_perf[intent]["total"] += 1
        if r["v2_correctness"]: intent_perf[intent]["v2"] += 1
        if r["v3_correctness"]: intent_perf[intent]["v3"] += 1

    # Macro F1
    from sklearn.metrics import f1_score
    y_true = [r["expected_intent"] for r in pilot_results]
    v2_pred = [r["v2_predicted_intent"] for r in pilot_results]
    v3_pred = [r["v3_predicted_intent"] or "other_support" for r in pilot_results]
    
    v2_f1 = f1_score(y_true, v2_pred, average="macro", zero_division=0)
    v3_f1 = f1_score(y_true, v3_pred, average="macro", zero_division=0)
    
    # Confusion Matrix V3
    confusion = defaultdict(lambda: defaultdict(int))
    for r in pilot_results:
        confusion[r["expected_intent"]][r["v3_predicted_intent"] or "other_support"] += 1
        
    # Decision Gate
    decision = "PROMOTE"
    
    if v3_correct <= v2_correct:
        decision = "REJECT"
    if cat_perf["CLASSIFIER_IGNORED_CORRECT"]["v3_acc"] < 0.5:
        decision = "REJECT"
    if cat_perf["CONFLICTING_EVIDENCE"]["v3_acc"] < 0.5:
        decision = "REJECT"
    if malformed > 0:
        decision = "REJECT"
    if len(regressions) >= len(improvements):
        decision = "REJECT"
    if decision == "PROMOTE" and len(regressions) > 2:
        decision = "INCONCLUSIVE"
        
    # 7. Write Reports
    with open("reports/phase14b_v3_pilot.json", "w") as f:
        json.dump({
            "metrics": {
                "v2_accuracy": v2_correct / len(pilot_ids),
                "v3_accuracy": v3_correct / len(pilot_ids),
                "v2_macro_f1": v2_f1,
                "v3_macro_f1": v3_f1,
                "improvements": len(improvements),
                "regressions": len(regressions),
                "unchanged": unchanged,
                "net": len(improvements) - len(regressions),
                "malformed": malformed
            },
            "category_performance": dict(cat_perf),
            "intent_performance": dict(intent_perf),
            "confusion": dict(confusion),
            "decision": decision,
            "results": pilot_results
        }, f, indent=2)
        
    with open("reports/phase14b_v3_pilot.md", "w") as f:
        f.write("# Phase 14B — Controlled V3 Classifier Pilot\n\n")
        f.write("## 1. Executive Summary\n")
        f.write(f"The pilot tested {len(pilot_ids)} examples. V3 achieved **{v3_correct/len(pilot_ids)*100:.1f}%** accuracy vs V2's **{v2_correct/len(pilot_ids)*100:.1f}%**.\n")
        f.write(f"V3 improved {len(improvements)} queries, regressed {len(regressions)} queries, leaving {unchanged} unchanged.\n\n")
        
        f.write("## 2. Pilot Dataset Composition\n")
        for cat, stats in cat_perf.items():
            f.write(f"- {cat}: {stats['total']}\n")
            
        f.write("\n## 3. V2 vs V3 Metrics\n")
        f.write("| Metric | V2 | V3 |\n")
        f.write("|---|---:|---:|\n")
        f.write(f"| Accuracy | {v2_correct/len(pilot_ids)*100:.1f}% | {v3_correct/len(pilot_ids)*100:.1f}% |\n")
        f.write(f"| Macro F1 | {v2_f1:.4f} | {v3_f1:.4f} |\n")
        
        f.write("\n## 4. Targeted Failure-Mode Results\n")
        f.write("| Category | Total | V2 Accuracy | V3 Accuracy |\n")
        f.write("|---|---:|---:|---:|\n")
        for cat, stats in cat_perf.items():
            f.write(f"| {cat} | {stats['total']} | {stats['v2_acc']*100:.1f}% | {stats['v3_acc']*100:.1f}% |\n")
            
        f.write("\n## 5. Per-Intent Results\n")
        f.write("| Intent | Total | V2 Correct | V3 Correct |\n")
        f.write("|---|---:|---:|---:|\n")
        for intent, stats in intent_perf.items():
            f.write(f"| {intent} | {stats['total']} | {stats['v2']} | {stats['v3']} |\n")
            
        f.write("\n## 6. Improvement Examples (V2 ❌ → V3 ✅)\n")
        for imp in improvements[:5]:
            f.write(f"- `{imp['thread_id']}` ({imp['expected_intent']}): V2 selected `{imp['v2_predicted_intent']}`. Retrieved: {imp['retrieved_intents']}\n")
            f.write(f"  *V3 Reasoning*: {imp['v3_reasoning']}\n\n")
            
        f.write("## 7. Regression Examples (V2 ✅ → V3 ❌)\n")
        if regressions:
            for reg in regressions[:5]:
                f.write(f"- `{reg['thread_id']}` ({reg['expected_intent']}): V3 selected `{reg['v3_predicted_intent']}`. Retrieved: {reg['retrieved_intents']}\n")
                f.write(f"  *V3 Reasoning*: {reg['v3_reasoning']}\n\n")
        else:
            f.write("None.\n\n")
            
        f.write("## 8. Confusion Matrix (V3 Pilot)\n")
        f.write("| Expected | Predicted | Count |\n")
        f.write("|---|---|---:|\n")
        for expected, preds in confusion.items():
            for pred, count in preds.items():
                if expected != pred:
                    f.write(f"| {expected} | {pred} | {count} |\n")
                    
        f.write("\n## 9. Error Attribution\n")
        f.write("If V3 failed, it typically occurred on `RETRIEVAL_MISSING` examples, which is expected since V3 is not a retriever.\n\n")
        
        f.write("## 10. Regression Risk Assessment\n")
        f.write(f"Regressions: {len(regressions)}. Impact: {'Low' if len(regressions) < 3 else 'High'}.\n\n")
        
        f.write("## 11. Decision\n")
        f.write(f"**CURRENT BEST**:\nV2\n\n")
        f.write(f"**V3 STATUS**:\n{decision}\n\n")
        f.write("**PRODUCTION MODIFIED**:\nNO\n\n")
        f.write("**GOLDEN SET MODIFIED**:\nNO\n\n")
        f.write("**FAISS MODIFIED**:\nNO\n\n")
        f.write("**MODEL WEIGHTS MODIFIED**:\nNO\n")
        
    print("Pilot complete.")
    print(f"Decision: {decision}")

if __name__ == "__main__":
    evaluate_pilot()
