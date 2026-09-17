# Step 14a: Dense FAISS Retrieval Baseline

> **Date**: 2026-09-12
> **Status**: Baseline measurement COMPLETE. No fine-tuning performed.

---

## 1. Evaluation Methodology

### 1.1 What Corpus Was Indexed

- **Source**: `data/processed/retrieval_corpus.jsonl` (82,360 threads)
- **Filtering**: Only threads with non-`other_support` rule-baseline intents are indexed
- **Indexed documents**: 35,247
- **Index type**: `IndexFlatIP` (exact cosine similarity via L2-normalized inner product)
- **Embedding model**: `all-MiniLM-L6-v2` (22M parameters, 384-dimensional embeddings)

### 1.2 What Evaluation Queries Were Used

- **Source**: `data/processed/val_split.jsonl` (16,472 threads)
- **Filtering**: Only threads with non-`other_support` rule-baseline intents that are present in the FAISS index
- **Evaluation queries**: 5,000
- **Excluded**: 11,472 `other_support` threads

### 1.3 How Relevance Was Determined

A retrieved document is considered a "hit" if its rule-baseline intent matches the query thread's rule-baseline intent. For each query, we retrieve K+1 nearest neighbors and exclude the query thread itself (self-exclusion), then evaluate the top K remaining results.

### 1.4 Evaluation–Corpus Overlap

Val_split threads ARE present in the retrieval corpus (and therefore in the FAISS index). Self-exclusion ensures the query thread itself is never counted as a hit. Other val_split threads with the same intent that appear in results are valid hits — they represent genuinely different conversations with the same intent.

### 1.5 Golden Set Leakage Prevention

| Check | Result |
|-------|--------|
| Golden Set threads in query set | 0 |
| Golden Set threads in FAISS index | 0 |
| Golden Set threads in val_split | 0 |
| Golden Set used for tuning | NO |

---

## 2. Results

### 2.1 Overall Retrieval Quality

| K | Recall@K | MRR | Hits | Queries |
|---|----------|-----|------|---------|
| 1 | **58.42%** | 0.5842 | 2,921 | 5,000 |
| 3 | **80.08%** | 0.6816 | 4,004 | 5,000 |
| 5 | **85.68%** | 0.6944 | 4,284 | 5,000 |

### 2.2 Comparison with TF-IDF Retrieval

| Retriever | Recall@1 | Recall@3 | Recall@5 |
|-----------|----------|----------|----------|
| TF-IDF (from baseline_rag_results.md) | 38.78% | 60.20% | 67.86% |
| **Dense (all-MiniLM-L6-v2)** | **58.42%** | **80.08%** | **85.68%** |
| **Improvement** | **+19.64pp** | **+19.88pp** | **+17.82pp** |

> [!IMPORTANT]
> The Dense Retriever significantly outperforms TF-IDF across all K values. Note: The TF-IDF metrics were evaluated on the Golden Set (N=196), while Dense metrics are evaluated on val_split (N=5,000). The evaluation sets are different, so the comparison is directional rather than strictly apples-to-apples.

### 2.3 Per-Intent Retrieval Performance (Recall@3)

| Intent | Recall@3 | Hits | Queries | Assessment |
|--------|----------|------|---------|------------|
| delivery_missing | **94.54%** | 1,039 | 1,099 | ✅ Excellent |
| digital_kindle | **91.53%** | 227 | 248 | ✅ Excellent |
| echo_alexa | **90.30%** | 270 | 299 | ✅ Excellent |
| digital_prime_video | **87.95%** | 219 | 249 | ✅ Very good |
| amazon_music | **85.29%** | 58 | 68 | ✅ Very good |
| returns_refunds | **81.42%** | 688 | 845 | ✅ Good |
| account_access | **76.02%** | 168 | 221 | ⚠️ Moderate |
| account_billing | **75.98%** | 408 | 537 | ⚠️ Moderate |
| delivery_delayed | **72.86%** | 518 | 711 | ⚠️ Moderate |
| delivery_wrong_item | **62.50%** | 20 | 32 | ⚠️ Low (small N) |
| promotions_pricing | **62.06%** | 193 | 311 | ⚠️ Low |
| product_availability | **54.93%** | 156 | 284 | ❌ Poor |
| amazon_locker | **47.17%** | 25 | 53 | ❌ Poor (small N) |
| grocery_fresh | **34.88%** | 15 | 43 | ❌ Very poor (small N) |

### 2.4 Failure Analysis

**Worst-performing intents** (Recall@3 < 55%):
- `grocery_fresh` (34.88%, N=43): Only 306 documents in the FAISS index. Sparse coverage limits retrieval quality.
- `amazon_locker` (47.17%, N=53): Only 303 documents in the index. Similar sparsity problem.
- `product_availability` (54.93%, N=284): 1,470 documents in the index. This intent likely has high vocabulary overlap with other intents, causing confusion.

**Best-performing intents** (Recall@3 > 90%):
- `delivery_missing` (94.54%): Largest intent class (9,316 indexed docs) with distinctive language patterns.
- `digital_kindle` (91.53%): Strong brand-specific keywords ("Kindle") aid retrieval.
- `echo_alexa` (90.30%): Strong device-specific keywords ("Echo", "Alexa") aid retrieval.

### 2.5 Latency

| Metric | Value |
|--------|-------|
| Mean | 18.8 ms |
| Median | 17.0 ms |
| P95 | 28.7 ms |
| P99 | 50.0 ms |

---

## 3. Key Findings

1. **Dense Recall@3 = 80.08%** — significantly better than expected and substantially better than TF-IDF (60.20%). The pre-trained all-MiniLM-L6-v2 model is already effective for customer support retrieval.

2. **The previously cited "Dense FAISS Recall@3 = 65.31%" was incorrect.** The actual Dense Recall@3 is 80.08%. The 65.31% figure was the TF-IDF RAG K=3 Escalation Accuracy.

3. **Retrieval quality varies dramatically by intent.** The range spans from 34.88% (grocery_fresh) to 94.54% (delivery_missing). Rare intents with few indexed documents perform worst.

4. **~20% of queries fail at K=3.** This means for ~1 in 5 conversations, the Dense Retriever cannot find a same-intent example in the top 3 results, forcing the LLM to generate without relevant grounding.

5. **Latency is excellent** (median 17ms). FAISS retrieval is not a bottleneck.

---

## 4. Implications for Fine-Tuning (Step 14b)

MNRL fine-tuning should target:
- Improving recall for underperforming intents (`grocery_fresh`, `amazon_locker`, `product_availability`, `promotions_pricing`)
- Reducing intent confusion between similar categories (`delivery_delayed` vs `delivery_missing`, `account_billing` vs `account_access`)
- The baseline is already strong (80.08% Recall@3), so fine-tuning improvements may be incremental

**Do NOT proceed to fine-tuning until this baseline is reviewed and approved.**

---

## 5. Artifacts

| File | Description |
|------|-------------|
| [dense_retrieval_baseline.json](file:///Users/pratikskanoj/ThreadMind/reports/dense_retrieval_baseline.json) | Full metrics in machine-readable format |
| [evaluate_dense_retriever_baseline.py](file:///Users/pratikskanoj/ThreadMind/scripts/evaluate_dense_retriever_baseline.py) | Evaluation script |
