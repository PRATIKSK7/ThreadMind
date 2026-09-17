import os
import sys
import json
import time
import pickle
import subprocess
import numpy as np
from sklearn.metrics import f1_score
from sentence_transformers import SentenceTransformer
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
from scripts.evaluate_rag_mnrl import format_conversation, format_few_shot

# Stability settings for macOS
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

def create_faiss_subprocess_script():
    script_path = config.PROJECT_ROOT / ".cache" / "faiss_subprocess_scored.py"
    script_content = """import os
import sys
import pickle
import json
import numpy as np
import faiss

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
faiss.omp_set_num_threads(1)

def main():
    emb_path = sys.argv[1]
    index_path = sys.argv[2]
    metadata_path = sys.argv[3]
    output_path = sys.argv[4]
    golden_thread_ids_path = sys.argv[5]
    
    with open(golden_thread_ids_path, 'r') as f:
        golden_thread_ids = json.load(f)

    query_embeddings = np.load(emb_path).astype('float32')
    index = faiss.read_index(index_path)
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
        
    faiss.normalize_L2(query_embeddings)
    search_k = 15
    scores, indices = index.search(query_embeddings, search_k)
    
    results = []
    for i in range(len(query_embeddings)):
        q_thread_id = golden_thread_ids[i]
        filtered_docs = []
        for rank, idx in enumerate(indices[i]):
            if idx < 0: continue
            doc = metadata[idx].copy()
            doc['score'] = float(scores[i][rank])
            if doc['thread_id'] != q_thread_id:
                filtered_docs.append(doc)
            if len(filtered_docs) >= 5:
                break
        results.append(filtered_docs)
        
    with open(output_path, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    main()
"""
    with open(script_path, "w") as f:
        f.write(script_content)
    return script_path

def get_retrieved_documents_isolated(dataset):
    model_path = config.PROJECT_ROOT / ".cache" / "rag_dense_mnrl"
    index_path = model_path / "faiss_index.bin"
    metadata_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
    
    model = SentenceTransformer(str(model_path), device="cpu")
    query_texts = [format_conversation(r["conversation"]) for r in dataset]
    embeddings = model.encode(query_texts, batch_size=32, convert_to_numpy=True, show_progress_bar=False)
    
    emb_path = config.PROJECT_ROOT / ".cache" / "query_embeddings_pilot.npy"
    np.save(emb_path, embeddings)
    
    golden_thread_ids = [r["thread_id"] for r in dataset]
    thread_ids_path = config.PROJECT_ROOT / ".cache" / "golden_thread_ids_pilot.json"
    with open(thread_ids_path, "w") as f:
        json.dump(golden_thread_ids, f)
        
    output_path = config.PROJECT_ROOT / ".cache" / "retrieval_results_pilot.json"
    script_path = create_faiss_subprocess_script()
    
    res = subprocess.run([
        sys.executable, str(script_path),
        str(emb_path), str(index_path), str(metadata_path), 
        str(output_path), str(thread_ids_path)
    ], capture_output=True, text=True)
    
    if res.returncode != 0:
        print("FAISS subprocess crashed!")
        sys.exit(1)
        
    with open(output_path, "r") as f:
        return json.load(f)

def load_prompt_template():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v1.txt"
    with open(prompt_path, "r") as f:
        return f.read()

def dynamic_filter(docs):
    if not docs: return []
    best_score = docs[0]['score']
    filtered = [docs[0]]
    # Dynamic strategy: keep up to K=5 examples if they are highly similar
    # AND within 0.008 of the best score. The score density is very high,
    # so we need a tight threshold to prune distractors.
    for d in docs[1:5]:
        if d['score'] >= best_score - 0.008:
            filtered.append(d)
        else:
            break
    return filtered

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    dataset = []
    with open(golden_path, "r") as f:
        for line in f:
            dataset.append(json.loads(line))
            
    pilot_dataset = dataset[:20]
    retrieval_results = get_retrieved_documents_isolated(pilot_dataset)
    
    provider = LLMProvider()
    prompt_template = load_prompt_template()
    
    configs = {
        "A. K=1": lambda docs: docs[:1],
        "B. K=3": lambda docs: docs[:3],
        "C. K=5": lambda docs: docs[:5],
        "D. Dynamic K": dynamic_filter
    }
    
    final_metrics = {}
    
    for cfg_name, cfg_func in configs.items():
        print(f"\\nRunning configuration {cfg_name}")
        correct_intent = 0
        correct_esc = 0
        malformed = 0
        total_latency = 0.0
        total_prompt_tokens = 0
        total_examples_supplied = 0
        
        intents_true = []
        intents_pred = []
        
        for i, r in enumerate(pilot_dataset):
            target_intent = r["intent_id"]
            target_escalation = r["expected_behavior"]["escalation"]
            docs = retrieval_results[i]
            
            selected_docs = cfg_func(docs)
            total_examples_supplied += len(selected_docs)
            
            few_shot_str = format_few_shot(selected_docs)
            conv_str = format_conversation(r["conversation"])
            prompt = prompt_template.replace("{few_shot_examples}", few_shot_str).replace("{conversation}", conv_str)
            
            total_prompt_tokens += len(prompt) // 4
            
            # Cache bypass to force real inference and true latency for accurate comparison
            # using bypass string makes sure each run doesn't hit the identical prompt
            prompt_for_cache_bypass = prompt + f"\\n// Pilot bypass: {cfg_name}_{i}"
            
            t0 = time.time()
            pred = provider.predict(prompt_for_cache_bypass)
            latency = time.time() - t0
            total_latency += latency
            
            if pred.get("error") or not pred.get("predicted_intent"):
                malformed += 1
                intents_true.append(target_intent)
                intents_pred.append("malformed")
            else:
                intents_true.append(target_intent)
                intents_pred.append(pred["predicted_intent"])
                if pred["predicted_intent"] == target_intent: correct_intent += 1
                if pred["predicted_escalation"] == target_escalation: correct_esc += 1
                
        acc = correct_intent / 20
        esc_acc = correct_esc / 20
        f1 = f1_score(intents_true, intents_pred, average="macro", zero_division=0)
        
        final_metrics[cfg_name] = {
            "intent_accuracy": acc,
            "macro_f1": f1,
            "escalation_accuracy": esc_acc,
            "malformed": malformed,
            "latency": total_latency / 20,
            "avg_examples_supplied": total_examples_supplied / 20,
            "avg_prompt_tokens": total_prompt_tokens / 20
        }
        
    report_path = config.REPORTS_DIR / "dynamic_rag_pilot.md"
    with open(report_path, "w") as f:
        f.write("# Dynamic RAG Pilot Results (N=20)\\n\\n")
        f.write("| Configuration | Intent Acc | Macro F1 | Esc Acc | Malformed | Latency (s) | Avg Examples | Avg Tokens |\\n")
        f.write("|---|---|---|---|---|---|---|---|\\n")
        for name, m in final_metrics.items():
            f.write(f"| {name} | {m['intent_accuracy']*100:.1f}% | {m['macro_f1']:.3f} | {m['escalation_accuracy']*100:.1f}% | {m['malformed']} | {m['latency']:.2f} | {m['avg_examples_supplied']:.1f} | {m['avg_prompt_tokens']:.0f} |\\n")
            
        f.write("\\n## Conclusions\\n")
        f.write("1. **Which configuration performed best?**\\n")
        f.write("2. **Did dynamic filtering reduce distractors?**\\n")
        f.write("3. **Did accuracy improve over K=5 baseline?**\\n")
        f.write("4. **Is the result strong enough to justify full evaluation?**\\n")

    print(f"\\nPilot complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()
