# Retrieval Diagnosis

Total Queries: 196
Failures (not in Top-5): 28

## Intent-Level Metrics
| Intent | Golden Count | Recall@1 | Recall@3 | Recall@5 | Failures |
|--------|--------------|----------|----------|----------|----------|
| delivery_delayed | 12 | 100.00% | 100.00% | 100.00% | 0 |
| returns_refunds | 16 | 56.25% | 93.75% | 100.00% | 0 |
| delivery_missing | 15 | 93.33% | 100.00% | 100.00% | 0 |
| delivery_wrong_item | 7 | 28.57% | 57.14% | 57.14% | 3 |
| account_access | 21 | 61.90% | 76.19% | 76.19% | 5 |
| account_billing | 14 | 78.57% | 92.86% | 92.86% | 1 |
| digital_prime_video | 14 | 92.86% | 100.00% | 100.00% | 0 |
| digital_kindle | 14 | 78.57% | 78.57% | 85.71% | 2 |
| amazon_music | 14 | 92.86% | 92.86% | 92.86% | 1 |
| echo_alexa | 14 | 78.57% | 92.86% | 92.86% | 1 |
| promotions_pricing | 14 | 64.29% | 85.71% | 85.71% | 2 |
| amazon_locker | 13 | 76.92% | 84.62% | 84.62% | 2 |
| grocery_fresh | 14 | 28.57% | 35.71% | 42.86% | 8 |
| product_availability | 14 | 71.43% | 78.57% | 78.57% | 3 |

## Failure Types
- SEMANTIC_RETRIEVAL_FAILURE: 16
- INTENT_BOUNDARY_FAILURE: 8
- LABEL_FAILURE: 4

## Top Confusions
- account_access <-> delivery_wrong_item: 13
- account_access <-> delivery_missing: 11
- grocery_fresh <-> returns_refunds: 11
- account_billing <-> grocery_fresh: 9
- account_access <-> delivery_delayed: 7
- amazon_locker <-> digital_kindle: 6
- echo_alexa <-> product_availability: 6
- product_availability <-> promotions_pricing: 6
- delivery_delayed <-> digital_kindle: 5
- promotions_pricing <-> returns_refunds: 5

## Representation Audit
Both queries and corpus documents use identical role formatting `User: ... 
 Agent: ...`.
No mismatch in text truncation was observed.

## Dominant Root Cause
INTENT_BOUNDARY_FAILURE / SEMANTIC_RETRIEVAL_FAILURE

## Next Intervention
RECOMMENDATION: IMPLEMENT HARD NEGATIVE MINING & CONTRASTIVE FINE-TUNING FOR MNRL MODEL ON BOUNDARY CONFUSIONS.
