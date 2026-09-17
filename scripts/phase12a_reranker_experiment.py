"""Phase 12A — Hybrid Retrieval + Cross-Encoder Reranking Experiment.

OFFLINE EXPERIMENT ONLY. Does NOT modify production models, FAISS, or Golden Set.

Pipeline:
  Stage 1: Existing MNRL dense retriever → Top-K candidates (K=10, K=20)
  Stage 2: cross-encoder/ms-marco-MiniLM-L-6-v2 reranker → reorder candidates
  Evaluate: Recall@1, Recall@3, Recall@5, MRR@3, per-intent, confusion boundaries
"""
import json
import os
import sys
import pickle
import time
import hashlib
import numpy as np
import faiss
from collections import defaultdict

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config


# ============================================================
# STEP 10 — INTEGRITY CHECKS
# ============================================================
def verify_integrity():
    gs_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    with open(gs_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    count = sum(1 for _ in open(gs_path))
    print(f"Golden Set: {count} examples, SHA-256: {sha}")
    assert count == 196, f"Expected 196, got {count}"

    mnrl_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    assert (mnrl_path / "model.safetensors").exists(), "MNRL model missing"
    print("Production MNRL model: PRESENT (not modified)")

    faiss_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "faiss_index.bin"
    assert faiss_path.exists(), "FAISS index missing"
    print("Production FAISS index: PRESENT (not modified)")
    print()


# ============================================================
# DATA LOADING
# ============================================================
def format_conv(messages):
    parts = []
    for msg in messages:
        is_inbound = msg.get("inbound")
        if is_inbound is not None:
            role = "User" if is_inbound else "Agent"
        else:
            role = "Agent" if msg.get("author_role") == "agent" else "User"
        parts.append(f"{role}: {msg.get('text', '')}")
    return "\n".join(parts)


def load_corpus_and_index():
    meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(meta_path, "rb") as f:
        corpus_metadata = pickle.load(f)

    from sentence_transformers import SentenceTransformer
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    mnrl_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    model = SentenceTransformer(str(mnrl_path), device=device)

    corpus_texts = [m["conversation"] for m in corpus_metadata]
    print(f"Encoding {len(corpus_texts)} corpus docs on {device}...")
    t0 = time.time()
    corpus_embs = model.encode(corpus_texts, show_progress_bar=True, batch_size=64)
    corpus_embs = np.array(corpus_embs).astype("float32")
    faiss.normalize_L2(corpus_embs)
    print(f"Corpus encoded in {time.time()-t0:.1f}s")

    dim = corpus_embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(corpus_embs)

    return model, index, corpus_metadata, device


def load_queries():
    queries = []
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
        for line in f:
            q = json.loads(line)
            queries.append({
                "id": q["thread_id"],
                "text": format_conv(q.get("messages", q.get("conversation", []))),
                "intent": q["intent_id"],
            })
    return queries


# ============================================================
# DENSE RETRIEVAL (Stage 1)
# ============================================================
def dense_retrieve(model, index, corpus_metadata, queries, top_k, device):
    query_texts = [q["text"] for q in queries]
    query_embs = model.encode(query_texts, show_progress_bar=False, batch_size=32)
    query_embs = np.array(query_embs).astype("float32")
    faiss.normalize_L2(query_embs)

    D, I = index.search(query_embs, top_k)

    results = []
    for i, q in enumerate(queries):
        candidates = []
        for j in range(top_k):
            idx = int(I[i][j])
            candidates.append({
                "corpus_idx": idx,
                "dense_score": float(D[i][j]),
                "intent": corpus_metadata[idx]["intent_id"],
                "text": corpus_metadata[idx]["conversation"],
                "thread_id": corpus_metadata[idx]["thread_id"],
            })
        results.append({"query": q, "candidates": candidates})
    return results


# ============================================================
# CROSS-ENCODER RERANKING (Stage 2)
# ============================================================
def rerank_with_cross_encoder(retrieval_results, cross_encoder):
    """Score each (query, candidate) pair and reorder."""
    reranked = []
    for item in retrieval_results:
        query_text = item["query"]["text"]
        candidates = item["candidates"]

        # Build pairs for cross-encoder
        pairs = [[query_text, c["text"]] for c in candidates]
        scores = cross_encoder.predict(pairs, show_progress_bar=False)

        # Attach scores and sort
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)

        sorted_cands = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        reranked.append({"query": item["query"], "candidates": sorted_cands})
    return reranked


