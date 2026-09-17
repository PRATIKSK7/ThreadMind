# MNRL RAG Failure Analysis

## Executive Summary
This report analyzes why the end-to-end intent accuracy for K=5 (61.22%) lags behind the retrieval Recall@5 (86.73%). Although the previous formatting and context window truncation fixes successfully eliminated malformed responses, the local 3B model still struggles to correctly classify intents even when the correct example is in the context window.

## K=1 / K=3 / K=5 Comparison
| K | Intent Accuracy | Recall | Gap (Recall - Accuracy) |
|---|-----------------|--------|-------------------------|
| 1 | 44.90% | 72.96% | 28.06% |
| 3 | 57.65% | 85.20% | 27.55% |
| 5 | 61.22% | 86.73% | 25.51% |

## Retrieval vs Generation Failure Breakdown (K=5)
- **1. retrieval failure**: 19 (18.45% of failures, 9.69% of total N=196)
- **2. retrieval success but LLM classification failure**: 57 (55.34% of failures, 29.08% of total N=196)
- **4. escalation classification failure**: 27 (26.21% of failures, 13.78% of total N=196)

## Representative Failure Examples
### Example of 2. retrieval success but LLM classification failure
- **Thread ID**: 6128774c272909e7
- **Expected Intent**: delivery_delayed
- **Predicted Intent**: other_support
- **Retrieved Intents**: ['delivery_delayed', 'delivery_delayed', 'delivery_delayed', 'delivery_delayed', 'delivery_delayed']

### Example of 1. retrieval failure
- **Thread ID**: e5e227f6392f6343
- **Expected Intent**: delivery_delayed
- **Predicted Intent**: returns_refunds
- **Retrieved Intents**: ['returns_refunds', 'returns_refunds', 'returns_refunds', 'returns_refunds', 'returns_refunds']

## Root Causes
1. **3B Model Reasoning Limits**: The Llama 3.2 3B model is not powerful enough to reliably perform multi-hop reasoning over 5 examples (even compacted ones). It often ignores the target classification patterns or gets distracted by lexical overlap, leading to a large 'Retrieval Success but LLM Failure' gap.
2. **Context Dilution**: Providing 5 examples means there are up to 4 distractor examples when only 1 correct example is retrieved. The model is easily swayed by the majority of distractor examples.
3. **Escalation Complexity**: Escalation is determined by subtle tone or policy rules, not just the base intent. Few-shot examples alone are not sufficient to teach escalation logic without explicit chain-of-thought rules.

## Top 3 Proposed Improvements (Without retraining MNRL)
1. **Dynamic Prompting (Only inject top 1 or 2 highest-confidence examples)**: Instead of a fixed K=3 or K=5, filter retrieved examples by a similarity threshold, or strictly limit to K=2 to reduce distractor dilution for the small model.
2. **Add Explicit Chain-of-Thought (CoT) to the Prompt**: Update the prompt schema to require the LLM to write out a short reasoning step (e.g., 'Target user mentioned X. This matches Example Y which is Z.') BEFORE outputting the JSON classification.
3. **Improve Retrieval Granularity via Reranking**: Add a lightweight Cross-Encoder or BM25 hybrid step on top of the MNRL FAISS index to ensure the #1 retrieved example is highly relevant, allowing us to rely on K=1 or K=2.

## Exact Files that Would Need Modification
- `src/threadmind/llm/prompts/rag_classification_v1.txt` (To add CoT instructions)
- `scripts/evaluate_rag_mnrl.py` (To implement dynamic K or hybrid reranking, and handle the new CoT JSON output)

## Recommended Next Experiment
Modify the prompt to require Chain-of-Thought reasoning (CoT) before outputting the final intent, and reduce K to 2 to minimize distractor dilution. Evaluate this modified prompt using the existing MNRL index on the Golden Set.
