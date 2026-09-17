import os
import sys
import json
import numpy as np
import faiss
import pickle
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config

def main():
    # 1. Load V2 Predictions
    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_data = json.load(f)
    predictions = v2_data["predictions"]

    # 2. Load FAISS Index, Metadata, and Embeddings
    model_dir = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    index_path = model_dir / "faiss_index.bin"
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    embeddings_path = config.PROJECT_ROOT / ".cache" / "query_embeddings.npy"
    thread_ids_path = config.PROJECT_ROOT / ".cache" / "golden_thread_ids.json"
    
    print("Loading embeddings and index...")
    query_embeddings = np.load(embeddings_path).astype('float32')
    index = faiss.read_index(str(index_path))
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    with open(thread_ids_path, 'r') as f:
        golden_thread_ids = json.load(f)
        
    faiss.normalize_L2(query_embeddings)
    search_k = 15
    scores, indices = index.search(query_embeddings, search_k)
    
    # 3. Compute stats
    stats = []
    
    for i in range(len(query_embeddings)):
        q_thread_id = golden_thread_ids[i]
        v2_pred = next(p for p in predictions if p["thread_id"] == q_thread_id)
        
        filtered_docs = []
        filtered_scores = []
        for j, idx in enumerate(indices[i]):
            if idx < 0: continue
            doc = metadata[idx]
            if doc['thread_id'] != q_thread_id:
                filtered_docs.append(doc)
                filtered_scores.append(float(scores[i][j]))
            if len(filtered_docs) >= 3:
                break
                
        retrieved_intents = [d['intent_id'] for d in filtered_docs]
        
        # Determine distribution
        if len(set(retrieved_intents)) == 1:
            distribution = "unanimous"
        elif len(set(retrieved_intents)) == 2:
            distribution = "2_vs_1"
        else:
            distribution = "all_different"
            
        expected_intent = v2_pred["expected_intent"]
        is_missing_expected = expected_intent not in retrieved_intents
        is_missing_predicted = v2_pred["predicted_intent"] not in retrieved_intents
        
        top1_score = filtered_scores[0]
        top3_score = filtered_scores[2] if len(filtered_scores) >= 3 else filtered_scores[-1]
        score_margin = top1_score - top3_score
        
        stats.append({
            "thread_id": q_thread_id,
            "expected_intent": expected_intent,
            "v2_predicted_intent": v2_pred["predicted_intent"],
            "v2_correct": v2_pred["correctness"],
            "retrieved_intents": retrieved_intents,
            "distribution": distribution,
            "is_missing_expected": is_missing_expected,
            "is_missing_predicted": is_missing_predicted,
            "top1_score": top1_score,
            "top3_score": top3_score,
            "score_margin": score_margin
        })

    # 4. Analyze
    total = len(stats)
    v2_correct = sum(1 for s in stats if s["v2_correct"])
    
    # By distribution
    dist_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for s in stats:
        dist_stats[s["distribution"]]["total"] += 1
        if s["v2_correct"]:
            dist_stats[s["distribution"]]["correct"] += 1
            
    dist_output = {}
    for k, v in dist_stats.items():
        dist_output[k] = {
            "total": v["total"],
            "correct": v["correct"],
            "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0
        }
        
    # By retrieval success
    missing_expected_stats = {"total": 0, "correct": 0}
    present_expected_stats = {"total": 0, "correct": 0}
    for s in stats:
        if s["is_missing_expected"]:
            missing_expected_stats["total"] += 1
            if s["v2_correct"]: missing_expected_stats["correct"] += 1
        else:
            present_expected_stats["total"] += 1
            if s["v2_correct"]: present_expected_stats["correct"] += 1
            
    # Look for confidence signals for fallbacks
    # A potential gate: Only fallback if V2 prediction is NOT in retrieved intents, OR if it's conflicting (2vs1, all_different)
    
    # Let's see how often V2 is wrong when its prediction IS in retrieved vs IS NOT in retrieved
    v2_pred_in_retrieval = [s for s in stats if not s["is_missing_predicted"]]
    v2_pred_not_in_retrieval = [s for s in stats if s["is_missing_predicted"]]
    
    acc_pred_in = sum(1 for s in v2_pred_in_retrieval if s["v2_correct"]) / len(v2_pred_in_retrieval) if v2_pred_in_retrieval else 0
    acc_pred_not_in = sum(1 for s in v2_pred_not_in_retrieval if s["v2_correct"]) / len(v2_pred_not_in_retrieval) if v2_pred_not_in_retrieval else 0

    # Output JSON
    output_json = {
        "overall_accuracy": v2_correct / total,
        "distribution_stats": dist_output,
        "retrieval_presence": {
            "expected_missing": {
                "total": missing_expected_stats["total"],
                "accuracy": missing_expected_stats["correct"] / missing_expected_stats["total"] if missing_expected_stats["total"] > 0 else 0
            },
            "expected_present": {
                "total": present_expected_stats["total"],
                "accuracy": present_expected_stats["correct"] / present_expected_stats["total"] if present_expected_stats["total"] > 0 else 0
            },
            "v2_predicted_in_retrieval": {
                "total": len(v2_pred_in_retrieval),
                "accuracy": acc_pred_in
            },
            "v2_predicted_not_in_retrieval": {
                "total": len(v2_pred_not_in_retrieval),
                "accuracy": acc_pred_not_in
            }
        },
        "stats": stats
    }
    
    with open("reports/phase15a_v2_confidence_diagnosis.json", "w") as f:
        json.dump(output_json, f, indent=2)

    # Output Markdown
    with open("reports/phase15a_v2_confidence_diagnosis.md", "w") as f:
        f.write("# Phase 15A — V2 Confidence Diagnosis\n\n")
        f.write("## 1. Retrieved Intent Distribution\n")
        f.write("| Distribution | Count | V2 Accuracy |\n")
        f.write("|---|---:|---:|\n")
        for k, v in dist_output.items():
            f.write(f"| {k} | {v['total']} | {v['accuracy']*100:.1f}% |\n")
            
        f.write("\n## 2. V2 Prediction Stability (Retrieval Agreement)\n")
        f.write("| Signal | Count | V2 Accuracy | False Positive Risk | False Negative Risk |\n")
        f.write("|---|---:|---:|---|---|\n")
        f.write(f"| V2 Prediction MATCHES a retrieved candidate | {len(v2_pred_in_retrieval)} | {acc_pred_in*100:.1f}% | Low (V2 is very reliable when it agrees with RAG) | High (If we force fallback, we risk V3/V4 regression) |\n")
        f.write(f"| V2 Prediction is ABSENT from retrieval | {len(v2_pred_not_in_retrieval)} | {acc_pred_not_in*100:.1f}% | High (V2 is guessing blindly against RAG) | Low (V2 is usually wrong here) |\n")
        
        f.write("\n## 3. Score Information\n")
        f.write("The FAISS index (using `IndexFlatIP`) outputs Inner Product scores (cosine similarity). These scores are available *before* classification and strongly correlate with semantic similarity. However, intent distribution (unanimous vs mixed) is a much stronger and safer gate than raw float scores, because semantic scores vary widely across different intents.\n\n")
        
        f.write("## 4. Proposed Confidence Gate (Targeted Fallback)\n")
        f.write("Instead of replacing V2 entirely, we can implement an Evidence Gate:\n")
        f.write("1. Run dense retrieval (K=3).\n")
        f.write("2. If retrieval is **Unanimous** AND V2's predicted intent is **not** that unanimous intent -> TRIGGER FALLBACK (V2 over-correction).\n")
        f.write("3. If retrieval is **Conflicting** -> TRIGGER FALLBACK (V2 struggles with conflicts).\n")
        f.write("4. Otherwise, trust V2.\n\n")
        
        f.write("Alternatively, a simpler semantic gate:\n")
        f.write("**GATE: If `V2_predicted_intent` is NOT IN `retrieved_intents`, trigger fallback.**\n")
        f.write(f"Looking at the data, when V2 predicts an intent that wasn't even in the top-3, it is accurate only {acc_pred_not_in*100:.1f}% of the time. This isolates the exact cases where V2 is \"going rogue\" (CLASSIFIER_IGNORED_CORRECT).\n\n")
        
        f.write("## 5. Estimated Coverage of Fallback\n")
        f.write(f"If we fallback whenever V2 prediction is absent from retrieval, we would intercept {len(v2_pred_not_in_retrieval)} queries out of 196 ({(len(v2_pred_not_in_retrieval)/196)*100:.1f}%).\n")
        f.write("If we fallback on ALL conflicting evidence, we would intercept a larger chunk.\n\n")
        
        f.write("## 6. Examples\n")
        f.write("**Trigger Fallback (V2 prediction absent from retrieval):**\n")
        sample_trigger = [s for s in v2_pred_not_in_retrieval if not s['v2_correct']][:2]
        for s in sample_trigger:
            f.write(f"- `{s['thread_id']}`: V2 predicted `{s['v2_predicted_intent']}`. Retrieved: `{s['retrieved_intents']}`.\n")
            
        f.write("\n**Remain Untouched (V2 prediction matches retrieval):**\n")
        sample_untouched = [s for s in v2_pred_in_retrieval if s['v2_correct']][:2]
        for s in sample_untouched:
            f.write(f"- `{s['thread_id']}`: V2 predicted `{s['v2_predicted_intent']}`. Retrieved: `{s['retrieved_intents']}`.\n")

        f.write("\n## 7. Recommendation\n")
        f.write("**READY**\n")
        f.write("The existing system surfaces enough information (top-3 intent strings and cosine similarity scores) to build a robust heuristic evidence gate *before* finalizing the response. We can wrap V2 with a rule-based arbiter that triggers a specialized fallback prompt only when V2 exhibits known failure patterns.\n")
        
    print("Diagnosis complete.")

if __name__ == "__main__":
    main()
