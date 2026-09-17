import json
import time
import random
from pathlib import Path
from collections import defaultdict
from src.threadmind import config
from src.threadmind.router.fallback_router import FallbackRouter

def main():
    random.seed(42)
    val_path = config.PROCESSED_DATA_DIR / "val_split.jsonl"
    
    threads = []
    with open(val_path, "r") as f:
        for line in f:
            threads.append(json.loads(line))
            
    # Sample 500
    sample = random.sample(threads, 500)
    
    print(f"Loaded {len(sample)} random validation examples for stress test.")
    
    router = FallbackRouter(k=3)
    
    results = []
    fallback_cases = []
    
    start_time = time.time()
    
    routes_taken = defaultdict(int)
    turn_length_metrics = defaultdict(lambda: {"total": 0, "fallback": 0})
    
    import sys
    for i, th in enumerate(sample):
        if i % 10 == 0:
            print(f"Processed {i}/500...")
            sys.stdout.flush()
            
        conv = [{"author_role": "customer" if m['inbound'] else "brand", "text": m['text']} for m in th['messages']]
        
        turn_len = len(conv)
        turn_bucket = "1-2" if turn_len <= 2 else "3-4" if turn_len <= 4 else "5+"
        turn_length_metrics[turn_bucket]["total"] += 1
        
        pred = router.predict(conv)
        
        routed_via = pred.get('routed_via', 'RuleBaseline')
        routes_taken[routed_via] += 1
        
        predicted_intent = pred.get('predicted_intent', 'other_support')
        
        if routed_via != "RuleBaseline":
            turn_length_metrics[turn_bucket]["fallback"] += 1
            fallback_cases.append({
                "thread_id": th['thread_id'],
                "conversation": conv,
                "predicted_intent": predicted_intent,
                "reasoning": pred.get('reasoning_summary', pred.get('error', ''))
            })
            
        results.append({
            "thread_id": th['thread_id'],
            "routed_via": routed_via,
            "predicted_intent": predicted_intent
        })
        
    end_time = time.time()
    total_time = end_time - start_time
    avg_latency = total_time / len(sample)
    
    print(f"\nStress Test Complete!")
    print(f"Total Compute Time: {total_time:.2f}s (Avg {avg_latency:.4f}s/query)")
    print(f"Routed via Rules: {routes_taken['RuleBaseline']}")
    print(f"Routed via LLM (Fallback): {routes_taken['Dense RAG (Llama 3.2)']}")
    
    # Save artifacts
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(config.REPORTS_DIR / "validation_stress_test_results.json", "w") as f:
        json.dump({
            "metrics": {
                "total_examples": len(sample),
                "routed_via_rules": routes_taken['RuleBaseline'],
                "routed_via_llm": routes_taken['Dense RAG (Llama 3.2)'],
                "avg_latency": avg_latency,
                "total_latency": total_time,
                "turn_length_metrics": turn_length_metrics
            },
            "predictions": results
        }, f, indent=2)
        
    with open(config.REPORTS_DIR / "validation_fallback_cases.json", "w") as f:
        json.dump(fallback_cases, f, indent=2)
        
    print(f"Saved {len(fallback_cases)} LLM fallback cases to reports/validation_fallback_cases.json")

if __name__ == "__main__":
    main()
