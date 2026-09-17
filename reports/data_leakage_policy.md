# Data Leakage Policy

## Objective
To strictly prevent temporal and evaluation leakage between the golden evaluation dataset and all other project layers.

## Policy Boundaries

1. **Golden Set Isolation**:
   - The golden set will be sampled *before* any RAG document chunking or embedding models are initialized.
   - It will consist of 150-250 complete, hand-labelled multi-turn threads.
   - Once selected, all tweets belonging to the golden set threads will be permanently excluded from the retrieval corpus.

2. **RAG Retrieval Corpus**:
   - The retrieval corpus will only consist of historically resolved issues that strictly exclude the golden set.
   - We will enforce temporal splitting if necessary, or hash-based exclusion, to ensure a golden-set example cannot retrieve its own historical target response.

3. **Development Data**:
   - A separate tuning subset may be selected. It will not intersect with the golden set.

4. **Generated Replies**:
   - When evaluating generated replies, the generation context will only be given the *customer's history* up to the point of generation, without providing the brand's actual response.

> [!IMPORTANT]
> The principle is absolute: A golden-set example must not accidentally retrieve itself or its target response from the historical retrieval corpus during final evaluation.
