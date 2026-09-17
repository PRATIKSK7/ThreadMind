# Phase 2: Deterministic Taxonomy Boundary Audit

## Executive Summary
A strict deterministic audit was performed to clarify the intent taxonomy boundaries and evaluate the 196-example Golden Set for label consistency. The audit relied entirely on explicit lexical signals (e.g., mention of passwords, tracking numbers, locker screens) mapped directly against the taxonomy definitions, without utilizing generative LLM heuristics. 

The audit successfully revealed that a portion of the K=5 "classification failures" are actually instances where the ground-truth Golden Set label contradicts the explicit text of the customer's request. Based on these findings, we strongly advise repairing the Golden Set before attempting further model optimization.

## Current Taxonomy Strengths
The existing 14-intent taxonomy provides strong, mutually exclusive coverage for the vast majority of e-commerce support queries. Categories like `product_availability`, `digital_prime_video`, and `echo_alexa` have well-defined scopes and unique keywords that do not bleed into logistics or billing issues. When a customer's query maps cleanly to one of these core intents, the taxonomy supports high-confidence classification.

## Taxonomy Boundary Problems
The taxonomy suffers from overlapping definitions in the logistics and account management space, primarily because intents were derived from TF-IDF clusters rather than strictly isolated customer goals.
- **Account Access vs Wrong Item**: Customers often say "wrong information" or "password incorrect". Without strict rules, "wrong" can bleed into merchandise issues.
- **Amazon Locker vs Missing Delivery**: The final state (customer doesn't have package) is the same, but the domain (technical failure of the locker vs logistical failure of the courier) differs.
- **Delayed Delivery vs Refunds**: Both involve waiting. The taxonomy lacks a strict boundary separating physical transit from financial transit.

## Golden Set Quality Findings
The Golden Set contains systemic labeling errors that directly penalize the classifier. In 14 cases (7.1% of the evaluation set), the assigned ground-truth label directly contradicts deterministic evidence in the text. For example, conversations explicitly discussing app passwords and login crashes were labeled as `delivery_wrong_item`.

## Confusion Pair Analysis
1. **account_access vs delivery_wrong_item**: The highest source of noise (11 flagged examples). The boundary must enforce that any mention of digital login credentials supersedes the use of the word "wrong".
2. **amazon_locker vs delivery_missing**: (1 flagged example). The boundary must enforce that physical locker technical failures are `amazon_locker`, while an empty locker is `delivery_missing`.
3. **delivery_delayed vs returns_refunds**: (2 flagged examples). The boundary must strictly segregate tracking of outbound shipments (`delivery_delayed`) from inbound returns and financial reimbursements (`returns_refunds`).

## Clear Mislabels
The deterministic audit identified **14** CLEAR_MISLABEL examples where the text contained explicit keywords (like "password") strongly indicating an intent fundamentally different from the assigned ground truth (like `delivery_wrong_item`).

## Ambiguous Examples
Because this was a strict deterministic keyword audit, we flagged **0** examples as purely TAXONOMY_AMBIGUITY. Only cases with strongly contradictory evidence were flagged. A human or semantic LLM review would likely surface additional nuanced ambiguity.

## Genuine Model Errors
After excluding the 14 clear mislabels, the remaining K=5 failures were analyzed.
- **53** examples remain as genuine **classification failures** (the model guessed incorrectly despite a valid ground-truth label and good retrieval).
- **17** examples remain as genuine **retrieval bottlenecks** (the retriever failed to fetch relevant context).

## Quantitative Impact
- **Total Golden Set examples**: 196
- **Number of deterministic flags**: 14
- **Percentage of Golden Set affected**: 7.1%
- **K=5 failures involving a flagged example**: 11
- **Adjusted K=5 baseline**: By repairing just these 11 mislabeled failures, the K=5 accuracy would rise from 58.67% to approximately 64.2%.

## Recommended Next Phase
**PHASE 3: Controlled Golden Set Repair**

**Reasoning:** The audit found clear mislabels that directly contradict the taxonomy definitions (7.1% of the dataset). Optimizing the LLM prompt or classifier to match these incorrect labels would force the model to learn incorrect decision boundaries. We must repair the Golden Set labels to establish a trustworthy ground truth before attempting to improve the model's accuracy.
