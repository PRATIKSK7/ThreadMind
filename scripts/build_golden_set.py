import json
import random
from collections import defaultdict
from src.threadmind import config
import os

DEFAULT_RANDOM_SEED = 42

INTENTS = [
    "delivery_delayed", "delivery_missing", "delivery_wrong_item", 
    "returns_refunds", "account_billing", "digital_prime_video", 
    "digital_kindle", "amazon_music", "echo_alexa", "account_access",
    "promotions_pricing", "amazon_locker", "grocery_fresh", "product_availability"
]

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def extract_thread_text(thread):
    return " ".join([m['text'].lower() for m in thread['messages'] if m['inbound']])

def assign_intent(thread):
    text = extract_thread_text(thread)
    
    # Priority order matching
    if any(k in text for k in ["wrong item", "incorrect", "not what i ordered"]): return "delivery_wrong_item"
    if any(k in text for k in ["delivered", "not here", "missing package", "stolen", "didn't receive", "empty box"]): return "delivery_missing"
    if any(k in text for k in ["late", "delay", "not arrived", "still waiting", "taking too long"]): return "delivery_delayed"
    if any(k in text for k in ["return", "refund", "label", "defective", "broken"]): return "returns_refunds"
    if any(k in text for k in ["charge", "billed", "unauthorized", "bank", "money"]): return "account_billing"
    if any(k in text for k in ["video", "movie", "streaming", "prime video"]): return "digital_prime_video"
    if any(k in text for k in ["kindle", "ebook", "paperwhite"]): return "digital_kindle"
    if any(k in text for k in ["music", "song", "playlist"]): return "amazon_music"
    if any(k in text for k in ["echo", "alexa", "dot"]): return "echo_alexa"
    if any(k in text for k in ["login", "password", "locked", "access"]): return "account_access"
    if any(k in text for k in ["discount", "promo", "price", "deal", "coupon"]): return "promotions_pricing"
    if any(k in text for k in ["locker", "access code", "pick up"]): return "amazon_locker"
    if any(k in text for k in ["fresh", "whole foods", "grocery", "spoiled"]): return "grocery_fresh"
    if any(k in text for k in ["stock", "pre-order", "available"]): return "product_availability"
    
    return "other_support"

def get_difficulty(thread):
    meta = thread['metadata']
    if meta['has_missing_parent'] or meta['branch_detected']:
        return "ambiguous"
    if meta['turn_count'] >= 6:
        return "hard"
    if meta['turn_count'] >= 3:
        return "medium"
    return "easy"

def get_escalation_label(thread):
    text = extract_thread_text(thread)
    meta = thread['metadata']
    
    # Evidence-based escalation
    if any(k in text for k in ["real person", "human", "agent", "supervisor", "manager", "lawyer", "fraud"]):
        return "human_review_recommended"
        
    # Unresolved loops (e.g., customer saying "it didn't work" multiple times)
    if text.count("didn't work") >= 2 or text.count("still not") >= 2:
        return "human_review_recommended"
        
    # Missing tracking numbers or missing context usually requires clarification
    if any(k in text for k in ["where is my", "tracking", "status"]):
        if not any(char.isdigit() for char in text): # Naive heuristic: no numbers = no tracking ID
            return "clarification_needed"
            
    if meta['has_missing_parent']:
        return "clarification_needed"
        
    return "no_escalation"

def get_expected_behavior(intent, thread, difficulty):
    escalation = get_escalation_label(thread)
    reqs = []
    must_not_claim = ["Cannot view personal order details without API", "Cannot process refunds directly"]
    
    if intent in ["account_billing", "account_access"]:
        reqs.append("Provide link to secure account dashboard")
    if intent.startswith("delivery"):
        reqs.append("Explain delivery timelines")
    if intent == "returns_refunds":
        reqs.append("Provide instructions on how to print return label")
        
    return {
        "intent": intent,
        "escalation": escalation,
        "response_requirements": reqs,
        "must_not_claim": must_not_claim
    }

