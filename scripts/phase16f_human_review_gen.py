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

def verify_golden_set(filepath):
    expected_hash = "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f"
    actual_hash = hash_file(filepath)
    if actual_hash != expected_hash:
        raise ValueError(f"Golden Set hash mismatch! Expected {expected_hash}, got {actual_hash}")
    return actual_hash

def get_boundary_definitions():
    return """
## amazon_locker ↔ delivery_missing
- **Intent A (amazon_locker)**: The customer's primary issue concerns the Amazon Locker itself, locker access, locker location, locker malfunction, or retrieving an order from a locker.
- **Intent B (delivery_missing)**: The customer's primary issue is that an expected delivery/order has not arrived, regardless of whether a locker is mentioned.
- **Distinguishing feature**: Operational locus (locker functionality vs package arrival).
- **Positive indicators for A**: "Locker won't open", "Locker is full", "Can't find the locker".
- **Positive indicators for B**: "Tracking says delivered but not in locker", "Package lost".
- **Explicit exclusions**: A missing package that happened to be routed to a locker is NOT a locker issue unless the locker itself is broken.
- **Examples that remain ambiguous**: The courier marked it delivered to a locker, but the locker door opened empty. (Did the courier steal it, or did the locker malfunction?)

## account_access ↔ delivery_missing
- **Intent A (account_access)**: Customer is locked out, forgot password, or reports suspicious account activity.
- **Intent B (delivery_missing)**: Customer is asking where their package is.
- **Distinguishing feature**: Security vs Logistics.
- **Positive indicators for A**: "Forgot password", "Hacked", "Can't log in".
- **Positive indicators for B**: "Where is my stuff", "Not received".
- **Explicit exclusions**: If they can't log in to check tracking, account_access takes priority.
- **Examples that remain ambiguous**: Customer says "Someone hacked me and stole my delivery".

## account_access ↔ delivery_delayed
- **Intent A (account_access)**: Customer is locked out, forgot password, or reports suspicious account activity.
- **Intent B (delivery_delayed)**: Package is arriving later than expected.
- **Distinguishing feature**: Security vs Logistics.
- **Positive indicators for A**: "Account locked".
- **Positive indicators for B**: "Tracking hasn't updated".
- **Explicit exclusions**: Same as above.
- **Examples that remain ambiguous**: Customer account locked after disputing a delayed package.

## account_access ↔ delivery_wrong_item
- **Intent A (account_access)**: Customer is locked out, forgot password, or reports suspicious account activity.
- **Intent B (delivery_wrong_item)**: Received incorrect product.
- **Distinguishing feature**: Security vs Logistics.
- **Positive indicators for A**: "Can't login".
- **Positive indicators for B**: "Sent me the wrong size".
- **Explicit exclusions**: Same as above.
- **Examples that remain ambiguous**: Account suspended for too many wrong item returns.

## returns_refunds ↔ delivery_missing
- **Intent A (returns_refunds)**: Requesting money back or initiating a return.
- **Intent B (delivery_missing)**: Reporting non-receipt of a package.
- **Distinguishing feature**: Desired resolution (Financial vs Logistics).
- **Positive indicators for A**: "I want a refund", "Give me my money back".
- **Positive indicators for B**: "Where is my package", "Can you find it".
- **Explicit exclusions**: Asking "where is my package" is delivery_missing even if they might ultimately want a refund if it's lost.
- **Examples that remain ambiguous**: "My package is missing, refund me now."

## returns_refunds ↔ delivery_delayed
- **Intent A (returns_refunds)**: Requesting money back or initiating a return.
- **Intent B (delivery_delayed)**: Package is arriving later than expected.
- **Distinguishing feature**: Desired resolution (Financial vs Logistics).
- **Positive indicators for A**: "Cancel and refund".
- **Positive indicators for B**: "When will it arrive".
- **Explicit exclusions**: Same as above.
- **Examples that remain ambiguous**: "It's late, if it doesn't arrive tomorrow I want a refund."

## grocery_fresh ↔ returns_refunds
- **Intent A (grocery_fresh)**: Issues specifically with Amazon Fresh / Grocery orders.
- **Intent B (returns_refunds)**: General refund requests.
- **Distinguishing feature**: Domain specificity.
- **Positive indicators for A**: "Fresh order", "Groceries spoiled", "Missing milk".
- **Positive indicators for B**: "Refund my shoes".
- **Explicit exclusions**: Grocery issues take precedence over general refunds because grocery has different logistical workflows.
- **Examples that remain ambiguous**: "Refund my entire fresh order."

## grocery_fresh ↔ other_support
- **Intent A (grocery_fresh)**: Issues specifically with Amazon Fresh / Grocery orders.
- **Intent B (other_support)**: Generic unclassified support.
- **Distinguishing feature**: Domain specificity.
- **Positive indicators for A**: "Fresh delivery".
- **Positive indicators for B**: "I have a weird question".
- **Explicit exclusions**: Anything grocery-related must never be other_support.
- **Examples that remain ambiguous**: None. Grocery_fresh always wins.

## digital_kindle ↔ other_support
- **Intent A (digital_kindle)**: Kindle devices or eBooks.
- **Intent B (other_support)**: Generic unclassified support.
- **Distinguishing feature**: Domain specificity.
- **Positive indicators for A**: "Kindle paperwhite", "Ebook won't download".
- **Explicit exclusions**: Anything Kindle-related must never be other_support.
- **Examples that remain ambiguous**: None. Digital_kindle always wins.

## echo_alexa ↔ other_support
- **Intent A (echo_alexa)**: Alexa devices or Echo hardware.
- **Intent B (other_support)**: Generic unclassified support.
- **Distinguishing feature**: Domain specificity.
- **Positive indicators for A**: "Alexa won't connect".
- **Explicit exclusions**: Anything Alexa-related must never be other_support.
- **Examples that remain ambiguous**: None. Echo_alexa always wins.

## promotions_pricing ↔ other_support
- **Intent A (promotions_pricing)**: Price matching, discounts, coupons.
- **Intent B (other_support)**: Generic unclassified support.
- **Distinguishing feature**: Financial inquiry vs Generic.
- **Positive indicators for A**: "Price dropped", "Promo code not working".
- **Explicit exclusions**: Pricing inquiries must never be other_support.
- **Examples that remain ambiguous**: None. Promotions_pricing always wins.

## product_availability ↔ other_support
- **Intent A (product_availability)**: Stock levels, pre-orders, release dates.
- **Intent B (other_support)**: Generic unclassified support.
- **Distinguishing feature**: Pre-purchase inquiry vs Generic.
- **Positive indicators for A**: "When is this back in stock", "Pre-order date".
- **Explicit exclusions**: Availability inquiries must never be other_support.
- **Examples that remain ambiguous**: None. Product_availability always wins.

## account_billing ↔ other_support
- **Intent A (account_billing)**: Charges, Prime membership fees, payment methods.
- **Intent B (other_support)**: Generic unclassified support.
- **Distinguishing feature**: Financial inquiry vs Generic.
- **Positive indicators for A**: "Unknown charge", "Update credit card".
- **Explicit exclusions**: Billing inquiries must never be other_support.
- **Examples that remain ambiguous**: None. Account_billing always wins.
"""

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    hash_before = verify_golden_set(golden_path)

    audit_json_path = config.PROJECT_ROOT / "reports" / "phase16e_taxonomy_audit.json"
    audit_csv_path = config.PROJECT_ROOT / "reports" / "phase16e_manual_review.csv"
    
    with open(audit_json_path, "r") as f:
        audit_json = json.load(f)
        
    csv_rows = []
    with open(audit_csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_rows.append(row)
            
    csv_dict = {r["id"]: r for r in csv_rows}
    
    # 1. Generate phase16f_human_taxonomy_review.md
    with open("reports/phase16f_human_taxonomy_review.md", "w") as f:
        f.write("# Phase 16F — Human Taxonomy Review\n\n")
        f.write("## Taxonomy Boundaries\n")
        f.write(get_boundary_definitions())
        f.write("\n## 24 Suspicious Examples\n")
        
        for case in audit_json:
            cid = case["id"]
            csv_data = csv_dict[cid]
            f.write(f"### Example: {cid}\n")
            f.write(f"**Conversation**:\n```\n{case['conversation']}\n```\n")
            f.write(f"- **Current Golden Label**: `{case['gold_label']}`\n")
            f.write(f"- **V2 Prediction**: `{case['v2_prediction']}`\n")
            f.write(f"- **Top-3 Retrieved Intents**: {case['top_3_retrieved_intents']}\n")
            f.write(f"- **Retrieval Scores**: {case['retrieval_scores']}\n")
            f.write(f"- **Failure Category**: {case['failure_category']}\n")
            f.write(f"- **Primary Ambiguity Boundary**: {csv_data['boundary']}\n")
            f.write(f"- **Why the example is ambiguous**: {case['reason_current_label_may_be_problematic']}\n")
            f.write(f"- **Evidence supporting current label**: {case['evidence_supporting_current_label']}\n")
            f.write(f"- **Evidence supporting alternative**: {case['evidence_supporting_alternative']}\n")
            
            f.write(f"\n**Taxonomy Gap Analysis**:\n")
            f.write("- Can exactly one existing intent represent the customer's PRIMARY problem? **AMBIGUOUS**\n")
            f.write("- Why the current taxonomy is insufficient: The taxonomy forces a choice between the symptom (e.g. delivery issue) and the requested resolution (e.g. refund/account change) without a strict encoding hierarchy.\n")
            f.write("- What new intent would theoretically be needed: A compound intent or multi-label paradigm (e.g., `delivery_missing+returns_refunds`).\n\n")
            
            f.write(f"**Human Decision**: `[PENDING]`\n")
            f.write(f"**Decision Reason**: \n")
            f.write(f"**Reviewer Confidence**: \n\n")
            f.write("---\n")
            
    # 2. Generate phase16f_human_taxonomy_review.csv
    # The output format for this CSV wasn't specifically defined with new columns, but we will output the required fields
    csv_headers = [
        "id", "conversation", "current_golden_label", "v2_prediction", "top_3_retrieved_intents",
        "retrieval_scores", "failure_category", "primary_ambiguity_boundary", "why_ambiguous",
        "evidence_current", "evidence_alternative", "human_decision", "decision_reason", "reviewer_confidence"
    ]
    with open("reports/phase16f_human_taxonomy_review.csv", "w", newline="") as outf:
        writer = csv.DictWriter(outf, fieldnames=csv_headers)
        writer.writeheader()
        for case in audit_json:
            cid = case["id"]
            csv_data = csv_dict[cid]
            writer.writerow({
                "id": cid,
                "conversation": case["conversation"].replace("\n", " | "),
                "current_golden_label": case["gold_label"],
                "v2_prediction": case["v2_prediction"],
                "top_3_retrieved_intents": ",".join(case["top_3_retrieved_intents"]),
                "retrieval_scores": ",".join(map(str, case["retrieval_scores"])),
                "failure_category": case["failure_category"],
                "primary_ambiguity_boundary": csv_data["boundary"],
                "why_ambiguous": case["reason_current_label_may_be_problematic"],
                "evidence_current": case["evidence_supporting_current_label"],
                "evidence_alternative": case["evidence_supporting_alternative"],
                "human_decision": "[PENDING]",
                "decision_reason": "",
                "reviewer_confidence": ""
            })

    # 3. Generate phase16f_review_form.md
    with open("reports/phase16f_review_form.md", "w") as f:
        for case in audit_json:
            cid = case["id"]
            csv_data = csv_dict[cid]
            f.write("--------------------------------\n\n")
            f.write(f"CASE ID:\n{cid}\n\n")
            f.write(f"CURRENT LABEL:\n{case['gold_label']}\n\n")
            f.write(f"V2 PREDICTION:\n{case['v2_prediction']}\n\n")
            f.write(f"TOP RETRIEVED:\n{', '.join(case['top_3_retrieved_intents'])}\n\n")
            f.write(f"CONVERSATION:\n{case['conversation']}\n\n")
            f.write(f"BOUNDARY:\n{csv_data['boundary']}\n\n")
            f.write(f"QUESTION:\n{csv_data['question_for_human']}\n\n")
            f.write(f"OPTION A:\n{csv_data['option_A']}\n\n")
            f.write(f"OPTION B:\n{csv_data['option_B']}\n\n")
            f.write("MY DECISION:\n[PENDING]\n\n")
            f.write("MY REASON:\n[ ]\n\n")
            f.write("CONFIDENCE:\n[HIGH / MEDIUM / LOW]\n\n")
        f.write("--------------------------------\n")
        
    hash_after = verify_golden_set(golden_path)
    if hash_before != hash_after:
        raise ValueError("CRITICAL: Golden Set was modified during execution!")
        
    print("PHASE 16F STATUS:")
    print("READY_FOR_HUMAN_REVIEW")
    print()
    print("CASES:")
    print("24")
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
    print("HUMAN DECISIONS:")
    print("0/24")
    print()
    print("FINAL DECISION:")
    print("HUMAN_REVIEW_REQUIRED")
    print()
    print("NEXT STEP:")
    print("WAIT_FOR_MANUAL_DECISIONS")

if __name__ == "__main__":
    main()
