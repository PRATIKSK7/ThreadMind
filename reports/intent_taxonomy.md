# AmazonHelp Intent Taxonomy

This evidence-driven taxonomy was generated deterministically from the 82,556 processed AmazonHelp conversational threads using TF-IDF and keyword grouping. 

## 1. Delivery & Fulfillment
### Intent ID: `delivery_delayed`
- **Intent Name**: Delayed Delivery
- **Definition**: Customer inquiring about an order that has not arrived by the expected date, or a tracking number that has not updated.
- **Inclusion Criteria**: Explicit mention of lateness, delays, or tracking issues.
- **Exclusion Criteria**: Packages marked as delivered (see `delivery_missing`).
- **Positive Example**: `7ebe0465070f9b90`
- **Resolution Pattern**: Apology, explanation of delay, or request for order tracking number.
- **Escalation Considerations**: Low escalation unless the delay is extreme or the customer is irate.
- **Evidence**: 5,012 supporting threads.

### Intent ID: `delivery_missing`
- **Intent Name**: Missing / Stolen Package
- **Definition**: The tracking claims the item was delivered, but the customer cannot find it.
- **Inclusion Criteria**: "Says delivered but not here", stolen packages, empty boxes.
- **Exclusion Criteria**: Delayed items that do not say delivered.
- **Positive Example**: `2eec3ef84ac463eb`
- **Resolution Pattern**: Instructions to wait 24 hours, check around the property, or offer a replacement.
- **Escalation Considerations**: Medium escalation, especially if high-value items are reported stolen.
- **Evidence**: 1,549 supporting threads.

### Intent ID: `delivery_wrong_item`
- **Intent Name**: Wrong / Incorrect Item
- **Definition**: The customer received a package but it contained the wrong product.
- **Inclusion Criteria**: "Not what I ordered", incorrect item.
- **Exclusion Criteria**: Defective items (see `returns_refunds`).
- **Positive Example**: `2429e4f53edf4fae`
- **Resolution Pattern**: Apology and return authorization.
- **Escalation Considerations**: Medium.
- **Evidence**: 562 supporting threads.

## 2. Orders & Returns
### Intent ID: `returns_refunds`
- **Intent Name**: Returns & Refunds
- **Definition**: Requesting a refund, returning an item, or asking for a return label.
- **Inclusion Criteria**: Mentions of refunds, return windows, defective products, or return labels.
- **Exclusion Criteria**: Missing packages where a refund hasn't explicitly been discussed yet.
- **Positive Example**: `f23d3ee4b25f4a56`
- **Resolution Pattern**: Providing instructions to access the Returns Center.
- **Escalation Considerations**: Low, unless a refund has taken longer than the stated 3-5 business days.
- **Evidence**: 8,068 supporting threads.

### Intent ID: `product_availability`
- **Intent Name**: Product Availability
- **Definition**: Inquiries about when an out-of-stock item will be available or pre-order status.
- **Inclusion Criteria**: "Out of stock", "pre-order", "when will this be available".
- **Exclusion Criteria**: Questions about shipping speed of an in-stock item.
- **Positive Example**: `f7f8ddfd02a769d9`
- **Resolution Pattern**: Informing the customer that Amazon does not have exact restock dates for all items.
- **Escalation Considerations**: Low.
- **Evidence**: 3,033 supporting threads.

### Intent ID: `promotions_pricing`
- **Intent Name**: Promotions & Pricing
- **Definition**: Questions about discounts, promo codes, price drops, or lightning deals.
- **Inclusion Criteria**: Promo codes not working, price match inquiries.
- **Exclusion Criteria**: Prime membership billing issues.
- **Positive Example**: `9397c97b1ca20d2a`
- **Resolution Pattern**: Explaining that Amazon does not typically price match after purchase.
- **Escalation Considerations**: Medium (customers get angry about pricing).
- **Evidence**: 1,845 supporting threads.

