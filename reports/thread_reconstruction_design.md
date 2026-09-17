# Thread Reconstruction Design

## Intended Algorithm
The THREADMIND thread reconstruction algorithm is designed to preserve multi-turn conversations safely from raw social media data.

1. **Root tweet identification**: A thread begins with an inbound customer tweet that has no `in_response_to_tweet_id` or an inbound tweet responding to a non-existent tweet (orphan).
2. **Parent-child traversal**: From a root, we use `response_tweet_id` (which can contain comma-separated IDs) to find replies, mapping them sequentially.
3. **Response relationships**: The dual-pointer system (`response_tweet_id` and `in_response_to_tweet_id`) will be used to resolve missing links and validate continuity.
4. **Branching**: A single tweet might receive multiple responses. We will prioritize the longest continuous Customer-Brand interaction branch or preserve the tree structure in full if computationally feasible.
5. **Broken references**: Orphan references will be treated as thread roots if they belong to a customer, or dropped if they are unresolvable brand responses.
6. **Duplicate IDs**: Exact duplicate rows will be discarded. Duplicate IDs with differing text will trigger a warning and be resolved chronologically.
7. **Cycles**: We will maintain a visited set of `tweet_id`s during traversal to prevent infinite loops caused by malformed data.
8. **Maximum traversal safeguards**: A hard limit (e.g., depth=50) will be enforced to prevent stack overflows and outlier mega-threads from crashing the pipeline.
9. **Chronological ordering**: Once a thread is assembled, it will be strictly ordered by `created_at`.
10. **Customer vs Brand messages**: The `inbound` boolean flag will dictate speaker identity. `inbound=True` is the Customer, `inbound=False` is the Brand.
11. **Conversation Boundaries**: A thread is bounded when there are no more valid `response_tweet_id`s within the dataset.

> [!WARNING]
> Social media data is inherently noisy. Reconstruction is an approximation and will not perfectly recover deleted or un-captured tweets.
