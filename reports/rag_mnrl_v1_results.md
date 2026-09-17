# MNRL RAG Evaluation

## Configuration
- **Retriever**: Fine-tuned MNRL Dense Retriever
- **Base model**: all-MiniLM-L6-v2
- **Loss**: MultipleNegativesRankingLoss
- **Golden Set Hash**: `4b85791cbcf152dedbed75b3c32c6994a4d0660dd9e5612bf838299b38258964`
- **Architecture**: 3-Process Isolation (Avoids macOS openblas/omp segfault)

## End-to-End RAG Metrics

| K | Intent Accuracy | Macro F1 | Escalation Accuracy | Cache Misses |
|---|-----------------|----------|---------------------|--------------|
| 1 | 46.43% | 0.4468 | 59.69% | 181 |
| 3 | 57.14% | 0.5320 | 66.33% | 196 |
| 5 | 58.67% | 0.5419 | 68.88% | 0 |

## Retrieval Metrics

| Metric | K=1 | K=3 | K=5 |
|--------|-----|-----|-----|
| Recall | 72.96% | 85.20% | 86.73% |
| MRR@3  | - | 0.7866 | - |
