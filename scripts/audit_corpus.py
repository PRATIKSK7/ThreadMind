import json
from collections import Counter
from src.threadmind import config
import os

def audit_corpus():
    with open("reports/phase3_golden_set_repair.md", "r") as f:
        phase3_report = f.read()
        
    valid_intents = {
        "delivery_delayed", "delivery_missing", "delivery_wrong_item",
        "returns_refunds", "product_availability", "promotions_pricing",
        "account_billing", "account_access", "digital_prime_video",
        "digital_kindle", "amazon_music", "echo_alexa",
        "amazon_locker", "grocery_fresh", "other_support"
    }

    corpus_path = config.PROCESSED_DATA_DIR / "retrieval_corpus.jsonl"
    
    intent_counts = Counter()
    invalid_intents = set()
    total_docs = 0
    short_docs = 0
    
    # We also want to check for taxonomy violations.
    # From Phase 3/5, the main violations were:
    # 1. account_access vs delivery_wrong_item: "wrong item" but customer has a physical box -> delivery_wrong_item
    # 2. account_access vs delivery_delayed: delivery delayed -> delivery_delayed
    # 3. amazon_locker vs delivery_missing: opened empty -> delivery_missing, broken hardware -> locker
    
    # Let's write a quick heuristic to flag suspicious documents in the corpus
    flagged_account_access = 0
    flagged_amazon_locker = 0
    
    seen_threads = set()
    duplicates = 0

    with open(corpus_path, "r") as f:
        for line in f:
            total_docs += 1
            doc = json.loads(line)
            intent = doc["intent_id"]
            
            intent_counts[intent] += 1
            if intent not in valid_intents:
                invalid_intents.add(intent)
                
            if len(doc["conversation"]) < 2:
                short_docs += 1
                
            thread_id = doc["thread_id"]
            if thread_id in seen_threads:
                duplicates += 1
            seen_threads.add(thread_id)
            
            # Simple keyword heuristics to flag potential mislabels (similar to Phase 2 deterministic flags)
            text = " ".join([m["body"].lower() for m in doc["conversation"]])
            
            if intent == "account_access":
                if "wrong item" in text or "received the wrong" in text:
                    flagged_account_access += 1
                elif "hasn't arrived" in text or "delayed" in text or "late" in text:
                    flagged_account_access += 1
                    
            if intent == "amazon_locker":
                if "empty" in text and "opened" in text:
                    flagged_amazon_locker += 1

    report = {
        "total_documents": total_docs,
        "duplicates": duplicates,
        "short_documents": short_docs,
        "invalid_intents_found": list(invalid_intents),
        "intent_distribution": dict(intent_counts),
        "taxonomy_flags": {
            "suspicious_account_access": flagged_account_access,
            "suspicious_amazon_locker": flagged_amazon_locker
        }
    }
    
    with open("reports/phase6_corpus_audit.json", "w") as f:
        json.dump(report, f, indent=2)
        
    with open("reports/phase6_corpus_audit.md", "w") as f:
        f.write("# Phase 6: Retrieval Corpus Audit\n\n")
        f.write(f"- Total Documents: {total_docs}\n")
        f.write(f"- Duplicates: {duplicates}\n")
        f.write(f"- Short/Empty Documents: {short_docs}\n")
        f.write(f"- Invalid Intents: {invalid_intents}\n\n")
        
        f.write("## Taxonomy Consistency Flags\n")
        f.write("Based on Phase 3 Golden Set repairs, we check if the corpus contains the same systemic mislabels:\n")
        f.write(f"- Suspicious `account_access` (mentions wrong item/delayed): {flagged_account_access}\n")
        f.write(f"- Suspicious `amazon_locker` (mentions opened but empty): {flagged_amazon_locker}\n\n")
        
        f.write("## Intent Distribution\n")
        for k, v in intent_counts.most_common():
            f.write(f"- {k}: {v}\n")

if __name__ == "__main__":
    audit_corpus()
