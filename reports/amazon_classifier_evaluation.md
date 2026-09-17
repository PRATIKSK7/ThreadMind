# Amazon Classifier Evaluation

## Overall Metrics
| System | Accuracy | Macro F1 | Micro F1 | Weighted F1 | Precision | Recall |
|--------|----------|----------|----------|-------------|-----------|--------|
| Baseline 1: Majority Class | 0.1071 | 0.0138 | 0.1071 | 0.0207 | 0.0077 | 0.0714 |
| Baseline 2: Nearest Example | 0.4949 | 0.4759 | 0.4949 | 0.4906 | 0.5576 | 0.4819 |
| **Current System: ThreadMind V2** | **0.8469** | **0.7898** | **0.8469** | **0.8547** | **0.8073** | **0.7967** |

## Per-Intent Performance (V2)
| Intent | Precision | Recall | F1 Score |
|--------|-----------|--------|----------|
| account_access | 0.8125 | 0.6190 | 0.7027 |
| account_billing | 0.8462 | 0.7857 | 0.8148 |
| amazon_locker | 0.9286 | 1.0000 | 0.9630 |
| amazon_music | 1.0000 | 0.8571 | 0.9231 |
| delivery_delayed | 0.6667 | 1.0000 | 0.8000 |
| delivery_missing | 1.0000 | 0.7333 | 0.8462 |
| delivery_wrong_item | 0.3571 | 0.7143 | 0.4762 |
| digital_kindle | 1.0000 | 0.7857 | 0.8800 |
| digital_prime_video | 1.0000 | 0.7857 | 0.8800 |
| echo_alexa | 0.8125 | 0.9286 | 0.8667 |
| grocery_fresh | 0.9333 | 1.0000 | 0.9655 |
| other_support | 0.0000 | 0.0000 | 0.0000 |
| product_availability | 0.8235 | 1.0000 | 0.9032 |
| promotions_pricing | 0.9286 | 0.9286 | 0.9286 |
| returns_refunds | 1.0000 | 0.8125 | 0.8966 |

## Worst Performing Intents
- **other_support**: F1 = 0.0000
- **delivery_wrong_item**: F1 = 0.4762
- **account_access**: F1 = 0.7027

## Most Confused Intent Pairs
- True **account_access** mispredicted as **delivery_wrong_item** (8 times)
- True **delivery_missing** mispredicted as **delivery_delayed** (2 times)
- True **delivery_wrong_item** mispredicted as **account_access** (2 times)
- True **returns_refunds** mispredicted as **delivery_delayed** (2 times)
- True **account_billing** mispredicted as **account_access** (1 times)
