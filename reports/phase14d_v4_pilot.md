# Phase 14D — Controlled V4 Classifier Pilot

## 1. Executive Summary
The pilot tested 60 examples. V4 achieved **50.0%** accuracy vs V2's **60.0%**.
V4 improved 13 queries, regressed 19 queries, leaving 28 unchanged. Net gain: -6

## 2. V2 Baseline vs V4 Results
| Metric | V2 | V4 |
|---|---:|---:|
| Accuracy | 60.0% | 50.0% |
| Macro F1 | 0.6794 | 0.4943 |

## 3. Targeted Failure-Mode Results
| Category | Total | V2 Accuracy | V4 Accuracy |
|---|---:|---:|---:|
| CLASSIFIER_IGNORED_CORRECT | 10 | 0.0% | 60.0% |
| CONFLICTING_EVIDENCE | 9 | 0.0% | 55.6% |
| RETRIEVAL_MISSING | 5 | 0.0% | 40.0% |
| CORRECT_V2 | 36 | 100.0% | 47.2% |

## 4. Regression Analysis
- V2 correct → V4 wrong (Regressions): 19
- V2 wrong → V4 wrong (Both wrong): 11
- V2 correct → V4 correct (Both correct): 17

### Regression: `d6cf59dcf89bf508`
- Expected: `account_billing`
- V2: `account_billing` | V4: `account_access`
- Retrieved: `['delivery_wrong_item', 'account_access', 'account_access']`
- V4 Reasoning: The customer is concerned about account security after receiving an unsolicited email about a free trial of Amazon Prime. They are seeking clarification on how the trial was activated and whether their account was compromised. The customer's primary problem is account access, and competing intents (e.g., delivery_wrong_item) are not relevant to this situation.

### Regression: `add56eb200cd4103`
- Expected: `echo_alexa`
- V2: `echo_alexa` | V4: `returns_refunds`
- Retrieved: `['echo_alexa', 'echo_alexa', 'echo_alexa']`
- V4 Reasoning: Customer is requesting a refund for a missing package, and the primary problem is the package not being delivered. The customer has already contacted @80, but they did not respond, and the package was returned to Amazon. The customer is frustrated with the lack of communication and the inability to recover the product.

### Regression: `663015f372cd3b8a`
- Expected: `promotions_pricing`
- V2: `promotions_pricing` | V4: `product_availability`
- Retrieved: `['returns_refunds', 'returns_refunds', 'returns_refunds']`
- V4 Reasoning: The customer is asking about the warranty for a specific product, indicating a product-related inquiry. Competing intents were rejected as the customer's primary problem is related to product information, not returns or refunds.

### Regression: `baa82fe4c3c04a25`
- Expected: `amazon_locker`
- V2: `amazon_locker` | V4: `delivery_missing`
- Retrieved: `['returns_refunds', 'returns_refunds', 'delivery_delayed']`
- V4 Reasoning: The customer is reporting a missing package despite tracking indicating delivery, and they have provided a call recording from BlueDart confirming the issue. This suggests a more complex issue than a simple missing package, warranting a human review for escalation.

### Regression: `7dd3e41677eca8cf`
- Expected: `delivery_delayed`
- V2: `delivery_delayed` | V4: `account_access`
- Retrieved: `['delivery_delayed', 'delivery_delayed', 'delivery_delayed']`
- V4 Reasoning: The customer is expressing appreciation for customer service, indicating that the issue was resolved and they are satisfied with the service, which suggests that the primary problem was not a delivery issue but rather a concern about the customer service experience.

### Regression: `220588c05e025c77`
- Expected: `product_availability`
- V2: `product_availability` | V4: `delivery_missing`
- Retrieved: `['product_availability', 'product_availability', 'product_availability']`
- V4 Reasoning: The customer is reporting that their package is not available, despite tracking showing delivery. This suggests a missing package, which is a stronger intent than other options like product_availability or promotions_pricing. The customer's frustration and request to forward the issue to a concerned team also indicates a need for escalation to a human reviewer.

### Regression: `b916108101eca175`
- Expected: `delivery_wrong_item`
- V2: `delivery_wrong_item` | V4: `account_access`
- Retrieved: `['account_access', 'account_billing', 'account_access']`
- V4 Reasoning: The customer is experiencing issues with their Amazon Pay balance and mobile number being blocked, indicating a problem with account access. However, the conversation lacks a clear order number or other critical context, suggesting that clarification is needed to accurately diagnose and resolve the issue.

