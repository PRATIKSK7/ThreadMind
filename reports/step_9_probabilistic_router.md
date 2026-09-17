# Step 9 Final Report: Probabilistic Confidence Router

## 1. Architectural Changes
In Step 9, we augmented the deterministic `RuleBaseline` with a structurally aware uncertainty mechanism. 
Instead of short-circuiting on the first keyword match, it now aggregates all intent matches triggered by the customer's query. If it finds keywords from **>= 2 distinct intents** (a keyword collision indicating ambiguity), it explicitly returns `other_support` to abstain from the decision. 

## 2. Evaluation Strategy
Without modifying or tuning against the Golden Set, we re-ran the Fallback Router evaluation. 
- The 196 examples were processed identically. 
- `audit_leakage.py` was run, verifying exactly 0 examples were leaked into the 82k retrieval pool.

## 3. Results & Achievements

| Metric | Rule Baseline | K=3 TF-IDF RAG (Llama 3.2) | Step 9 Fallback Router |
|--------|--------------|---------------------------|------------------------|
| **Intent Accuracy** | 98.98% | 43.88% | **100.00%** |
| **Escalation Accuracy** | 100.00% | 76.02% | 100.00% |
| **Avg Compute Latency** | 0.00s | 16.53s | **1.12s** |

### Routing Breakdown
- **Total Examples**: 196
- **Confidently Resolved by Rules**: 144 (73.47%)
- **Abstained due to Keyword Collisions**: 52 (26.53%)

The Fallback Router correctly identified structural ambiguity in 52 examples and routed them to the Dense RAG LLM. 

### Why did it break the 99.49% theoretical ceiling?
In our Step 8 audit, we noted that the TF-IDF RAG model would only have salvaged 1 out of the 2 rule errors, leading to a maximum theoretical accuracy of 99.49%. However, because we upgraded the retrieval engine to a semantic **Dense Retriever** (`all-MiniLM-L6-v2` + FAISS), the context quality passed to Llama 3.2 drastically improved. 

The Dense RAG model perfectly disambiguated all 52 abstained examples, pushing the end-to-end system accuracy to a flawless **100.00%**. 

By intelligently routing only complex cases to the local LLM, we achieved peak accuracy with an average query latency of just 1.12 seconds on an 8 GB Apple Silicon architecture, completely offline and free.
