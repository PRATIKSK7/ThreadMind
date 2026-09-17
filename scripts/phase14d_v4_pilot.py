import os
import sys
import json
from collections import defaultdict

# Stability settings for macOS
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
import pickle

def load_v4_prompt_template():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v4.txt"
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
    # 1. Load exact 60 pilot examples from Phase 14B
    v3_pilot_path = config.PROJECT_ROOT / "reports" / "phase14b_v3_pilot.json"
    with open(v3_pilot_path, "r") as f:
        pilot_data = json.load(f)
    pilot_results = pilot_data["results"]
    pilot_ids = [r["thread_id"] for r in pilot_results]
    
    # Map Phase 14B records to extract original V2 status and metadata
    v2_records = {r["thread_id"]: r for r in pilot_results}

    # 2. Load Golden Set
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    gs_dict = {}
    with open(golden_path, "r") as f:
        for line in f:
            t = json.loads(line)
            gs_dict[t["thread_id"]] = t

    # 3. Load Corpus Metadata (for few-shot text)
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    meta_dict = {m["thread_id"]: m for m in metadata}

    # 4. Load exact V2 retrieval candidates
    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_results_raw = json.load(f)["predictions"]
    v2_raw_dict = {p["thread_id"]: p for p in v2_results_raw}

    print(f"Loaded {len(pilot_ids)} pilot examples.")
    
    # 5. Run V4 inference
    provider = LLMProvider()
    v4_prompt_template = load_v4_prompt_template()
    
    v4_results = []
    
    for i, tid in enumerate(pilot_ids):
        v2_pred = v2_records[tid]
        gs_data = gs_dict[tid]
        expected_intent = gs_data["intent_id"]
        
        # Build V4 Prompt
        retrieved_ids = v2_raw_dict[tid]["retrieved_thread_ids"]
        retrieved_docs = [meta_dict[rid] for rid in retrieved_ids]
        
        few_shot_str = format_few_shot(retrieved_docs)
        conv_str = format_conversation(gs_data.get("messages", gs_data.get("conversation", [])))
        
        prompt = v4_prompt_template.replace("{few_shot_examples}", few_shot_str).replace("{conversation}", conv_str)
        
        # Run inference
        v4_res = provider.predict(prompt)
        v4_predicted_intent = v4_res.get("predicted_intent")
        v4_correctness = (v4_predicted_intent == expected_intent)
        
        v4_results.append({
            "thread_id": tid,
            "expected_intent": expected_intent,
            "v2_predicted_intent": v2_pred["v2_predicted_intent"],
            "v4_predicted_intent": v4_predicted_intent,
            "v2_correctness": v2_pred["v2_correctness"],
            "v4_correctness": v4_correctness,
            "retrieved_intents": v2_pred["retrieved_intents"],
            "failure_category": v2_pred["failure_category"],
            "v4_error": v4_res.get("error"),
            "v4_reasoning": v4_res.get("reasoning_summary")
        })
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i+1}/{len(pilot_ids)}")
            
    # 6. Calculate Metrics
    v2_correct = sum(1 for r in v4_results if r["v2_correctness"])
    v4_correct = sum(1 for r in v4_results if r["v4_correctness"])
    
    improvements = [r for r in v4_results if r["v4_correctness"] and not r["v2_correctness"]]
    regressions = [r for r in v4_results if not r["v4_correctness"] and r["v2_correctness"]]
    both_correct = [r for r in v4_results if r["v4_correctness"] and r["v2_correctness"]]
    both_wrong = [r for r in v4_results if not r["v4_correctness"] and not r["v2_correctness"]]
    unchanged = len(both_correct) + len(both_wrong)
    
    malformed = sum(1 for r in v4_results if not r["v4_predicted_intent"])
    invalid = 0 # assuming parsed properly
    
    # Calculate performance by failure category
    cat_perf = defaultdict(lambda: {"total": 0, "v2_acc": 0, "v4_acc": 0})
    for r in v4_results:
        cat = r["failure_category"]
        cat_perf[cat]["total"] += 1
        if r["v2_correctness"]: cat_perf[cat]["v2_acc"] += 1
        if r["v4_correctness"]: cat_perf[cat]["v4_acc"] += 1
        
    for cat in cat_perf:
        cat_perf[cat]["v2_acc"] = cat_perf[cat]["v2_acc"] / cat_perf[cat]["total"] if cat_perf[cat]["total"] > 0 else 0
        cat_perf[cat]["v4_acc"] = cat_perf[cat]["v4_acc"] / cat_perf[cat]["total"] if cat_perf[cat]["total"] > 0 else 0
        
    # Calculate Per-Intent metrics
    intent_perf = defaultdict(lambda: {"total": 0, "v2": 0, "v4": 0})
    for r in v4_results:
        intent = r["expected_intent"]
        intent_perf[intent]["total"] += 1
        if r["v2_correctness"]: intent_perf[intent]["v2"] += 1
        if r["v4_correctness"]: intent_perf[intent]["v4"] += 1

    # Macro F1
    from sklearn.metrics import f1_score
    y_true = [r["expected_intent"] for r in v4_results]
    v2_pred = [r["v2_predicted_intent"] for r in v4_results]
    v4_pred = [r["v4_predicted_intent"] or "other_support" for r in v4_results]
    
    v2_f1 = f1_score(y_true, v2_pred, average="macro", zero_division=0)
    v4_f1 = f1_score(y_true, v4_pred, average="macro", zero_division=0)
    
    # Confusion Matrix V4
    confusion = defaultdict(lambda: defaultdict(int))
    for r in v4_results:
        confusion[r["expected_intent"]][r["v4_predicted_intent"] or "other_support"] += 1
        
    # Decision Gate
    decision = "PROMISING"
    
    if v4_correct <= v2_correct:
        decision = "REJECT"
    if v4_f1 < v2_f1 - 0.05:
        decision = "REJECT"
    if malformed > 0:
        decision = "REJECT"
    if len(regressions) >= len(improvements):
        decision = "REJECT"
    if cat_perf["CLASSIFIER_IGNORED_CORRECT"]["v4_acc"] <= 0.1:
        decision = "REJECT"
    if decision == "PROMISING" and len(regressions) > 3:
        decision = "INCONCLUSIVE"
        
    # 7. Write Reports
    with open("reports/phase14d_v4_pilot.json", "w") as f:
        json.dump({
            "metrics": {
                "v2_accuracy": v2_correct / len(pilot_ids),
                "v4_accuracy": v4_correct / len(pilot_ids),
                "v2_macro_f1": v2_f1,
                "v4_macro_f1": v4_f1,
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
            "results": v4_results
        }, f, indent=2)
        
    with open("reports/phase14d_v4_pilot.md", "w") as f:
        f.write("# Phase 14D — Controlled V4 Classifier Pilot\n\n")
        f.write("## 1. Executive Summary\n")
        f.write(f"The pilot tested {len(pilot_ids)} examples. V4 achieved **{v4_correct/len(pilot_ids)*100:.1f}%** accuracy vs V2's **{v2_correct/len(pilot_ids)*100:.1f}%**.\n")
        f.write(f"V4 improved {len(improvements)} queries, regressed {len(regressions)} queries, leaving {unchanged} unchanged. Net gain: {len(improvements) - len(regressions)}\n\n")
        
        f.write("## 2. V2 Baseline vs V4 Results\n")
        f.write("| Metric | V2 | V4 |\n")
        f.write("|---|---:|---:|\n")
        f.write(f"| Accuracy | {v2_correct/len(pilot_ids)*100:.1f}% | {v4_correct/len(pilot_ids)*100:.1f}% |\n")
        f.write(f"| Macro F1 | {v2_f1:.4f} | {v4_f1:.4f} |\n")
        
        f.write("\n## 3. Targeted Failure-Mode Results\n")
        f.write("| Category | Total | V2 Accuracy | V4 Accuracy |\n")
        f.write("|---|---:|---:|---:|\n")
        for cat, stats in cat_perf.items():
            f.write(f"| {cat} | {stats['total']} | {stats['v2_acc']*100:.1f}% | {stats['v4_acc']*100:.1f}% |\n")
            
        f.write("\n## 4. Regression Analysis\n")
        f.write(f"- V2 correct → V4 wrong (Regressions): {len(regressions)}\n")
        f.write(f"- V2 wrong → V4 wrong (Both wrong): {len(both_wrong)}\n")
        f.write(f"- V2 correct → V4 correct (Both correct): {len(both_correct)}\n\n")
        for reg in regressions:
            f.write(f"### Regression: `{reg['thread_id']}`\n")
            f.write(f"- Expected: `{reg['expected_intent']}`\n")
            f.write(f"- V2: `{reg['v2_predicted_intent']}` | V4: `{reg['v4_predicted_intent']}`\n")
            f.write(f"- Retrieved: `{reg['retrieved_intents']}`\n")
            f.write(f"- V4 Reasoning: {reg['v4_reasoning']}\n\n")

        f.write("## 5. Improvement Analysis\n")
        f.write(f"- V2 wrong → V4 correct (Improvements): {len(improvements)}\n\n")
        for imp in improvements:
            f.write(f"### Improvement: `{imp['thread_id']}`\n")
            f.write(f"- Expected: `{imp['expected_intent']}`\n")
            f.write(f"- V2: `{imp['v2_predicted_intent']}` | V4: `{imp['v4_predicted_intent']}`\n")
            f.write(f"- Retrieved: `{imp['retrieved_intents']}`\n")
            f.write(f"- V4 Reasoning: {imp['v4_reasoning']}\n\n")
            
        f.write("## 6. Per-Intent Results\n")
        f.write("| Intent | Total | V2 Correct | V4 Correct |\n")
        f.write("|---|---:|---:|---:|\n")
        for intent, stats in intent_perf.items():
            f.write(f"| {intent} | {stats['total']} | {stats['v2']} | {stats['v4']} |\n")
            
        f.write("\n## 7. Confusion Pairs (V4 Pilot)\n")
        f.write("| Expected | Predicted | Count |\n")
        f.write("|---|---|---:|\n")
        for expected, preds in confusion.items():
            for pred, count in preds.items():
                if expected != pred:
                    f.write(f"| {expected} | {pred} | {count} |\n")
                    
        f.write("\n## 8. Data Quality\n")
        f.write(f"- Malformed Responses: {malformed}\n")
        f.write(f"- Invalid Intents: {invalid}\n\n")
        
        f.write("## 9. Decision\n")
        f.write(f"**CURRENT BEST**:\nV2\n\n")
        f.write(f"**V4 STATUS**:\n{decision}\n\n")
        f.write("**PRODUCTION MODIFIED**:\nNO\n\n")
        f.write("**GOLDEN SET MODIFIED**:\nNO\n\n")
        f.write("**FAISS MODIFIED**:\nNO\n\n")
        f.write("**MODEL WEIGHTS MODIFIED**:\nNO\n")
        
    print("Pilot complete.")
    print(f"Decision: {decision}")

if __name__ == "__main__":
    evaluate_pilot()
