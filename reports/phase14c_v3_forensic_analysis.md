# Phase 14C — V2 vs V3 Forensic Failure Analysis

## 1. Top V3 Improvements (V2 ❌ → V3 ✅)
These represent the POSITIVE behaviors introduced by V3.

### 1. 2555a8d9872a2f15
- **Expected**: `delivery_missing`
- **V2 Prediction**: `amazon_locker`
- **Retrieved**: `['delivery_missing', 'delivery_missing', 'delivery_missing']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `amazon_locker` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: User explicitly mentions that the package was delivered but didn't receive it, indicating a missing package issue.

### 2. 548c4f7b87a573e3
- **Expected**: `account_billing`
- **V2 Prediction**: `other_support`
- **Retrieved**: `['account_billing', 'account_billing', 'account_billing']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `other_support` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: User is experiencing an issue with adding money to Amazon Pay using a debit card, which is a billing-related problem, and is requesting assistance from the support team.

### 3. a0cb92cfb35738bb
- **Expected**: `digital_kindle`
- **V2 Prediction**: `other_support`
- **Retrieved**: `['digital_kindle', 'digital_kindle', 'digital_kindle']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `other_support` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: The user is trying to purchase an Italian ebook, La gente by Bianchi, but is unable to do so because it's only available on amazon.it and the user's account is in the UK. The user is looking for a way to access the ebook on Amazon UK, and the agent is providing guidance on how to proceed.

### 4. 7e10f8a5300df65c
- **Expected**: `account_access`
- **V2 Prediction**: `delivery_wrong_item`
- **Retrieved**: `['account_access', 'account_access', 'account_access']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `delivery_wrong_item` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: The user's account has been blocked due to security reasons, and they are seeking assistance with the verification process, which is a common issue with account access. Competing intents were rejected because the user's concerns are related to their account login and verification process, not a physical package or delivery issue.

### 5. a3b31228d3f292c5
- **Expected**: `promotions_pricing`
- **V2 Prediction**: `other_support`
- **Retrieved**: `['promotions_pricing', 'promotions_pricing', 'promotions_pricing']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `other_support` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: The user is questioning the legitimacy of a promotional price, suggesting that it may be a price increase rather than a genuine discount. The agent should request more context to clarify the issue, such as the order number or product details, to determine the correct course of action.

### 6. 4c2ba68f8d6d8d01
- **Expected**: `echo_alexa`
- **V2 Prediction**: `other_support`
- **Retrieved**: `['echo_alexa', 'delivery_delayed', 'echo_alexa']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `other_support` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: User is experiencing issues with Alexa's birthday feature, specifically the 'happy birthday' prompt not working as expected. This is a technical issue with the Alexa skill, not a problem with the device or account.

### 7. 59b64538302cb337
- **Expected**: `echo_alexa`
- **V2 Prediction**: `other_support`
- **Retrieved**: `['echo_alexa', 'echo_alexa', 'amazon_music']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `other_support` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: User is expressing disappointment with the quality of speakers on Echo Plus and asking for an update on when better speakers will be available, indicating a concern with the device itself, which aligns with the intent for Echo-related issues.

### 8. 507a5d959193bd85
- **Expected**: `promotions_pricing`
- **V2 Prediction**: `other_support`
- **Retrieved**: `['delivery_delayed', 'promotions_pricing', 'promotions_pricing']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `other_support` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: The user is expressing frustration with a price discrepancy on an SD card, but the agent's response indicates that the pricing is set by the sellers and is subject to market fluctuations, suggesting that the intent is related to promotions and pricing rather than a delivery issue.

### 9. 20c1a80b2496fb80
- **Expected**: `delivery_missing`
- **V2 Prediction**: `amazon_locker`
- **Retrieved**: `['delivery_missing', 'amazon_locker', 'amazon_locker']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `amazon_locker` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: The user is reporting that they received an empty package, which suggests a delivery issue. The intent `delivery_missing` is preferred over `delivery_wrong_item` because the user explicitly mentions receiving an empty package, which is a common cause of `delivery_missing`. The conversation does not indicate that the user is requesting a refund or asking about product availability, which are characteristics of `returns_refunds` and `product_availability`, respectively.

### 10. e0e2bacc798bff2b
- **Expected**: `digital_kindle`
- **V2 Prediction**: `other_support`
- **Retrieved**: `['delivery_delayed', 'delivery_delayed', 'delivery_delayed']`
- **Why V2 Failed**: V2 was explicitly told 'DO NOT classify based solely on the closest retrieved example', causing it to over-correct and guess `other_support` despite correct evidence.
- **Helpful V3 Rule**: `If the retrieved examples unanimously share an intent that aligns with the user's actual problem, prefer it.`
- **V3 Reasoning Snippet**: The user is asking about a Kindle device, which is a digital product, and is seeking information about its delivery status. The intent is digital_kindle because the user is inquiring about a specific digital product, and the conversation does not indicate a delivery issue or a problem with the Kindle itself. The confidence is 0.9 because the conversation strongly suggests the intent of digital_kindle, with the user explicitly mentioning a Kindle device and asking about its delivery status.

## 2. Top V3 Regressions (V2 ✅ → V3 ❌)
These represent the HARMFUL behaviors introduced by V3.

