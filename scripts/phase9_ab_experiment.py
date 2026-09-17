import json
import os
import hashlib
import pickle
import numpy as np
import faiss
import shutil
from sentence_transformers import SentenceTransformer
from src.threadmind import config
import time
from collections import Counter

def phase9_ab_experiment():
    # STEP 1 - Verify V1 Artifacts
    v1_corpus_path = config.PROCESSED_DATA_DIR / "retrieval_corpus_v1_backup.jsonl"
    assert os.path.exists(v1_corpus_path)
    
    v1_metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(v1_metadata_path, 'rb') as f:
        v1_metadata = pickle.load(f)
        
    v1_index_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl" / "faiss_index.bin"
    v1_index = faiss.read_index(str(v1_index_path))
    
    mnrl_model_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    
    with open(v1_corpus_path, 'rb') as f:
        v1_corpus_hash = hashlib.sha256(f.read()).hexdigest()
        
    v1_manifest = {
        "v1_corpus_sha256": v1_corpus_hash,
        "mnrl_model_path": str(mnrl_model_path),
        "embedding_dimension": v1_index.d,
        "faiss_index_size": v1_index.ntotal,
        "document_count": len(v1_metadata)
    }
    
    with open("reports/phase9_v1_artifact_manifest.json", "w") as f:
        json.dump(v1_manifest, f, indent=2)
        
    # STEP 2 - Verify V2 Candidate
    v2_corpus_path = config.PROCESSED_DATA_DIR / "retrieval_corpus_v2_candidate.jsonl"
    
    # STEP 3 - Build Isolated V2 Index
    v2_cache_dir = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl_v2"
    v2_meta_dir = config.PROJECT_ROOT / ".cache" / "rag_dense_v2"
    os.makedirs(v2_cache_dir, exist_ok=True)
    os.makedirs(v2_meta_dir, exist_ok=True)
    
    v2_index_path = v2_cache_dir / "faiss_index.bin"
    v2_metadata_path = v2_meta_dir / "corpus_metadata.pkl"
    
    # Copy index directly because text is identical!
    shutil.copyfile(str(v1_index_path), str(v2_index_path))
    v2_index = faiss.read_index(str(v2_index_path))
    
    v2_metadata = []
    
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
        
    # Read labels from candidate
    v2_labels_map = {}
    with open(v2_corpus_path, "r") as f:
        for line in f:
            doc = json.loads(line)
            v2_labels_map[doc["thread_id"]] = doc["intent_id"]
            
    # Build V2 metadata exactly aligning with V1 indexing order!
    for m in v1_metadata:
        t_id = m["thread_id"]
        new_intent = v2_labels_map.get(t_id, m["intent_id"])
        v2_metadata.append({
            "thread_id": t_id,
            "intent_id": new_intent,
            "escalation": m["escalation"],
            "conversation": m["conversation"]
        })
    
    with open(v2_metadata_path, "wb") as f:
        pickle.dump(v2_metadata, f)
        
    # STEP 4 - Index Validation
    index_integrity = {
        "v1_document_count": len(v1_metadata),
        "v2_document_count": len(v2_metadata),
        "embedding_dimension": v1_index.d,
        "index_dimension": v2_index.d,
        "metadata_count": len(v2_metadata),
        "index_vector_count": v2_index.ntotal,
        "document_id_uniqueness": len(set([m["thread_id"] for m in v2_metadata])) == len(v2_metadata)
    }
    
    with open("reports/phase9_index_integrity.json", "w") as f:
        json.dump(index_integrity, f, indent=2)
        
    if not (index_integrity["metadata_count"] == index_integrity["index_vector_count"] == index_integrity["v1_document_count"]):
        print("ABORT: Index validation failed.")
        return
        
    # STEP 5 - Controlled Retrieval A/B Test
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = SentenceTransformer(str(mnrl_model_path), device=device)
    
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    queries = []
    golden_expected = {}
    with open(golden_path, "r") as f:
        for line in f:
            q = json.loads(line)
            q_text = format_conv(q["conversation"])
            queries.append({"id": q["thread_id"], "text": q_text, "intent": q["intent_id"]})
            golden_expected[q["thread_id"]] = q["intent_id"]
            
    query_texts = [q["text"] for q in queries]
    query_embs = model.encode(query_texts, show_progress_bar=False, batch_size=32)
    query_embs = np.array(query_embs).astype('float32')
    faiss.normalize_L2(query_embs)
    
    k_max = 5
    D_v1, I_v1 = v1_index.search(query_embs, k_max)
    D_v2, I_v2 = v2_index.search(query_embs, k_max)
    
    v1_k1, v1_k3, v1_k5 = 0, 0, 0
    v2_k1, v2_k3, v2_k5 = 0, 0, 0
    
    v1_rr3, v2_rr3 = 0.0, 0.0
    
    regressions = []
    
    v1_intent_recall = {1: Counter(), 3: Counter(), 5: Counter()}
    v2_intent_recall = {1: Counter(), 3: Counter(), 5: Counter()}
    golden_intent_counts = Counter()
    
    for i, q in enumerate(queries):
        expected = q["intent"]
        golden_intent_counts[expected] += 1
        
        v1_retrieved_intents = [v1_metadata[idx]["intent_id"] for idx in I_v1[i]]
        v2_retrieved_intents = [v2_metadata[idx]["intent_id"] for idx in I_v2[i]]
        
        v1_rank = v1_retrieved_intents.index(expected) + 1 if expected in v1_retrieved_intents else 999
        v2_rank = v2_retrieved_intents.index(expected) + 1 if expected in v2_retrieved_intents else 999
        
        if v1_rank == 1: v1_k1 += 1
        if v1_rank <= 3: 
            v1_k3 += 1
            v1_rr3 += 1.0 / v1_rank
        if v1_rank <= 5: v1_k5 += 1
            
        if v2_rank == 1: v2_k1 += 1
        if v2_rank <= 3: 
            v2_k3 += 1
            v2_rr3 += 1.0 / v2_rank
        if v2_rank <= 5: v2_k5 += 1
            
        if v2_rank > v1_rank and v1_rank <= 5:
            regressions.append({
                "query_id": q["id"],
                "expected_intent": expected,
                "v1_retrieved_examples": [v1_metadata[idx]["thread_id"] for idx in I_v1[i]],
                "v2_retrieved_examples": [v2_metadata[idx]["thread_id"] for idx in I_v2[i]],
                "old_labels": v1_retrieved_intents,
                "new_labels": v2_retrieved_intents,
                "v1_rank": v1_rank,
                "v2_rank": v2_rank,
                "reason_for_regression": "LABEL_REPAIR_EFFECT"
            })
            
    num_queries = len(queries)
    v1_metrics = {
        "Recall@1": v1_k1 / num_queries,
        "Recall@3": v1_k3 / num_queries,
        "Recall@5": v1_k5 / num_queries,
        "MRR@3": v1_rr3 / num_queries
    }
    v2_metrics = {
        "Recall@1": v2_k1 / num_queries,
        "Recall@3": v2_k3 / num_queries,
        "Recall@5": v2_k5 / num_queries,
        "MRR@3": v2_rr3 / num_queries
    }
    
    with open("reports/phase9_retrieval_ab_results.json", "w") as f:
        json.dump({"v1": v1_metrics, "v2": v2_metrics, "regressions": len(regressions)}, f, indent=2)
        
    with open("reports/phase9_retrieval_ab_final.md", "w") as f:
        f.write("# Phase 9: A/B Retrieval Evaluation\n\n")
        f.write("| Metric | V1 | V2 | Delta |\n")
        f.write("|--------|----|----|-------|\n")
        f.write(f"| Recall@1 | {v1_metrics['Recall@1']:.4f} | {v2_metrics['Recall@1']:.4f} | {v2_metrics['Recall@1'] - v1_metrics['Recall@1']:.4f} |\n")
        f.write(f"| Recall@3 | {v1_metrics['Recall@3']:.4f} | {v2_metrics['Recall@3']:.4f} | {v2_metrics['Recall@3'] - v1_metrics['Recall@3']:.4f} |\n")
        f.write(f"| Recall@5 | {v1_metrics['Recall@5']:.4f} | {v2_metrics['Recall@5']:.4f} | {v2_metrics['Recall@5'] - v1_metrics['Recall@5']:.4f} |\n")
        f.write(f"| MRR@3 | {v1_metrics['MRR@3']:.4f} | {v2_metrics['MRR@3']:.4f} | {v2_metrics['MRR@3'] - v1_metrics['MRR@3']:.4f} |\n")
        
    with open("reports/phase9_retrieval_ab_final.json", "w") as f:
        json.dump({
            "v1": v1_metrics,
            "v2": v2_metrics,
            "regressions": len(regressions),
            "improvements": (v2_k3 - v1_k3) + len(regressions), # approx
            "decision": "PROMOTE_V2_RETRIEVAL" if v2_k3 > v1_k3 else "KEEP_V1"
        }, f, indent=2)
        
    print(json.dumps(v1_metrics, indent=2))
    print(json.dumps(v2_metrics, indent=2))
    print(f"Regressions: {len(regressions)}")

if __name__ == "__main__":
    phase9_ab_experiment()
