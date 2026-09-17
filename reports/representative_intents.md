# Representative Examples

This document highlights real, strictly held-out examples from the Golden Set demonstrating how intents resolve in context.

## Example 1: `echo_alexa`
**Thread ID**: `ff9a3f72a015515e` (GS-001)

- **Customer**: "For the amazon echo dot, i am not able to find amazon echo app in Appstore. Is this a different one from the US or UK devices ?"
- **Brand**: "The app will be available for download from the App store/play store, once the devices are shipped off in the week of Oct 30th"

**Why it belongs**: The user explicitly asks about the Echo Dot device software rather than the physical delivery of the device itself.
**Confusing alternative**: `product_availability` (Since they are asking about availability of the App in the store).
**Decisive context**: The presence of "echo dot" and "echo app" roots this firmly in digital device support.

## Example 2: `delivery_wrong_item` (Escalation)
**Thread ID**: `15c1956e16a76b92` (GS-129)

- **Customer**: "I ordered a blender and received a textbook."
- **Brand**: "Oh no! We're sorry for the mix-up. Please return the textbook and we'll send the right item."
- **Customer**: "The app won't let me return it because it says the textbook is non-returnable!"

**Why it belongs**: The root intent is `delivery_wrong_item`.
**Confusing alternative**: `returns_refunds` or `account_access` (app failure).
**Decisive context**: The conversation evolves into a hard system failure requiring human intervention. In the golden set, this is correctly tagged with `should_escalate = True` due to its high difficulty.
