# Phase 13A — Query Representation Pilot

## Candidate Representations

| Representation | R@1 | R@3 | R@5 | MRR@3 |
|---|---:|---:|---:|---:|
| BASELINE | 64.80% | 77.55% | 79.59% | 0.7083 |
| QUERY_ONLY | 64.29% | 77.04% | 80.10% | 0.7032 |
| USER_AGENT | 64.80% | 77.55% | 79.59% | 0.7083 |
| STRUCTURED | 63.78% | 78.57% | 81.63% | 0.7032 |
| KEYWORD-AUGMENTED | 65.82% | 77.55% | 80.61% | 0.7151 |
| LAST-USER-TURN | 20.41% | 32.14% | 38.78% | 0.2534 |

## Paired Improvements

| Representation | Improved | Regressed | Unchanged | Net |
|---|---:|---:|---:|---:|
| QUERY_ONLY | 19 | 17 | 160 | 2 |
| USER_AGENT | 0 | 0 | 196 | 0 |
| STRUCTURED | 15 | 16 | 165 | -1 |
| KEYWORD-AUGMENTED | 8 | 5 | 183 | 3 |
| LAST-USER-TURN | 15 | 117 | 64 | -102 |

## Intent-Level Results (Recall@3)

| Intent | BASELINE | QUERY_ONLY | USER_AGENT | STRUCTURED | KEYWORD-AUGMENTED | LAST-USER-TURN |
|---|---:|---:|---:|---:|---:|---:|
| account_access | 66.7% | 66.7% | 66.7% | 71.4% | 66.7% | 23.8% |
| account_billing | 92.9% | 100.0% | 92.9% | 92.9% | 92.9% | 42.9% |
| amazon_locker | 76.9% | 53.8% | 76.9% | 69.2% | 76.9% | 15.4% |
| amazon_music | 92.9% | 92.9% | 92.9% | 92.9% | 92.9% | 7.1% |
| delivery_delayed | 83.3% | 91.7% | 83.3% | 83.3% | 83.3% | 41.7% |
| delivery_missing | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 53.3% |
| delivery_wrong_item | 14.3% | 14.3% | 14.3% | 28.6% | 14.3% | 0.0% |
| digital_kindle | 78.6% | 78.6% | 78.6% | 78.6% | 78.6% | 7.1% |
| digital_prime_video | 85.7% | 92.9% | 85.7% | 92.9% | 85.7% | 21.4% |
| echo_alexa | 92.9% | 85.7% | 92.9% | 92.9% | 92.9% | 35.7% |
| grocery_fresh | 14.3% | 14.3% | 14.3% | 21.4% | 14.3% | 0.0% |
| product_availability | 78.6% | 78.6% | 78.6% | 78.6% | 78.6% | 57.1% |
| promotions_pricing | 78.6% | 78.6% | 78.6% | 71.4% | 78.6% | 35.7% |
| returns_refunds | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 87.5% |

## Confusion Boundary Analysis (Top 5)

Shows number of queries where the 'confuser' intent was ranked higher than the correct intent.

| Boundary | BASELINE | QUERY_ONLY | USER_AGENT | STRUCTURED | KEYWORD-AUGMENTED | LAST-USER-TURN |
|---|---:|---:|---:|---:|---:|---:|
| account_access <-> delivery_wrong_item | 9 | 8 | 9 | 8 | 8 | 2 |
| account_access <-> delivery_missing | 4 | 5 | 4 | 4 | 4 | 13 |
| account_access <-> delivery_delayed | 2 | 2 | 2 | 2 | 2 | 9 |
| grocery_fresh <-> returns_refunds | 8 | 6 | 8 | 8 | 10 | 12 |
| account_billing <-> grocery_fresh | 4 | 4 | 4 | 3 | 6 | 3 |
| amazon_locker <-> delivery_missing | 3 | 6 | 3 | 6 | 3 | 7 |
| delivery_delayed <-> returns_refunds | 5 | 3 | 5 | 5 | 4 | 10 |