### Regression: `962f87319795305d`
- Expected: `amazon_locker`
- V2: `amazon_locker` | V4: `product_availability`
- Retrieved: `['amazon_locker', 'amazon_locker', 'amazon_locker']`
- V4 Reasoning: The customer is asking about the availability of an oil diffuser, which is not a product that can be shipped to PO BOX, Home address, or an Amazon Locker. The customer is requesting help with ordering the product, indicating a need for product availability information.

### Regression: `fc5e5ed945b5af36`
- Expected: `amazon_locker`
- V2: `amazon_locker` | V4: `product_availability`
- Retrieved: `['amazon_locker', 'amazon_locker', 'amazon_locker']`
- V4 Reasoning: The customer is asking about the availability of a new Amazon Locker, and the primary problem is the lack of information about when it will be available. Competing intents were rejected because the conversation does not describe a delivery issue, locker access code, or refund request.

### Regression: `7906799da7f63453`
- Expected: `digital_prime_video`
- V2: `digital_prime_video` | V4: `echo_alexa`
- Retrieved: `['digital_prime_video', 'digital_prime_video', 'digital_prime_video']`
- V4 Reasoning: The customer is expressing frustration with the limitations of their Echo device in India, specifically the lack of video integration and other features. The conversation requires a more in-depth review to understand the customer's concerns and provide a suitable solution, indicating a need for human review.

### Regression: `f80ee1ce26d346fd`
- Expected: `promotions_pricing`
- V2: `promotions_pricing` | V4: `digital_kindle`
- Retrieved: `['promotions_pricing', 'promotions_pricing', 'promotions_pricing']`
- V4 Reasoning: The customer is experiencing issues with eBook downloads on their Kindle device, with the primary problem being that the page is not loading properly and an error is occurring. Competing intents were rejected as the customer's issue is specific to eBook downloads and not related to Prime Video or account access.

### Regression: `564d4563079bdbfb`
- Expected: `delivery_missing`
- V2: `delivery_missing` | V4: `delivery_wrong_item`
- Retrieved: `['delivery_missing', 'delivery_missing', 'delivery_missing']`
- V4 Reasoning: The customer received a damaged item, which is a physical product, and is requesting assistance from the support team to resolve the issue.

### Regression: `271f08dfe4b24f20`
- Expected: `promotions_pricing`
- V2: `promotions_pricing` | V4: `account_access`
- Retrieved: `['promotions_pricing', 'promotions_pricing', 'promotions_pricing']`
- V4 Reasoning: The customer is reporting a security concern with their account, specifically false commitments by Amazon customer service and escalation team, and is requesting assistance to resolve the issue. Competing intents were rejected due to the customer's primary problem being related to account security and the need for a supervisor to review the situation.

### Regression: `7537e113f152e797`
- Expected: `returns_refunds`
- V2: `returns_refunds` | V4: `account_billing`
- Retrieved: `['returns_refunds', 'returns_refunds', 'returns_refunds']`
- V4 Reasoning: The customer is disputing an unauthorized Prime charge, indicating a billing issue, and is seeking a refund. Competing intents were rejected as the primary problem is related to account billing, not returns or refunds.

### Regression: `04f0d488a16c8b29`
- Expected: `account_access`
- V2: `account_access` | V4: `delivery_wrong_item`
- Retrieved: `['delivery_missing', 'delivery_missing', 'delivery_missing']`
- V4 Reasoning: The customer received an incorrect box for their order, indicating a problem with the physical product. Competing intents were rejected because the primary issue is with the physical item, not with delivery or billing. The customer's request for assistance with the incorrect order aligns with the intent for delivery_wrong_item.

### Regression: `c763f518de8ef948`
- Expected: `account_access`
- V2: `account_access` | V4: `other_support`
- Retrieved: `['account_access', 'account_access', 'account_access']`
- V4 Reasoning: The conversation does not describe a specific issue with Amazon services or products, but rather a general question about accessing the Google Play store from an Amazon Fire HD tablet, which is outside the scope of Amazon's support.

### Regression: `3bb93e2f47e6c826`
- Expected: `digital_prime_video`
- V2: `digital_prime_video` | V4: `product_availability`
- Retrieved: `['digital_prime_video', 'delivery_delayed', 'digital_prime_video']`
- V4 Reasoning: Customer is asking about the availability of a specific product (Fire TV Stick with Alexa Voice Remote) in India, and the agent's response indicates that the device is geo-location specific and not available in India, but suggests ordering from amazon.in instead.

### Regression: `dd3f0d83804bec2a`
- Expected: `delivery_wrong_item`
- V2: `delivery_wrong_item` | V4: `account_access`
- Retrieved: `['delivery_wrong_item', 'account_access', 'account_billing']`
- V4 Reasoning: The customer is experiencing login issues and receiving an 'incorrect password' error message, suggesting a potential account access problem. Further clarification is needed to determine the root cause of the issue.

