# Step 14b: Dense Retrieval Failure Diagnosis

> **Date**: 2026-09-12
> **Goal**: Understand why 19.9% of queries fail to retrieve a relevant document at K=3 using the pre-trained `all-MiniLM-L6-v2` model.

---

## 1. Overall Failure Rate

On a 5,000-query validation set (val_split.jsonl):
- **K=3 Failures**: 996 (19.9%)
- **K=3 Successes**: 4,004 (80.1%)

---

## 2. Failure Modes

### 2.1 The "Black Hole" Intent (`delivery_missing`)

The most common failure mode is lexical ambiguity where queries are incorrectly matched to `delivery_missing`. Because `delivery_missing` is the largest intent class (9,316 indexed documents), it dominates the semantic space.

**Top 5 Intent Confusions (True Intent → Retrieved Intent)**:
1. `delivery_delayed` → `delivery_missing` (379 failures)
2. `returns_refunds` → `delivery_missing` (259 failures)
3. `product_availability` → `delivery_missing` (149 failures)
4. `account_billing` → `delivery_missing` (132 failures)
5. `promotions_pricing` → `delivery_missing` (110 failures)

*Diagnosis*: Pre-trained sentence transformers focus heavily on overlapping nouns. A query about a delayed delivery ("Where is my order?") is semantically identical in pre-trained space to a missing delivery ("I didn't get my order").

### 2.2 Rare Intent Starvation

Intents with very few indexed documents have catastrophic retrieval failure rates:

- `grocery_fresh` (306 indexed docs) → **34.88% Recall@3**
- `amazon_locker` (303 indexed docs) → **47.17% Recall@3**

*Diagnosis*: When an intent is rare, the dense space around its keywords is sparse. Queries with slightly unusual phrasing easily drift into the territory of larger intents.

### 2.3 The "Long Query" Penalty

- **Mean tokens for failures**: 122 tokens
- **Mean tokens for successes**: 89 tokens

*Diagnosis*: Dense retrieval struggles with noisy, multi-turn conversations. The longer a thread gets, the more greetings, agent scripts ("I'm sorry to hear that..."), and off-topic pleasantries dilute the core semantic meaning.

### 2.4 Uncalibrated Confidence Scores

- **Mean top-1 score for failures**: 0.7736
- **Mean top-1 score for successes**: 0.7723

*Diagnosis*: The raw cosine similarity score from the pre-trained model is useless for confidence estimation. The model assigns roughly the same similarity score whether it's right or wrong.

---

## 3. Implications for MNRL Fine-Tuning

A fine-tuning pass using Multiple Negatives Ranking Loss (MNRL) should specifically address these failures:

1. **Pulling intents apart**: By providing in-batch negatives, the model will learn that `delivery_delayed` and `delivery_missing` belong in separate regions of the vector space, despite sharing words like "order" and "delivery".
2. **Ignoring noise**: The model will learn to ignore agent pleasantries and focus on the customer's core issue, reducing the "long query" penalty.
3. **Hard negatives**: We can explicitly sample confusions (e.g., `returns_refunds` paired against a `delivery_missing` negative) to force the model to learn the boundary.

**Next Action**: Run a small pilot MNRL fine-tuning experiment on a leakage-safe subset of `train_split.jsonl` to verify if these theoretical improvements hold true.
