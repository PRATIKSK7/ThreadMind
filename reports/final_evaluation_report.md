# ThreadMind — Final Evaluation Report

> **Date**: 2026-09-12
> **Project**: AI Customer Support Agent (Hiver SDE Intern Take-Home)
> **Dataset**: Customer Support on Twitter — AmazonHelp (single-brand)
> **Infrastructure**: 100% local — Ollama + Llama 3.2:latest (3B), zero paid API calls

---

## 1. Architecture Summary

```
Raw Twitter Data (2.8M tweets)
  → Thread Reconstruction (82,556 threads)
    → Single-Brand Filtering (AmazonHelp)
      → Intent Taxonomy (9 intents + 3 escalation levels)
        → Golden Evaluation Set (196 examples, leak-free)
          → Classifier Pipeline:
              Rule Baseline (deterministic keywords)
                → TF-IDF Confidence Router (threshold = 0.95)
                  → Dense FAISS Retrieval (K=3, all-MiniLM-L6-v2)
                    → Llama 3.2 (classification + reply generation)
          → Evaluation Harness:
              LLM-as-Judge (Pass 1: standard rubric)
              Independent LLM Scorer (Pass 2: strict rubric)
              Human Evaluation: PENDING
```

---

## 2. Intent Classification Results

### 2.1 Baseline Comparison (Golden Set, N=196)

| Method | Accuracy | Macro F1 |
|--------|----------|----------|
| Rule Baseline | 98.98% | — |
| TF-IDF Baseline | — | — |
| Llama 3.2 Zero-Shot | — | — |
| TF-IDF RAG K=3 | 43.88% | — |
| **Final Fallback Router** | **100.00%** | **1.000** |

### 2.2 Router Performance on Unseen Data (N=500, Step 10 Validation)

| Metric | Value |
|--------|-------|
| Rule-handled rate | 30.8% |
| Fallback (LLM) rate | **69.2%** |
| Latency (rule path) | ~1ms |
| Latency (LLM path) | ~3–8s |

---

## 3. Reply Generation Quality

### 3.1 LLM-as-Judge (N=196, Automated — Llama 3.2)

| Dimension | Avg Score (1–5) |
|-----------|-----------------|
| Correctness | 4.54 |
| Groundedness | 4.86 |
| Helpfulness | 4.58 |
| Tone | 5.00 |
| **Hallucination Rate** | **4.59% (9/196)** |

### 3.2 Independent LLM Scorer (N=30, Automated — Llama 3.2 with Strict Rubric)

| Dimension | Ind. Scorer | Judge | Delta |
|-----------|-------------|-------|-------|
| Correctness | 3.73 | 4.53 | −0.80 |
| Groundedness | 4.67 | 4.80 | −0.13 |
| Helpfulness | 3.63 | 4.63 | **−1.00** |
| Tone | 4.97 | 5.00 | −0.03 |

### 3.3 Cohen's Quadratic Kappa (Between Two Automated LLM Evaluators)

| Dimension | κ | Interpretation |
|-----------|---|----------------|
| Correctness | +0.186 | Slight agreement |
| Groundedness | −0.098 | Poor (worse than chance) |
| Helpfulness | −0.058 | Poor (worse than chance) |
| Tone | +0.000 | Slight (ceiling effect) |

> [!WARNING]
> These Kappa values measure agreement between **two automated Llama 3.2 evaluators**. They do NOT represent human-vs-judge agreement. Because no human annotator has independently scored the 30-example subset, human-vs-judge agreement cannot currently be established.

### 3.4 Human Evaluation Status

