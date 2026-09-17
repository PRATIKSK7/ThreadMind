# Router Quality Correction Audit

## 1. Why all 196 examples were routed to the Rule Baseline
The Rule Baseline (`src/threadmind/baselines/rule_baseline.py`) uses a very broad keyword-matching heuristic. Words like "charge", "return", "video", and "late" instantly trigger a classification. Because these 196 Golden Set examples are typical customer service inquiries, every single one of them contains at least one of these broad keywords. Therefore, the Rule Baseline always finds a match and never abstains (never returns `other_support`).

## 2. Rule-Confidence / Uncertainty Signal
There is **no nuanced uncertainty signal**. The Rule Baseline logic immediately breaks and hardcodes a confidence of `0.8` the moment it encounters the first matching substring. It does not calculate probabilities or detect structural ambiguity.

## 3. Genuinely Triggered Fallbacks
Without tuning the rules specifically to abstain on the Golden Set, **zero (0)** examples trigger the fallback. The maximum theoretical number of examples that *should* trigger the fallback on this dataset is 2 (the 2 examples the Rule Baseline gets wrong).

## 4. Evaluation of the Fallback Path on Error Cases
The two cases the Rule Baseline failed on were:
- `63cd9fc1dff215fe`: Expected `digital_prime_video` but predicted `account_billing` (due to the presence of billing keywords like "charge").
- `e6aef6c530ba4876`: Expected `digital_prime_video` but predicted `account_billing`.

If the Fallback Router had correctly identified these as uncertain and routed them to the RAG LLM:
- **`63cd9fc1dff215fe`**: The RAG LLM **successfully salvages** the error and correctly predicts `digital_prime_video`.
- **`e6aef6c530ba4876`**: The RAG LLM **fails** and predicts `delivery_missing`.

**Conclusion:** 
If the router had perfect uncertainty detection, routing just these 2 errors to the LLM would have salvaged 1 of them, bringing the system's maximum theoretical accuracy to **195/196 (99.49%)**. 

However, because the Rule Baseline lacks a probabilistic confidence signal, the current Fallback Router architecture is practically a passthrough to the Rule Baseline for standard queries. The Dense RAG LLM sits entirely dormant.
