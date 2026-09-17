# Dynamic RAG Pilot Results (N=20)

| Configuration | Intent Acc | Macro F1 | Esc Acc | Malformed | Latency (s) | Avg Examples | Avg Tokens |
|---|---|---|---|---|---|---|---|
| A. K=1 | 40.0% | 0.111 | 35.0% | 0 | 0.00 | 1.0 | 892 |
| B. K=3 | 70.0% | 0.272 | 60.0% | 0 | 0.00 | 3.0 | 1153 |
| C. K=5 | 70.0% | 0.272 | 65.0% | 0 | 0.00 | 5.0 | 1423 |
| D. Dynamic K | 60.0% | 0.230 | 60.0% | 0 | 8.04 | 3.0 | 1160 |

## Conclusions
1. **Which configuration performed best?**
   Fixed K=3 and K=5 tied for the highest Intent Accuracy (70.0%). K=5 slightly edged out K=3 on Escalation Accuracy (65.0% vs 60.0%).

2. **Did dynamic filtering reduce distractors?**
   Yes, the dynamic threshold (score >= max - 0.008) successfully reduced the average number of examples to 3.0 (from 5.0), pruning examples with slightly lower similarity scores.
   
3. **Did accuracy improve over K=5 baseline?**
   No. The Dynamic K configuration actually saw a performance regression (Intent Accuracy: 60.0%) compared to fixed K=3 and K=5 (70.0%). It seems that slightly lower-scoring examples still provide useful few-shot pattern reinforcement for the 3B model, and aggressively filtering them removes valuable context.

4. **Is the result strong enough to justify full evaluation?**
   No. Based on this 20-example pilot, dynamic similarity-based thresholding does not reliably improve upon a fixed K=3 or K=5 strategy. The LLM benefits more from consistent few-shot volume than from hyper-filtered similarity. The next steps should likely focus on Chain-of-Thought or direct prompt iteration rather than dynamic retrieval thresholds.