# Golden Set Human Review Queue

## GS-028 - LIKELY_MISLABELED
- **Current Label**: `delivery_wrong_item`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The customer's tone and language suggest frustration and disappointment, which is more indicative of a delayed or missing delivery issue rather than a wrong item. The mention of 'await yet another email stating incorrect information' implies a sense of repetition and frustration, which is not typically associated with a wrong item issue.
- **Competing Labels**: delivery_delayed, delivery_missing
- **Evidence**: The customer's tone and language suggest frustration and disappointment, The mention of 'await yet another email stating incorrect information' implies a sense of repetition and frustration
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-035 - LIKELY_MISLABELED
- **Current Label**: `delivery_wrong_item`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The conversation starts with a complaint about account issues, which is not directly related to the assigned intent. The customer mentions unauthorized access and password reset, but the primary concern is the delivery issue.
- **Competing Labels**: delivery_missing, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_music, echo_alexa, amazon_locker, grocery_fresh
- **Evidence**: @AmazonHelp Placed an order, got an email to say there has been unauthorized access and to reset password, @AmazonHelp But i get an email to say it's successfully updated then try to log in and it says it is incorrect
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-040 - LIKELY_MISLABELED
- **Current Label**: `delivery_wrong_item`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The customer's initial statement about the item not arriving on time and the subsequent statements about incorrect tracking information and delivery address suggest a more complex issue than a simple wrong item. The customer's frustration and confusion also indicate a potential mislabeling of the assigned intent.
- **Competing Labels**: delivery_delayed, delivery_missing
- **Evidence**: The customer's statement about the item not arriving on time and the subsequent statements about incorrect tracking information and delivery address., The customer's frustration and confusion about the situation.
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-056 - LIKELY_MISLABELED
- **Current Label**: `account_billing`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The customer's language and tone suggest a frustration with a delivery issue, rather than a billing concern.
- **Competing Labels**: returns_refunds, product_availability
- **Evidence**: @115821 i will singlehandedly destroy your reputation on this Website, where the f*ck is my money????
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-058 - LIKELY_MISLABELED
- **Current Label**: `account_billing`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The conversation mentions 'delivery' multiple times, which suggests that the intent is related to shipping or delivery issues, rather than account billing.
- **Competing Labels**: returns_refunds, product_availability, promotions_pricing, account_access
- **Evidence**: delivery, delayed, missing, wrong_item
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-063 - LIKELY_MISLABELED
- **Current Label**: `account_billing`
- **Suggested Label**: `account_access`
- **Why Problematic**: The conversation starts with a complaint about a poor experience with a Prime purchase, which doesn't align with account billing. The customer also mentions cancelling Prime and seeking help with a previous purchase, indicating a need for account access.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item
- **Evidence**: The customer mentions cancelling Prime, The customer mentions a previous purchase
- **Recommended Human Decision**: Review text and reassign to `account_access` if appropriate.

## GS-066 - LIKELY_MISLABELED
- **Current Label**: `account_billing`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The conversation starts with a concern about an unsolicited email from Amazon, which is not related to account billing. The conversation then shifts to discussing the potential reasons behind the email and the customer's concerns about account security.
- **Competing Labels**: delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_access, digital_prime_video, digital_kindle, amazon_music, echo_alexa, amazon_locker, grocery_fresh
- **Evidence**: The email is definitely from Amazon, for a trial of Amazon Prime that I didn't sign up for., If 2, while I appreciate free things, it seems like this trial will auto renew with my credit card info.
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-067 - LIKELY_MISLABELED
- **Current Label**: `account_billing`
- **Suggested Label**: `returns_refunds`
- **Why Problematic**: The customer is expressing frustration and desperation about a delayed or missing book delivery, and is threatening to take drastic actions, including a hunger strike and shutting off utilities. This behavior is not typical of a customer seeking to resolve an account billing issue.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item
- **Evidence**: The customer is expressing frustration and desperation about a delayed or missing book delivery, The customer is threatening to take drastic actions, including a hunger strike and shutting off utilities
- **Recommended Human Decision**: Review text and reassign to `returns_refunds` if appropriate.

## GS-101 - LIKELY_MISLABELED
- **Current Label**: `amazon_music`
- **Suggested Label**: `returns_refunds`
- **Why Problematic**: The conversation starts with a complaint about a delivery issue, which is not related to Amazon Music.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item
- **Evidence**: The customer mentions 'devolví dos productos' (I returned two products) and 'el otro no era el que pedí' (the other one was not the one I ordered)
- **Recommended Human Decision**: Review text and reassign to `returns_refunds` if appropriate.

