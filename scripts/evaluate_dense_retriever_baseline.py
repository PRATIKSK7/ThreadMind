#!/usr/bin/env python3
"""
Step 14a: Measure Dense FAISS Retrieval Baseline.

Evaluates the pre-trained all-MiniLM-L6-v2 Dense Retriever's Recall@K and MRR
using val_split.jsonl as the query set.

EVALUATION METHODOLOGY:
- Corpus indexed: 35,247 threads from retrieval_corpus.jsonl with non-other_support
  intents (as labeled by RuleBaseline). Stored in .cache/rag_dense/.
- Query set: val_split.jsonl threads that have non-other_support rule-baseline intents
  AND are present in the FAISS index.
- For each query, we retrieve K+1 nearest neighbors, then exclude the query thread
  itself (since val_split threads can appear in the index).
- A "hit" = at least one of the remaining K retrieved documents shares the same
  rule-baseline intent as the query.
- This measures the retriever's ability to find same-intent documents for unseen
  queries from the held-out validation split.

LEAKAGE PREVENTION:
- Golden Set threads are NOT in val_split (verified: 0 overlap).
- Golden Set threads are NOT in the FAISS index (verified: 0 overlap).
- Golden Set is NOT used as queries or targets in this evaluation.
"""

import json
import time
import pickle
import numpy as np
import faiss
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.threadmind import config
from src.threadmind.baselines.rule_baseline import RuleBaseline
from src.threadmind.rag.dense_retriever import DenseRetriever