def run_sampling(seed, conversational_threads):
    random.seed(seed)
    
    intent_buckets = defaultdict(list)
    for th in conversational_threads:
        intent = assign_intent(th)
        if intent in INTENTS:
            intent_buckets[intent].append(th)
            
    # Sample 14-15 per intent up to ~200 total
    # 14 intents * 14 = 196
    golden_set = []
    
    for intent in INTENTS:
        population = intent_buckets[intent]
        short = [th for th in population if th['metadata']['turn_count'] <= 2]
        med = [th for th in population if 3 <= th['metadata']['turn_count'] <= 4]
        long = [th for th in population if th['metadata']['turn_count'] >= 5]
        
        # Target: 7 short, 5 med, 2 long = 14 examples per intent
        s_samp = random.sample(short, min(len(short), 7))
        m_samp = random.sample(med, min(len(med), 5))
        l_samp = random.sample(long, min(len(long), 2))
        
        sampled = s_samp + m_samp + l_samp
        
        # Fill missing with whatever
        if len(sampled) < 14:
            remaining = [t for t in population if t not in sampled]
            sampled += random.sample(remaining, min(len(remaining), 14 - len(sampled)))
            
        golden_set.extend(sampled)
        
    # Build schema
    golden_records = []
    for idx, th in enumerate(golden_set):
        intent = assign_intent(th)
        diff = get_difficulty(th)
        expected = get_expected_behavior(intent, th, diff)
        
        conv = []
        for m in th['messages']:
            conv.append({
                "author_role": "customer" if m['inbound'] else "brand",
                "text": m['text']
            })
            
        rec = {
            "example_id": f"GS-{idx:03d}",
            "thread_id": th['thread_id'],
            "intent_id": intent,
            "conversation": conv,
            "expected_behavior": expected,
            "difficulty": diff,
            "source_metadata": {
                "turn_count": th['metadata']['turn_count'],
                "message_count": th['metadata']['message_count']
            }
        }
        golden_records.append(rec)
    return golden_records

def main():
    filepath = config.PROCESSED_DATA_DIR / "AmazonHelp_threads.jsonl"
    print(f"Loading {filepath}...")
    threads = load_threads(filepath)
    conversational_threads = [th for th in threads if th['metadata']['message_count'] >= 2]
    
    print("Running sampling pass 1...")
    golden_records_1 = run_sampling(DEFAULT_RANDOM_SEED, conversational_threads)
    
    print("Running sampling pass 2 to verify reproducibility...")
    golden_records_2 = run_sampling(DEFAULT_RANDOM_SEED, conversational_threads)
    
    assert [r['thread_id'] for r in golden_records_1] == [r['thread_id'] for r in golden_records_2], "Sampling is non-deterministic!"
    print("Determinism verified.")
    
    # Use the first run
    golden_records = golden_records_1
    
    # Save JSONL
    out_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    with open(out_path, "w") as f:
        for r in golden_records:
            f.write(json.dumps(r) + "\n")
            
    print(f"Saved {len(golden_records)} golden examples to {out_path}.")
    
    # Save review CSV
    csv_path = config.REPORTS_DIR / "golden_set_review.csv"
    with open(csv_path, "w") as f:
        f.write("example_id,thread_id,intent_id,turn_count,difficulty,review_status,review_notes\n")
        for r in golden_records:
            f.write(f"{r['example_id']},{r['thread_id']},{r['intent_id']},{r['source_metadata']['turn_count']},{r['difficulty']},pending,\n")

    # Generate Statistics
    intent_dist = defaultdict(int)
    turn_dist = defaultdict(int)
    diff_dist = defaultdict(int)
    esc_dist = defaultdict(int)
    lengths = []
    
    for r in golden_records:
        intent_dist[r['intent_id']] += 1
        turn_dist[r['source_metadata']['turn_count']] += 1
        diff_dist[r['difficulty']] += 1
        esc_dist[r['expected_behavior']['escalation']] += 1
        lengths.append(r['source_metadata']['message_count'])
        
    stats = {
        "total_examples": len(golden_records),
        "examples_per_intent": dict(intent_dist),
        "turn_distribution": dict(turn_dist),
        "difficulty_distribution": dict(diff_dist),
        "escalation_distribution": dict(esc_dist),
        "average_conversation_length": float(sum(lengths)) / max(len(lengths), 1),
        "median_conversation_length": float(sorted(lengths)[len(lengths)//2]) if lengths else 0,
        "p90_conversation_length": float(sorted(lengths)[int(len(lengths)*0.9)]) if lengths else 0,
    }
    
    with open(config.REPORTS_DIR / "golden_set_statistics.json", "w") as f:
        json.dump(stats, f, indent=2)
        
    with open(config.REPORTS_DIR / "golden_set_statistics.md", "w") as f:
        f.write("# Golden Set Statistics\n\n")
        f.write(f"- **Total Examples**: {stats['total_examples']}\n")
        f.write(f"- **Average Messages**: {stats['average_conversation_length']:.1f}\n")
        f.write(f"- **Median Messages**: {stats['median_conversation_length']}\n")
        f.write(f"- **P90 Messages**: {stats['p90_conversation_length']}\n\n")
        f.write("## Intent Distribution\n")
        for k, v in intent_dist.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Difficulty Distribution\n")
        for k, v in diff_dist.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Escalation Labels\n")
        f.write(f"- human_review_recommended: {esc_dist['human_review_recommended']}\n")
        f.write(f"- clarification_needed: {esc_dist['clarification_needed']}\n")
        f.write(f"- no_escalation: {esc_dist['no_escalation']}\n")

if __name__ == "__main__":
    main()
