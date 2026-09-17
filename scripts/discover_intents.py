import json
import re
from collections import defaultdict
import numpy as np
import pandas as pd
from src.threadmind import config
from sklearn.feature_extraction.text import TfidfVectorizer

INTENT_HEURISTICS = {
    "delivery_delayed": [r"\blate\b", r"\bdelay(?:ed)?\b", r"not arrived", r"tracking hasn't updated", r"still waiting", r"taking too long"],
    "delivery_missing": [r"says delivered", r"marked delivered", r"not here", r"missing package", r"stolen", r"didn't receive", r"never received", r"empty box"],
    "delivery_wrong_item": [r"wrong item", r"incorrect", r"not what i ordered", r"different item"],
    "returns_refunds": [r"\breturn\b", r"\brefund\b", r"label", r"\breplace(?:ment)?\b", r"defective", r"broken"],
    "account_billing": [r"\bcharge(?:d)?\b", r"billed", r"membership", r"subscription", r"unauthorized", r"\bbank\b", r"money"],
    "digital_prime_video": [r"\bvideo\b", r"\bmovie\b", r"streaming", r"playback", r"prime video"],
    "digital_kindle": [r"\bkindle\b", r"paperwhite", r"ebook", r"downloading book", r"library"],
    "amazon_music": [r"\bmusic\b", r"playlist", r"song", r"amazon music"],
    "echo_alexa": [r"\becho\b", r"\balexa\b", r"\bdot\b", r"device not responding"],
    "product_availability": [r"\bstock\b", r"out of stock", r"pre-order", r"available"],
    "account_access": [r"\blogin\b", r"password", r"locked", r"access", r"can't sign in", r"app crashing"],
    "promotions_pricing": [r"discount", r"promo code", r"price drop", r"deal", r"coupon"],
    "prime_wardrobe_try": [r"wardrobe", r"try before you buy"],
    "amazon_locker": [r"locker", r"access code", r"pick up"],
    "grocery_fresh": [r"fresh", r"whole foods", r"grocery", r"delivery window", r"food"]
}

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def extract_thread_text(thread):
    # Combine only customer messages to discover intent, as brand messages are reactive
    cust_msgs = [m['text'].lower() for m in thread['messages'] if m['inbound']]
    return " ".join(cust_msgs)

def match_intents(text):
    matched = []
    for intent, patterns in INTENT_HEURISTICS.items():
        for p in patterns:
            if re.search(p, text):
                matched.append(intent)
                break
    return matched

def main():
    filepath = config.PROCESSED_DATA_DIR / "AmazonHelp_threads.jsonl"
    print(f"Loading {filepath}...")
    threads = load_threads(filepath)
    print(f"Loaded {len(threads)} threads.")
    
    intent_stats = defaultdict(lambda: {
        "thread_count": 0,
        "message_count": 0,
        "example_thread_ids": [],
        "overlap": defaultdict(int)
    })
    
    unclassified = 0
    multi_intent = 0
    corpus = []
    thread_to_intents = {}
    
    for th in threads:
        text = extract_thread_text(th)
        corpus.append(text)
        
        matches = match_intents(text)
        thread_to_intents[th['thread_id']] = matches
        
        if not matches:
            unclassified += 1
            intent_stats["UNKNOWN"]["thread_count"] += 1
            intent_stats["UNKNOWN"]["message_count"] += th['metadata']['message_count']
            continue
            
        if len(matches) > 1:
            multi_intent += 1
            for m1 in matches:
                for m2 in matches:
                    if m1 != m2:
                        intent_stats[m1]["overlap"][m2] += 1
                        
        for m in matches:
            st = intent_stats[m]
            st["thread_count"] += 1
            st["message_count"] += th['metadata']['message_count']
            if len(st["example_thread_ids"]) < 5:
                st["example_thread_ids"].append(th['thread_id'])
                
    # Extract representative keywords per group using TF-IDF
    # We will build a sub-corpus for each intent
    print("Computing TF-IDF for top keywords...")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000, ngram_range=(1, 3))
    
    try:
        X = vectorizer.fit_transform(corpus)
        feature_names = np.array(vectorizer.get_feature_names_out())
        
        for intent in INTENT_HEURISTICS.keys():
            intent_indices = [i for i, th in enumerate(threads) if intent in thread_to_intents.get(th['thread_id'], [])]
            if not intent_indices:
                continue
            
            # Mean TF-IDF vector for this intent
            mean_tfidf = np.asarray(X[intent_indices].mean(axis=0)).flatten()
            top_n = np.argsort(mean_tfidf)[-10:][::-1]
            top_keywords = feature_names[top_n].tolist()
            intent_stats[intent]["representative_keywords"] = top_keywords
    except Exception as e:
        print("TF-IDF extraction failed:", e)

    # Save to CSV
    csv_path = config.REPORTS_DIR / "intent_discovery.csv"
    records = []
    for intent, st in intent_stats.items():
        if intent == "UNKNOWN":
            continue
        # Get top overlaps
        overlaps = sorted(st["overlap"].items(), key=lambda x: x[1], reverse=True)[:3]
        overlap_str = ", ".join([f"{k}({v})" for k, v in overlaps])
        
        records.append({
            "candidate_name": intent,
            "supporting_thread_count": st["thread_count"],
            "supporting_message_count": st["message_count"],
            "representative_keywords": " | ".join(st.get("representative_keywords", [])),
            "representative_phrases": " | ".join(INTENT_HEURISTICS.get(intent, [])),
            "example_thread_ids": ", ".join(st["example_thread_ids"]),
            "confidence": "High" if st["thread_count"] > 1000 else "Medium",
            "overlap_with_other_intents": overlap_str,
            "notes": "Evidence based on heuristic matching."
        })
        
    df = pd.DataFrame(records)
    df = df.sort_values("supporting_thread_count", ascending=False)
    df.to_csv(csv_path, index=False)
    
    print(f"Discovered intents saved to {csv_path}")
    print(f"Coverage: {len(threads) - unclassified} classified, {unclassified} unknown, {multi_intent} overlapping.")

if __name__ == "__main__":
    main()
