import json
import time
import hashlib
import numpy as np
from sklearn.metrics import f1_score
from src.threadmind import config
from src.threadmind.router.fallback_router import FallbackRouter

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def calculate_metrics(results):
    intents_true = []
    intents_pred = []
    escalation_true = []
    escalation_pred = []
    
    api_failures = 0
    malformed = 0
    cache_hits = 0
    latencies = []
    
    rule_routed = 0
    llm_routed = 0
    
    for r in results:
        if r.get('_cache_hit', False):
            cache_hits += 1
            
        if 'latency_seconds' in r:
            latencies.append(r['latency_seconds'])
            
        if r.get('routed_via') == 'RuleBaseline':
            rule_routed += 1
        else:
            llm_routed += 1
            
        if r.get('error'):
            api_failures += 1
            continue
            
        if not r.get('predicted_intent'):
            malformed += 1
            continue
            
        intents_true.append(r['expected_intent'])
        intents_pred.append(r['predicted_intent'])
        
        escalation_true.append(r['expected_escalation'])
        escalation_pred.append(r['predicted_escalation'])

    intent_acc = sum([1 for t, p in zip(intents_true, intents_pred) if t == p]) / len(intents_true) if intents_true else 0
    escalation_acc = sum([1 for t, p in zip(escalation_true, escalation_pred) if t == p]) / len(escalation_true) if escalation_true else 0
    macro_f1 = f1_score(intents_true, intents_pred, average='macro', zero_division=0) if intents_true else 0
    
    return {
        "intent_accuracy": intent_acc,
        "macro_f1": macro_f1,
        "escalation_accuracy": escalation_acc,
        "api_failures": api_failures,
        "malformed_responses": malformed,
        "cache_hits": cache_hits,
        "latency_avg": float(np.mean(latencies)) if latencies else 0.0,
        "total_latency": sum(latencies),
        "rule_routed_count": rule_routed,
        "llm_routed_count": llm_routed
    }

def main():
    print("Initializing Fallback Router (K=3)...")
    router = FallbackRouter(k=3)
    
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    dataset = load_threads(golden_path)
    
    with open(golden_path, "rb") as f:
        golden_hash = hashlib.sha256(f.read()).hexdigest()
        
    print(f"\nEvaluating Router Baseline on {len(dataset)} Golden Set examples...")
    results = []
    
    for i, r in enumerate(dataset):
        target_intent = r['intent_id']
        target_escalation = r['expected_behavior']['escalation']
        
        start_time = time.time()
        pred = router.predict(r['conversation'])
        latency = time.time() - start_time
        
        if pred.get('_cache_hit', False):
            latency = 0.0
            
        is_correct = pred.get('predicted_intent') == target_intent
        
        record = {
            "example_id": r['example_id'],
            "thread_id": r['thread_id'],
            "predicted_intent": pred.get('predicted_intent'),
            "expected_intent": target_intent,
            "predicted_escalation": pred.get('predicted_escalation'),
            "expected_escalation": target_escalation,
            "correctness": is_correct,
            "latency_seconds": latency,
            "error": pred.get('error'),
            "_cache_hit": pred.get('_cache_hit', False),
            "routed_via": pred.get('routed_via')
        }
                
        results.append(record)
        
        if (i+1) % 20 == 0:
            print(f"Processed {i+1}/{len(dataset)}... (Routed via LLM so far: {sum([1 for res in results if res['routed_via'] != 'RuleBaseline'])})")
            
    metrics = calculate_metrics(results)
    
    # Save results
    clean_results = [{k:v for k,v in res.items() if not k.startswith('_')} for res in results]
    
    with open(config.REPORTS_DIR / "baseline_router_results.json", "w") as f:
        json.dump({"metrics": metrics, "predictions": clean_results}, f, indent=2)
        
    # Generate unified markdown report
    with open(config.REPORTS_DIR / "baseline_router_results.md", "w") as f:
        f.write("# Step 8: Rule-First Fallback Router Evaluation\n\n")
        f.write("## Configuration\n")
        f.write(f"- **Architecture**: Rule Baseline -> Dense RAG (K=3) -> Llama 3.2\n")
        f.write(f"- **Golden Set Hash**: `{golden_hash}`\n\n")
        
        f.write("## System Metrics\n")
        f.write(f"- **Total Examples**: {len(dataset)}\n")
        f.write(f"- **Routed to Rules**: {metrics['rule_routed_count']} ({(metrics['rule_routed_count']/len(dataset))*100:.2f}%)\n")
        f.write(f"- **Routed to Dense RAG**: {metrics['llm_routed_count']} ({(metrics['llm_routed_count']/len(dataset))*100:.2f}%)\n")
        f.write(f"- **Average Latency**: {metrics['latency_avg']:.4f}s\n")
        f.write(f"- **Total Compute Latency**: {metrics['total_latency']:.2f}s\n\n")
        
        f.write("## Performance Metrics\n")
        f.write(f"- **Intent Accuracy**: {metrics['intent_accuracy']*100:.2f}%\n")
        f.write(f"- **Intent Macro F1**: {metrics['macro_f1']:.4f}\n")
        f.write(f"- **Escalation Accuracy**: {metrics['escalation_accuracy']*100:.2f}%\n\n")
        
    print(f"\nRouter Evaluation Complete! Final Accuracy: {metrics['intent_accuracy']*100:.2f}%")

if __name__ == "__main__":
    main()
