# Phase 7: Controlled Relabeling Policy

## 1. Valid Intent IDs
The relabeler MUST output one of the following exact 14 intent IDs:
`delivery_missing`, `delivery_delayed`, `delivery_wrong_item`, `returns_refunds`, `account_access`, `account_billing`, `digital_prime_video`, `digital_kindle`, `amazon_music`, `echo_alexa`, `amazon_locker`, `grocery_fresh`, `promotions_pricing`, `product_availability`. 
No new intent IDs are permitted.

## 2. Taxonomy Definitions
- **delivery_missing**: Package never arrived, empty box, or stolen package.
- **delivery_delayed**: Package is late but expected.
- **delivery_wrong_item**: Customer received a package, but it contained the wrong physical item.
- **returns_refunds**: Requesting to return an item, reporting defective physical merchandise, or asking for refund status.
- **account_access**: Issues logging in, reset password, locked account, or app crashing.
- **account_billing**: Unauthorized charges, Prime subscription billing, or payment method issues.
- **digital_prime_video**: Streaming issues, Prime Video playback.
- **digital_kindle**: Kindle device syncing, eBook download issues.
- **amazon_music**: Music streaming, playlist issues.
- **echo_alexa**: Echo hardware, Alexa voice assistant issues.
- **amazon_locker**: Problems opening an Amazon Locker, locker access codes.
- **grocery_fresh**: Amazon Fresh, Whole Foods, spoiled food.
- **promotions_pricing**: Coupon codes, price matching, lightning deals.
- **product_availability**: Pre-orders, out-of-stock items, release dates.

## 3. Explicit Intent Boundaries
- **account_access vs delivery_wrong_item**: Mentions of "wrong item" must be ignored if the context is digital account access (e.g. wrong email/password). `delivery_wrong_item` is strictly for physical package contents.
- **amazon_locker vs delivery_missing**: If a locker was opened but empty, it is `delivery_missing`. If the locker itself is malfunctioning (won't open), it is `amazon_locker`.
- **account_access vs delivery_delayed**: Mentions of "delayed" or "late" apply to `account_access` if referencing OTP emails/app loading. `delivery_delayed` is strictly for physical package transit.
- **delivery_delayed vs returns_refunds**: `delivery_delayed` applies to outbound shipments to the customer. `returns_refunds` applies to inbound shipments (returns) and refund processing.
- **delivery_missing vs delivery_wrong_item**: If the customer received a box but it was empty, it is `delivery_missing`. If it contained a different item, it is `delivery_wrong_item`.

## 4. High-Confidence Deterministic Cases (Accept >= 0.90)
Predictions with confidence >= 0.90 are accepted if they do not violate known boundaries (e.g., if a document mentions "locker" and "empty", it must be flagged for review regardless of confidence, unless it explicitly falls perfectly into the definition).

## 5. Ambiguous Cases (Review 0.70 - 0.89)
If the conversation lacks sufficient detail to definitively separate it across a known boundary (e.g. "I got the wrong thing" without specifying if it's a digital charge or a physical item), it must be flagged for REVIEW.

## 6. Insufficient-Context Cases (< 0.70)
Conversations that are too short (e.g., just "hello" or "help") or completely off-topic will result in low confidence and must be flagged as INSUFFICIENT_CONTEXT.

## 7. Escalation Handling
Escalation is evaluated simultaneously. Human review is recommended if the user explicitly demands a supervisor, agent, or reports fraud.
