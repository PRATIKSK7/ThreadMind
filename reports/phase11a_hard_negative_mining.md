# Phase 11A: Hard Negative Mining

## Methodology
Extracted top 100 dense retrieval results using the MNRL index. For each golden query, documents with mismatched intents were retained. Up to 3 hardest negatives were selected, prioritizing known confusion boundaries and ranking by highest vector similarity.

## Dataset Statistics
- Total Queries: 196
- Total Hard Negatives: 551
- Average Similarity: 0.8869
- Queries with zero valid negatives: 6

## Strength Breakdown
- LOW: 85
- MEDIUM: 222
- HIGH: 244

## Top 5 Confusion Boundaries
- delivery_delayed<->returns_refunds: 51
- account_access<->delivery_wrong_item: 41
- amazon_locker<->delivery_missing: 40
- delivery_delayed<->delivery_missing: 29
- grocery_fresh<->returns_refunds: 27

## Quality Checks
- No duplicate negative IDs: PASS
- No query/negative intent equality: PASS
- No fabricated text (drawn from corpus): PASS

SAFE_FOR_TRAINING: YES
