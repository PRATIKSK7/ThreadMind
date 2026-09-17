import json
from src.threadmind import config
from src.threadmind.baselines.rule_baseline import RuleBaseline

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def evaluate_baseline(baseline, dataset):
    results = []
    correct_intent = 0
    correct_escalation = 0
    abstentions = 0
    errors = 0
    
    for r in dataset:
        target_intent = r['intent_id']
        target_escalation = r['expected_behavior']['escalation']
        
        pred = baseline.predict(r['conversation'])
        pred['example_id'] = r['example_id']
        
        if pred['error']:
            errors += 1
        else:
            if pred['predicted_intent'] == target_intent:
                correct_intent += 1
            if pred['predicted_intent'] == "other_support":
                abstentions += 1
            if pred['predicted_escalation'] == target_escalation:
                correct_escalation += 1
                
        results.append(pred)
        
    total = len(dataset)
    metrics = {
        "total_examples": total,
        "intent_accuracy": correct_intent / total if total > 0 else 0,
        "escalation_accuracy": correct_escalation / total if total > 0 else 0,
        "abstention_rate": abstentions / total if total > 0 else 0,
        "error_rate": errors / total if total > 0 else 0
    }
    
    return results, metrics

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    print(f"Loading {golden_path}...")
    dataset = load_threads(golden_path)
    
    baseline = RuleBaseline()
    predictions, metrics = evaluate_baseline(baseline, dataset)
    
    print("Metrics:")
    print(json.dumps(metrics, indent=2))
    
    # Save Results
    with open(config.REPORTS_DIR / "baseline_rule_results.json", "w") as f:
        json.dump({"metrics": metrics, "predictions": predictions}, f, indent=2)
        
    with open(config.REPORTS_DIR / "baseline_rule_results.md", "w") as f:
        f.write("# Baseline 0: Rule System Evaluation\n\n")
        f.write("## Metrics\n")
        f.write(f"- **Intent Accuracy**: {metrics['intent_accuracy'] * 100:.2f}%\n")
        f.write(f"- **Escalation Accuracy**: {metrics['escalation_accuracy'] * 100:.2f}%\n")
        f.write(f"- **Abstention Rate**: {metrics['abstention_rate'] * 100:.2f}%\n")
        f.write(f"- **Error Rate**: {metrics['error_rate'] * 100:.2f}%\n")

if __name__ == "__main__":
    main()
