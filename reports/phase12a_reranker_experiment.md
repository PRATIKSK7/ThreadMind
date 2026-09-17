# Phase 12A — Hybrid Retrieval + Cross-Encoder Reranking

## Configuration
- Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Dense model: MNRL (`.cache/rag_dense_mnrl/`)
- Candidate recall Top-10: 87.2%
- Candidate recall Top-20: 91.8%

## A/B Comparison

| Configuration | R@1 | R@3 | R@5 | MRR@3 |
|---|---:|---:|---:|---:|
| Dense baseline (K=5) | 0.7245 | 0.8418 | 0.8571 | 0.7772 |
| Dense Top-10 → rerank | 0.6735 | 0.8214 | 0.8520 | 0.7406 |
| Dense Top-20 → rerank | 0.6531 | 0.8367 | 0.8571 | 0.7389 |

## Diff Analysis (Dense vs Top-20 Rerank)
- Improved: 19
- Regressed: 34
- Unchanged: 143

## Error Categories

- **CANDIDATE_GENERATION_FAILURE**: 16
- **RERANKING_FAILURE**: 7
- **SUCCESSFUL_RERANK**: 19
- **HARMFUL_RERANK**: 34

## Decision
**REJECT**
