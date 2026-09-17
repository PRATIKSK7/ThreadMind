import json
import os
from collections import defaultdict, Counter
import numpy as np

def run():
    with open("reports/rag_mnrl_k5_results.json", "r") as f:
        results = json.load(f)

    predictions = results["predictions"]
    errors = [p for p in predictions if not p["correctness"]]
    
    # We need texts for retrieved threads.
    # We'll load the golden set threads and the corpus threads.
    golden_threads = {}
    with open("data/processed/golden_set.jsonl", "r") as f:
        for line in f:
            t = json.loads(line)
            golden_threads[t["thread_id"]] = t

    retrieved_thread_ids = set()
    for e in errors:
        retrieved_thread_ids.update(e["retrieved_thread_ids"])
        
    corpus_threads = {}
    with open("data/processed/retrieval_corpus.jsonl", "r") as f:
        for line in f:
            t = json.loads(line)
            if t["thread_id"] in retrieved_thread_ids:
                corpus_threads[t["thread_id"]] = t
                
    # Also load the train split because that's where the retriever probably gets its threads from
    with open("data/processed/train_split.jsonl", "r") as f:
        for line in f:
            t = json.loads(line)
            if t["thread_id"] in retrieved_thread_ids:
                corpus_threads[t["thread_id"]] = t

    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def get_text(thread):
        if "conversation" in thread:
            return "\n".join([m["text"] for m in thread["conversation"]])
        return "\n".join([m["text"] for m in thread["messages"]])
        
    error_attribution = []
    
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    confusion_pairs = defaultdict(int)
    
    retrieval_present = 0
    retrieval_absent = 0
    
    for e in errors:
        gt = e["expected_intent"]
        pred = e["predicted_intent"]
        
        confusion_matrix[gt][pred] += 1
        
        # Sort pair alphabetically for consistency
        pair = tuple(sorted([gt, pred]))
        confusion_pairs[pair] += 1
        
        top_correct = e["retrieved_intents"][0] == gt
        any_correct = gt in e["retrieved_intents"]
        
        if any_correct:
            rank = e["retrieved_intents"].index(gt) + 1
            retrieval_present += 1
        else:
            rank = -1
            retrieval_absent += 1
            
        follows_incorrect = (pred in e["retrieved_intents"]) and (pred != gt)
        
        if not any_correct:
            primary_failure = "retrieval"
        elif follows_incorrect:
            primary_failure = "LLM classification" # The LLM was swayed by a wrong label in context
        else:
            primary_failure = "LLM classification"
            
        target_text = get_text(golden_threads[e["thread_id"]])
        retrieved_texts = [get_text(corpus_threads[tid]) for tid in e["retrieved_thread_ids"] if tid in corpus_threads]
        
        if len(retrieved_texts) > 0:
            target_emb = model.encode([target_text])
            ret_embs = model.encode(retrieved_texts)
            
            sims = cosine_similarity(target_emb, ret_embs)[0]
            semantically_relevant = bool(np.mean(sims) > 0.5)
            
            if len(retrieved_texts) > 1:
                cross_sims = cosine_similarity(ret_embs, ret_embs)
                np.fill_diagonal(cross_sims, 0)
                duplicates = bool(np.max(cross_sims) > 0.95)
            else:
                duplicates = False
        else:
            semantically_relevant = False
            duplicates = False
            
        attr = {
            "example_id": e["example_id"],
            "ground_truth_intent": gt,
            "predicted_intent": pred,
            "top_retrieved_correct": top_correct,
            "any_top_5_correct": any_correct,
            "rank_first_correct": rank,
            "semantically_relevant": semantically_relevant,
            "duplicates_present": duplicates,
            "target_ambiguous": False, # Heuristic
            "follows_incorrect_label": follows_incorrect,
            "primary_failure": primary_failure
        }
        error_attribution.append(attr)

    top_pairs = sorted(confusion_pairs.items(), key=lambda x: x[1], reverse=True)[:5]
    
    with open("reports/phase1_error_attribution.json", "w") as f:
        json.dump({
            "error_attribution": error_attribution,
            "confusion_pairs": [{"pair": p[0], "count": p[1]} for p in top_pairs],
            "retrieval_present": retrieval_present,
            "retrieval_absent": retrieval_absent,
            "total_errors": len(errors)
        }, f, indent=2)

    # Dump some examples for the top pair to analyze
    top_pair = top_pairs[0][0]
    print(f"Top confusion pair: {top_pair} (Count: {top_pairs[0][1]})")
    for e in errors:
        pair = tuple(sorted([e["expected_intent"], e["predicted_intent"]]))
        if pair == top_pair:
            print(f"--- Example ID: {e['example_id']} ---")
            print(f"GT: {e['expected_intent']} | Pred: {e['predicted_intent']}")
            print("Target Thread:")
            print(get_text(golden_threads[e["thread_id"]]))
            print("Retrieved Intents:", e["retrieved_intents"])
            print("-" * 50)
            break

if __name__ == "__main__":
    run()
