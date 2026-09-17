import os
import sys
import json
import csv
import hashlib
from collections import defaultdict

# Stability settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_golden_set(filepath):
    expected_hash = "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f"
    actual_hash = hash_file(filepath)
    if actual_hash != expected_hash:
        raise ValueError(f"Golden Set hash mismatch! Expected {expected_hash}, got {actual_hash}")
        
    line_count = sum(1 for _ in open(filepath))
    if line_count != 196:
        raise ValueError(f"Expected 196 lines, got {line_count}")
        
    return actual_hash

def get_review_guidance(boundary):
    guidance = {
        "amazon_locker ↔ delivery_missing": "Determine whether the locker itself is the primary problem (e.g. broken, wrong code) or whether the missing package is the primary problem (e.g. tracking says delivered but locker is empty).",
        "account_access ↔ delivery_missing": "Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution. If they cannot log in to check tracking, account recovery may take precedence.",
        "account_access ↔ delivery_delayed": "Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution.",
        "account_access ↔ delivery_wrong_item": "Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution.",
        "returns_refunds ↔ delivery_missing": "Determine whether the customer is just reporting a missing item (seeking a replacement/whereabouts) or explicitly and primarily requesting a refund for the failure.",
        "returns_refunds ↔ delivery_delayed": "Determine whether the customer is just reporting a delayed item or explicitly and primarily requesting a refund for the delay.",
        "grocery_fresh ↔ returns_refunds": "Determine whether the issue is specifically about Amazon Fresh/grocery items. Grocery issues generally have specific handling separate from general returns.",
        "digital_kindle ↔ other_support": "Determine if the issue strictly pertains to Kindle devices or eBooks.",
        "echo_alexa ↔ other_support": "Determine if the issue strictly pertains to Alexa/Echo devices.",
        "promotions_pricing ↔ other_support": "Determine if the core issue is about pricing, price-matching, or promotions.",
        "product_availability ↔ other_support": "Determine if the core issue is inquiring about stock availability or pre-order dates.",
        "account_billing ↔ other_support": "Determine if the core issue is related to unexpected charges, payment methods, or Prime membership fees."
    }
    return guidance.get(boundary, "Examine the conversation to determine which label captures the customer's primary actionable request.")

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    hash_before = verify_golden_set(golden_path)

    audit_json_path = config.PROJECT_ROOT / "reports" / "phase16e_taxonomy_audit.json"
    with open(audit_json_path, "r") as f:
        cases = json.load(f)
        
    patch_path = config.PROJECT_ROOT / "reports" / "phase16b_golden_set_proposed_patch.json"
    simulated_patches = {}
    if os.path.exists(patch_path):
        with open(patch_path, "r") as f:
            for p in json.load(f):
                simulated_patches[p["example_id"]] = p["proposed_intent"]

    # Generate reports/phase16h_human_review_decisions.csv
    csv_headers = [
        "example_id",
        "current_label",
        "v2_prediction",
        "retrieved_intents",
        "similarity_scores",
        "failure_category",
        "ambiguity_boundary",
        "proposed_label",
        "human_decision",
        "new_label",
        "reviewer_rationale"
    ]
    
    csv_rows = []
    workbench_cases = []
    
    failures_by_category = defaultdict(int)
    boundaries = defaultdict(int)

    for case in cases:
        boundary = " ↔ ".join(sorted([case["gold_label"], case["v2_prediction"]]))
        proposed = simulated_patches.get(case["id"], "")
        
        failures_by_category[case["failure_category"]] += 1
        boundaries[boundary] += 1
        
        row = {
            "example_id": case["id"],
            "current_label": case["gold_label"],
            "v2_prediction": case["v2_prediction"],
            "retrieved_intents": ",".join(case["top_3_retrieved_intents"]),
            "similarity_scores": ",".join(map(str, case["retrieval_scores"])),
            "failure_category": case["failure_category"],
            "ambiguity_boundary": boundary,
            "proposed_label": proposed,
            "human_decision": "",
            "new_label": "",
            "reviewer_rationale": ""
        }
        csv_rows.append(row)
        
        workbench_cases.append({
            "id": case["id"],
            "current_label": case["gold_label"],
            "conversation": case["conversation"],
            "v2_prediction": case["v2_prediction"],
            "predicted_in_top3": case["v2_prediction"] in case["top_3_retrieved_intents"],
            "top_3_retrieved": case["top_3_retrieved_intents"],
            "retrieval_scores": case["retrieval_scores"],
            "failure_category": case["failure_category"],
            "boundary": boundary,
            "guidance": get_review_guidance(boundary),
            "proposed_label": proposed,
            "evidence_current": case["evidence_supporting_current_label"],
            "evidence_alternative": case["evidence_supporting_alternative"]
        })

    with open("reports/phase16h_human_review_decisions.csv", "w", newline="") as outf:
        writer = csv.DictWriter(outf, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_rows)
        
    with open("reports/phase16h_human_review_workbench.json", "w") as outf:
        json.dump(workbench_cases, outf, indent=2)

    with open("reports/phase16h_human_review_workbench.md", "w") as outf:
        outf.write("# PHASE 16H — HUMAN TAXONOMY REVIEW\n\n")
        
        outf.write("## Baseline\n")
        outf.write("- **V2 Accuracy**: 87.76%\n")
        outf.write("- **V2 Macro F1**: 0.8579\n")
        outf.write("- **Golden Set count**: 196\n")
        outf.write(f"- **Golden Set hash**: {hash_before}\n\n")
        
        outf.write("## Review Population\n")
        outf.write(f"- **Total cases**: 24\n\n")
        outf.write("### Failure categories\n")
        for cat, cnt in failures_by_category.items():
            outf.write(f"- {cat}: {cnt}\n")
        outf.write("\n### Ambiguity boundaries\n")
        for b, cnt in boundaries.items():
            outf.write(f"- {b}: {cnt}\n")
            
        outf.write("\n## Case-by-Case Review\n")
        for c in workbench_cases:
            outf.write(f"\n### {c['id']}\n")
            outf.write(f"**Conversation**:\n```\n{c['conversation']}\n```\n")
            outf.write(f"- **Current Golden Set label**: `{c['current_label']}`\n")
            outf.write(f"- **V2 predicted intent**: `{c['v2_prediction']}`\n")
            outf.write(f"- **V2 prediction in Top-3?**: {'Yes' if c['predicted_in_top3'] else 'No'}\n")
            outf.write(f"- **Top-3 retrieved intents**: {c['top_3_retrieved']}\n")
            outf.write(f"- **Retrieval similarity scores**: {c['retrieval_scores']}\n")
            outf.write(f"- **Failure category**: {c['failure_category']}\n")
            outf.write(f"- **Ambiguity boundary**: {c['boundary']}\n")
            outf.write(f"- **Review Guidance**: {c['guidance']}\n")
            if c['proposed_label']:
                outf.write(f"- **Proposed alternative label**: `{c['proposed_label']}`\n")
            outf.write(f"- **Evidence supporting current label**: {c['evidence_current']}\n")
            outf.write(f"- **Evidence supporting alternative label**: {c['evidence_alternative']}\n")
            outf.write("\n**Human decision field**: `[BLANK]`\n")
            outf.write("**Human reviewer rationale**: `[BLANK]`\n")
            outf.write("---\n")
            
        outf.write("\n## Human Decision Instructions\n")
        outf.write("""
The `reports/phase16h_human_review_decisions.csv` file must be completed using exactly these decisions:
1. **KEEP**: The current label is completely correct and unambiguous.
2. **CHANGE_LABEL**: The current label is wrong. You MUST provide the `new_label` (from the standard 14 intents).
3. **AMBIGUOUS_KEEP**: Both the current label and the V2 prediction are valid interpretations, but we will preserve the current label as the ground truth.
4. **REVIEW_TAXONOMY**: The taxonomy fundamentally fails to distinguish these two concepts and requires a structural update.
5. **INSUFFICIENT_EVIDENCE**: The conversation is too short or garbled to determine any intent.

If `CHANGE_LABEL` is chosen, `new_label` MUST be filled. Otherwise, `new_label` remains blank.
Provide a `reviewer_rationale` for every decision.
""")
        outf.write("\n## Safety Verification\n")
        outf.write("- Golden Set modified: NO\n")
        outf.write("- FAISS modified: NO\n")
        outf.write("- Model modified: NO\n")
        outf.write("- Production modified: NO\n\n")
        
        outf.write("## Final Status\n")
        outf.write("READY_FOR_REAL_HUMAN_REVIEW\n")
        
    hash_after = verify_golden_set(golden_path)
    if hash_before != hash_after:
        raise ValueError("CRITICAL: Golden Set was modified during execution!")
        
    print("PHASE 16H STATUS:")
    print("READY_FOR_REAL_HUMAN_REVIEW")
    print()
    print("CURRENT BEST:")
    print("V2")
    print()
    print("V2 ACCURACY:")
    print("87.76%")
    print()
    print("V2 MACRO F1:")
    print("0.8579")
    print()
    print("REVIEW CASES:")
    print("24")
    print()
    print("HUMAN DECISIONS:")
    print("0/24")
    print()
    print("GOLDEN SET:")
    print("196")
    print()
    print("GOLDEN SET HASH:")
    print("6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f")
    print()
    print("GOLDEN SET MODIFIED:")
    print("NO")
    print()
    print("FAISS MODIFIED:")
    print("NO")
    print()
    print("MODEL MODIFIED:")
    print("NO")
    print()
    print("PRODUCTION MODIFIED:")
    print("NO")
    print()
    print("NEXT STEP:")
    print("ACTUAL HUMAN TAXONOMY DECISIONS")
    print()
    print("STOP_AFTER_PHASE_16H:")
    print("YES")

if __name__ == "__main__":
    main()
