# Escalation Labeling Policy

## Objective
To deterministically assign ground-truth escalation conditions to the Golden Set.

## Label Definitions

### `should_escalate = False`
The user's query can be completely resolved using general troubleshooting steps, public policy explanations (e.g. standard refund windows), or informational tracking data, provided the agent is assumed to have API access to those systems.

### `should_escalate = True`
The thread must be passed to a human support agent.

## Triggers for Escalation

1. **Length / Loop Limit**: Any conversation that has reached 5+ turns (Customer ➔ Brand ➔ Customer ➔ Brand ➔ Customer) without resolution indicates a high-friction edge case that AI should not continually attempt to handle.
2. **Ambiguity / Data Corruption**: If the thread contains a missing parent reference (`has_missing_parent = True`), it represents broken context. The agent should ask for clarification or escalate.
3. **High-Risk Intents**:
   - `account_billing`: Queries involving unauthorized bank charges or missing money require strict compliance and account verification.
   - `account_access`: Locked accounts, compromised passwords, or suspected fraud.
   - `delivery_wrong_item` (with high turn count): Complex return authorizations for wrong items sent from third-party sellers.

> [!NOTE]
> The golden set assumes the agent is a Level 1 AI responder. High-risk intents and looped arguments explicitly require Level 2 (Human) intervention.
