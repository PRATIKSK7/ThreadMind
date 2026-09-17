import os
import sys
import json
import time
import subprocess
import numpy as np
from sklearn.metrics import f1_score
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider
from scripts.evaluate_rag_mnrl import format_conversation, format_few_shot
from scripts.pilot_dynamic_rag import get_retrieved_documents_isolated

def load_base_prompt():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v1.txt"
    with open(prompt_path, "r") as f:
        return f.read()

def inject_instruction(base_prompt, instruction, instruction_header="# Classification Instructions"):
    # Inject the new section right before # Output Schema
    parts = base_prompt.split("# Output Schema")
    return f"{parts[0]}{instruction_header}\n{instruction}\n\n# Output Schema{parts[1]}"

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    dataset = []
    with open(golden_path, "r") as f:
        for line in f:
            dataset.append(json.loads(line))
            
    pilot_dataset = dataset[:20]
    
    # We will use K=5 for everything
    print("Retrieving candidates (K=5)...")
    retrieval_results = get_retrieved_documents_isolated(pilot_dataset)
    
    provider = LLMProvider()
    base_prompt = load_base_prompt()
    
    v1_text = """Make the classification decision explicit:
- Identify the user's primary intent.
- Distinguish similar intents using the retrieved examples.
- Return exactly one valid intent.
- Return exactly one escalation value.
- Do not invent an intent.
- Output JSON only."""
    
    v2_text = """Follow this label-selection discipline:
- Compare the conversation against the retrieved examples.
- Prioritize semantic/user-goal similarity.
- Select the single best matching intent.
- Ignore irrelevant details.
- Never combine multiple intents.
- Output only the required JSON schema."""
    
    v3_text = """Use the following decision checklist:
1. What is the user's primary goal?
2. Which retrieved example is most similar?
3. Which intent label best matches that goal?
4. Is escalation required?

After considering these steps, output JSON only."""
    
    configs = {
        "BASE": base_prompt,
        "VARIANT 1": inject_instruction(base_prompt, v1_text, "# Explicit Classification Instruction"),
        "VARIANT 2": inject_instruction(base_prompt, v2_text, "# Label-Selection Discipline"),
        "VARIANT 3": inject_instruction(base_prompt, v3_text, "# Structured Decision Checklist")
    }
    
    final_metrics = {}
    
    for cfg_name, prompt_template in configs.items():
        print(f"\nRunning configuration {cfg_name}")
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
            
            selected_docs = docs[:5] # Fixed K=5
            total_examples_supplied += len(selected_docs)
            
            few_shot_str = format_few_shot(selected_docs)
            conv_str = format_conversation(r["conversation"])
            prompt = prompt_template.replace("{few_shot_examples}", few_shot_str).replace("{conversation}", conv_str)
            
            total_prompt_tokens += len(prompt) // 4
            
            t0 = time.time()
            pred = provider.predict(prompt)
            latency = time.time() - t0
            
            # Since LLMProvider hits cache immediately, only increment latency if it wasn't a cache hit
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
        
        # We only count real inference latency, so we find how many were not cached
        # Alternatively, if we just want the real cost, we can measure raw time.
        # But wait, LLMProvider caching is based on the hash. If we just bypass cache, we get true latency.
        # I won't bypass the cache for BASE so it can hit the previous run's cache.
        
        final_metrics[cfg_name] = {
            "intent_accuracy": acc,
            "macro_f1": f1,
            "escalation_accuracy": esc_acc,
            "malformed": malformed,
            "latency": total_latency / 20, # Might be ~0 if fully cached, but we can note that
            "avg_examples_supplied": total_examples_supplied / 20,
            "avg_prompt_tokens": total_prompt_tokens / 20
        }
        
    report_path = config.REPORTS_DIR / "prompt_variants_pilot.md"
    with open(report_path, "w") as f:
        f.write("# Prompt Variants Pilot Results (N=20, K=5)\n\n")
        f.write("| Configuration | Intent Acc | Macro F1 | Esc Acc | Malformed | Latency (s)* | Avg Examples | Avg Tokens |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for name, m in final_metrics.items():
            f.write(f"| {name} | {m['intent_accuracy']*100:.1f}% | {m['macro_f1']:.3f} | {m['escalation_accuracy']*100:.1f}% | {m['malformed']} | {m['latency']:.2f} | {m['avg_examples_supplied']:.1f} | {m['avg_prompt_tokens']:.0f} |\n")
            
        f.write("\n*Latency may be artificially low for cached prompts.*\n")
        f.write("\n## Conclusions\n")
        f.write("1. **Best variant by intent accuracy:**\n")
        f.write("2. **Improvement over BASE in percentage points:**\n")
        f.write("3. **Escalation improvement:**\n")
        f.write("4. **Latency change:**\n")
        f.write("5. **Malformed-response change:**\n")
        f.write("6. **Justify full evaluation?**\n")

    print(f"\nPilot complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()
