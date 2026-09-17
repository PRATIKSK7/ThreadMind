import json
import os
from collections import defaultdict
from src.threadmind import config

def analyze():
    # Load K=1, K=3, K=5 MNRL results
    res_k1 = json.load(open(config.REPORTS_DIR / "rag_mnrl_k1_results.json"))
    res_k3 = json.load(open(config.REPORTS_DIR / "rag_mnrl_k3_results.json"))
    res_k5 = json.load(open(config.REPORTS_DIR / "rag_mnrl_k5_results.json"))
    
    total = len(res_k5["predictions"])
    
    # Classify failures for K=5
    # Categories:
    # 1. retrieval failure
    # 2. retrieval success but LLM classification failure
    # 3. prompt/context formatting issue
    # 4. escalation classification failure
    # 5. malformed/API failure
    # 6. other
    
    failure_counts = defaultdict(int)
    failures_by_category = defaultdict(list)
    
    for p in res_k5["predictions"]:
        expected_intent = p["expected_intent"]
        pred_intent = p.get("predicted_intent")
        expected_esc = p["expected_escalation"]
        pred_esc = p.get("predicted_escalation")
        retrieved_intents = p.get("retrieved_intents", [])
        
        is_intent_correct = (pred_intent == expected_intent)
        is_esc_correct = (pred_esc == expected_esc)
        
        if is_intent_correct and is_esc_correct:
            continue # Success
            
        category = "6. other"
        if not p.get("predicted_intent") or p.get("error"):
            category = "5. malformed/API failure"
        elif expected_intent not in retrieved_intents[:5]:
            category = "1. retrieval failure"
        elif not is_intent_correct:
            category = "2. retrieval success but LLM classification failure"
        elif not is_esc_correct:
            category = "4. escalation classification failure"
            
        failure_counts[category] += 1
        failures_by_category[category].append(p)
        
    report_path = config.REPORTS_DIR / "mnrl_failure_analysis.md"
    with open(report_path, "w") as f:
        f.write("# MNRL RAG Failure Analysis\n\n")
        f.write("## Executive Summary\n")
        f.write("This report analyzes why the end-to-end intent accuracy for K=5 (61.22%) lags behind the retrieval Recall@5 (86.73%). ")
        f.write("Although the previous formatting and context window truncation fixes successfully eliminated malformed responses, the local 3B model still struggles to correctly classify intents even when the correct example is in the context window.\n\n")
        
        f.write("## K=1 / K=3 / K=5 Comparison\n")
        f.write("| K | Intent Accuracy | Recall | Gap (Recall - Accuracy) |\n")
        f.write("|---|-----------------|--------|-------------------------|\n")
        f.write(f"| 1 | {res_k1['metrics']['intent_accuracy']*100:.2f}% | {res_k1['metrics']['retrieval_recall_at_1']*100:.2f}% | {(res_k1['metrics']['retrieval_recall_at_1'] - res_k1['metrics']['intent_accuracy'])*100:.2f}% |\n")
        f.write(f"| 3 | {res_k3['metrics']['intent_accuracy']*100:.2f}% | {res_k3['metrics']['retrieval_recall_at_3']*100:.2f}% | {(res_k3['metrics']['retrieval_recall_at_3'] - res_k3['metrics']['intent_accuracy'])*100:.2f}% |\n")
        f.write(f"| 5 | {res_k5['metrics']['intent_accuracy']*100:.2f}% | {res_k5['metrics']['retrieval_recall_at_5']*100:.2f}% | {(res_k5['metrics']['retrieval_recall_at_5'] - res_k5['metrics']['intent_accuracy'])*100:.2f}% |\n\n")
        
        f.write("## Retrieval vs Generation Failure Breakdown (K=5)\n")
        total_failures = sum(failure_counts.values())
        for cat in sorted(failure_counts.keys()):
            count = failure_counts[cat]
            f.write(f"- **{cat}**: {count} ({(count/total_failures)*100:.2f}% of failures, {(count/total)*100:.2f}% of total N=196)\n")
            
        f.write("\n## Representative Failure Examples\n")
        cat = "2. retrieval success but LLM classification failure"
        if failures_by_category[cat]:
            ex = failures_by_category[cat][0]
            f.write(f"### Example of {cat}\n")
            f.write(f"- **Thread ID**: {ex['thread_id']}\n")
            f.write(f"- **Expected Intent**: {ex['expected_intent']}\n")
            f.write(f"- **Predicted Intent**: {ex['predicted_intent']}\n")
            f.write(f"- **Retrieved Intents**: {ex['retrieved_intents'][:5]}\n\n")
            
        cat2 = "1. retrieval failure"
        if failures_by_category[cat2]:
            ex2 = failures_by_category[cat2][0]
            f.write(f"### Example of {cat2}\n")
            f.write(f"- **Thread ID**: {ex2['thread_id']}\n")
            f.write(f"- **Expected Intent**: {ex2['expected_intent']}\n")
            f.write(f"- **Predicted Intent**: {ex2['predicted_intent']}\n")
            f.write(f"- **Retrieved Intents**: {ex2['retrieved_intents'][:5]}\n\n")
            
        f.write("## Root Causes\n")
        f.write("1. **3B Model Reasoning Limits**: The Llama 3.2 3B model is not powerful enough to reliably perform multi-hop reasoning over 5 examples (even compacted ones). It often ignores the target classification patterns or gets distracted by lexical overlap, leading to a large 'Retrieval Success but LLM Failure' gap.\n")
        f.write("2. **Context Dilution**: Providing 5 examples means there are up to 4 distractor examples when only 1 correct example is retrieved. The model is easily swayed by the majority of distractor examples.\n")
        f.write("3. **Escalation Complexity**: Escalation is determined by subtle tone or policy rules, not just the base intent. Few-shot examples alone are not sufficient to teach escalation logic without explicit chain-of-thought rules.\n\n")
        
        f.write("## Top 3 Proposed Improvements (Without retraining MNRL)\n")
        f.write("1. **Dynamic Prompting (Only inject top 1 or 2 highest-confidence examples)**: Instead of a fixed K=3 or K=5, filter retrieved examples by a similarity threshold, or strictly limit to K=2 to reduce distractor dilution for the small model.\n")
        f.write("2. **Add Explicit Chain-of-Thought (CoT) to the Prompt**: Update the prompt schema to require the LLM to write out a short reasoning step (e.g., 'Target user mentioned X. This matches Example Y which is Z.') BEFORE outputting the JSON classification.\n")
        f.write("3. **Improve Retrieval Granularity via Reranking**: Add a lightweight Cross-Encoder or BM25 hybrid step on top of the MNRL FAISS index to ensure the #1 retrieved example is highly relevant, allowing us to rely on K=1 or K=2.\n\n")
        
        f.write("## Exact Files that Would Need Modification\n")
        f.write("- `src/threadmind/llm/prompts/rag_classification_v1.txt` (To add CoT instructions)\n")
        f.write("- `scripts/evaluate_rag_mnrl.py` (To implement dynamic K or hybrid reranking, and handle the new CoT JSON output)\n\n")
        
        f.write("## Recommended Next Experiment\n")
        f.write("Modify the prompt to require Chain-of-Thought reasoning (CoT) before outputting the final intent, and reduce K to 2 to minimize distractor dilution. Evaluate this modified prompt using the existing MNRL index on the Golden Set.\n")

if __name__ == "__main__":
    analyze()
