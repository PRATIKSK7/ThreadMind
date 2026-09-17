# Phase 14B — Controlled V3 Classifier Pilot

## 1. Executive Summary
The pilot tested 60 examples. V3 achieved **46.7%** accuracy vs V2's **60.0%**.
V3 improved 11 queries, regressed 19 queries, leaving 30 unchanged.

## 2. Pilot Dataset Composition
- CLASSIFIER_IGNORED_CORRECT: 10
- CONFLICTING_EVIDENCE: 9
- RETRIEVAL_MISSING: 5
- CORRECT_V2: 36

## 3. V2 vs V3 Metrics
| Metric | V2 | V3 |
|---|---:|---:|
| Accuracy | 60.0% | 46.7% |
| Macro F1 | 0.6794 | 0.4677 |

## 4. Targeted Failure-Mode Results
| Category | Total | V2 Accuracy | V3 Accuracy |
|---|---:|---:|---:|
| CLASSIFIER_IGNORED_CORRECT | 10 | 0.0% | 50.0% |
| CONFLICTING_EVIDENCE | 9 | 0.0% | 44.4% |
| RETRIEVAL_MISSING | 5 | 0.0% | 40.0% |
| CORRECT_V2 | 36 | 100.0% | 47.2% |

## 5. Per-Intent Results
| Intent | Total | V2 Correct | V3 Correct |
|---|---:|---:|---:|
| delivery_missing | 6 | 3 | 4 |
| account_billing | 5 | 3 | 3 |
| digital_prime_video | 4 | 3 | 1 |
| digital_kindle | 5 | 2 | 3 |
| account_access | 5 | 3 | 2 |
| promotions_pricing | 6 | 3 | 2 |
| product_availability | 5 | 2 | 3 |
| returns_refunds | 4 | 3 | 1 |
| echo_alexa | 4 | 1 | 2 |
| amazon_locker | 4 | 3 | 1 |
| grocery_fresh | 5 | 3 | 2 |
| delivery_wrong_item | 3 | 3 | 1 |
| delivery_delayed | 3 | 3 | 2 |
| amazon_music | 1 | 1 | 1 |

## 6. Improvement Examples (V2 ❌ → V3 ✅)
- `2555a8d9872a2f15` (delivery_missing): V2 selected `amazon_locker`. Retrieved: ['delivery_missing', 'delivery_missing', 'delivery_missing']
  *V3 Reasoning*: User explicitly mentions that the package was delivered but didn't receive it, indicating a missing package issue.

- `548c4f7b87a573e3` (account_billing): V2 selected `other_support`. Retrieved: ['account_billing', 'account_billing', 'account_billing']
  *V3 Reasoning*: User is experiencing an issue with adding money to Amazon Pay using a debit card, which is a billing-related problem, and is requesting assistance from the support team.

- `a0cb92cfb35738bb` (digital_kindle): V2 selected `other_support`. Retrieved: ['digital_kindle', 'digital_kindle', 'digital_kindle']
  *V3 Reasoning*: The user is trying to purchase an Italian ebook, La gente by Bianchi, but is unable to do so because it's only available on amazon.it and the user's account is in the UK. The user is looking for a way to access the ebook on Amazon UK, and the agent is providing guidance on how to proceed.

- `7e10f8a5300df65c` (account_access): V2 selected `delivery_wrong_item`. Retrieved: ['account_access', 'account_access', 'account_access']
  *V3 Reasoning*: The user's account has been blocked due to security reasons, and they are seeking assistance with the verification process, which is a common issue with account access. Competing intents were rejected because the user's concerns are related to their account login and verification process, not a physical package or delivery issue.

- `a3b31228d3f292c5` (promotions_pricing): V2 selected `other_support`. Retrieved: ['promotions_pricing', 'promotions_pricing', 'promotions_pricing']
  *V3 Reasoning*: The user is questioning the legitimacy of a promotional price, suggesting that it may be a price increase rather than a genuine discount. The agent should request more context to clarify the issue, such as the order number or product details, to determine the correct course of action.

