import json
import os

def get_text(example):
    if "conversation" in example:
        return " ".join([m["text"] for m in example["conversation"]]).lower()
    if "messages" in example:
        return " ".join([m["text"] for m in example["messages"]]).lower()
    return ""

def audit_golden_set():
    with open("data/processed/golden_set.jsonl", "r") as f:
        data = [json.loads(line) for line in f]
        
    with open("reports/phase1_error_attribution.json", "r") as f:
        k5_failures = json.load(f)["error_attribution"]
        
    failed_map = {ex["example_id"]: ex for ex in k5_failures}
    
    flags = []
    
    counts = {
        "CLEAR_MISLABEL": 0,
        "TAXONOMY_AMBIGUITY": 0,
        "MODEL_ERROR": 0
    }
    intent_counts = {}
    pair_counts = {
        "account_access_vs_delivery_wrong_item": 0,
        "amazon_locker_vs_delivery_missing": 0,
        "delivery_delayed_vs_returns_refunds": 0
    }
    
    for ex in data:
        ex_id = ex["example_id"]
        assigned = ex["intent_id"]
        text = get_text(ex)
        
        flag = None
        
        # 1. account_access vs delivery_wrong_item
        if assigned == "delivery_wrong_item" and any(k in text for k in ["password", "login", "app", "account locked"]):
            flag = {
                "example_id": ex_id,
                "assigned_intent": assigned,
                "suspected_intent": "account_access",
                "confidence": "high",
                "reason": "Customer mentions digital access keywords, not physical wrong items.",
                "evidence": "password/login mentioned",
                "source": "deterministic_rule",
                "category": "CLEAR_MISLABEL"
            }
            pair_counts["account_access_vs_delivery_wrong_item"] += 1
            
        elif assigned == "account_access" and any(k in text for k in ["wrong item", "instead of", "received"]):
            if "app" in text or "login" in text:
                flag = {
                    "example_id": ex_id,
                    "assigned_intent": assigned,
                    "suspected_intent": "delivery_wrong_item",
                    "confidence": "medium",
                    "reason": "Customer mentions wrong item but also digital access.",
                    "evidence": "wrong item + login mentioned",
                    "source": "deterministic_rule",
                    "category": "TAXONOMY_AMBIGUITY"
                }
            else:
                flag = {
                    "example_id": ex_id,
                    "assigned_intent": assigned,
                    "suspected_intent": "delivery_wrong_item",
                    "confidence": "high",
                    "reason": "Customer mentions wrong physical item, not digital access.",
                    "evidence": "wrong item mentioned without login",
                    "source": "deterministic_rule",
                    "category": "CLEAR_MISLABEL"
                }
            pair_counts["account_access_vs_delivery_wrong_item"] += 1

        # 2. amazon_locker vs delivery_missing
        elif assigned == "amazon_locker" and any(k in text for k in ["empty", "missing", "not inside"]):
            flag = {
                "example_id": ex_id,
                "assigned_intent": assigned,
                "suspected_intent": "delivery_missing",
                "confidence": "high",
                "reason": "Locker was accessed but contents missing.",
                "evidence": "empty locker",
                "source": "deterministic_rule",
                "category": "CLEAR_MISLABEL"
            }
            pair_counts["amazon_locker_vs_delivery_missing"] += 1
            
        elif assigned == "delivery_missing" and any(k in text for k in ["code", "won't open", "screen"]):
            flag = {
                "example_id": ex_id,
                "assigned_intent": assigned,
                "suspected_intent": "amazon_locker",
                "confidence": "medium",
                "reason": "Issue is accessing the locker, not necessarily missing package.",
                "evidence": "locker access failure",
                "source": "deterministic_rule",
                "category": "TAXONOMY_AMBIGUITY"
            }
            pair_counts["amazon_locker_vs_delivery_missing"] += 1

        # 3. delivery_delayed vs returns_refunds
        elif assigned == "delivery_delayed" and any(k in text for k in ["refund", "return", "money back"]):
            flag = {
                "example_id": ex_id,
                "assigned_intent": assigned,
                "suspected_intent": "returns_refunds",
                "confidence": "high",
                "reason": "Customer is waiting for money, not a package.",
                "evidence": "refund mentioned",
                "source": "deterministic_rule",
                "category": "CLEAR_MISLABEL"
            }
            pair_counts["delivery_delayed_vs_returns_refunds"] += 1
            
        elif assigned == "returns_refunds" and any(k in text for k in ["arriving", "shipped", "tracking"]):
            if "refund" not in text and "return" not in text:
                flag = {
                    "example_id": ex_id,
                    "assigned_intent": assigned,
                    "suspected_intent": "delivery_delayed",
                    "confidence": "high",
                    "reason": "Customer is tracking an outbound package, not a return.",
                    "evidence": "tracking mentioned without return",
                    "source": "deterministic_rule",
                    "category": "CLEAR_MISLABEL"
                }
                pair_counts["delivery_delayed_vs_returns_refunds"] += 1

        # 4. Check for genuine model errors
        if ex_id in failed_map and not flag:
            failure_info = failed_map[ex_id]
            flag = {
                "example_id": ex_id,
                "assigned_intent": assigned,
                "suspected_intent": None,
                "confidence": "high",
                "reason": "Assigned label appears correct based on rules, so this is a genuine model failure.",
                "evidence": f"Failed prediction but no deterministic mislabel flag. Bottleneck: {failure_info.get('bottleneck')}",
                "source": "deterministic_rule",
                "category": "MODEL_ERROR"
            }

        if flag:
            counts[flag["category"]] += 1
            if flag["category"] != "MODEL_ERROR":
                intent_counts[assigned] = intent_counts.get(assigned, 0) + 1
            flags.append(flag)
            
    with open("reports/golden_set_deterministic_flags.json", "w") as f:
        json.dump(flags, f, indent=2)

    total = len(data)
    num_flagged = counts["CLEAR_MISLABEL"] + counts["TAXONOMY_AMBIGUITY"]
    
    k5_flagged = len([f for f in flags if f["example_id"] in failed_map and f["category"] in ["CLEAR_MISLABEL", "TAXONOMY_AMBIGUITY"]])
    genuine_classification = 0
    genuine_retrieval = 0
    
    for f in flags:
        if f["category"] == "MODEL_ERROR" and f["example_id"] in failed_map:
            if failed_map[f["example_id"]].get("primary_failure") == "LLM classification":
                genuine_classification += 1
            else:
                genuine_retrieval += 1
    
    with open("reports/golden_set_deterministic_summary.md", "w") as f:
        f.write("# Golden Set Deterministic Summary\n\n")
        f.write(f"- Total Golden Set examples: {total}\n")
        f.write(f"- Number flagged: {num_flagged}\n")
        f.write(f"- CLEAR_MISLABEL count: {counts['CLEAR_MISLABEL']}\n")
        f.write(f"- TAXONOMY_AMBIGUITY count: {counts['TAXONOMY_AMBIGUITY']}\n")
        f.write(f"- MODEL_ERROR count: {counts['MODEL_ERROR']}\n")
        f.write(f"- Percentage of Golden Set affected: {(num_flagged / total) * 100:.1f}%\n\n")
        
        f.write("## Count by Intent (Flagged)\n")
        for k, v in intent_counts.items():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n## Count by Confusion Pair\n")
        for k, v in pair_counts.items():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n## K=5 Failure Impact\n")
        f.write(f"- K=5 failures involving a flagged Golden Set example: {k5_flagged}\n")
        f.write(f"- K=5 failures remain genuine model/classification failures: {genuine_classification}\n")
        f.write(f"- Retrieval bottlenecks remain: {genuine_retrieval}\n")

if __name__ == '__main__':
    audit_golden_set()
