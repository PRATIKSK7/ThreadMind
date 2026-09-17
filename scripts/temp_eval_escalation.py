import json
from sklearn.metrics import precision_recall_fscore_support

def main():
    with open("reports/baseline_router_results.json", "r") as f:
        data = json.load(f)
        
    y_true = [p["expected_escalation"] for p in data["predictions"]]
    y_pred = [p["predicted_escalation"] if p.get("predicted_escalation") else "no_escalation" for p in data["predictions"]]
    
    # We want metrics for each class
    labels = ["no_escalation", "clarification_needed", "human_review_recommended"]
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    
    for i, label in enumerate(labels):
        print(f"{label}: Precision={p[i]:.4f}, Recall={r[i]:.4f}")

if __name__ == "__main__":
    main()
