# Golden Set Repair Proposal

### Example: GS-006

**Conversation Text**:
> @244842 please explain where parcels pd74a000026 and pd74a000027 for @115830 are? one week later and i still await refunds. @495307 @115830 hi jag, your parcels are en-route back to amazon. here's the link to amazon's help page which is useful https://t.co/41piebasls @244842 @115830 over a week a later! how long does a simple return take? this is ridiculous - what is the maximum timescale? @495307 after the carrier has received your item, it can take up to 2 weeks for us to receive and process your return.  ^td

- Original intent: delivery_delayed
- Proposed intent: returns_refunds
- Evidence: refund mentioned
- Relevant taxonomy boundary: delivery_delayed vs returns_refunds
- Why original label is incorrect: Customer is waiting for money, not a package.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-009

**Conversation Text**:
> @115821.ca so apprently a 3 to 5 bussines days refund from you means 2 + weeks and counting, good know. seriously now happy with your customer service. @564183 i'm sorry for the frustration! are you able to see your refund status here: https://t.co/5wrq60kw24 ^ac @amazonhelp my refund claim is 2 weeks old. sorry dosn't exactly cut it. it was an issue on your end that caused the problem, i was told i had to wait, and i'm still waiting. @564183 can you tell us what information we provided about the refund? did we mention the cause of the error and if it was processed correctly since then? ^ez

- Original intent: delivery_delayed
- Proposed intent: returns_refunds
- Evidence: refund mentioned
- Relevant taxonomy boundary: delivery_delayed vs returns_refunds
- Why original label is incorrect: Customer is waiting for money, not a package.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-029

**Conversation Text**:
> @115850 the delivery may be delayed by a day due to the package arriving at an incorrect courier facility!
y does dis happen all da tym?😡😤 @491543 we've sent the correspondence to your registered email id. kindly check it here: https://t.co/8dac10s7ww ^gk

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-030

**Conversation Text**:
> @115833 trying to set up for the 1st time but the app says my amazon password is incorrect. no. it's not. any ideas? @158254 hey dave. please reach out - https://t.co/jzp7hla23b a member of our digital team will be happy to assist. keep us posted. ^tp

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-034

**Conversation Text**:
> @amazonhelp why can’t i get into my amazon account? it says my password is incorrect and i know it’s correct i changed it 3 times now @392732 please reach out to an account specialist. they can be reached by phone: 888-282-2406 or e-mail: https://t.co/sceypbira2 ^af

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-035

**Conversation Text**:
> @115830 what on earth is going on with my account? @418466 i'm sorry for the trouble! without any account info, could you please let us know a little more about what is going on? ^mo @amazonhelp placed an order, got an email to say there has been unauthorized access and to reset password, so i've tried to reset it multiple times @amazonhelp but i get an email to say it's successfully updated then try to log in and it says it is incorrect. how do i get my access back? @418466 we'd like to help sort this. when you have a moment, please contact us here: https://t.co/zyvx1qi29g ^ra

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-036

**Conversation Text**:
> @115821 you guys have sent me the wrong item twice in a row @319209 hi, sorry to hear that. was the order fulfilled by amazon or a 3rd party seller? what amazon website did you use to place the order? https://t.co/eytlxm7zz9? ^jj @amazonhelp it says "shipped and sold from amazon".  i'm using the android app @319209 thanks - please contact us so we can assist :  https://t.co/haplpmlfhn ^td

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-037

**Conversation Text**:
> @amazonhelp i ordered some stuff last night and i checked the recent orders tab and some of them are missing. should i reorder them or wait? @321984 i'd double check here first: https://t.co/y5jpi9grhe
if they are not there, then i'd say reorder! ^tr @amazonhelp now it says i can't log in? @amazonhelp yeah i changed my password and it still says it's incorrect @321984 thanks for letting us know! we feel we can provide the best assistance via phone or chat here: https://t.co/haplpmlfhn ^da

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-038

**Conversation Text**:
> @amazonhelp hi there, i've already reset my password and tried to sign in but it still says itis incorrect. email is __email__ @309422 i'm sorry you're having issues signing in. what site do you order from? .co.uk, .com or another? ^em @amazonhelp yes .co.uk @309422 thanks for the additional info! let's take a closer look with you in real time here: https://t.co/nghbef6slo ^jz

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-039

