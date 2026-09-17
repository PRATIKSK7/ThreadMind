import json
import os
import sys
import random

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

print("Processing train_split.jsonl...")
golden_ids = set()
with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl") as f:
    for line in f:
        golden_ids.add(json.loads(line)["thread_id"])
        
val_ids = set()
with open(config.PROCESSED_DATA_DIR / "val_split.jsonl") as f:
    for line in f:
        val_ids.add(json.loads(line)["thread_id"])

intent_groups = {}
with open(config.PROCESSED_DATA_DIR / "train_split.jsonl") as f:
    for line in f:
        thread = json.loads(line)
        tid = thread["thread_id"]
        
        if tid in golden_ids or tid in val_ids:
            continue
            
        conv = []
        for m in thread["messages"]:
            conv.append({
                "author_role": "customer" if m.get("inbound", True) else "agent",
                "text": m["text"]
            })
        
        pred = rule_system.predict(conv)
        intent = pred["predicted_intent"]
        
        if intent == "other_support":
            continue
            
        text = format_conversation(thread["messages"])
        if intent not in intent_groups:
            intent_groups[intent] = []
        intent_groups[intent].append(text)

train_dict = {"anchor": [], "positive": []}
MAX_PAIRS_PER_INTENT = 400

random.seed(42)
for intent, texts in intent_groups.items():
    if len(texts) < 2:
        continue
    random.shuffle(texts)
    pairs_made = 0
    for i in range(0, len(texts)-1, 2):
        if pairs_made >= MAX_PAIRS_PER_INTENT:
            break
        train_dict["anchor"].append(texts[i])
        train_dict["positive"].append(texts[i+1])
        pairs_made += 1

out_path = config.PROJECT_ROOT / ".cache" / "mnrl_train_dict.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(train_dict, f)

print(f"Created {len(train_dict['anchor'])} pairs. Saved to {out_path}")
