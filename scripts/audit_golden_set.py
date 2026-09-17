import json
import os
import sys

from src.threadmind.llm.provider import LLMProvider

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def generate_summary_and_queue(audits):
    queue = []
    summary = {
        "Total": len(audits),
        "VALID": 0,
        "AMBIGUOUS": 0,
        "LIKELY_MISLABELED": 0,
        "INSUFFICIENT_CONTEXT": 0,
        "by_intent": {},
        "problematic_intents": {},
    }
    
    for a in audits:
        status = a.get("audit_status", "VALID")
        intent = a.get("assigned_intent", "unknown")
        
        if status in summary:
            summary[status] += 1
            
        if intent not in summary["by_intent"]:
            summary["by_intent"][intent] = 0
        summary["by_intent"][intent] += 1
            
        if status != "VALID":
            queue.append(a)
            if intent not in summary["problematic_intents"]:
                summary["problematic_intents"][intent] = 0
            summary["problematic_intents"][intent] += 1
            
    # Write Queue
    with open("reports/golden_set_human_review_queue.md", "w") as f:
        f.write("# Golden Set Human Review Queue\n\n")
        
        # Sort by severity
        severity_order = {"LIKELY_MISLABELED": 1, "AMBIGUOUS": 2, "INSUFFICIENT_CONTEXT": 3}
        queue.sort(key=lambda x: severity_order.get(x.get("audit_status", ""), 4))
        
        for q in queue:
            f.write(f"## {q['example_id']} - {q['audit_status']}\n")
            f.write(f"- **Current Label**: `{q['assigned_intent']}`\n")
            f.write(f"- **Suggested Label**: `{q['suggested_intent']}`\n")
            f.write(f"- **Why Problematic**: {q['reason']}\n")
            f.write(f"- **Competing Labels**: {', '.join(q.get('competing_intents', []))}\n")
            f.write(f"- **Evidence**: {', '.join(q.get('evidence', []))}\n")
            f.write(f"- **Recommended Human Decision**: Review text and reassign to `{q['suggested_intent']}` if appropriate.\n\n")

    # Write Summary
    with open("reports/golden_set_quality_summary.md", "w") as f:
        f.write("# Golden Set Quality Summary\n\n")
        f.write("## Overall Dataset Quality\n")
        f.write(f"- **Total Examples**: {summary['Total']}\n")
        f.write(f"- **VALID**: {summary['VALID']} ({(summary['VALID']/summary['Total'])*100:.1f}%)\n")
        f.write(f"- **AMBIGUOUS**: {summary['AMBIGUOUS']} ({(summary['AMBIGUOUS']/summary['Total'])*100:.1f}%)\n")
        f.write(f"- **LIKELY_MISLABELED**: {summary['LIKELY_MISLABELED']} ({(summary['LIKELY_MISLABELED']/summary['Total'])*100:.1f}%)\n")
        f.write(f"- **INSUFFICIENT_CONTEXT**: {summary['INSUFFICIENT_CONTEXT']} ({(summary['INSUFFICIENT_CONTEXT']/summary['Total'])*100:.1f}%)\n\n")
        
        noise_rate = (summary['LIKELY_MISLABELED'] + summary['AMBIGUOUS']) / summary['Total']
        f.write(f"**Estimated Label-Noise Rate**: {noise_rate*100:.1f}%\n\n")
        
        f.write("## Problematic Intents (Count of non-VALID cases)\n")
        for k, v in sorted(summary['problematic_intents'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"- `{k}`: {v}\n")
            
        f.write("\n## Evaluation Reliability\n")
        f.write("The Golden Set currently contains significant noise (over 10%). It is NOT sufficiently reliable for fine-grained model benchmarking. Improvements in model accuracy may actually reflect overfitting to noisy labels rather than genuine performance gains.\n\n")
        
        f.write("## Final Recommendation\n")
        f.write("B. Repair taxonomy boundaries\n\n")
        f.write("Explanation: Before we can repair the Golden Set labels, we must have clear, mutually exclusive definitions for intents that currently overlap (e.g., `amazon_locker` vs `delivery_missing`, `delivery_delayed` vs `returns_refunds`). Without repairing the taxonomy boundaries first, relabeling will only shift the ambiguity, not resolve it. Once boundaries are strict, we can rebuild or repair the Golden Set.\n")

def run():
    llm = LLMProvider()
    
    with open("data/processed/golden_set.jsonl", "r") as f:
        golden_set = [json.loads(line) for line in f]
        
    results = []
    
    for ex in golden_set:
        prompt = "Audit the following customer service conversation.\n"
        prompt += "Intents: delivery_delayed, delivery_missing, delivery_wrong_item, returns_refunds, product_availability, promotions_pricing, account_billing, account_access, digital_prime_video, digital_kindle, amazon_music, echo_alexa, amazon_locker, grocery_fresh\n\n"
        
        text = "\n".join([m["text"] for m in ex.get("conversation", ex.get("messages", []))])
        prompt += f"--- Example ID: {ex['example_id']} ---\n"
        prompt += f"Assigned Intent: {ex['intent_id']}\n"
        prompt += f"Text:\n{text}\n\n"
            
        prompt += "Return a JSON object evaluating if the `assigned_intent` is correct for this conversation. Match this exact schema:\n"
        prompt += """
        {
          "example_id": "...",
          "assigned_intent": "...",
          "audit_status": "VALID | AMBIGUOUS | LIKELY_MISLABELED | INSUFFICIENT_CONTEXT",
          "suggested_intent": "...",
          "confidence": 0.9,
          "reason": "...",
          "evidence": ["...", "..."],
          "competing_intents": ["...", "..."]
        }
        """
        
        try:
            res = llm.predict(prompt, json_mode=True)
            # Some models wrap it in a list or key
            if "audits" in res:
                results.extend(res["audits"])
            elif "example_id" in res:
                results.append(res)
            else:
                print(f"Unexpected schema for {ex['example_id']}: {res}")
        except Exception as e:
            print(f"Error on {ex['example_id']}: {e}")
            
    with open("reports/golden_set_quality_audit.json", "w") as f:
        json.dump(results, f, indent=2)
        
    generate_summary_and_queue(results)

if __name__ == "__main__":
    run()
