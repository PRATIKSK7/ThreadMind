# Phase 6: Retrieval Corpus Re-indexing

## 1. Executive Summary
Phase 6 aimed to determine if the retrieval corpus was limiting performance due to outdated intent labels. The audit found that the corpus does not natively store intent labels; instead, labels are dynamically generated during FAISS indexing using the `RuleBaseline`. This weak keyword baseline suffers from the same taxonomy issues identified in Phase 2 (e.g., assigning `account_access` to logistics issues based on simple keywords). 50 such ambiguous examples were flagged. Since deterministic rules cannot safely resolve these ambiguities and LLM relabeling is prohibited in this phase, Outcome C (Flag for Review) was triggered. No V2 index was built.

## 2. Baseline
- **Golden Set Size:** 196
- **Hash:** 6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f
- **K=3 Intent Accuracy:** 87.76%

## 3. Corpus Audit
- **Total Documents:** 35,247
- **Obsolete Labels:** 0 (All 14 intents are valid)
- **Flagged Examples:** 50 suspicious `account_access` examples mentioning logistics keywords.
- **Outcome:** C (Mixed/ambiguous labels).

## 4. Corpus & Index Changes
- N/A (Re-indexing aborted).

## 5. Retrieval Metrics
- **Old Recall@3:** 84.18%
- **New Recall@3:** N/A

## 6. End-to-End K=3 Metrics
- **Old Intent Accuracy:** 87.76%
- **New Intent Accuracy:** N/A

## 7. Failure Attribution
- N/A (No new failures to attribute).

## 8. Integrity Checks
- Golden Set hash remains unchanged.
- Original retrieval corpus and index safely backed up.

## 9. Recommendation
**REJECT (Aborted)**
We cannot safely repair the corpus using deterministic rules. We must implement Phase 7: LLM-Assisted Corpus Relabeling to annotate the corpus metadata with the high-quality V2 classifier before rebuilding the retrieval index.
