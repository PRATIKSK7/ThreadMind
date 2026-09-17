import json
import time
import hashlib
import numpy as np
from collections import defaultdict
from sklearn.metrics import f1_score, precision_recall_fscore_support, confusion_matrix
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def load_prompt_template():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "intent_classification_v1.txt"
    with open(prompt_path, "r") as f:
        return f.read()

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
    
    # Subgroup tracking
    subgroups = {
        'context_dependent': {'correct': 0, 'total': 0},
        'semantic_ambiguity': {'correct': 0, 'total': 0},
        'structural_complex': {'correct': 0, 'total': 0},
        'hard_ambiguous': {'correct': 0, 'total': 0},
        'multi_turn': {'correct': 0, 'total': 0},
        'turns_1_2': {'correct': 0, 'total': 0},
        'turns_3_4': {'correct': 0, 'total': 0},
        'turns_5_plus': {'correct': 0, 'total': 0}
    }
    
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
        
        is_correct = r['predicted_intent'] == r['expected_intent']
        
        # Subgroup analysis
        meta = r.get('_metadata', {})
        diff = r.get('_difficulty', 'easy')
        turn_count = r.get('_turn_count', 0)
        
        if meta.get('context_dependent'):
            subgroups['context_dependent']['total'] += 1
            if is_correct: subgroups['context_dependent']['correct'] += 1
            
        if meta.get('semantic_ambiguity'):
            subgroups['semantic_ambiguity']['total'] += 1
            if is_correct: subgroups['semantic_ambiguity']['correct'] += 1
            
        if meta.get('structural_complexity') in ['branched', 'incomplete']:
            subgroups['structural_complex']['total'] += 1
            if is_correct: subgroups['structural_complex']['correct'] += 1
            
        if diff in ['hard', 'ambiguous']:
            subgroups['hard_ambiguous']['total'] += 1
            if is_correct: subgroups['hard_ambiguous']['correct'] += 1
            
        if turn_count >= 3:
            subgroups['multi_turn']['total'] += 1
            if is_correct: subgroups['multi_turn']['correct'] += 1
            
        if turn_count in [1, 2]:
            subgroups['turns_1_2']['total'] += 1
            if is_correct: subgroups['turns_1_2']['correct'] += 1
        elif turn_count in [3, 4]:
            subgroups['turns_3_4']['total'] += 1
            if is_correct: subgroups['turns_3_4']['correct'] += 1
        elif turn_count >= 5:
            subgroups['turns_5_plus']['total'] += 1
            if is_correct: subgroups['turns_5_plus']['correct'] += 1

    intent_acc = sum([1 for t, p in zip(intents_true, intents_pred) if t == p]) / len(intents_true) if intents_true else 0
    escalation_acc = sum([1 for t, p in zip(escalation_true, escalation_pred) if t == p]) / len(escalation_true) if escalation_true else 0
    macro_f1 = f1_score(intents_true, intents_pred, average='macro', zero_division=0) if intents_true else 0
    
    unique_intents = sorted(list(set(intents_true + intents_pred)))
    unique_escalations = sorted(list(set(escalation_true + escalation_pred)))
    
    intent_cm = confusion_matrix(intents_true, intents_pred, labels=unique_intents).tolist() if intents_true else []
    escalation_cm = confusion_matrix(escalation_true, escalation_pred, labels=unique_escalations).tolist() if escalation_true else []
    
    p, r, f, s = precision_recall_fscore_support(intents_true, intents_pred, labels=unique_intents, zero_division=0) if intents_true else ([], [], [], [])
    
    per_intent = {}
    for i, intent in enumerate(unique_intents):
        per_intent[intent] = {
            "precision": float(p[i]),
            "recall": float(r[i]),
            "f1": float(f[i]),
            "support": int(s[i])
        }

    return {
        "intent_accuracy": intent_acc,
        "macro_f1": macro_f1,
        "escalation_accuracy": escalation_acc,
        "api_failures": api_failures,
        "malformed_responses": malformed,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "latency_avg": float(np.mean(latencies)) if latencies else 0.0,
        "latency_median": float(np.median(latencies)) if latencies else 0.0,
        "per_intent_metrics": per_intent,
        "confusion_matrices": {
            "intent_labels": unique_intents,
            "intent_matrix": intent_cm,
            "escalation_labels": unique_escalations,
            "escalation_matrix": escalation_cm
        },
        "subgroups": subgroups
    }

