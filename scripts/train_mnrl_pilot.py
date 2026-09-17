import os
import sys
import json
import time
import torch
import numpy as np
from datasets import Dataset
from sentence_transformers import SentenceTransformer, losses

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config

def main():
    print("=" * 70)
    print("Step 14b: MNRL Pilot Training & Evaluation (FAST CPU CUSTOM LOOP)")
    print("=" * 70)
    
    device = "cpu"
    print(f"Device: {device}")
    
    # 1. Load Data
    print("\n[1/7] Loading training pairs from mnrl_train_dict.json...")
    with open(config.PROJECT_ROOT / ".cache" / "mnrl_train_dict.json", "r") as f:
        train_dict = json.load(f)
    print(f"  Loaded {len(train_dict['anchor'])} positive pairs for MNRL.")
    
    # 2. Train Model
    output_model_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl_pilot"
    os.makedirs(output_model_path, exist_ok=True)
    
    print("\n[2/7] Training MNRL Pilot Model...")
    model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    train_loss = losses.MultipleNegativesRankingLoss(model)
    train_loss.to(device)
    
    from torch.utils.data import DataLoader
    class DictDataset(torch.utils.data.Dataset):
        def __init__(self, data_dict):
            self.anchors = data_dict["anchor"]
            self.positives = data_dict["positive"]
        def __len__(self): return len(self.anchors)
        def __getitem__(self, idx):
            from sentence_transformers import InputExample
            return InputExample(texts=[self.anchors[idx], self.positives[idx]])
            
    train_dl = DataLoader(DictDataset(train_dict), shuffle=True, batch_size=32, collate_fn=model.smart_batching_collate)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    
    model.train()
    print(f"  Starting 1 epoch of training...")
    t0 = time.time()
    
    for i, batch in enumerate(train_dl):
        features, labels = batch
        for f in features:
            for key in f:
                f[key] = f[key].to(device)
                
        loss_val = train_loss(features, labels)
        loss_val.backward()
        optimizer.step()
        optimizer.zero_grad()
        
        if (i + 1) % 10 == 0:
            print(f"  Step {i+1}/{len(train_dl)} - Loss: {loss_val.item():.4f}")
            
    model.save_pretrained(str(output_model_path))
    
    print(f"  Training complete in {time.time()-t0:.1f}s.")
    print(f"  Saved to {output_model_path}")
    
    # 3. FAISS Re-indexing
    print("\n[3/7] Re-indexing FAISS corpus with Pilot model...")
    meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    import pickle
    with open(meta_path, "rb") as f:
        corpus_metadata = pickle.load(f)
        
    texts_to_encode = [m["conversation"] for m in corpus_metadata]
    print(f"  Encoding {len(texts_to_encode)} documents...")
    
    t0 = time.time()
    # For encoding, MPS is fine and fast! We will use MPS here!
    encode_device = "mps" if torch.backends.mps.is_available() else "cpu"
    encode_model = SentenceTransformer(str(output_model_path), device=encode_device)
    embeddings = encode_model.encode(texts_to_encode, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings).astype('float32')
    print(f"  Encoded in {time.time()-t0:.1f}s.")
    
    import faiss
    faiss.normalize_L2(embeddings)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    pilot_index_path = output_model_path / "faiss_index.bin"
    faiss.write_index(index, str(pilot_index_path))
    
    # 4. Load Eval Queries
    print("\n[4/7] Loading val_split queries for evaluation (from JSON cache)...")
    with open(config.PROJECT_ROOT / ".cache" / "val_queries.json", "r") as f:
        val_queries = json.load(f)
    print(f"  Evaluating {len(val_queries)} queries (same as baseline)...")
    
    # 5. Evaluate
    print("\n[5/7] Running Evaluation...")
    k_values = [1, 3, 5]
    max_k = 6
    
    results = {k: {"hits": 0, "mrr_sum": 0.0} for k in k_values}
    latencies = []
    per_intent = {}
    
    for i, q in enumerate(val_queries):
        target_intent = q["intent"]
        
        if target_intent not in per_intent:
            per_intent[target_intent] = {3: {"hits": 0, "total": 0}}
            
        t0 = time.time()
        q_emb = encode_model.encode([q["query_text"]])
        q_emb = np.array(q_emb).astype('float32')
        faiss.normalize_L2(q_emb)
        
        scores, indices = index.search(q_emb, max_k)
        latencies.append(time.time() - t0)
        
        filtered_docs = []
        for j in range(max_k):
            idx = indices[0][j]
            meta = corpus_metadata[idx]
            if meta["thread_id"] != q["thread_id"]:
                filtered_docs.append(meta)
                
        for k in k_values:
            top_k = filtered_docs[:k]
            hit = any(d["intent_id"] == target_intent for d in top_k)
            
            if hit:
                results[k]["hits"] += 1
                for rank, d in enumerate(top_k):
                    if d["intent_id"] == target_intent:
                        results[k]["mrr_sum"] += 1.0 / (rank + 1)
                        break
                        
            if k == 3:
                per_intent[target_intent][3]["total"] += 1
                if hit:
                    per_intent[target_intent][3]["hits"] += 1
                    
        if (i+1) % 1000 == 0:
            print(f"  {i+1}/{len(val_queries)}")
            
    # 6. Save Results
    print("\n[6/7] Computing final metrics...")
    n = len(val_queries)
    metrics = {}
    
    print(f"\n{'='*50}")
    print("MNRL PILOT EVALUATION RESULTS")
    print(f"{'='*50}")
    
    for k in k_values:
        recall = results[k]["hits"] / n
        mrr = results[k]["mrr_sum"] / n
        print(f"Recall@{k}: {recall:.4f}  |  MRR@{k}: {mrr:.4f}")
        metrics[f"recall_at_{k}"] = round(recall, 4)
        metrics[f"mrr_at_{k}"] = round(mrr, 4)
        
    lat_arr = np.array(latencies)
    print(f"Median latency: {np.median(lat_arr)*1000:.1f}ms")
    
    print(f"\n{'='*50}")
    print("BASELINE COMPARISON (from previous run)")
    print(f"{'='*50}")
    print("Recall@1: 0.5842")
    print("Recall@3: 0.8008")
    print("Recall@5: 0.8568")
    print("MRR@3:    0.6816")
    
    intent_metrics = {}
    for intent in sorted(per_intent.keys()):
        d = per_intent[intent][3]
        r = d["hits"] / d["total"] if d["total"] > 0 else 0
        intent_metrics[intent] = round(r, 4)
        
    output = {
        "pilot_hyperparameters": {
            "model": "all-MiniLM-L6-v2",
            "epochs": 1,
            "batch_size": 32,
            "loss": "MultipleNegativesRankingLoss",
            "training_pairs": len(train_dict["anchor"]),
        },
        "metrics": metrics,
        "latency_ms": {
            "median": round(np.median(lat_arr) * 1000, 1),
            "mean": round(lat_arr.mean() * 1000, 1)
        },
        "per_intent_recall_3": intent_metrics
    }
    
    out_path = "reports/dense_mnrl_pilot_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[7/7] Saved to {out_path}")
    print("Done.")

if __name__ == "__main__":
    main()