## GS-105 - LIKELY_MISLABELED
- **Current Label**: `amazon_music`
- **Suggested Label**: `grocery_fresh`
- **Why Problematic**: The conversation starts with a complaint about a product (Nokia 6) not working and the customer's experience with Amazon's delivery and replacement process. The assigned intent 'amazon_music' does not match the context of the conversation.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_music
- **Evidence**: The customer mentions a product (Nokia 6) and a complaint about delivery and replacement., The conversation does not mention music or Prime Music at all.
- **Recommended Human Decision**: Review text and reassign to `grocery_fresh` if appropriate.

## GS-109 - LIKELY_MISLABELED
- **Current Label**: `amazon_music`
- **Suggested Label**: `grocery_fresh`
- **Why Problematic**: The conversation mentions 'Song', 'finden' (find), and 'eindeutig' (clearly) which are not typical phrases used in Amazon Music context. The mention of '@116935' and 'https://t.co/kzXfMZIY3b' suggests a different intent.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_locker, grocery_fresh
- **Evidence**: The conversation mentions 'Song' and 'finden' (find) which are not typical phrases used in Amazon Music context., @116935 and https://t.co/kzXfMZIY3b suggest a different intent.
- **Recommended Human Decision**: Review text and reassign to `grocery_fresh` if appropriate.

## GS-030 - AMBIGUOUS
- **Current Label**: `delivery_wrong_item`
- **Suggested Label**: `account_access`
- **Why Problematic**: The conversation starts with a question about Amazon password, which is not related to delivery. The assigned intent 'delivery_wrong_item' is not supported by the initial message.
- **Competing Labels**: delivery_delayed, delivery_missing, returns_refunds, product_availability, promotions_pricing, account_billing, digital_prime_video, digital_kindle, amazon_music, echo_alexa, amazon_locker, grocery_fresh
- **Evidence**: The conversation starts with a question about Amazon password., The assigned intent 'delivery_wrong_item' is not supported by the initial message.
- **Recommended Human Decision**: Review text and reassign to `account_access` if appropriate.

## GS-034 - AMBIGUOUS
- **Current Label**: `delivery_wrong_item`
- **Suggested Label**: `account_access`
- **Why Problematic**: The conversation starts with a complaint about not being able to log in to the account, which is not related to delivery. The mention of password changes and incorrect login attempts suggests an issue with account access rather than a delivery-related issue.
- **Competing Labels**: delivery_delayed, delivery_missing, returns_refunds, product_availability, promotions_pricing, account_billing
- **Evidence**: The conversation starts with a complaint about not being able to log in to the account., The mention of password changes and incorrect login attempts
- **Recommended Human Decision**: Review text and reassign to `account_access` if appropriate.

## GS-037 - AMBIGUOUS
- **Current Label**: `delivery_wrong_item`
- **Suggested Label**: `delivery_missing`
- **Why Problematic**: The conversation starts with a concern about missing orders, which could be related to delivery delays or missing items. However, the conversation quickly shifts to login issues and password changes, which doesn't strongly support the assigned intent. The suggested intent 'delivery_missing' seems more plausible given the initial concern about missing orders.
- **Competing Labels**: delivery_delayed, returns_refunds
- **Evidence**: The conversation starts with a concern about missing orders., The conversation quickly shifts to login issues and password changes.
- **Recommended Human Decision**: Review text and reassign to `delivery_missing` if appropriate.

## GS-041 - AMBIGUOUS
- **Current Label**: `delivery_wrong_item`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The conversation starts with a complaint about not having access to their account, which could be related to various intents, including account_access. The conversation then shifts to discussing password issues, which is more closely related to account_access.
- **Competing Labels**: delivery_delayed, returns_refunds, account_access
- **Evidence**: @AmazonHelp bonjour je n'ai plus accès à mon compte !!!, @389945 Avez-vous reçu un e-mail concernant votre compte ?
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-049 - AMBIGUOUS
- **Current Label**: `returns_refunds`
- **Suggested Label**: `product_availability`
- **Why Problematic**: The customer is asking about refund policies on price drops, but the response provided by the agent is not directly related to returns or refunds. The conversation is more related to product pricing and availability.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item
- **Evidence**: The constantly changing marketplace and our efforts to offer you the lowest price, may result in fluctuations in our prices over time.
- **Recommended Human Decision**: Review text and reassign to `product_availability` if appropriate.

