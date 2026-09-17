# Phase 16D — Conservative Policy Pilot

- V2 Accuracy: 87.76%
- Conservative Accuracy: 87.24%
- Improvements: 14
- Regressions: 15

## Detailed Cases
- **IMPROVEMENT**: `9d4ee10b51d6518c`. Expected: `delivery_missing`, V2: `amazon_locker`, Cons: `delivery_missing`. Top3: ['delivery_missing', 'delivery_missing', 'delivery_missing']
- **IMPROVEMENT**: `2555a8d9872a2f15`. Expected: `delivery_missing`, V2: `amazon_locker`, Cons: `delivery_missing`. Top3: ['delivery_missing', 'delivery_missing', 'delivery_missing']
- **REGRESSION**: `37bacc4a02a35a8b`. Expected: `delivery_wrong_item`, V2: `delivery_wrong_item`, Cons: `delivery_missing`. Top3: ['delivery_missing', 'delivery_missing', 'delivery_delayed']
- **REGRESSION**: `72784fad0c2d64eb`. Expected: `delivery_wrong_item`, V2: `delivery_wrong_item`, Cons: `delivery_missing`. Top3: ['delivery_wrong_item', 'delivery_missing', 'delivery_missing']
- **IMPROVEMENT**: `548c4f7b87a573e3`. Expected: `account_billing`, V2: `other_support`, Cons: `account_billing`. Top3: ['account_billing', 'account_billing', 'account_billing']
- **IMPROVEMENT**: `5bdc103dceaa85cc`. Expected: `account_billing`, V2: `other_support`, Cons: `account_billing`. Top3: ['account_billing', 'account_billing', 'account_billing']
- **REGRESSION**: `d6cf59dcf89bf508`. Expected: `account_billing`, V2: `account_billing`, Cons: `account_access`. Top3: ['delivery_wrong_item', 'account_access', 'account_access']
- **IMPROVEMENT**: `e6aef6c530ba4876`. Expected: `digital_prime_video`, V2: `other_support`, Cons: `digital_prime_video`. Top3: ['digital_prime_video', 'digital_prime_video', 'digital_prime_video']
- **REGRESSION**: `39c418bf1848d060`. Expected: `digital_kindle`, V2: `digital_kindle`, Cons: `amazon_locker`. Top3: ['amazon_locker', 'amazon_locker', 'amazon_locker']
- **IMPROVEMENT**: `a0cb92cfb35738bb`. Expected: `digital_kindle`, V2: `other_support`, Cons: `digital_kindle`. Top3: ['digital_kindle', 'digital_kindle', 'digital_kindle']
- **REGRESSION**: `a6dbcc41eea15111`. Expected: `amazon_music`, V2: `amazon_music`, Cons: `echo_alexa`. Top3: ['delivery_delayed', 'echo_alexa', 'echo_alexa']
- **IMPROVEMENT**: `4c2ba68f8d6d8d01`. Expected: `echo_alexa`, V2: `other_support`, Cons: `echo_alexa`. Top3: ['echo_alexa', 'delivery_delayed', 'echo_alexa']
- **IMPROVEMENT**: `59b64538302cb337`. Expected: `echo_alexa`, V2: `other_support`, Cons: `echo_alexa`. Top3: ['echo_alexa', 'echo_alexa', 'amazon_music']
- **IMPROVEMENT**: `7407c0dd1c4a8822`. Expected: `account_access`, V2: `delivery_wrong_item`, Cons: `account_access`. Top3: ['account_access', 'delivery_delayed', 'account_access']
- **REGRESSION**: `f96b9b10c4206c30`. Expected: `delivery_wrong_item`, V2: `delivery_wrong_item`, Cons: `account_access`. Top3: ['account_access', 'account_access', 'account_access']
- **REGRESSION**: `b916108101eca175`. Expected: `delivery_wrong_item`, V2: `delivery_wrong_item`, Cons: `account_access`. Top3: ['account_access', 'account_billing', 'account_access']
- **IMPROVEMENT**: `7e10f8a5300df65c`. Expected: `account_access`, V2: `delivery_wrong_item`, Cons: `account_access`. Top3: ['account_access', 'account_access', 'account_access']
- **IMPROVEMENT**: `507a5d959193bd85`. Expected: `promotions_pricing`, V2: `other_support`, Cons: `promotions_pricing`. Top3: ['delivery_delayed', 'promotions_pricing', 'promotions_pricing']
- **REGRESSION**: `663015f372cd3b8a`. Expected: `promotions_pricing`, V2: `promotions_pricing`, Cons: `returns_refunds`. Top3: ['returns_refunds', 'returns_refunds', 'returns_refunds']
- **IMPROVEMENT**: `a3b31228d3f292c5`. Expected: `promotions_pricing`, V2: `other_support`, Cons: `promotions_pricing`. Top3: ['promotions_pricing', 'promotions_pricing', 'promotions_pricing']
- **REGRESSION**: `1df63ea1d5a69936`. Expected: `amazon_locker`, V2: `amazon_locker`, Cons: `delivery_missing`. Top3: ['delivery_missing', 'delivery_missing', 'delivery_missing']
- **REGRESSION**: `baa82fe4c3c04a25`. Expected: `amazon_locker`, V2: `amazon_locker`, Cons: `returns_refunds`. Top3: ['returns_refunds', 'returns_refunds', 'delivery_delayed']
- **REGRESSION**: `9d048a20fd47ab7f`. Expected: `grocery_fresh`, V2: `grocery_fresh`, Cons: `returns_refunds`. Top3: ['returns_refunds', 'delivery_wrong_item', 'returns_refunds']
- **REGRESSION**: `4659bf7cb80e967a`. Expected: `grocery_fresh`, V2: `grocery_fresh`, Cons: `account_billing`. Top3: ['account_billing', 'account_billing', 'account_billing']
- **REGRESSION**: `51a322d37e9a7679`. Expected: `grocery_fresh`, V2: `grocery_fresh`, Cons: `returns_refunds`. Top3: ['delivery_delayed', 'returns_refunds', 'returns_refunds']
- **REGRESSION**: `e84a7e6d5d4a4373`. Expected: `grocery_fresh`, V2: `grocery_fresh`, Cons: `returns_refunds`. Top3: ['returns_refunds', 'returns_refunds', 'delivery_delayed']
- **IMPROVEMENT**: `7fa5ccca8702f290`. Expected: `product_availability`, V2: `other_support`, Cons: `product_availability`. Top3: ['product_availability', 'product_availability', 'product_availability']
- **IMPROVEMENT**: `058a1adda23bf491`. Expected: `product_availability`, V2: `other_support`, Cons: `product_availability`. Top3: ['product_availability', 'product_availability', 'product_availability']
- **REGRESSION**: `c5f3c1301f833cc0`. Expected: `product_availability`, V2: `product_availability`, Cons: `promotions_pricing`. Top3: ['promotions_pricing', 'promotions_pricing', 'promotions_pricing']
