# Phase 15B — Targeted V5 Fallback Results

## 1. Top-Level Comparison
- **V2 BASELINE**: 87.76%
- **V5 FALLBACK (Intercepted Only)**: 26.53%
- **GATED SYSTEM**: 81.12%

- **IMPROVEMENTS**: 11
- **REGRESSIONS**: 24
- **UNCHANGED**: 14
- **NET**: -13
- **MACRO F1**: 0.8054
- **ESCALATION**: 77.04%

## 2. Gating Safety (Control Group)
The V5 fallback was also run in isolation on the 147 control cases where V2 matched the retrieved evidence. V5 achieved 19.73% accuracy on this control group. (Note: These cases were NOT overridden in the Gated System). This proves the necessity of the gate: V5 alone would have regressed the stable baseline.

## 3. Targeted Impact
For the 25 intercepted cases:
- `[IMPROVEMENT]` 136747dbfd949f68 (CONFLICTING_EVIDENCE): V2 `other_support` -> V5 `returns_refunds`. Expected: `returns_refunds`
- `[IMPROVEMENT]` 9d4ee10b51d6518c (CLASSIFIER_IGNORED_CORRECT): V2 `amazon_locker` -> V5 `delivery_missing`. Expected: `delivery_missing`
- `[IMPROVEMENT]` 2555a8d9872a2f15 (CLASSIFIER_IGNORED_CORRECT): V2 `amazon_locker` -> V5 `delivery_missing`. Expected: `delivery_missing`
- `[REGRESSION]` 971d58ab9348de04 (CORRECT_V2): V2 `account_access` -> V5 `delivery_delayed`. Expected: `account_access`
- `[REGRESSION]` 80daedda83f344bd (CORRECT_V2): V2 `account_access` -> V5 `delivery_wrong_item`. Expected: `account_access`
- `[REGRESSION]` 04f0d488a16c8b29 (CORRECT_V2): V2 `account_access` -> V5 `delivery_missing`. Expected: `account_access`
- `[REGRESSION]` 62c4d90a25d0f418 (CORRECT_V2): V2 `account_access` -> V5 `delivery_missing`. Expected: `account_access`
- `[REGRESSION]` 583e80a133042b71 (CORRECT_V2): V2 `returns_refunds` -> V5 `delivery_delayed`. Expected: `returns_refunds`
- `[IMPROVEMENT]` 548c4f7b87a573e3 (CLASSIFIER_IGNORED_CORRECT): V2 `other_support` -> V5 `account_billing`. Expected: `account_billing`
- `[REGRESSION]` d6cf59dcf89bf508 (CORRECT_V2): V2 `account_billing` -> V5 `account_access`. Expected: `account_billing`
- `[IMPROVEMENT]` e6aef6c530ba4876 (CLASSIFIER_IGNORED_CORRECT): V2 `other_support` -> V5 `digital_prime_video`. Expected: `digital_prime_video`
- `[IMPROVEMENT]` e0e2bacc798bff2b (RETRIEVAL_MISSING): V2 `other_support` -> V5 `digital_kindle`. Expected: `digital_kindle`
- `[REGRESSION]` 39c418bf1848d060 (CORRECT_V2): V2 `digital_kindle` -> V5 `account_access`. Expected: `digital_kindle`
- `[REGRESSION]` a6dbcc41eea15111 (CORRECT_V2): V2 `amazon_music` -> V5 `delivery_missing`. Expected: `amazon_music`
- `[IMPROVEMENT]` 4c2ba68f8d6d8d01 (CONFLICTING_EVIDENCE): V2 `other_support` -> V5 `echo_alexa`. Expected: `echo_alexa`
- `[IMPROVEMENT]` 59b64538302cb337 (CONFLICTING_EVIDENCE): V2 `other_support` -> V5 `echo_alexa`. Expected: `echo_alexa`
- `[REGRESSION]` 1dcf6340ae04e307 (CORRECT_V2): V2 `echo_alexa` -> V5 `delivery_delayed`. Expected: `echo_alexa`
- `[REGRESSION]` f96b9b10c4206c30 (CORRECT_V2): V2 `delivery_wrong_item` -> V5 `account_access`. Expected: `delivery_wrong_item`
- `[REGRESSION]` b916108101eca175 (CORRECT_V2): V2 `delivery_wrong_item` -> V5 `account_access`. Expected: `delivery_wrong_item`
- `[IMPROVEMENT]` 7e10f8a5300df65c (CLASSIFIER_IGNORED_CORRECT): V2 `delivery_wrong_item` -> V5 `account_access`. Expected: `account_access`
- `[IMPROVEMENT]` 507a5d959193bd85 (CONFLICTING_EVIDENCE): V2 `other_support` -> V5 `promotions_pricing`. Expected: `promotions_pricing`
- `[REGRESSION]` 663015f372cd3b8a (CORRECT_V2): V2 `promotions_pricing` -> V5 `product_availability`. Expected: `promotions_pricing`
- `[IMPROVEMENT]` a3b31228d3f292c5 (CLASSIFIER_IGNORED_CORRECT): V2 `other_support` -> V5 `promotions_pricing`. Expected: `promotions_pricing`
- `[REGRESSION]` 5d58b0bdefae1299 (CORRECT_V2): V2 `promotions_pricing` -> V5 `delivery_delayed`. Expected: `promotions_pricing`
- `[REGRESSION]` 1df63ea1d5a69936 (CORRECT_V2): V2 `amazon_locker` -> V5 `delivery_missing`. Expected: `amazon_locker`
- `[REGRESSION]` baa82fe4c3c04a25 (CORRECT_V2): V2 `amazon_locker` -> V5 `delivery_delayed`. Expected: `amazon_locker`
- `[REGRESSION]` 9d048a20fd47ab7f (CORRECT_V2): V2 `grocery_fresh` -> V5 `account_access`. Expected: `grocery_fresh`
- `[REGRESSION]` 4659bf7cb80e967a (CORRECT_V2): V2 `grocery_fresh` -> V5 `account_billing`. Expected: `grocery_fresh`
- `[REGRESSION]` 3f38d0690064ea3e (CORRECT_V2): V2 `grocery_fresh` -> V5 `account_access`. Expected: `grocery_fresh`
- `[REGRESSION]` 16cfcf62900ef5ea (CORRECT_V2): V2 `grocery_fresh` -> V5 `digital_kindle`. Expected: `grocery_fresh`
- `[REGRESSION]` 632f0aed89f71a07 (CORRECT_V2): V2 `grocery_fresh` -> V5 `delivery_missing`. Expected: `grocery_fresh`
- `[REGRESSION]` 51a322d37e9a7679 (CORRECT_V2): V2 `grocery_fresh` -> V5 `delivery_wrong_item`. Expected: `grocery_fresh`
- `[REGRESSION]` e84a7e6d5d4a4373 (CORRECT_V2): V2 `grocery_fresh` -> V5 `delivery_wrong_item`. Expected: `grocery_fresh`
- `[REGRESSION]` ebefc67d2ab0c89b (CORRECT_V2): V2 `product_availability` -> V5 `delivery_wrong_item`. Expected: `product_availability`
- `[REGRESSION]` c5f3c1301f833cc0 (CORRECT_V2): V2 `product_availability` -> V5 `promotions_pricing`. Expected: `product_availability`
