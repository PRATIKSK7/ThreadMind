import os
import sys
import json
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from src.threadmind import config

def main():
    print("Auditing Amazon Taxonomy...")
    
    gs_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    gs_cases = []
    with open(gs_path, "r") as f:
        for line in f:
            gs_cases.append(json.loads(line))
            
    intent_counts = defaultdict(int)
    examples = defaultdict(list)
    for c in gs_cases:
        intent = c["intent_id"]
        intent_counts[intent] += 1
        if len(examples[intent]) < 2:
            examples[intent].append(c["conversation"][0]["text"])
            
    # Hardcoded Amazon Taxonomy Definitions mapped from phase 16
    definitions = {
        "account_access": "Issues logging in, password resets, locked accounts.",
        "account_billing": "Unrecognized charges, Prime membership billing, invoice requests.",
        "returns_refunds": "Requesting a refund, returning an item, checking refund status.",
        "promotions_pricing": "Price matching, promotional code issues, discounts.",
        "delivery_missing": "Package marked delivered but not found, stolen packages.",
        "delivery_wrong_item": "Received incorrect item, damaged item upon arrival.",
        "grocery_fresh": "Amazon Fresh or Whole Foods delivery issues, spoiled food.",
        "amazon_locker": "Locker codes not working, locker full, pickup issues.",
        "delivery_delayed": "Package has not arrived by promised date, tracking stalled.",
        "echo_alexa": "Echo device troubleshooting, Alexa voice recognition issues.",
        "digital_prime_video": "Prime Video streaming errors, renting/purchasing digital movies.",
        "digital_kindle": "Kindle device sync issues, missing e-books.",
        "amazon_music": "Amazon Music Unlimited billing, playback issues.",
        "product_availability": "Restock dates, pre-order status, stock inquiries.",
        "other_support": "Miscellaneous inquiries not fitting other categories."
    }
    
    boundaries = {
        "delivery_missing": "Only when package is marked delivered but not received. If not delivered yet, use delivery_delayed.",
        "returns_refunds": "Must explicitly involve returning a product or getting money back. If it's a billing dispute for a service, use account_billing.",
        "digital_prime_video": "Strictly digital streaming. Physical DVDs use delivery_delayed/wrong_item.",
        "account_access": "Login and account lockouts. Billing issues inside an accessible account go to account_billing."
    }
    
    audit_md = f"""# Amazon Support Taxonomy Audit

## Overview
The selected brand is **Amazon**. The taxonomy is specifically tailored to Amazon customer support on Twitter (@AmazonHelp), covering e-commerce logistics, digital services (Prime Video, Kindle, Music), physical devices (Echo), and grocery (Fresh).

## Intent Definitions & Boundaries
"""
    audit_json = []
    
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        definition = definitions.get(intent, "General Amazon support inquiry.")
        boundary = boundaries.get(intent, "Standard isolation.")
        exs = examples[intent]
        
        audit_md += f"### {intent} (Count: {count})\n"
        audit_md += f"- **Definition**: {definition}\n"
        audit_md += f"- **Boundary / Common Confusion**: {boundary}\n"
        audit_md += f"- **Example 1**: \"{exs[0] if len(exs) > 0 else ''}\"\n"
        if len(exs) > 1:
            audit_md += f"- **Example 2**: \"{exs[1]}\"\n"
        audit_md += "\n"
        
        audit_json.append({
            "intent": intent,
            "count": count,
            "definition": definition,
            "boundary": boundary,
            "examples": exs
        })
        
    with open(config.REPORTS_DIR / "amazon_taxonomy_audit.md", "w") as f:
        f.write(audit_md)
        
    with open(config.REPORTS_DIR / "amazon_taxonomy_audit.json", "w") as f:
        json.dump(audit_json, f, indent=2)
        
    print("Taxonomy audit complete.")

if __name__ == "__main__":
    main()
