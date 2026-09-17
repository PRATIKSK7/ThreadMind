# Phase 8: Final Filtering Analysis

## Strategy Comparison
| Strategy | Documents | Label Quality | Intent Coverage | Risk |
|----------|-----------|---------------|-----------------|------|
| Option A: HIGH_CONFIDENCE ONLY | 24952 | High | Poor (Many intents < 20%) | High (Coverage Collapse) |
| Option B: HIGH_CONFIDENCE + TRUSTED ORIGINAL | 35247 | Mixed | Excellent | Moderate (Originals are noisy) |
| Option C: THRESHOLD FILTERING | N/A | N/A | N/A | Threshold-based filtering cannot be evaluated from available metadata. |

## Recommended Strategy
REQUIRES_TARGETED_RELABELING

## Explicit Reason
Option A (HIGH_CONFIDENCE ONLY) causes a dangerous collapse in intent coverage because 47,113 raw documents lack valid intents in the taxonomy and fail the strict confidence gate. The original index safely dropped these by only using 35,247 known documents. If we filter to HIGH_CONFIDENCE, we will likely lose most of our core intents. We need to perform targeted relabeling ONLY on the 35,247 documents that were previously indexed, rather than attempting to filter the noisy 82,360 raw dump.