# ============================================================
# EVALUATION
# ============================================================
def evaluate(results, label=""):
    n = len(results)
    k1 = k3 = k5 = 0
    rr3 = 0.0
    intent_detail = defaultdict(lambda: {"k1": 0, "k3": 0, "k5": 0, "count": 0})
    per_query = {}

    for item in results:
        expected = item["query"]["intent"]
        qid = item["query"]["id"]
        intent_detail[expected]["count"] += 1

        cand_intents = [c["intent"] for c in item["candidates"]]
        if expected in cand_intents:
            rank = cand_intents.index(expected) + 1
        else:
            rank = 999

        per_query[qid] = {"intent": expected, "rank": rank, "cand_intents": cand_intents[:5]}

        if rank == 1:
            k1 += 1
            intent_detail[expected]["k1"] += 1
        if rank <= 3:
            k3 += 1
            rr3 += 1.0 / rank
            intent_detail[expected]["k3"] += 1
        if rank <= 5:
            k5 += 1
            intent_detail[expected]["k5"] += 1

    metrics = {
        "Recall@1": k1 / n,
        "Recall@3": k3 / n,
        "Recall@5": k5 / n,
        "MRR@3": rr3 / n,
    }
    return metrics, dict(intent_detail), per_query


# ============================================================
# DIFF ANALYSIS
# ============================================================
def diff_analysis(dense_pq, reranked_pq, queries):
    improved = []
    regressed = []
    unchanged = 0

    for q in queries:
        qid = q["id"]
        d_rank = dense_pq[qid]["rank"]
        r_rank = reranked_pq[qid]["rank"]

        if r_rank < d_rank and r_rank <= 5:
            improved.append({"id": qid, "intent": q["intent"], "dense_rank": d_rank, "reranked_rank": r_rank})
        elif r_rank > d_rank and d_rank <= 5:
            regressed.append({"id": qid, "intent": q["intent"], "dense_rank": d_rank, "reranked_rank": r_rank})
        else:
            unchanged += 1

    return improved, regressed, unchanged


# ============================================================
# ERROR CATEGORIZATION (Step 8)
# ============================================================
def categorize_errors(dense_results_20, reranked_results, queries):
    categories = {
        "CANDIDATE_GENERATION_FAILURE": [],
        "RERANKING_FAILURE": [],
        "SUCCESSFUL_RERANK": [],
        "HARMFUL_RERANK": [],
    }

    dense_pq = {}
    for item in dense_results_20:
        qid = item["query"]["id"]
        expected = item["query"]["intent"]
        cand_intents = [c["intent"] for c in item["candidates"]]
        in_top20 = expected in cand_intents
        rank = cand_intents.index(expected) + 1 if in_top20 else 999
        dense_pq[qid] = {"rank": rank, "in_top20": in_top20}

    reranked_pq = {}
    for item in reranked_results:
        qid = item["query"]["id"]
        expected = item["query"]["intent"]
        cand_intents = [c["intent"] for c in item["candidates"]]
        rank = cand_intents.index(expected) + 1 if expected in cand_intents else 999
        reranked_pq[qid] = {"rank": rank}

    for q in queries:
        qid = q["id"]
        d = dense_pq[qid]
        r = reranked_pq[qid]
        entry = {"id": qid, "intent": q["intent"], "dense_rank": d["rank"], "reranked_rank": r["rank"]}

        if not d["in_top20"]:
            categories["CANDIDATE_GENERATION_FAILURE"].append(entry)
        elif r["rank"] < d["rank"] and r["rank"] <= 5:
            categories["SUCCESSFUL_RERANK"].append(entry)
        elif r["rank"] > d["rank"] and d["rank"] <= 5:
            categories["HARMFUL_RERANK"].append(entry)
        elif d["rank"] > 5 and r["rank"] > 5:
            categories["RERANKING_FAILURE"].append(entry)

    return categories


