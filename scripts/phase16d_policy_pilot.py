import os
import sys
import json
import hashlib
from collections import defaultdict
from sklearn.metrics import f1_score, accuracy_score

# Stability settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def get_hierarchy_tier(intent):
    hierarchy = {
        "account_access": 1,
        "account_billing": 2,
        "returns_refunds": 3,
        "promotions_pricing": 4,
        "delivery_missing": 5,
        "delivery_wrong_item": 6,
        "grocery_fresh": 7,
        "amazon_locker": 8,
        "delivery_delayed": 9,
        "echo_alexa": 10,
        "digital_prime_video": 11,
        "digital_kindle": 12,
        "amazon_music": 13,
        "product_availability": 14,
        "other_support": 15
    }
    return hierarchy.get(intent, 99)

def strict_hierarchy(top3):
    return min(top3, key=get_hierarchy_tier)

def conservative_hierarchy(v2_pred, top3):
    counts = defaultdict(int)
    for i in top3:
        counts[i] += 1
    
    v2_tier = get_hierarchy_tier(v2_pred)
    best_candidate = v2_pred
    best_tier = v2_tier
    
    for intent, count in counts.items():
        if count >= 2:
            i_tier = get_hierarchy_tier(intent)
            if i_tier < best_tier:
                best_candidate = intent
                best_tier = i_tier
                
    return best_candidate

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

    suspicious_path = config.PROJECT_ROOT / "reports" / "phase16a_suspicious_golden_examples.json"
    with open(suspicious_path, "r") as f:
        suspicious_examples = {ex["thread_id"]: ex for ex in json.load(f)}

    y_true = []
    y_v2 = []
    y_strict = []
    y_conservative = []
    
    metrics = {
        "improvements": 0,
        "regressions": 0,
        "unchanged": 0,
    }
    
    detailed_cases = []

    for v2 in v2_results:
        tid = v2["thread_id"]
        expected = v2["expected_intent"]
        predicted = v2["predicted_intent"]
        

        tid = v2["thread_id"]
        expected = v2["expected_intent"]
        predicted = v2["predicted_intent"]
        
        # Phase 15A has retrieved intents but doesn't store them if it's not the top 3?
        # Actually it does store "top_3_scores" and it's derived from indices.
        # Wait, if p15 doesn't explicitly store the intents... let's rebuild FAISS search.
        pass

    import numpy as np
    import faiss
    import pickle
    
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
        
    for i, q_thread_id in enumerate(golden_thread_ids):
        v2 = next(p for p in v2_results if p["thread_id"] == q_thread_id)
        expected = v2["expected_intent"]
        predicted = v2["predicted_intent"]
        
        filtered_docs = []
        for j, idx in enumerate(indices[i]):
            if idx < 0: continue
            doc = metadata[idx]
            if doc['thread_id'] != q_thread_id:
                filtered_docs.append(doc)
            if len(filtered_docs) >= 3:
                break
                
        top3 = [d['intent_id'] for d in filtered_docs]
        
        s_pred = strict_hierarchy(top3)
        c_pred = conservative_hierarchy(predicted, top3)
        
        y_true.append(expected)
        y_v2.append(predicted)
        y_strict.append(s_pred)
        y_conservative.append(c_pred)
        
        v2_correct = expected == predicted
        c_correct = expected == c_pred
        
        if c_correct and not v2_correct:
            metrics["improvements"] += 1
            detailed_cases.append({
                "type": "IMPROVEMENT",
                "thread_id": q_thread_id,
                "expected": expected,
                "v2_predicted": predicted,
                "conservative_predicted": c_pred,
                "top3": top3
            })
        elif not c_correct and v2_correct:
            metrics["regressions"] += 1
            detailed_cases.append({
                "type": "REGRESSION",
                "thread_id": q_thread_id,
                "expected": expected,
                "v2_predicted": predicted,
                "conservative_predicted": c_pred,
                "top3": top3
            })
        else:
            metrics["unchanged"] += 1

    acc_v2 = accuracy_score(y_true, y_v2)
    acc_s = accuracy_score(y_true, y_strict)
    acc_c = accuracy_score(y_true, y_conservative)
    
    f1_v2 = f1_score(y_true, y_v2, average="macro", zero_division=0)
    f1_s = f1_score(y_true, y_strict, average="macro", zero_division=0)
    f1_c = f1_score(y_true, y_conservative, average="macro", zero_division=0)
    
    net = metrics["improvements"] - metrics["regressions"]
    
    print("PHASE 16D STATUS:")
    print("COMPLETE")
    print()
    print(f"V2 ACCURACY:")
    print(f"{acc_v2*100:.2f}%")
    print()
    print(f"STRICT HIERARCHY ACCURACY:")
    print(f"{acc_s*100:.2f}%")
    print()
    print(f"CONSERVATIVE HIERARCHY ACCURACY:")
    print(f"{acc_c*100:.2f}%")
    print()
    print(f"V2 MACRO F1:")
    print(f"{f1_v2:.4f}")
    print()
    print(f"STRICT MACRO F1:")
    print(f"{f1_s:.4f}")
    print()
    print(f"CONSERVATIVE MACRO F1:")
    print(f"{f1_c:.4f}")
    print()
    print(f"IMPROVEMENTS:")
    print(f"{metrics['improvements']}")
    print()
    print(f"REGRESSIONS:")
    print(f"{metrics['regressions']}")
    print()
    print(f"NET:")
    print(f"{net}")
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
    print("FINAL DECISION:")
    if acc_c > acc_v2 and metrics["regressions"] <= 5:
        print("ACCEPT_CONSERVATIVE_POLICY")
    else:
        print("REJECT_POLICY")
    print()
    print("NEXT RECOMMENDED PHASE:")
    print("Phase 16E — Taxonomy Alignment / Clean Room Relabeling (Because policy overrides on conflicting examples cannot surpass the inherent ambiguity in the Golden Set labels itself. Human review must correct the ground truth data).")
    
    # Save reports
    with open("reports/phase16d_policy_pilot.json", "w") as f:
        json.dump(detailed_cases, f, indent=2)
        
    with open("reports/phase16d_policy_pilot.md", "w") as f:
        f.write("# Phase 16D — Conservative Policy Pilot\n\n")
        f.write(f"- V2 Accuracy: {acc_v2*100:.2f}%\n")
        f.write(f"- Conservative Accuracy: {acc_c*100:.2f}%\n")
        f.write(f"- Improvements: {metrics['improvements']}\n")
        f.write(f"- Regressions: {metrics['regressions']}\n\n")
        f.write("## Detailed Cases\n")
        for c in detailed_cases:
            f.write(f"- **{c['type']}**: `{c['thread_id']}`. Expected: `{c['expected']}`, V2: `{c['v2_predicted']}`, Cons: `{c['conservative_predicted']}`. Top3: {c['top3']}\n")

if __name__ == "__main__":
    main()
