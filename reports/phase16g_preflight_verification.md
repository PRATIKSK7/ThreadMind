# Phase 16G — Pre-flight Verification

- **Current Best**: V2
- **Golden Set Status**: UNCHANGED
- **Production Status**: UNCHANGED
- **Human Review Status**: SIMULATED
- **Simulated Decisions**: 24
- **Real Decisions**: 0

## Verified 24 Suspicious Cases
### GS-009
- Current Label: `returns_refunds`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['delivery_delayed', 'returns_refunds', 'delivery_delayed']
- Boundary: `other_support ↔ returns_refunds`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-017
- Current Label: `delivery_missing`
- V2 Prediction: `amazon_locker`
- Top-3 Retrieved: ['delivery_missing', 'delivery_missing', 'delivery_missing']
- Boundary: `amazon_locker ↔ delivery_missing`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-027
- Current Label: `delivery_missing`
- V2 Prediction: `amazon_locker`
- Top-3 Retrieved: ['delivery_missing', 'delivery_missing', 'delivery_missing']
- Boundary: `amazon_locker ↔ delivery_missing`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-057
- Current Label: `account_billing`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['account_billing', 'account_billing', 'account_billing']
- Boundary: `account_billing ↔ other_support`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-064
- Current Label: `account_billing`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['account_billing', 'account_billing', 'account_billing']
- Boundary: `account_billing ↔ other_support`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-077
- Current Label: `digital_prime_video`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['digital_prime_video', 'digital_prime_video', 'digital_prime_video']
- Boundary: `digital_prime_video ↔ other_support`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-084
- Current Label: `digital_kindle`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['delivery_delayed', 'delivery_delayed', 'delivery_delayed']
- Boundary: `digital_kindle ↔ other_support`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-086
- Current Label: `digital_kindle`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['account_billing', 'account_billing', 'account_billing']
- Boundary: `digital_kindle ↔ other_support`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-096
- Current Label: `digital_kindle`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['digital_kindle', 'digital_kindle', 'digital_kindle']
- Boundary: `digital_kindle ↔ other_support`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-122
- Current Label: `echo_alexa`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['echo_alexa', 'delivery_delayed', 'echo_alexa']
- Boundary: `echo_alexa ↔ other_support`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-123
- Current Label: `echo_alexa`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['echo_alexa', 'echo_alexa', 'amazon_music']
- Boundary: `echo_alexa ↔ other_support`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-124
- Current Label: `echo_alexa`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['product_availability', 'account_access', 'echo_alexa']
- Boundary: `echo_alexa ↔ other_support`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-128
- Current Label: `account_access`
- V2 Prediction: `delivery_wrong_item`
- Top-3 Retrieved: ['account_access', 'delivery_delayed', 'account_access']
- Boundary: `account_access ↔ delivery_wrong_item`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-139
- Current Label: `account_access`
- V2 Prediction: `delivery_wrong_item`
- Top-3 Retrieved: ['account_access', 'account_access', 'account_access']
- Boundary: `account_access ↔ delivery_wrong_item`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-141
- Current Label: `promotions_pricing`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['delivery_delayed', 'promotions_pricing', 'promotions_pricing']
- Boundary: `other_support ↔ promotions_pricing`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-144
- Current Label: `promotions_pricing`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['promotions_pricing', 'delivery_missing', 'delivery_missing']
- Boundary: `other_support ↔ promotions_pricing`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-150
- Current Label: `promotions_pricing`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['promotions_pricing', 'promotions_pricing', 'promotions_pricing']
- Boundary: `other_support ↔ promotions_pricing`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-159
- Current Label: `delivery_missing`
- V2 Prediction: `amazon_locker`
- Top-3 Retrieved: ['delivery_missing', 'amazon_locker', 'amazon_locker']
- Boundary: `amazon_locker ↔ delivery_missing`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-164
- Current Label: `amazon_locker`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['amazon_locker', 'delivery_missing', 'delivery_delayed']
- Boundary: `amazon_locker ↔ other_support`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-174
- Current Label: `grocery_fresh`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['delivery_delayed', 'delivery_missing', 'delivery_delayed']
- Boundary: `grocery_fresh ↔ other_support`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-178
- Current Label: `grocery_fresh`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['delivery_missing', 'delivery_delayed', 'delivery_delayed']
- Boundary: `grocery_fresh ↔ other_support`
- Decision: `CHANGE_LABEL` (Source: SIMULATED_LLM)

### GS-182
- Current Label: `product_availability`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['product_availability', 'product_availability', 'product_availability']
- Boundary: `other_support ↔ product_availability`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-186
- Current Label: `product_availability`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['account_billing', 'account_billing', 'amazon_music']
- Boundary: `other_support ↔ product_availability`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

### GS-189
- Current Label: `product_availability`
- V2 Prediction: `other_support`
- Top-3 Retrieved: ['product_availability', 'product_availability', 'product_availability']
- Boundary: `other_support ↔ product_availability`
- Decision: `TAXONOMY_RULE_NEEDED` (Source: SIMULATED_LLM)

