# Golden Set Deterministic Summary

- Total Golden Set examples: 196
- Number flagged: 14
- CLEAR_MISLABEL count: 14
- TAXONOMY_AMBIGUITY count: 0
- MODEL_ERROR count: 70
- Percentage of Golden Set affected: 7.1%

## Count by Intent (Flagged)
- delivery_delayed: 2
- delivery_wrong_item: 9
- account_access: 2
- amazon_locker: 1

## Count by Confusion Pair
- account_access_vs_delivery_wrong_item: 11
- amazon_locker_vs_delivery_missing: 1
- delivery_delayed_vs_returns_refunds: 2

## K=5 Failure Impact
- K=5 failures involving a flagged Golden Set example: 11
- K=5 failures remain genuine model/classification failures: 53
- Retrieval bottlenecks remain: 17
