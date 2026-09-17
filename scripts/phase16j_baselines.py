import os
import sys
import json
from collections import Counter
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.threadmind import config
from src.threadmind.rag.dense_retriever import DenseRetriever
from src.threadmind.router.fallback_router import FallbackRouter

def load_golden():
    gs = []
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl", "r") as f:
        for line in f:
            gs.append(json.loads(line))
    return gs

def compute_metrics(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "micro_f1": f1_score(y_true, y_pred, average="micro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0)
    }

def main():
    print("Running Phase 16J Baseline Evaluation...")
    gs = load_golden()
    
    y_true = [item["intent_id"] for item in gs]
    
    # 1. Majority Classifier
    # We find the majority class in the Golden Set (or training set, but for baselines we can just use training split stats if needed. 
    # Let's check training split).
    train_intents = []
    with open(config.PROCESSED_DATA_DIR / "train_split.jsonl", "r") as f:
        for line in f:
            d = json.loads(line)
            # Find intent somehow... in train_split it's not directly labeled in the root usually?
            # Actually train_split comes from the original dataset which didn't have intents! 
            # So the rule-based intent was used. Let's just use the majority class of the Golden Set.
            pass
            
    majority_class = Counter(y_true).most_common(1)[0][0]
    print(f"Majority Class: {majority_class}")
    
    y_pred_majority = [majority_class] * len(y_true)
    metrics_majority = compute_metrics(y_true, y_pred_majority)
    
    # 2. Simple Nearest-Example (Dense Retriever top-1)
    retriever = DenseRetriever()
    y_pred_nearest = []
    for item in gs:
        conv = item["conversation"]
        docs = retriever.retrieve(conv, k=1)
        if docs:
            y_pred_nearest.append(docs[0]["metadata"]["intent_id"])
        else:
            y_pred_nearest.append("other_support")
            
    metrics_nearest = compute_metrics(y_true, y_pred_nearest)
    
    # 3. ThreadMind V2 (FallbackRouter)
    router = FallbackRouter()
    y_pred_v2 = []
    for item in gs:
        conv = item["conversation"]
        res = router.predict(conv)
        y_pred_v2.append(res["predicted_intent"])
        
    metrics_v2 = compute_metrics(y_true, y_pred_v2)
    
    report_md = f"""# Phase 16J Baselines Evaluation

## Dataset
- Golden Set Size: {len(gs)} examples
- Majority Class: {majority_class}

## Comparison Table

| Metric | Baseline 1: Majority | Baseline 2: Nearest Example | Current: ThreadMind V2 |
|--------|----------------------|-----------------------------|------------------------|
| Accuracy | {metrics_majority['accuracy']:.4f} | {metrics_nearest['accuracy']:.4f} | {metrics_v2['accuracy']:.4f} |
| Macro F1 | {metrics_majority['macro_f1']:.4f} | {metrics_nearest['macro_f1']:.4f} | {metrics_v2['macro_f1']:.4f} |
| Micro F1 | {metrics_majority['micro_f1']:.4f} | {metrics_nearest['micro_f1']:.4f} | {metrics_v2['micro_f1']:.4f} |
| Weighted F1 | {metrics_majority['weighted_f1']:.4f} | {metrics_nearest['weighted_f1']:.4f} | {metrics_v2['weighted_f1']:.4f} |
| Precision (Macro) | {metrics_majority['precision_macro']:.4f} | {metrics_nearest['precision_macro']:.4f} | {metrics_v2['precision_macro']:.4f} |
| Recall (Macro) | {metrics_majority['recall_macro']:.4f} | {metrics_nearest['recall_macro']:.4f} | {metrics_v2['recall_macro']:.4f} |
"""
    
    with open(config.REPORTS_DIR / "phase16j_baselines.md", "w") as f:
        f.write(report_md)
        
    with open(config.REPORTS_DIR / "phase16j_baselines.json", "w") as f:
        json.dump({
            "majority": metrics_majority,
            "nearest_example": metrics_nearest,
            "v2": metrics_v2
        }, f, indent=2)
        
    print("Baseline evaluation complete.")
    print(report_md)

if __name__ == "__main__":
    main()
