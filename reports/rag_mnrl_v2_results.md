# MNRL RAG — Golden Set V2 Baseline

## Benchmark

- Golden Set version: V2
- Examples: 196
- SHA-256: 6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f

## Model

- Retriever: Fine-tuned MNRL Dense Retriever
- Base model: all-MiniLM-L6-v2
- Loss: MultipleNegativesRankingLoss
- LLM: llama3.2:latest
- Context: 4096

## Results

| K | Intent Accuracy | Macro F1 | Escalation Accuracy |
|---|---:|---:|---:|
| 1 | 48.47% | 0.4624 | 59.69% |
| 3 | 59.18% | 0.5443 | 66.33% |
| 5 | 60.71% | 0.5550 | 68.88% |

Retrieval:

| Metric | K=1 | K=3 | K=5 |
|---|---:|---:|---:|
| Recall | 72.45% | 84.18% | 85.71% |
| MRR@3 | 0.7245 | 0.7772 | 0.7772 |

## V1 vs V2

| Metric | V1 | V2 | Delta |
|---|---:|---:|---:|
| Intent Accuracy (K=5) | 58.67% | 60.71% | +2.04% |
| Macro F1 (K=5) | 0.5419 | 0.5550 | +0.0131 |
| Escalation Accuracy (K=5) | 68.88% | 68.88% | 0.00% |
| Recall@5 | 86.73% | 85.71% | -1.02% |

The V1→V2 differences reflect the benchmark repair rather than any model capability changes. The 14 Golden Set label corrections mathematically aligned the ground truth with the deterministic text contents, increasing the model's apparent accuracy (since the model had actually been predicting some of these correctly in V1, but was penalized by incorrect ground truth). The slight drop in Recall@5 indicates that the static retrieval corpus still contains old potentially mislabeled examples.
