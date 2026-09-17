import os
import sys
import json
import time
import math
import random
import pickle
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config
from src.threadmind.baselines.rule_baseline import RuleBaseline

import torch
import numpy as np
from datasets import Dataset
from sentence_transformers import SentenceTransformer, losses
import faiss

# Disable tokenizers parallelism to avoid macOS deadlocks
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def format_conversation(messages):
    parts = []
    for m in messages:
        role = "User" if m.get("inbound", True) else "Agent"
        parts.append(f"{role}: {m['text']}")
    return "\n".join(parts)

def load_or_create_train_pairs():
    cache_file = config.PROJECT_ROOT / ".cache" / "mnrl_train_dict.json"
    if cache_file.exists():
        with open(cache_file, "r") as f:
            return json.load(f)
            
    print("Generating training pairs from train_split.jsonl...")
    rule_system = RuleBaseline()
    
    golden_ids = set()
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
        for line in f:
            golden_ids.add(json.loads(line)["thread_id"])
            
    val_ids = set()
    with open(config.PROCESSED_DATA_DIR / "val_split.jsonl") as f:
        for line in f:
            val_ids.add(json.loads(line)["thread_id"])

    intent_groups = {}
    with open(config.PROCESSED_DATA_DIR / "train_split.jsonl") as f:
        for line in f:
            thread = json.loads(line)
            tid = thread["thread_id"]
            
            if tid in golden_ids or tid in val_ids:
                continue
                
            conv = []
            for m in thread["messages"]:
                conv.append({
                    "author_role": "customer" if m.get("inbound", True) else "agent",
                    "text": m["text"]
                })
            
            pred = rule_system.predict(conv)
            intent = pred["predicted_intent"]
            
            if intent == "other_support":
                continue
                
            text = format_conversation(thread["messages"])
            if intent not in intent_groups:
                intent_groups[intent] = []
            intent_groups[intent].append(text)

    train_dict = {"anchor": [], "positive": []}
    MAX_PAIRS_PER_INTENT = 1000

    random.seed(42)
    for intent, texts in intent_groups.items():
        if len(texts) < 2:
            continue
        random.shuffle(texts)
        pairs_made = 0
        for i in range(0, len(texts)-1, 2):
            if pairs_made >= MAX_PAIRS_PER_INTENT:
                break
            train_dict["anchor"].append(texts[i])
            train_dict["positive"].append(texts[i+1])
            pairs_made += 1

    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(train_dict, f)
        
    return train_dict

def load_or_create_val_queries():
    cache_file = config.PROJECT_ROOT / ".cache" / "val_queries.json"
    if cache_file.exists():
        with open(cache_file, "r") as f:
            return json.load(f)
            
    print("Generating validation queries from val_split.jsonl...")
    rule_system = RuleBaseline()
    
    meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(meta_path, "rb") as f:
        corpus_metadata = pickle.load(f)
        
    faiss_thread_ids = {m["thread_id"]: i for i, m in enumerate(corpus_metadata)}
    val_queries = []

    with open(config.PROCESSED_DATA_DIR / "val_split.jsonl") as f:
        for line in f:
            thread = json.loads(line)
            tid = thread["thread_id"]
            
            conv = []
            for m in thread["messages"]:
                conv.append({
                    "author_role": "customer" if m.get("inbound", True) else "agent",
                    "text": m["text"]
                })
            pred = rule_system.predict(conv)
            intent = pred["predicted_intent"]
            
            if intent != "other_support" and tid in faiss_thread_ids:
                val_queries.append({
                    "thread_id": tid,
                    "intent": intent,
                    "conversation": thread["messages"],
                    "query_text": format_conversation(thread["messages"])
                })

    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(val_queries, f)
        
    return val_queries


