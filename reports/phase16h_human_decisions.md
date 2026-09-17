# PHASE 16H — HUMAN TAXONOMY REVIEW


### GS-009
- **Current Golden Label**: `returns_refunds`
- **User Conversation**:
```
User: @115821.ca So apprently a 3 to 5 bussines days refund from you means 2 + weeks and counting, good know. Seriously now happy with your customer service.
User: @564183 I'm sorry for the frustration! Are you able to see your refund status here: https://t.co/5WRq60kw24 ^AC
User: @AmazonHelp My refund claim is 2 weeks old. Sorry dosn't exactly cut it. It was an issue on your end that caused the problem, I was told I had to wait, and I'm still waiting.
User: @564183 Can you tell us what information we provided about the refund? Did we mention the cause of the error and if it was processed correctly since then? ^EZ
```
- **Retrieved Top-3 Intents**: ['delivery_delayed', 'returns_refunds', 'delivery_delayed']
- **Retrieved similarity scores**: [0.9449585676193237, 0.9393183588981628, 0.939152181148529]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The current label 'returns_refunds' is too broad and does not capture the specific issue of delayed refunds.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The user mentions that the refund claim is 2 weeks old and they are still waiting, indicating a potential issue with the refund processing.
- **Evidence supporting competing label**: The user also mentions that the issue was on Amazon's end and they were told to wait, suggesting that the issue is related to the delivery or processing of the refund.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-017
- **Current Golden Label**: `delivery_missing`
- **User Conversation**:
```
User: @115850 you people are torturing me since last 3 days by not collecting the faulty phone that has been delivered to me by mistake 1/5
User: @268374 Sorry about the experience, Ajay. We have responded to your query here: https://t.co/Ghyge8BqMg. Please check. ^NK
```
- **Retrieved Top-3 Intents**: ['delivery_missing', 'delivery_missing', 'delivery_missing']
- **Retrieved similarity scores**: [0.9331766366958618, 0.9201962351799011, 0.9196209907531738]
- **V2 Prediction**: `amazon_locker`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `amazon_locker`
- **Why the case is ambiguous**: The classifier predicted 'amazon_locker' but the user's intent seems to be related to a missing delivery.
- **Relevant taxonomy definitions**: Determine whether the locker itself is the primary problem (e.g. broken, wrong code) or whether the missing package is the primary problem (e.g. tracking says delivered but locker is empty).
- **Evidence supporting current label**: The classifier predicted 'delivery_missing' three times, which may indicate a strong signal towards the issue.
- **Evidence supporting competing label**: The user's sentiment is negative (1/5) and they mention being 'tortured' by the issue, suggesting a stronger connection to the 'delivery_missing' label.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-027
- **Current Golden Label**: `delivery_missing`
- **User Conversation**:
```
User: @549653 Welcome to Prime, Sudarshan. I'm positive the product would be delivered according to the estimate. Please keep us posted.^KA
User: @AmazonHelp Loved the ease of shopping and checkout.
User: @549653 Delighted to know that. Do keep us posted for further issues or concerns. ^SB
User: @AmazonHelp Delivered bang in time. https://t.co/OGmzvgFyXQ
User: @549653 We're glad you've received the order. Wish you and your family a happy &amp; safe Diwali! 😊🎇 ^EM
```
- **Retrieved Top-3 Intents**: ['delivery_missing', 'delivery_missing', 'delivery_missing']
- **Retrieved similarity scores**: [0.9353843927383423, 0.9231410026550293, 0.9214577078819275]
- **V2 Prediction**: `amazon_locker`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `amazon_locker`
- **Why the case is ambiguous**: The classifier predicted 'amazon_locker' but the conversation contains multiple mentions of 'delivery_missing'. This suggests that the classifier may be overly specific or not capturing the full context of the conversation.
- **Relevant taxonomy definitions**: Determine whether the locker itself is the primary problem (e.g. broken, wrong code) or whether the missing package is the primary problem (e.g. tracking says delivered but locker is empty).
- **Evidence supporting current label**: The user explicitly mentions 'delivered bang in time' and shares a screenshot of the order confirmation, indicating that the product was delivered on time.
- **Evidence supporting competing label**: The user also mentions 'keep us posted for further issues or concerns', which could imply that there were some issues with the delivery.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-057
- **Current Golden Label**: `account_billing`
- **User Conversation**:
```
User: @115850 Im not able to add money to AmazonPay thr DebitCard. Im being taken to same page after filling the info.#AmazonGreatIndianFestival https://t.co/nDJn8OGBmn
User: @193112 Allow our support team to investigate this. You can report this here: https://t.co/R3EfhzgU8B ^CB.
```
- **Retrieved Top-3 Intents**: ['account_billing', 'account_billing', 'account_billing']
- **Retrieved similarity scores**: [0.9469398856163025, 0.9464626908302307, 0.9394469261169434]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'account_billing' but the context of the conversation suggests a different issue with the DebitCard payment.
- **Relevant taxonomy definitions**: Determine if the core issue is related to unexpected charges, payment methods, or Prime membership fees.
- **Evidence supporting current label**: The classifier retrieved ['account_billing', 'account_billing', 'account_billing'] which indicates a strong confidence in the label.
- **Evidence supporting competing label**: The user's issue with the DebitCard payment and the request to investigate suggests a different intent.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-064
- **Current Golden Label**: `account_billing`
- **User Conversation**:
```
User: Sir, price of your book Black money &amp; Tax heavens has doubled in last few hours on @115850 ..what's d actual price ? https://t.co/7DjCvtsLs1
User: @356321 The price you see are the lowest we are able to offer. You can check the price of the product here : https://t.co/bPZAnv9WLy.^GD
User: @AmazonHelp Did u even see the screenshot ? The price has increased more then 100 INR in last few hours..and u say its lowest ?? Smell some coffee..
User: @356321 The price and availability of the items and services offered on our website are subject to change. Adding an item (1/2)
User: @356321 or service to your Cart doesn't lock in the price of that item and it doesn't reserve the inventory available. ^SG(2/2)
```
- **Retrieved Top-3 Intents**: ['account_billing', 'account_billing', 'account_billing']
- **Retrieved similarity scores**: [0.9153305292129517, 0.9030941724777222, 0.9006351232528687]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The current label 'account_billing' is too broad and doesn't capture the specific issue of price increase, which is a more nuanced topic.
- **Relevant taxonomy definitions**: Determine if the core issue is related to unexpected charges, payment methods, or Prime membership fees.
- **Evidence supporting current label**: The conversation doesn't provide enough evidence to support the current label 'account_billing' as the primary intent.
- **Evidence supporting competing label**: The user's concern about the price increase and the need for a more specific label, such as 'price increase', is supported by the conversation.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-077
- **Current Golden Label**: `digital_prime_video`
- **User Conversation**:
```
User: @AmazonHelp my friend subscribed for Prime videos. Amt. has been deducted frm her accnt. But prime subscription is still not activated.
User: @465245 That's strange. Request the account holder to share the details here: https://t.co/beaaDm0muc and we'll check. ^GK
User: @AmazonHelp Thanks team. Spoke with customer care and it's resolved now.
User: @465245 We're happy to hear that the issue is resolved. Keep us posted, for further concerns. ^SC
```
- **Retrieved Top-3 Intents**: ['digital_prime_video', 'digital_prime_video', 'digital_prime_video']
- **Retrieved similarity scores**: [0.8938703536987305, 0.8895843029022217, 0.8851688504219055]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'digital_prime_video' for multiple conversations, indicating potential overfitting or lack of diversity in the training data.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The classifier predicted 'digital_prime_video' for 3 out of 3 conversations, suggesting a strong association between the label and the conversations.
- **Evidence supporting competing label**: The conversations do not provide clear evidence of the 'digital_prime_video' intent, as the user only reports an issue with their Prime Video subscription.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-084
- **Current Golden Label**: `digital_kindle`
- **User Conversation**:
```
User: where's my kindle💆🏽
User: @798774 Hi. Are you waiting on a delivery? What was the expected delivery date given at the time the order was placed? ^DC
```
- **Retrieved Top-3 Intents**: ['delivery_delayed', 'delivery_delayed', 'delivery_delayed']
- **Retrieved similarity scores**: [0.8410353660583496, 0.8402255177497864, 0.8387489318847656]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: RETRIEVAL_MISSING
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'other_support' but the context suggests a delivery issue, which is not a typical use case for 'other_support'.
- **Relevant taxonomy definitions**: Determine if the issue strictly pertains to Kindle devices or eBooks.
- **Evidence supporting current label**: ['delivery_delayed', 'delivery_delayed', 'delivery_delayed']
- **Evidence supporting competing label**: The user asked for the location of their Kindle, which is a common query for a delivery issue.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-086
- **Current Golden Label**: `digital_kindle`
- **User Conversation**:
```
User: @amazonhelp @44867 is this site legit? I'm seeing ads on Twitter &amp; Facebook.. Thanks

https://t.co/gt3cPmEqUP
User: @529488 Thanks for bringing this to our attention. This is not an official Amazon account page. I’ve reported it to the appropriate team. ^LI
```
- **Retrieved Top-3 Intents**: ['account_billing', 'account_billing', 'account_billing']
- **Retrieved similarity scores**: [0.85796719789505, 0.8537827134132385, 0.8530888557434082]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: RETRIEVAL_MISSING
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'other_support' but the context suggests it's a phishing attempt.
- **Relevant taxonomy definitions**: Determine if the issue strictly pertains to Kindle devices or eBooks.
- **Evidence supporting current label**: The classifier retrieved ['account_billing'] which is not a typical intent for a phishing attempt.
- **Evidence supporting competing label**: The user's question about the legitimacy of the site and the presence of ads on Twitter & Facebook suggests a phishing attempt.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-096
- **Current Golden Label**: `digital_kindle`
- **User Conversation**:
```
User: @115830, I am trying to buy an Italian ebook - La gente by Bianchi - but I can't just because I am in the UK? How's that possible? It's an ebook, not a paperback? It would be great if you could let me know if there is anyway I can buy it (ebook only)
User: @280803 Hi There, I am sorry to hear this! could you please send us a link to the ebook? ^HS
User: @AmazonHelp Hi, thanks for the quick reply. The italian link is the following https://t.co/SfY8Nmq831
User: @280803 What error message are you receiving when purchasing the ebook?^CN
User: @AmazonHelp I cannot buy the ebook because it's only available on amazon.it in which I can't purchase because my account is in the UK. If I search it on https://t.co/5JeCbiv3lj no results are available. Is there a way in which you could get the book on https://t.co/7ZmjRmPlGB
User: @280803 I am sorry to hear this. Just to note you can access the Amazon.it website with the same login credentials as the AmazonUK website. Can I ask what item you are searching for please?^GA
User: @AmazonHelp Hi, I can access but I can't buy ebook in the italian Amazon, only in the UK and US ones. It's an ebook, La Gente by Bianchi. I do not want to buy paperback just ebook for kindle!
User: @280803 Please contact our Customer Service for help by clicking here: https://t.co/u32OIkkndA. ^MZ
```
- **Retrieved Top-3 Intents**: ['digital_kindle', 'digital_kindle', 'digital_kindle']
- **Retrieved similarity scores**: [0.906688928604126, 0.9011340737342834, 0.8993411064147949]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'digital_kindle' but the correct label is 'other_support'.
- **Relevant taxonomy definitions**: Determine if the issue strictly pertains to Kindle devices or eBooks.
- **Evidence supporting current label**: The classifier predicted 'digital_kindle' three times, indicating a strong confidence in this label.
- **Evidence supporting competing label**: The customer's intent is to purchase an ebook, not a digital_kindle specifically.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-122
- **Current Golden Label**: `echo_alexa`
- **User Conversation**:
```
User: Today we're celebrating Alexa's 3rd birthday. 🎂 🎁🎈 #HBDAlexa https://t.co/dD0mE0be1D
User: @116439 @115833 Seriously, why does she tell us " the happy birthday app is no longer enabled"? Why the big ad campaign with no payoff here at home?
User: @518122 Hey there! Have you enabled the skill? You can learn more about enabling Alexa skills here: https://t.co/4jjBvcBduG ^GM
User: @AmazonHelp My opinion: happy birthday on her birthday should be a standard prompt like "good morning"&amp; "thank you" it should elicit a response from her
User: @AmazonHelp Looking at the apps I can't even tell which would be the official birthday app.  Now it says " the skill is not available right now"
User: @AmazonHelp she's getting the others but " happy birthday" is the one that just doesn't work. Weird.( We've tried all three units with same results) https://t.co/b8RZJl9inJ
```
- **Retrieved Top-3 Intents**: ['echo_alexa', 'delivery_delayed', 'echo_alexa']
- **Retrieved similarity scores**: [0.9200084805488586, 0.9176813364028931, 0.9162073731422424]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'echo_alexa' but the retrieved intents were ['echo_alexa', 'delivery_delayed', 'echo_alexa']
- **Relevant taxonomy definitions**: Determine if the issue strictly pertains to Alexa/Echo devices.
- **Evidence supporting current label**: The classifier predicted 'echo_alexa' which is a valid intent
- **Evidence supporting competing label**: The retrieved intents included 'delivery_delayed' which is not a valid intent for this conversation
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-123
- **Current Golden Label**: `echo_alexa`
- **User Conversation**:
```
User: There is certain expectation from @115821 , please do not let down customers with such low quality speakers on Echo plus @AmazonHelp
User: @127217 I'm sorry to know that the device wasn't as expected. I'll certainly forward your feedback to the relevant team. ^EM
User: @AmazonHelp Let me know once have better speakers on Echo Plus I may once again try my luck. As of now disappointed as it is not expected from @115821
User: @127217 I get your concern, we've passed on your feedback internally. ^PS
```
- **Retrieved Top-3 Intents**: ['echo_alexa', 'echo_alexa', 'amazon_music']
- **Retrieved similarity scores**: [0.9324939250946045, 0.9287726879119873, 0.9253297448158264]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier prediction 'echo_alexa' is not specific enough to capture the intent of the conversation, as it is also present in the 'amazon_music' intent.
- **Relevant taxonomy definitions**: Determine if the issue strictly pertains to Alexa/Echo devices.
- **Evidence supporting current label**: The classifier prediction 'echo_alexa' is a valid intent, but it is not the primary intent of the conversation.
- **Evidence supporting competing label**: The user explicitly mentions 'Echo Plus' and expresses disappointment with the device's speakers, suggesting a more specific intent.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-124
- **Current Golden Label**: `echo_alexa`
- **User Conversation**:
```
User: Porqué @116928 tarda tanto en tomar un pedido 😨
User: @299203 Lamento cualquier inconveniente, Lichis, ¿Podrías comentarnos más sobre lo que ha ocurrido sin publicar detalles de tu cuenta? ^AZ
User: @AmazonHelp Ordene por su web el martes! Y no me han hecho el cargo a mi tarjeta, y mi pedido sigue pendiente!
User: @299203 Lichis, ¿cuál es la fecha estimada de entrega de tu pedido? ^LG
User: @AmazonHelp Únicamente dice Fecha estimada pendiente!!
User: @299203 Lichis, ¿verificaste la disponibilidad de los productos (https://t.co/AqWMye8QMq)? ^HC
```
- **Retrieved Top-3 Intents**: ['product_availability', 'account_access', 'echo_alexa']
- **Retrieved similarity scores**: [0.9002453088760376, 0.8712779879570007, 0.8707875609397888]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: classifier prediction mismatch
- **Relevant taxonomy definitions**: Determine if the issue strictly pertains to Alexa/Echo devices.
- **Evidence supporting current label**: ['product_availability', 'account_access', 'echo_alexa']
- **Evidence supporting competing label**: ['other_support']
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-128
- **Current Golden Label**: `account_access`
- **User Conversation**:
```
User: @115830 Really poor delivery service today. Saw van arrive when upstairs, by time I'd come down the van had driven off. No attempt to open the unlocked gates or place in the mail box at roadside.
User: @505085 I do apologize about this experience! Please give us a ring so we can look into this with you: https://t.co/JzP7hlA23B ^TR
```
- **Retrieved Top-3 Intents**: ['account_access', 'delivery_delayed', 'account_access']
- **Retrieved similarity scores**: [0.8716715574264526, 0.8532477617263794, 0.8488761782646179]
- **V2 Prediction**: `delivery_wrong_item`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `delivery_wrong_item`
- **Why the case is ambiguous**: The classifier predicted 'delivery_wrong_item' but the current label is 'account_access'. This suggests that the classifier may have misclassified the conversation.
- **Relevant taxonomy definitions**: Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution.
- **Evidence supporting current label**: The customer service response acknowledges the issue and offers to look into it, indicating that the customer's concern is being taken seriously.
- **Evidence supporting competing label**: The classifier predicted 'delivery_wrong_item' which implies that the customer is reporting a problem with the delivery, but the current label 'account_access' suggests that the issue is with account access rather than delivery.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-139
- **Current Golden Label**: `account_access`
- **User Conversation**:
```
User: @AmazonHelp hello my account has been blocked due to security reasons I tried to buy £20 on Xbox and it was pending verification
User: @650920 Did you receive an email from one of our Account Specialists? ^SH
User: @AmazonHelp Not yet
User: @650920 When an account is put on hold, an e-mail with more information is sent out. Have you checked your junk/spam folder? ^MJ
User: @AmazonHelp Oh I got one telling me to fax them I haven't even seen a fax in real life before!
```
- **Retrieved Top-3 Intents**: ['account_access', 'account_access', 'account_access']
- **Retrieved similarity scores**: [0.9017435312271118, 0.8891456127166748, 0.8843434453010559]
- **V2 Prediction**: `delivery_wrong_item`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `delivery_wrong_item`
- **Why the case is ambiguous**: The current label 'account_access' may be problematic because the conversation is about a blocked account due to security reasons, which doesn't directly relate to the issue of a pending verification for a wrong item.
- **Relevant taxonomy definitions**: Determine whether the customer's primary objective is account recovery (cannot log in) or delivery resolution.
- **Evidence supporting current label**: The conversation mentions a blocked account and security reasons, which doesn't align with the typical intent of 'account_access'.
- **Evidence supporting competing label**: The conversation mentions a pending verification for a wrong item, which is more closely related to the intent of 'delivery_wrong_item'.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-141
- **Current Golden Label**: `promotions_pricing`
- **User Conversation**:
```
User: WTF .. KAUNSA AISA COMPANY HAI JO 1290 MA 32GB SD CARD PRICE KARTHAI . STOP TRAPPING INNOCENT PEOPLE. @115850 https://t.co/Hbjmxdtf8r
User: @165811 We constantly receive new data from our suppliers &amp; our prices are set by the sellers. (2/2) ^AS
User: @165811 As Amazon.in is a marketplace, the products are sold by individual sellers/suppliers. (1/2) ^AS
```
- **Retrieved Top-3 Intents**: ['delivery_delayed', 'promotions_pricing', 'promotions_pricing']
- **Retrieved similarity scores**: [0.8951706886291504, 0.8792407512664795, 0.8781062364578247]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The current label 'promotions_pricing' is too broad and does not accurately capture the intent of the conversation.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The conversation mentions a specific product price, which suggests a focus on pricing information.
- **Evidence supporting competing label**: The conversation also mentions a complaint about a company, which suggests a focus on customer service or support.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-144
- **Current Golden Label**: `promotions_pricing`
- **User Conversation**:
```
User: @115850 @115851 
Totally unprofessional, bought Xbox on preorder offer, CC team refused any such promo existed, 10 days  no resolution. https://t.co/bNlpeOujdC
User: @444428 Apologies, That was not intended. Please share your details here: https://t.co/GIJyeYqKE0 &amp; we'll get in touch with you. ^BS
```
- **Retrieved Top-3 Intents**: ['promotions_pricing', 'delivery_missing', 'delivery_missing']
- **Retrieved similarity scores**: [0.9012398719787598, 0.8811377882957458, 0.8809977173805237]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'other_support' but the conversation is related to a promotion pricing issue.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The conversation mentions a preorder offer and a promo code, which suggests a pricing promotion issue.
- **Evidence supporting competing label**: The conversation also mentions a delay in resolution, which could be related to a delivery issue.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-150
- **Current Golden Label**: `promotions_pricing`
- **User Conversation**:
```
User: @6326 vous pouvez me dire en quoi c’est une promo ? Ça s’appellerait pas par hasard gonfler ses prix avant promo pour faire croire à une remise ? @120533 vous êtes pareil ! #BlackFriday2017 https://t.co/R0oZWY96FW
User: @147033 Bonjour, pouvez-vous me fournir le lien de l'article sur notre site s'il vous plaît ? ^AR
User: @AmazonHelp https://t.co/uXk7h5QNDa  encore une remise de 11% fictive ! Le vrai prix est déjà de 1329,99€
User: @AmazonHelp Pas de réponse ! Apparemment c’est normal comme pratique @6326
User: @147033 Est-ce que vous avez une idée si le prix affiché sur le site du constructeur (Gopro), est sous promotion ou non ? ^AR
```
- **Retrieved Top-3 Intents**: ['promotions_pricing', 'promotions_pricing', 'promotions_pricing']
- **Retrieved similarity scores**: [0.9370699524879456, 0.9244974255561829, 0.9241569638252258]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The current label 'promotions_pricing' may be too broad and does not accurately capture the specific issue of pricing manipulation.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The user's concern about the price being 'fictive' and the mention of 'gonfler ses prix avant promo' suggest that the issue is related to pricing manipulation.
- **Evidence supporting competing label**: The alternative label 'promotions_pricing' does not account for the specific context of pricing manipulation.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-159
- **Current Golden Label**: `delivery_missing`
- **User Conversation**:
```
User: @AmazonHelp Hello, I ordered an item from you fro collection at a locker - but I have only recieved an empty cardboard sleeve. Can you help?
User: @800869 Hi! We'll need to investigate this issue further. Please contact us by phone or chat here: https://t.co/JzP7hlA23B One of our representatives will be able to provide the best options available. Let us know if you need anything! ^DA
```
- **Retrieved Top-3 Intents**: ['delivery_missing', 'amazon_locker', 'amazon_locker']
- **Retrieved similarity scores**: [0.903884768486023, 0.899826169013977, 0.8944842219352722]
- **V2 Prediction**: `amazon_locker`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `amazon_locker`
- **Why the case is ambiguous**: The classifier predicted two labels ('delivery_missing' and 'amazon_locker') which is more than one label, indicating potential ambiguity.
- **Relevant taxonomy definitions**: Determine whether the locker itself is the primary problem (e.g. broken, wrong code) or whether the missing package is the primary problem (e.g. tracking says delivered but locker is empty).
- **Evidence supporting current label**: The classifier predicted 'amazon_locker' which is a specific intent, but the user's question is more general ('I ordered an item from you fro collection at a locker')
- **Evidence supporting competing label**: The classifier predicted 'delivery_missing' which is a more general intent, but the user's question is specific to a missing item from a locker
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-164
- **Current Golden Label**: `amazon_locker`
- **User Conversation**:
```
User: Do you ever get so angry at something so stupid that it's not even worth the effort? I don't, usually, but @115821 - you suck. USPS can't deliver a BOOK in my mailbox or at the house? Failed attempt? I'm supposed to chase it down now? Really. Not so #Prime.
User: @725306 I hate to hear of any trouble getting your package, Sherri! Usually missed deliveries are attempted again the next business day. Has it been more than one day since the delivery was failed? Let us know! We want to be sure you receive your package. ^MT
User: @AmazonHelp Very frustrating-- "You can reschedule the delivery by visiting USPS Redelivery or you can pick up your package from the post office listed on the notice of attempted delivery." 2nd time in recent weeks. Guess we'll see today. How can USPS fail to put a BOOK in the mailbox?!
User: @AmazonHelp This is not #Prime service.
```
- **Retrieved Top-3 Intents**: ['amazon_locker', 'delivery_missing', 'delivery_delayed']
- **Retrieved similarity scores**: [0.8583084344863892, 0.8561914563179016, 0.8504761457443237]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CONFLICTING_EVIDENCE
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The current label 'amazon_locker' is not directly related to the issue of a missing package, while the label 'delivery_missing' is more relevant to the problem.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The label 'amazon_locker' is a specific type of delivery location, whereas 'delivery_missing' is a more general term for the issue of a package not being delivered.
- **Evidence supporting competing label**: The label 'delivery_missing' is supported by the context of the conversation, where the customer is frustrated with a missed delivery and is seeking assistance.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-174
- **Current Golden Label**: `grocery_fresh`
- **User Conversation**:
```
User: @115821 any idea when this order will arrive? I have a sassy Brit since grocery stopped carrying his @118826 #teatime #isthisatrick https://t.co/wb8uMOsjcW
User: @118825 I'm sorry there was a delay! Let us know if your package doesn't arrive by November 2. Please keep us posted on its delivery. ^TN
```
- **Retrieved Top-3 Intents**: ['delivery_delayed', 'delivery_missing', 'delivery_delayed']
- **Retrieved similarity scores**: [0.8763971924781799, 0.8600615859031677, 0.8527288436889648]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: RETRIEVAL_MISSING
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'other_support' but the Golden Label is 'grocery_fresh'. This suggests that the current label may not accurately capture the intent of the conversation.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The classifier predicted 'other_support' which is a more general label that may not be specific enough to capture the intent of the conversation.
- **Evidence supporting competing label**: The Golden Label 'grocery_fresh' suggests that the intent of the conversation is related to grocery delivery, which is not captured by the 'other_support' label.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-178
- **Current Golden Label**: `grocery_fresh`
- **User Conversation**:
```
User: @115850 is so pathetic that it says guaranteed delivery by 11 AM tomorrow for a fresh order but cant deliver an order placed on 25th oct
User: @478782 Did you report this to our customer service team here: https://t.co/vlvfJrlYEH? ^SI
User: @AmazonHelp Yes 33 times but no one @115850 even takes the initiative to resolve issues just lie...pathetic service will never place an order with
User: @AmazonHelp @115850 No one even took the initiative to give me a call after so much hassle @118919 @115850 @115830 @AmazonHelp
```
- **Retrieved Top-3 Intents**: ['delivery_missing', 'delivery_delayed', 'delivery_delayed']
- **Retrieved similarity scores**: [0.8562769293785095, 0.8502965569496155, 0.8501577377319336]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: RETRIEVAL_MISSING
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'other_support' but the conversation context suggests a different intent.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The classifier predicted 'other_support' but the conversation context does not support this intent.
- **Evidence supporting competing label**: The conversation context suggests a 'delivery_missing' intent, as the user reports a guaranteed delivery promise not being met.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-182
- **Current Golden Label**: `product_availability`
- **User Conversation**:
```
User: @121284 Can't change my device location to India. It is  only accepting US pincodes! Saavn says that service is not available here!
User: @449425 Sorry to know you're having trouble changing the location. Kindly connect with us here: https://t.co/HQhpS2qeEd. We'll help. ^PS
```
- **Retrieved Top-3 Intents**: ['product_availability', 'product_availability', 'product_availability']
- **Retrieved similarity scores**: [0.8869276642799377, 0.8764824867248535, 0.8705329298973083]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'product_availability' but the context suggests a different issue (device location change).
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: ['product_availability', 'product_availability', 'product_availability']
- **Evidence supporting competing label**: The user's issue is related to device location change, which is not covered by the 'product_availability' label.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-186
- **Current Golden Label**: `product_availability`
- **User Conversation**:
```
User: @AmazonHelp if I pre-order an mp3 album and I have a giftcard balance, will it automatically take it off when I order it? it's not showing
User: @305178 We charge as songs or the album are released. For more details, please click here: https://t.co/ErE5xqdYyZ ^JR
```
- **Retrieved Top-3 Intents**: ['account_billing', 'account_billing', 'amazon_music']
- **Retrieved similarity scores**: [0.8720964789390564, 0.863773763179779, 0.8626340627670288]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: RETRIEVAL_MISSING
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'other_support' but the Golden Label is 'product_availability'. This suggests that the current label may not accurately capture the intent of the user's question.
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: The classifier predicted 'account_billing' as the alternative label, which is related to account-related topics, but the user's question is about product availability.
- **Evidence supporting competing label**: The Golden Label 'product_availability' is more relevant to the user's question about the availability of the pre-ordered album.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---

