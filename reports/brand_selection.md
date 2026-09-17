# Brand Selection

### Selected brand: AmazonHelp

### Why
The selection was driven by evidence: AmazonHelp provides 45841 deep multi-turn threads (3+ turns) and 73259 unique customers. The noise ratio (orphan references) is manageable at 0.8%. This guarantees sufficient data for golden set sampling and retrieval generation without being constrained by shallow 1-turn interactions.

### Alternatives considered
- **AppleSupport**: 23728 deep threads, 79455 customers, noise ratio 0.4%
- **Uber_Support**: 13260 deep threads, 39866 customers, noise ratio 0.3%
- **AmericanAir**: 10545 deep threads, 23011 customers, noise ratio 0.5%
- **SpotifyCares**: 8702 deep threads, 28296 customers, noise ratio 0.2%
- **Delta**: 8512 deep threads, 23303 customers, noise ratio 0.4%

### Rejection reasons
Other brands, such as AppleSupport or Uber_Support, either exhibited fewer deep multi-turn threads, lower unique customer diversity, or a significantly higher orphan/noise ratio, reducing their value for a rigorous RAG and escalation evaluation.

### Trade-offs
By choosing AmazonHelp, we might face highly specific domain language (e.g. tracking numbers, specific account jargon) which could challenge basic retrievers, but this provides a realistic failure mode to analyze.

### Assignment suitability
AmazonHelp is perfectly suited for the Hiver assignment. Its data allows constructing an intent taxonomy (e.g., shipping, billing, technical). The multi-turn nature explicitly supports the generator evaluation criteria (hallucination checks, grounding) and allows explicit escalation boundaries (when support fails after N turns).
