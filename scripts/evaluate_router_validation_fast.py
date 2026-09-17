import json
import time
from collections import defaultdict
from src.threadmind import config
from src.threadmind.router.fallback_router import FallbackRouter

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def main():
    val_path = config.PROCESSED_DATA_DIR / "val_split.jsonl"
    threads = load_threads(val_path)
    
    # In Step 10, we used a specific random seed to sample the same 500
    import random
    random.seed(42)
    sample = random.sample(threads, 500)
    
    # We will temporarily patch FallbackRouter to NOT call DenseRAG_LLM
    # just to see how many examples fallback.
    router = FallbackRouter(k=3, confidence_threshold=0.70)
    
    routes_taken = defaultdict(int)
    turn_length_metrics = defaultdict(lambda: {"total": 0, "fallback": 0})
    
    print("Evaluating fallback rate on 500 unseen validation threads...")
    start_time = time.time()
    
    for th in sample:
        conv = [{"author_role": "customer" if m['inbound'] else "brand", "text": m['text']} for m in th['messages']]
        
        turn_len = len(conv)
        turn_bucket = "1-2" if turn_len <= 2 else "3-4" if turn_len <= 4 else "5+"
        turn_length_metrics[turn_bucket]["total"] += 1
        
        rule_pred = router.rule_system.predict(conv)
        if rule_pred['predicted_intent'] != "other_support":
            routed_via = "RuleBaseline"
        else:
            tfidf_pred = router.tfidf_system.predict(conv)
            confidence = tfidf_pred.get('confidence', 0.0)
            if confidence >= router.confidence_threshold and tfidf_pred['predicted_intent'] != "other_support":
                routed_via = "TFIDFBaseline"
            else:
                routed_via = "DenseRAG_LLM"
            
        routes_taken[routed_via] += 1
        
        if routed_via == "DenseRAG_LLM":
            turn_length_metrics[turn_bucket]["fallback"] += 1
            
    end_time = time.time()
    print("\n--- Validation Stress Test (Fast) ---")
    print(f"Total Examples: {len(sample)}")
    print(f"Routed via TF-IDF: {routes_taken['TFIDFBaseline']}")
    print(f"Routed via LLM (Fallback): {routes_taken['DenseRAG_LLM']}")
    fallback_rate = routes_taken['DenseRAG_LLM'] / len(sample) * 100
    print(f"Fallback Rate: {fallback_rate:.1f}%")
    
    print("\nFallback by Turn Length:")
    for bucket in ["1-2", "3-4", "5+"]:
        metrics = turn_length_metrics[bucket]
        if metrics['total'] > 0:
            print(f"  {bucket} turns: {metrics['fallback']}/{metrics['total']} ({metrics['fallback']/metrics['total']*100:.1f}%)")

if __name__ == "__main__":
    main()
