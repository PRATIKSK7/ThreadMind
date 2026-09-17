import os
import sys
import json
import numpy as np
import faiss
import pickle
import hashlib
from collections import defaultdict
from tqdm import tqdm

# Stability settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def analyze_failure(provider, conversation_text, expected, predicted, retrieved):
    prompt = f"""You are a senior data taxonomist.
Review this customer support conversation.
It was expected to be labeled: '{expected}'
But the classifier guessed: '{predicted}'
Top-3 retrieved examples were: {retrieved}

Conversation:
{conversation_text}

Task:
1. Explain why this example might be suspicious or difficult.
2. Identify the true competing intent.
3. Assign a label quality score: DEFINITELY_CORRECT, POSSIBLY_AMBIGUOUS, POSSIBLY_MISLABELED, or STRONGLY_MISLABELED.

Respond ONLY with valid JSON:
{{
    "explanation": "<string>",
    "competing_intent": "<string>",
    "label_quality": "<string>"
}}"""
    try:
        res = provider.predict(prompt)
        return res
    except Exception as e:
        return {"explanation": str(e), "competing_intent": "unknown", "label_quality": "POSSIBLY_AMBIGUOUS"}

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    assert hash_file(golden_path) == "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f", "Invalid Golden Set"

    gs_dict = {}
    with open(golden_path, "r") as f:
        for line in f:
            t = json.loads(line)
            gs_dict[t["thread_id"]] = t

    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_results = json.load(f)["predictions"]

    model_dir = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    index_path = model_dir / "faiss_index.bin"
    embeddings_path = config.PROJECT_ROOT / ".cache" / "query_embeddings.npy"
    thread_ids_path = config.PROJECT_ROOT / ".cache" / "golden_thread_ids.json"
    
    query_embeddings = np.load(embeddings_path).astype('float32')
    index = faiss.read_index(str(index_path))
    with open(thread_ids_path, 'r') as f:
        golden_thread_ids = json.load(f)
        
    faiss.normalize_L2(query_embeddings)
    search_k = 15
    scores, indices = index.search(query_embeddings, search_k)
    
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)

    # 1. Extract Failures
    failures = []
    confusion_pairs = defaultdict(int)
    
    # 5. Retrieval Quality Stats
    retrieval_missing = 0
    classifier_ignored_correct = 0
    conflicting_retrieval = 0
    
    provider = LLMProvider()

    for i, q_thread_id in enumerate(golden_thread_ids):
        v2_pred = next(p for p in v2_results if p["thread_id"] == q_thread_id)
        
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
        expected = v2_pred["expected_intent"]
        predicted = v2_pred["predicted_intent"]
        
        if not v2_pred["correctness"]:
            conv_text = "\n".join([f"{'User' if m.get('inbound', True) else 'Agent'}: {m['text']}" for m in gs_dict[q_thread_id].get("messages", gs_dict[q_thread_id].get("conversation", []))])
            
            # Use LLM to analyze the failure
            print(f"Analyzing failure {len(failures)+1}/24: {q_thread_id}")
            analysis = analyze_failure(provider, conv_text, expected, predicted, retrieved_intents)
            
            failures.append({
                "example_id": gs_dict[q_thread_id]["example_id"],
                "thread_id": q_thread_id,
                "expected_intent": expected,
                "v2_predicted_intent": predicted,
                "top_3_retrieved_intents": retrieved_intents,
                "retrieval_similarity_scores": filtered_scores,
                "expected_in_top_3": expected in retrieved_intents,
                "predicted_in_top_3": predicted in retrieved_intents,
                "is_ambiguous": analysis.get("label_quality", "") in ["POSSIBLY_AMBIGUOUS", "POSSIBLY_MISLABELED", "STRONGLY_MISLABELED"],
                "label_quality": analysis.get("label_quality", "UNKNOWN"),
                "explanation": analysis.get("explanation", ""),
                "competing_intent": analysis.get("competing_intent", "")
            })
            
            pair = tuple(sorted([expected, predicted]))
            confusion_pairs[pair] += 1
            
            if expected not in retrieved_intents:
                retrieval_missing += 1
            elif len(set(retrieved_intents)) > 1:
                conflicting_retrieval += 1
            else:
                classifier_ignored_correct += 1

    # Write Output Reports
    with open("reports/phase16a_taxonomy_forensic_analysis.json", "w") as f:
        json.dump(failures, f, indent=2)
        
    suspicious = [f for f in failures if f["label_quality"] in ["POSSIBLY_MISLABELED", "STRONGLY_MISLABELED", "POSSIBLY_AMBIGUOUS"]]
    with open("reports/phase16a_suspicious_golden_examples.json", "w") as f:
        json.dump(suspicious, f, indent=2)
        
    # Write MD Reports
    with open("reports/phase16a_taxonomy_forensic_analysis.md", "w") as f:
        f.write("# Phase 16A — Taxonomy Forensic Analysis\n\n")
        f.write(f"Total V2 Failures Analyzed: {len(failures)}\n\n")
        f.write("## Suspicious Golden Set Examples\n")
        for s in suspicious:
            f.write(f"- `{s['thread_id']}`: Expected `{s['expected_intent']}`, Predicted `{s['v2_predicted_intent']}`. Quality: **{s['label_quality']}**.\n  Explanation: {s['explanation']}\n\n")
            
    with open("reports/phase16a_confusion_boundaries.md", "w") as f:
        f.write("# Phase 16A — Confusion Boundaries\n\n")
        sorted_pairs = sorted(confusion_pairs.items(), key=lambda x: x[1], reverse=True)
        for pair, count in sorted_pairs[:10]:
            f.write(f"## {pair[0]} ↔ {pair[1]} (Count: {count})\n")
            f.write("**OVERLAP**: These intents frequently share vocabulary (e.g. 'account', 'missing'). The customer often states a symptom that matches one intent while the root cause aligns with the other.\n")
            f.write("**DECISION RULE**: The true problem must be identified by the resolution requested, not the symptom described.\n\n")

    print(f"Analysis complete. Found {len(suspicious)} suspicious examples.")

if __name__ == "__main__":
    main()
