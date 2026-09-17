import os
import sys
import json
import time
from sklearn.metrics import f1_score
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
from scripts.evaluate_rag_mnrl import format_conversation, format_few_shot
from scripts.pilot_dynamic_rag import get_retrieved_documents_isolated

def load_prompt():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v1.txt"
    with open(prompt_path, "r") as f:
        return f.read()

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    dataset = []
    with open(golden_path, "r") as f:
        for line in f:
            dataset.append(json.loads(line))
            
    pilot_dataset = dataset[:20]
    
    print("Retrieving candidates (K=5)...")
    retrieval_results = get_retrieved_documents_isolated(pilot_dataset)
    
    provider = LLMProvider()
    prompt_template = load_prompt()
    
    print("\nRunning final production prompt...")
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
        docs = retrieval_results[i][:5] # Fixed K=5
        
        total_examples_supplied += len(docs)
        few_shot_str = format_few_shot(docs)
        conv_str = format_conversation(r["conversation"])
        prompt = prompt_template.replace("{few_shot_examples}", few_shot_str).replace("{conversation}", conv_str)
        
        total_prompt_tokens += len(prompt) // 4
        
        # Bypass cache so we get true latency, even though it's technically a new hash since the file changed
        # Actually it will naturally miss the cache because the base prompt text has changed!
        t0 = time.time()
        pred = provider.predict(prompt)
        latency = time.time() - t0
        
        if not pred.get("_cache_hit", False):
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
    
    # Previous BASE metrics
    base_acc = 0.70
    base_f1 = 0.272
    base_esc_acc = 0.70
    
    acc_diff = (acc - base_acc) * 100
    f1_diff = f1 - base_f1
    esc_diff = (esc_acc - base_esc_acc) * 100
    
    report_path = config.REPORTS_DIR / "final_prompt_pilot.md"
    with open(report_path, "w") as f:
        f.write("# Final Production Prompt Pilot (N=20)\n\n")
        f.write("## Exact Configuration\n")
        f.write("- **Dataset**: N=20 Golden Set subset\n")
        f.write("- **Retriever**: MNRL (all-MiniLM-L6-v2) FAISS\n")
        f.write("- **Retrieval K**: 5\n")
        f.write("- **Prompt**: Updated `rag_classification_v1.txt` (Variant 2)\n")
        f.write("- **LLM Provider**: Ollama (local)\n\n")
        
        f.write("## Comparison\n")
        f.write("| Metric | Old BASE | New Variant 2 | Improvement |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| Intent Accuracy | {base_acc*100:.1f}% | {acc*100:.1f}% | {'+' if acc_diff>=0 else ''}{acc_diff:.1f} pts |\n")
        f.write(f"| Macro F1 | {base_f1:.3f} | {f1:.3f} | {'+' if f1_diff>=0 else ''}{f1_diff:.3f} |\n")
        f.write(f"| Escalation Accuracy | {base_esc_acc*100:.1f}% | {esc_acc*100:.1f}% | {'+' if esc_diff>=0 else ''}{esc_diff:.1f} pts |\n")
        f.write(f"| Malformed | 0 | {malformed} | - |\n")
        
        f.write("\n## Execution Details\n")
        f.write(f"- True Latency: {total_latency/20:.2f}s per query\n")
        f.write(f"- Avg Examples: {total_examples_supplied/20:.1f}\n")
        f.write(f"- Avg Tokens: {total_prompt_tokens/20:.0f}\n")
        
    print(f"\nFinal pilot complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()
