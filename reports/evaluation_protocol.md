# Evaluation Protocol

This document defines the strict evaluation contract for all baseline models and the final THREADMIND agent.

## Evaluation Dataset
- **Golden Set (`data/processed/golden_set.jsonl`)**: Exactly 196 strictly held-out conversations covering 14 intents. 
- **Isolation Constraint**: Absolutely no Golden Set data may be used for vocabulary fitting, classifier training, or few-shot prompt injection.

## Prediction Schema
Every model evaluated against the Golden Set must output a uniform JSON schema for every conversation:
```json
{
  "example_id": "GS-001",
  "predicted_intent": "delivery_missing",
  "confidence": 0.85,
  "predicted_escalation": "no_escalation",
  "reasoning_summary": "Customer stated tracking shows delivered but they cannot find it.",
  "error": null
}
```
If a model fails to process a conversation, it must output:
```json
{
  "example_id": "GS-001",
  "error": "API Timeout"
}
```

## Metrics
1. **Intent Accuracy**: Overall percentage of examples where `predicted_intent == target_intent`.
2. **Intent Weighted F1**: F1 score weighted by class support to handle minority intents.
3. **Escalation Exact Match**: Accuracy for the three-way `escalation` label.
4. **Abstention Rate**: Percentage of examples where the model outputs `other_support` or fails to predict due to low confidence.
5. **Error Rate**: Percentage of examples that result in a hard failure (e.g. API timeout, regex crash).

## Error Handling
Failed predictions are marked strictly as errors and graded as `0` for accuracy. We do not silently drop failed calls from the denominator.

## Reproducibility
- Randomness is controlled with `SEED = 42`.
- The first run against the Golden Set is considered the frozen baseline. Subsequent prompt/model tuning requires a new experiment ID to prevent unintentional data snooping.
