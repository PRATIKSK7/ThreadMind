import json
from src.threadmind import config
from src.threadmind.baselines.tfidf_baseline import TfidfBaseline

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def extract_text(thread):
    return " ".join([m['text'].lower() for m in thread['messages'] if m['inbound']])

def main():
    train_path = config.PROCESSED_DATA_DIR / "train_split.jsonl"
    print(f"Loading training data from {train_path}...")
    train_threads = load_threads(train_path)
    
    # We need labels for the training set. Since we don't have human labels for the 65k training set, 
    # we use the same assignment logic as the rule baseline for training targets.
    # Note: This means the TF-IDF model is learning the heuristic rules, not human labels.
    from src.threadmind.baselines.rule_baseline import RuleBaseline
    rule_system = RuleBaseline()
    
    texts = []
    labels = []
    
    print("Extracting features and heuristically labeling training data for ML fit...")
    for th in train_threads:
        text = extract_text(th)
        if not text:
            continue
            
        conv = [{"author_role": "customer" if m['inbound'] else "brand", "text": m['text']} for m in th['messages']]
        pred = rule_system.predict(conv)
        label = pred['predicted_intent']
        
        # Only train on classified intents, skip 'other_support' to avoid a massive garbage class
        if label != "other_support":
            texts.append(text)
            labels.append(label)
            
    print(f"Training on {len(texts)} threads...")
    
    baseline = TfidfBaseline()
    baseline.train(texts, labels)
    
    # Save the model
    vec_path = config.PROCESSED_DATA_DIR / "tfidf_vectorizer.joblib"
    mod_path = config.PROCESSED_DATA_DIR / "tfidf_model.joblib"
    
    baseline.save(vec_path, mod_path)
    print("Training complete and models saved.")

if __name__ == "__main__":
    main()