### 1. d6cf59dcf89bf508
- **Expected**: `account_billing`
- **V3 Prediction**: `account_access` (V2 correctly chose `account_billing`)
- **Retrieved**: `['delivery_wrong_item', 'account_access', 'account_access']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is concerned about account security after receiving an unsolicited email about a free trial of Amazon Prime. They are seeking clarification on how the trial was activated and whether their account was compromised. Competing intents were rejected because the user's primary concern is account security, which aligns with the intent for account_access.

### 2. add56eb200cd4103
- **Expected**: `echo_alexa`
- **V3 Prediction**: `delivery_missing` (V2 correctly chose `echo_alexa`)
- **Retrieved**: `['echo_alexa', 'echo_alexa', 'echo_alexa']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is reporting a missing package, as they were not notified of its delivery and were unable to retrieve it from the locker. The primary issue is the missing package, and competing intents were rejected due to the explicit mention of a missing package and the lack of information about a physical order problem.

### 3. 663015f372cd3b8a
- **Expected**: `promotions_pricing`
- **V3 Prediction**: `product_availability` (V2 correctly chose `promotions_pricing`)
- **Retrieved**: `['returns_refunds', 'returns_refunds', 'returns_refunds']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is asking about the availability of a specific product (LG refrigerator) and its warranty, indicating a product-related inquiry rather than a delivery or billing issue.

### 4. 373f82ed0389646e
- **Expected**: `returns_refunds`
- **V3 Prediction**: `delivery_wrong_item` (V2 correctly chose `returns_refunds`)
- **Retrieved**: `['returns_refunds', 'returns_refunds', 'returns_refunds']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is unable to return a product due to the system not allowing it, and they are frustrated with the response, indicating a need for a supervisor's review.

### 5. baa82fe4c3c04a25
- **Expected**: `amazon_locker`
- **V3 Prediction**: `delivery_delayed` (V2 correctly chose `amazon_locker`)
- **Retrieved**: `['returns_refunds', 'returns_refunds', 'delivery_delayed']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is expressing frustration with the delayed pickup of their package, mentioning that they have contacted the customer service team multiple times and are seeking assistance to resolve the issue.

### 6. 7dd3e41677eca8cf
- **Expected**: `delivery_delayed`
- **V3 Prediction**: `account_access` (V2 correctly chose `delivery_delayed`)
- **Retrieved**: `['delivery_delayed', 'delivery_delayed', 'delivery_delayed']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is expressing gratitude for customer service and acknowledging the issue with their order, indicating that the primary problem is with their account access, not the delivery itself.

### 7. b916108101eca175
- **Expected**: `delivery_wrong_item`
- **V3 Prediction**: `account_access` (V2 correctly chose `delivery_wrong_item`)
- **Retrieved**: `['account_access', 'account_billing', 'account_access']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: User is experiencing issues with their Amazon Pay Balance and mobile number being blocked, indicating a problem with their account access.

### 8. 962f87319795305d
- **Expected**: `amazon_locker`
- **V3 Prediction**: `product_availability` (V2 correctly chose `amazon_locker`)
- **Retrieved**: `['amazon_locker', 'amazon_locker', 'amazon_locker']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is inquiring about the availability of an item, specifically an oil diffuser, which is not a physical product that can be shipped to a PO BOX, home address, or Amazon Locker. The user's frustration with the shipping options is not the primary issue, but rather the unavailability of the product.

### 9. 7906799da7f63453
- **Expected**: `digital_prime_video`
- **V3 Prediction**: `echo_alexa` (V2 correctly chose `digital_prime_video`)
- **Retrieved**: `['digital_prime_video', 'digital_prime_video', 'digital_prime_video']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: The user is expressing frustration with the limitations of their Echo device, specifically the lack of video integration and other features, which suggests a need for human review to understand the issue and provide a suitable solution.

### 10. f80ee1ce26d346fd
- **Expected**: `promotions_pricing`
- **V3 Prediction**: `digital_kindle` (V2 correctly chose `promotions_pricing`)
- **Retrieved**: `['promotions_pricing', 'promotions_pricing', 'promotions_pricing']`
- **Harmful V3 Rule**: Boundary Over-Enforcement or Rigid Keyword Priority. V3 explicitly prioritized a zero-shot keyword match over the correct retrieved context.
- **V3 Reasoning Snippet**: User is experiencing issues with eBook downloads on their Kindle device, with no mention of Prime Video or other digital services. The conversation focuses on troubleshooting eBook-related problems, making digital_kindle the most appropriate intent.

## 3. Instruction-Level Causal Patterns

| V3 Instruction/Rule | Intended Effect | Risk |
|---|---|---|
| `If retrieved examples unanimously share an intent... prefer it.` | Fix CLASSIFIER_IGNORED_CORRECT | **BENEFICIAL** (Fixed 11 cases) |
| Explicit Taxonomy Boundary Rules (e.g. `grocery_fresh` vs `returns_refunds`) | Fix CONFLICTING_EVIDENCE | **OVERLY AGGRESSIVE** (Caused regressions by forcing intents against context) |
| `Prefer the candidate whose taxonomy definition best matches...` | Anchor reasoning in actual problem | **HARMFUL** (Caused the LLM to completely ignore unanimous RAG context and act zero-shot) |
| `Do not choose an intent merely because it appears frequently in retrieval` | Prevent RAG bias | **REDUNDANT/OVERLY AGGRESSIVE** (Re-introduced the V2 over-correction problem) |

## 4. Evidence Hierarchy Recommendation

**STRATEGY D**: Unanimous high-quality RAG evidence gets strong weight, but never overrides explicit contradiction in the user request.
- **Why**: The biggest win of V3 was explicitly trusting unanimous RAG context. The biggest failure was V3 overriding RAG context due to rigid, hardcoded boundary rules or zero-shot keyword interpretations. By implementing Strategy D, we keep the gains on `CLASSIFIER_IGNORED_CORRECT` without destroying the baseline accuracy on `CORRECT_V2` examples.

