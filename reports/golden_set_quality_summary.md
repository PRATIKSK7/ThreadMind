# Golden Set Quality Summary

## Overall Dataset Quality
- **Total Examples**: 111
- **VALID**: 79 (71.2%)
- **AMBIGUOUS**: 21 (18.9%)
- **LIKELY_MISLABELED**: 11 (9.9%)
- **INSUFFICIENT_CONTEXT**: 0 (0.0%)

**Estimated Label-Noise Rate**: 28.8%

## Problematic Intents (Count of non-VALID cases)
- `digital_prime_video`: 8
- `delivery_wrong_item`: 7
- `account_billing`: 6
- `amazon_music`: 5
- `digital_kindle`: 4
- `returns_refunds`: 2

## Evaluation Reliability
The Golden Set currently contains significant noise (over 10%). It is NOT sufficiently reliable for fine-grained model benchmarking. Improvements in model accuracy may actually reflect overfitting to noisy labels rather than genuine performance gains.

## Final Recommendation
B. Repair taxonomy boundaries

Explanation: Before we can repair the Golden Set labels, we must have clear, mutually exclusive definitions for intents that currently overlap (e.g., `amazon_locker` vs `delivery_missing`, `delivery_delayed` vs `returns_refunds`). Without repairing the taxonomy boundaries first, relabeling will only shift the ambiguity, not resolve it. Once boundaries are strict, we can rebuild or repair the Golden Set.