## Failure Examples

### QUERY_ONLY changed queries
- ✅ `1d34fe17e6385fba` (delivery_delayed): Rank 999 → 1
- ✅ `136747dbfd949f68` (returns_refunds): Rank 2 → 1
- ✅ `9bd9508fd74f46c4` (delivery_delayed): Rank 999 → 4
- ✅ `1e9fb1462c55081f` (delivery_missing): Rank 2 → 1
- ✅ `0d7053cbb502d63a` (delivery_missing): Rank 2 → 1
- ✅ `5fc32478a3b63ac7` (delivery_wrong_item): Rank 999 → 3
- ✅ `20cce9b10faebf82` (account_access): Rank 4 → 2
- ✅ `d25f65835961b06a` (account_access): Rank 999 → 5
- ✅ `5bdc103dceaa85cc` (account_billing): Rank 999 → 1
- ✅ `7906799da7f63453` (digital_prime_video): Rank 4 → 1
- ✅ `24d6b4a375ee21d6` (digital_kindle): Rank 2 → 1
- ✅ `547be894014b4903` (digital_kindle): Rank 2 → 1
- ✅ `811b3d82afdfeb33` (digital_kindle): Rank 2 → 1
- ✅ `c4dfa7c7bd5687f2` (echo_alexa): Rank 3 → 1
- ✅ `8b231a42dfff628d` (account_access): Rank 2 → 1
- ✅ `b75b8aba4b7a9baf` (amazon_locker): Rank 999 → 2
- ✅ `8ce1398a13df32c7` (grocery_fresh): Rank 4 → 2
- ✅ `1da537bb39d637d6` (product_availability): Rank 2 → 1
- ✅ `ebefc67d2ab0c89b` (product_availability): Rank 999 → 4
- ❌ `ffdab40197f48de2` (delivery_delayed): Rank 1 → 3
- ❌ `788e6b6ab3ad975f` (delivery_delayed): Rank 1 → 2
- ❌ `979bcf1ba7572381` (delivery_missing): Rank 1 → 2
- ❌ `dd3f0d83804bec2a` (delivery_wrong_item): Rank 1 → 999
- ❌ `583e80a133042b71` (returns_refunds): Rank 1 → 2
- ❌ `61d93d9d63543125` (account_billing): Rank 1 → 2
- ❌ `b7fe8e583253b111` (echo_alexa): Rank 1 → 999
- ❌ `fbb7f3a219b04208` (account_access): Rank 1 → 2
- ❌ `7407c0dd1c4a8822` (account_access): Rank 3 → 999
- ❌ `6177b8cf868e7f36` (account_access): Rank 4 → 999
- ❌ `d766800f05f78196` (amazon_locker): Rank 1 → 999
- ❌ `8311a3c79d0be7ff` (amazon_locker): Rank 2 → 5
- ❌ `962f87319795305d` (amazon_locker): Rank 1 → 4
- ❌ `88d34caa84fe33cf` (amazon_locker): Rank 1 → 2
- ❌ `97d46e56ad05b8e3` (amazon_locker): Rank 2 → 999
- ❌ `f3e2bfa73a8376a8` (grocery_fresh): Rank 1 → 4
- ❌ `92a7b4c25fb7c2f3` (product_availability): Rank 1 → 2

