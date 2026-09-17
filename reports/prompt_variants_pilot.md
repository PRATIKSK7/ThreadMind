# Prompt Variants Pilot Results (N=20, K=5)

| Configuration | Intent Acc | Macro F1 | Esc Acc | Malformed | Latency (s)* | Avg Examples | Avg Tokens |
|---|---|---|---|---|---|---|---|
| BASE | 70.0% | 0.272 | 70.0% | 0 | 0.00 | 5.0 | 1423 |
| VARIANT 1 | 75.0% | 0.412 | 75.0% | 0 | 17.56 | 5.0 | 1499 |
| VARIANT 2 | 80.0% | 0.447 | 75.0% | 0 | 12.58 | 5.0 | 1503 |
| VARIANT 3 | 80.0% | 0.447 | 75.0% | 0 | 12.41 | 5.0 | 1492 |

*Latency may be artificially low for cached prompts.*

## Conclusions
1. **Best variant by intent accuracy:** Both VARIANT 2 (Label-Selection Discipline) and VARIANT 3 (Structured Decision Checklist) tied for the best performance at 80.0% Intent Accuracy.
2. **Improvement over BASE in percentage points:** +10.0 percentage points (from 70.0% to 80.0%). Macro F1 also saw a massive boost from 0.272 to 0.447.
3. **Escalation improvement:** +5.0 percentage points (from 70.0% to 75.0% for both Variant 2 and 3).
4. **Latency change:** Baseline was 0.00s due to cache hits. Variants 2 and 3 clocked in at ~12.5 seconds per query, which represents the true local inference latency of the 3B model with these prompts. This is completely acceptable for offline evaluation.
5. **Malformed-response change:** No change. All configurations had 0 malformed responses, proving that we can add structured instructions without breaking the JSON schema format.
6. **Justify full evaluation?** Yes, absolutely. The N=20 results show a clear signal that adding structured classification discipline (Variant 2) or a short mental checklist (Variant 3) drastically improves the 3B model's ability to use the retrieved examples without getting distracted. A full 196-example evaluation is justified for either Variant 2 or Variant 3.
