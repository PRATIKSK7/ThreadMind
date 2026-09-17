# Multi-Turn Intent Analysis

Multi-turn conversations fundamentally change how an AI support agent must behave. In the AmazonHelp dataset, many intents are not fully resolvable in a single turn.

## Evolution of Intent
1. **Ambiguous Initial Contact**:
   - Customer: "Where is my package?" (Could be `delivery_delayed` or `delivery_missing`)
   - Brand: "I'm sorry to hear that. What does the tracking say?"
   - Customer: "It says delivered but I don't have it." (Intent officially resolves to `delivery_missing`)

2. **Compound Intents**:
   - Customer starts with `delivery_wrong_item`.
   - Brand apologizes and authorizes a return.
   - Customer asks: "When will I get my refund for this?" (Intent shifts to `returns_refunds`).

3. **Escalation Realization**:
   - Customer: "Why was I charged $139?" (`account_billing`)
   - Brand: "That looks like Prime renewal. We can refund it."
   - Customer: "I already cancelled it 3 months ago! This is fraud."
   - Brand: "Please click this secure link so we can authenticate you." (Intent severity escalates from basic inquiry to potential fraud).

## Importance for Agent Design
Because intents evolve, classifying *only* the last message will lead to context collapse. The agent must:
1. Maintain memory of the root issue.
2. Recognize when the customer has fulfilled a previous request (e.g., providing an order number).
3. Know when the conversation is looping (e.g., customer repeatedly saying "the link doesn't work").
