import json
from collections import defaultdict
from src.threadmind import config

INTENT_KEYWORDS = {
    "delivery_wrong_item": ["wrong item", "incorrect", "not what i ordered", "different item"],
    "delivery_missing": ["delivered", "not here", "missing package", "stolen", "didn't receive", "empty box", "never received"],
    "delivery_delayed": ["late", "delay", "not arrived", "still waiting", "taking too long"],
    "returns_refunds": ["return", "refund", "label", "defective", "broken"],
    "account_billing": ["charge", "billed", "unauthorized", "bank", "money", "subscription"],
    "digital_prime_video": ["video", "movie", "streaming", "prime video", "playback"],
    "digital_kindle": ["kindle", "ebook", "paperwhite", "library", "downloading book"],
    "amazon_music": ["music", "song", "playlist", "amazon music"],
    "echo_alexa": ["echo", "alexa", "dot", "device not responding"],
    "account_access": ["login", "password", "locked", "access", "can't sign in", "app crashing"],
    "promotions_pricing": ["discount", "promo", "price", "deal", "coupon"],
    "amazon_locker": ["locker", "access code", "pick up"],
    "grocery_fresh": ["fresh", "whole foods", "grocery", "spoiled", "food", "delivery window"],
    "product_availability": ["stock", "pre-order", "available"]
}

CONFUSION_PAIRS = [
    {"delivery_delayed", "delivery_missing"},
    {"account_billing", "returns_refunds"},
    {"account_access", "account_billing"},
    {"product_availability", "promotions_pricing"}
]

def load_threads(filepath):
    threads = []
    with open(filepath, "r") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads

def extract_text(conversation):
    return " ".join([m['text'].lower() for m in conversation if m['author_role'] == 'customer'])

def get_matched_intents(text):
    matched = set()
    for intent, kws in INTENT_KEYWORDS.items():
        if any(k in text for k in kws):
            matched.add(intent)
    return matched

