# Step 7: RAG Error Analysis and Quality Evaluation

## 1. Overall Performance
- Total Examples: 196
- Correct Intent Predictions: 86 (43.88%)
- Incorrect Intent Predictions: 110 (56.12%)
- Correct Escalation Predictions: 128 (65.31%)

## 2. Intent Confusion Matrix (K=3)
Row = True Intent, Column = Predicted Intent

```
[[ 8  4  0  1  0  0  0  0  0  0  0  0  0  0  1]
 [ 3  8  2  1  0  0  0  0  0  0  0  0  0  0  0]
 [ 2  2  3  0  0  1  0  5  0  0  0  0  0  0  1]
 [ 1  3  0  7  0  1  0  2  0  0  0  0  0  0  0]
 [ 1  3  0  0  7  1  1  1  0  0  0  0  0  0  0]
 [ 1  1  0  1  2  5  1  0  1  0  0  0  0  0  2]
 [ 0  2  0  0  0  3  7  0  0  0  0  0  0  0  1]
 [ 0  2  0  0  1  0  1 10  0  0  0  0  0  0  0]
 [ 0  1  0  0  1  1  0  0  9  0  0  1  0  0  1]
 [ 0  2  1  0  0  2  0  2  0  5  0  1  0  0  1]
 [ 0  0  0  1  1  1  0  2  1  0  5  3  0  0  0]
 [ 1  0  0  0  1  1  0  1  2  0  0  8  0  0  0]
 [ 2  5  0  0  1  0  0  5  0  0  0  0  1  0  0]
 [ 1  4  0  0  2  3  0  0  0  0  0  0  0  3  1]
 [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]]
```

## 3. Per-Intent Accuracy
| Intent | Accuracy | Correct / Total |
|--------|----------|-----------------|
| delivery_delayed | 57.14% | 8/14 |
| delivery_missing | 57.14% | 8/14 |
| delivery_wrong_item | 21.43% | 3/14 |
| returns_refunds | 50.00% | 7/14 |
| product_availability | 50.00% | 7/14 |
| promotions_pricing | 35.71% | 5/14 |
| account_billing | 50.00% | 7/14 |
| account_access | 71.43% | 10/14 |
| digital_prime_video | 64.29% | 9/14 |
| digital_kindle | 35.71% | 5/14 |
| amazon_music | 35.71% | 5/14 |
| echo_alexa | 57.14% | 8/14 |
| amazon_locker | 7.14% | 1/14 |
| grocery_fresh | 21.43% | 3/14 |

## 4 & 5 & 6. Subgroup Performance
| Subgroup | Accuracy | Correct / Total |
|----------|----------|-----------------|
| turns_1_2 | 48.98% | 48/98 |
| turns_3_4 | 41.43% | 29/70 |
| context_dependent | 27.27% | 12/44 |
| turns_5_plus | 32.14% | 9/28 |
| semantic_ambiguity | 54.55% | 6/11 |

## 7 & 8. RAG vs Zero-Shot Baseline (Llama 3.2 3B)
- **RAG Helped (Zero-Shot Failed, RAG Correct)**: 33 cases
- **RAG Hurt (Zero-Shot Correct, RAG Failed)**: 9 cases
- **Both Failed**: 101 cases
- **Both Correct**: 53 cases

### Cases Where RAG Helped (Sample of 3)
- Thread `d3a37c0eb6a2e1af`: Zero-Shot predicted `product_availability`, RAG correctly predicted `delivery_delayed`
- Thread `e5e227f6392f6343`: Zero-Shot predicted `returns_refunds`, RAG correctly predicted `delivery_delayed`
- Thread `979bcf1ba7572381`: Zero-Shot predicted `delivery_wrong_item`, RAG correctly predicted `delivery_missing`

### Cases Where RAG Hurt (Sample of 3)
- Thread `6211a9e0735ee03b`: Zero-Shot correctly predicted `delivery_delayed`, RAG mistakenly predicted `delivery_missing`
- Thread `1d34fe17e6385fba`: Zero-Shot correctly predicted `delivery_delayed`, RAG mistakenly predicted `delivery_missing`
- Thread `c329621fdd6a6860`: Zero-Shot correctly predicted `delivery_delayed`, RAG mistakenly predicted `delivery_missing`

## 9. Retrieval Quality Impact
When RAG 'hurts', it is typically because the TF-IDF retriever retrieves examples that share high lexical overlap (e.g. 'refund' and 'account') but actually map to different root causes, thereby forcing the 3B model to output the wrong class.

## 10. Escalation Prediction Errors
Row = True, Column = Predicted (Order: no_escalation, clarification_needed, human_review_recommended)
```
[[125  27  38]
 [  0   0   0]
 [  2   1   3]]
```

## 11. Representative Failures
**Failure Case `66b6dfde5ea6a023`**
- **Expected**: `delivery_delayed`
- **RAG Predicted**: `other_support`
- **Why it failed**: The intent is structurally complex or ambiguous, and the retrieved few-shot examples did not resolve the ambiguity, causing the model to guess randomly or stick to its zero-shot bias.

## 12. Error Categories
1. **Lexical Hijacking**: The retriever pulls examples based on exact word matches that correspond to a different intent, misleading the small parameter model.
2. **Context Bloat**: A 3B parameter model struggles to process 5-shot contexts efficiently, causing reasoning decay.
3. **Compound Intent Failure**: Threads with multiple intents (e.g., late delivery -> refund) still confuse the LLM, despite rules dictating the root cause.

## 13. Recommendations for Next Improvement
Based on the data, the local 3B model is too small to reason reliably across complex RAG contexts, peaking at 43.88% accuracy, which is vastly inferior to the Rule Baseline (98.98%).

**Recommendations**:
1. **Switch to Dense Retrieval**: Replace TF-IDF with a lightweight sentence embedding model (e.g., `all-MiniLM-L6-v2`) to capture semantic intent rather than lexical overlap.
2. **Implement a Fallback Router**: Route high-confidence queries to the Rule Baseline, and only use RAG for queries that the rules abstain on or have low confidence.
3. **Instruction Fine-Tuning**: If the model must remain at 3B parameters running locally, RAG is insufficient. The model should be instruction-tuned (LoRA) on the golden rules.