# ============================================================
# CONFUSION BOUNDARY ANALYSIS (Step 6)
# ============================================================
def confusion_boundary_analysis(dense_results_20, reranked_results, queries):
    boundaries = [
        ("account_access", "delivery_wrong_item"),
        ("account_access", "delivery_missing"),
        ("grocery_fresh", "returns_refunds"),
        ("account_billing", "grocery_fresh"),
        ("account_access", "delivery_delayed"),
        ("delivery_wrong_item", "delivery_missing"),
        ("amazon_locker", "delivery_missing"),
    ]

    # Build lookup
    dense_map = {}
    for item in dense_results_20:
        qid = item["query"]["id"]
        dense_map[qid] = [c["intent"] for c in item["candidates"]]

    reranked_map = {}
    for item in reranked_results:
        qid = item["query"]["id"]
        reranked_map[qid] = [c["intent"] for c in item["candidates"]]

    boundary_results = {}
    for a, b in boundaries:
        key = f"{a} <-> {b}"
        affected = []
        for q in queries:
            if q["intent"] not in (a, b):
                continue
            qid = q["id"]
            expected = q["intent"]
            confuser = b if expected == a else a

            d_intents = dense_map.get(qid, [])
            r_intents = reranked_map.get(qid, [])

            d_rank = d_intents.index(expected) + 1 if expected in d_intents else 999
            r_rank = r_intents.index(expected) + 1 if expected in r_intents else 999

            d_confuser_rank = d_intents.index(confuser) + 1 if confuser in d_intents else 999
            r_confuser_rank = r_intents.index(confuser) + 1 if confuser in r_intents else 999

            recovered = (d_rank > 3 and r_rank <= 3)
            promoted_wrong = (d_confuser_rank > 3 and r_confuser_rank <= 3 and r_rank > 3)
            regression = (r_rank > d_rank and d_rank <= 5)

            affected.append({
                "id": qid, "intent": expected,
                "dense_rank": d_rank, "reranked_rank": r_rank,
                "confuser_dense_rank": d_confuser_rank, "confuser_reranked_rank": r_confuser_rank,
                "recovered": recovered, "promoted_wrong": promoted_wrong, "regression": regression,
            })
        boundary_results[key] = affected

    return boundary_results


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("PHASE 12A — HYBRID RETRIEVAL + CROSS-ENCODER RERANKING")
    print("=" * 60)
    print()

    # Integrity
    verify_integrity()

    # Load
    model, index, corpus_metadata, device = load_corpus_and_index()
    queries = load_queries()
    print(f"Queries: {len(queries)}")

    # Stage 1: Dense retrieval at multiple depths
    print("\n--- Stage 1: Dense Retrieval ---")
    dense_5 = dense_retrieve(model, index, corpus_metadata, queries, 5, device)
    dense_10 = dense_retrieve(model, index, corpus_metadata, queries, 10, device)
    dense_20 = dense_retrieve(model, index, corpus_metadata, queries, 20, device)

    # Evaluate dense baselines
    dense5_metrics, dense5_intent, dense5_pq = evaluate(dense_5, "Dense@5")
    dense10_metrics, _, dense10_pq = evaluate(dense_10, "Dense@10")
    dense20_metrics, _, dense20_pq = evaluate(dense_20, "Dense@20")

    # Candidate recall analysis
    in_top10 = sum(1 for item in dense_10 if item["query"]["intent"] in [c["intent"] for c in item["candidates"]])
    in_top20 = sum(1 for item in dense_20 if item["query"]["intent"] in [c["intent"] for c in item["candidates"]])
    print(f"Candidate recall Top-10: {in_top10}/{len(queries)} ({in_top10/len(queries)*100:.1f}%)")
    print(f"Candidate recall Top-20: {in_top20}/{len(queries)} ({in_top20/len(queries)*100:.1f}%)")

    # Stage 2: Cross-encoder reranking
    print("\n--- Stage 2: Cross-Encoder Reranking ---")
    from sentence_transformers import CrossEncoder
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    print("Reranking Top-10 candidates...")
    t0 = time.time()
    reranked_10 = rerank_with_cross_encoder(dense_10, cross_encoder)
    print(f"Top-10 reranking: {time.time()-t0:.1f}s")

    print("Reranking Top-20 candidates...")
    t0 = time.time()
    reranked_20 = rerank_with_cross_encoder(dense_20, cross_encoder)
    print(f"Top-20 reranking: {time.time()-t0:.1f}s")

    # Evaluate reranked
    reranked10_metrics, reranked10_intent, reranked10_pq = evaluate(reranked_10, "Reranked@10")
    reranked20_metrics, reranked20_intent, reranked20_pq = evaluate(reranked_20, "Reranked@20")

    # Step 7 — A/B table
    print("\n" + "=" * 60)
    print("STEP 7 — A/B COMPARISON")
    print("=" * 60)
    configs = [
        ("Dense baseline (K=5)", dense5_metrics),
        ("Dense Top-10 → rerank", reranked10_metrics),
        ("Dense Top-20 → rerank", reranked20_metrics),
    ]
    print(f"\n{'Configuration':<30} {'R@1':>8} {'R@3':>8} {'R@5':>8} {'MRR@3':>8}")
    print("-" * 62)
    for name, m in configs:
        print(f"{name:<30} {m['Recall@1']*100:>7.2f}% {m['Recall@3']*100:>7.2f}% {m['Recall@5']*100:>7.2f}% {m['MRR@3']:>8.4f}")

    # Diff analysis
    imp10, reg10, unch10 = diff_analysis(dense5_pq, reranked10_pq, queries)
    imp20, reg20, unch20 = diff_analysis(dense5_pq, reranked20_pq, queries)

    print(f"\nDense vs Reranked@10: +{len(imp10)} improved, -{len(reg10)} regressed, {unch10} unchanged")
    print(f"Dense vs Reranked@20: +{len(imp20)} improved, -{len(reg20)} regressed, {unch20} unchanged")

    # Step 5 — Per-intent analysis
    print("\n" + "=" * 60)
    print("STEP 5 — PER-INTENT ANALYSIS (Recall@5)")
    print("=" * 60)
    focus_intents = [
        "grocery_fresh", "account_access", "delivery_wrong_item",
        "delivery_missing", "delivery_delayed", "returns_refunds",
        "account_billing", "amazon_locker", "product_availability",
    ]
    print(f"\n{'Intent':<25} {'Dense R@5':>10} {'Rerank20 R@5':>13}")
    print("-" * 50)
    for intent in focus_intents:
        d = dense5_intent.get(intent, {"k5": 0, "count": 1})
        r = reranked20_intent.get(intent, {"k5": 0, "count": 1})
        d_r5 = d["k5"] / d["count"] * 100 if d["count"] else 0
        r_r5 = r["k5"] / r["count"] * 100 if r["count"] else 0
        delta = r_r5 - d_r5
        marker = "✅" if delta > 0 else ("❌" if delta < 0 else "➖")
        print(f"{intent:<25} {d_r5:>9.1f}% {r_r5:>12.1f}% {marker}")

    # Step 8 — Error categorization
    print("\n" + "=" * 60)
    print("STEP 8 — ERROR CATEGORIZATION (Top-20 rerank)")
    print("=" * 60)
    categories = categorize_errors(dense_20, reranked_20, queries)
    for cat, items in categories.items():
        print(f"\n{cat}: {len(items)}")
        for item in items[:5]:
            print(f"  {item['id'][:12]} ({item['intent']}): dense={item['dense_rank']} reranked={item['reranked_rank']}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more")

    # Step 6 — Confusion boundary analysis
    print("\n" + "=" * 60)
    print("STEP 6 — CONFUSION BOUNDARY ANALYSIS (Top-20 rerank)")
    print("=" * 60)
    boundaries = confusion_boundary_analysis(dense_20, reranked_20, queries)
    for boundary, items in boundaries.items():
        recoveries = sum(1 for i in items if i["recovered"])
        promotions = sum(1 for i in items if i["promoted_wrong"])
        regressions = sum(1 for i in items if i["regression"])
        print(f"\n{boundary}: {len(items)} queries, {recoveries} recovered, {promotions} wrong promoted, {regressions} regressions")

    # Best config determination
    best_config = "Dense Top-20 → rerank"
    best_metrics = reranked20_metrics

    # Weak intent checks
    gf_d = dense5_intent.get("grocery_fresh", {"k5": 0, "count": 1})
    gf_r = reranked20_intent.get("grocery_fresh", {"k5": 0, "count": 1})
    aa_d = dense5_intent.get("account_access", {"k5": 0, "count": 1})
    aa_r = reranked20_intent.get("account_access", {"k5": 0, "count": 1})
    dwi_d = dense5_intent.get("delivery_wrong_item", {"k5": 0, "count": 1})
    dwi_r = reranked20_intent.get("delivery_wrong_item", {"k5": 0, "count": 1})

    gf_r5 = gf_r["k5"] / gf_r["count"] if gf_r["count"] else 0
    aa_r5 = aa_r["k5"] / aa_r["count"] if aa_r["count"] else 0
    dwi_r5 = dwi_r["k5"] / dwi_r["count"] if dwi_r["count"] else 0
    dwi_d5 = dwi_d["k5"] / dwi_d["count"] if dwi_d["count"] else 0

    r3_improved = best_metrics["Recall@3"] > dense5_metrics["Recall@3"]
    r5_improved = best_metrics["Recall@5"] > dense5_metrics["Recall@5"]
    low_regressions = len(reg20) <= 5
    dwi_safe = dwi_r5 >= dwi_d5

    if (r3_improved or r5_improved) and low_regressions and dwi_safe:
        decision = "PROMISING"
    elif r3_improved or r5_improved:
        decision = "REQUIRES_REVIEW"
    else:
        decision = "REJECT"

    # Final output
    print("\n" + "=" * 60)
    print("PHASE 12A COMPLETE")
    print("=" * 60)
    print(f"\nDense R@1:\n{dense5_metrics['Recall@1']*100:.2f}%")
    print(f"\nReranked R@1:\n{best_metrics['Recall@1']*100:.2f}%")
    print(f"\nDense R@3:\n{dense5_metrics['Recall@3']*100:.2f}%")
    print(f"\nReranked R@3:\n{best_metrics['Recall@3']*100:.2f}%")
    print(f"\nDense R@5:\n{dense5_metrics['Recall@5']*100:.2f}%")
    print(f"\nReranked R@5:\n{best_metrics['Recall@5']*100:.2f}%")
    print(f"\nDense MRR@3:\n{dense5_metrics['MRR@3']:.4f}")
    print(f"\nReranked MRR@3:\n{best_metrics['MRR@3']:.4f}")
    print(f"\nSuccessful reranks:\n{len(categories['SUCCESSFUL_RERANK'])}")
    print(f"\nHarmful reranks:\n{len(categories['HARMFUL_RERANK'])}")
    print(f"\nCandidate-generation failures:\n{len(categories['CANDIDATE_GENERATION_FAILURE'])}")
    print(f"\nReranking failures:\n{len(categories['RERANKING_FAILURE'])}")
    print(f"\ngrocery_fresh R@5:\n{gf_r5*100:.2f}%")
    print(f"\naccount_access R@5:\n{aa_r5*100:.2f}%")
    print(f"\ndelivery_wrong_item R@5:\n{dwi_r5*100:.2f}%")
    print(f"\nDecision:\n{decision}")
    print(f"\nProduction model modified:\nNO")
    print(f"\nProduction FAISS modified:\nNO")
    print(f"\nGolden Set modified:\nNO")
    if decision == "PROMISING":
        print(f"\nRecommended next phase:\nPHASE 12B — CROSS-ENCODER INTEGRATION PILOT")
    elif decision == "REQUIRES_REVIEW":
        print(f"\nRecommended next phase:\nPHASE 12B — TARGETED RERANKER ANALYSIS")
    else:
        print(f"\nRecommended next phase:\nPHASE 12B — ALTERNATIVE RETRIEVAL STRATEGIES")

    # Save reports
    os.makedirs("reports", exist_ok=True)

    report_json = {
        "dense_baseline": dense5_metrics,
        "dense_top10_reranked": reranked10_metrics,
        "dense_top20_reranked": reranked20_metrics,
        "candidate_recall_top10": in_top10 / len(queries),
        "candidate_recall_top20": in_top20 / len(queries),
        "dense_vs_reranked10": {"improved": len(imp10), "regressed": len(reg10), "unchanged": unch10},
        "dense_vs_reranked20": {"improved": len(imp20), "regressed": len(reg20), "unchanged": unch20},
        "improved_details_20": imp20,
        "regressed_details_20": reg20,
        "error_categories": {k: len(v) for k, v in categories.items()},
        "error_details": {k: v for k, v in categories.items()},
        "weak_intents": {
            "grocery_fresh_r5": gf_r5,
            "account_access_r5": aa_r5,
            "delivery_wrong_item_r5": dwi_r5,
        },
        "decision": decision,
        "cross_encoder_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "production_model_modified": False,
        "production_faiss_modified": False,
        "golden_set_modified": False,
    }

    with open("reports/phase12a_reranker_experiment.json", "w") as f:
        json.dump(report_json, f, indent=2, default=str)

    # Markdown report
    with open("reports/phase12a_reranker_experiment.md", "w") as f:
        f.write("# Phase 12A — Hybrid Retrieval + Cross-Encoder Reranking\n\n")
        f.write("## Configuration\n")
        f.write(f"- Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2`\n")
        f.write(f"- Dense model: MNRL (`.cache/rag_dense_mnrl/`)\n")
        f.write(f"- Candidate recall Top-10: {in_top10/len(queries)*100:.1f}%\n")
        f.write(f"- Candidate recall Top-20: {in_top20/len(queries)*100:.1f}%\n\n")

        f.write("## A/B Comparison\n\n")
        f.write("| Configuration | R@1 | R@3 | R@5 | MRR@3 |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for name, m in configs:
            f.write(f"| {name} | {m['Recall@1']:.4f} | {m['Recall@3']:.4f} | {m['Recall@5']:.4f} | {m['MRR@3']:.4f} |\n")

        f.write(f"\n## Diff Analysis (Dense vs Top-20 Rerank)\n")
        f.write(f"- Improved: {len(imp20)}\n")
        f.write(f"- Regressed: {len(reg20)}\n")
        f.write(f"- Unchanged: {unch20}\n\n")

        f.write("## Error Categories\n\n")
        for cat, items in categories.items():
            f.write(f"- **{cat}**: {len(items)}\n")

        f.write(f"\n## Decision\n**{decision}**\n")

    print("\nReports saved.")


if __name__ == "__main__":
    main()
