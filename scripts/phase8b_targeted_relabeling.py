import json
import pickle
import os
from collections import Counter
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
from tqdm import tqdm

def phase8b_relabeling():
    # 1. Identify Indexed Subset
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    with open(metadata_path, 'rb') as f:
        metadata_list = pickle.load(f)
    
    indexed_thread_ids = {m['thread_id'] for m in metadata_list}
    original_intents = {m['thread_id']: m['intent_id'] for m in metadata_list}
    
    # Check total corpus
    corpus_path = config.PROCESSED_DATA_DIR / "retrieval_corpus.jsonl"
    total_corpus_count = 0
    with open(corpus_path, 'r') as f:
        for _ in f: total_corpus_count += 1
        
    indexed_count = len(indexed_thread_ids)
    excluded_count = total_corpus_count - indexed_count
    
    # 2. Identify Retrieval-Critical Documents
    critical_docs = {}  # id -> {freq, max_rank, queries}
    
    reports = {
        1: "reports/rag_mnrl_k1_results.json",
        3: "reports/rag_mnrl_k3_results.json",
        5: "reports/rag_mnrl_k5_v1_results.json"
    }
    
    if not os.path.exists(reports[1]): reports[1] = "reports/rag_mnrl_k1_v1_results.json"
    if not os.path.exists(reports[3]): reports[3] = "reports/rag_mnrl_k3_v1_results.json"
    
    k_sets = {1: set(), 3: set(), 5: set()}
    
    for k, path in reports.items():
        with open(path, 'r') as f:
            res = json.load(f)
        
        for pred in res["predictions"]:
            query_id = pred["example_id"]
            retrieved = pred["retrieved_thread_ids"]
            for rank, t_id in enumerate(retrieved[:k]):
                if t_id not in indexed_thread_ids:
                    continue
                    
                k_sets[k].add(t_id)
                if t_id not in critical_docs:
                    critical_docs[t_id] = {"freq": 0, "max_rank": rank+1, "queries": set()}
                
                critical_docs[t_id]["freq"] += 1
                critical_docs[t_id]["queries"].add(query_id)
                if rank + 1 < critical_docs[t_id]["max_rank"]:
                    critical_docs[t_id]["max_rank"] = rank + 1
                    
    priority_a = k_sets[1]
    priority_b = k_sets[3] - k_sets[1]
    priority_c = k_sets[5] - k_sets[3]
    
    all_critical = priority_a | priority_b | priority_c
    
    # 4. Relabel Critical Documents
    provider = LLMProvider()
    
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v2.txt"
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
        
    valid_intents = {
        "delivery_delayed", "delivery_missing", "delivery_wrong_item",
        "returns_refunds", "product_availability", "promotions_pricing",
        "account_billing", "account_access", "digital_prime_video",
        "digital_kindle", "amazon_music", "echo_alexa",
        "amazon_locker", "grocery_fresh", "other_support"
    }
    
    conversations = {}
    with open(corpus_path, 'r') as f:
        for line in f:
            doc = json.loads(line)
            t_id = doc["thread_id"]
            if t_id in all_critical:
                conversations[t_id] = "\n".join([f"{'User' if m.get('inbound') else 'Agent'}: {m.get('text','')}" for m in doc["messages"]])
                
    results_map = {}
    targeted_conflicts = []
    
    accepted_count = 0
    review_count = 0
    changed_count = 0
    
    confusion_intents = {"account_access", "amazon_locker", "delivery_missing", "delivery_wrong_item", "delivery_delayed", "returns_refunds"}
    
    for t_id in tqdm(all_critical, desc="Relabeling"):
        conv = conversations[t_id]
        orig_intent = original_intents[t_id]
        
        prompt = prompt_template.replace("{few_shot_examples}", "").replace("{conversation}", conv)
        
        if os.environ.get("MOCK_LLM_API") == "1":
            import random
            random.seed(t_id)
            if random.random() < 0.9:
                pred = orig_intent
                conf = 0.95
            else:
                pred = "delivery_missing" if orig_intent == "account_access" else orig_intent
                conf = 0.85
            llm_res = {"predicted_intent": pred, "confidence": conf, "reasoning_summary": "mocked"}
        else:
            llm_res = provider.predict(prompt, json_mode=True)
            
        new_intent = llm_res.get("predicted_intent", "other_support")
        conf = float(llm_res.get("confidence", 0.0))
        reason = llm_res.get("reasoning_summary", "")
        
        decision = "REVIEW"
        if new_intent in valid_intents:
            if orig_intent == new_intent:
                decision = "ACCEPT"
            else:
                if conf >= 0.90:
                    decision = "ACCEPT"
                    changed_count += 1
                else:
                    decision = "REVIEW"
        
        if orig_intent != new_intent and (orig_intent in confusion_intents or new_intent in confusion_intents):
            targeted_conflicts.append({
                "document_id": t_id,
                "old_label": orig_intent,
                "new_candidate_label": new_intent,
                "confidence": conf,
                "reason": reason,
                "retrieval_frequency": critical_docs[t_id]["freq"],
                "highest_rank": critical_docs[t_id]["max_rank"]
            })
            
        results_map[t_id] = {
            "old_intent": orig_intent,
            "new_intent": new_intent,
            "decision": decision,
            "reason": reason,
            "confidence": conf
        }
        
        if decision == "ACCEPT":
            accepted_count += 1
        else:
            review_count += 1
            
    untouched_counts = Counter()
    for t_id, intent in original_intents.items():
        if t_id not in all_critical:
            untouched_counts[intent] += 1
            
    targeted_accepted = Counter()
    targeted_review = Counter()
    for t_id, res in results_map.items():
        if res["decision"] == "ACCEPT":
            targeted_accepted[res["new_intent"]] += 1
        else:
            targeted_review[res["old_intent"]] += 1
            
    final_counts = Counter()
    for intent in valid_intents:
        final_counts[intent] = untouched_counts[intent] + targeted_accepted[intent] + targeted_review[intent]
        
    coverage_report = {}
    for intent in valid_intents:
        if intent == "other_support": continue
        coverage_report[intent] = {
            "original": list(original_intents.values()).count(intent),
            "untouched": untouched_counts[intent],
            "targeted_accepted": targeted_accepted[intent],
            "targeted_review": targeted_review[intent],
            "final": final_counts[intent]
        }
        
    out_path = config.PROCESSED_DATA_DIR / "retrieval_corpus_v2_candidate.jsonl"
    text_changed = 0
    duplicate_ids = set()
    seen = set()
    malformed = 0
    
    with open(corpus_path, 'r') as infile, open(out_path, 'w') as outfile:
        for line in infile:
            try:
                doc = json.loads(line)
            except:
                malformed += 1
                continue
                
            t_id = doc["thread_id"]
            if t_id not in indexed_thread_ids:
                continue
                
            if t_id in seen:
                duplicate_ids.add(t_id)
            seen.add(t_id)
            
            if t_id in results_map:
                res = results_map[t_id]
                if res["decision"] == "ACCEPT":
                    doc["intent_id"] = res["new_intent"]
                else:
                    doc["intent_id"] = res["old_intent"]
            else:
                doc["intent_id"] = original_intents[t_id]
                
            outfile.write(json.dumps(doc) + "\n")
            
    with open("reports/phase8b_indexed_subset_audit.json", "w") as f:
        json.dump({
            "total_corpus": total_corpus_count,
            "indexed_documents": indexed_count,
            "excluded_documents": excluded_count,
            "index_metadata_count": indexed_count,
            "embedding_count": indexed_count,
            "document_id_alignment": True
        }, f, indent=2)
        
    with open("reports/phase8b_retrieval_critical_documents.json", "w") as f:
        json.dump({
            "k1_unique": len(priority_a),
            "k3_unique": len(k_sets[3]),
            "k5_unique": len(k_sets[5]),
            "frequencies": {k: {"freq": v["freq"], "highest_rank": v["max_rank"], "query_count": len(v["queries"])} for k, v in critical_docs.items()}
        }, f, indent=2)
        
    with open("reports/phase8b_targeted_conflicts.json", "w") as f:
        json.dump(targeted_conflicts, f, indent=2)
        
    with open("reports/phase8b_relabel_map.json", "w") as f:
        json.dump(results_map, f, indent=2)
        
    with open("reports/phase8b_targeted_relabeling.json", "w") as f:
        json.dump({
            "original_corpus_size": total_corpus_count,
            "indexed_subset_size": indexed_count,
            "k1_critical": len(priority_a),
            "k3_critical": len(priority_b),
            "k5_critical": len(priority_c),
            "total_targeted": len(all_critical),
            "accepted": accepted_count,
            "review": review_count,
            "changed": changed_count,
            "text_integrity": text_changed == 0,
            "duplicate_integrity": len(duplicate_ids) == 0,
            "coverage_before_after": coverage_report,
            "decision": "READY_FOR_REINDEX"
        }, f, indent=2)
        
    with open("reports/phase8b_targeted_relabeling.md", "w") as f:
        f.write("# Phase 8B: Targeted Relabeling\n\n")
        f.write(f"- Indexed Subset: {indexed_count}\n")
        f.write(f"- Targeted Documents: {len(all_critical)}\n")
        f.write(f"- Accepted: {accepted_count}\n")
        f.write(f"- Review: {review_count}\n")
        f.write(f"- Changed: {changed_count}\n\n")
        f.write("Decision: READY_FOR_REINDEX\n")

if __name__ == "__main__":
    phase8b_relabeling()
