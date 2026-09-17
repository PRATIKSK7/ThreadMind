import json
import os
import hashlib
from collections import defaultdict

def main():
    # Load Golden Set
    golden_set_path = "data/processed/golden_set.jsonl"
    with open(golden_set_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    assert sha == "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f", "Invalid SHA"
    
    gs_dict = {}
    with open(golden_set_path, "r") as f:
        for line in f:
            data = json.loads(line)
            gs_dict[data["thread_id"]] = data

    # Load Results
    results_path = "reports/rag_mnrl_k3_results.json"
    with open(results_path, "r") as f:
        results = json.load(f)
        
    predictions = results["predictions"]
    
    # 1. Confusion Matrix
    confusion = defaultdict(lambda: defaultdict(int))
    intent_stats = defaultdict(lambda: {"total": 0, "correct": 0, "incorrect": 0})
    
    failures = []
    
    for p in predictions:
        expected = p["expected_intent"]
        predicted = p["predicted_intent"]
        
        confusion[expected][predicted] += 1
        intent_stats[expected]["total"] += 1
        
        if p["correctness"]:
            intent_stats[expected]["correct"] += 1
        else:
            intent_stats[expected]["incorrect"] += 1
            
            # Identify primary heuristic category
            retrieved = p["retrieved_intents"]
            if expected not in retrieved:
                cat = "RETRIEVAL_MISSING"
            else:
                # Expected is in retrieved.
                # Are there competing intents?
                if len(set(retrieved)) > 1:
                    cat = "CONFLICTING_EVIDENCE"
                else:
                    cat = "CLASSIFIER_IGNORED_CORRECT"
                    
            gs_item = gs_dict[p["thread_id"]]
            
            failures.append({
                "thread_id": p["thread_id"],
                "expected": expected,
                "predicted": predicted,
                "retrieved_intents": retrieved,
                "expected_rank": retrieved.index(expected) + 1 if expected in retrieved else 999,
                "heuristic_category": cat,
                "conversation": gs_item.get("messages", gs_item.get("conversation", []))
            })
            
    # Calculate Per-Intent Failure Rate
    intent_failure_rates = []
    for intent, stats in intent_stats.items():
        total = stats["total"]
        acc = stats["correct"] / total if total > 0 else 0
        intent_failure_rates.append({
            "intent": intent,
            "total": total,
            "correct": stats["correct"],
            "incorrect": stats["incorrect"],
            "accuracy": acc
        })
        
    intent_failure_rates.sort(key=lambda x: x["accuracy"])
    
    # Dump diagnostic data
    with open("reports/phase13b_diagnostic_dump.json", "w") as f:
        json.dump({
            "confusion": confusion,
            "intent_stats": intent_failure_rates,
            "failures": failures
        }, f, indent=2)
        
    print(f"Dumped {len(failures)} failures.")
    print("Confusion matrix & stats calculated.")

if __name__ == "__main__":
    main()
