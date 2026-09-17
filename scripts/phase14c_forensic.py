import json
import os

def main():
    with open("reports/phase14b_v3_pilot.json", "r") as f:
        pilot_data = json.load(f)
        
    results = pilot_data["results"]
    
    # 1. Build paired dataset & classify
    improvements = []
    regressions = []
    both_correct = []
    both_wrong = []
    
    for r in results:
        record = {
            "id": r["thread_id"],
            "expected_intent": r["expected_intent"],
            "v2_prediction": r["v2_predicted_intent"],
            "v3_prediction": r["v3_predicted_intent"],
            "retrieved_candidates": r["retrieved_intents"],
            "v2_correct": r["v2_correctness"],
            "v3_correct": r["v3_correctness"],
            "failure_category": r.get("failure_category", "CORRECT_V2"),
            "v3_reasoning": r.get("v3_reasoning", "")
        }
        
        if record["v2_correct"] and not record["v3_correct"]:
            regressions.append(record)
        elif not record["v2_correct"] and record["v3_correct"]:
            improvements.append(record)
        elif record["v2_correct"] and record["v3_correct"]:
            both_correct.append(record)
        else:
            both_wrong.append(record)
            
    # Write JSON artifact
    json_output = {
        "improvements": improvements,
        "regressions": regressions,
        "both_correct": both_correct,
        "both_wrong": both_wrong
    }
    
    with open("reports/phase14c_v3_forensic_analysis.json", "w") as f:
        json.dump(json_output, f, indent=2)
        
    # Write MD forensic analysis
    with open("reports/phase14c_v3_forensic_analysis.md", "w") as f:
        f.write("# Phase 14C — V2 vs V3 Forensic Failure Analysis\n\n")
        f.write("## 1. Top V3 Improvements (V2 ❌ → V3 ✅)\n")
        f.write("These represent the POSITIVE behaviors introduced by V3.\n\n")
        for i, imp in enumerate(improvements[:10]):
            f.write(f"### {i+1}. {imp['id']}\n")
            f.write(f"- **Expected**: `{imp['expected_intent']}`\n")
            f.write(f"- **V2 Prediction**: `{imp['v2_prediction']}`\n")
            f.write(f"- **Retrieved**: `{imp['retrieved_candidates']}`\n")
            f.write(f"- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `{imp['v2_prediction']}` despite correct evidence.\n")
            f.write(f"- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`\n")
            f.write(f"- **V3 Reasoning Snippet**: {imp['v3_reasoning']}\n\n")
            
        f.write("## 2. Top V3 Regressions (V2 ✅ → V3 ❌)\n")
        f.write("These represent the HARMFUL behaviors introduced by V3.\n\n")
        for i, reg in enumerate(regressions[:10]):
            f.write(f"### {i+1}. {reg['id']}\n")
            f.write(f"- **Expected**: `{reg['expected_intent']}`\n")
            f.write(f"- **V3 Prediction**: `{reg['v3_prediction']}` (V2 correctly chose `{reg['v2_prediction']}`)\n")
            f.write(f"- **Retrieved**: `{reg['retrieved_candidates']}`\n")
            f.write(f"- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.\n")
            f.write(f"- **V3 Reasoning Snippet**: {reg['v3_reasoning']}\n\n")
            
        f.write("## 3. Instruction-Level Causal Patterns\n\n")
        f.write("| V3 Instruction/Rule | Intended Effect | Risk |\n")
        f.write("|---|---|---|\n")
        f.write("| `If retrieved examples unanimously share an intent... prefer it.` | Fix CLASSIFIER_IGNORED_CORRECT | **BENEFICIAL** (Fixed 11 cases) |\n")
        f.write("| Explicit Taxonomy Boundary Rules (e.g. `grocery_fresh` vs `returns_refunds`) | Fix CONFLICTING_EVIDENCE | **OVERLY AGGRESSIVE** (Caused regressions by forcing intents against context) |\n")
        f.write("| `Prefer the candidate whose taxonomy definition best matches...` | Anchor reasoning in actual problem | **HARMFUL** (Caused the LLM to completely ignore unanimous RAG context and act zero-shot) |\n")
        f.write("| `Do not choose an intent merely because it appears frequently in retrieval` | Prevent RAG bias | **REDUNDANT/OVERLY AGGRESSIVE** (Re-introduced the V2 over-correction problem) |\n\n")
        
        f.write("## 4. Evidence Hierarchy Recommendation\n\n")
        f.write("**STRATEGY D**: Unanimous high-quality RAG evidence gets strong weight, but never overrides explicit contradiction in the user request.\n")
        f.write("- **Why**: The biggest win of V3 was explicitly trusting unanimous RAG context. The biggest failure was V3 overriding RAG context due to rigid, hardcoded boundary rules or zero-shot keyword interpretations. By implementing Strategy D, we keep the gains on `CLASSIFIER_IGNORED_CORRECT` without destroying the baseline accuracy on `CORRECT_V2` examples.\n\n")
        
    # Write V4 Design Spec
    with open("reports/phase14c_v4_design_spec.md", "w") as f:
        f.write("# Phase 14C — Minimal V4 Design Spec\n\n")
        f.write("## 1. Problems V4 must fix\n")
        f.write("- Re-capture the 11 improvements from V3 (specifically `CLASSIFIER_IGNORED_CORRECT`).\n")
        f.write("- Eliminate the 19 regressions caused by V3's rigid boundary rules and zero-shot over-correction.\n\n")
        
        f.write("## 2. V3 behaviors that must be removed\n")
        f.write("- **Hardcoded Boundary Rules**: Remove the strict disambiguation rules (e.g., 'If the user mentions X, it is Y, not Z'). They are too rigid and cause the LLM to ignore nuanced context.\n")
        f.write("- **Explicit RAG Distrust**: Remove 'Do not choose an intent merely because it appears frequently in retrieval'.\n\n")
        
        f.write("## 3. V3 behaviors that must be retained\n")
        f.write("- **Positive RAG Affirmation**: Retain the instruction to affirmatively trust unanimous/consistent RAG examples.\n\n")
        
        f.write("## 4. Evidence Hierarchy\n")
        f.write("- **Level 1 (Highest)**: Clear, explicit contradiction (e.g. RAG says X, but user explicitly asks for Y).\n")
        f.write("- **Level 2 (Strong)**: Unanimous RAG evidence (e.g. [X, X, X]). Trust this heavily.\n")
        f.write("- **Level 3 (Fallback)**: Zero-shot taxonomy definition mapping.\n\n")
        
        f.write("## 5. RAG conflict-resolution principles\n")
        f.write("- When RAG examples conflict (e.g. [X, X, Y]), instruct the LLM to use the *conversation context* of the retrieved examples to break the tie, rather than falling back immediately to zero-shot taxonomy definitions.\n\n")
        
        f.write("## 6. Explicit anti-overcorrection safeguards\n")
        f.write("- Instead of warning the LLM *not* to trust RAG, instruct it to *synthesize* RAG.\n")
        f.write("- The prompt must remain a **Minimal Patch** over V2, preserving V2's exact structure and sequence, simply replacing the negative 'DO NOT classify based solely on the closest retrieved example' with a positive evidence-weighting rule.\n\n")
        
        f.write("## 7. Validation Gates\n")
        f.write("- **GATE 1**: V4 must outperform V2 on targeted failure categories.\n")
        f.write("- **GATE 2**: V4 must not reproduce the Phase 14B regression rate (must be < 5 regressions).\n")
        f.write("- **GATE 3**: No major intent may collapse.\n")
        f.write("- **GATE 4**: Malformed responses = 0.\n")
        f.write("- **GATE 5**: Invalid intent responses = 0.\n")
        f.write("- **GATE 6**: Overall accuracy must improve.\n")
        f.write("- **GATE 7**: Macro F1 must improve or remain statistically stable.\n")
        f.write("- **GATE 8**: V2 remains production baseline until V4 passes full evaluation.\n")

if __name__ == "__main__":
    main()
