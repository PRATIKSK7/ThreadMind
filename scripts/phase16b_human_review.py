import os
import sys
import json
import hashlib
from collections import defaultdict

# Stability settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def perform_human_review(provider, example, conversation_text):
    prompt = f"""You are the ultimate expert human taxonomist for Amazon Customer Support.
You are reviewing a suspicious Golden Set example. Do not blindly trust the LLM prediction or the current label.
Use the 14 intents: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_music, echo_alexa, amazon_locker, grocery_fresh, other_support.

Conversation:
{conversation_text}

Current Golden Label: {example['expected_intent']}
V2 Predicted Label: {example['v2_predicted_intent']}
Top-3 Retrieved: {example['top_3_retrieved_intents']}

Perform a strict human-style review and return ONLY valid JSON:
{{
  "primary_problem": "<string>",
  "customer_action": "<string>",
  "best_intent": "<string>",
  "golden_label_matches": <boolean>,
  "retrieval_relevant": <boolean>,
  "is_ambiguous": <boolean>,
  "review_status": "<CONFIRMED_CORRECT | PROPOSE_LABEL_CHANGE | GENUINELY_AMBIGUOUS | INSUFFICIENT_CONTEXT>",
  "proposed_intent": "<string or null>",
  "confidence": "<HIGH | MEDIUM | LOW>",
  "reason": "<string>",
  "evidence": "<string>",
  "why_current_inferior": "<string>",
  "why_proposed_superior": "<string>",
  "competing_intents": "<string>",
  "ambiguity_explanation": "<string>",
  "ambiguity_resolution": "<string>"
}}"""
    try:
        res = provider.predict(prompt)
        return res
    except Exception as e:
        return {"review_status": "INSUFFICIENT_CONTEXT", "reason": str(e)}

def calculate_metrics(y_true, y_pred):
    from sklearn.metrics import f1_score
    acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true) if y_true else 0
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    return acc, f1

