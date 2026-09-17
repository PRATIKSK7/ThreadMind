# Step 14: Dense Retrieval Improvement Plan

> **Date**: 2026-09-12
> **Goal**: Measure, diagnose, and improve Dense FAISS retrieval quality to reduce hallucination rate and LLM fallback dependence
> **Status**: PLAN ONLY — Do NOT start fine-tuning until approved

---

## 1. Problem Statement

The ThreadMind reply generation pipeline depends on Dense FAISS retrieval (K=3) to provide grounded context to Llama 3.2. However:

1. **Dense Retrieval Recall@K has never been measured.** The `scripts/evaluate_retriever.py` script exists but was never run against the Dense Retriever with results recorded.
2. **The only measured retrieval recall is from the TF-IDF retriever**: Recall@1=38.78%, Recall@3=60.20%, Recall@5=67.86%.
3. **The previously cited "Dense FAISS Recall@3 = 65.31%" is incorrect** — that figure is actually the TF-IDF RAG K=3 Escalation Accuracy.
4. **4.59% hallucination rate** (9/196) is directly linked to retrieval failures where the model lacks grounded context.
5. **69.2% fallback rate** on unseen data means most conversations hit the expensive LLM path.

---

## 2. Current Architecture

### 2.1 Embedding Model

- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Parameters**: ~22M
- **Embedding dimension**: 384
- **Training**: Pre-trained on 1B+ sentence pairs (paraphrase mining, NLI, etc.)
- **NOT fine-tuned** on the customer support domain

### 2.2 FAISS Index

- **Index type**: `IndexFlatIP` (exact inner product search after L2 normalization → cosine similarity)
- **Indexed documents**: 35,247 (non-`other_support` threads from the retrieval corpus)
- **Full retrieval corpus**: 82,360 threads
- **Documents excluded from index**: 47,113 threads labeled `other_support` by rule baseline

### 2.3 Data Splits (Verified Leak-Free)

| Split | Size | Golden Set Overlap |
|-------|------|--------------------|
| Golden Set | 196 | — |
| Retrieval Corpus | 82,360 | 0 |
| Train Split | 65,888 | 0 |
| Validation Split | 16,472 | 0 |

### 2.4 Intent Distribution in FAISS Index

| Intent | Count |
|--------|-------|
| delivery_missing | 9,316 |
| returns_refunds | 6,098 |
| delivery_delayed | 5,469 |
| account_billing | 3,387 |
| promotions_pricing | 1,769 |
| echo_alexa | 1,655 |
| digital_kindle | 1,533 |
| digital_prime_video | 1,503 |
| product_availability | 1,470 |
| account_access | 1,193 |
| amazon_music | 697 |
| delivery_wrong_item | 548 |
| grocery_fresh | 306 |
| amazon_locker | 303 |

---

## 3. Phase 1: Measure Baseline Dense Retrieval Recall

**Before any fine-tuning**, we must establish the actual baseline.

### 3.1 Task

Run `scripts/evaluate_retriever.py` against the Dense Retriever with K=1, 3, 5 and record:

| Metric | K=1 | K=3 | K=5 |
|--------|-----|-----|-----|
| Dense Recall@K | ? | ? | ? |
| Dense MRR | ? | ? | ? |

### 3.2 Definition

**Recall@K**: For each Golden Set example, retrieve K documents from the FAISS index. A "hit" = at least one retrieved document shares the same intent as the Golden Set example's ground-truth intent.

### 3.3 Comparison Baseline

| Retriever | Recall@1 | Recall@3 | Recall@5 |
|-----------|----------|----------|----------|
| TF-IDF | 38.78% | 60.20% | 67.86% |
| Dense (all-MiniLM-L6-v2) | ? | ? | ? |

---

## 4. Phase 2: Diagnose Retrieval Failures

After measuring recall, analyze:

1. **Per-intent recall**: Which intents have lowest retrieval recall? (Likely rare intents like `amazon_locker` with only 303 docs)
2. **False positive analysis**: When retrieval returns wrong-intent documents, what's the common confusion pattern?
3. **Score distribution**: What are the cosine similarity scores for hits vs. misses? Is there a score threshold that separates them?
4. **Query length effect**: Do longer/shorter conversations retrieve better or worse?

---

## 5. Phase 3: Fine-Tuning with MNRL

### 5.1 Approach: Multiple Negatives Ranking Loss (MNRL)

MNRL is the standard contrastive loss for embedding fine-tuning with sentence-transformers. It uses in-batch negatives, making it efficient for large-scale training.

### 5.2 Training Data Construction

**Source**: `data/processed/train_split.jsonl` (65,888 threads)

