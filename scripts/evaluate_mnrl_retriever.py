import os
import sys
import json
import time
import pickle
import subprocess
import numpy as np

# Disable tokenizers parallelism
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config

def main():
    print("=" * 70)
    print("Step 14b: MNRL Model FAISS Indexing & Evaluation")
    print("=" * 70)
    
    output_model_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    if not output_model_path.exists():
        print("ERROR: Model not found at", output_model_path)
        sys.exit(1)
        
    print(f"Loading fine-tuned model from {output_model_path}...")
    
    encode_device = "cpu"
    print(f"Encode Device: {encode_device}")
    
    encode_model = SentenceTransformer(str(output_model_path), device=encode_device)
    
    print("\n[1/3] Encoding corpus with Fine-tuned model...")
    meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(meta_path, "rb") as f:
        corpus_metadata = pickle.load(f)
        
    texts_to_encode = [m["conversation"] for m in corpus_metadata]
    print(f"  Encoding {len(texts_to_encode)} documents...")
    
    t0 = time.time()
    embeddings = encode_model.encode(texts_to_encode, show_progress_bar=True, batch_size=32)
    embeddings = np.array(embeddings).astype('float32')
    print(f"  Encoded in {time.time()-t0:.1f}s.")
    
    # Save embeddings to disk so we can build FAISS index in a separate process
    emb_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl" / "embeddings.npy"
    np.save(emb_path, embeddings)
    
    print("\n[2/3] Building FAISS Index in isolated process...")
    faiss_script = """
import numpy as np
import faiss
import sys

emb_path = sys.argv[1]
index_path = sys.argv[2]

embeddings = np.load(emb_path)
faiss.normalize_L2(embeddings)
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)
faiss.write_index(index, index_path)
print("FAISS index built and saved successfully.")
"""
    builder_path = config.PROJECT_ROOT / ".cache" / "build_faiss.py"
    with open(builder_path, "w") as f:
        f.write(faiss_script)
        
    mnrl_index_path = output_model_path / "faiss_index.bin"
    
    # Run the isolated FAISS builder
    res = subprocess.run([sys.executable, str(builder_path), str(emb_path), str(mnrl_index_path)], capture_output=True, text=True)
    if res.returncode != 0:
        print("FAISS build failed!")
        print(res.stderr)
        sys.exit(1)
        
    print(res.stdout)
    print(f"  Saved FAISS index to {mnrl_index_path}")
    
    print("\n[3/3] Loading val_queries for evaluation...")
    with open(config.PROJECT_ROOT / ".cache" / "val_queries.json", "r") as f:
        val_queries = json.load(f)
    print(f"  Evaluating {len(val_queries)} queries...")
    
    # Load the index now (safe because encoding is done and we just do single queries)
    import faiss
    index = faiss.read_index(str(mnrl_index_path))
    
    k_values = [1, 3, 5]
    max_k = max(k_values)
    
    results = {k: {"hits": 0, "mrr_sum": 0.0} for k in k_values}
    latencies = []
    
    for i, q in enumerate(val_queries):
        target_intent = q["intent"]
        
        t0_search = time.time()
        q_emb = encode_model.encode([q["query_text"]])
        q_emb = np.array(q_emb).astype('float32')
        faiss.normalize_L2(q_emb)
        
        scores, indices = index.search(q_emb, max_k + 1)
        latencies.append(time.time() - t0_search)
        
        filtered_docs = []
        for j in range(max_k + 1):
            if len(filtered_docs) == max_k:
                break
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
                        
        if (i+1) % 1000 == 0:
            print(f"  Processed {i+1}/{len(val_queries)}")
            
    print("\nComputing final metrics...")
    n = len(val_queries)
    metrics = {}
    
    print(f"\n{'='*50}")
    print("MNRL EVALUATION RESULTS")
    print(f"{'='*50}")
    
    for k in k_values:
        recall = results[k]["hits"] / n
        mrr = results[k]["mrr_sum"] / n
        print(f"Recall@{k}: {recall:.4f}  |  MRR@{k}: {mrr:.4f}")
        metrics[f"recall_at_{k}"] = round(recall, 4)
        metrics[f"mrr_at_{k}"] = round(mrr, 4)
        
    lat_arr = np.array(latencies)
    print(f"Median latency: {np.median(lat_arr)*1000:.1f}ms")
    print(f"Mean latency: {lat_arr.mean()*1000:.1f}ms")
    
    print(f"\n{'='*50}")
    print("BASELINE COMPARISON (from Step 14a)")
    print(f"{'='*50}")
    print("Recall@1: 0.5842")
    print("Recall@3: 0.8008")
    print("Recall@5: 0.8568")
    print("MRR@3:    0.6816")
    
    output = {
        "hyperparameters": {
            "model": "rag_dense_mnrl",
            "epochs": 3,
            "loss": "MultipleNegativesRankingLoss",
            "training_pairs": 4457,
        },
        "metrics": metrics,
        "latency_ms": {
            "median": round(np.median(lat_arr) * 1000, 1),
            "mean": round(lat_arr.mean() * 1000, 1)
        }
    }
    
    out_path = config.PROJECT_ROOT / "reports" / "dense_retrieval_mnrl_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {out_path}")
    print("Done.")

if __name__ == "__main__":
    main()