### Regression: `3f38d0690064ea3e`
- Expected: `grocery_fresh`
- V2: `grocery_fresh` | V4: `other_support`
- Retrieved: `['delivery_missing', 'account_billing', 'delivery_wrong_item']`
- V4 Reasoning: The conversation does not describe a specific issue with a product or service, but rather a comparison between Amazon and Flipkart's user interface.

## 5. Improvement Analysis
- V2 wrong → V4 correct (Improvements): 13

### Improvement: `9d4ee10b51d6518c`
- Expected: `delivery_missing`
- V2: `amazon_locker` | V4: `delivery_missing`
- Retrieved: `['delivery_missing', 'delivery_missing', 'delivery_missing']`
- V4 Reasoning: The customer is reporting that a package was delivered, but the item inside is faulty and not the correct item. This is a classic case of a delivery missing, where the customer is claiming that the item received is not the one they ordered. The customer's language and tone suggest frustration and disappointment, which is consistent with a delivery missing intent.

### Improvement: `548c4f7b87a573e3`
- Expected: `account_billing`
- V2: `other_support` | V4: `account_billing`
- Retrieved: `['account_billing', 'account_billing', 'account_billing']`
- V4 Reasoning: The customer is experiencing an issue with adding money to Amazon Pay using a debit card, which suggests a problem with their account billing. The conversation does not indicate a missing critical context or a fundamentally different problem, and the customer is requesting assistance from the support team.

### Improvement: `e6aef6c530ba4876`
- Expected: `digital_prime_video`
- V2: `other_support` | V4: `digital_prime_video`
- Retrieved: `['digital_prime_video', 'digital_prime_video', 'digital_prime_video']`
- V4 Reasoning: The customer is experiencing issues with their Prime Video subscription, specifically with the activation process after a payment deduction. Competing intents were rejected as the primary problem is related to the Prime Video service, not the account billing or subscription status.

### Improvement: `a0cb92cfb35738bb`
- Expected: `digital_kindle`
- V2: `other_support` | V4: `digital_kindle`
- Retrieved: `['digital_kindle', 'digital_kindle', 'digital_kindle']`
- V4 Reasoning: The customer is trying to purchase an Italian ebook, La Gente by Bianchi, but is unable to do so because it's only available on Amazon.it and their account is in the UK. The primary problem is related to digital access, and the customer is seeking assistance with purchasing the ebook. Competing intents were rejected because the customer's request is specific to digital access and ebook purchasing, which is not covered by other intents.

### Improvement: `7e10f8a5300df65c`
- Expected: `account_access`
- V2: `delivery_wrong_item` | V4: `account_access`
- Retrieved: `['account_access', 'account_access', 'account_access']`
- V4 Reasoning: The customer's account has been blocked due to security reasons, and they are seeking assistance with the verification process. Competing intents were rejected as the primary issue is account access, not a specific product purchase or refund.

### Improvement: `a3b31228d3f292c5`
- Expected: `promotions_pricing`
- V2: `other_support` | V4: `promotions_pricing`
- Retrieved: `['promotions_pricing', 'promotions_pricing', 'promotions_pricing']`
- V4 Reasoning: The customer is questioning the legitimacy of a promotional price, suggesting that it may be a price increase rather than a discount. The primary problem is the customer's skepticism about the promotional price, and a clarification is needed to understand the situation.

### Improvement: `136747dbfd949f68`
- Expected: `returns_refunds`
- V2: `other_support` | V4: `returns_refunds`
- Retrieved: `['delivery_delayed', 'returns_refunds', 'delivery_delayed']`
- V4 Reasoning: The customer is requesting the status of their refund, which is 2 weeks old, and is unhappy with the response that it will take 3-5 business days to process. The customer is asking for clarification on the cause of the delay and if the issue was processed correctly since then.

### Improvement: `4c2ba68f8d6d8d01`
- Expected: `echo_alexa`
- V2: `other_support` | V4: `echo_alexa`
- Retrieved: `['echo_alexa', 'delivery_delayed', 'echo_alexa']`
- V4 Reasoning: The customer is experiencing issues with the Alexa app and its birthday feature, which is not working as expected. The primary problem is with the Alexa app, and the customer is seeking assistance with enabling the skill and resolving the issue.

