# Taxonomy Boundary Audit

## Step 1: Reconstructed Taxonomy Boundaries

### `delivery_delayed`
- **Means**: Order is late or tracking hasn't updated, but is NOT marked delivered.
- **Positive indicators**: "late", "delay", "not arrived", "still waiting".
- **Negative indicators**: "says delivered", "refund", "empty box".
- **Closest competing**: `delivery_missing`, `returns_refunds`.
- **Determining signal**: Status of the tracking. If tracking is in transit/delayed, it's this intent.
- **Clear case**: "My package was supposed to arrive yesterday but tracking says it's delayed in transit."

### `delivery_missing`
- **Means**: Order marked as delivered but customer does not have the items, or box arrived empty/stolen.
- **Positive indicators**: "says delivered but not here", "stolen", "empty box".
- **Negative indicators**: "wrong item", "late", "still in transit".
- **Closest competing**: `delivery_delayed`, `delivery_wrong_item`, `amazon_locker`.
- **Determining signal**: Tracking says delivered, but package/contents are completely missing.
- **Clear case**: "Amazon says my package was delivered to the porch, but I checked and there's nothing there."

### `delivery_wrong_item`
- **Means**: Package arrived but contains incorrect merchandise.
- **Positive indicators**: "wrong item", "incorrect", "not what I ordered".
- **Negative indicators**: "empty box", "broken", "defective".
- **Closest competing**: `delivery_missing`, `returns_refunds`, `account_access`.
- **Determining signal**: Customer has physical possession of a product they did not order.
- **Clear case**: "I ordered a book but received a pair of shoes instead."

### `returns_refunds`
- **Means**: Returning an item or inquiring about a refund status.
- **Positive indicators**: "return", "refund", "defective", "broken".
- **Negative indicators**: "late", "unauthorized charge".
- **Closest competing**: `delivery_delayed`, `account_billing`.
- **Determining signal**: A physical product was/is being returned, or a refund for a specific product is expected/missing.
- **Clear case**: "I sent my defective vacuum back last week but haven't received my refund."

### `product_availability`
- **Means**: Asking if/when an item will be in stock.
- **Positive indicators**: "out of stock", "pre-order", "available".
- **Negative indicators**: "tracking", "late".
- **Closest competing**: `delivery_delayed`.
- **Determining signal**: Item has not yet been shipped or cannot be purchased yet.
- **Clear case**: "When will the new Playstation be back in stock?"

### `promotions_pricing`
- **Means**: Price matching, discounts, coupons.
- **Positive indicators**: "discount", "promo", "price match", "coupon".
- **Negative indicators**: "subscription fee", "charged me".
- **Closest competing**: `account_billing`.
- **Determining signal**: Inquiry relates to the purchase price of an item, not a recurring account charge.
- **Clear case**: "My 20% off promo code isn't working at checkout."

### `account_billing`
- **Means**: Recurring subscription fees, bank charges, or unknown/unauthorized charges.
- **Positive indicators**: "charge", "billed", "unauthorized", "bank", "subscription".
- **Negative indicators**: "refund for my return", "promo".
- **Closest competing**: `returns_refunds`, `promotions_pricing`.
- **Determining signal**: Focus on the financial transaction itself, usually independent of a physical product return (e.g. Prime renewal, fraud).
- **Clear case**: "I see a $139 charge on my credit card for Prime but I didn't sign up."

### `account_access`
- **Means**: Customer cannot log into their account/app, or account security issues.
- **Positive indicators**: "login", "password", "locked", "app crashing".
- **Negative indicators**: "wrong item", "locker code".
- **Closest competing**: `delivery_wrong_item`, `amazon_locker`.
- **Determining signal**: The issue is digital access to the Amazon account or app functionality.
- **Clear case**: "I keep getting an incorrect password error when trying to log into the app."

### `digital_prime_video`
- **Means**: Prime Video streaming, playback, or purchases.
- **Positive indicators**: "video", "movie", "streaming", "playback".
- **Negative indicators**: "music", "kindle".
- **Closest competing**: `digital_kindle`, `amazon_music`.
- **Determining signal**: Mention of video content or streaming.
- **Clear case**: "My Prime Video app keeps buffering while watching a movie."

### `digital_kindle`
- **Means**: Kindle devices, eBooks, or Kindle Unlimited.
- **Positive indicators**: "kindle", "ebook", "paperwhite".
- **Negative indicators**: "echo", "alexa".
- **Closest competing**: `digital_prime_video`, `echo_alexa`.
- **Determining signal**: Mention of books or e-readers.
- **Clear case**: "My new eBook won't download to my Paperwhite."

