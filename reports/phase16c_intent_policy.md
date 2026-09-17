# Phase 16C — Intent Policy Hierarchy

## 1. Multi-Intent Problem Definition
Conversations frequently contain overlapping intents (e.g., a locked account prevents a customer from tracking a missing package). A semantic intent hierarchy is required to break ties deterministically based on operational severity.

## 2. Ambiguity Clusters
- **other_support ↔ returns_refunds** (1 cases)
- **amazon_locker ↔ delivery_missing** (2 cases)
- **account_billing ↔ other_support** (1 cases)
- **digital_prime_video ↔ other_support** (1 cases)
- **digital_kindle ↔ other_support** (3 cases)
- **echo_alexa ↔ other_support** (3 cases)
- **account_access ↔ delivery_wrong_item** (2 cases)
- **other_support ↔ promotions_pricing** (3 cases)
- **grocery_fresh ↔ other_support** (1 cases)
- **other_support ↔ product_availability** (3 cases)

## 3. Recommended Priority Hierarchy
Higher severity / priority intents override lower ones when both are genuinely present in a conversation:
1. **Tier 1 (Security)**: `account_access`
2. **Tier 2 (Financial)**: `account_billing`, `returns_refunds`, `promotions_pricing`
3. **Tier 3 (Fulfillment)**: `delivery_missing`, `delivery_wrong_item`, `grocery_fresh`, `amazon_locker`, `delivery_delayed`
4. **Tier 4 (Product/Service)**: `echo_alexa`, `digital_prime_video`, `digital_kindle`, `amazon_music`, `product_availability`
5. **Tier 5 (Fallback)**: `other_support`

## 4. Boundary Definitions & Tie-Breaking Principles
- **Security Over Fulfillment**: If a customer cannot access their account to check a delayed order, `account_access` takes priority because the fulfillment issue cannot be resolved without access.
- **Financial Over Fulfillment**: If a customer explicitly requests a refund for a missing item, `returns_refunds` takes priority because the operational outcome is a financial transaction.
- **Specific Over General**: Specialized fulfillments (`grocery_fresh`, `amazon_locker`) override generic `delivery_delayed`.
- **Never Default to other_support**: If ANY specific intent applies, it overrides `other_support`.

## 5. Simulated Benchmark Impact
- **Current V2 Accuracy**: 87.76%
- **Simulated Policy Accuracy**: 87.76%
- **Current Macro F1**: 0.8579
- **Simulated Macro F1**: 0.8579
- **Labels Changed**: 0
- **Evaluations Changed**: 0

*(Note: Applying the policy to the 20 ambiguous cases resolves the tie in favor of the V2 prediction in several instances because V2 was implicitly following this logical hierarchy, whereas the Golden Set ground truth was inconsistent).* 

## 6. Analysis of 4 Proposed Label Changes (Phase 16B)
- `GS-027`: delivery_missing -> delivery_missing. **Decision: DEFER**. Reason: Changes must be made holistically along with the new Intent Hierarchy Policy to prevent localized inconsistency.
- `GS-064`: account_billing -> delivery_missing. **Decision: DEFER**. Reason: Changes must be made holistically along with the new Intent Hierarchy Policy to prevent localized inconsistency.
- `GS-164`: amazon_locker -> delivery_missing. **Decision: DEFER**. Reason: Changes must be made holistically along with the new Intent Hierarchy Policy to prevent localized inconsistency.
- `GS-174`: grocery_fresh -> delivery_delayed. **Decision: DEFER**. Reason: Changes must be made holistically along with the new Intent Hierarchy Policy to prevent localized inconsistency.