### Improvement: `59b64538302cb337`
- Expected: `echo_alexa`
- V2: `other_support` | V4: `echo_alexa`
- Retrieved: `['echo_alexa', 'echo_alexa', 'amazon_music']`
- V4 Reasoning: The customer is inquiring about the Echo device, specifically asking about compatibility with previously built-in home speakers and requesting information on how to contact Amazon for further assistance. Competing intents were rejected due to the lack of a clear request for a refund or return, and the customer's primary concern is seeking information about the Echo device.

### Improvement: `507a5d959193bd85`
- Expected: `promotions_pricing`
- V2: `other_support` | V4: `promotions_pricing`
- Retrieved: `['delivery_delayed', 'promotions_pricing', 'promotions_pricing']`
- V4 Reasoning: The customer is upset about a price discrepancy between a listed price and the actual price at checkout, indicating a pricing issue rather than a delivery or product problem.

### Improvement: `20c1a80b2496fb80`
- Expected: `delivery_missing`
- V2: `amazon_locker` | V4: `delivery_missing`
- Retrieved: `['delivery_missing', 'amazon_locker', 'amazon_locker']`
- V4 Reasoning: The customer received an empty cardboard sleeve instead of the ordered item, indicating a missing item. This aligns with the delivery_missing intent, which is semantically closest to the customer's actual problem.

### Improvement: `e0e2bacc798bff2b`
- Expected: `digital_kindle`
- V2: `other_support` | V4: `digital_kindle`
- Retrieved: `['delivery_delayed', 'delivery_delayed', 'delivery_delayed']`
- V4 Reasoning: The customer is asking about their Kindle device, which is a digital product. The primary problem is related to the device itself, not a delivery issue. Competing intents were rejected because the customer's request clearly describes a fundamentally different problem.

### Improvement: `451122bbe75eae6a`
- Expected: `product_availability`
- V2: `other_support` | V4: `product_availability`
- Retrieved: `['account_billing', 'account_billing', 'amazon_music']`
- V4 Reasoning: The customer is asking about the behavior of pre-ordering an mp3 album and how it interacts with a gift card balance, indicating a question about product availability and pricing.

## 6. Per-Intent Results
| Intent | Total | V2 Correct | V4 Correct |
|---|---:|---:|---:|
| delivery_missing | 6 | 3 | 4 |
| account_billing | 5 | 3 | 3 |
| digital_prime_video | 4 | 3 | 2 |
| digital_kindle | 5 | 2 | 4 |
| account_access | 5 | 3 | 2 |
| promotions_pricing | 6 | 3 | 2 |
| product_availability | 5 | 2 | 2 |
| returns_refunds | 4 | 3 | 3 |
| echo_alexa | 4 | 1 | 2 |
| amazon_locker | 4 | 3 | 0 |
| grocery_fresh | 5 | 3 | 2 |
| delivery_wrong_item | 3 | 3 | 1 |
| delivery_delayed | 3 | 3 | 2 |
| amazon_music | 1 | 1 | 1 |

## 7. Confusion Pairs (V4 Pilot)
| Expected | Predicted | Count |
|---|---|---:|
| delivery_missing | product_availability | 1 |
| delivery_missing | delivery_wrong_item | 1 |
| account_billing | promotions_pricing | 1 |
| account_billing | account_access | 1 |
| digital_prime_video | echo_alexa | 1 |
| digital_prime_video | product_availability | 1 |
| digital_kindle | other_support | 1 |
| account_access | delivery_delayed | 1 |
| account_access | delivery_wrong_item | 1 |
| account_access | other_support | 1 |
| promotions_pricing | account_access | 2 |
| promotions_pricing | product_availability | 1 |
| promotions_pricing | digital_kindle | 1 |
| product_availability | echo_alexa | 1 |
| product_availability | delivery_delayed | 1 |
| product_availability | delivery_missing | 1 |
| returns_refunds | account_billing | 1 |
| echo_alexa | delivery_delayed | 1 |
| echo_alexa | returns_refunds | 1 |
| amazon_locker | delivery_delayed | 1 |
| amazon_locker | delivery_missing | 1 |
| amazon_locker | product_availability | 2 |
| grocery_fresh | product_availability | 1 |
| grocery_fresh | delivery_delayed | 1 |
| grocery_fresh | other_support | 1 |
| delivery_wrong_item | account_access | 2 |
| delivery_delayed | account_access | 1 |

## 8. Data Quality
- Malformed Responses: 0
- Invalid Intents: 0

## 9. Decision
**CURRENT BEST**:
V2

**V4 STATUS**:
REJECT

**PRODUCTION MODIFIED**:
NO

**GOLDEN SET MODIFIED**:
NO

**FAISS MODIFIED**:
NO

**MODEL WEIGHTS MODIFIED**:
NO