### `amazon_music`
- **Means**: Amazon Music app, playlists, or songs.
- **Positive indicators**: "music", "song", "playlist".
- **Negative indicators**: "video", "ebook".
- **Closest competing**: `digital_prime_video`.
- **Determining signal**: Mention of audio tracks or the music app.
- **Clear case**: "My offline playlist disappeared from Amazon Music."

### `echo_alexa`
- **Means**: Echo devices or Alexa voice assistant issues.
- **Positive indicators**: "echo", "alexa", "dot".
- **Negative indicators**: "kindle".
- **Closest competing**: `digital_kindle`.
- **Determining signal**: Mention of voice assistant or smart speaker hardware.
- **Clear case**: "My Alexa isn't responding to my voice commands."

### `amazon_locker`
- **Means**: Physical locker pickup or access issues.
- **Positive indicators**: "locker", "access code", "pick up".
- **Negative indicators**: "empty box", "app password".
- **Closest competing**: `delivery_missing`, `account_access`.
- **Determining signal**: The issue specifically involves retrieving a package from an Amazon Hub Locker location using a code/app.
- **Clear case**: "The locker access code you emailed me isn't opening the door."

### `grocery_fresh`
- **Means**: Amazon Fresh or Whole Foods delivery issues.
- **Positive indicators**: "fresh", "whole foods", "grocery", "spoiled".
- **Negative indicators**: "locker", "digital".
- **Closest competing**: `delivery_wrong_item`, `delivery_missing`.
- **Determining signal**: Mentions of food, groceries, or specific Fresh delivery windows.
- **Clear case**: "My groceries arrived but the milk was spoiled."

---

## Step 2: Confusion Pair Analysis

### A. `account_access` vs `delivery_wrong_item`
1. **Semantic Distinction**: Digital credentials/app errors vs physical incorrect merchandise.
2. **Minimum Evidence**: Mention of "app", "password", or "login" signals `account_access`. Mention of receiving a physical item signals `delivery_wrong_item`.
3. **Strong Indicators**: "password incorrect", "app crashing" (`account_access`) vs "received a phone case instead", "wrong size" (`delivery_wrong_item`).
4. **Genuinely Ambiguous**: "The information is wrong." (Needs context to know if it's login info or order info).
5. **Taxonomy Insufficiency**: If an app crash *causes* a wrong order to be placed.

| Intent A (`account_access`) | Intent B (`delivery_wrong_item`) | Distinguishing Signal | Ambiguous When |
|---|---|---|---|
| "My password says incorrect" | "I got the incorrect item" | Digital access vs physical possession | Customer says "The info is wrong" |

### B. `amazon_locker` vs `delivery_missing`
1. **Semantic Distinction**: Logistics of locker access vs the package not being in the expected location.
2. **Minimum Evidence**: Issues with scanning a barcode or typing a pin is `amazon_locker`. Opening a locker to find nothing is `delivery_missing`.
3. **Strong Indicators**: "barcode won't scan", "expired code" (`amazon_locker`) vs "door opened but it was empty", "stolen" (`delivery_missing`).
4. **Genuinely Ambiguous**: "I can't get my package from the locker." (Is the locker broken, or is the package not there?)
5. **Taxonomy Insufficiency**: If the locker code works, but the locker door is jammed.

| Intent A (`amazon_locker`) | Intent B (`delivery_missing`) | Distinguishing Signal | Ambiguous When |
|---|---|---|---|
| "Access code failed" | "Locker was empty" | Technical locker failure vs missing goods | "Can't get my package at the locker" |

### C. `delivery_delayed` vs `returns_refunds`
1. **Semantic Distinction**: Waiting for an outbound physical shipment vs waiting for an inbound refund/return process.
2. **Minimum Evidence**: "Tracking" of a purchased item is `delivery_delayed`. "Refund" or "return" is `returns_refunds`.
3. **Strong Indicators**: "Still in transit", "arriving late" (`delivery_delayed`) vs "refund to my card", "return label" (`returns_refunds`).
4. **Genuinely Ambiguous**: "Where is my replacement?" (Replacement orders straddle returns and new deliveries).
5. **Taxonomy Insufficiency**: A delayed refund check sent via physical mail.

| Intent A (`delivery_delayed`) | Intent B (`returns_refunds`) | Distinguishing Signal | Ambiguous When |
|---|---|---|---|
| "Where is my package?" | "Where is my money?" | Physical item delay vs Financial processing delay | "Where is my replacement?" |
