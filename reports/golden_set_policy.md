# Golden Set Policy

## Objective
To ensure strict isolation between the evaluation dataset (Golden Set) and any future retrieval corpus, development data, or training data used in the THREADMIND agent.

## Policy Rules

### 1. Separation Boundary
Isolation is enforced strictly at the **thread level**. If a thread is selected for the Golden Set, *all messages* belonging to that thread (both customer and brand) are permanently banned from appearing in the retrieval/RAG corpus.

### 2. Message-Level Safety
We do not split threads. If a thread contains 10 turns, we do not evaluate on turns 8-10 while letting turns 1-7 leak into the retrieval pool. The entire history of a golden-set thread is held out.

### 3. Deduplication
Before the final retrieval corpus is created in later steps, it must verify that no `thread_id` matches any `thread_id` in `data/processed/golden_set.jsonl`.

### 4. Zero Generation Leakage
The `golden_set.jsonl` explicitly does *not* contain the target "ideal model response" string. It only contains the source thread and the `expected_behavior`. This structurally prevents an LLM from "accidentally" training on the exact text of a reference answer, because the reference answer text is not generated yet.

> [!CAUTION]
> Future vector embeddings MUST use a filter to exclude any documents whose `thread_id` exists in the Golden Set metadata.