def main():
    print("Initializing LLM Provider...")
    try:
        provider = LLMProvider()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return
        
    print(f"Verifying model availability: {provider.model} via {provider.provider}")
    try:
        provider.verify_model_availability()
    except Exception as e:
        print(f"Model Availability Error: {e}")
        print("\nSTOPPING execution as per user requirements (do not silently substitute models).")
        return
        
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    print(f"Loading {golden_path}...")
    dataset = load_threads(golden_path)
    prompt_template = load_prompt_template()
    
    # Hash check to verify Golden Set is unchanged
    with open(golden_path, "rb") as f:
        golden_hash = hashlib.sha256(f.read()).hexdigest()
    
    results = []
    
    print("Evaluating Golden Set with LLM Zero-Shot Baseline...")
    
    for i, r in enumerate(dataset):
        target_intent = r['intent_id']
        target_escalation = r['expected_behavior']['escalation']
        
        # Format conversation
        conv_str = json.dumps(r['conversation'], indent=2)
        prompt = prompt_template.replace("{conversation}", conv_str)
        
        start_time = time.time()
        pred = provider.predict(prompt)
        latency = time.time() - start_time
        
        # We don't want to log latency for cache hits because it's virtually 0
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
            "model_identifier": provider.model,
            "prompt_version": "v1",
            "error": pred.get('error'),
            "reasoning_summary": pred.get('reasoning_summary'),
            "_cache_hit": pred.get('_cache_hit', False),
            "_metadata": r.get('metadata', {}),
            "_difficulty": r.get('difficulty'),
            "_turn_count": len(r['conversation'])
        }
                
        results.append(record)
        
        if (i+1) % 20 == 0:
            print(f"Processed {i+1}/{len(dataset)}")
            
    metrics = calculate_metrics(results)
    metrics['golden_set_hash'] = golden_hash
    metrics['total_examples'] = len(dataset)
    
    print("Metrics:")
    print(json.dumps(metrics, indent=2))
    
    # Exclude temporary private metadata keys from final json dump
    clean_results = []
    for res in results:
        clean = {k:v for k,v in res.items() if not k.startswith('_')}
        clean_results.append(clean)
    
    if provider.provider == "ollama":
        results_prefix = "baseline_local_llm_results"
    else:
        results_prefix = "baseline_llm_results"
        
    with open(config.REPORTS_DIR / f"{results_prefix}.json", "w") as f:
        json.dump({"metrics": metrics, "predictions": clean_results}, f, indent=2)
        
    with open(config.REPORTS_DIR / f"{results_prefix}.md", "w") as f:
        f.write("# Baseline 2: LLM Zero-Shot Evaluation\n\n")
        f.write("## Configuration\n")
        f.write(f"- **Provider**: {provider.provider}\n")
        f.write(f"- **Model**: {provider.model}\n")
        f.write(f"- **Prompt Version**: v1\n")
        f.write(f"- **Golden Set Hash**: `{golden_hash}`\n\n")
        
        f.write("## System Metrics\n")
        f.write(f"- **API Failures**: {metrics['api_failures']}\n")
        f.write(f"- **Malformed Responses**: {metrics['malformed_responses']}\n")
        f.write(f"- **Cache Hits**: {metrics['cache_hits']}\n")
        f.write(f"- **Cache Misses**: {metrics['cache_misses']}\n")
        if metrics['cache_misses'] > 0:
            f.write(f"- **Avg Latency (Misses)**: {metrics['latency_avg']:.2f}s\n")
            f.write(f"- **Median Latency (Misses)**: {metrics['latency_median']:.2f}s\n\n")
            
        f.write("## Performance Metrics\n")
        f.write(f"- **Intent Accuracy**: {metrics['intent_accuracy'] * 100:.2f}%\n")
        f.write(f"- **Intent Macro F1**: {metrics['macro_f1']:.4f}\n")
        f.write(f"- **Escalation Accuracy**: {metrics['escalation_accuracy'] * 100:.2f}%\n\n")
        
        f.write("## Subgroup Analysis\n")
        f.write("| Subgroup | Total | Correct | Accuracy |\n")
        f.write("|----------|-------|---------|----------|\n")
        for sg, data in metrics['subgroups'].items():
            if data['total'] > 0:
                acc = data['correct'] / data['total']
                f.write(f"| {sg} | {data['total']} | {data['correct']} | {acc*100:.2f}% |\n")
        
        f.write("\n## Per-Intent Metrics\n")
        f.write("| Intent | Precision | Recall | F1 | Support |\n")
        f.write("|--------|-----------|--------|----|---------|\n")
        for intent, data in metrics['per_intent_metrics'].items():
            f.write(f"| {intent} | {data['precision']:.4f} | {data['recall']:.4f} | {data['f1']:.4f} | {data['support']} |\n")

if __name__ == "__main__":
    main()
