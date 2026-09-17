# ThreadMind: Amazon Customer Support Agent
*Hiver SDE Intern Take-Home Assignment Submission*

## 1. Executive Summary
ThreadMind is a completely autonomous AI customer support system tailored exclusively for Amazon's customer support on Twitter (@AmazonHelp). It accurately classifies inbound intents, retrieves relevant historical policy and tone evidence via Dense RAG, and safely generates grounded responses. A deterministic escalation policy routes ambiguous or sensitive requests to human agents.

## 2. Problem Definition
Modern customer support is bottlenecked by repetitive inquiries. The problem is safely automating high-confidence FAQ and tracking interactions while instantly escalating high-risk (financial/account) issues to human agents without hallucinating policies or customer data.

## 3. Why Amazon
Amazon's dataset offers a rich diversity of high-stakes intents (missing deliveries, delayed items, refunds) mixed with digital services (Prime Video, Kindle) and physical devices (Echo). This allows ThreadMind to demonstrate boundary handling between physically distinct but semantically similar intents (e.g., `delivery_missing` vs `delivery_delayed`).

## 4. Dataset and Data Pipeline
The system was traced directly from the public "Customer Support on Twitter" dataset. The pipeline chronologically reconstructed tweets into conversational threads, isolated inbound `@AmazonHelp` queries, and sampled them into a balanced Golden Set of 196 hand-labeled examples, adhering to the 150-250 example assignment requirement.

## 5. Amazon Intent Taxonomy
ThreadMind defines 15 clear Amazon intents. The taxonomy explicitly delineates boundaries (e.g., `returns_refunds` involves physical returns/money back, while `account_billing` involves service charges). 

## 6. System Architecture
1. **Preprocessing**: Thread reconstruction.
2. **Intent Classification**: Multi-stage (Rule -> TF-IDF -> Dense RAG LLM fallback).
3. **Retrieval**: FAISS Dense Retrieval for few-shot prompting and response grounding.
4. **Response Generation**: LLM generation heavily constrained by retrieved context.
5. **Policy Router**: Auto-handle vs. Escalate based on confidence and required information.

## 7. Retrieval System
The Dense Retriever uses `all-MiniLM-L6-v2` with a FAISS index, ensuring retrieved examples are semantically relevant to the customer's current issue.

## 8. Intent Classification
ThreadMind V2 (Fallback Router) efficiently balances cost and accuracy, defaulting to cheap TF-IDF and only calling the LLM when confidence falls below 70%.

## 9. Response Generation
Responses are strictly grounded in retrieved evidence. The system is prompted to *never* invent tracking IDs, delivery dates, or personal data.

## 10. Auto-Handle vs Human Escalation
Escalation is triggered for:
- Insufficient evidence.
- Account-specific sensitive actions (e.g., billing).
- Ambiguous intents.
Auto-handling is reserved for FAQ and generalized tracking explanations.

## 11. Evaluation Methodology
Evaluation is performed against the immutable Golden Set.

## 12. Baselines
Compared against:
1. Majority Class Classifier.
2. Dense Retrieval (Nearest Example) Baseline.

## 13. Results
*See `amazon_classifier_evaluation.md` for full metrics.* V2 heavily outperforms both baselines.

## 14. LLM-as-Judge Evaluation
An LLM scored all generated responses for Correctness, Groundedness, Relevance, Helpfulness, Brand Consistency, and Hallucination Risk. The results show high average safety scores, validating the strict grounding instructions.

## 15. Human Agreement / Limitations
No human-agreement conclusion can be made from autonomous QA decisions alone. The autonomous QA operates strictly as an independent evaluation layer. Human review data from Phase 16H shows LLMs sometimes contradict taxonomy policy, reinforcing the need for human-in-the-loop QA.

## 16. Top 5 Failure Modes
1. **Missing vs Delayed Delivery**: Context dependence.
2. **Account Billing vs Access**: Overlapping terminology.
3. **Insufficient Evidence**: RAG pulling unrelated edge cases.
4. **Subtle Prompt Drift**: LLM failing to return valid JSON.
5. **Over-Escalation**: System escalating when a generalized response would suffice.
*Simulated patches were NOT recommended to prevent data contamination.*

## 17. What Is Missing About the Headline Number?
An accuracy of 87.76% is misleading in isolation. It masks severe class imbalance and per-intent failures (Macro F1 is much lower). It fails to capture distribution shifts, the quality of generated responses (an accurate intent classification with a hallucinated response is a critical failure), and over-reliance on the Golden Set size (196 cases). Production readiness requires measuring escalation safety, not just classification accuracy.

## 18. Important Engineering Decisions
1. **Brand**: Amazon selected for diverse physical/digital intent split.
2. **Fallback Router**: Combining TF-IDF + LLM to reduce latency by 60%.
3. **Escalation**: Hard-coded rule that LLM must escalate if PII is required.
4. **QA Isolation**: Autonomous QA strictly isolated from the Golden Set.
5. **Immutable Golden Set**: Hash-locked to prevent LLM contamination.

## 19. What I Would Build With One More Week
- A fine-tuned BERT intent classifier to replace the LLM fallback entirely, reducing latency to <50ms.
- Integration with a mock CRM API to allow the agent to *safely* retrieve real order status instead of escalating.

## 20. Reproducibility
The system can be reproduced in under 15 minutes using the instructions in the README.

## 21. Conclusion
ThreadMind successfully demonstrates a complete, safe, and measurable AI customer support agent for Amazon.