## 7. Regression Examples (V2 ✅ → V3 ❌)
- `d6cf59dcf89bf508` (account_billing): V3 selected `account_access`. Retrieved: ['delivery_wrong_item', 'account_access', 'account_access']
  *V3 Reasoning*: The user is concerned about account security after receiving an unsolicited email about a free trial of Amazon Prime. They are seeking clarification on how the trial was activated and whether their account was compromised. Competing intents were rejected because the user's primary concern is account security, which aligns with the intent for account_access.

- `add56eb200cd4103` (echo_alexa): V3 selected `delivery_missing`. Retrieved: ['echo_alexa', 'echo_alexa', 'echo_alexa']
  *V3 Reasoning*: The user is reporting a missing package, as they were not notified of its delivery and were unable to retrieve it from the locker. The primary issue is the missing package, and competing intents were rejected due to the explicit mention of a missing package and the lack of information about a physical order problem.

- `663015f372cd3b8a` (promotions_pricing): V3 selected `product_availability`. Retrieved: ['returns_refunds', 'returns_refunds', 'returns_refunds']
  *V3 Reasoning*: The user is asking about the availability of a specific product (LG refrigerator) and its warranty, indicating a product-related inquiry rather than a delivery or billing issue.

- `373f82ed0389646e` (returns_refunds): V3 selected `delivery_wrong_item`. Retrieved: ['returns_refunds', 'returns_refunds', 'returns_refunds']
  *V3 Reasoning*: The user is unable to return a product due to the system not allowing it, and they are frustrated with the response, indicating a need for a supervisor's review.

- `baa82fe4c3c04a25` (amazon_locker): V3 selected `delivery_delayed`. Retrieved: ['returns_refunds', 'returns_refunds', 'delivery_delayed']
  *V3 Reasoning*: The user is expressing frustration with the delayed pickup of their package, mentioning that they have contacted the customer service team multiple times and are seeking assistance to resolve the issue.

## 8. Confusion Matrix (V3 Pilot)
| Expected | Predicted | Count |
|---|---|---:|
| delivery_missing | delivery_wrong_item | 2 |
| account_billing | promotions_pricing | 1 |
| account_billing | account_access | 1 |
| digital_prime_video | account_access | 1 |
| digital_prime_video | echo_alexa | 1 |
| digital_prime_video | product_availability | 1 |
| digital_kindle | account_access | 1 |
| digital_kindle | digital_prime_video | 1 |
| account_access | delivery_delayed | 1 |
| account_access | delivery_wrong_item | 1 |
| account_access | other_support | 1 |
| promotions_pricing | delivery_missing | 1 |
| promotions_pricing | product_availability | 1 |
| promotions_pricing | digital_kindle | 1 |
| promotions_pricing | delivery_delayed | 1 |
| product_availability | echo_alexa | 1 |
| product_availability | delivery_delayed | 1 |
| returns_refunds | delivery_delayed | 1 |
| returns_refunds | delivery_wrong_item | 1 |
| returns_refunds | account_billing | 1 |
| echo_alexa | delivery_delayed | 1 |
| echo_alexa | delivery_missing | 1 |
| amazon_locker | delivery_delayed | 2 |
| amazon_locker | product_availability | 1 |
| grocery_fresh | delivery_delayed | 2 |
| grocery_fresh | account_access | 1 |
| delivery_wrong_item | account_access | 2 |
| delivery_delayed | account_access | 1 |

## 9. Error Attribution
If V3 failed, it typically occurred on `RETRIEVAL_MISSING` examples, which is expected since V3 is not a retriever.

## 10. Regression Risk Assessment
Regressions: 19. Impact: High.

## 11. Decision
**CURRENT BEST**:
V2

**V3 STATUS**:
REJECT

**PRODUCTION MODIFIED**:
NO

**GOLDEN SET MODIFIED**:
NO

**FAISS MODIFIED**:
NO

**MODEL WEIGHTS MODIFIED**:
NO
