import json
import time
import hashlib
import numpy as np
from collections import defaultdict
from sklearn.metrics import f1_score, precision_recall_fscore_support, confusion_matrix
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
from src.threadmind.rag.tfidf_retriever import TFIDFRetriever

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def load_prompt_template():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v1.txt"
    with open(prompt_path, "r") as f:
        return f.read()

def format_few_shot(retrieved_docs):
    blocks = []
    for i, doc in enumerate(retrieved_docs):
        meta = doc['metadata']
        block = f"--- Example {i+1} ---\n"
        block += f"Conversation:\n{meta['conversation']}\n\n"
        block += f"Classification:\n"
        block += f"{{\n  \"predicted_intent\": \"{meta['intent_id']}\",\n"
        block += f"  \"predicted_escalation\": \"{meta['escalation']}\"\n}}\n"
        blocks.append(block)
    return "\n".join(blocks)

def calculate_metrics(results):
    intents_true = []
    intents_pred = []
    escalation_true = []
    escalation_pred = []
    
    api_failures = 0
    malformed = 0
    cache_hits = 0
    cache_misses = 0
    latencies = []
    
    for r in results:
        if r.get('_cache_hit', False):
            cache_hits += 1
        else:
            cache_misses += 1
            
        if 'latency_seconds' in r and r['latency_seconds'] > 0:
            latencies.append(r['latency_seconds'])
            
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
        "cache_misses": cache_misses,
        "latency_avg": float(np.mean(latencies)) if latencies else 0.0
    }

def main():
    print("Initializing LLM Provider and Retriever...")
    provider = LLMProvider()
    retriever = TFIDFRetriever()
    
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    dataset = load_threads(golden_path)
    prompt_template = load_prompt_template()
    
    with open(golden_path, "rb") as f:
        golden_hash = hashlib.sha256(f.read()).hexdigest()
        
    k_values = [1, 3, 5]
    all_metrics = {}
    
    for k in k_values:
        print(f"\nEvaluating RAG Baseline with K={k}...")
        results = []
        
        for i, r in enumerate(dataset):
            target_intent = r['intent_id']
            target_escalation = r['expected_behavior']['escalation']
            
            # Retrieve
            retrieved_docs = retriever.retrieve(r['conversation'], k=k)
            few_shot_str = format_few_shot(retrieved_docs)
            
            # Format conversation
            conv_str = json.dumps(r['conversation'], indent=2)
            
            # Build prompt
            prompt = prompt_template.replace("{few_shot_examples}", few_shot_str)
            prompt = prompt.replace("{conversation}", conv_str)
            
            start_time = time.time()
            pred = provider.predict(prompt)
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
                "_cache_hit": pred.get('_cache_hit', False)
            }
                    
            results.append(record)
            
            if (i+1) % 20 == 0:
                print(f"Processed {i+1}/{len(dataset)}")
                
        metrics = calculate_metrics(results)
        metrics['k'] = k
        all_metrics[k] = metrics
        
        # Save results for this K
        clean_results = [{k:v for k,v in res.items() if not k.startswith('_')} for res in results]
        
        with open(config.REPORTS_DIR / f"baseline_rag_k{k}_results.json", "w") as f:
            json.dump({"metrics": metrics, "predictions": clean_results}, f, indent=2)
            
    # Generate unified markdown report
    with open(config.REPORTS_DIR / "baseline_rag_results.md", "w") as f:
        f.write("# Step 6: RAG Baseline Evaluation\n\n")
        f.write("## Configuration\n")
        f.write(f"- **Provider**: {provider.provider} (Model: {provider.model})\n")
        f.write(f"- **Retriever**: TF-IDF\n")
        f.write(f"- **Golden Set Hash**: `{golden_hash}`\n\n")
        
        f.write("## Performance by K\n")
        f.write("| K | Intent Accuracy | Macro F1 | Escalation Accuracy | Cache Misses |\n")
        f.write("|---|-----------------|----------|---------------------|--------------|\n")
        
        for k in k_values:
            m = all_metrics[k]
            f.write(f"| {k} | {m['intent_accuracy']*100:.2f}% | {m['macro_f1']:.4f} | {m['escalation_accuracy']*100:.2f}% | {m['cache_misses']} |\n")

if __name__ == "__main__":
    main()
