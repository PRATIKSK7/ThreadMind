import json
def run():
    with open("reports/phase1_error_attribution.json", "r") as f:
        data = json.load(f)
        
    pairs = data["confusion_pairs"]
    
    golden = {}
    with open("data/processed/golden_set.jsonl", "r") as f:
        for line in f:
            t = json.loads(line)
            golden[t["thread_id"]] = t
            
    with open("reports/rag_mnrl_k5_results.json", "r") as f:
        res = json.load(f)
        
    for p in pairs:
        pair_set = set(p["pair"])
        print(f"\n=== Pair: {p['pair']} ({p['count']}) ===")
        found = 0
        for pred in res["predictions"]:
            if not pred["correctness"]:
                if set([pred["expected_intent"], pred["predicted_intent"]]) == pair_set:
                    t = golden[pred["thread_id"]]
                    text = "\n".join([m["text"] for m in t["conversation"]])
                    print(f"GT: {pred['expected_intent']} | Pred: {pred['predicted_intent']}")
                    print(f"Text:\n{text}")
                    print("-" * 40)
                    found += 1
                    if found >= 2:
                        break

if __name__ == "__main__":
    run()
