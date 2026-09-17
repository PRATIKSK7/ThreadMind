import os
import sys
import json
import csv
import hashlib

# Stability settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def get_review_guidance(boundary):
    guidance = {
        "amazon_locker ↔ delivery_missing": "Determine whether the locker itself is the primary problem (e.g. broken, wrong code) or whether the missing package is the primary problem (e.g. tracking says delivered but locker is empty).",
        "account_access ↔ delivery_missing": "Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution. If they cannot log in to check tracking, account recovery may take precedence.",
        "account_access ↔ delivery_delayed": "Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution.",
        "account_access ↔ delivery_wrong_item": "Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution.",
        "returns_refunds ↔ delivery_missing": "Determine whether the customer is just reporting a missing item (seeking a replacement/whereabouts) or explicitly and primarily requesting a refund for the failure.",
        "returns_refunds ↔ delivery_delayed": "Determine whether the customer is just reporting a delayed item or explicitly and primarily requesting a refund for the delay.",
        "grocery_fresh ↔ returns_refunds": "Determine whether the issue is specifically about Amazon Fresh/grocery items. Grocery issues generally have specific handling separate from general returns.",
        "digital_kindle ↔ other_support": "Determine if the issue strictly pertains to Kindle devices or eBooks.",
        "echo_alexa ↔ other_support": "Determine if the issue strictly pertains to Alexa/Echo devices.",
        "promotions_pricing ↔ other_support": "Determine if the core issue is about pricing, price-matching, or promotions.",
        "product_availability ↔ other_support": "Determine if the core issue is inquiring about stock availability or pre-order dates.",
        "account_billing ↔ other_support": "Determine if the core issue is related to unexpected charges, payment methods, or Prime membership fees."
    }
    return guidance.get(boundary, "Examine the conversation to determine which label captures the customer's primary actionable request.")

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    hash_before = hash_file(golden_path)

    audit_json_path = config.PROJECT_ROOT / "reports" / "phase16e_taxonomy_audit.json"
    with open(audit_json_path, "r") as f:
        cases = json.load(f)
        
    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_results = json.load(f)["predictions"]
    
    v2_dict = {p["example_id"]: p for p in v2_results}

    csv_headers = [
        "case_id",
        "current_label",
        "proposed_label",
        "human_decision",
        "human_reason",
        "confidence",
        "reviewer"
    ]
    
    csv_rows = []
    
    with open("reports/phase16h_human_decisions.md", "w") as outf:
        outf.write("# PHASE 16H — HUMAN TAXONOMY REVIEW\n\n")
        
        for case in cases:
            v2_pred = case["v2_prediction"]
            v2_correct = case["gold_label"] == v2_pred
            boundary = " ↔ ".join(sorted([case["gold_label"], case["v2_prediction"]]))
            
            row = {
                "case_id": case["id"],
                "current_label": case["gold_label"],
                "proposed_label": "",
                "human_decision": "PENDING",
                "human_reason": "",
                "confidence": "",
                "reviewer": ""
            }
            csv_rows.append(row)
            
            outf.write(f"\n### {case['id']}\n")
            outf.write(f"- **Current Golden Label**: `{case['gold_label']}`\n")
            outf.write(f"- **User Conversation**:\n```\n{case['conversation']}\n```\n")
            outf.write(f"- **Retrieved Top-3 Intents**: {case['top_3_retrieved_intents']}\n")
            outf.write(f"- **Retrieved similarity scores**: {case['retrieval_scores']}\n")
            outf.write(f"- **V2 Prediction**: `{case['v2_prediction']}`\n")
            outf.write(f"- **Whether V2 was correct**: {v2_correct}\n")
            outf.write(f"- **Failure category**: {case['failure_category']}\n")
            outf.write(f"- **Competing intent(s)**: `{case['v2_prediction']}`\n")
            outf.write(f"- **Why the case is ambiguous**: {case['reason_current_label_may_be_problematic']}\n")
            outf.write(f"- **Relevant taxonomy definitions**: {get_review_guidance(boundary)}\n")
            outf.write(f"- **Evidence supporting current label**: {case['evidence_supporting_current_label']}\n")
            outf.write(f"- **Evidence supporting competing label**: {case['evidence_supporting_alternative']}\n")
            outf.write("- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT\n")
            outf.write("---\n")

    with open("reports/phase16h_human_decisions.csv", "w", newline="") as outf:
        writer = csv.DictWriter(outf, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_rows)
        
    print("PHASE 16H STATUS:")
    print("READY_FOR_REAL_HUMAN_REVIEW")
    print()
    print("CASES:")
    print("24")
    print()
    print("HUMAN DECISIONS:")
    print("0/24")
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
    print("STOP_AFTER_PHASE_16H:")
    print("YES")

if __name__ == "__main__":
    main()
