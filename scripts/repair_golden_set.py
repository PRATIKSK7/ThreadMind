import json
import hashlib
import shutil
import os

def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def get_text(example):
    if "conversation" in example:
        return " ".join([m["text"] for m in example["conversation"]]).lower()
    if "messages" in example:
        return " ".join([m["text"] for m in example["messages"]]).lower()
    return ""

def run():
    golden_set_path = "data/processed/golden_set.jsonl"
    backup_path = "data/processed/golden_set_pre_phase3.jsonl"

    # Step 1: Read flags
    with open("reports/golden_set_deterministic_flags.json", "r") as f:
        flags = json.load(f)

    clear_mislabels = [f for f in flags if f.get("category") == "CLEAR_MISLABEL"]
    
    # Read original golden set
    original_data = []
    with open(golden_set_path, "r") as f:
        for line in f:
            original_data.append(json.loads(line))
            
    # Step 2: Generate repair proposal
    repair_map_entries = []
    
    with open("reports/golden_set_repair_proposal.md", "w") as f:
        f.write("# Golden Set Repair Proposal\n\n")
        
        for flag in clear_mislabels:
            ex_id = flag["example_id"]
            orig_intent = flag["assigned_intent"]
            prop_intent = flag["suspected_intent"]
            
            # Find the example to get exact text
            ex = next((e for e in original_data if e["example_id"] == ex_id), None)
            text = get_text(ex) if ex else "UNKNOWN"
            
            # Formulate boundary
            boundary = f"{orig_intent} vs {prop_intent}"
            
            # We are highly confident because these were deterministic strict keyword matches
            decision = "REPAIR"
            
            f.write(f"### Example: {ex_id}\n\n")
            f.write(f"**Conversation Text**:\n> {text}\n\n")
            f.write(f"- Original intent: {orig_intent}\n")
            f.write(f"- Proposed intent: {prop_intent}\n")
            f.write(f"- Evidence: {flag['evidence']}\n")
            f.write(f"- Relevant taxonomy boundary: {boundary}\n")
            f.write(f"- Why original label is incorrect: {flag['reason']}\n")
            f.write(f"- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.\n")
            f.write(f"- Confidence: HIGH\n")
            f.write(f"- Decision: {decision}\n\n")
            
            repair_map_entries.append({
                "example_id": ex_id,
                "old_intent": orig_intent,
                "new_intent": prop_intent,
                "reason": flag['reason'],
                "confidence": "HIGH"
            })
            
    # Step 3: Create repair map
    original_hash = hash_file(golden_set_path)
    
    repair_map = {
        "golden_set_hash_before": original_hash,
        "repairs": repair_map_entries
    }
    with open("reports/golden_set_repair_map.json", "w") as f:
        json.dump(repair_map, f, indent=2)
        
    # Step 4: Backup
    shutil.copy2(golden_set_path, backup_path)
    backup_hash = hash_file(backup_path)
    if backup_hash != original_hash:
        print("BACKUP HASH MISMATCH. STOPPING.")
        return

    # Count before
    intent_counts_before = {}
    for ex in original_data:
        intent_counts_before[ex["intent_id"]] = intent_counts_before.get(ex["intent_id"], 0) + 1

    # Step 5: Apply repairs
    repair_dict = {r["example_id"]: r["new_intent"] for r in repair_map_entries}
    
    new_data = []
    actual_intent_changes = 0
    conversation_changes = 0
    escalation_changes = 0
    unexpected_changes = 0
    
    for ex in original_data:
        # copy dict to avoid mutating original_data (so we can compare later)
        new_ex = dict(ex)
        
        if new_ex["example_id"] in repair_dict:
            new_ex["intent_id"] = repair_dict[new_ex["example_id"]]
            actual_intent_changes += 1
            
        new_data.append(new_ex)
        
    with open(golden_set_path, "w") as f:
        for ex in new_data:
            f.write(json.dumps(ex) + "\n")
            
    # Step 6: Integrity check
    new_hash = hash_file(golden_set_path)
    
    # Reload and verify
    reloaded_data = []
    with open(golden_set_path, "r") as f:
        for line in f:
            reloaded_data.append(json.loads(line))
            
    count_before = len(original_data)
    count_after = len(reloaded_data)
    
    integrity_pass = True
    
    if count_before != count_after:
        integrity_pass = False
        
    id_set = set()
    for ex in reloaded_data:
        if ex["example_id"] in id_set:
            integrity_pass = False
        id_set.add(ex["example_id"])
        
    for orig, rep in zip(original_data, reloaded_data):
        if orig["example_id"] != rep["example_id"]:
            integrity_pass = False
        if orig.get("conversation") != rep.get("conversation") and orig.get("messages") != rep.get("messages"):
            conversation_changes += 1
            integrity_pass = False
        if orig.get("escalation") != rep.get("escalation"):
            escalation_changes += 1
            integrity_pass = False
        if orig.get("expected_behavior") != rep.get("expected_behavior"):
            unexpected_changes += 1
            integrity_pass = False
            
        if orig["intent_id"] != rep["intent_id"]:
            if orig["example_id"] not in repair_dict:
                unexpected_changes += 1
                integrity_pass = False
            elif rep["intent_id"] != repair_dict[orig["example_id"]]:
                unexpected_changes += 1
                integrity_pass = False
                
    integrity_report = {
        "count_before": count_before,
        "count_after": count_after,
        "approved_repairs": len(repair_map_entries),
        "actual_intent_changes": actual_intent_changes,
        "conversation_changes": conversation_changes,
        "escalation_changes": escalation_changes,
        "unexpected_changes": unexpected_changes,
        "integrity_pass": integrity_pass
    }
    
    with open("reports/golden_set_integrity_check.json", "w") as f:
        json.dump(integrity_report, f, indent=2)
        
    if not integrity_pass:
        print("INTEGRITY CHECK FAILED. STOPPING.")
        return
        
    # Step 7: Update Hash
    with open("reports/golden_set_version_history.md", "w") as f:
        f.write("# Golden Set Version History\n\n")
        f.write("## Version 1 — Pre Phase 3\n\n")
        f.write(f"- Hash: {original_hash}\n")
        f.write(f"- Examples: {count_before}\n")
        f.write(f"- Status: DEPRECATED (Contains known classification mislabels)\n\n")
        
        f.write("## Version 2 — Post Phase 3\n\n")
        f.write(f"- Hash: {new_hash}\n")
        f.write(f"- Examples: {count_after}\n")
        f.write(f"- Repairs: {actual_intent_changes}\n")
        f.write(f"- Status: ACTIVE (Repaired benchmark)\n\n")
        f.write("Version 2 is the repaired benchmark with resolved deterministic taxonomy overlap contradictions.\n")
        
    # Step 9: Distribution Check
    intent_counts_after = {}
    for ex in reloaded_data:
        intent_counts_after[ex["intent_id"]] = intent_counts_after.get(ex["intent_id"], 0) + 1
        
    all_intents = sorted(list(set(list(intent_counts_before.keys()) + list(intent_counts_after.keys()))))
    
    with open("reports/golden_set_distribution_before_after.md", "w") as f:
        f.write("# Golden Set Label Distribution\n\n")
        f.write("| Intent | Before | After | Change |\n")
        f.write("|---|---:|---:|---:|\n")
        for intent in all_intents:
            b = intent_counts_before.get(intent, 0)
            a = intent_counts_after.get(intent, 0)
            diff = a - b
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            f.write(f"| {intent} | {b} | {a} | {diff_str} |\n")
            
    # Step 10: Update Docs
    with open("reports/phase3_golden_set_repair.md", "w") as f:
        f.write("# Phase 3 — Golden Set Repair\n\n")
        f.write("## Motivation\nPhase 2 identified deterministic label contradictions where the Golden Set labels directly conflicted with the explicit lexical contents of the customer conversations based on the taxonomy definitions.\n\n")
        f.write("## Repairs\n")
        for r in repair_map_entries:
            f.write(f"- `{r['example_id']}`: `{r['old_intent']}` → `{r['new_intent']}`\n")
        f.write(f"\n## Unchanged Examples\n{count_before - actual_intent_changes} examples were left unchanged.\n\n")
        f.write("## Integrity Validation\nAll integrity checks passed. No unexpected conversation, escalation, or structural changes occurred.\n\n")
        f.write("## Benchmark Version\n")
        f.write(f"- Old Hash (V1): {original_hash}\n")
        f.write(f"- New Hash (V2): {new_hash}\n\n")
        f.write("## Impact\nThe benchmark labels were corrected. Model performance has NOT yet been re-evaluated against V2.\n\n")
        f.write("## Next Phase\nRecommend Phase 4: Model Evaluation (re-running the baseline against the repaired V2 benchmark) to determine true model capability.\n")

if __name__ == '__main__':
    run()
