"""Phase 13A — Intent-Aware Query Representation Pilot

OFFLINE EXPERIMENT ONLY.

Compares different query representations against the exact same MNRL retriever and FAISS index.
"""
import json
import os
import sys
import pickle
import hashlib
import time
import re
from collections import defaultdict, Counter

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config


# ============================================================
# INTEGRITY CHECKS
# ============================================================
def verify_integrity():
    gs_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    with open(gs_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    count = sum(1 for _ in open(gs_path))
    print(f"Golden Set: {count} examples, SHA-256: {sha}")
    assert count == 196, f"Expected 196, got {count}"
    assert sha == "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f", f"Invalid SHA: {sha}"

    mnrl_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    assert (mnrl_path / "model.safetensors").exists(), "MNRL model missing"
    
    faiss_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "faiss_index.bin"
    assert faiss_path.exists(), "FAISS index missing"


# ============================================================
# QUERY REPRESENTATIONS
# ============================================================

def is_user_msg(msg):
    is_inbound = msg.get("inbound")
    if is_inbound is not None:
        return is_inbound
    return msg.get("author_role") != "agent"

def format_baseline(messages):
    text_parts = []
    for msg in messages:
        role = "User" if is_user_msg(msg) else "Agent"
        text_parts.append(f"{role}: {msg.get('text', '')}")
    return "\n".join(text_parts)

def format_query_only(messages):
    return "\n".join([msg.get('text', '') for msg in messages if is_user_msg(msg)])

def format_user_agent(messages):
    # Same as baseline since baseline already uses User/Agent format
    return format_baseline(messages)

def format_structured(messages):
    user_texts = [msg.get('text', '') for msg in messages if is_user_msg(msg)]
    agent_texts = [msg.get('text', '') for msg in messages if not is_user_msg(msg)]
    
    return f"Intent-relevant user request:\n{chr(10).join(user_texts)}\n\nImportant context:\n{chr(10).join(agent_texts)}"

STOPWORDS = {"i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
             "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
             "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
             "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
             "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
             "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
             "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", 
             "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", 
             "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", 
             "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", 
             "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", 
             "can", "will", "just", "don", "should", "now", "agent", "user", "hi", "hello", "thanks", "please"}

def format_keyword_augmented(messages):
    base_text = format_baseline(messages)
    
    # Extract keywords
    words = re.findall(r'\b[a-z]{3,}\b', base_text.lower())
    filtered_words = [w for w in words if w not in STOPWORDS]
    
    # Get top 5 most common words
    top_words = [word for word, count in Counter(filtered_words).most_common(5)]
    keywords_str = " ".join(top_words)
    
    return f"{base_text}\n{keywords_str}"

def format_last_user_turn(messages):
    user_msgs = [msg.get('text', '') for msg in messages if is_user_msg(msg)]
    if user_msgs:
        return user_msgs[-1]
    return ""

REPRESENTATIONS = {
    "BASELINE": format_baseline,
    "QUERY_ONLY": format_query_only,
    "USER_AGENT": format_user_agent,
    "STRUCTURED": format_structured,
    "KEYWORD-AUGMENTED": format_keyword_augmented,
    "LAST-USER-TURN": format_last_user_turn
}

# ============================================================
# EVALUATION CORE
# ============================================================

def evaluate_retrieval(model, index, corpus_metadata, queries, format_fn):
    # Format queries
    formatted_queries = []
    for q in queries:
        text = format_fn(q["messages"])
        formatted_queries.append({
            "id": q["id"],
            "expected_intent": q["intent"],
            "text": text
        })
        
    # Encode queries
    import torch
    query_texts = [q["text"] for q in formatted_queries]
    
    # We use a smaller batch size to avoid any OOM issues just in case, though queries are small
    query_embs = model.encode(query_texts, show_progress_bar=False, batch_size=32)
    query_embs = np.array(query_embs).astype("float32")
    faiss.normalize_L2(query_embs)
    
    # Retrieve top 5
    D, I = index.search(query_embs, 5)
    
    # Calculate metrics
    n = len(queries)
    k1 = k3 = k5 = 0
    rr3 = 0.0
    intent_detail = defaultdict(lambda: {"k1": 0, "k3": 0, "k5": 0, "count": 0})
    per_query = {}
    
    for i, q in enumerate(formatted_queries):
        expected = q["expected_intent"]
        qid = q["id"]
        intent_detail[expected]["count"] += 1
        
        retrieved_intents = [corpus_metadata[idx]["intent_id"] for idx in I[i]]
        
        if expected in retrieved_intents:
            rank = retrieved_intents.index(expected) + 1
        else:
            rank = 999
            
        per_query[qid] = {"intent": expected, "rank": rank, "retrieved_intents": retrieved_intents}
            
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
            
    return {
        "Recall@1": k1 / n,
        "Recall@3": k3 / n,
        "Recall@5": k5 / n,
        "MRR@3": rr3 / n,
        "intent_detail": dict(intent_detail),
        "per_query": per_query
    }


def compare_paired(base_pq, cand_pq):
    improved = 0
    regressed = 0
    unchanged = 0
    details = []
    
    for qid in base_pq:
        b_rank = base_pq[qid]["rank"]
        c_rank = cand_pq[qid]["rank"]
        intent = base_pq[qid]["intent"]
        
        status = "unchanged"
        if c_rank < b_rank and c_rank <= 5:
            improved += 1
            status = "improved"
        elif c_rank > b_rank and b_rank <= 5:
            regressed += 1
            status = "regressed"
        else:
            unchanged += 1
            
        if status != "unchanged":
            details.append({
                "id": qid,
                "intent": intent,
                "base_rank": b_rank,
                "new_rank": c_rank,
                "status": status
            })
            
    return improved, regressed, unchanged, details

# ============================================================
# CONFUSION BOUNDARIES
# ============================================================

def analyze_confusion(per_query, boundary_pairs):
    results = {}
    for a, b in boundary_pairs:
        key = f"{a} <-> {b}"
        confusions = 0
        total = 0
        
        for qid, data in per_query.items():
            expected = data["intent"]
            if expected not in (a, b):
                continue
                
            total += 1
            confuser = b if expected == a else a
            
            # Check if confuser is ranked higher than expected in top 5
            expected_rank = data["rank"]
            confuser_rank = data["retrieved_intents"].index(confuser) + 1 if confuser in data["retrieved_intents"] else 999
            
            if confuser_rank < expected_rank and confuser_rank <= 5:
                confusions += 1
                
        results[key] = {"confusions": confusions, "total": total}
        
    return results


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("PHASE 13A — QUERY REPRESENTATION EXPERIMENT")
    print("=" * 60)
    
    verify_integrity()
    
    # 1. Load Data
    queries = []
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
        for line in f:
            q = json.loads(line)
            msgs = q.get("messages", q.get("conversation", []))
            queries.append({
                "id": q["thread_id"],
                "intent": q["intent_id"],
                "messages": msgs
            })
            
    meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(meta_path, "rb") as f:
        corpus_metadata = pickle.load(f)
        
    # 2. Load Model and FAISS
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    mnrl_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    model = SentenceTransformer(str(mnrl_path), device=device)
    
    index_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "faiss_index.bin"
    index = faiss.read_index(str(index_path))
    
    print(f"Loaded Golden Set: {len(queries)}")
    print(f"Loaded FAISS index: {index.ntotal} vectors")
    print("Running evaluations...")
    
    # 3. Evaluate all representations
    results = {}
    for name, format_fn in REPRESENTATIONS.items():
        print(f"Evaluating {name}...")
        results[name] = evaluate_retrieval(model, index, corpus_metadata, queries, format_fn)
        
    base_results = results["BASELINE"]
    
    # 4. Compute Paired Comparisons
    paired = {}
    failure_details = {}
    for name, res in results.items():
        if name == "BASELINE":
            continue
        imp, reg, unch, details = compare_paired(base_results["per_query"], res["per_query"])
        paired[name] = {
            "improved": imp,
            "regressed": reg,
            "unchanged": unch,
            "net": imp - reg
        }
        failure_details[name] = details
        
    # 5. Confusion Boundaries
    boundaries = [
        ("account_access", "delivery_wrong_item"),
        ("account_access", "delivery_missing"),
        ("account_access", "delivery_delayed"),
        ("grocery_fresh", "returns_refunds"),
        ("account_billing", "grocery_fresh"),
        ("amazon_locker", "delivery_missing"),
        ("delivery_delayed", "returns_refunds")
    ]
    
    confusions = {}
    for name, res in results.items():
        confusions[name] = analyze_confusion(res["per_query"], boundaries)
        
    # 6. Winner Selection
    winner = "BASELINE"
    winner_score = base_results["Recall@3"]
    best_net = 0
    decision = "REJECT"
    
    for name in paired:
        res = results[name]
        net = paired[name]["net"]
        r3 = res["Recall@3"]
        
        # We want meaningful improvement, so net > 2 or R@3 improves
        if (net > 2 or r3 > base_results["Recall@3"]) and paired[name]["regressed"] <= 5:
            if r3 > winner_score or (r3 == winner_score and net > best_net):
                winner = name
                winner_score = r3
                best_net = net
                decision = "PROMOTE"
                
    if decision == "REJECT":
        # Check if they are all just noise
        decision = "NO_CLEAR_RETRIEVAL_GAIN"
        
    # ============================================================
    # PRINT RESULTS
    # ============================================================
    print("\n" + "=" * 60)
    print("PHASE 13A COMPLETE")
    print("=" * 60)
    
    print("\nCandidate Representations:")
    print(f"{'Representation':<20} {'R@1':>8} {'R@3':>8} {'R@5':>8} {'MRR@3':>8}")
    print("-" * 55)
    for name, res in results.items():
        print(f"{name:<20} {res['Recall@1']*100:>7.2f}% {res['Recall@3']*100:>7.2f}% {res['Recall@5']*100:>7.2f}% {res['MRR@3']:>8.4f}")
        
    print("\nPaired Improvements (vs BASELINE):")
    print(f"{'Representation':<20} {'Improved':>8} {'Regressed':>9} {'Unchanged':>9} {'Net':>5}")
    print("-" * 55)
    for name, p in paired.items():
        print(f"{name:<20} {p['improved']:>8} {p['regressed']:>9} {p['unchanged']:>9} {p['net']:>5}")
        
    print(f"\ngrocery_fresh R@5:")
    print(f"BASELINE: {base_results['intent_detail']['grocery_fresh']['k5']/base_results['intent_detail']['grocery_fresh']['count']*100:.2f}%")
    for name in paired:
        val = results[name]['intent_detail']['grocery_fresh']['k5']/results[name]['intent_detail']['grocery_fresh']['count']*100
        print(f"{name}: {val:.2f}%")
        
    print(f"\naccount_access R@5:")
    print(f"BASELINE: {base_results['intent_detail']['account_access']['k5']/base_results['intent_detail']['account_access']['count']*100:.2f}%")
    for name in paired:
        val = results[name]['intent_detail']['account_access']['k5']/results[name]['intent_detail']['account_access']['count']*100
        print(f"{name}: {val:.2f}%")
        
    print(f"\ndelivery_wrong_item R@5:")
    print(f"BASELINE: {base_results['intent_detail']['delivery_wrong_item']['k5']/base_results['intent_detail']['delivery_wrong_item']['count']*100:.2f}%")
    for name in paired:
        val = results[name]['intent_detail']['delivery_wrong_item']['k5']/results[name]['intent_detail']['delivery_wrong_item']['count']*100
        print(f"{name}: {val:.2f}%")
        
    print(f"\nDecision:\n{decision}")
    print(f"\nProduction model modified:\nNO")
    print(f"\nProduction FAISS modified:\nNO")
    print(f"\nGolden Set modified:\nNO")
    print(f"\nRecommended next phase:")
    if decision == "NO_CLEAR_RETRIEVAL_GAIN":
        print("PHASE 13B — CLASSIFIER PROMPT DIAGNOSTIC")
    else:
        print(f"PHASE 13B — DEPLOY {winner} QUERY REPRESENTATION")
        
    # ============================================================
    # SAVE REPORTS
    # ============================================================
    os.makedirs("reports", exist_ok=True)
    
    # JSON
    with open("reports/phase13a_query_representation_results.json", "w") as f:
        json.dump({
            "results": {name: {
                "Recall@1": r["Recall@1"],
                "Recall@3": r["Recall@3"],
                "Recall@5": r["Recall@5"],
                "MRR@3": r["MRR@3"]
            } for name, r in results.items()},
            "paired": paired,
            "confusions": confusions,
            "decision": decision
        }, f, indent=2)
        
    # MD
    with open("reports/phase13a_query_representation_results.md", "w") as f:
        f.write("# Phase 13A — Query Representation Pilot\n\n")
        
        f.write("## Candidate Representations\n\n")
        f.write("| Representation | R@1 | R@3 | R@5 | MRR@3 |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for name, res in results.items():
            f.write(f"| {name} | {res['Recall@1']*100:.2f}% | {res['Recall@3']*100:.2f}% | {res['Recall@5']*100:.2f}% | {res['MRR@3']:.4f} |\n")
            
        f.write("\n## Paired Improvements\n\n")
        f.write("| Representation | Improved | Regressed | Unchanged | Net |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for name, p in paired.items():
            f.write(f"| {name} | {p['improved']} | {p['regressed']} | {p['unchanged']} | {p['net']} |\n")
            
        f.write("\n## Intent-Level Results (Recall@3)\n\n")
        intents = list(base_results["intent_detail"].keys())
        intents.sort()
        f.write("| Intent | " + " | ".join(results.keys()) + " |\n")
        f.write("|---|" + "|".join(["---:"] * len(results)) + "|\n")
        for intent in intents:
            row = [intent]
            for name in results:
                d = results[name]["intent_detail"].get(intent, {"k3": 0, "count": 1})
                val = d["k3"] / d["count"] * 100 if d["count"] else 0
                row.append(f"{val:.1f}%")
            f.write("| " + " | ".join(row) + " |\n")
            
        f.write("\n## Confusion Boundary Analysis (Top 5)\n\n")
        f.write("Shows number of queries where the 'confuser' intent was ranked higher than the correct intent.\n\n")
        f.write("| Boundary | " + " | ".join(results.keys()) + " |\n")
        f.write("|---|" + "|".join(["---:"] * len(results)) + "|\n")
        for b_key in boundaries:
            key = f"{b_key[0]} <-> {b_key[1]}"
            row = [key]
            for name in results:
                row.append(str(confusions[name][key]["confusions"]))
            f.write("| " + " | ".join(row) + " |\n")
            
        f.write("\n## Failure Examples\n\n")
        for name, details in failure_details.items():
            if not details:
                continue
            f.write(f"### {name} changed queries\n")
            for d in sorted(details, key=lambda x: x["status"]):
                icon = "✅" if d["status"] == "improved" else "❌"
                f.write(f"- {icon} `{d['id']}` ({d['intent']}): Rank {d['base_rank']} → {d['new_rank']}\n")
            f.write("\n")
            
        f.write(f"## Winner Selection\n")
        f.write(f"**{decision}**\n")
        
        f.write("\n## Production Safety\n")
        f.write("- Golden Set modified: NO\n")
        f.write("- FAISS modified: NO\n")
        f.write("- MNRL model modified: NO\n")
        f.write("- Production code modified: NO\n")


if __name__ == "__main__":
    main()
