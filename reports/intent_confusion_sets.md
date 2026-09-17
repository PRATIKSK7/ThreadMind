# Intent Confusion Sets

Certain intents are naturally confusable. The agent and the evaluation framework must explicitly handle these overlaps.

### 1. `delivery_delayed` vs `delivery_missing`
- **Why they are similar**: Both involve a customer not having their expected package.
- **What evidence distinguishes them**: The presence of the "Delivered" status. If the tracking says delivered, it is `delivery_missing`. If tracking says in-transit or delayed, it is `delivery_delayed`.
- **Resolving context**: The agent must ask the customer what the tracking status currently says if it isn't clear from the initial message.

### 2. `account_billing` vs `returns_refunds`
- **Why they are similar**: Both involve money moving between the customer and Amazon.
- **What evidence distinguishes them**: `returns_refunds` is tied to a specific physical order that is being sent back. `account_billing` usually refers to digital subscription charges (Prime, Music) or unauthorized bank activity.
- **Resolving context**: Mention of "returning an item" points to refunds, whereas "charged my card out of nowhere" points to billing.

### 3. `product_availability` vs `delivery_delayed`
- **Why they are similar**: The customer is asking when they will receive an item.
- **What evidence distinguishes them**: `product_availability` applies when the item has *not yet shipped* due to stock limits or pre-order status. `delivery_delayed` implies the item has shipped but is stuck in transit.
- **Resolving context**: Checking if the item has a tracking number.

### 4. `digital_prime_video` vs `amazon_music` vs `digital_kindle`
- **Why they are similar**: All represent digital/software troubleshooting rather than physical fulfillment.
- **What evidence distinguishes them**: Specific app names and device context (e.g. streaming movie vs reading eBook).
- **Resolving context**: The exact error message provided by the user.