**Positive pair construction**:
- For each thread in the training split, the rule baseline assigns an intent label
- Two threads with the **same intent** form a positive pair
- The anchor is the formatted conversation text; the positive is another conversation with the same intent

**Hard negative construction**:
- Threads with **different intents** that share confusing keywords (e.g., "delivery" + "refund" across `delivery_missing` vs `returns_refunds`)
- Mine hard negatives using the pre-fine-tuned model's top-K retrievals that are wrong-intent

### 5.3 Leakage Prevention (Critical)

| Constraint | Implementation |
|------------|----------------|
| Golden Set excluded from training pairs | Filter by `thread_id` — verified: 0 Golden IDs in train_split |
| Golden Set excluded from validation pairs | Filter by `thread_id` — verified: 0 Golden IDs in val_split |
| Retrieval corpus unchanged | Fine-tuning changes the model weights, not the indexed documents. After fine-tuning, the index must be rebuilt with the new embeddings. |
| Evaluation on held-out data only | Recall@K computed on Golden Set (never seen during training) |

### 5.4 Training Configuration

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

model = SentenceTransformer("all-MiniLM-L6-v2")

# Training pairs from train_split only
train_examples = [...]  # InputExample(texts=[anchor, positive])

train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=64)
train_loss = losses.MultipleNegativesRankingLoss(model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100,
    output_path="models/finetuned-minilm-support",
    show_progress_bar=True,
)
```

### 5.5 Hyperparameter Search Space

| Parameter | Range |
|-----------|-------|
| Epochs | 1, 3, 5 |
| Batch size | 32, 64, 128 |
| Learning rate | 2e-5 (default) |
| Warmup steps | 10% of training steps |
| Hard negatives per anchor | 0 (in-batch only), 1, 3 |

---

## 6. Phase 4: Post-Fine-Tuning Evaluation

### 6.1 Retrieval Recall Comparison

| Retriever | Recall@1 | Recall@3 | Recall@5 |
|-----------|----------|----------|----------|
| TF-IDF | 38.78% | 60.20% | 67.86% |
| Dense (pre-FT) | ? | ? | ? |
| Dense (post-FT) | ? | ? | ? |

### 6.2 Downstream Impact Assessment

After rebuilding the FAISS index with fine-tuned embeddings:

1. **Re-run reply generation** on the 196 Golden Set examples
2. **Re-run LLM-as-Judge** on the new replies
3. **Compare**:
   - Hallucination rate: before vs. after
   - Judge Correctness/Groundedness/Helpfulness/Tone: before vs. after
4. **Re-run on 500-thread unseen validation**:
   - Fallback rate: before vs. after (should remain ~69.2% since fallback is router-driven, not retrieval-driven)

### 6.3 Embedding Model Comparison (Optional)

If time permits, benchmark alternative base models:

| Model | Parameters | Dim | Domain |
|-------|-----------|-----|--------|
| all-MiniLM-L6-v2 | 22M | 384 | General |
| all-mpnet-base-v2 | 110M | 768 | General |
| multi-qa-MiniLM-L6-cos-v1 | 22M | 384 | QA-tuned |

Each would be evaluated with and without MNRL fine-tuning.

---

## 7. Execution Order

```
Step 14a: Measure Dense Retriever Recall@1/3/5 baseline (MUST DO FIRST)
Step 14b: Diagnose retrieval failures by intent
Step 14c: Construct training pairs from train_split.jsonl
Step 14d: Fine-tune with MNRL (start with 1 epoch, batch=64)
Step 14e: Rebuild FAISS index with fine-tuned embeddings
Step 14f: Re-measure Recall@1/3/5
Step 14g: Re-run reply generation and Judge evaluation
Step 14h: Compare all metrics (before vs. after)
```

---

## 8. Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Dense Recall@3 | UNMEASURED | >70% |
| Hallucination rate | 4.59% | <3% |
| Judge Correctness | 4.54 | >4.6 |
| Judge Groundedness | 4.86 | >4.9 |
| Golden Set leakage | 0 | 0 |
| Test suite | 40/40 | 40/40 |

---

## 9. Risks

1. **Overfitting to rule-baseline labels**: Training pairs are constructed using rule-baseline intent labels, which may contain errors. The model may learn to replicate rule-baseline biases rather than genuine semantic similarity.
2. **MNRL in-batch negatives may be too easy**: With 14 intents and a batch of 64, random negatives are likely to be from different intents. Hard negative mining may be needed.
3. **Index rebuild cost**: After fine-tuning, all 35,247 documents must be re-encoded (~5 min on MPS).
4. **Evaluation bias**: Recall@K measures intent-matching, which may not perfectly correlate with reply quality. A retrieved document with the correct intent but different sub-topic may still produce poor grounding.