### STRUCTURED changed queries
- ✅ `1d34fe17e6385fba` (delivery_delayed): Rank 999 → 5
- ✅ `9bd9508fd74f46c4` (delivery_delayed): Rank 999 → 5
- ✅ `1e9fb1462c55081f` (delivery_missing): Rank 2 → 1
- ✅ `0d7053cbb502d63a` (delivery_missing): Rank 2 → 1
- ✅ `5fc32478a3b63ac7` (delivery_wrong_item): Rank 999 → 3
- ✅ `20cce9b10faebf82` (account_access): Rank 4 → 2
- ✅ `d25f65835961b06a` (account_access): Rank 999 → 3
- ✅ `5bdc103dceaa85cc` (account_billing): Rank 999 → 4
- ✅ `7906799da7f63453` (digital_prime_video): Rank 4 → 1
- ✅ `3bb93e2f47e6c826` (digital_prime_video): Rank 2 → 1
- ✅ `547be894014b4903` (digital_kindle): Rank 2 → 1
- ✅ `124e29ffa7d5085f` (echo_alexa): Rank 2 → 1
- ✅ `c4dfa7c7bd5687f2` (echo_alexa): Rank 3 → 1
- ✅ `b75b8aba4b7a9baf` (amazon_locker): Rank 999 → 4
- ✅ `8ce1398a13df32c7` (grocery_fresh): Rank 4 → 2
- ❌ `979bcf1ba7572381` (delivery_missing): Rank 1 → 2
- ❌ `3f03050f2ccd56e1` (delivery_missing): Rank 1 → 3
- ❌ `df577fc749f849fc` (account_access): Rank 1 → 2
- ❌ `dd3f0d83804bec2a` (delivery_wrong_item): Rank 1 → 2
- ❌ `507666bffe853255` (returns_refunds): Rank 2 → 3
- ❌ `2516a81a039f9f65` (account_billing): Rank 2 → 3
- ❌ `7407c0dd1c4a8822` (account_access): Rank 3 → 999
- ❌ `c763f518de8ef948` (account_access): Rank 1 → 2
- ❌ `2d269faf8a58863e` (promotions_pricing): Rank 3 → 4
- ❌ `a2bbc722057b5719` (promotions_pricing): Rank 2 → 3
- ❌ `a3b31228d3f292c5` (promotions_pricing): Rank 1 → 2
- ❌ `8311a3c79d0be7ff` (amazon_locker): Rank 2 → 3
- ❌ `962f87319795305d` (amazon_locker): Rank 1 → 3
- ❌ `88d34caa84fe33cf` (amazon_locker): Rank 1 → 3
- ❌ `97d46e56ad05b8e3` (amazon_locker): Rank 2 → 999
- ❌ `f3e2bfa73a8376a8` (grocery_fresh): Rank 1 → 2

### KEYWORD-AUGMENTED changed queries
- ✅ `1d34fe17e6385fba` (delivery_delayed): Rank 999 → 4
- ✅ `136747dbfd949f68` (returns_refunds): Rank 2 → 1
- ✅ `d25f65835961b06a` (account_access): Rank 999 → 4
- ✅ `e0e2bacc798bff2b` (digital_kindle): Rank 999 → 1
- ✅ `547be894014b4903` (digital_kindle): Rank 2 → 1
- ✅ `124e29ffa7d5085f` (echo_alexa): Rank 2 → 1
- ✅ `7407c0dd1c4a8822` (account_access): Rank 3 → 2
- ✅ `9df66edc158ef84e` (account_access): Rank 2 → 1
- ❌ `875009abfa44529c` (digital_kindle): Rank 1 → 2
- ❌ `17b4e0cd5b4ccece` (digital_kindle): Rank 3 → 4
- ❌ `962f87319795305d` (amazon_locker): Rank 1 → 2
- ❌ `88d34caa84fe33cf` (amazon_locker): Rank 1 → 2
- ❌ `8ce1398a13df32c7` (grocery_fresh): Rank 4 → 999

