# Phase 4 — V2 Error Analysis

## Summary Statistics (K=5)
- **Total Intent Failures**: 77
- **Total Escalation Failures**: 61

## Bottleneck Attribution
Based on K=5 metrics:
- **Retrieval Bottlenecks**: 28 examples (14.29%) failed to retrieve the correct intent in the Top 5.
- **Classification Bottlenecks**: 49 examples (25.00%) retrieved the correct intent in the Top 5 but were misclassified by the LLM.

## Top Confusion Pairs
1. `account_access` ↔ `delivery_wrong_item` (5 failures)
2. `amazon_locker` ↔ `delivery_missing` (5 failures)
3. `account_access` ↔ `delivery_delayed` (4 failures)
4. `account_access` ↔ `amazon_locker` (4 failures)
5. `account_access` ↔ `delivery_missing` (3 failures)

Even after Golden Set repairs, the boundaries between logistics issues and digital access remain the leading cause of classification failures. The LLM still struggles to differentiate whether an unauthenticated user checking on a delivery delay constitutes a log-in issue or a delivery issue.

## Distribution Shift Note
The repair of the Golden Set shifted the failure distribution. Because the retrieval corpus was untouched (it still reflects the V1 taxonomy assumptions), 7 of the repaired Golden Set examples now fail to fetch relevant context from the stale corpus, effectively converting what appeared to be "classification failures" into "retrieval failures."
