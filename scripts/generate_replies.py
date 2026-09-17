import json
import time
import hashlib
from collections import defaultdict
from src.threadmind import config
from src.threadmind.router.fallback_router import FallbackRouter
from src.threadmind.rag.dense_retriever import DenseRetriever
from src.threadmind.llm.provider import LLMProvider

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def format_few_shot(retrieved_docs):
    blocks = []
    for i, doc in enumerate(retrieved_docs):
        meta = doc['metadata']
        conv = meta['conversation']
        if isinstance(conv, str):
            try:
                conv = json.loads(conv)
            except json.JSONDecodeError:
                conv = []
        
        # Split into context and final agent response
        # Assume the last message by 'agent' is the response we want to show
        # Since we retrieve full resolved threads, the last message is usually the resolution.
        
        context_lines = []
        final_agent_reply = "We apologize, please DM us with more details."
        
        for m in conv:
            role = "customer" if m.get('inbound', True) else "agent"
            text = m.get('text', '')
            if role == "agent":
                final_agent_reply = text
            context_lines.append(f"{role.capitalize()}: {text}")
            
        block = f"--- Past Example {i+1} ---\n"
        block += f"Conversation:\n" + "\n".join(context_lines[:-1]) + "\n"
        block += f"Agent Reply: {final_agent_reply}\n"
        blocks.append(block)
    return "\n".join(blocks)

def main():
    print("Initializing components for Reply Generation...")
    router = FallbackRouter(k=3, confidence_threshold=0.95)
    retriever = DenseRetriever()
    llm = LLMProvider()
    
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "reply_generation_v1.txt"
    with open(prompt_path, "r") as f:
        prompt_template = f.read()
        
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    dataset = load_threads(golden_path)
    
    print(f"\nGenerating replies for {len(dataset)} Golden Set examples...")
    results = []
    
    for i, r in enumerate(dataset):
        conv = r['conversation']
        
        # 1. Route to get intent and escalation
        # We use the router to get the classification, which is our grounded state
        router_pred = router.predict(conv)
        predicted_intent = router_pred.get('predicted_intent', 'other_support')
        predicted_escalation = router_pred.get('predicted_escalation', 'no_escalation')
        
        # 2. Retrieve similar resolved cases for grounding
        retrieved_docs = retriever.retrieve(conv, k=3)
        few_shot_str = format_few_shot(retrieved_docs)
        
        # 3. Format the Target Conversation
        conv_lines = []
        for m in conv:
            role = "customer" if m.get('inbound', True) else "agent"
            conv_lines.append(f"{role.capitalize()}: {m.get('text', '')}")
        conv_str = "\n".join(conv_lines)
        
        # 4. Generate the reply
        prompt = prompt_template.replace("{few_shot_examples}", few_shot_str)
        prompt = prompt.replace("{conversation}", conv_str)
        prompt = prompt.replace("{predicted_intent}", predicted_intent)
        prompt = prompt.replace("{predicted_escalation}", predicted_escalation)
        
        # For the reply generation, we don't want JSON, just the text.
        # However, our LLMProvider has `json_mode=True` as default for `predict()`.
        # We need to add a non-JSON mode to LLMProvider, or use `_call_ollama` directly.
        # Wait, I should check LLMProvider implementation.
        
        raw_response = llm.predict(prompt, json_mode=False)
        if "error" in raw_response:
            generated_reply = "ERROR: Failed to generate reply. " + raw_response["error"]
        else:
            generated_reply = raw_response.get("text", "").strip()
            
        record = {
            "example_id": r['example_id'],
            "thread_id": r['thread_id'],
            "predicted_intent": predicted_intent,
            "predicted_escalation": predicted_escalation,
            "routed_via": router_pred.get('routed_via'),
            "generated_reply": generated_reply
        }
        results.append(record)
        
        if (i+1) % 10 == 0:
            print(f"Generated {i+1}/{len(dataset)} replies...")
            
    # Save results
    output_path = config.REPORTS_DIR / "generated_replies.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nSaved generated replies to {output_path}")

if __name__ == "__main__":
    main()
