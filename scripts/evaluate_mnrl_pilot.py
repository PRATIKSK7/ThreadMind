"""Phase 11B — Evaluate MNRL Hard-Negative Pilot vs Baseline.

Encodes on MPS (fast), runs FAISS search on CPU (always CPU).
Produces reports/phase11b_mnrl_pilot.json and .md.
"""
import json
import os
import sys
import pickle
import time
import torch
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config


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


def evaluate_model(model_dir, corpus_texts, corpus_metadata, queries, device="mps"):
    """Encode with SentenceTransformer on `device`, search with FAISS on CPU."""
    print(f"  Loading model from {model_dir} on {device}...")
    model = SentenceTransformer(str(model_dir), device=device)

    print(f"  Encoding {len(corpus_texts)} corpus docs...")
    t0 = time.time()
    corpus_embs = model.encode(corpus_texts, show_progress_bar=True, batch_size=64)
    corpus_embs = np.array(corpus_embs).astype("float32")
    faiss.normalize_L2(corpus_embs)
    print(f"  Corpus encoded in {time.time() - t0:.1f}s")

    print(f"  Encoding {len(queries)} queries...")
    query_texts = [q["text"] for q in queries]
    query_embs = model.encode(query_texts, show_progress_bar=False, batch_size=32)
    query_embs = np.array(query_embs).astype("float32")
    faiss.normalize_L2(query_embs)

    dim = corpus_embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(corpus_embs)

    D, I = index.search(query_embs, 5)

    # Compute metrics
    k1 = k3 = k5 = 0
    rr3 = 0.0
    intent_detail = {}
    retrieved_map = {}

    for i, q in enumerate(queries):
        expected = q["intent"]
        if expected not in intent_detail:
            intent_detail[expected] = {"k1": 0, "k3": 0, "k5": 0, "count": 0}
        intent_detail[expected]["count"] += 1

        retrieved = [corpus_metadata[idx]["intent_id"] for idx in I[i]]
        retrieved_map[q["id"]] = retrieved

        if expected in retrieved:
            rank = retrieved.index(expected) + 1
        else:
            rank = 999

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

    n = len(queries)
    return {
        "Recall@1": k1 / n,
        "Recall@3": k3 / n,
        "Recall@5": k5 / n,
        "MRR@3": rr3 / n,
        "intent_detail": intent_detail,
        "retrieved_map": retrieved_map,
    }


