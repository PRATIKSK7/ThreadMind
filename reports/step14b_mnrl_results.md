# Step 14b: MNRL Fine-Tuning Results

## Overview
This report documents the results of fine-tuning the `all-MiniLM-L6-v2` dense embedding model using Multiple Negatives Ranking Loss (MNRL). The goal was to improve retrieval performance (specifically Recall@3) for the `ThreadMind` customer support agent.

## Training Details
- **Training completed successfully.**
- **Training Data**: 4,457 positive conversation pairs automatically generated from `data/processed/train_split.jsonl`.
- **Golden Set Leakage**: None. The Golden Set and Validation Set were strictly excluded from the training data pool.
- **Model**: `all-MiniLM-L6-v2`
- **Loss Function**: `MultipleNegativesRankingLoss`
- **Epochs**: 3
- **Batch Size**: 32 (Custom CPU PyTorch loop to avoid macOS OpenMP memory lock segmentation faults)
- **Training Loss (Avg)**:
  - Epoch 1 = 2.9332
  - Epoch 2 = 2.2454
  - Epoch 3 = 2.0307
- **Model Checkpoints**: The final trained model was successfully saved to `.cache/rag_dense_mnrl`.

## Evaluation Pipeline Note
The previous automated run experienced a segmentation fault during Step 3 (FAISS re-indexing). This crash was diagnosed as a macOS `resource_tracker` collision between `faiss` and `sentence-transformers` running in the same memory space. 
This evaluation strictly bypassed the crash by:
1. Resuming directly from the previously saved `.cache/rag_dense_mnrl` model (avoiding retraining).
2. Generating the FAISS index inside a completely isolated Python subprocess (`build_faiss.py`).

## Baseline vs. Fine-Tuned Metrics
The model was evaluated against the exact same 5,000 leakage-safe validation queries from `data/processed/val_split.jsonl` used in Step 14a. The query's own `thread_id` was strictly excluded from the retrieved candidates.

| Metric | Baseline (`all-MiniLM-L6-v2`) | Fine-Tuned (MNRL) | Absolute Difference |
|--------|------------------------------|-------------------|---------------------|
| **Recall@1** | 58.42% | **83.40%** | +24.98% |
| **Recall@3** | 80.08% | **92.78%** | +12.70% |
| **Recall@5** | 85.68% | **94.78%** | +9.10% |
| **MRR@3**    | 0.6816 | **0.8773** | +0.1957 |

## Latency
- **Median Latency**: 25.8 ms
- **Mean Latency**: 28.3 ms
*(Note: FAISS search remains extremely fast and is well within real-time deployment constraints.)*

## Conclusion
The MNRL fine-tuning **significantly improved retrieval across all metrics**.
- **Recall@3**, our primary target metric, improved by an impressive **12.70 percentage points**, surpassing 92%.
- **Recall@1** saw a staggering **24.98 percentage point** improvement, proving the model learned the highly specific domain semantics of the ThreadMind customer support intents.
- Since Recall@1 did not deteriorate, and Recall@3 improved massively, the fine-tuning is officially categorized as a **strict improvement**.

The baseline FAISS index (`.cache/rag_dense/faiss_index.bin`) was preserved entirely, and the new index is safely stored in `.cache/rag_dense_mnrl/faiss_index.bin`.
