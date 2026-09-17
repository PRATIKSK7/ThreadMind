# Decision Log

## Step 2: Data Ingestion and Quality Audit

| Decision | Reason | Trade-off / Limitation |
|---|---|---|
| **Raw dataset kept immutable** | Ensures reproducibility and allows recovery from processing errors. | Costs extra storage when we write processed outputs, but protects data integrity. |
| **IDs treated as strings** | Twitter IDs are large integers. Pandas defaults to float64 for columns with nulls, losing precision on large IDs. | Marginally higher memory usage than `Int64`, but 100% precision safety. |
| **Audit performed before cleaning** | We need a true picture of the dataset's flaws (duplicates, empty text, orphans) to justify cleaning steps. | Audit script might take longer since it processes noisy, unstructured data. |
| **Final brand selection deferred** | The instructions forbid automatic selection. Human review is required to verify usefulness. | Delays the pipeline slightly until a human acts. |
| **Thread relationships preserved** | Single tweets lack conversational context. We must preserve multi-turn structures to evaluate RAG properly. | Reconstruction logic will be complex and computationally expensive. |
| **Full dataset not committed to Git** | The dataset is ~500MB and would bloat the repository history unnecessarily. | Requires a local copy or automated download step for new developers. |
| **Reproducibility through deterministic processing** | We use explicit random seeds and chronological sorting to guarantee the same outputs every time. | None. |

## Step 3: Empirical Brand Comparison and Thread Reconstruction

| Decision | Reason | Trade-off / Limitation |
|---|---|---|
| **In-Memory Graph Construction** | Parsing 2.8M rows using Pandas `groupby` or `merge` is heavily memory/time inefficient for multi-level hierarchical trees. A Python dictionary mapping is much faster. | Dicts require ~300MB RAM but complete in seconds compared to minutes/hours for pure Pandas. |
| **Branch Preservation** | Real threads sometimes branch (e.g. customer replies twice to the same message). We preserve the entire tree in a chronological list rather than enforcing a single linear path. | Thread structures can become slightly confusing if branches are deep, requiring intelligent rendering later. |
| **Deterministic Thread IDs** | Re-running the pipeline must produce the same exact IDs for consistency in downstream evaluation sets. | We hash the `root_tweet_id` to generate a 16-char thread ID. |
| **Non-destructive Filtering** | Quality issues like `has_missing_parent` or `branch_detected` are tagged in metadata rather than deleting the thread. | Downstream processes must actively filter out bad threads. |

## Step 4: Intent Taxonomy & Golden Set

| Decision | Reason | Trade-off / Limitation |
|---|---|---|
| **Heuristic-Driven Taxonomy** | Because LLMs were banned for this step, intent clustering was performed using deterministic TF-IDF extraction and regular expressions over 82k threads. | Heavily relies on keyword presence, which may fail on subtle or misspelled queries, but perfectly fulfills the "No Model Yet" and reproducibility requirements. |
| **14 Intent Categories** | Kept domains strictly isolated (e.g. `digital_kindle` vs `digital_prime_video` vs `account_access`) based on empirical data distribution. All 14 intents are represented in the Golden Set. | A long tail of "Other Support" queries remains unclassified. |
| **Stratified Golden Sampling** | Pure random sampling might miss rare intents or long conversations. We explicitly stratified across 14 intents and 3 length buckets (short, medium, long) to hit exactly 196 examples (14 per intent). | Forces a balanced representation that doesn't strictly match the highly imbalanced global distribution, ensuring rare intents are tested. |
| **Thread-Level Isolation** | Golden set sampling claims the *entire* thread history, rather than splitting single messages. An explicit audit verified zero data leakage. | Reduces available training data slightly, but provides an airtight firewall against data leakage. |
| **Deterministic Escalation** | Replaced naive length limits with semantic heuristics detecting looping (e.g. "didn't work") or human-intervention requests. Classified into `no_escalation`, `clarification_needed`, or `human_review_recommended`. | Lacks nuanced human interpretation for complex edge cases, but scales deterministically for a 200-example benchmark. |

## Phase 4: Reply Generation and LLM Judge Evaluation

| Decision | Reason | Trade-off / Limitation |
|---|---|---|
| **Deterministic Generation (Temperature=0.0)** | Ensures that generated replies are 100% reproducible for a given input + context pair. | Limits creative phrasing but maximizes consistency in evaluation. |
| **LLM-as-Judge using Zero-Shot Llama 3.2** | Maintains the "Local / Offline Only" requirement while enabling automated scaling of generation grading. | 3B parameter models are notoriously weak judges compared to GPT-4. They may hallucinate their own evaluations. |
| **0.95 Strict Threshold Maintained** | A lower threshold drastically reduces the Golden Set accuracy by intercepting ambiguous edge cases. Accuracy was prioritized over fallback rate. | Generates a 67% LLM fallback rate, which is expensive in production. |
| **Human Scoring Sub-sampling** | Output exactly 30 replies to CSV for blind human evaluation. | Due to time constraints, actual human evaluation (and Cohen's Kappa) could not be executed immediately. |
| **Ollama API Raw Post** | Custom JSON extraction was bypassed for raw string outputs from Ollama, because the generation prompt asks for raw text, not JSON. | Disables built-in json\_mode safeguards, but allows natural language generation. |