## GS-053 - AMBIGUOUS
- **Current Label**: `returns_refunds`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The conversation starts with a complaint about a delayed delivery, which is not directly related to returns or refunds.
- **Competing Labels**: delivery_missing, delivery_wrong_item
- **Evidence**: @115823 is the new trick from amazon to lock up refunds (paid through gift card) which cannot be transferred to bank account., @AmazonHelp Which won't be of any use
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-069 - AMBIGUOUS
- **Current Label**: `account_billing`
- **Suggested Label**: `delivery_delayed`
- **Why Problematic**: The conversation starts with a request for assistance with loading Amazon Pay, which is not directly related to account billing. The conversation then shifts to discussing a delayed delivery, which is a more relevant intent.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item
- **Evidence**: @115850 @115821 Please help asap. We tried to load some amount in Amazon pay but after almost 20 hours, it doesn't show any amount., @AmazonHelp Why we can't connect if we haven't placed order? What a strategy to avoid traffic!!  How can we get the status of the Amazon Pay
- **Recommended Human Decision**: Review text and reassign to `delivery_delayed` if appropriate.

## GS-070 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `echo_alexa`
- **Why Problematic**: The conversation mentions 'Smart speaker. Smart living.' and 'ECHO', which suggests a strong connection to Echo devices. However, the assigned intent 'digital_prime_video' seems unrelated to the context.
- **Competing Labels**: product_availability, promotions_pricing, account_billing, account_access
- **Evidence**: Smart speaker. Smart living., ECHO
- **Recommended Human Decision**: Review text and reassign to `echo_alexa` if appropriate.

## GS-071 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `digital_prime_video`
- **Why Problematic**: Lack of context about the error message or symptoms described. The customer mentions issues with Amazon Video and Netflix, but the assigned intent only accounts for Amazon Video.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access
- **Evidence**: The customer mentions issues with Amazon Video and Netflix., The assigned intent only accounts for Amazon Video.
- **Recommended Human Decision**: Review text and reassign to `digital_prime_video` if appropriate.

## GS-074 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `digital_prime_video`
- **Why Problematic**: The conversation does not contain any explicit mention of Amazon Prime Video, and the context does not strongly suggest a discussion about the service.
- **Competing Labels**: returns_refunds, product_availability, promotions_pricing, account_billing, account_access
- **Evidence**: The mention of 'crazy on subscriptions' could be related to Amazon Prime Video, but it's not a clear indicator., The conversation does not contain any specific details about movies or video releases.
- **Recommended Human Decision**: Review text and reassign to `digital_prime_video` if appropriate.

## GS-075 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `product_availability`
- **Why Problematic**: The conversation mentions 'next update' and 'time passing without noticing', which could be related to product availability or a feature update, but the context is not strong enough to confirm the assigned intent.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item
- **Evidence**: The conversation mentions 'next update' and 'time passing without noticing'
- **Recommended Human Decision**: Review text and reassign to `product_availability` if appropriate.

## GS-076 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `grocery_fresh`
- **Why Problematic**: The conversation does not contain any relevant information about Prime Video, and the mention of 'Ver Redskins vs Cowboys en vivo' seems unrelated to the topic.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access
- **Evidence**: The conversation mentions 'Ver Redskins vs Cowboys en vivo' which is not related to Prime Video., The conversation does not contain any information about the Prime Video application or its features.
- **Recommended Human Decision**: Review text and reassign to `grocery_fresh` if appropriate.

## GS-081 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `product_availability`
- **Why Problematic**: The conversation starts with a question about the availability of Kannada movies in Prime, which is not directly related to Prime Video. The assigned intent does not match the context of the conversation.
- **Competing Labels**: product_availability, delivery_delayed
- **Evidence**: The conversation starts with a question about the availability of Kannada movies in Prime., The assigned intent does not match the context of the conversation.
- **Recommended Human Decision**: Review text and reassign to `product_availability` if appropriate.

