import json
import os
import sys
import argparse
from tqdm import tqdm
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
from src.threadmind.baselines.rule_baseline import RuleBaseline
from collections import Counter

PROMPT_TEMPLATE = """You are a strict data annotator for customer support transcripts.
Your task is to classify the intent of the following customer support conversation based on strict rules.

TAXONOMY:
- delivery_missing: Package never arrived, empty box, or stolen package.
- delivery_delayed: Package is late but expected.
- delivery_wrong_item: Customer received a package, but it contained the wrong physical item.
- returns_refunds: Requesting to return an item, reporting defective physical merchandise, or asking for refund status.
- account_access: Issues logging in, reset password, locked account, or app crashing.
- account_billing: Unauthorized charges, Prime subscription billing, or payment method issues.
- digital_prime_video: Streaming issues, Prime Video playback.
- digital_kindle: Kindle device syncing, eBook download issues.
- amazon_music: Music streaming, playlist issues.
- echo_alexa: Echo hardware, Alexa voice assistant issues.
- amazon_locker: Problems opening an Amazon Locker, locker access codes.
- grocery_fresh: Amazon Fresh, Whole Foods, spoiled food.
- promotions_pricing: Coupon codes, price matching, lightning deals.
- product_availability: Pre-orders, out-of-stock items, release dates.

STRICT BOUNDARIES:
- account_access vs delivery_wrong_item: "wrong item" must be ignored if context is digital account access. delivery_wrong_item is strictly for physical package contents.
- amazon_locker vs delivery_missing: If a locker was opened but empty, it is delivery_missing. If locker itself is malfunctioning, it is amazon_locker.
- account_access vs delivery_delayed: Mentions of "delayed" or "late" apply to account_access if referencing OTP emails/app. delivery_delayed is for physical package transit.
- delivery_delayed vs returns_refunds: delivery_delayed applies to outbound shipments. returns_refunds applies to inbound shipments (returns) and refunds.
- delivery_missing vs delivery_wrong_item: If customer received a box but it was empty, it is delivery_missing. If it contained a different item, it is delivery_wrong_item.

Respond with ONLY valid JSON:
{{
  "intent_id": "<one of the 14 intents>",
  "confidence": <float 0.0 to 1.0>,
  "reason": "<short reasoning>",
  "status": "<HIGH_CONFIDENCE | REVIEW | INSUFFICIENT_CONTEXT>"
}}

CONVERSATION:
{conversation}
"""

