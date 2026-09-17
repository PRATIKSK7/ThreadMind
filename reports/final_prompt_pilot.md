# Final Production Prompt Pilot (N=20)

## Exact Configuration
- **Dataset**: N=20 Golden Set subset
- **Retriever**: MNRL (all-MiniLM-L6-v2) FAISS
- **Retrieval K**: 5
- **Prompt**: Updated `rag_classification_v1.txt` (Variant 2)
- **LLM Provider**: Ollama (local)

## Comparison
| Metric | Old BASE | New Variant 2 | Improvement |
|---|---|---|---|
| Intent Accuracy | 70.0% | 80.0% | +10.0 pts |
| Macro F1 | 0.272 | 0.447 | +0.175 |
| Escalation Accuracy | 70.0% | 75.0% | +5.0 pts |
| Malformed | 0 | 0 | - |

## Execution Details
- True Latency: 12.25s per query
- Avg Examples: 5.0
- Avg Tokens: 1503
