# Amazon Dataset Traceability Audit

## Dataset Source
- **Original Dataset**: Customer Support on Twitter (twcs.csv)
- **Total Tweets in Raw Dataset**: 2,811,774
- **Selected Brand**: Amazon (@AmazonHelp)
- **Brand Tweets in Dataset**: 169,840
- **Estimated Inbound Amazon Threads**: 135,160

## Pipeline Methodology
The raw tweets were chronologically reconstructed into conversation threads. Amazon-related threads were isolated, and a representative subset was sampled to form the evaluation benchmark.

## Golden Set Provenance
- **Size**: 196 hand-labeled examples
- **Brand Scope**: 100% Amazon customer support scenarios
- **Validation**: Meets the assignment requirement of approximately 150-250 hand-labeled examples.
- **Preprocessing**: Preserves conversational structure, annotates `expected_behavior`, `intent_id`, and `escalation`.