def relabel_corpus(limit=None):
    raw_path = config.PROCESSED_DATA_DIR / "retrieval_corpus.jsonl"
    out_path = config.PROCESSED_DATA_DIR / "retrieval_corpus_v2_candidate.jsonl"
    
    # We also need the original metadata to get the original label for comparison
    import pickle
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(metadata_path, 'rb') as f:
        metadata_list = pickle.load(f)
    
    original_labels = {m['thread_id']: m['intent_id'] for m in metadata_list}
    
    provider = LLMProvider()
    rule_sys = RuleBaseline()
    
    valid_intents = set(rule_sys.INTENT_KEYWORDS.keys())
    
    results = []
    stats = {
        "original_count": 0,
        "candidate_count": 0,
        "high_confidence": 0,
        "review": 0,
        "insufficient_context": 0,
        "changed": 0,
        "unchanged": 0
    }
    transitions = Counter()
    
    # Boundary stats
    boundary_stats = Counter()
    
    with open(raw_path, 'r') as infile, open(out_path, 'w') as outfile:
        lines = infile.readlines()
        if limit:
            lines = lines[:limit]
            
        for line in tqdm(lines, desc="Relabeling"):
            doc = json.loads(line)
            thread_id = doc['thread_id']
            stats["original_count"] += 1
            
            # Format conv
            conv_text = "\n".join([f"{'User' if m.get('inbound') else 'Agent'}: {m.get('text','')}" for m in doc['messages']])
            
            # Skip empty
            if len(conv_text.strip()) < 10:
                stats["insufficient_context"] += 1
                continue
                
            prompt = PROMPT_TEMPLATE.format(conversation=conv_text)
            
            try:
                # We will use the rule baseline to mock this if MOCK is set to avoid 48 hours wait
                if os.getenv("MOCK_RELABEL", "0") == "1":
                    # Simulate LLM using rule baseline but add a tiny bit of noise/confidence
                    pred = rule_sys.predict([{"author_role": "customer" if m.get("inbound") else "agent", "text": m.get("text","")} for m in doc['messages']])
                    label = pred["predicted_intent"]

                    
                    # deterministic mock of confidence
                    conf = 0.95
                    if "wrong item" in conv_text.lower() and "password" in conv_text.lower():
                        label = "account_access"
                        conf = 0.98
                        
                    status = "HIGH_CONFIDENCE" if conf >= 0.90 else ("REVIEW" if conf >= 0.70 else "INSUFFICIENT_CONTEXT")
                    
                    llm_pred = {
                        "intent_id": label,
                        "confidence": conf,
                        "reason": "Mocked reason",
                        "status": status
                    }
                else:
                    llm_pred = provider.predict(prompt, json_mode=True)
                    
                intent_id = llm_pred.get("intent_id")
                confidence = float(llm_pred.get("confidence", 0.0))
                status = llm_pred.get("status", "REVIEW")
                
                # Validation
                if intent_id not in valid_intents:
                    status = "REVIEW"
                    
                if status == "HIGH_CONFIDENCE" and confidence < 0.90:
                    status = "REVIEW"
                elif status == "REVIEW" and confidence < 0.70:
                    status = "INSUFFICIENT_CONTEXT"
                    
                # Known confusion boundaries validation
                txt_lower = conv_text.lower()
                if intent_id == "delivery_wrong_item" and ("login" in txt_lower or "password" in txt_lower):
                    status = "REVIEW"
                    boundary_stats["account_access_vs_wrong_item_flagged"] += 1
                    
                doc["intent_id_v2"] = intent_id
                doc["confidence"] = confidence
                doc["relabel_status"] = status
                doc["relabel_reason"] = llm_pred.get("reason", "")
                
                outfile.write(json.dumps(doc) + "\n")
                stats["candidate_count"] += 1
                
                if status == "HIGH_CONFIDENCE":
                    stats["high_confidence"] += 1
                elif status == "REVIEW":
                    stats["review"] += 1
                else:
                    stats["insufficient_context"] += 1
                    
                orig_label = original_labels.get(thread_id, "unknown")
                if orig_label != intent_id:
                    stats["changed"] += 1
                    transitions[f"{orig_label} -> {intent_id}"] += 1
                else:
                    stats["unchanged"] += 1
                    
                results.append(doc)
                
            except Exception as e:
                print(f"Error processing {thread_id}: {e}")
                stats["review"] += 1
                
    # Create audit sample
    audit_sample = []
    # Pick 50 of each
    accepted = [r for r in results if r.get("relabel_status") == "HIGH_CONFIDENCE"]
    review = [r for r in results if r.get("relabel_status") == "REVIEW"]
    
    changed = []
    unchanged = []
    for r in results:
        t_id = r["thread_id"]
        if original_labels.get(t_id) != r.get("intent_id_v2"):
            changed.append(r)
        else:
            unchanged.append(r)
            
    audit_sample.extend(accepted[:50])
    audit_sample.extend(changed[:50])
    audit_sample.extend(review[:50])
    audit_sample.extend(unchanged[:50])
    
    with open("reports/phase7_relabel_audit_sample.json", "w") as f:
        json.dump(audit_sample, f, indent=2)
        
    with open("reports/phase7_relabel_audit.md", "w") as f:
        f.write("# Phase 7 Audit Sample\n\n")
        for idx, r in enumerate(audit_sample):
            f.write(f"## Sample {idx+1}: {r['thread_id']}\n")
            f.write(f"- Original Label: {original_labels.get(r['thread_id'])}\n")
            f.write(f"- New Label: {r.get('intent_id_v2')}\n")
            f.write(f"- Confidence: {r.get('confidence')}\n")
            f.write(f"- Status: {r.get('relabel_status')}\n")
            f.write(f"- Reason: {r.get('relabel_reason')}\n\n")
            
    print("Relabeling Complete.")
    print(json.dumps(stats, indent=2))
    
    with open("reports/phase7_corpus_relabeling_report.json", "w") as f:
        json.dump({
            "stats": stats,
            "top_transitions": dict(transitions.most_common(10)),
            "boundary_stats": dict(boundary_stats)
        }, f, indent=2)

if __name__ == "__main__":
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    relabel_corpus(limit)
