import os
import sys
import json
import time
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def load_prompt_template():
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v1.txt"
    with open(prompt_path, "r") as f:
        return f.read()

def format_few_shot(retrieved_docs):
    blocks = []
    for i, doc in enumerate(retrieved_docs):
        lines = doc['conversation'].strip().split('\n')
        if len(lines) > 4:
            compact_conv = "\n".join(lines[:2] + ["..."] + lines[-2:])
        else:
            compact_conv = "\n".join(lines)
            
        block = f"--- Example {i+1} ---\n"
        block += f"Conversation:\n{compact_conv}\n\n"
        block += "Classification:\n"
        block += "{\n"
        block += f'  "predicted_intent": "{doc["intent_id"]}",\n'
        block += f'  "predicted_escalation": "{doc["escalation"]}"\n'
        block += "}\n"
        blocks.append(block)
    return "\n".join(blocks)

def main():
    print("Running deterministic pilot on N=5...")
    
    # Load dataset
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    dataset = []
    with open(golden_path, "r") as f:
        for line in f:
            dataset.append(json.loads(line))
            
    pilot_dataset = dataset[:5]
    
    # Load retrieval results
    retrieval_path = config.PROJECT_ROOT / ".cache" / "retrieval_results.json"
    with open(retrieval_path, "r") as f:
        retrieval_results = json.load(f)[:5]
        
    prompt_template = load_prompt_template()
    provider = LLMProvider()
    
    for k in [1, 3, 5]:
        print(f"\n--- Pilot K={k} ---")
        correct = 0
        malformed = 0
        total_prompt_length = 0
        total_latency = 0
        
        for i, r in enumerate(pilot_dataset):
            target_intent = r["intent_id"]
            retrieved_docs = retrieval_results[i][:k]
            
            few_shot_str = format_few_shot(retrieved_docs)
            
            parts = []
            for m in r["conversation"]:
                role = "User" if m.get("inbound", True) else "Agent"
                parts.append(f"{role}: {m['text']}")
            conv_str = "\n".join(parts)
            
            prompt = prompt_template.replace("{few_shot_examples}", few_shot_str)
            prompt = prompt.replace("{conversation}", conv_str)
            
            # Simple token approximation (4 chars = 1 token)
            prompt_tokens = len(prompt) // 4
            total_prompt_length += prompt_tokens
            
            # Force cache hit miss simulation by running provider?
            # Actually, I'll bypass the cache check in this pilot by appending a random string 
            # so we get real latencies.
            prompt_for_cache_bypass = prompt + f"\n// Bypass Cache Pilot K={k} I={i}"
            
            t0 = time.time()
            pred = provider.predict(prompt_for_cache_bypass)
            latency = time.time() - t0
            total_latency += latency
            
            if pred.get("error") or not pred.get("predicted_intent"):
                malformed += 1; print(pred.get("error"))
            else:
                if pred["predicted_intent"] == target_intent:
                    correct += 1
                    
        print(f"Accuracy: {correct/5 * 100:.1f}%")
        print(f"Malformed: {malformed}")
        print(f"Avg Prompt Tokens (approx): {total_prompt_length/5:.0f}")
        print(f"Avg Latency: {total_latency/5:.2f}s")

if __name__ == "__main__":
    main()
