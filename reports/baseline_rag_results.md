# Step 6: RAG Baseline Evaluation and Comparison

This report details the evaluation of the Retrieval-Augmented Generation (RAG) configuration using the local `llama3.2` model. A TF-IDF retriever was built to fetch the top-k most semantically similar threads from the 82k `AmazonHelp` corpus (with the Golden Set strictly isolated to prevent leakage). These retrieved examples were injected into the Llama 3.2 prompt as few-shot demonstrations.

## 1. RAG Configuration
- **Provider**: local `ollama`
- **Model**: `llama3.2` (3B Parameters)
- **Retriever**: `sklearn` TF-IDF with Sparse Cosine Similarity
- **Retrieval Corpus Size**: 82,164 unlabeled threads (weakly labeled for intent/escalation via Rule Baseline)
- **Golden Set Hash**: `4b85791cbcf152dedbed75b3c32c6994a4d0660dd9e5612bf838299b38258964`

## 2. Leakage Audit
- **Status**: PASSED
- `golden_set_leakage_audit.json` confirms **0** Golden Threads appear in the retrieval corpus.

## 3. Retriever Quality (Recall@K & MRR)
Before evaluating the LLM, the retriever was evaluated for its ability to pull threads that share the same correct intent as the target Golden Set thread.

| K | Recall@K | Mean Reciprocal Rank (MRR) |
|---|----------|----------------------------|
| 1 | 38.78% | 0.3878 |
| 3 | 60.20% | 0.4813 |
| 5 | 67.86% | 0.4991 |

> [!NOTE]
> Even with a simple TF-IDF index, `Recall@5` approaches 68%, proving that simple lexical overlap strongly correlates with conversational intent in customer service domains.

## 4. LLM Generation Performance (Ablation over K)
We performed a controlled ablation over $k=1$, $k=3$, and $k=5$ injected examples.

| K | Intent Accuracy | Macro F1 | Escalation Accuracy | Cache Misses |
|---|-----------------|----------|---------------------|--------------|
| 1 | 39.80% | 0.3827 | 64.29% | 196 |
| **3** | **43.88%** | **0.3920** | **65.31%** | **196** |
| 5 | 41.84% | 0.3165 | 67.86% | 196 |

> [!TIP]
> **K=3** yields the best Intent classification results (43.88%). At K=5 (41.84%), performance drops slightly, likely due to the "Lost in the Middle" phenomenon where the 3B parameter model struggles with the heavily bloated context window.

## 5. Global Baseline Comparison
Here is how the new RAG configurations stack against our existing baselines:

| Baseline | Type | Intent Accuracy | Escalation Accuracy | Hardware |
|----------|------|-----------------|---------------------|----------|
| Rule Baseline | Heuristic | **98.98%** | **100.00%** | CPU |
| TF-IDF Baseline | ML (Linear) | 84.69% | N/A | CPU |
| **RAG (K=3)** | **LLM (Few-Shot)**| **43.88%** | **65.31%** | **Apple Silicon GPU** |
| Llama 3.2 | LLM (Zero-Shot) | 31.63% | 48.47% | Apple Silicon GPU |

### Key Takeaways
1. **RAG Works**: Injecting just 3 examples via RAG boosted the local Llama 3.2 model's intent accuracy from 31.63% to 43.88%, and its escalation accuracy from 48.47% to 65.31%. This is a massive relative improvement over zero-shot prompting.
2. **Context Window Limits**: A local 3B model is not a drop-in replacement for OpenAI's GPT-4. Supplying $K=5$ examples degraded intent accuracy, suggesting the model fails to process dense, lengthy contexts efficiently.
3. **The Power of Heuristics**: The rule-based and linear ML baselines significantly outperform the local 3B parameter LLM. The LLM fundamentally lacks the deterministic mapping provided by the heavily-tuned Rule baseline. Using a local LLM for intent classification on limited hardware without extensive fine-tuning is strictly inferior to traditional NLP methods for this specific domain.
