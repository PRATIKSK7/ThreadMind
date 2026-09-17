import json
import random
import numpy as np
from src.threadmind import config
from src.threadmind.baselines.tfidf_baseline import TfidfBaseline
from src.threadmind.baselines.rule_baseline import RuleBaseline

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def extract_text(thread):
    return " ".join([m['text'].lower() for m in thread['messages'] if m['inbound']])

def main():
    random.seed(42)
    train_path = config.PROCESSED_DATA_DIR / "train_split.jsonl"
    
    print(f"Loading training data from {train_path}...")
    threads = load_threads(train_path)
    
    sample = random.sample(threads, 2000)
    
    baseline = TfidfBaseline(
        vectorizer_path=config.PROCESSED_DATA_DIR / "tfidf_vectorizer.joblib",
        model_path=config.PROCESSED_DATA_DIR / "tfidf_model.joblib"
    )
    rule_sys = RuleBaseline()
    
    results = []
    
    for th in sample:
        conv = [{"author_role": "customer" if m['inbound'] else "brand", "text": m['text']} for m in th['messages']]
        
        # Get TF-IDF prediction and confidence
        pred = baseline.predict(conv)
        
        # Get Rule Prediction for pseudo-ground-truth (since train set has no human labels)
        rule_pred = rule_sys.predict(conv)
        pseudo_label = rule_pred['predicted_intent']
        
        # We only care about cases where the rule baseline didn't abstain (meaning it was somewhat confident)
        if pseudo_label != "other_support":
            results.append({
                "confidence": pred["confidence"],
                "predicted": pred["predicted_intent"],
                "pseudo_label": pseudo_label,
                "is_correct": pred["predicted_intent"] == pseudo_label
            })
            
    print(f"Evaluated {len(results)} valid examples.")
    
    thresholds = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    
    print("\n--- Calibration Results ---")
    print(f"{'Threshold':<10} | {'Fallback Rate':<15} | {'ML Handled Rate':<15} | {'Accuracy of ML-Handled':<25}")
    print("-" * 75)
    
    best_threshold = None
    
    for t in thresholds:
        handled = [r for r in results if r["confidence"] >= t]
        fallback = [r for r in results if r["confidence"] < t]
        
        if len(handled) == 0:
            acc = 0.0
        else:
            acc = sum(1 for r in handled if r["is_correct"]) / len(handled)
            
        fallback_rate = len(fallback) / len(results)
        handled_rate = len(handled) / len(results)
        
        print(f"{t:<10.2f} | {fallback_rate*100:>13.1f}% | {handled_rate*100:>13.1f}% | {acc*100:>23.2f}%")
        
        # We want to minimize fallback while maintaining >95% accuracy on the ML-handled cases
        if best_threshold is None and acc >= 0.95 and handled_rate > 0.50:
            best_threshold = t
            
    # If none met strict criteria, fallback to a sensible default like 0.70
    if not best_threshold:
        best_threshold = 0.70
        
    print(f"\nRecommended Confidence Threshold: {best_threshold}")

if __name__ == "__main__":
    main()
