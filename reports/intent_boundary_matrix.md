# Intent Boundary Matrix

## 1. `account_access` vs `delivery_wrong_item`
- **Shared semantic area**: Customer frustration, failure of a process, "wrong" information.
- **Critical distinguishing signal**: Focus on physical package contents vs digital login/app credentials.
- **Example A (`account_access`)**: "Trying to set up for the 1st time but the app says my Amazon password is incorrect."
- **Example B (`delivery_wrong_item`)**: "I received a phone case instead of the headphones I ordered."
- **Recommended decision rule**: If the issue mentions passwords, login, accounts, or the app crashing, assign `account_access` regardless of words like "incorrect" or "wrong".

## 2. `amazon_locker` vs `delivery_missing`
- **Shared semantic area**: Customer cannot access their items at a physical location.
- **Critical distinguishing signal**: Did the package fail to arrive/get stolen, or is the customer struggling with the locker interface/access codes?
- **Example A (`amazon_locker`)**: "My locker access code isn't working and it expires today."
- **Example B (`delivery_missing`)**: "I went to the locker, opened the door, and there was just an empty cardboard sleeve inside."
- **Recommended decision rule**: If the package is actually missing or the box is empty, it is a `delivery_missing` issue. `amazon_locker` should be reserved for logistical/access issues with the locker itself.

## 3. `delivery_delayed` vs `returns_refunds`
- **Shared semantic area**: Waiting for something to be delivered or processed. Time delays.
- **Critical distinguishing signal**: Is the customer waiting for a physical product, or the return of their funds?
- **Example A (`delivery_delayed`)**: "Tracking says it should have been here Tuesday, but it's still in transit."
- **Example B (`returns_refunds`)**: "My refund claim is 2 weeks old. You said 3 to 5 business days."
- **Recommended decision rule**: Any delayed refund or missing money goes to `returns_refunds`. `delivery_delayed` is strictly for physical package shipments.

## 4. `delivery_missing` vs `delivery_wrong_item`
- **Shared semantic area**: The final delivery state is incorrect, items are missing from the expected total.
- **Critical distinguishing signal**: Did they receive someone else's items, or did they receive nothing / partial quantity?
- **Example A (`delivery_missing`)**: "I ordered 4 items, but only 2 were in the box."
- **Example B (`delivery_wrong_item`)**: "I got 2 items I didn't order instead of the 4 I did."
- **Recommended decision rule**: If the customer received items they *did not order*, it is `delivery_wrong_item`. If they received an empty box or partial order with no incorrect items, it is `delivery_missing`. If both, `delivery_wrong_item` takes precedence as it requires return authorization.

## 5. `account_billing` vs `returns_refunds`
- **Shared semantic area**: Money, charges, bank accounts.
- **Critical distinguishing signal**: Was the initial charge authorized for a product (now being returned), or was the charge completely unknown/unauthorized (like Prime renewal)?
- **Example A (`account_billing`)**: "I was charged $119 for a Prime membership I didn't sign up for."
- **Example B (`returns_refunds`)**: "I returned the defective TV but haven't gotten my money back."
- **Recommended decision rule**: Use `returns_refunds` if a physical product return is involved. Use `account_billing` for subscription fees or unauthorized account charges.
