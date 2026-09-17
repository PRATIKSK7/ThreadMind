# Phase 4 — V2 Baseline Evaluation

## Objective
Re-evaluate the existing MNRL RAG model against the repaired Golden Set V2 to establish an honest post-repair baseline, isolating model performance from benchmark labeling errors.

## Benchmark Integrity
- **Golden Set Hash**: 6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f
- **Size**: 196 examples
- **Status**: V2 Repaired (14 label corrections)
- **Integrity**: Passed, no conversation text or model configuration modified.

## V2 Results

| K | Intent Accuracy | Macro F1 | Escalation Accuracy | Recall | MRR@3 |
|---|---:|---:|---:|---:|---:|
| 1 | 48.47% | 0.4624 | 59.69% | 72.45% | 0.7245 |
| 3 | 59.18% | 0.5443 | 66.33% | 84.18% | 0.7772 |
| 5 | 60.71% | 0.5550 | 68.88% | 85.71% | 0.7772 |

## V1 vs V2

| Metric | V1 | V2 | Delta |
|---|---:|---:|---:|
| Intent Accuracy (K=5) | 58.67% | 60.71% | +2.04% |
| Macro F1 (K=5) | 0.5419 | 0.5550 | +0.0131 |
| Escalation Accuracy (K=5) | 68.88% | 68.88% | 0.00% |
| Recall@5 | 86.73% | 85.71% | -1.02% |

The V1→V2 improvement in accuracy reflects mathematically the correction of the benchmark labels. Because the retriever corpus still uses V1 uncorrected labels, Recall@5 slightly decreased. 

## Retrieval Performance
Retrieval performance peaked at K=5 with 85.71% Recall. This means 28 examples (14.29%) failed to retrieve the necessary context.

## Classification Performance
End-to-end intent classification at K=5 reached 60.71%. The gap between what is retrieved (85.71%) and what is correctly classified (60.71%) is the classification gap. 

## Escalation Performance
Escalation accuracy (68.88%) remains somewhat decoupled from intent accuracy, likely because escalation can often be safely predicted from conversation tone (e.g., frustration) regardless of the exact logistical issue.

## Error Distribution
- **Classification Bottlenecks**: 49 failures (LLM misclassifies despite correct context).
- **Retrieval Bottlenecks**: 28 failures (Retriever fails to fetch correct context).

## Top Failure Modes
1. `account_access` vs `delivery_wrong_item` (5 failures)
2. `amazon_locker` vs `delivery_missing` (5 failures)
3. `account_access` vs `delivery_delayed` (4 failures)

## Interpretation
Even with a cleanly labeled Golden Set, classification remains the dominant bottleneck (49 vs 28). The LLM is failing to appropriately reason over the provided context, often confusing digital account access with logistical failures. 

## Recommended Phase 5
**Phase 5 = Classifier/Prompt Reasoning Improvement**
Because classification failures represent the largest measurable bottleneck, optimizing the LLM prompt, its reasoning structure, or few-shot example diversity should yield the highest end-to-end impact. 
