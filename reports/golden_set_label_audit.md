# Golden Set Label Integrity Audit

- **Total Examples Audited**: 196
- **Suspicious Examples**: 11
- **Semantic Ambiguity Count**: 11
- **Context-Dependent Count**: 44
- **Intent Conflict Count**: 11

## Structural Complexity
- simple: 156
- incomplete: 40

## Escalation Evidence Distribution
- no_escalation: 190
- human_review_recommended: 6

## Suspicious Examples Analysis
### GS-021 (Thread: `1e9fb1462c55081f`)
- Assigned Intent: `delivery_missing`
- Reasons:
  - Multiple confusable intents detected: [{'delivery_delayed', 'delivery_missing'}]
### GS-026 (Thread: `0d7053cbb502d63a`)
- Assigned Intent: `delivery_missing`
- Reasons:
  - Multiple confusable intents detected: [{'account_billing', 'returns_refunds'}]
### GS-035 (Thread: `df577fc749f849fc`)
- Assigned Intent: `delivery_wrong_item`
- Reasons:
  - Multiple confusable intents detected: [{'account_access', 'account_billing'}]
### GS-040 (Thread: `62c4d90a25d0f418`)
- Assigned Intent: `delivery_wrong_item`
- Reasons:
  - Multiple confusable intents detected: [{'delivery_delayed', 'delivery_missing'}]
### GS-045 (Thread: `7537e113f152e797`)
- Assigned Intent: `returns_refunds`
- Reasons:
  - Multiple confusable intents detected: [{'account_billing', 'returns_refunds'}]
### GS-046 (Thread: `9cae32f77fa87a38`)
- Assigned Intent: `returns_refunds`
- Reasons:
  - Multiple confusable intents detected: [{'account_billing', 'returns_refunds'}]
### GS-048 (Thread: `acbce372aa4fd05c`)
- Assigned Intent: `returns_refunds`
- Reasons:
  - Multiple confusable intents detected: [{'account_billing', 'returns_refunds'}]
### GS-052 (Thread: `f7b90627ea18d8f6`)
- Assigned Intent: `returns_refunds`
- Reasons:
  - Multiple confusable intents detected: [{'account_billing', 'returns_refunds'}]
### GS-053 (Thread: `5b8bf1ab06aa0f1a`)
- Assigned Intent: `returns_refunds`
- Reasons:
  - Multiple confusable intents detected: [{'account_billing', 'returns_refunds'}]
### GS-066 (Thread: `d6cf59dcf89bf508`)
- Assigned Intent: `account_billing`
- Reasons:
  - Multiple confusable intents detected: [{'account_access', 'account_billing'}]
### GS-153 (Thread: `5d58b0bdefae1299`)
- Assigned Intent: `promotions_pricing`
- Reasons:
  - Multiple confusable intents detected: [{'product_availability', 'promotions_pricing'}]