### LAST-USER-TURN changed queries
- ✅ `136747dbfd949f68` (returns_refunds): Rank 2 → 1
- ✅ `9bd9508fd74f46c4` (delivery_delayed): Rank 999 → 1
- ✅ `1e9fb1462c55081f` (delivery_missing): Rank 2 → 1
- ✅ `971d58ab9348de04` (account_access): Rank 999 → 3
- ✅ `20cce9b10faebf82` (account_access): Rank 4 → 1
- ✅ `b614a28772a4ff9a` (returns_refunds): Rank 2 → 1
- ✅ `5bdc103dceaa85cc` (account_billing): Rank 999 → 3
- ✅ `17b4e0cd5b4ccece` (digital_kindle): Rank 3 → 2
- ✅ `8b231a42dfff628d` (account_access): Rank 2 → 1
- ✅ `5d58b0bdefae1299` (promotions_pricing): Rank 999 → 2
- ✅ `b75b8aba4b7a9baf` (amazon_locker): Rank 999 → 1
- ✅ `e4b818ccb8232155` (amazon_locker): Rank 999 → 4
- ✅ `1da537bb39d637d6` (product_availability): Rank 2 → 1
- ✅ `079b146a88a14dc0` (product_availability): Rank 2 → 1
- ✅ `c5f3c1301f833cc0` (product_availability): Rank 999 → 2
- ❌ `d3a37c0eb6a2e1af` (delivery_delayed): Rank 1 → 999
- ❌ `6128774c272909e7` (delivery_delayed): Rank 1 → 2
- ❌ `7dd3e41677eca8cf` (delivery_delayed): Rank 1 → 3
- ❌ `66b6dfde5ea6a023` (delivery_delayed): Rank 1 → 999
- ❌ `6211a9e0735ee03b` (delivery_delayed): Rank 1 → 5
- ❌ `da35f7dc09d3f8d2` (delivery_delayed): Rank 1 → 5
- ❌ `c329621fdd6a6860` (delivery_delayed): Rank 1 → 999
- ❌ `788e6b6ab3ad975f` (delivery_delayed): Rank 1 → 999
- ❌ `564d4563079bdbfb` (delivery_missing): Rank 1 → 5
- ❌ `c01dbc075c112a90` (delivery_missing): Rank 1 → 999
- ❌ `9d4ee10b51d6518c` (delivery_missing): Rank 1 → 3
- ❌ `26e37f657a9242c0` (delivery_missing): Rank 1 → 999
- ❌ `d62bfab11ba69a91` (delivery_missing): Rank 1 → 2
- ❌ `44e4104210bad607` (delivery_missing): Rank 1 → 4
- ❌ `3f03050f2ccd56e1` (delivery_missing): Rank 1 → 3
- ❌ `1812ebbdb250a03e` (delivery_missing): Rank 1 → 4
- ❌ `c9b23242d5347d51` (delivery_missing): Rank 1 → 999
- ❌ `0d7053cbb502d63a` (delivery_missing): Rank 2 → 4
- ❌ `2555a8d9872a2f15` (delivery_missing): Rank 1 → 3
- ❌ `25ca3ab474dd691d` (account_access): Rank 1 → 5
- ❌ `df577fc749f849fc` (account_access): Rank 1 → 999
- ❌ `aa1845b17e22923e` (account_access): Rank 1 → 3
- ❌ `dd3f0d83804bec2a` (delivery_wrong_item): Rank 1 → 999
- ❌ `09b03780f7d6795f` (returns_refunds): Rank 1 → 3
- ❌ `507666bffe853255` (returns_refunds): Rank 2 → 999
- ❌ `9cae32f77fa87a38` (returns_refunds): Rank 1 → 2
- ❌ `acbce372aa4fd05c` (returns_refunds): Rank 1 → 3
- ❌ `deff7ff8ef25e07d` (returns_refunds): Rank 1 → 4
- ❌ `583e80a133042b71` (returns_refunds): Rank 1 → 2
- ❌ `6aae04ebe65fd679` (returns_refunds): Rank 1 → 3
- ❌ `78620867b16ba960` (account_billing): Rank 1 → 2
- ❌ `548c4f7b87a573e3` (account_billing): Rank 1 → 999
- ❌ `2e3f3cc2c3e5aaf3` (account_billing): Rank 1 → 999
- ❌ `2516a81a039f9f65` (account_billing): Rank 2 → 999
- ❌ `61d93d9d63543125` (account_billing): Rank 1 → 999
- ❌ `c1b7a8c0f138c843` (account_billing): Rank 1 → 5
- ❌ `0e5b9b2c0a94881f` (account_billing): Rank 2 → 999
- ❌ `9ff3f7dcf8a34d52` (account_billing): Rank 1 → 999
- ❌ `ddc983b3b471f230` (account_billing): Rank 1 → 999
- ❌ `7906799da7f63453` (digital_prime_video): Rank 4 → 999
- ❌ `d0a24e717d769d53` (digital_prime_video): Rank 1 → 999
- ❌ `63cd9fc1dff215fe` (digital_prime_video): Rank 1 → 999
- ❌ `0a0634610b8e0e15` (digital_prime_video): Rank 1 → 999
- ❌ `e6aef6c530ba4876` (digital_prime_video): Rank 1 → 999
- ❌ `e2c6b4110efb929a` (digital_prime_video): Rank 1 → 999
- ❌ `573ffd6be31435a7` (digital_prime_video): Rank 1 → 999
- ❌ `bf9c3cb5c69de4ea` (digital_prime_video): Rank 1 → 999
- ❌ `3bb93e2f47e6c826` (digital_prime_video): Rank 2 → 999
- ❌ `400491ccf469b530` (digital_prime_video): Rank 1 → 999
- ❌ `d773ff9dfa682357` (digital_kindle): Rank 1 → 999
- ❌ `d4bf43a13c2232a4` (digital_kindle): Rank 1 → 999
- ❌ `f3b9d9f09b657817` (digital_kindle): Rank 1 → 999
- ❌ `935824c4704c860b` (digital_kindle): Rank 1 → 999
- ❌ `875009abfa44529c` (digital_kindle): Rank 1 → 999
- ❌ `e4e2152608ade08d` (digital_kindle): Rank 1 → 999
- ❌ `24d6b4a375ee21d6` (digital_kindle): Rank 2 → 999
- ❌ `547be894014b4903` (digital_kindle): Rank 2 → 999
- ❌ `a0cb92cfb35738bb` (digital_kindle): Rank 1 → 999
- ❌ `811b3d82afdfeb33` (digital_kindle): Rank 2 → 999
- ❌ `15f5c05258eab8c8` (amazon_music): Rank 1 → 999
- ❌ `fa4e4850dc1714f0` (amazon_music): Rank 1 → 999
- ❌ `07c5e73971f78e86` (amazon_music): Rank 1 → 999
- ❌ `f6a518e270c277ae` (amazon_music): Rank 1 → 999
- ❌ `63b3f781506205d3` (amazon_music): Rank 1 → 999
- ❌ `acd6f1d0d28dc947` (amazon_music): Rank 1 → 999
- ❌ `5d794124ada5a1f9` (amazon_music): Rank 1 → 999
- ❌ `e91c71a242ee6355` (amazon_music): Rank 1 → 999
- ❌ `6740224804dec314` (amazon_music): Rank 1 → 999
- ❌ `d8ba70b3c92b7b78` (amazon_music): Rank 1 → 999
- ❌ `957c35145701a2e6` (amazon_music): Rank 1 → 999
- ❌ `54def58a96d81403` (amazon_music): Rank 1 → 999
- ❌ `d5047fc16cd0e349` (echo_alexa): Rank 1 → 999
- ❌ `124e29ffa7d5085f` (echo_alexa): Rank 2 → 999
- ❌ `cdc4792145fc1397` (echo_alexa): Rank 2 → 999
- ❌ `0be61a30ba12a5e0` (echo_alexa): Rank 1 → 2
- ❌ `5869ba28a48cf763` (echo_alexa): Rank 1 → 999
- ❌ `15417200d18d8247` (echo_alexa): Rank 1 → 999
- ❌ `4c2ba68f8d6d8d01` (echo_alexa): Rank 1 → 999
- ❌ `59b64538302cb337` (echo_alexa): Rank 1 → 999
- ❌ `c4dfa7c7bd5687f2` (echo_alexa): Rank 3 → 999
- ❌ `fbb7f3a219b04208` (account_access): Rank 1 → 999
- ❌ `c4943ba47c397940` (account_access): Rank 1 → 999
- ❌ `7407c0dd1c4a8822` (account_access): Rank 3 → 999
- ❌ `9df66edc158ef84e` (account_access): Rank 2 → 999
- ❌ `e8d28e94aab63200` (account_access): Rank 1 → 999
- ❌ `424b7075b73da620` (account_access): Rank 1 → 999
- ❌ `086732e38ad7c1f5` (account_access): Rank 1 → 999
- ❌ `c763f518de8ef948` (account_access): Rank 1 → 999
- ❌ `d1f22969cd0ed8e7` (account_access): Rank 1 → 999
- ❌ `6177b8cf868e7f36` (account_access): Rank 4 → 999
- ❌ `7e10f8a5300df65c` (account_access): Rank 1 → 2
- ❌ `271f08dfe4b24f20` (promotions_pricing): Rank 1 → 999
- ❌ `2d269faf8a58863e` (promotions_pricing): Rank 3 → 999
- ❌ `a2bbc722057b5719` (promotions_pricing): Rank 2 → 999
- ❌ `94623b4fdd7ab5bf` (promotions_pricing): Rank 1 → 999
- ❌ `9f194783f7dbfae8` (promotions_pricing): Rank 1 → 4
- ❌ `b881f26bc54d6db1` (promotions_pricing): Rank 1 → 999
- ❌ `f80ee1ce26d346fd` (promotions_pricing): Rank 1 → 999
- ❌ `d766800f05f78196` (amazon_locker): Rank 1 → 999
- ❌ `9e9de62e088affbc` (amazon_locker): Rank 1 → 999
- ❌ `8311a3c79d0be7ff` (amazon_locker): Rank 2 → 999
- ❌ `962f87319795305d` (amazon_locker): Rank 1 → 999
- ❌ `e1e6809c33e1958c` (amazon_locker): Rank 1 → 999
- ❌ `20c1a80b2496fb80` (delivery_missing): Rank 1 → 2
- ❌ `88d34caa84fe33cf` (amazon_locker): Rank 1 → 999
- ❌ `fc5e5ed945b5af36` (amazon_locker): Rank 1 → 999
- ❌ `0303b444819797be` (amazon_locker): Rank 1 → 999
- ❌ `97d46e56ad05b8e3` (amazon_locker): Rank 2 → 999
- ❌ `baa82fe4c3c04a25` (amazon_locker): Rank 1 → 2
- ❌ `8ce1398a13df32c7` (grocery_fresh): Rank 4 → 999
- ❌ `5de6e76b4a73d660` (grocery_fresh): Rank 1 → 999
- ❌ `f3e2bfa73a8376a8` (grocery_fresh): Rank 1 → 999
- ❌ `7fa5ccca8702f290` (product_availability): Rank 1 → 5
- ❌ `220588c05e025c77` (product_availability): Rank 1 → 999
- ❌ `058a1adda23bf491` (product_availability): Rank 1 → 4
- ❌ `b0889d80badcbecd` (product_availability): Rank 1 → 999
- ❌ `8fac12fcb3126ce8` (product_availability): Rank 2 → 3

## Winner Selection
**NO_CLEAR_RETRIEVAL_GAIN**

## Production Safety
- Golden Set modified: NO
- FAISS modified: NO
- MNRL model modified: NO
- Production code modified: NO

Recommended next phase:
PHASE 13B — CLASSIFIER PROMPT DIAGNOSTIC
