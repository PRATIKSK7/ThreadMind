# Phase 15A — V2 Confidence Diagnosis

## 1. Retrieved Intent Distribution
| Distribution | Count | V2 Accuracy |
|---|---:|---:|
| unanimous | 130 | 90.8% |
| 2_vs_1 | 49 | 79.6% |
| all_different | 17 | 88.2% |

## 2. V2 Prediction Stability (Retrieval Agreement)
| Signal | Count | V2 Accuracy | False Positive Risk | False Negative Risk |
|---|---:|---:|---|---|
| V2 Prediction MATCHES a retrieved candidate | 147 | 99.3% | Low (V2 is very reliable when it agrees with RAG) | High (If we force fallback, we risk V3/V4 regression) |
| V2 Prediction is ABSENT from retrieval | 49 | 53.1% | High (V2 is guessing blindly against RAG) | Low (V2 is usually wrong here) |

## 3. Score Information
The FAISS index (using `IndexFlatIP`) outputs Inner Product scores (cosine similarity). These scores are available *before* classification and strongly correlate with semantic similarity. However, intent distribution (unanimous vs mixed) is a much stronger and safer gate than raw float scores, because semantic scores vary widely across different intents.

## 4. Proposed Confidence Gate (Targeted Fallback)
Instead of replacing V2 entirely, we can implement an Evidence Gate:
1. Run dense retrieval (K=3).
2. If retrieval is **Unanimous** AND V2's predicted intent is **not** that unanimous intent -> TRIGGER FALLBACK (V2 over-correction).
3. If retrieval is **Conflicting** -> TRIGGER FALLBACK (V2 struggles with conflicts).
4. Otherwise, trust V2.

Alternatively, a simpler semantic gate:
**GATE: If `V2_predicted_intent` is NOT IN `retrieved_intents`, trigger fallback.**
Looking at the data, when V2 predicts an intent that wasn't even in the top-3, it is accurate only 53.1% of the time. This isolates the exact cases where V2 is "going rogue" (CLASSIFIER_IGNORED_CORRECT).

## 5. Estimated Coverage of Fallback
If we fallback whenever V2 prediction is absent from retrieval, we would intercept 49 queries out of 196 (25.0%).
If we fallback on ALL conflicting evidence, we would intercept a larger chunk.

## 6. Examples
**Trigger Fallback (V2 prediction absent from retrieval):**
- `136747dbfd949f68`: V2 predicted `other_support`. Retrieved: `['delivery_delayed', 'returns_refunds', 'delivery_delayed']`.
- `9d4ee10b51d6518c`: V2 predicted `amazon_locker`. Retrieved: `['delivery_missing', 'delivery_missing', 'delivery_missing']`.

**Remain Untouched (V2 prediction matches retrieval):**
- `d3a37c0eb6a2e1af`: V2 predicted `delivery_delayed`. Retrieved: `['delivery_delayed', 'delivery_delayed', 'delivery_delayed']`.
- `6128774c272909e7`: V2 predicted `delivery_delayed`. Retrieved: `['delivery_delayed', 'delivery_delayed', 'delivery_delayed']`.

## 7. Recommendation
**READY**
The existing system surfaces enough information (top-3 intent strings and cosine similarity scores) to build a robust heuristic evidence gate *before* finalizing the response. We can wrap V2 with a rule-based arbiter that triggers a specialized fallback prompt only when V2 exhibits known failure patterns.
