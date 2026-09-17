# Phase 11B — MNRL Hard-Negative Pilot Results

## Training
- Triplets: 195 train / 49 val
- Epochs: 1
- Loss: 2.419
- Runtime: 122s (MPS)

## Retrieval Comparison

| Metric | Baseline | Pilot | Delta |
|---|---:|---:|---:|
| Recall@1 | 0.7245 | 0.7347 | +0.0102 |
| Recall@3 | 0.8418 | 0.8418 | +0.0000 |
| Recall@5 | 0.8571 | 0.8571 | +0.0000 |
| MRR@3 | 0.7772 | 0.7857 | +0.0085 |

## Diff Analysis
- Improvements: 14
- Regressions: 11

## Weak Intent Analysis

| Intent | Baseline R@5 | Pilot R@5 | Baseline R@3 | Pilot R@3 |
|---|---:|---:|---:|---:|
| grocery_fresh | 0.4286 | 0.5000 | 0.3571 | 0.5000 |
| account_access | 0.7619 | 0.7619 | 0.7619 | 0.7619 |
| delivery_wrong_item | 0.5714 | 0.2857 | 0.5714 | 0.2857 |

## Regression Details

- `3f03050f2ccd56e1` (delivery_missing): rank 1 → 4
- `8e6ae6b8bb6ff8d9` (delivery_wrong_item): rank 3 → 999
- `5fc32478a3b63ac7` (delivery_wrong_item): rank 3 → 999
- `471d985ba341b408` (returns_refunds): rank 1 → 2
- `74d3d83c4ad45c3d` (returns_refunds): rank 3 → 5
- `51f7b73ff3175ac1` (digital_kindle): rank 4 → 999
- `547be894014b4903` (digital_kindle): rank 1 → 2
- `c763f518de8ef948` (account_access): rank 1 → 2
- `f7cd418894688848` (promotions_pricing): rank 2 → 3
- `20c1a80b2496fb80` (delivery_missing): rank 1 → 2
- `079b146a88a14dc0` (product_availability): rank 1 → 2

## Decision
**REJECT**

## Safety
- Production model modified: NO
- Production FAISS modified: NO
- Golden Set modified: NO
