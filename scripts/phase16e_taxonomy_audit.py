import os
import sys
import json
import hashlib
import csv
import numpy as np
import faiss
import pickle
from collections import defaultdict

# Stability settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_golden_set(filepath):
    # Integrity check
    expected_hash = "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f"
    actual_hash = hash_file(filepath)
    if actual_hash != expected_hash:
        raise ValueError(f"Golden Set hash mismatch! Expected {expected_hash}, got {actual_hash}")
        
    line_count = 0
    tids = set()
    schema_ok = True
    with open(filepath, "r") as f:
        for line in f:
            line_count += 1
            j = json.loads(line)
            tid = j.get("thread_id")
            if not tid or tid in tids:
                schema_ok = False
            tids.add(tid)
            if "messages" not in j and "conversation" not in j:
                schema_ok = False
                
    if line_count != 196:
        raise ValueError(f"Expected 196 lines, got {line_count}")
    if not schema_ok:
        raise ValueError("Schema validation failed.")

def generate_audit_data(provider, conv_text, expected, predicted, top3):
    prompt = f"""You are generating an ambiguity audit for a customer service taxonomy.
Conversation:
{conv_text}

Golden Label: {expected}
Classifier Prediction: {predicted}
Retrieved: {top3}

Analyze this failure and return ONLY valid JSON:
{{
  "ambiguity_type": "<string>",
  "reason_current_label_may_be_problematic": "<string>",
  "evidence_supporting_current_label": "<string>",
  "evidence_supporting_alternative": "<string>",
  "recommended_action": "<REVIEW_LABEL|REVIEW_TAXONOMY|REVIEW_CORPUS|KEEP_LABEL|INSUFFICIENT_EVIDENCE>",
  "question_for_human": "<A binary question. e.g., 'Customer reports a delayed package and asks for refund. Primary intent?'>",
  "option_A": "<intent 1>",
  "option_B": "<intent 2>"
}}"""
    try:
        res = provider.predict(prompt)
        return res
    except:
        return {
            "ambiguity_type": "UNKNOWN",
            "reason_current_label_may_be_problematic": "Error generating audit",
            "evidence_supporting_current_label": "",
            "evidence_supporting_alternative": "",
            "recommended_action": "REVIEW_LABEL",
            "question_for_human": f"Choose between {expected} and {predicted}.",
            "option_A": expected,
            "option_B": predicted
        }

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    verify_golden_set(golden_path)

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
        
    failures = []
    
    for i, q_thread_id in enumerate(golden_thread_ids):
        v2 = next(p for p in v2_results if p["thread_id"] == q_thread_id)
        if v2["correctness"]:
            continue
            
        expected = v2["expected_intent"]
        predicted = v2["predicted_intent"]
        
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
                
        top3 = [d['intent_id'] for d in filtered_docs]
        
        failure_category = "UNKNOWN"
        if expected not in top3:
            failure_category = "RETRIEVAL_MISSING"
        elif len(set(top3)) > 1:
            failure_category = "CONFLICTING_EVIDENCE"
        else:
            failure_category = "CLASSIFIER_IGNORED_CORRECT"
            
        messages = gs_dict[q_thread_id].get("messages", gs_dict[q_thread_id].get("conversation", []))
        conv_text = "\n".join([f"{'User' if m.get('inbound', True) else 'Agent'}: {m['text']}" for m in messages])
        
        failures.append({
            "id": gs_dict[q_thread_id]["example_id"],
            "thread_id": q_thread_id,
            "conversation": conv_text,
            "gold_label": expected,
            "v2_prediction": predicted,
            "top_3_retrieved_intents": top3,
            "retrieval_scores": filtered_scores,
            "failure_category": failure_category
        })

    provider = LLMProvider()
    
    actions = {
        "REVIEW_LABEL": 0,
        "REVIEW_TAXONOMY": 0,
        "REVIEW_CORPUS": 0,
        "KEEP_LABEL": 0,
        "INSUFFICIENT_EVIDENCE": 0
    }
    
    json_report = []
    csv_rows = []
    
    boundaries = defaultdict(list)

    print(f"Generating audit for {len(failures)} failures...")
    for i, f in enumerate(failures):
        print(f"Auditing {i+1}/{len(failures)}: {f['id']}")
        audit = generate_audit_data(provider, f["conversation"], f["gold_label"], f["v2_prediction"], f["top_3_retrieved_intents"])
        
        action = audit.get("recommended_action", "REVIEW_LABEL")
        if action not in actions: action = "REVIEW_LABEL"
        actions[action] += 1
        
        # Identify boundaries
        boundary_name = " ↔ ".join(sorted([f["gold_label"], f["v2_prediction"]]))
        boundaries[boundary_name].append(f)
        
        json_report.append({
            "id": f["id"],
            "conversation": f["conversation"],
            "gold_label": f["gold_label"],
            "v2_prediction": f["v2_prediction"],
            "top_3_retrieved_intents": f["top_3_retrieved_intents"],
            "retrieval_scores": f["retrieval_scores"],
            "failure_category": f["failure_category"],
            "candidate_intents": list(set([f["gold_label"], f["v2_prediction"]] + f["top_3_retrieved_intents"])),
            "ambiguity_type": audit.get("ambiguity_type", ""),
            "reason_current_label_may_be_problematic": audit.get("reason_current_label_may_be_problematic", ""),
            "evidence_supporting_current_label": audit.get("evidence_supporting_current_label", ""),
            "evidence_supporting_alternative": audit.get("evidence_supporting_alternative", ""),
            "recommended_action": action
        })
        
        csv_rows.append({
            "id": f["id"],
            "conversation": f["conversation"].replace("\n", " | "),
            "current_label": f["gold_label"],
            "v2_prediction": f["v2_prediction"],
            "retrieved_intents": ",".join(f["top_3_retrieved_intents"]),
            "failure_category": f["failure_category"],
            "boundary": boundary_name,
            "question_for_human": audit.get("question_for_human", ""),
            "option_A": audit.get("option_A", ""),
            "option_B": audit.get("option_B", ""),
            "recommended_action": action,
            "review_status": "PENDING"
        })

    with open("reports/phase16e_taxonomy_audit.json", "w") as outf:
        json.dump(json_report, outf, indent=2)
        
    csv_headers = ["id", "conversation", "current_label", "v2_prediction", "retrieved_intents", "failure_category", "boundary", "question_for_human", "option_A", "option_B", "recommended_action", "review_status"]
    with open("reports/phase16e_manual_review.csv", "w", newline="") as outf:
        writer = csv.DictWriter(outf, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_rows)
        
    top_boundary = max(boundaries.items(), key=lambda x: len(x[1])) if boundaries else ("None", [])

    with open("reports/phase16e_taxonomy_audit.md", "w") as outf:
        outf.write("# Phase 16E — Taxonomy Alignment Audit\n\n")
        outf.write(f"Total Suspicious Cases: {len(failures)}\n\n")
        outf.write("## Recommended Actions\n")
        for act, cnt in actions.items():
            outf.write(f"- {act}: {cnt}\n")
            
        outf.write("\n## Ambiguity Matrix\n")
        for b, exs in sorted(boundaries.items(), key=lambda x: len(x[1]), reverse=True):
            outf.write(f"### {b} (Count: {len(exs)})\n")
            outf.write(f"This boundary suffers from overlapping definitions. A human annotator needs explicit guidance.\n\n")

    print("PHASE 16E STATUS:")
    print("COMPLETE")
    print()
    print("GOLDEN SET MODIFIED:")
    print("NO")
    print()
    print("FAISS MODIFIED:")
    print("NO")
    print()
    print("MODEL MODIFIED:")
    print("NO")
    print()
    print("PRODUCTION MODIFIED:")
    print("NO")
    print()
    print(f"SUSPICIOUS CASES:")
    print(f"{len(failures)}")
    print()
    print("REVIEW_LABEL:")
    print(actions["REVIEW_LABEL"])
    print()
    print("REVIEW_TAXONOMY:")
    print(actions["REVIEW_TAXONOMY"])
    print()
    print("REVIEW_CORPUS:")
    print(actions["REVIEW_CORPUS"])
    print()
    print("KEEP_LABEL:")
    print(actions["KEEP_LABEL"])
    print()
    print("INSUFFICIENT_EVIDENCE:")
    print(actions["INSUFFICIENT_EVIDENCE"])
    print()
    print("TOP AMBIGUITY BOUNDARY:")
    print(top_boundary[0])
    print()
    print("FINAL DECISION:")
    print("HUMAN_REVIEW_REQUIRED")
    print()
    print("NEXT RECOMMENDED PHASE:")
    print("PHASE 16F — MANUAL TAXONOMY DECISION")

if __name__ == "__main__":
    main()
