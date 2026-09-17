# Amazon Support Taxonomy Audit

## Overview
The selected brand is **Amazon**. The taxonomy is specifically tailored to Amazon customer support on Twitter (@AmazonHelp), covering e-commerce logistics, digital services (Prime Video, Kindle, Music), physical devices (Echo), and grocery (Fresh).

## Intent Definitions & Boundaries
### account_access (Count: 21)
- **Definition**: Issues logging in, password resets, locked accounts.
- **Boundary / Common Confusion**: Login and account lockouts. Billing issues inside an accessible account go to account_billing.
- **Example 1**: "@115850 The delivery may be delayed by a day due to the package arriving at an incorrect courier facility!
Y does dis happen all da tym?😡😤"
- **Example 2**: "@115833 Trying to set up for the 1st time but the app says my Amazon password is incorrect. no. it's not. any ideas?"

### returns_refunds (Count: 16)
- **Definition**: Requesting a refund, returning an item, checking refund status.
- **Boundary / Common Confusion**: Must explicitly involve returning a product or getting money back. If it's a billing dispute for a service, use account_billing.
- **Example 1**: "@244842 please explain where parcels PD74A000026 and PD74A000027 for @115830 are? One week later and I still await refunds."
- **Example 2**: "@115821.ca So apprently a 3 to 5 bussines days refund from you means 2 + weeks and counting, good know. Seriously now happy with your customer service."

### delivery_missing (Count: 15)
- **Definition**: Package marked delivered but not found, stolen packages.
- **Boundary / Common Confusion**: Only when package is marked delivered but not received. If not delivered yet, use delivery_delayed.
- **Example 1**: "@115850 just delivered me a broken room heater."
- **Example 2**: "@AmazonHelp A package meant for someone else was delivered to me by mistake. I've tried to contact then owner. How do I return to Amazon?"

### account_billing (Count: 14)
- **Definition**: Unrecognized charges, Prime membership billing, invoice requests.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "where the f*ck is my money???? @115821 i will singlehandedly destroy your reputation on this Website"
- **Example 2**: "@115850 Im not able to add money to AmazonPay thr DebitCard. Im being taken to same page after filling the info.#AmazonGreatIndianFestival https://t.co/nDJn8OGBmn"

### digital_prime_video (Count: 14)
- **Definition**: Prime Video streaming errors, renting/purchasing digital movies.
- **Boundary / Common Confusion**: Strictly digital streaming. Physical DVDs use delivery_delayed/wrong_item.
- **Example 1**: "Smart speaker. Smart living. #AskAlexa https://t.co/WLUjbFotDB"
- **Example 2**: "@181080 i can’t watch anything on amazon video or Netflix I keep getting a error it’s been like this for 2 days I checked my WiFi it’s fine"

### digital_kindle (Count: 14)
- **Definition**: Kindle device sync issues, missing e-books.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "where's my kindle💆🏽"
- **Example 2**: "@AmazonHelp - trying to purchase your kindle unlimited offer, but it keeps putting the price back to normal at checkout. Help??!! https://t.co/FXadyukjm7"

### amazon_music (Count: 14)
- **Definition**: Amazon Music Unlimited billing, playback issues.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "@115833 how am I supposed 2 know all of the commands I can give Alexa? I’m really not sure what to do with it besides weather/music/news"
- **Example 2**: "@AmazonHelp is Amazon Music down or something? The app opens, but nothing works. Even stuff I have downloaded doesn't work. Tried a restart."

### echo_alexa (Count: 14)
- **Definition**: Echo device troubleshooting, Alexa voice recognition issues.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "@115833 please teach Alexa slang. I've been trying to play Momentz by gorillaz for the last 30 minutes."
- **Example 2**: "Amazon EchoPlus良い。携帯でせっせと検索することなく、直感即時発声だけで曲がかかるのってすごい。ハードル低い。そういえばアレ聴きたいなって思った5秒後だもん。"

### promotions_pricing (Count: 14)
- **Definition**: Price matching, promotional code issues, discounts.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "@115850 what kind of joke is this ?? same product, with two different prices ??? and ur selling higher value saying its lighting deal !!! https://t.co/ApK0kFwLxf"
- **Example 2**: "WTF .. KAUNSA AISA COMPANY HAI JO 1290 MA 32GB SD CARD PRICE KARTHAI . STOP TRAPPING INNOCENT PEOPLE. @115850 https://t.co/Hbjmxdtf8r"

### grocery_fresh (Count: 14)
- **Definition**: Amazon Fresh or Whole Foods delivery issues, spoiled food.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "@115850 Change in account user interfaces is fine. But page wise listing of wish list was much better. This auto refresh is bad UX!"
- **Example 2**: "@115850 We ordered grocery from your pantry and my only concern is use of plastic for packaging. So much plastic? https://t.co/7TtmjM0su3"

### product_availability (Count: 14)
- **Definition**: Restock dates, pre-order status, stock inquiries.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "@121284 Can't change my device location to India. It is  only accepting US pincodes! Saavn says that service is not available here!"
- **Example 2**: "@AmazonHelp now waao see this message !! am waiting for my delivery all my numbers are working and the delivery boy's no was not available"

### amazon_locker (Count: 13)
- **Definition**: Locker codes not working, locker full, pickup issues.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "Prime Membership is waste. They want us to pick up from their location instead of delivering to doorstep @115850 @115821 Order #                         404-2427118-6554764 No use complaining through their customer call center. #Disapponted"
- **Example 2**: "Address is given for a reason. I am happy to help delivery guys w navigation, but unprofessional to insist I pick up the order @115850"

### delivery_delayed (Count: 12)
- **Definition**: Package has not arrived by promised date, tracking stalled.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: "Confused at how 2-day shipping means it arrives 7 days later @115821"
- **Example 2**: "@115821 does such a good job trying to keep customers happy. Shipment coming in late and they made it right. Thanks “Anita S” very prompt!"

### delivery_wrong_item (Count: 7)
- **Definition**: Received incorrect item, damaged item upon arrival.
- **Boundary / Common Confusion**: Standard isolation.
- **Example 1**: ".@AmazonHelp finally ended chat with customer support. Was I supported? No. Am I hopeful? No. Absolute waste of so much time... Await yet another email stating incorrect information... Huge abyss in their customer service!"
- **Example 2**: "@AmazonHelp I’ve had a delivery just now but it’s not what I ordered and paid for, what should I do?"

