import json
import os
import sys
import pickle

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config
from src.threadmind.baselines.rule_baseline import RuleBaseline

def format_conversation(messages):
    parts = []
    for m in messages:
        role = "User" if m.get("inbound", True) else "Agent"
        parts.append(f"{role}: {m['text']}")
    return "\n".join(parts)

print("Loading RuleBaseline...")
rule_system = RuleBaseline()

meta_path = config.PROJECT_ROOT / ".cache" / "rag_dense" / "corpus_metadata.pkl"
with open(meta_path, "rb") as f:
    corpus_metadata = pickle.load(f)

faiss_thread_ids = {m["thread_id"]: i for i, m in enumerate(corpus_metadata)}
val_queries = []

print("Processing val_split.jsonl...")
with open(config.PROCESSED_DATA_DIR / "val_split.jsonl") as f:
    for line in f:
        thread = json.loads(line)
        tid = thread["thread_id"]
        
        conv = []
        for m in thread["messages"]:
            conv.append({
                "author_role": "customer" if m.get("inbound", True) else "agent",
                "text": m["text"]
            })
        pred = rule_system.predict(conv)
        intent = pred["predicted_intent"]
        
        if intent != "other_support" and tid in faiss_thread_ids:
            val_queries.append({
                "thread_id": tid,
                "intent": intent,
                "conversation": thread["messages"],
                "query_text": format_conversation(thread["messages"])
            })

out_path = config.PROJECT_ROOT / ".cache" / "val_queries.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(val_queries, f)

print(f"Created {len(val_queries)} val queries. Saved to {out_path}")
