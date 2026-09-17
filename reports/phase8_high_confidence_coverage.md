# Phase 8: High Confidence Coverage Analysis

| Intent | Golden Set | Full Corpus | High Confidence | Retention |
|--------|------------|-------------|-----------------|-----------|
| delivery_delayed | 12 | 5469 | 3524 | 64.44% |
| returns_refunds | 16 | 6098 | 3964 | 65.0% |
| delivery_missing | 15 | 9316 | 5571 | 59.8% |
| delivery_wrong_item | 7 | 548 | 139 | 25.36% |
| account_access | 21 | 1193 | 1069 | 89.61% |
| account_billing | 14 | 3387 | 2720 | 80.31% |
| digital_prime_video | 14 | 1503 | 1174 | 78.11% |
| digital_kindle | 14 | 1533 | 1245 | 81.21% |
| amazon_music | 14 | 697 | 392 | 56.24% |
| echo_alexa | 14 | 1655 | 1490 | 90.03% |
| promotions_pricing | 14 | 1769 | 1613 | 91.18% |
| amazon_locker | 13 | 303 | 282 | 93.07% |
| grocery_fresh | 14 | 306 | 299 | 97.71% |
| product_availability | 14 | 1470 | 1470 | 100.0% |

## Dangerous Filtering Flags
- **delivery_delayed**: 64.44% retained (< 80%)
- **returns_refunds**: 65.0% retained (< 80%)
- **delivery_missing**: 59.8% retained (< 60%)
- **delivery_wrong_item**: 25.36% retained (< 40%)
- **digital_prime_video**: 78.11% retained (< 80%)
- **amazon_music**: 56.24% retained (< 60%)
