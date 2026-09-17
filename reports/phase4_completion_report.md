# Phase 4: Reply Generation & LLM-as-Judge Evaluation Report

> **Date**: 2026-09-12
> **Infrastructure**: Local Ollama + Llama 3.2:latest (3B) — zero paid API calls.
> **Important**: All evaluations in this report are automated. No human annotator has independently scored the generated replies. Actual human evaluation remains **PENDING**.

---

## 1. Executive Summary

This report presents the complete evaluation of ThreadMind's retrieval-grounded reply generation pipeline. All 196 Golden Set examples were processed through the full architecture (Rule Baseline → TF-IDF Confidence Router → Dense FAISS K=3 → Llama 3.2) and evaluated by two independent automated evaluators:

1. **LLM Judge** (Pass 1): Zero-shot Llama 3.2 evaluation using `judge_rubric_v1.txt`
2. **Independent LLM Scorer** (Pass 2): Llama 3.2 re-evaluation with an explicitly strict rubric on a 30-example stratified subset

**Key finding**: The two automated evaluators show **poor to slight agreement** (Quadratic κ ranging from −0.10 to +0.19). The LLM Judge systematically overrates Helpfulness (Judge mean 4.63 vs Independent Scorer mean 3.63, Δ = +1.00) and Correctness (Judge 4.53 vs Independent Scorer 3.73, Δ = +0.80). Because both evaluators are the same 3B parameter model, this disagreement demonstrates that Llama 3.2 produces unstable quality judgements that vary significantly with prompt framing. **Actual human evaluation has not been performed.**

---

## 2. Architecture

```
Customer Thread
  → Thread Reconstruction
    → Rule Baseline (deterministic keywords)
      → TF-IDF Confidence Router (threshold = 0.95)
        → Dense FAISS Retrieval (K=3, all-MiniLM-L6-v2)
          → Llama 3.2 (grounded reply generation)
            → LLM-as-Judge (quality evaluation)
```

---

## 3. Evaluation Layer A: LLM-as-Judge (N=196, Automated)

| Dimension      | Avg Score (1–5) |
|----------------|-----------------|
| Correctness    | 4.54            |
| Groundedness   | 4.86            |
| Helpfulness    | 4.58            |
| Tone           | 5.00            |

| Metric              | Value  |
|----------------------|--------|
| Hallucination Rate   | 4.59%  |
| Hallucinated Cases   | 9/196  |
| Evaluation Failures  | 0/196  |

---

## 4. Evaluation Layer B: Independent LLM Scorer (N=30, Automated Strict Re-evaluation)

> [!IMPORTANT]
> These scores are from a **second, independent** Llama 3.2 evaluation pass with an explicitly strict rubric. Both the Judge and this scorer are automated Llama 3.2 evaluators — neither constitutes human evaluation.

### 4.1 Average Score Comparison (Independent LLM Scorer vs LLM Judge)

| Dimension      | Independent Scorer | Judge | Delta  |
|----------------|-------------------|-------|--------|
| Correctness    | 3.73              | 4.53  | −0.80  |
| Groundedness   | 4.67              | 4.80  | −0.13  |
| Helpfulness    | 3.63              | 4.63  | −1.00  |
| Tone           | 4.97              | 5.00  | −0.03  |

### 4.2 Cohen's Quadratic Kappa (Independent LLM Scorer vs LLM Judge)

> [!WARNING]
> These Kappa values measure agreement between **two automated LLM evaluators**, not between a human and an LLM. They should NOT be interpreted as human validation.

| Dimension      | Quadratic κ | Exact Agreement | Interpretation          |
|----------------|-------------|-----------------|-------------------------|
| Correctness    | +0.186      | 13/30 (43.3%)   | Slight agreement        |
| Groundedness   | −0.098      | 24/30 (80.0%)   | Poor (worse than chance) |
| Helpfulness    | −0.058      | 14/30 (46.7%)   | Poor (worse than chance) |
| Tone           | +0.000      | 29/30 (96.7%)   | Slight (ceiling effect)  |

