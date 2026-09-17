import json
import numpy as np
from src.threadmind import config
from src.threadmind.rag.tfidf_retriever import TFIDFRetriever
from src.threadmind.rag.dense_retriever import DenseRetriever

def load_golden_set():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    threads = []
    with open(golden_path, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def run_retriever_eval(retriever, dataset, name, k_values):
    print(f"\nEvaluating {name}...")
    results = {k: {"hits": 0, "mrr_sum": 0.0} for k in k_values}
    
    for i, r in enumerate(dataset):
        target_intent = r['intent_id']
        conversation = r['conversation']
        
        max_k = max(k_values)
        retrieved = retriever.retrieve(conversation, k=max_k)
        
        # Calculate hits and MRR for each k
        for k in k_values:
            top_k_docs = retrieved[:k]
            hit = False
            reciprocal_rank = 0.0
            
            for rank, doc in enumerate(top_k_docs):
                if doc["metadata"]["intent_id"] == target_intent:
                    hit = True
                    reciprocal_rank = 1.0 / (rank + 1)
                    break
                    
            if hit:
                results[k]["hits"] += 1
                results[k]["mrr_sum"] += reciprocal_rank
                
        if (i+1) % 50 == 0:
            print(f"Processed {i+1}/{len(dataset)}")
            
    print(f"\n--- {name} Evaluation Results ---")
    for k in k_values:
        recall = results[k]["hits"] / len(dataset)
        mrr = results[k]["mrr_sum"] / len(dataset)
        print(f"K={k}: Recall@{k} = {recall:.4f}, MRR = {mrr:.4f}")

def evaluate_retriever(k_values=[1, 3, 5]):
    dataset = load_golden_set()
    print(f"Loaded {len(dataset)} Golden Set examples for retriever evaluation.")
    
    # We can skip TF-IDF evaluation here since we already have the metrics,
    # but we'll leave it in for completeness if the user wants to re-run it.
    
    print("Initializing Dense Retriever (this will build the FAISS index on first run)...")
    dense_retriever = DenseRetriever()
    run_retriever_eval(dense_retriever, dataset, "Dense Retriever (all-MiniLM-L6-v2)", k_values)

if __name__ == "__main__":
    evaluate_retriever()