def main():
    print("=" * 70)
    print("Step 14a: Dense FAISS Retrieval Baseline Measurement")
    print("=" * 70)

    # 1. Load Dense Retriever (existing pre-trained model + FAISS index)
    print("\n[1/6] Loading Dense Retriever...")
    retriever = DenseRetriever()
    
    # Load FAISS metadata to get thread_ids in the index
    with open(retriever.corpus_metadata_path, "rb") as f:
        corpus_metadata = pickle.load(f)
    faiss_thread_ids = {m["thread_id"]: i for i, m in enumerate(corpus_metadata)}
    print(f"  FAISS index: {len(corpus_metadata)} documents")
    print(f"  Model: {retriever.model_name}")
    
    # 2. Load val_split and label with rule baseline
    print("\n[2/6] Loading val_split.jsonl and labeling with RuleBaseline...")
    rule_system = RuleBaseline()
    
    val_queries = []
    val_total = 0
    val_other_support = 0
    val_not_in_faiss = 0
    
    with open(config.PROCESSED_DATA_DIR / "val_split.jsonl") as f:
        for line in f:
            val_total += 1
            thread = json.loads(line)
            tid = thread["thread_id"]
            
            # Label with rule baseline
            conv = []
            for m in thread["messages"]:
                is_inbound = m.get("inbound", True)
                conv.append({
                    "author_role": "customer" if is_inbound else "agent",
                    "text": m["text"]
                })
            
            pred = rule_system.predict(conv)
            intent = pred["predicted_intent"]
            
            if intent == "other_support":
                val_other_support += 1
                continue
            
            if tid not in faiss_thread_ids:
                val_not_in_faiss += 1
                continue
            
            val_queries.append({
                "thread_id": tid,
                "intent": intent,
                "conversation": thread["messages"],
                "faiss_idx": faiss_thread_ids[tid],
            })
    
    print(f"  val_split total: {val_total}")
    print(f"  Excluded (other_support): {val_other_support}")
    print(f"  Excluded (not in FAISS): {val_not_in_faiss}")
    print(f"  Evaluation queries: {len(val_queries)}")
    
    # 3. Verify Golden Set leakage
    print("\n[3/6] Verifying Golden Set leakage...")
    golden_ids = set()
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
        for line in f:
            golden_ids.add(json.loads(line)["thread_id"])
    
    query_ids = {q["thread_id"] for q in val_queries}
    leak_in_queries = golden_ids & query_ids
    leak_in_faiss = golden_ids & set(faiss_thread_ids.keys())
    print(f"  Golden IDs in query set: {len(leak_in_queries)}")
    print(f"  Golden IDs in FAISS index: {len(leak_in_faiss)}")
    assert len(leak_in_queries) == 0, "LEAKAGE: Golden Set threads found in query set!"
    assert len(leak_in_faiss) == 0, "LEAKAGE: Golden Set threads found in FAISS index!"
    print("  ✅ Zero leakage confirmed.")
    
    # 4. Run retrieval evaluation
    k_values = [1, 3, 5]
    max_k = max(k_values) + 1  # +1 to allow excluding self
    
    results = {k: {"hits": 0, "mrr_sum": 0.0} for k in k_values}
    per_intent = {}  # intent -> {k: {hits, total}}
    latencies = []
    self_excluded_count = 0
    
    print(f"\n[4/6] Evaluating {len(val_queries)} queries (K={k_values})...")
    
    for i, q in enumerate(val_queries):
        target_intent = q["intent"]
        
        # Initialize per-intent tracking
        if target_intent not in per_intent:
            per_intent[target_intent] = {
                k: {"hits": 0, "total": 0} for k in k_values
            }
        
        # Retrieve K+1 to allow self-exclusion
        t_start = time.time()
        retrieved = retriever.retrieve(q["conversation"], k=max_k)
        t_elapsed = time.time() - t_start
        latencies.append(t_elapsed)
        
        # Exclude self from results
        filtered = []
        for doc in retrieved:
            if doc["metadata"]["thread_id"] != q["thread_id"]:
                filtered.append(doc)
        
        if len(filtered) < len(retrieved):
            self_excluded_count += 1
        
        # Evaluate at each K
        for k in k_values:
            top_k = filtered[:k]
            hit = False
            reciprocal_rank = 0.0
            
            for rank, doc in enumerate(top_k):
                if doc["metadata"]["intent_id"] == target_intent:
                    hit = True
                    reciprocal_rank = 1.0 / (rank + 1)
                    break
            
            per_intent[target_intent][k]["total"] += 1
            
            if hit:
                results[k]["hits"] += 1
                results[k]["mrr_sum"] += reciprocal_rank
                per_intent[target_intent][k]["hits"] += 1
        
        if (i + 1) % 500 == 0:
            r3 = results[3]["hits"] / (i + 1)
            print(f"  {i+1}/{len(val_queries)} — Running Recall@3: {r3:.4f}")
    
    # 5. Compute final metrics
    n = len(val_queries)
    print(f"\n[5/6] Computing final metrics (N={n})...")
    
    print(f"\n{'='*70}")
    print(f"DENSE FAISS RETRIEVAL BASELINE (all-MiniLM-L6-v2)")
    print(f"{'='*70}")
    print(f"Evaluation queries: {n} (from val_split.jsonl)")
    print(f"FAISS indexed docs: {len(corpus_metadata)}")
    print(f"Self-excluded from results: {self_excluded_count}/{n}")
    print(f"Golden Set leakage: 0")
    print()
    
    metrics = {}
    print(f"{'K':<4} {'Recall@K':>10} {'MRR':>10} {'Hits':>8} {'Queries':>8}")
    print("-" * 44)
    for k in k_values:
        recall = results[k]["hits"] / n
        mrr = results[k]["mrr_sum"] / n
        print(f"{k:<4} {recall:>10.4f} {mrr:>10.4f} {results[k]['hits']:>8} {n:>8}")
        metrics[f"recall_at_{k}"] = round(recall, 4)
        metrics[f"mrr_at_{k}"] = round(mrr, 4)
        metrics[f"hits_at_{k}"] = results[k]["hits"]
    
    # Per-intent breakdown
    print(f"\n{'='*70}")
    print(f"PER-INTENT RETRIEVAL PERFORMANCE (Recall@3)")
    print(f"{'='*70}")
    print(f"{'Intent':<25} {'Recall@3':>10} {'Hits':>6} {'Total':>6}")
    print("-" * 50)
    intent_metrics = {}
    for intent in sorted(per_intent.keys()):
        d = per_intent[intent][3]
        r = d["hits"] / d["total"] if d["total"] > 0 else 0
        print(f"{intent:<25} {r:>10.4f} {d['hits']:>6} {d['total']:>6}")
        intent_metrics[intent] = {
            "recall_at_3": round(r, 4),
            "hits": d["hits"],
            "total": d["total"],
        }
    
    # Latency stats
    lat_arr = np.array(latencies)
    print(f"\n{'='*70}")
    print(f"LATENCY STATISTICS")
    print(f"{'='*70}")
    print(f"  Mean: {lat_arr.mean()*1000:.1f} ms")
    print(f"  Median: {np.median(lat_arr)*1000:.1f} ms")
    print(f"  P95: {np.percentile(lat_arr, 95)*1000:.1f} ms")
    print(f"  P99: {np.percentile(lat_arr, 99)*1000:.1f} ms")
    
    # 6. Save results
    print(f"\n[6/6] Saving results...")
    
    output = {
        "evaluation_metadata": {
            "date": "2026-09-12",
            "embedding_model": "all-MiniLM-L6-v2",
            "faiss_index_type": "IndexFlatIP (cosine similarity via L2-normalized inner product)",
            "faiss_indexed_documents": len(corpus_metadata),
            "query_source": "val_split.jsonl (non-other_support, present in FAISS index)",
            "evaluation_queries": n,
            "self_exclusion": True,
            "self_excluded_count": self_excluded_count,
            "golden_set_leakage": 0,
            "relevance_criterion": "Retrieved document shares same rule-baseline intent as query",
        },
        "metrics": metrics,
        "per_intent": intent_metrics,
        "latency_ms": {
            "mean": round(lat_arr.mean() * 1000, 1),
            "median": round(np.median(lat_arr) * 1000, 1),
            "p95": round(np.percentile(lat_arr, 95) * 1000, 1),
            "p99": round(np.percentile(lat_arr, 99) * 1000, 1),
        },
    }
    
    json_path = "reports/dense_retrieval_baseline.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved: {json_path}")
    
    print("\nDone.")


if __name__ == "__main__":
    main()