def main():
    # --- Load corpus metadata ---
    meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    print(f"Loading corpus metadata from {meta_path}...")
    with open(meta_path, "rb") as f:
        corpus_metadata = pickle.load(f)

    golden_ids = set()
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
        for line in f:
            golden_ids.add(json.loads(line)["thread_id"])

    corpus_texts = [m["conversation"] for m in corpus_metadata]
    print(f"Corpus size: {len(corpus_texts)}")

    # --- Load queries ---
    queries = []
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
        for line in f:
            q = json.loads(line)
            queries.append({
                "id": q["thread_id"],
                "text": format_conv(q.get("messages", q.get("conversation", []))),
                "intent": q["intent_id"],
            })
    print(f"Queries: {len(queries)}")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Encoding device: {device}")

    # --- Evaluate Baseline ---
    baseline_dir = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    print("\n=== BASELINE ===")
    baseline = evaluate_model(baseline_dir, corpus_texts, corpus_metadata, queries, device)

    # --- Evaluate Pilot ---
    pilot_dir = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl_hn_pilot_v1"
    print("\n=== PILOT (Hard-Negative) ===")
    pilot = evaluate_model(pilot_dir, corpus_texts, corpus_metadata, queries, device)

    # --- Diff analysis ---
    improved = 0
    regressed = 0
    improved_details = []
    regressed_details = []

    for q in queries:
        qid = q["id"]
        expected = q["intent"]
        b_ret = baseline["retrieved_map"][qid]
        p_ret = pilot["retrieved_map"][qid]
        b_rank = b_ret.index(expected) + 1 if expected in b_ret else 999
        p_rank = p_ret.index(expected) + 1 if expected in p_ret else 999

        if p_rank < b_rank and p_rank <= 5:
            improved += 1
            improved_details.append({"id": qid, "intent": expected, "base_rank": b_rank, "pilot_rank": p_rank})
        elif p_rank > b_rank and b_rank <= 5:
            regressed += 1
            regressed_details.append({"id": qid, "intent": expected, "base_rank": b_rank, "pilot_rank": p_rank})

    # --- Per-intent analysis for weak intents ---
    weak_intents = ["grocery_fresh", "account_access", "delivery_wrong_item"]
    weak_analysis = {}
    for intent in weak_intents:
        bd = baseline["intent_detail"].get(intent, {"k5": 0, "count": 1})
        pd = pilot["intent_detail"].get(intent, {"k5": 0, "count": 1})
        weak_analysis[intent] = {
            "baseline_recall5": bd["k5"] / bd["count"] if bd["count"] else 0,
            "pilot_recall5": pd["k5"] / pd["count"] if pd["count"] else 0,
            "baseline_recall3": bd["k3"] / bd["count"] if bd["count"] else 0,
            "pilot_recall3": pd["k3"] / pd["count"] if pd["count"] else 0,
        }

    # --- Decision ---
    r3_improved = pilot["Recall@3"] > baseline["Recall@3"]
    r5_improved = pilot["Recall@5"] > baseline["Recall@5"]
    low_regressions = regressed <= 2
    gf_improved = weak_analysis["grocery_fresh"]["pilot_recall5"] >= weak_analysis["grocery_fresh"]["baseline_recall5"]

    if (r3_improved or r5_improved) and low_regressions and gf_improved:
        decision = "PROMISING"
    elif r3_improved or r5_improved:
        decision = "REQUIRES_REVIEW"
    else:
        decision = "REJECT"

    # --- Print results ---
    print("\n" + "=" * 60)
    print("PHASE 11B — MNRL HARD-NEGATIVE PILOT RESULTS")
    print("=" * 60)
    print(f"\n{'Metric':<15} {'Baseline':>10} {'Pilot':>10} {'Delta':>10}")
    print("-" * 45)
    for m in ["Recall@1", "Recall@3", "Recall@5", "MRR@3"]:
        d = pilot[m] - baseline[m]
        print(f"{m:<15} {baseline[m]*100:>9.2f}% {pilot[m]*100:>9.2f}% {d*100:>+9.2f}%")

    print(f"\nImprovements: {improved}")
    print(f"Regressions:  {regressed}")

    print("\nWeak intent analysis:")
    for intent, data in weak_analysis.items():
        print(f"  {intent}: R@5 {data['baseline_recall5']*100:.1f}% -> {data['pilot_recall5']*100:.1f}%  |  R@3 {data['baseline_recall3']*100:.1f}% -> {data['pilot_recall3']*100:.1f}%")

    if regressed_details:
        print("\nRegression details:")
        for r in regressed_details:
            print(f"  {r['id']} ({r['intent']}): rank {r['base_rank']} -> {r['pilot_rank']}")

    print(f"\nDECISION: {decision}")

    # --- Save reports ---
    os.makedirs("reports", exist_ok=True)

    report_json = {
        "baseline": {k: baseline[k] for k in ["Recall@1", "Recall@3", "Recall@5", "MRR@3"]},
        "pilot": {k: pilot[k] for k in ["Recall@1", "Recall@3", "Recall@5", "MRR@3"]},
        "improvements": improved,
        "regressions": regressed,
        "improved_details": improved_details,
        "regressed_details": regressed_details,
        "weak_intent_analysis": weak_analysis,
        "decision": decision,
        "training_loss": 2.4190709040715146,
        "training_runtime_sec": 122.23,
        "production_model_modified": False,
        "production_faiss_modified": False,
        "golden_set_modified": False,
    }
    with open("reports/phase11b_mnrl_pilot.json", "w") as f:
        json.dump(report_json, f, indent=2)

    with open("reports/phase11b_mnrl_pilot.md", "w") as f:
        f.write("# Phase 11B — MNRL Hard-Negative Pilot Results\n\n")
        f.write("## Training\n")
        f.write("- Triplets: 195 train / 49 val\n")
        f.write("- Epochs: 1\n")
        f.write("- Loss: 2.419\n")
        f.write("- Runtime: 122s (MPS)\n\n")
        f.write("## Retrieval Comparison\n\n")
        f.write("| Metric | Baseline | Pilot | Delta |\n")
        f.write("|---|---:|---:|---:|\n")
        for m in ["Recall@1", "Recall@3", "Recall@5", "MRR@3"]:
            d = pilot[m] - baseline[m]
            f.write(f"| {m} | {baseline[m]:.4f} | {pilot[m]:.4f} | {d:+.4f} |\n")
        f.write(f"\n## Diff Analysis\n")
        f.write(f"- Improvements: {improved}\n")
        f.write(f"- Regressions: {regressed}\n\n")
        f.write("## Weak Intent Analysis\n\n")
        f.write("| Intent | Baseline R@5 | Pilot R@5 | Baseline R@3 | Pilot R@3 |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for intent, data in weak_analysis.items():
            f.write(f"| {intent} | {data['baseline_recall5']:.4f} | {data['pilot_recall5']:.4f} | {data['baseline_recall3']:.4f} | {data['pilot_recall3']:.4f} |\n")
        if regressed_details:
            f.write("\n## Regression Details\n\n")
            for r in regressed_details:
                f.write(f"- `{r['id']}` ({r['intent']}): rank {r['base_rank']} → {r['pilot_rank']}\n")
        f.write(f"\n## Decision\n**{decision}**\n")
        f.write("\n## Safety\n")
        f.write("- Production model modified: NO\n")
        f.write("- Production FAISS modified: NO\n")
        f.write("- Golden Set modified: NO\n")

    print("\nReports saved to reports/phase11b_mnrl_pilot.json and .md")


if __name__ == "__main__":
    main()
