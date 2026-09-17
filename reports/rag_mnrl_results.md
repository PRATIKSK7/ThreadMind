# MNRL RAG Evaluation

## Configuration
- **Retriever**: Fine-tuned MNRL Dense Retriever
- **Base model**: all-MiniLM-L6-v2
- **Loss**: MultipleNegativesRankingLoss
- **Golden Set Hash**: `6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f`
- **Architecture**: 3-Process Isolation (Avoids macOS openblas/omp segfault)

## End-to-End RAG Metrics

| K | Intent Accuracy | Macro F1 | Escalation Accuracy | Cache Misses |
|---|-----------------|----------|---------------------|--------------|
| 1 | 81.63% | 0.8185 | 100.00% | 196 |
| 3 | 87.76% | 0.8579 | 100.00% | 196 |
| 5 | 80.61% | 0.8004 | 100.00% | 196 |

## Retrieval Metrics

| Metric | K=1 | K=3 | K=5 |
|--------|-----|-----|-----|
| Recall | 72.45% | 84.18% | 85.71% |
| MRR@3  | - | 0.7772 | - |
