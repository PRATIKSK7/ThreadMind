# Baseline 2: LLM Zero-Shot Evaluation

## Configuration
- **Provider**: ollama
- **Model**: llama3.2
- **Prompt Version**: v1
- **Golden Set Hash**: `4b85791cbcf152dedbed75b3c32c6994a4d0660dd9e5612bf838299b38258964`

## System Metrics
- **API Failures**: 0
- **Malformed Responses**: 0
- **Cache Hits**: 0
- **Cache Misses**: 196
- **Avg Latency (Misses)**: 7.21s
- **Median Latency (Misses)**: 6.80s

## Performance Metrics
- **Intent Accuracy**: 31.63%
- **Intent Macro F1**: 0.2924
- **Escalation Accuracy**: 48.47%

## Subgroup Analysis
| Subgroup | Total | Correct | Accuracy |
|----------|-------|---------|----------|
| context_dependent | 44 | 7 | 15.91% |
| semantic_ambiguity | 11 | 0 | 0.00% |
| structural_complex | 40 | 9 | 22.50% |
| hard_ambiguous | 49 | 10 | 20.41% |
| multi_turn | 111 | 32 | 28.83% |
| turns_1_2 | 85 | 30 | 35.29% |
| turns_3_4 | 62 | 18 | 29.03% |
| turns_5_plus | 49 | 14 | 28.57% |

## Per-Intent Metrics
| Intent | Precision | Recall | F1 | Support |
|--------|-----------|--------|----|---------|
| account_access | 0.2444 | 0.7857 | 0.3729 | 14 |
| account_billing | 0.6667 | 0.4286 | 0.5217 | 14 |
| amazon_locker | 1.0000 | 0.0714 | 0.1333 | 14 |
| amazon_music | 0.6667 | 0.1429 | 0.2353 | 14 |
| delivery_delayed | 0.3846 | 0.7143 | 0.5000 | 14 |
| delivery_missing | 0.1429 | 0.0714 | 0.0952 | 14 |
| delivery_wrong_item | 0.3333 | 0.2143 | 0.2609 | 14 |
| digital_kindle | 0.4000 | 0.1429 | 0.2105 | 14 |
| digital_prime_video | 0.5000 | 0.2143 | 0.3000 | 14 |
| echo_alexa | 0.6000 | 0.4286 | 0.5000 | 14 |
| grocery_fresh | 0.7500 | 0.2143 | 0.3333 | 14 |
| other_support | 0.0000 | 0.0000 | 0.0000 | 0 |
| product_availability | 0.2857 | 0.4286 | 0.3429 | 14 |
| promotions_pricing | 0.2500 | 0.3571 | 0.2941 | 14 |
| returns_refunds | 0.4286 | 0.2143 | 0.2857 | 14 |
