import os
import sys
import json
from collections import Counter
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.threadmind import config
from src.threadmind.router.fallback_router import FallbackRouter
from src.threadmind.rag.dense_retriever import DenseRetriever

def load_golden():
    gs = []
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl", "r") as f:
        for line in f:
            gs.append(json.loads(line))
    return gs

def evaluate(y_true, y_pred, name):
    labels = sorted(list(set(y_true + y_pred)))
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    micro_f1 = f1_score(y_true, y_pred, average='micro', zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
    
    return {
        "name": name,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "micro_f1": micro_f1,
        "weighted_f1": weighted_f1,
        "precision": precision,
        "recall": recall
    }

def main():
    print("Evaluating Amazon Classifier...")
    gs = load_golden()
    y_true = [item['intent_id'] for item in gs]
    
    # 1. Majority Class Baseline
    majority_class = Counter(y_true).most_common(1)[0][0]
    y_pred_majority = [majority_class] * len(y_true)
    res_majority = evaluate(y_true, y_pred_majority, "Baseline 1: Majority Class")
    
    # 2. Simple Retrieval / Nearest-Example Baseline (Dense Retriever k=1)
    print("Running Nearest-Example Baseline...")
    retriever = DenseRetriever()
    y_pred_retrieval = []
    for item in gs:
        docs = retriever.retrieve(item["conversation"], k=1)
        if docs:
            y_pred_retrieval.append(docs[0]['metadata']['intent_id'])
        else:
            y_pred_retrieval.append("other_support")
            
    res_retrieval = evaluate(y_true, y_pred_retrieval, "Baseline 2: Nearest Example")
    
    # 3. ThreadMind V2 (Fallback Router)
    print("Running ThreadMind V2 Baseline...")
    router = FallbackRouter()
    y_pred_v2 = []
    for item in gs:
        res = router.predict(item["conversation"])
        y_pred_v2.append(res["predicted_intent"])
        
    res_v2 = evaluate(y_true, y_pred_v2, "Current System: ThreadMind V2")
    
    # Compute confusion matrix and worst intents for V2
    labels = sorted(list(set(y_true + y_pred_v2)))
    cm = confusion_matrix(y_true, y_pred_v2, labels=labels)
    
    per_intent_stats = {}
    for i, label in enumerate(labels):
        true_pos = cm[i, i]
        false_pos = sum(cm[:, i]) - true_pos
        false_neg = sum(cm[i, :]) - true_pos
        prec = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
        rec = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
        per_intent_stats[label] = {"precision": prec, "recall": rec, "f1": f1}
        
    sorted_worst = sorted(per_intent_stats.items(), key=lambda x: x[1]['f1'])
    worst_intents = [{"intent": k, "f1": v['f1']} for k, v in sorted_worst[:3]]
    
    # Confusion pairs
    confusions = []
    for i in range(len(labels)):
        for j in range(len(labels)):
            if i != j and cm[i, j] > 0:
                confusions.append({
                    "true": labels[i],
                    "predicted": labels[j],
                    "count": int(cm[i, j])
                })
    sorted_confusions = sorted(confusions, key=lambda x: x['count'], reverse=True)[:5]
    
    audit_md = f"""# Amazon Classifier Evaluation

## Overall Metrics
| System | Accuracy | Macro F1 | Micro F1 | Weighted F1 | Precision | Recall |
|--------|----------|----------|----------|-------------|-----------|--------|
| {res_majority['name']} | {res_majority['accuracy']:.4f} | {res_majority['macro_f1']:.4f} | {res_majority['micro_f1']:.4f} | {res_majority['weighted_f1']:.4f} | {res_majority['precision']:.4f} | {res_majority['recall']:.4f} |
| {res_retrieval['name']} | {res_retrieval['accuracy']:.4f} | {res_retrieval['macro_f1']:.4f} | {res_retrieval['micro_f1']:.4f} | {res_retrieval['weighted_f1']:.4f} | {res_retrieval['precision']:.4f} | {res_retrieval['recall']:.4f} |
| **{res_v2['name']}** | **{res_v2['accuracy']:.4f}** | **{res_v2['macro_f1']:.4f}** | **{res_v2['micro_f1']:.4f}** | **{res_v2['weighted_f1']:.4f}** | **{res_v2['precision']:.4f}** | **{res_v2['recall']:.4f}** |

## Per-Intent Performance (V2)
| Intent | Precision | Recall | F1 Score |
|--------|-----------|--------|----------|
"""
    for label in labels:
        stat = per_intent_stats[label]
        audit_md += f"| {label} | {stat['precision']:.4f} | {stat['recall']:.4f} | {stat['f1']:.4f} |\n"
        
    audit_md += "\n## Worst Performing Intents\n"
    for w in worst_intents:
        audit_md += f"- **{w['intent']}**: F1 = {w['f1']:.4f}\n"
        
    audit_md += "\n## Most Confused Intent Pairs\n"
    for c in sorted_confusions:
        audit_md += f"- True **{c['true']}** mispredicted as **{c['predicted']}** ({c['count']} times)\n"
        
    with open(config.REPORTS_DIR / "amazon_classifier_evaluation.md", "w") as f:
        f.write(audit_md)
        
    with open(config.REPORTS_DIR / "amazon_classifier_evaluation.json", "w") as f:
        json.dump({
            "majority": res_majority,
            "nearest_example": res_retrieval,
            "v2": res_v2,
            "worst_intents": worst_intents,
            "confusions": sorted_confusions,
            "per_intent": per_intent_stats
        }, f, indent=2)

    print("Classifier evaluation complete.")

if __name__ == "__main__":
    main()