### 4.3 Largest Disagreements Between Automated Evaluators (|Δ| ≥ 2)

| Example | Dimension     | Ind. Scorer | Judge | Δ   |
|---------|---------------|-------------|-------|-----|
| GS-107  | Correctness   | 2           | 5     | −3  |
| GS-107  | Groundedness  | 2           | 5     | −3  |
| GS-107  | Helpfulness   | 2           | 5     | −3  |
| GS-028  | Groundedness  | 2           | 5     | −3  |
| GS-056  | Groundedness  | 2           | 5     | −3  |
| GS-062  | Helpfulness   | 2           | 5     | −3  |
| GS-173  | Helpfulness   | 2           | 5     | −3  |
| GS-108  | Helpfulness   | 2           | 5     | −3  |
| GS-139  | Helpfulness   | 2           | 5     | −3  |
| GS-139  | Groundedness  | 5           | 2     | +3  |
| GS-150  | Groundedness  | 5           | 2     | +3  |

### 4.4 Interpretation

1. **Correctness (κ = 0.19)**: Slight agreement. The Judge inflates scores for generic but topically-adjacent replies that don't address the customer's specific latest message.
2. **Groundedness (κ = −0.10)**: Poor agreement. The two evaluators disagree in both directions — the Judge misses hallucinations (GS-028, GS-056, GS-107) and also falsely flags grounded replies (GS-139, GS-150).
3. **Helpfulness (κ = −0.06)**: Poor agreement. This is the largest systematic bias: the Judge gives 5/5 to replies that the stricter scorer considers unhelpful (Δ = −1.00 mean gap).
4. **Tone (κ = 0.00)**: Ceiling effect — both scorers nearly always assign 5, so there is no meaningful variation to measure agreement on.

---

## 5. Evaluation Layer C: Human Evaluation — PENDING

