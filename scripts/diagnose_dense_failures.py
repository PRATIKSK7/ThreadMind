#!/usr/bin/env python3
"""
Step 14b Part 1: Dense Retrieval Failure Diagnosis.

Analyzes the 5,000 val_split queries to identify:
- Which queries fail at K=3 and why
- Per-intent Recall@1/3/5
- Failure mode classification (rare intent, ambiguity, short query, etc.)
- Examples of successful vs failed retrievals
"""

import json
import pickle
import time
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.threadmind import config
from src.threadmind.baselines.rule_baseline import RuleBaseline
from src.threadmind.rag.dense_retriever import DenseRetriever


def main():
    print("=" * 70)
    print("Step 14b: Dense Retrieval Failure Diagnosis")
    print("=" * 70)

    # 1. Load components
    print("\n[1/5] Loading Dense Retriever...")
    retriever = DenseRetriever()
    
    with open(retriever.corpus_metadata_path, "rb") as f:
        corpus_metadata = pickle.load(f)
    faiss_thread_ids = {m["thread_id"]: i for i, m in enumerate(corpus_metadata)}
    
    # Intent distribution in FAISS
    faiss_intent_counts = {}
    for m in corpus_metadata:
        i = m["intent_id"]
        faiss_intent_counts[i] = faiss_intent_counts.get(i, 0) + 1
    
    print(f"  FAISS index: {len(corpus_metadata)} documents")
    
    # 2. Load and label val_split queries
    print("\n[2/5] Loading val_split queries...")
    rule_system = RuleBaseline()
    
    queries = []
    with open(config.PROCESSED_DATA_DIR / "val_split.jsonl") as f:
        for line in f:
            thread = json.loads(line)
            tid = thread["thread_id"]
            
            conv = []
            for m in thread["messages"]:
                is_inbound = m.get("inbound", True)
                conv.append({
                    "author_role": "customer" if is_inbound else "agent",
                    "text": m["text"]
                })
            
            pred = rule_system.predict(conv)
            intent = pred["predicted_intent"]
            
            if intent == "other_support" or tid not in faiss_thread_ids:
                continue
            
            # Compute query length
            query_text = retriever._format_conversation(thread["messages"])
            
            queries.append({
                "thread_id": tid,
                "intent": intent,
                "conversation": thread["messages"],
                "faiss_idx": faiss_thread_ids[tid],
                "query_text": query_text,
                "query_len_chars": len(query_text),
                "query_len_tokens": len(query_text.split()),
                "num_messages": len(thread["messages"]),
            })
    
    print(f"  Evaluation queries: {len(queries)}")
    
    # 3. Evaluate with detailed failure tracking
    k_values = [1, 3, 5]
    max_k = max(k_values) + 1
    
    per_intent = {}
    failures_k3 = []
    successes_k3 = []
    
    print(f"\n[3/5] Evaluating {len(queries)} queries with failure tracking...")
    
    for i, q in enumerate(queries):
        target_intent = q["intent"]
        
        if target_intent not in per_intent:
            per_intent[target_intent] = {
                k: {"hits": 0, "total": 0} for k in k_values
            }
        
        retrieved = retriever.retrieve(q["conversation"], k=max_k)
        
        # Exclude self
        filtered = []
        for doc in retrieved:
            if doc["metadata"]["thread_id"] != q["thread_id"]:
                filtered.append(doc)
        
        # Track K=3 results for failure analysis
        top3 = filtered[:3]
        top3_intents = [d["metadata"]["intent_id"] for d in top3]
        top3_scores = [d["score"] for d in top3]
        
        hit_k3 = target_intent in top3_intents
        
        for k in k_values:
            top_k = filtered[:k]
            hit = any(d["metadata"]["intent_id"] == target_intent for d in top_k)
            per_intent[target_intent][k]["total"] += 1
            if hit:
                per_intent[target_intent][k]["hits"] += 1
        
        record = {
            "thread_id": q["thread_id"],
            "intent": target_intent,
            "query_len_tokens": q["query_len_tokens"],
            "num_messages": q["num_messages"],
            "top3_intents": top3_intents,
            "top3_scores": top3_scores,
            "top1_score": top3_scores[0] if top3_scores else 0,
            "hit_k3": hit_k3,
        }
        
        if hit_k3:
            if len(successes_k3) < 50:
                record["query_preview"] = q["query_text"][:300]
                successes_k3.append(record)
        else:
            record["query_preview"] = q["query_text"][:300]
            failures_k3.append(record)
        
        if (i + 1) % 1000 == 0:
            print(f"  {i+1}/{len(queries)}")
    
    n = len(queries)
    n_failures = len(failures_k3)
    print(f"\n  Total queries: {n}")
    print(f"  K=3 failures: {n_failures} ({n_failures/n*100:.1f}%)")
    
    # 4. Analyze failure modes
    print(f"\n[4/5] Analyzing failure modes...")
    
    # Failure by intent
    failure_by_intent = {}
    for f in failures_k3:
        intent = f["intent"]
        failure_by_intent[intent] = failure_by_intent.get(intent, 0) + 1
    
    # Failure by query length
    fail_lens = [f["query_len_tokens"] for f in failures_k3]
    success_lens = [s["query_len_tokens"] for s in successes_k3]
    
    # Failure by top-1 score
    fail_scores = [f["top1_score"] for f in failures_k3]
    success_scores = [s["top1_score"] for s in successes_k3]
    
    # Confusion analysis: what intents do failed queries retrieve instead?
    confusion = {}
    for f in failures_k3:
        true_intent = f["intent"]
        for pred_intent in f["top3_intents"]:
            if pred_intent != true_intent:
                pair = (true_intent, pred_intent)
                confusion[pair] = confusion.get(pair, 0) + 1
    
    top_confusions = sorted(confusion.items(), key=lambda x: -x[1])[:20]
    
    # Short query analysis
    short_threshold = 20  # tokens
    short_fails = sum(1 for f in failures_k3 if f["query_len_tokens"] < short_threshold)
    short_total_fail = sum(1 for f in failures_k3)
    
    # Single-message analysis
    single_msg_fails = sum(1 for f in failures_k3 if f["num_messages"] <= 2)
    
    # 5. Build report
    print(f"\n[5/5] Saving results...")
    
    # Per-intent full table
    intent_table = {}
    for intent in sorted(per_intent.keys()):
        d = per_intent[intent]
        total = d[3]["total"]
        intent_table[intent] = {
            "recall_at_1": round(d[1]["hits"] / total, 4) if total > 0 else 0,
            "recall_at_3": round(d[3]["hits"] / total, 4) if total > 0 else 0,
            "recall_at_5": round(d[5]["hits"] / total, 4) if total > 0 else 0,
            "total_queries": total,
            "failures_at_k3": total - d[3]["hits"],
            "faiss_docs": faiss_intent_counts.get(intent, 0),
        }
    
    output = {
        "summary": {
            "total_queries": n,
            "failures_at_k3": n_failures,
            "failure_rate_k3": round(n_failures / n, 4),
            "failures_by_intent": {k: v for k, v in sorted(failure_by_intent.items(), key=lambda x: -x[1])},
        },
        "per_intent": intent_table,
        "confusion_matrix_top20": [
            {"true": pair[0], "predicted": pair[1], "count": count}
            for pair, count in top_confusions
        ],
        "failure_characteristics": {
            "mean_query_len_failures": round(np.mean(fail_lens), 1) if fail_lens else 0,
            "mean_query_len_successes": round(np.mean(success_lens), 1) if success_lens else 0,
            "mean_top1_score_failures": round(float(np.mean(fail_scores)), 4) if fail_scores else 0,
            "mean_top1_score_successes": round(float(np.mean(success_scores)), 4) if success_scores else 0,
            "short_query_failures": short_fails,
            "single_message_failures": single_msg_fails,
        },
        "failure_examples": failures_k3[:20],
        "success_examples": successes_k3[:10],
    }
    
    with open("reports/dense_retrieval_failure_analysis.json", "w") as f:
        json.dump(output, f, indent=2)
    print("  Saved: reports/dense_retrieval_failure_analysis.json")
    
    # Print summary
    print(f"\n{'='*70}")
    print("FAILURE ANALYSIS SUMMARY")
    print(f"{'='*70}")
    
    print(f"\nPer-Intent Recall@1 / Recall@3 / Recall@5:")
    print(f"{'Intent':<25} {'R@1':>7} {'R@3':>7} {'R@5':>7} {'Fails':>6} {'FAISS':>6}")
    print("-" * 60)
    for intent in sorted(intent_table.keys(), key=lambda x: intent_table[x]["recall_at_3"]):
        d = intent_table[intent]
        print(f"{intent:<25} {d['recall_at_1']:>7.2%} {d['recall_at_3']:>7.2%} {d['recall_at_5']:>7.2%} {d['failures_at_k3']:>6} {d['faiss_docs']:>6}")
    
    print(f"\nTop 10 Intent Confusions (true → retrieved):")
    for pair, count in top_confusions[:10]:
        print(f"  {pair[0]} → {pair[1]}: {count}")
    
    print(f"\nQuery Length: fails={np.mean(fail_lens):.0f} tokens vs success={np.mean(success_lens):.0f} tokens")
    print(f"Top-1 Score: fails={np.mean(fail_scores):.4f} vs success={np.mean(success_scores):.4f}")
    print(f"Short queries (<{short_threshold} tokens) in failures: {short_fails}/{n_failures}")
    print(f"Single/two-message in failures: {single_msg_fails}/{n_failures}")
    
    print("\nDone.")


if __name__ == "__main__":
    main()