**PENDING.** The rubric and blank CSV are available at:
- [human_scoring_instructions.md](file:///Users/pratikskanoj/ThreadMind/reports/human_scoring_instructions.md) — 1–5 scoring rubric for Correctness, Groundedness, Helpfulness, Tone
- [human_scoring_subset.csv](file:///Users/pratikskanoj/ThreadMind/reports/human_scoring_subset.csv) — 30-example subset (currently contains automated scores, NOT human scores)

To complete human validation: a human annotator must independently score the 30 examples and overwrite the `human_*_1_to_5` columns with genuine human judgements.

---

## 4. Retrieval Performance

| Metric | Value |
|--------|-------|
| Embedding Model | all-MiniLM-L6-v2 |
| Index Type | FAISS (Dense) |
| Retrieval K | 3 |
| Recall@3 | **65.31%** |
| Retrieval Pool Size | 82,360 threads |

> [!IMPORTANT]
> The 65.31% Recall@3 means 35% of generated replies lack relevant grounded context, forcing the LLM to rely on zero-shot generation and increasing hallucination risk.

---

## 5. Integrity & Safety

| Check | Result |
|-------|--------|
| Test suite | ✅ 40/40 passed |
| Golden Set leakage | ✅ 0 threads in retrieval pool |
| Gold labels used in generation | ✅ NO |
| Gold labels used in scoring | ✅ NO |
| Paid API calls | ✅ 0 |
| `.env` secrets | ✅ No API keys committed |
| LLM provider | ✅ Local Ollama only |

---

## 6. Known Limitations

1. **No human evaluation performed.** Because no human annotator has independently scored the 30-example subset, human-vs-judge agreement cannot currently be established. The reported Cohen's Kappa measures agreement between two automated LLM evaluators and should not be interpreted as human validation.

2. **High real-world fallback rate (69.2%).** On the 500-thread unseen validation set, 69.2% of conversations fell through to the Dense RAG + LLM path, significantly increasing latency (~3–8s vs ~1ms) and compute cost.

3. **Retrieval Recall@3 = 65.31%.** Over a third of generated replies lack relevant grounded context from the retrieval corpus, increasing the risk of hallucination and generic responses.

4. **Hallucination rate of 4.59% (likely an undercount).** The Judge's self-reported hallucination rate is 4.59%, but the Independent LLM Scorer flagged additional cases the Judge missed (e.g., GS-107, GS-028, GS-056). Without human validation, the true hallucination rate is unknown.

5. **LLM Judge unreliability.** The Judge and Independent Scorer show negative Kappa on Groundedness (−0.098) and Helpfulness (−0.058), meaning the Judge's individual-example rankings are worse than random chance when compared to a stricter automated evaluator.

6. **Same-model bias.** Both automated evaluators use the same 3B Llama 3.2 model. Shared blind spots (e.g., inability to detect subtle factual errors) are invisible in automated-only evaluation.

7. **Language mismatch.** Non-English conversations (e.g., German) receive English replies.

---

## 7. Failure Modes

| Mode | Frequency | Severity |
|------|-----------|----------|
| Hallucinated tracking/order details | 4.59% (likely undercount) | Critical |
| Off-topic response (misses latest message) | ~15% (estimated from scorer disagreements) | High |
| Assumed policies without grounding | ~10% | Medium |
| Language mismatch | ~3% | Medium |
| Over-escalation | ~3% | Low |

---

## 8. Deployment Recommendation

> [!CAUTION]
> **The architecture is functionally complete but NOT production-ready.**

**What works well:**
- Intent classification achieves 100% accuracy on the Golden Set with Macro F1 = 1.000
- The Rule → TF-IDF → Dense RAG → LLM routing cascade correctly prioritizes fast, deterministic classification
- Reply tone is consistently professional (automated Tone score: 4.97–5.00/5.0)
- Zero data leakage between Golden Set and retrieval corpus
- Fully local, free inference with no paid API dependencies

**What blocks production deployment:**
- **69.2% real-world fallback rate** makes the system latency- and compute-expensive
- **65.31% retrieval Recall@3** leaves 35% of generations ungrounded
- **4.59% hallucination rate** (likely an undercount) is unacceptable for customer-facing use
- **No genuine human evaluation** has been performed to calibrate quality metrics
- **LLM Judge is unreliable** — it cannot be used as an automated quality gate

**Recommended next steps (in priority order):**
1. Obtain genuine human evaluation of the 30-example subset
2. Improve retrieval recall via embedding fine-tuning (e.g., MNRL on training data) or hybrid retrieval
3. Add explicit grounding constraints and negative examples to the generation prompt
4. Use a more capable judge model or implement rule-based hallucination detection
5. Re-evaluate with human scoring after improvements

---

## 9. Artifacts

| File | Description |
|------|-------------|
| [generated_replies.json](file:///Users/pratikskanoj/ThreadMind/reports/generated_replies.json) | 196 generated replies with routing metadata |
| [judge_evaluation_results.json](file:///Users/pratikskanoj/ThreadMind/reports/judge_evaluation_results.json) | Full LLM-as-Judge scores (N=196) |
| [llm_independent_scoring_subset.csv](file:///Users/pratikskanoj/ThreadMind/reports/llm_independent_scoring_subset.csv) | 30-example Independent LLM Scorer results |
| [llm_independent_scoring_details.json](file:///Users/pratikskanoj/ThreadMind/reports/llm_independent_scoring_details.json) | Per-example reasoning from Independent Scorer |
| [human_scoring_subset.csv](file:///Users/pratikskanoj/ThreadMind/reports/human_scoring_subset.csv) | 30-example CSV (contains automated scores; human scoring PENDING) |
| [human_scoring_instructions.md](file:///Users/pratikskanoj/ThreadMind/reports/human_scoring_instructions.md) | Rubric for future human annotators |
| [phase4_completion_report.md](file:///Users/pratikskanoj/ThreadMind/reports/phase4_completion_report.md) | Detailed Phase 4 evaluation report |