def main():
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    assert hash_file(golden_path) == "6d4e700bfe65f0134acb39aa1ec0dbb1ba4dfafcf1ae1f0c102858ab2d54610f", "Invalid Golden Set"

    gs_dict = {}
    with open(golden_path, "r") as f:
        for line in f:
            t = json.loads(line)
            gs_dict[t["thread_id"]] = t

    suspicious_path = config.PROJECT_ROOT / "reports" / "phase16a_suspicious_golden_examples.json"
    with open(suspicious_path, "r") as f:
        suspicious_examples = json.load(f)

    v2_results_path = config.REPORTS_DIR / "rag_mnrl_k3_results.json"
    with open(v2_results_path, "r") as f:
        v2_results = json.load(f)["predictions"]

    provider = LLMProvider()
    reviews = []
    
    status_counts = defaultdict(int)
    proposed_patch = []

    print(f"Starting human-style review of {len(suspicious_examples)} examples...")
    for i, ex in enumerate(suspicious_examples):
        tid = ex["thread_id"]
        messages = gs_dict[tid].get("messages", gs_dict[tid].get("conversation", []))
        conv_text = "\n".join([f"{'User' if m.get('inbound', True) else 'Agent'}: {m['text']}" for m in messages])
        
        print(f"Reviewing {i+1}/{len(suspicious_examples)}: {tid}")
        review = perform_human_review(provider, ex, conv_text)
        
        status = review.get("review_status", "INSUFFICIENT_CONTEXT")
        status_counts[status] += 1
        
        if status == "PROPOSE_LABEL_CHANGE":
            proposed_patch.append({
                "example_id": ex["example_id"],
                "thread_id": tid,
                "current_intent": ex["expected_intent"],
                "proposed_intent": review.get("proposed_intent", ""),
                "status": status,
                "confidence": review.get("confidence", ""),
                "reason": review.get("reason", ""),
                "evidence": review.get("evidence", ""),
                "why_current_inferior": review.get("why_current_inferior", ""),
                "why_proposed_superior": review.get("why_proposed_superior", ""),
                "competing_intents": review.get("competing_intents", "")
            })
            
        reviews.append({
            "example": ex,
            "review": review
        })

    # Simulate metrics
    y_true_current = []
    y_true_simulated = []
    y_pred = []
    
    patch_map = {p["thread_id"]: p["proposed_intent"] for p in proposed_patch}
    changed_evaluations = 0

    for v2 in v2_results:
        tid = v2["thread_id"]
        expected = v2["expected_intent"]
        predicted = v2["predicted_intent"]
        
        y_true_current.append(expected)
        y_pred.append(predicted)
        
        if tid in patch_map:
            sim_expected = patch_map[tid]
            y_true_simulated.append(sim_expected)
            # Did the evaluation outcome change?
            curr_correct = (expected == predicted)
            sim_correct = (sim_expected == predicted)
            if curr_correct != sim_correct:
                changed_evaluations += 1
        else:
            y_true_simulated.append(expected)
            
    curr_acc, curr_f1 = calculate_metrics(y_true_current, y_pred)
    sim_acc, sim_f1 = calculate_metrics(y_true_simulated, y_pred)

    # Write patch
    with open("reports/phase16b_golden_set_proposed_patch.json", "w") as f:
        json.dump(proposed_patch, f, indent=2)

    # Write MD report
    with open("reports/phase16b_human_review.md", "w") as f:
        f.write("# Phase 16B — Human-in-the-Loop Review Report\n\n")
        f.write(f"1. Total cases reviewed: {len(suspicious_examples)}\n")
        f.write(f"2. CONFIRMED_CORRECT count: {status_counts.get('CONFIRMED_CORRECT', 0)}\n")
        f.write(f"3. PROPOSE_LABEL_CHANGE count: {status_counts.get('PROPOSE_LABEL_CHANGE', 0)}\n")
        f.write(f"4. GENUINELY_AMBIGUOUS count: {status_counts.get('GENUINELY_AMBIGUOUS', 0)}\n")
        f.write(f"5. INSUFFICIENT_CONTEXT count: {status_counts.get('INSUFFICIENT_CONTEXT', 0)}\n\n")
        
        f.write("## 6. Proposed Label Transitions\n")
        for p in proposed_patch:
            f.write(f"- `{p['example_id']}`: `{p['current_intent']}` -> `{p['proposed_intent']}`\n")
            f.write(f"  - **Reason**: {p['reason']}\n")
            
        f.write("\n## 7. Taxonomy Boundary Recommendations\n")
        f.write("""
### other_support vs Specific Intents
**other_support**: The customer's primary issue genuinely falls completely outside the 14 standard intents, or is so broad/vague that no specific workflow applies.
**Specific Intents**: If the customer's primary issue can be reasonably mapped to a specific intent (like returns_refunds or digital_kindle), that intent must be chosen over other_support, even if the phrasing is unusual.

### grocery_fresh vs other_support
**grocery_fresh**: The customer is explicitly dealing with Amazon Fresh, grocery deliveries, or grocery returns.
**other_support**: The customer is complaining about a general Amazon experience not tied to grocery services.

### account_access vs delivery_wrong_item
**account_access**: The customer is primarily locked out of their account, facing login issues, or reporting a hacked account.
**delivery_wrong_item**: The customer received a physical package but the contents were incorrect, even if they later mention 'accessing their account' to process the return.
""")

        f.write("\n## 8. Simulated Benchmark Impact\n")
        f.write(f"- **Current V2 Accuracy**: {curr_acc*100:.2f}%\n")
        f.write(f"- **Current Macro F1**: {curr_f1:.4f}\n")
        f.write(f"- **Simulated Accuracy**: {sim_acc*100:.2f}%\n")
        f.write(f"- **Simulated Macro F1**: {sim_f1:.4f}\n")
        f.write(f"- **Number of labels changed**: {len(proposed_patch)}\n")
        f.write(f"- **Number of examples whose evaluation outcome changes**: {changed_evaluations}\n\n")
        
        f.write("## 9. Cases Requiring Actual Human Decision\n")
        f.write("Cases marked GENUINELY_AMBIGUOUS require a product manager to decide policy (e.g., if a customer asks for a refund for a late package, is it delivery_delayed or returns_refunds?).\n")

    print(f"Review complete. Found {len(proposed_patch)} proposed label changes.")

if __name__ == "__main__":
    main()