### GS-189
- **Current Golden Label**: `product_availability`
- **User Conversation**:
```
User: @AmazonHelp is there a way to check why 2 orders keep having their delivery dates pushed back? Item shows as in-stock, and it’s been a month since the order was placed.
User: @449947 I'm sorry to hear about the delay with your order! Have you received any messages regarding the delay? You can check here: https://t.co/Xl6oQRQ1sb ^MW
User: @AmazonHelp No message. The expected shipping/delivery date just changes in my list of orders.
User: @449947 We can have a further look into this with you. Please use the following link so that we may do so: https://t.co/hApLpMlfHN ^DO
```
- **Retrieved Top-3 Intents**: ['product_availability', 'product_availability', 'product_availability']
- **Retrieved similarity scores**: [0.9304636716842651, 0.929894208908081, 0.9276256561279297]
- **V2 Prediction**: `other_support`
- **Whether V2 was correct**: False
- **Failure category**: CLASSIFIER_IGNORED_CORRECT
- **Competing intent(s)**: `other_support`
- **Why the case is ambiguous**: The classifier predicted 'product_availability' three times, indicating a high confidence in this label, but the context of the conversation suggests a different issue (delayed delivery).
- **Relevant taxonomy definitions**: Examine the conversation to determine which label captures the customer's primary actionable request.
- **Evidence supporting current label**: ['product_availability', 'product_availability', 'product_availability']
- **Evidence supporting competing label**: The conversation context suggests a delayed delivery issue, not a product availability issue.
- **Recommended human decision options**: KEEP_CURRENT_LABEL, CHANGE_LABEL, AMBIGUOUS_KEEP, INSUFFICIENT_CONTEXT
---