def main():
    print("TRAINING DATA: train_split.jsonl")
    print("VALIDATION DATA: val_split.jsonl")
    print("GOLDEN SET USED FOR TRAINING: NO")
    print("MODEL: all-MiniLM-L6-v2")
    print("LOSS: MultipleNegativesRankingLoss\n")
    
    device = "cpu"
    print(f"Device: {device} (forced for stability & speed on MNRL)")
    
    # 1. Load Data
    train_dict = load_or_create_train_pairs()
    print(f"Loaded {len(train_dict['anchor'])} positive pairs for MNRL.")
    
    # 2. Train Model
    output_model_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    history_path = config.PROJECT_ROOT / "reports" / "mnrl_training_history.json"
    checkpoint_dir = config.PROJECT_ROOT / ".cache" / "mnrl_checkpoints"
    os.makedirs(output_model_path, exist_ok=True)
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Check for resume
    start_epoch = 0
    history = []
    model_name_or_path = "all-MiniLM-L6-v2"
    
    if history_path.exists():
        with open(history_path, "r") as f:
            history = json.load(f)
        if len(history) > 0:
            start_epoch = history[-1]["epoch"]
            latest_ckpt = checkpoint_dir / f"epoch_{start_epoch}"
            if latest_ckpt.exists():
                model_name_or_path = str(latest_ckpt)
                print(f"Resuming from epoch {start_epoch} checkpoint...")
                
    model = SentenceTransformer(model_name_or_path, device=device)
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
            
    batch_size = 32
    num_epochs = 3
    train_dl = DataLoader(DictDataset(train_dict), shuffle=True, batch_size=batch_size, collate_fn=model.smart_batching_collate)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    
    # LR Scheduler (linear warmup)
    total_steps = len(train_dl) * num_epochs
    warmup_steps = int(total_steps * 0.1)
    
    def get_lr_multiplier(step):
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        return max(0.0, float(total_steps - step) / float(max(1, total_steps - warmup_steps)))
        
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=get_lr_multiplier)
    
    # Advance scheduler if resuming
    if start_epoch > 0:
        for _ in range(start_epoch * len(train_dl)):
            scheduler.step()
            
    print("\nStarting Training...")
    global_step = start_epoch * len(train_dl)
    t0_train = time.time()
    
    for epoch in range(start_epoch + 1, num_epochs + 1):
        model.train()
        epoch_loss = 0.0
        
        with tqdm(total=len(train_dl), desc=f"Epoch {epoch}/{num_epochs}") as pbar:
            for i, batch in enumerate(train_dl):
                features, labels = batch
                for f in features:
                    for key in f:
                        f[key] = f[key].to(device)
                        
                loss_val = train_loss(features, labels)
                loss_val.backward()
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                
                epoch_loss += loss_val.item()
                global_step += 1
                
                current_lr = scheduler.get_last_lr()[0]
                elapsed = time.time() - t0_train
                
                pbar.set_postfix({
                    "loss": f"{loss_val.item():.4f}", 
                    "lr": f"{current_lr:.2e}"
                })
                pbar.update(1)
                
        avg_loss = epoch_loss / len(train_dl)
        print(f"Epoch {epoch} Complete | Avg Loss: {avg_loss:.4f}")
        
        # Save checkpoint
        ckpt_path = checkpoint_dir / f"epoch_{epoch}"
        model.save_pretrained(str(ckpt_path))
        
        history.append({
            "epoch": epoch,
            "avg_loss": round(avg_loss, 4),
            "lr": current_lr
        })
        with open(history_path, "w") as f:
            json.dump(history, f, indent=2)
            
    model.save_pretrained(str(output_model_path))
    print(f"\nTraining complete. Saved final model to {output_model_path}")
    
    # 3. FAISS Re-indexing
    print("\n[3/7] Re-indexing FAISS corpus with Fine-tuned model...")
    meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(meta_path, "rb") as f:
        corpus_metadata = pickle.load(f)
        
    texts_to_encode = [m["conversation"] for m in corpus_metadata]
    print(f"  Encoding {len(texts_to_encode)} documents...")
    
    t0 = time.time()
    # Use MPS for fast inference if available
    encode_device = "mps" if torch.backends.mps.is_available() else "cpu"
    encode_model = SentenceTransformer(str(output_model_path), device=encode_device)
    embeddings = encode_model.encode(texts_to_encode, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings).astype('float32')
    print(f"  Encoded in {time.time()-t0:.1f}s.")
    
    faiss.normalize_L2(embeddings)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    mnrl_index_path = output_model_path / "faiss_index.bin"
    faiss.write_index(index, str(mnrl_index_path))
    
    # 4. Load Eval Queries
    val_queries = load_or_create_val_queries()
    print(f"\n[4/7] Evaluating {len(val_queries)} queries (same as baseline)...")
    
    # 5. Evaluate
    k_values = [1, 3, 5]
    max_k = 6
    
    results = {k: {"hits": 0, "mrr_sum": 0.0} for k in k_values}
    latencies = []
    
    for i, q in enumerate(tqdm(val_queries, desc="Evaluating")):
        target_intent = q["intent"]
        
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
            
    # 6. Save Results
    print("\n[6/7] Computing final metrics...")
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
    
    print(f"\n{'='*50}")
    print("BASELINE COMPARISON (from Step 14a)")
    print(f"{'='*50}")
    print("Recall@1: 0.5842")
    print("Recall@3: 0.8008")
    print("Recall@5: 0.8568")
    print("MRR@3:    0.6816")
    
    output = {
        "hyperparameters": {
            "model": "all-MiniLM-L6-v2",
            "epochs": num_epochs,
            "batch_size": batch_size,
            "loss": "MultipleNegativesRankingLoss",
            "training_pairs": len(train_dict["anchor"]),
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
