# Phase 14C — Minimal V4 Design Spec

## 1. Problems V4 must fix
- Re-capture the 11 improvements from V3 (specifically `CLASSIFIER_IGNORED_CORRECT`).
- Eliminate the 19 regressions caused by V3's rigid boundary rules and zero-shot over-correction.

## 2. V3 behaviors that must be removed
- **Hardcoded Boundary Rules**: Remove the strict disambiguation rules (e.g., 'If the user mentions X, it is Y, not Z'). They are too rigid and cause the LLM to ignore nuanced context.
- **Explicit RAG Distrust**: Remove 'Do not choose an intent merely because it appears frequently in retrieval'.

## 3. V3 behaviors that must be retained
- **Positive RAG Affirmation**: Retain the instruction to affirmatively trust unanimous/consistent RAG examples.

## 4. Evidence Hierarchy
- **Level 1 (Highest)**: Clear, explicit contradiction (e.g. RAG says X, but user explicitly asks for Y).
- **Level 2 (Strong)**: Unanimous RAG evidence (e.g. [X, X, X]). Trust this heavily.
- **Level 3 (Fallback)**: Zero-shot taxonomy definition mapping.

## 5. RAG conflict-resolution principles
- When RAG examples conflict (e.g. [X, X, Y]), instruct the LLM to use the *conversation context* of the retrieved examples to break the tie, rather than falling back immediately to zero-shot taxonomy definitions.

## 6. Explicit anti-overcorrection safeguards
- Instead of warning the LLM *not* to trust RAG, instruct it to *synthesize* RAG.
- The prompt must remain a **Minimal Patch** over V2, preserving V2's exact structure and sequence, simply replacing the negative 'DO NOT classify based solely on the closest retrieved example' with a positive evidence-weighting rule.

## 7. Validation Gates
- **GATE 1**: V4 must outperform V2 on targeted failure categories.
- **GATE 2**: V4 must not reproduce the Phase 14B regression rate (must be < 5 regressions).
- **GATE 3**: No major intent may collapse.
- **GATE 4**: Malformed responses = 0.
- **GATE 5**: Invalid intent responses = 0.
- **GATE 6**: Overall accuracy must improve.
- **GATE 7**: Macro F1 must improve or remain statistically stable.
- **GATE 8**: V2 remains production baseline until V4 passes full evaluation.