**Conversation Text**:
> @115850 , i had delivered an incorrect box for my order (#406-0293843-4945979) yesterday. possibly wrong labeling. delivery staff and his peers were unable to help on this. no response on your call center also. pls look into it. @735524 i'm sorry you've received the incorrect order. we certainly did not expect this to happen. i'd like to assist you with this. please provide your details here: https://t.co/cllwxc2hek. i'll look into it right away. please don't provide your order details via twitter, 1/2 @amazonhelp i had filled in the url, let me know on this asap @735524 thanks for the update. we've received your details and we'll get back to you at the earliest. ^sc @735524 as we consider it to be personal information. our page is visible to public. 2/2 ^ar

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-040

**Conversation Text**:
> @amazonhelp tried to highlight issues with being told the wrong thing 3 times by 3 different cs representatives and got yet another 1/2 @212238 hey! i'm really sorry you've had an experience like that. we'd love to help! can you tell us a little about what happened? ^aj @amazonhelp i ordered an item via amazon prime on thursday 5th october and it didn't arrive until today 9th october. i have now had 2 late prime @amazonhelp deliveries in the space of a week.when i emailed customer services i was told 3 completely different things by 3 different cs reps @amazonhelp all of which were incorrect. first i was told it was delivered (it wasn't), then i was told there was no tracking information (there was) @amazonhelp then i was told it was delivered to the wrong address (it wasn't - it arrived today). now i've been told by a 4th person that i am getting @amazonhelp a full refund because the order was delivered to the wrong address. it wasn't! it arrived today! @212238 i'm so sorry to hear about this trouble you've been experiencing! did the associates mention they would be leaving feedback? ^bg @amazonhelp no.the english in the emails is absolutely terrible and now i feel like i have committed mail fraud by getting a refund i did not ask for! @212238 this is an easy fix. please contact us again to confirm you've received the item, by phone or chat: https://t.co/haplpmlfhn ^st

- Original intent: delivery_wrong_item
- Proposed intent: account_access
- Evidence: password/login mentioned
- Relevant taxonomy boundary: delivery_wrong_item vs account_access
- Why original label is incorrect: Customer mentions digital access keywords, not physical wrong items.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-130

**Conversation Text**:
> has anyone ever been locked out of an @115821 account after a large purchase...? @520963 we'd like to help. have you received an e-mail from our account specialist team? be sure to check your junk/spam folder. ^nm

- Original intent: account_access
- Proposed intent: delivery_wrong_item
- Evidence: wrong item mentioned without login
- Relevant taxonomy boundary: account_access vs delivery_wrong_item
- Why original label is incorrect: Customer mentions wrong physical item, not digital access.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-136

**Conversation Text**:
> @amazonhelp hello there, i'vent received cashback in my amazon pay balance. and my mobile number is  blocked to get in touch with cc @115821 @523078 you can get in touch with us via email/chat/phone. please contact us here: https://t.co/hqhps2qeed. ^mn @amazonhelp thank you :-) @amazonhelp #amazon cc hang up the call and now not able to connect... what a pathetic customer care services. the worst i have ever seen @115851 @523078 my apologies for the experience. please fill in your details here: https://t.co/rtpz2hbj0e and we will get back to you. ^ks

- Original intent: account_access
- Proposed intent: delivery_wrong_item
- Evidence: wrong item mentioned without login
- Relevant taxonomy boundary: account_access vs delivery_wrong_item
- Why original label is incorrect: Customer mentions wrong physical item, not digital access.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

### Example: GS-159

**Conversation Text**:
> @amazonhelp hello, i ordered an item from you fro collection at a locker - but i have only recieved an empty cardboard sleeve. can you help? @800869 hi! we'll need to investigate this issue further. please contact us by phone or chat here: https://t.co/jzp7hla23b one of our representatives will be able to provide the best options available. let us know if you need anything! ^da

- Original intent: amazon_locker
- Proposed intent: delivery_missing
- Evidence: empty locker
- Relevant taxonomy boundary: amazon_locker vs delivery_missing
- Why original label is incorrect: Locker was accessed but contents missing.
- Why proposed label is correct: Text explicitly contains keywords mapped exclusively to the proposed intent.
- Confidence: HIGH
- Decision: REPAIR

