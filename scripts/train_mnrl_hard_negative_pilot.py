import json
import os
import pickle
import random
import time
import torch
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, losses, InputExample
from torch.utils.data import DataLoader
from src.threadmind import config
from collections import Counter

# macOS fallback for tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def train_mnrl_pilot():
    print("Loading datasets...")
    
    # 1. Load Golden Set IDs (to exclude)
    golden_ids = set()
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
        for line in f:
            golden_ids.add(json.loads(line)["thread_id"])
            
    # 2. Load Corpus Metadata (has V2 labels)
    v1_metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(v1_metadata_path, 'rb') as f:
        v1_metadata = pickle.load(f)
        
    intent_to_docs = {}
    for meta in v1_metadata:
        if meta["thread_id"] in golden_ids:
            continue
        intent = meta["intent_id"]
        if intent not in intent_to_docs:
            intent_to_docs[intent] = []
        intent_to_docs[intent].append(meta["conversation"])
        
    # 3. Load Hard Negatives
    hn_path = config.PROCESSED_DATA_DIR / "hard_negatives_v1.jsonl"
    hard_negatives = []
    with open(hn_path, "r") as f:
        for line in f:
            record = json.loads(line)
            if record["hard_negative_strength"] == "HIGH":
                hard_negatives.append(record)
                
    # Target boundaries prioritization
    target_pairs = {
        tuple(sorted(["account_access", "delivery_wrong_item"])),
        tuple(sorted(["account_access", "delivery_missing"])),
        tuple(sorted(["grocery_fresh", "returns_refunds"])),
        tuple(sorted(["account_billing", "grocery_fresh"])),
        tuple(sorted(["account_access", "delivery_delayed"]))
    }
    
    # 4. Construct Triplets
    random.seed(42)
    training_data = []
    
    for hn in hard_negatives:
        q_intent = hn["query_intent"]
        neg_text = hn["negative_text"]
        
        # We replace the query with a random corpus positive to prevent Golden Set leakage
        if q_intent in intent_to_docs and len(intent_to_docs[q_intent]) >= 2:
            docs = random.sample(intent_to_docs[q_intent], 2)
            anchor = docs[0]
            positive = docs[1]
            
            training_data.append({
                "anchor": anchor,
                "positive": positive,
                "negative": neg_text,
                "intent": q_intent,
                "confusion_boundary": hn["confusion_boundary"],
                "is_target": tuple(sorted(hn["confusion_boundary"].split("<->"))) in target_pairs
            })

    # Shuffle and split
    random.shuffle(training_data)
    split_idx = int(len(training_data) * 0.8)
    train_split = training_data[:split_idx]
    val_split = training_data[split_idx:]
    
    pilot_data_path = config.PROCESSED_DATA_DIR / "mnrl_hard_negative_pilot_v1.jsonl"
    with open(pilot_data_path, "w") as f:
        for rec in training_data:
            f.write(json.dumps(rec) + "\n")
            
    print(f"Constructed {len(train_split)} train and {len(val_split)} val triplets.")
    
    # 5. Train Model
    mnrl_model_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    model = SentenceTransformer(str(mnrl_model_path), device=device)
    
    train_examples = []
    for rec in train_split:
        train_examples.append(InputExample(texts=[rec["anchor"], rec["positive"], rec["negative"]]))
        
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
    
    pilot_model_dir = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl_hn_pilot_v1"
    os.makedirs(pilot_model_dir, exist_ok=True)
    
    print("Training pilot model...")
    t0 = time.time()
    
    # Very conservative config
    epochs = 1
    warmup_steps = int(len(train_dataloader) * 0.1)
    
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=warmup_steps,
        output_path=str(pilot_model_dir),
        show_progress_bar=True
    )
    
    train_time = time.time() - t0
    print(f"Training completed in {train_time:.1f}s")
    
    # 6. Evaluation
    print("Evaluating Baseline and Pilot models...")
    
    def evaluate_model(model_dir):
        eval_model = SentenceTransformer(str(model_dir), device="cpu")
        
        # Build Index
        corpus_texts = [m["conversation"] for m in v1_metadata]
        corpus_embs = eval_model.encode(corpus_texts, show_progress_bar=False, batch_size=128)
        corpus_embs = np.array(corpus_embs).astype('float32')
        faiss.normalize_L2(corpus_embs)
        
        dim = corpus_embs.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(corpus_embs)
        
        # Load queries
        golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
        queries = []
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
            
        with open(golden_path, "r") as f:
            for line in f:
                q = json.loads(line)
                queries.append({
                    "id": q["thread_id"], 
                    "text": format_conv(q.get("messages", q.get("conversation", []))), 
                    "intent": q["intent_id"]
                })
                
        query_texts = [q["text"] for q in queries]
        query_embs = eval_model.encode(query_texts, show_progress_bar=False, batch_size=32)
        query_embs = np.array(query_embs).astype('float32')
        faiss.normalize_L2(query_embs)
        
        D, I = index.search(query_embs, 5)
        
        metrics = {"k1": 0, "k3": 0, "k5": 0, "rr3": 0.0}
        intent_metrics = {q["intent"]: {"k5": 0, "count": 0} for q in queries}
        retrieved_intents_dict = {}
        
        for i, q in enumerate(queries):
            expected = q["intent"]
            intent_metrics[expected]["count"] += 1
            
            retrieved_intents = [v1_metadata[idx]["intent_id"] for idx in I[i]]
            retrieved_intents_dict[q["id"]] = retrieved_intents
            
            rank = retrieved_intents.index(expected) + 1 if expected in retrieved_intents else 999
            
            if rank == 1: metrics["k1"] += 1
            if rank <= 3: 
                metrics["k3"] += 1
                metrics["rr3"] += 1.0 / rank
            if rank <= 5: 
                metrics["k5"] += 1
                intent_metrics[expected]["k5"] += 1
                
        num_queries = len(queries)
        final_metrics = {
            "Recall@1": metrics["k1"] / num_queries,
            "Recall@3": metrics["k3"] / num_queries,
            "Recall@5": metrics["k5"] / num_queries,
            "MRR@3": metrics["rr3"] / num_queries,
            "intent_metrics": intent_metrics,
            "retrieved_intents_dict": retrieved_intents_dict
        }
        return final_metrics
        
    baseline_res = evaluate_model(mnrl_model_path)
    pilot_res = evaluate_model(pilot_model_dir)
    
    # 7. Failure Analysis
    improved = 0
    regressed = 0
    unchanged = 0
    
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    with open(golden_path, "r") as f:
        golden_queries = [json.loads(line) for line in f]
        
    for q in golden_queries:
        qid = q["thread_id"]
        expected = q["intent_id"]
        
        base_ret = baseline_res["retrieved_intents_dict"][qid]
        pilot_ret = pilot_res["retrieved_intents_dict"][qid]
        
        base_rank = base_ret.index(expected) + 1 if expected in base_ret else 999
        pilot_rank = pilot_ret.index(expected) + 1 if expected in pilot_ret else 999
        
        if pilot_rank < base_rank and (pilot_rank <= 5 or base_rank > 5):
            if pilot_rank <= 5:
                improved += 1
        elif pilot_rank > base_rank and (base_rank <= 5):
            regressed += 1
        else:
            unchanged += 1
            
    # Decision
    gf_base = baseline_res["intent_metrics"]["grocery_fresh"]["k5"] / baseline_res["intent_metrics"]["grocery_fresh"]["count"]
    gf_pilot = pilot_res["intent_metrics"]["grocery_fresh"]["k5"] / pilot_res["intent_metrics"]["grocery_fresh"]["count"]
    
    aa_base = baseline_res["intent_metrics"]["account_access"]["k5"] / baseline_res["intent_metrics"]["account_access"]["count"]
    aa_pilot = pilot_res["intent_metrics"]["account_access"]["k5"] / pilot_res["intent_metrics"]["account_access"]["count"]
    
    dwi_base = baseline_res["intent_metrics"]["delivery_wrong_item"]["k5"] / baseline_res["intent_metrics"]["delivery_wrong_item"]["count"]
    dwi_pilot = pilot_res["intent_metrics"]["delivery_wrong_item"]["k5"] / pilot_res["intent_metrics"]["delivery_wrong_item"]["count"]
    
    if pilot_res["Recall@3"] > baseline_res["Recall@3"] or pilot_res["Recall@5"] > baseline_res["Recall@5"]:
        if regressed <= 2 and gf_pilot > gf_base:
            decision = "PROMISING"
        else:
            decision = "REQUIRES_REVIEW"
    else:
        decision = "REJECT"
        
    # Reports
    report_json = {
        "baseline": {
            "Recall@1": baseline_res["Recall@1"],
            "Recall@3": baseline_res["Recall@3"],
            "Recall@5": baseline_res["Recall@5"],
            "MRR@3": baseline_res["MRR@3"]
        },
        "pilot": {
            "Recall@1": pilot_res["Recall@1"],
            "Recall@3": pilot_res["Recall@3"],
            "Recall@5": pilot_res["Recall@5"],
            "MRR@3": pilot_res["MRR@3"]
        },
        "improvements": improved,
        "regressions": regressed,
        "grocery_fresh": gf_pilot,
        "account_access": aa_pilot,
        "delivery_wrong_item": dwi_pilot,
        "decision": decision
    }
    
    with open("reports/phase11b_mnrl_pilot.json", "w") as f:
        json.dump(report_json, f, indent=2)
        
    with open("reports/phase11b_mnrl_pilot.md", "w") as f:
        f.write("# Phase 11B — MNRL Hard Negative Pilot\n\n")
        f.write("## Dataset\n")
        f.write(f"- Train count: {len(train_split)}\n")
        f.write(f"- Validation count: {len(val_split)}\n")
        f.write("\n## Pilot Results\n")
        f.write("| Metric | Baseline | Pilot | Delta |\n")
        f.write("|---|---:|---:|---:|\n")
        f.write(f"| Recall@1 | {baseline_res['Recall@1']:.4f} | {pilot_res['Recall@1']:.4f} | {pilot_res['Recall@1'] - baseline_res['Recall@1']:.4f} |\n")
        f.write(f"| Recall@3 | {baseline_res['Recall@3']:.4f} | {pilot_res['Recall@3']:.4f} | {pilot_res['Recall@3'] - baseline_res['Recall@3']:.4f} |\n")
        f.write(f"| Recall@5 | {baseline_res['Recall@5']:.4f} | {pilot_res['Recall@5']:.4f} | {pilot_res['Recall@5'] - baseline_res['Recall@5']:.4f} |\n")
        f.write(f"| MRR@3 | {baseline_res['MRR@3']:.4f} | {pilot_res['MRR@3']:.4f} | {pilot_res['MRR@3'] - baseline_res['MRR@3']:.4f} |\n")
        f.write(f"\n## Decision\n{decision}\n")
        f.write(f"\n## Recommendation\nPHASE 11C — HYPERPARAMETER TUNING OR INTEGRATION\n")
        
    print("\nPHASE 11B COMPLETE\n")
    print(f"Baseline Recall@1:\n{baseline_res['Recall@1'] * 100:.2f}%")
    print(f"Pilot Recall@1:\n{pilot_res['Recall@1'] * 100:.2f}%")
    print(f"Baseline Recall@3:\n{baseline_res['Recall@3'] * 100:.2f}%")
    print(f"Pilot Recall@3:\n{pilot_res['Recall@3'] * 100:.2f}%")
    print(f"Baseline Recall@5:\n{baseline_res['Recall@5'] * 100:.2f}%")
    print(f"Pilot Recall@5:\n{pilot_res['Recall@5'] * 100:.2f}%")
    print(f"Baseline MRR@3:\n{baseline_res['MRR@3']:.4f}")
    print(f"Pilot MRR@3:\n{pilot_res['MRR@3']:.4f}")
    print(f"Retrieval improvements:\n{improved}")
    print(f"Retrieval regressions:\n{regressed}")
    print(f"grocery_fresh Recall@5:\n{gf_pilot * 100:.2f}%")
    print(f"account_access Recall@5:\n{aa_pilot * 100:.2f}%")
    print(f"delivery_wrong_item Recall@5:\n{dwi_pilot * 100:.2f}%")
    print(f"\nDecision:\n{decision}")
    print("Production model modified:\nNO")
    print("Production FAISS modified:\nNO")
    print("Golden Set modified:\nNO")
    print("Recommended next phase:\nPHASE 12 — INTEGRATION" if decision == "PROMISING" else "PHASE 11C — REVISION")
    
if __name__ == "__main__":
    train_mnrl_pilot()