## 3. Account & Billing
### Intent ID: `account_billing`
- **Intent Name**: Billing & Charges
- **Definition**: Questions regarding credit card charges, Prime membership renewals, or unauthorized transactions.
- **Inclusion Criteria**: "Charged me", "unknown charge", "bank", "subscription fee".
- **Exclusion Criteria**: General refunds for returned items.
- **Positive Example**: `7ef9dfc9169a101e`
- **Resolution Pattern**: Directing the customer to a secure account link.
- **Escalation Considerations**: High. Financial issues require strict security.
- **Evidence**: 6,442 supporting threads.

### Intent ID: `account_access`
- **Intent Name**: Account Access & Security
- **Definition**: Locked out of accounts, password resets, app crashing, or suspected fraud.
- **Inclusion Criteria**: "Can't login", "locked account", "password reset".
- **Exclusion Criteria**: Kindle specific device locks.
- **Positive Example**: `c60948c813bce291`
- **Resolution Pattern**: Providing a secure password reset link or escalating to the fraud team.
- **Escalation Considerations**: High. Security risk.
- **Evidence**: 2,126 supporting threads.

## 4. Digital Services & Devices
### Intent ID: `digital_prime_video`
- **Intent Name**: Prime Video
- **Definition**: Streaming issues, missing episodes, or purchasing movies.
- **Inclusion Criteria**: "Prime video", "streaming error", "playback".
- **Positive Example**: `b269e1f2a5f806d7`
- **Resolution Pattern**: Troubleshooting device, clearing cache, or confirming licensing.
- **Escalation Considerations**: Low.
- **Evidence**: 1,362 supporting threads.

### Intent ID: `digital_kindle`
- **Intent Name**: Kindle & eBooks
- **Definition**: eBook downloads, Kindle device troubleshooting, or Kindle Unlimited issues.
- **Inclusion Criteria**: "Paperwhite", "eBook not downloading", "Kindle library".
- **Positive Example**: `f6efd28df02b4edf`
- **Resolution Pattern**: Sync device, restart Kindle.
- **Escalation Considerations**: Low.
- **Evidence**: 1,780 supporting threads.

### Intent ID: `amazon_music`
- **Intent Name**: Amazon Music
- **Definition**: Issues playing songs, playlists, or Music Unlimited subscriptions.
- **Inclusion Criteria**: "Amazon music app", "song won't play".
- **Positive Example**: `2ad4a5e68579ab3e`
- **Resolution Pattern**: Clear app cache or check subscription tier.
- **Escalation Considerations**: Low.
- **Evidence**: 873 supporting threads.

### Intent ID: `echo_alexa`
- **Intent Name**: Echo & Alexa
- **Definition**: Smart speaker troubleshooting or Alexa command failures.
- **Inclusion Criteria**: "Echo dot", "Alexa not responding", "red ring".
- **Positive Example**: `1c12baaf43e2c58a`
- **Resolution Pattern**: Device reset instructions.
- **Escalation Considerations**: Low.
- **Evidence**: 1,901 supporting threads.

## 5. Specialty Services
### Intent ID: `amazon_locker`
- **Intent Name**: Amazon Locker & Pickup
- **Definition**: Access codes not working, full lockers, or locating a locker.
- **Inclusion Criteria**: "Locker", "access code", "pickup point".
- **Positive Example**: `878f69c05ea2aa6d`
- **Resolution Pattern**: Requesting order details to resend code or extending pickup time.
- **Escalation Considerations**: Medium (customer is often physically stranded at the locker).
- **Evidence**: 861 supporting threads.

### Intent ID: `grocery_fresh`
- **Intent Name**: Amazon Fresh / Grocery
- **Definition**: Issues with grocery delivery windows, spoiled food, or Whole Foods pickup.
- **Inclusion Criteria**: "Fresh delivery", "spoiled", "grocery window".
- **Positive Example**: `416f367ae994e79c`
- **Resolution Pattern**: Immediate refund for spoiled food.
- **Escalation Considerations**: Medium.
- **Evidence**: 611 supporting threads.
