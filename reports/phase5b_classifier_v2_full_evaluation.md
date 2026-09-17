# Phase 5B — Full-Scale Classifier V2 Validation

## 1. Executive Summary
The V2 Classifier Reasoning logic was validated on the full 196-example V2 Golden Set across K=1, K=3, and K=5. The V2 prompt successfully resolved the classification bottleneck, demonstrating massive improvements in Intent Accuracy (+19.9% at K=5, up to 87.76% at K=3) without introducing regressions or malformed outputs. K=3 was identified as the optimal retrieval size, as K=5 introduces context dilution.

## 2. Benchmark Integrity
- **Golden Set Examples:** 196 (verified)
- **Golden Set SHA-256:** `6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f`
- **Labels Modified:** False
- **Conversations Modified:** False
- **Escalations Modified:** False
- **Retrieval Corpus Modified:** False
- **MNRL Model Modified:** False
- **Prompt Loaded:** `src/threadmind/llm/prompts/rag_classification_v2.txt` (via `PROMPT_VERSION=v2`)

## 3. Configuration
- **Model:** `llama3.2:latest`
- **Temperature:** 0.0
- **Context Size:** 4096
- **Architecture:** Unchanged MNRL Dense Retriever + LLM Classifier

## 4. K=1 Results
- **Recall@1:** 72.45%
- **Intent Accuracy:** 81.63%
- **Macro F1:** 0.8185
- **Escalation Accuracy:** 100.00%
- **Malformed Outputs:** 0

## 5. K=3 Results
- **Recall@3:** 84.18%
- **Intent Accuracy:** 87.76%
- **Macro F1:** 0.8579
- **Escalation Accuracy:** 100.00%
- **Malformed Outputs:** 0

## 6. K=5 Results
- **Recall@5:** 85.71%
- **Intent Accuracy:** 80.61%
- **Macro F1:** 0.8004
- **Escalation Accuracy:** 100.00%
- **Malformed Outputs:** 0

## 7. V1 vs V2 Comparison (K=5)

| Metric | V1 | V2 | Absolute Delta | Relative Delta |
|---|---:|---:|---:|---:|
| Intent Accuracy | 60.71% | 80.61% | +19.90 pp | +32.77% |
| Macro F1 | 0.5550 | 0.8004 | +0.2454 | +44.21% |
| Escalation Accuracy | 68.88% | 100.00% | +31.12 pp | +45.18% |

*(Note: Maximum performance actually peaked at K=3 for V2, reaching 87.76% accuracy).*

## 8. Confusion Analysis
At K=3 (the optimal parameter), the top remaining confusion pairs are:
1. `amazon_locker` ↔ `delivery_missing` (3 failures)
2. `digital_kindle` ↔ `other_support` (3 failures)
3. `echo_alexa` ↔ `other_support` (3 failures)

**Crucial Finding:** The previously dominant confusion pairs (`account_access` vs `delivery_wrong_item` and `account_access` vs `delivery_delayed`) have been entirely eliminated at K=3 by the V2 reasoning framework.

## 9. Failure Attribution (K=3)
Total Failures: 24
- **Retrieval Bottlenecks (A):** ~15 (Retriever missed the context entirely, and the LLM could not bridge the gap).
- **Classification Bottlenecks (B):** ~9 (LLM misclassified despite correct context, mostly falling back to `other_support`).
- **Malformed-output (D):** 0
- **Ambiguous Taxonomy (E):** Remaining `locker` vs `missing` cases often lack sufficient customer context.

## 10. Latency / Reliability
- **Average Retrieval Latency:** 6.2 ms/query
- **Malformed JSON Count:** 0
- **API Failures:** 0

## 11. K Selection Recommendation
**Recommended K:** 3
**Reasoning:** Intent Accuracy peaks at K=3 (87.76%) and declines at K=5 (80.61%). This indicates **context dilution**: adding the 4th and 5th retrieved examples introduces conflicting taxonomy patterns that confuse the LLM's primary-problem reasoning, overriding the benefits of marginally higher recall (Recall@5 is only 1.5% higher than Recall@3).

## 12. Phase 5B Conclusion
The V2 Classifier Reasoning Policy successfully generalized from the pilot to the full benchmark. It systematically eliminated the most damaging classification bottlenecks without introducing regressions or malformed outputs. 

## 13. Recommended Next Phase
**Phase 6: Retrieval Corpus Re-indexing**
Since classification is now highly accurate (87.76%), the next bottleneck is Retrieval. The existing retrieval corpus still uses the old, un-repaired Golden Set (V1) labels, causing the retriever to fetch mathematically misaligned examples. Rebuilding the dense vector index using the V2 labels is the required next step to push Recall@3 closer to 95%.
