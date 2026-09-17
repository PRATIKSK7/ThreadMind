# Taxonomy Quality Assessment

## Coverage
The 14 intent categories provide robust coverage over the most frequent domains in the `AmazonHelp` corpus: Fulfillment, Returns, Digital Devices, and Account Billing. A large number of threads fall into the long tail of "other_support", but our taxonomy explicitly covers the 14 dominant repeatable patterns. All 14 intents are now successfully represented in the Golden Set (14 examples each).

## Class Imbalance
Real support data is naturally imbalanced. 
- **Dominant Classes**: `returns_refunds` (8,068 threads) and `account_billing` (6,442 threads) dominate the dataset. This reflects the reality that financial disputes drive users to social media.
- **Minority Classes**: `grocery_fresh` (611) and `delivery_wrong_item` (562) are much rarer. 

We deliberately did not artificially balance the dataset sizes during discovery, as recognizing the true distribution of support load is critical for evaluating agent scalability. However, the Golden Set will be stratified to guarantee that minority intents are thoroughly evaluated.

## Ambiguity and Overlap
As documented in the confusion sets, there is high overlap between delivery intents. For instance, a customer might say "My item is late and now I want a refund." In these cases, the primary intent is determined by the action the agent must take (`returns_refunds` takes precedence because it requires processing a financial return, whereas a delay is just informational).

## Granularity
The taxonomy avoids overly broad categories like "Customer Service Issue", splitting them into functional domains (Delivery vs Returns vs Billing). Simultaneously, we avoided creating hyper-narrow categories (e.g., splitting `digital_prime_video` into `prime_video_app_crash` and `prime_video_buffering`), keeping the taxonomy practical for a high-level router.
