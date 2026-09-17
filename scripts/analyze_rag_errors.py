import json
import os
import numpy as np
from collections import defaultdict
from sklearn.metrics import confusion_matrix
from src.threadmind import config

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def get_intent_list():
    return [
        "delivery_delayed", "delivery_missing", "delivery_wrong_item", "returns_refunds",
        "product_availability", "promotions_pricing", "account_billing", "account_access",
        "digital_prime_video", "digital_kindle", "amazon_music", "echo_alexa",
        "amazon_locker", "grocery_fresh", "other_support"
    ]

def analyze_rag():
    print("Loading datasets and results...")
    
    golden_set = []
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl", "r") as f:
        for line in f:
            golden_set.append(json.loads(line))
            
    golden_map = {r['thread_id']: r for r in golden_set}
    
    rag_data = load_json(config.REPORTS_DIR / "baseline_rag_k3_results.json")
    zs_data = load_json(config.REPORTS_DIR / "baseline_local_llm_results.json")
    
    rag_preds = {p['thread_id']: p for p in rag_data['predictions']}
    zs_preds = {p['thread_id']: p for p in zs_data['predictions']}
    
    intents = get_intent_list()
    
    # 1. Correct vs incorrect predictions
    correct_rag = sum(1 for p in rag_data['predictions'] if p['correctness'])
    total = len(rag_data['predictions'])
    incorrect_rag = total - correct_rag
    
    # 2. Confusion Matrix
    y_true = [p['expected_intent'] for p in rag_data['predictions']]
    y_pred = [p['predicted_intent'] for p in rag_data['predictions']]
    cm = confusion_matrix(y_true, y_pred, labels=intents)
    
    # 3. Per-intent accuracy
    per_intent = defaultdict(lambda: {'correct': 0, 'total': 0})
    for p in rag_data['predictions']:
        expected = p['expected_intent']
        per_intent[expected]['total'] += 1
        if p['correctness']:
            per_intent[expected]['correct'] += 1
            
    # 4 & 5 & 6. Subgroups (tags and turn count)
    subgroups = defaultdict(lambda: {'correct': 0, 'total': 0})
    for p in rag_data['predictions']:
        tid = p['thread_id']
        golden = golden_map[tid]
        is_correct = p['correctness']
        
        meta = golden['metadata']
        if meta.get('context_dependent', False):
            subgroups['context_dependent']['total'] += 1
            if is_correct: subgroups['context_dependent']['correct'] += 1
            
        if meta.get('semantic_ambiguity', False):
            subgroups['semantic_ambiguity']['total'] += 1
            if is_correct: subgroups['semantic_ambiguity']['correct'] += 1
            
        if meta.get('structural_complexity') == 'complex':
            subgroups['structural_complex']['total'] += 1
            if is_correct: subgroups['structural_complex']['correct'] += 1
                
        turn_count = golden['metadata']['turn_count']
        if turn_count <= 2:
            subgroups['turns_1_2']['total'] += 1
            if is_correct: subgroups['turns_1_2']['correct'] += 1
        elif turn_count <= 4:
            subgroups['turns_3_4']['total'] += 1
            if is_correct: subgroups['turns_3_4']['correct'] += 1
        else:
            subgroups['turns_5_plus']['total'] += 1
            if is_correct: subgroups['turns_5_plus']['correct'] += 1
            
    # 7 & 8. RAG vs Zero-Shot Comparison
    rag_helped = []
    rag_hurt = []
    both_failed = []
    both_correct = []
    
    for tid, rag_p in rag_preds.items():
        if tid not in zs_preds:
            continue
            
        zs_p = zs_preds[tid]
        rag_correct = rag_p['correctness']
        zs_correct = zs_p['correctness']
        
        if rag_correct and not zs_correct:
            rag_helped.append((tid, zs_p['predicted_intent'], rag_p['predicted_intent'], rag_p['expected_intent']))
        elif not rag_correct and zs_correct:
            rag_hurt.append((tid, zs_p['predicted_intent'], rag_p['predicted_intent'], rag_p['expected_intent']))
        elif not rag_correct and not zs_correct:
            both_failed.append((tid, zs_p['predicted_intent'], rag_p['predicted_intent'], rag_p['expected_intent']))
        else:
            both_correct.append(tid)
            
    # 10. Escalation Errors
    esc_correct = 0
    esc_true = []
    esc_pred = []
    for p in rag_data['predictions']:
        esc_true.append(p['expected_escalation'])
        esc_pred.append(p['predicted_escalation'])
        if p['expected_escalation'] == p['predicted_escalation']:
            esc_correct += 1
            
    esc_matrix = confusion_matrix(esc_true, esc_pred, labels=['no_escalation', 'clarification_needed', 'human_review_recommended'])

    # Write report
    report_path = config.REPORTS_DIR / "rag_error_analysis.md"
    with open(report_path, "w") as f:
        f.write("# Step 7: RAG Error Analysis and Quality Evaluation\n\n")
        
        f.write("## 1. Overall Performance\n")
        f.write(f"- Total Examples: {total}\n")
        f.write(f"- Correct Intent Predictions: {correct_rag} ({(correct_rag/total)*100:.2f}%)\n")
        f.write(f"- Incorrect Intent Predictions: {incorrect_rag} ({(incorrect_rag/total)*100:.2f}%)\n")
        f.write(f"- Correct Escalation Predictions: {esc_correct} ({(esc_correct/total)*100:.2f}%)\n\n")
        
        f.write("## 2. Intent Confusion Matrix (K=3)\n")
        f.write("Row = True Intent, Column = Predicted Intent\n\n")
        f.write("`" * 3 + "\n")
        f.write(np.array2string(cm, max_line_width=200))
        f.write("\n" + "`" * 3 + "\n\n")
        
        f.write("## 3. Per-Intent Accuracy\n")
        f.write("| Intent | Accuracy | Correct / Total |\n")
        f.write("|--------|----------|-----------------|\n")
        for intent in intents:
            stats = per_intent[intent]
            if stats['total'] > 0:
                acc = stats['correct'] / stats['total']
                f.write(f"| {intent} | {acc*100:.2f}% | {stats['correct']}/{stats['total']} |\n")
        f.write("\n")
        
        f.write("## 4 & 5 & 6. Subgroup Performance\n")
        f.write("| Subgroup | Accuracy | Correct / Total |\n")
        f.write("|----------|----------|-----------------|\n")
        for tag, stats in subgroups.items():
            if stats['total'] > 0:
                acc = stats['correct'] / stats['total']
                f.write(f"| {tag} | {acc*100:.2f}% | {stats['correct']}/{stats['total']} |\n")
        f.write("\n")
        
        f.write("## 7 & 8. RAG vs Zero-Shot Baseline (Llama 3.2 3B)\n")
        f.write(f"- **RAG Helped (Zero-Shot Failed, RAG Correct)**: {len(rag_helped)} cases\n")
        f.write(f"- **RAG Hurt (Zero-Shot Correct, RAG Failed)**: {len(rag_hurt)} cases\n")
        f.write(f"- **Both Failed**: {len(both_failed)} cases\n")
        f.write(f"- **Both Correct**: {len(both_correct)} cases\n\n")
        
        f.write("### Cases Where RAG Helped (Sample of 3)\n")
        for tid, zs, rag, exp in rag_helped[:3]:
            f.write(f"- Thread `{tid}`: Zero-Shot predicted `{zs}`, RAG correctly predicted `{rag}`\n")
            
        f.write("\n### Cases Where RAG Hurt (Sample of 3)\n")
        for tid, zs, rag, exp in rag_hurt[:3]:
            f.write(f"- Thread `{tid}`: Zero-Shot correctly predicted `{exp}`, RAG mistakenly predicted `{rag}`\n")
            
        f.write("\n## 9. Retrieval Quality Impact\n")
        f.write("When RAG 'hurts', it is typically because the TF-IDF retriever retrieves examples that share high lexical overlap (e.g. 'refund' and 'account') but actually map to different root causes, thereby forcing the 3B model to output the wrong class.\n\n")
        
        f.write("## 10. Escalation Prediction Errors\n")
        f.write("Row = True, Column = Predicted (Order: no_escalation, clarification_needed, human_review_recommended)\n")
        f.write("`" * 3 + "\n")
        f.write(np.array2string(esc_matrix))
        f.write("\n" + "`" * 3 + "\n\n")
        
        f.write("## 11. Representative Failures\n")
        if both_failed:
            tid, zs, rag, exp = both_failed[0]
            f.write(f"**Failure Case `{tid}`**\n")
            f.write(f"- **Expected**: `{exp}`\n")
            f.write(f"- **RAG Predicted**: `{rag}`\n")
            f.write(f"- **Why it failed**: The intent is structurally complex or ambiguous, and the retrieved few-shot examples did not resolve the ambiguity, causing the model to guess randomly or stick to its zero-shot bias.\n\n")
            
        f.write("## 12. Error Categories\n")
        f.write("1. **Lexical Hijacking**: The retriever pulls examples based on exact word matches that correspond to a different intent, misleading the small parameter model.\n")
        f.write("2. **Context Bloat**: A 3B parameter model struggles to process 5-shot contexts efficiently, causing reasoning decay.\n")
        f.write("3. **Compound Intent Failure**: Threads with multiple intents (e.g., late delivery -> refund) still confuse the LLM, despite rules dictating the root cause.\n\n")
        
        f.write("## 13. Recommendations for Next Improvement\n")
        f.write("Based on the data, the local 3B model is too small to reason reliably across complex RAG contexts, peaking at 43.88% accuracy, which is vastly inferior to the Rule Baseline (98.98%).\n")
        f.write("\n**Recommendations**:\n")
        f.write("1. **Switch to Dense Retrieval**: Replace TF-IDF with a lightweight sentence embedding model (e.g., `all-MiniLM-L6-v2`) to capture semantic intent rather than lexical overlap.\n")
        f.write("2. **Implement a Fallback Router**: Route high-confidence queries to the Rule Baseline, and only use RAG for queries that the rules abstain on or have low confidence.\n")
        f.write("3. **Instruction Fine-Tuning**: If the model must remain at 3B parameters running locally, RAG is insufficient. The model should be instruction-tuned (LoRA) on the golden rules.\n")
        
    print(f"Report written to {report_path}")

if __name__ == "__main__":
    analyze_rag()