## GS-082 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `product_availability`
- **Why Problematic**: The conversation starts with a question about a specific product (Fire TV Stick with Alexa Voice Remote) and its availability in India, which is not related to the assigned intent of digital_prime_video. The conversation also mentions Amazon Prime Video in India, which is a different topic.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access
- **Evidence**: The device is geo-location specific. Hence, you will not be able to access the features of the device here., You can place an order for the device sold on amazon.in to the shipping address in India.
- **Recommended Human Decision**: Review text and reassign to `product_availability` if appropriate.

## GS-083 - AMBIGUOUS
- **Current Label**: `digital_prime_video`
- **Suggested Label**: `product_availability`
- **Why Problematic**: The conversation does not contain any clear indication of a Prime Video-related issue or inquiry. The user's request for Odia movies and the response from the customer support team does not align with the assigned intent.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_music, echo_alexa, amazon_locker, grocery_fresh
- **Evidence**: @119625 you should add Odia movies in your content.... Many more people will happy with that., @643626 We will continue to add new content. Keep checking https://t.co/FYM9PIZOR8 where we highlight the latest movies and TV shows we have available. ^MN
- **Recommended Human Decision**: Review text and reassign to `product_availability` if appropriate.

## GS-086 - AMBIGUOUS
- **Current Label**: `digital_kindle`
- **Suggested Label**: `account_access`
- **Why Problematic**: The conversation starts with a question about the legitimacy of a website, which is unrelated to the assigned intent of digital_kindle. The mention of ads on Twitter and Facebook suggests a concern about account security or billing, which is more relevant to account_access.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_music, echo_alexa, amazon_locker, grocery_fresh
- **Evidence**: The conversation starts with a question about the legitimacy of a website., The mention of ads on Twitter and Facebook suggests a concern about account security or billing.
- **Recommended Human Decision**: Review text and reassign to `account_access` if appropriate.

## GS-087 - AMBIGUOUS
- **Current Label**: `digital_kindle`
- **Suggested Label**: `digital_kindle`
- **Why Problematic**: The assigned intent 'digital_kindle' is ambiguous because the customer's issue is related to account registration, which is not a typical use case for the 'digital_kindle' intent.
- **Competing Labels**: returns_refunds, product_availability, account_billing
- **Evidence**: The customer mentions deregistering their Kindle., The customer's issue is related to account registration, which is not a typical use case for the 'digital_kindle' intent.
- **Recommended Human Decision**: Review text and reassign to `digital_kindle` if appropriate.

## GS-090 - AMBIGUOUS
- **Current Label**: `digital_kindle`
- **Suggested Label**: `returns_refunds`
- **Why Problematic**: The conversation mentions a delivery issue and a wrong address, which doesn't align with the intent of a digital product like Kindle.
- **Competing Labels**: delivery_delayed, delivery_missing
- **Evidence**: The conversation mentions a delivery issue and a wrong address., The assigned intent doesn't match the context of the conversation.
- **Recommended Human Decision**: Review text and reassign to `returns_refunds` if appropriate.

## GS-095 - AMBIGUOUS
- **Current Label**: `digital_kindle`
- **Suggested Label**: `product_availability`
- **Why Problematic**: The conversation does not contain any clear indication of a Kindle-related issue, and the mention of 'order shows already ready to pick up' suggests a delivery-related issue.
- **Competing Labels**: delivery_delayed, delivery_missing
- **Evidence**: The conversation mentions a delivery issue., The mention of 'order shows already ready to pick up' suggests a delivery-related issue.
- **Recommended Human Decision**: Review text and reassign to `product_availability` if appropriate.

## GS-102 - AMBIGUOUS
- **Current Label**: `amazon_music`
- **Suggested Label**: `grocery_fresh`
- **Why Problematic**: The conversation starts with a question about Amazon Music Unlimited, but the context is unclear and could be related to other services.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_locker, grocery_fresh
- **Evidence**: The conversation starts with a question about Amazon Music Unlimited., The context is unclear and could be related to other services.
- **Recommended Human Decision**: Review text and reassign to `grocery_fresh` if appropriate.

## GS-106 - AMBIGUOUS
- **Current Label**: `amazon_music`
- **Suggested Label**: `grocery_fresh`
- **Why Problematic**: The conversation does not contain any clear indication of music-related intent, and the assigned intent does not match the context of the conversation.
- **Competing Labels**: delivery_delayed, delivery_missing, delivery_wrong_item
- **Evidence**: The text does not mention music or Alexa., The conversation is about a delivery issue and order details.
- **Recommended Human Decision**: Review text and reassign to `grocery_fresh` if appropriate.

