# Phase 14A — V3 Classifier Reasoning Policy

## Design Rationale
Phase 13B diagnostics revealed that exactly 66.7% of V2 classification failures occurred **despite the correct intent being successfully retrieved** by the dense retriever. The V2 prompt was explicitly instructed to "NOT classify based solely on the closest retrieved example", causing it to ignore unanimous correct evidence (causing 8 failures) and it lacked conflict-resolution logic for mixed retrieval signals (causing another 8 failures). The V3 policy addresses these two specific failure modes by explicitly teaching the LLM *how* to weigh RAG evidence, rather than telling it to distrust the evidence altogether.

## Decision Hierarchy
The V3 prompt enforces a rigid 9-step reasoning sequence:
1. Understand the user's actual problem
2. Identify the operational object/entity involved
3. Identify the requested action/problem
4. Determine the strongest intent-defining evidence
5. Compare only plausible candidate intents
6. **Use retrieved examples as supporting evidence, NOT as ground truth** (The core RAG synthesis step)
7. Prefer the candidate whose taxonomy definition best matches the user's actual problem
8. Do not choose an intent merely because it appears frequently in retrieval if the taxonomy definition does not fit
9. Do not let superficial lexical overlap override the actual intent

## Conflict-Resolution Strategy
The V3 policy explicitly handles the 3 scenarios of RAG evidence:
1. **Unanimous & Consistent**: If retrieved examples unanimously share an intent that aligns with the user's actual problem, the classifier is instructed to explicitly **prefer it**. This directly addresses the 8 `CLASSIFIER_IGNORED_CORRECT` failures.
2. **Conflicting Evidence**: If retrieved examples conflict, the classifier is instructed to resolve the conflict using the explicit taxonomy boundary rules. This directly addresses the 8 `CONFLICTING_EVIDENCE` failures.
3. **Noisy / Missing**: If the retrieved examples do not match the user's actual problem, the classifier is instructed to ignore them and rely on independent taxonomy reasoning.

## Boundary Handling Strategy
The V3 policy explicitly encodes logic to resolve the most common confusion boundaries identified in Phase 13B:
- **`account_access` vs `delivery_wrong_item/missing/delayed`**: Enforces that physical order issues belong to delivery intents, preventing `account_access` from swallowing delivery problems just because a user can't "see their tracking in the app".
- **`amazon_locker` vs `delivery_missing`**: Clarifies that empty lockers or stolen packages belong to `delivery_missing`. `amazon_locker` is strictly for technical locker failures (doors won't open, code invalid).
- **`grocery_fresh` vs `returns_refunds`**: Enforces prioritization of `grocery_fresh` over refund requests when dealing with spoiled food.
- **`account_billing` vs `grocery_fresh`**: Distinguishes between Amazon Fresh fulfillment errors vs generalized Prime membership billing issues.

## Expected Failure Modes
- **Retrieval Ceiling**: The 8 `RETRIEVAL_MISSING` failures will likely remain unsolved. The classifier cannot magically hallucinate the perfect few-shot pattern if the retriever completely fails to provide it.
- **Over-correction on Boundaries**: The rigid boundary rules might cause the classifier to be overly literal (e.g. assigning `delivery_missing` to an `amazon_locker` issue if a package was placed in the wrong slot).

## Safeguards Against Retrieval-Context Bias
The policy enforces that the LLM must first "Understand the user's actual problem" and "Identify the operational object/entity involved" *before* it looks at the retrieved examples. Furthermore, it explicitly states: "Do not choose an intent merely because it appears frequently in retrieval if the taxonomy definition does not fit."

---

## Status
- **Files created**: `src/threadmind/llm/prompts/classification_reasoning_policy_v3.txt`, `reports/phase14a_v3_reasoning_policy.md`
- **Files modified**: None
- **Production files changed**: None
- **Golden Set changed**: No
- **FAISS changed**: No
- **Ready for Phase 14B pilot**: **YES**
