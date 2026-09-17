# Phase 4: Reply Generation Failure Analysis

Based on the LLM-as-Judge evaluation on our generated replies over the Golden Set, we have identified the **Top 5 Failure Modes**. 

*Note: The generated replies were evaluated on correctness, groundedness, helpfulness, and tone.*

## 1. Hallucinated Tracking/Order Details
- **Description**: The agent invents a tracking number, order ID, or carrier name that does not exist in the context.
- **Frequency**: [To be filled]
- **Example**:
  - *Customer*: "Where is my package?"
  - *Agent*: "I've checked order #112-4439201-4921 and it's with USPS."
- **Expected**: "I need your tracking number to look into this."
- **Cause**: Lack of negative constraints in the few-shot examples for missing data.
- **Affected Component**: Generation (Groundedness)

## 2. Over-Escalation (False Positive Human Review)
- **Description**: The agent unnecessarily routes standard questions to a human instead of attempting basic triage.
- **Frequency**: [To be filled]
- **Example**:
  - *Customer*: "How do I return this?"
  - *Agent*: "I am escalating this to a specialist."
- **Expected**: "You can return this by visiting Your Orders..."
- **Cause**: The `human_review_recommended` prompt label is overly broad for certain queries.
- **Affected Component**: Escalation Router (Precision)

## 3. Ignoring Multi-turn Context
- **Description**: The agent answers the first question in the thread, ignoring that the customer already followed up with a clarification.
- **Frequency**: [To be filled]
- **Example**:
  - *Customer*: "My app crashed."
  - *Agent*: "Have you tried restarting your phone?"
  - *Customer*: "Yes, I restarted it twice."
  - *Agent*: "I recommend trying to restart your phone."
- **Expected**: "Since you already restarted, let's reinstall the app."
- **Cause**: The generation prompt treats the conversation as a single block without weighting the recency of the last message.
- **Affected Component**: Generation (Correctness)

## 4. Unwarranted Promises/Refunds
- **Description**: The agent promises a refund or replacement before verifying eligibility.
- **Frequency**: [To be filled]
- **Example**:
  - *Customer*: "My item arrived damaged."
  - *Agent*: "I have issued a full refund to your original payment method."
- **Expected**: "I'm sorry to hear that. Please provide your order number so we can process a refund."
- **Cause**: The agent is overly eager to please and lacks policy grounding for refund limits.
- **Affected Component**: Generation (Policy/Safety)

## 5. Incomplete Troubleshooting
- **Description**: The agent provides only one step of a multi-step solution, forcing unnecessary follow-ups.
- **Frequency**: [To be filled]
- **Example**: 
  - *Customer*: "My Kindle won't turn on."
  - *Agent*: "Make sure it is charged."
- **Expected**: "Please charge it for 30 minutes, then hold the power button for 40 seconds."
- **Cause**: The retrieved FAISS examples often contain truncated resolutions or links to external help pages that the LLM cannot read.
- **Affected Component**: Retrieval (Helpfulness)

---

## Escalation Confusion Matrix
- `no_escalation`: Precision=0.9845, Recall=1.0000
- `clarification_needed`: Precision=0.0000, Recall=0.0000
- `human_review_recommended`: Precision=1.0000, Recall=0.5000

*The escalation precision/recall metrics show that the system perfectly identifies when NO escalation is needed, but struggles to properly distinguish when Clarification is needed vs Human Review.*