> [!CAUTION]
> **No human annotator has independently scored the 30-example subset.** The scores currently stored in `reports/human_scoring_subset.csv` were generated by an automated script (Independent LLM Scorer), NOT by a human.
>
> Therefore:
> - **Judge-vs-Human agreement cannot currently be established.**
> - The reported Cohen's Kappa values measure agreement between two automated Llama 3.2 evaluators only.
> - These Kappa values should NOT be interpreted as human validation of the LLM Judge.
>
> To complete human validation, a human annotator must independently score the 30 examples using the rubric in [human_scoring_instructions.md](file:///Users/pratikskanoj/ThreadMind/reports/human_scoring_instructions.md).

---

## 6. Failure Case Analysis

### 6.1 Worst-Scored Example: GS-107

| Dimension      | Judge | Ind. Scorer |
|----------------|-------|-------------|
| Correctness    | 5     | 2           |
| Groundedness   | 5     | 2           |
| Helpfulness    | 5     | 2           |
| Tone           | 5     | 4           |

**Independent Scorer Reasoning:**
- *Correctness (2)*: The reply does not address the customer's latest message about Music Unlimited for DFB-Pokal (Radio). It asks for order information instead, which is irrelevant.
- *Groundedness (2)*: The reply invents the concept of "order information" and assumes the customer has an order, which is not present in the conversation.
- *Helpfulness (2)*: Provides generic help but doesn't acknowledge the specific issue.
- *Tone (4)*: Professional but formulaic.

### 6.2 Top 5 Verified Failure Modes

1. **Hallucinated Context** (4.59%): Agent invents tracking numbers, order details, or policy specifics not grounded in the retrieved evidence.
2. **Off-Topic Response**: Agent addresses the general domain but misses the customer's specific latest message (especially in multi-turn conversations).
3. **Assumed Policies**: Agent states generic policies (refund timelines, return windows) without explicit grounding.
4. **Language Mismatch**: German/other-language conversations receive English replies, which may not help the customer.
5. **Over-Escalation**: Agent escalates routine queries to human review unnecessarily.

---

## 7. Integrity Checks

| Check                          | Result |
|--------------------------------|--------|
| Full test suite (40 tests)     | ✅ All passed |
| Golden Set leakage audit       | ✅ 0 threads in retrieval pool |
| Golden Set labels used in generation | ✅ NO — only conversation_history and retrieved FAISS examples |
| Golden Set labels used in scoring    | ✅ NO — only conversation_history and agent_reply |
| Paid API calls                 | ✅ 0 (local Ollama only) |
| `.env` secrets                 | ✅ No API keys committed |

---

## 8. Limitations

1. **No human evaluation**: No human annotator has scored the generated replies. All quality assessments are automated and subject to the biases of the 3B Llama 3.2 model.
2. **Judge unreliability**: Two independent Llama 3.2 scoring passes show poor-to-slight agreement (κ from −0.10 to +0.19), demonstrating that the model cannot produce stable quality judgements.
3. **Retrieval coverage**: Dense FAISS Recall@3 is 65.31%, meaning 35% of generated replies lack relevant grounded context.
4. **Language support**: The system generates English replies for non-English conversations (e.g., GS-163 in German).
5. **Hallucination rate underestimated**: The Judge's 4.59% hallucination rate is likely an undercount, given that the Independent Scorer flagged additional cases the Judge missed.
6. **Same-model bias**: Both automated evaluators use the same Llama 3.2 architecture, meaning shared blind spots are invisible in automated evaluation.

---

## 9. Production-Readiness Recommendation

> [!CAUTION]
> **NOT production-ready.** Key concerns:
> - No human evaluation has been performed
> - The LLM Judge **cannot be used as a quality gate** (negative Kappa between two automated evaluators)
> - Independent LLM Scorer-rated Helpfulness averages 3.63/5.0
> - Hallucination detection by the Judge is unreliable (missed 3-point disagreements)
> - 4.59% hallucination rate is likely an undercount

**Next steps (in priority order):**
1. Obtain genuine human evaluation of the 30-example subset
2. Improve retrieval recall (embedding fine-tuning or hybrid retrieval) to reduce ungrounded generation
3. Add explicit grounding constraints and negative examples to the generation prompt
4. If automated evaluation is needed, use a larger/more capable judge model or implement rule-based hallucination detection
5. Re-evaluate after retrieval and prompt improvements

---

## 10. Artifacts Produced

| File | Description |
|------|-------------|
| [generated_replies.json](file:///Users/pratikskanoj/ThreadMind/reports/generated_replies.json) | 196 generated replies with routing metadata |
| [judge_evaluation_results.json](file:///Users/pratikskanoj/ThreadMind/reports/judge_evaluation_results.json) | Full LLM-as-Judge scores for all 196 examples |
| [llm_independent_scoring_subset.csv](file:///Users/pratikskanoj/ThreadMind/reports/llm_independent_scoring_subset.csv) | 30-example subset with Independent LLM Scorer scores |
| [llm_independent_scoring_details.json](file:///Users/pratikskanoj/ThreadMind/reports/llm_independent_scoring_details.json) | Per-example reasoning from Independent LLM Scorer |
| [human_scoring_subset.csv](file:///Users/pratikskanoj/ThreadMind/reports/human_scoring_subset.csv) | 30-example subset with automated scores (human columns filled by LLM, NOT human) |
| [human_scoring_instructions.md](file:///Users/pratikskanoj/ThreadMind/reports/human_scoring_instructions.md) | Rubric for future human annotators |
| [human_vs_judge_agreement.json](file:///Users/pratikskanoj/ThreadMind/reports/human_vs_judge_agreement.json) | Cohen's Kappa between two automated LLM evaluators (mislabeled as "human" in JSON keys) |
