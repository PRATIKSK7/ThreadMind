import json
from src.threadmind import config
from src.threadmind.baselines.tfidf_baseline import TfidfBaseline
import os

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def evaluate_baseline(baseline, dataset):
    results = []
    correct_intent = 0
    abstentions = 0
    errors = 0
    
    for r in dataset:
        target_intent = r['intent_id']
        
        pred = baseline.predict(r['conversation'])
        pred['example_id'] = r['example_id']
        
        if pred['error']:
            errors += 1
        else:
            if pred['predicted_intent'] == target_intent:
                correct_intent += 1
            if pred['predicted_intent'] == "other_support":
                abstentions += 1
                
        results.append(pred)
        
    total = len(dataset)
    metrics = {
        "total_examples": total,
        "intent_accuracy": correct_intent / total if total > 0 else 0,
        "abstention_rate": abstentions / total if total > 0 else 0,
        "error_rate": errors / total if total > 0 else 0
    }
    
    return results, metrics

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    vec_path = config.PROCESSED_DATA_DIR / "tfidf_vectorizer.joblib"
    mod_path = config.PROCESSED_DATA_DIR / "tfidf_model.joblib"
    
    if not os.path.exists(vec_path) or not os.path.exists(mod_path):
        print("Models not found. Run train_tfidf_baseline.py first.")
        return
        
    print(f"Loading {golden_path}...")
    dataset = load_threads(golden_path)
    
    print("Loading TF-IDF model...")
    baseline = TfidfBaseline(vectorizer_path=vec_path, model_path=mod_path)
    
    print("Evaluating...")
    predictions, metrics = evaluate_baseline(baseline, dataset)
    
    print("Metrics:")
    print(json.dumps(metrics, indent=2))
    
    # Save Results
    with open(config.REPORTS_DIR / "baseline_tfidf_results.json", "w") as f:
        json.dump({"metrics": metrics, "predictions": predictions}, f, indent=2)
        
    with open(config.REPORTS_DIR / "baseline_tfidf_results.md", "w") as f:
        f.write("# Baseline 1: TF-IDF Evaluation\n\n")
        f.write("## Metrics\n")
        f.write(f"- **Intent Accuracy**: {metrics['intent_accuracy'] * 100:.2f}%\n")
        f.write(f"- **Abstention Rate**: {metrics['abstention_rate'] * 100:.2f}%\n")
        f.write(f"- **Error Rate**: {metrics['error_rate'] * 100:.2f}%\n")

if __name__ == "__main__":
    main()