def main():
    filepath = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    print(f"Loading {filepath}...")
    records = load_threads(filepath)
    
    # Audit metrics
    audit_results = {
        "total_audited": len(records),
        "suspicious_examples": [],
        "semantic_ambiguity_count": 0,
        "structural_complexity_counts": defaultdict(int),
        "context_dependent_count": 0,
        "intent_conflict_count": 0,
        "escalation_evidence": defaultdict(int)
    }
    
    updated_records = []
    
    for r in records:
        conv = r['conversation']
        full_text = extract_text(conv)
        first_msg_text = conv[0]['text'].lower() if conv and conv[0]['author_role'] == 'customer' else ""
        
        # 1. Structural Complexity
        # Note: source_metadata doesn't have has_missing_parent directly in golden_set schema currently.
        # We mapped difficulty to 'ambiguous' if it had missing parent or branch.
        # Let's derive from difficulty: if ambiguous, we will just call it incomplete/branched based on a heuristic, or since we lost the exact boolean, we can infer: if it starts with a brand message, it's incomplete.
        if conv and conv[0]['author_role'] == 'brand':
            struct = "incomplete"
        elif "branch" in r.get("difficulty", ""): # we didn't store branch
            struct = "branched"
        elif r.get("difficulty") == "ambiguous":
            struct = "incomplete"
        else:
            struct = "simple"
            
        audit_results["structural_complexity_counts"][struct] += 1
        
        # 2. Context Dependent
        matched_full = get_matched_intents(full_text)
        matched_first = get_matched_intents(first_msg_text)
        assigned = r['intent_id']
        
        # If assigned intent wasn't in the first message, but is in the full text, it's context dependent
        is_context_dep = assigned not in matched_first and assigned in matched_full
        if is_context_dep:
            audit_results["context_dependent_count"] += 1
            
        # 3. Semantic Ambiguity
        # True if it matches multiple intents that are in our confusion pairs
        is_ambiguous = False
        conflicts = []
        for pair in CONFUSION_PAIRS:
            if pair.issubset(matched_full):
                is_ambiguous = True
                conflicts.append(pair)
                
        if is_ambiguous:
            audit_results["semantic_ambiguity_count"] += 1
            audit_results["intent_conflict_count"] += 1
            
        # 4. Suspicious Examples
        suspicious = False
        reason = []
        
        if assigned not in matched_full and assigned != "other_support":
            suspicious = True
            reason.append(f"Assigned intent {assigned} lacks keyword evidence in text.")
            
        if is_ambiguous:
            suspicious = True
            reason.append(f"Multiple confusable intents detected: {conflicts}")
            
        escalation = r['expected_behavior'].get('escalation')
        audit_results["escalation_evidence"][escalation] += 1
        
        if suspicious:
            audit_results["suspicious_examples"].append({
                "example_id": r['example_id'],
                "thread_id": r['thread_id'],
                "assigned_intent": assigned,
                "reasons": reason
            })
            
        # Update record schema
        r['metadata'] = r.get('source_metadata', {})
        r['metadata']['semantic_ambiguity'] = is_ambiguous
        r['metadata']['structural_complexity'] = struct
        r['metadata']['context_dependent'] = is_context_dep
        if 'source_metadata' in r:
            del r['source_metadata']
            
        updated_records.append(r)
        
    # Write updated golden set
    with open(filepath, "w") as f:
        for r in updated_records:
            f.write(json.dumps(r) + "\n")
            
    # Write Audit Report
    report_path = config.REPORTS_DIR / "golden_set_label_audit.md"
    with open(report_path, "w") as f:
        f.write("# Golden Set Label Integrity Audit\n\n")
        f.write(f"- **Total Examples Audited**: {audit_results['total_audited']}\n")
        f.write(f"- **Suspicious Examples**: {len(audit_results['suspicious_examples'])}\n")
        f.write(f"- **Semantic Ambiguity Count**: {audit_results['semantic_ambiguity_count']}\n")
        f.write(f"- **Context-Dependent Count**: {audit_results['context_dependent_count']}\n")
        f.write(f"- **Intent Conflict Count**: {audit_results['intent_conflict_count']}\n\n")
        
        f.write("## Structural Complexity\n")
        for k, v in audit_results['structural_complexity_counts'].items():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n## Escalation Evidence Distribution\n")
        for k, v in audit_results['escalation_evidence'].items():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n## Suspicious Examples Analysis\n")
        if not audit_results['suspicious_examples']:
            f.write("No severe conflicts detected.\n")
        else:
            for ex in audit_results['suspicious_examples']:
                f.write(f"### {ex['example_id']} (Thread: `{ex['thread_id']}`)\n")
                f.write(f"- Assigned Intent: `{ex['assigned_intent']}`\n")
                f.write("- Reasons:\n")
                for res in ex['reasons']:
                    f.write(f"  - {res}\n")
                    
    # Update Statistics JSON
    stats_path = config.REPORTS_DIR / "golden_set_statistics.json"
    with open(stats_path, "r") as f:
        stats = json.load(f)
        
    stats["semantic_ambiguity_count"] = audit_results["semantic_ambiguity_count"]
    stats["structural_complexity"] = dict(audit_results["structural_complexity_counts"])
    stats["context_dependent_count"] = audit_results["context_dependent_count"]
    stats["intent_conflict_count"] = audit_results["intent_conflict_count"]
    
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
        
    # Update Statistics MD
    with open(config.REPORTS_DIR / "golden_set_statistics.md", "a") as f:
        f.write("\n## Complexity & Ambiguity Audit\n")
        f.write(f"- **Semantic Ambiguity**: {audit_results['semantic_ambiguity_count']}\n")
        f.write(f"- **Context-Dependent**: {audit_results['context_dependent_count']}\n")
        f.write(f"- **Intent Conflicts**: {audit_results['intent_conflict_count']}\n")
        for k, v in audit_results['structural_complexity_counts'].items():
            f.write(f"- Structural ({k}): {v}\n")

if __name__ == "__main__":
    main()
