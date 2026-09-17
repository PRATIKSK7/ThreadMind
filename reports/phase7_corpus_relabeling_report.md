# Phase 7: Corpus Relabeling Report

## 1. Corpus Statistics
- **Original corpus count**: 82,360 (Raw `retrieval_corpus.jsonl`. Note: the V1 FAISS index only indexed 35,247 of these because it dropped `other_support` cases).
- **Candidate corpus count**: 82,360
- **High-confidence count**: 24,952
- **Review count**: 57,408
- **Insufficient-context count**: 0
- **Label-change percentage**: 69.7% (57,408 / 82,360)

## 2. Top Label Transitions
1. `unknown` -> `other_support`: 47,113 (These were dropped in V1, but the script flagged them for REVIEW as `other_support` is invalid).
2. `delivery_missing` -> `other_support`: 3,745
3. `returns_refunds` -> `other_support`: 2,134
4. `delivery_delayed` -> `other_support`: 1,945
5. `account_billing` -> `other_support`: 667

## 3. Known-Boundary Statistics
- `account_access_vs_wrong_item_flagged`: 0

## 4. Audit Result
- A 200-example deterministic audit sample was created in `reports/phase7_relabel_audit.md`. The sample confirms that the script correctly routed uncertain predictions (such as the invalid `other_support` label) into the `REVIEW` status bucket.

## 5. Integrity Result
- PASS: No missing IDs, no duplicate IDs, no malformed JSONL, no empty conversations, and original conversation text is byte-for-byte unchanged.
- FAIL: The strict requirement that "all accepted labels belong to the 14-intent taxonomy" caused a massive shift of documents into the REVIEW status.

## 6. Decision Gate
**ABORT**
More than 25% of the corpus requires uncertain relabeling (69.7%). There is a massive systematic shift because 47,113 documents that were previously silently dropped by the V1 indexer (due to being `other_support`) were forced into the relabeling pipeline, causing a label explosion into the `REVIEW` bucket.

## 7. Recommendation for Phase 8
Phase 8 must implement a **Corpus Filtering and Thresholding** step. Instead of forcing all 82,360 raw documents into the FAISS index, we should aggressively filter out the 57,408 `REVIEW` and `INSUFFICIENT_CONTEXT` documents, and build a high-quality V2 index using ONLY the 24,952 `HIGH_CONFIDENCE` documents that map perfectly to the 14 intents.
