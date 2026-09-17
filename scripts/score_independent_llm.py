#!/usr/bin/env python3
"""
LLM-Independent Scoring of the 30-example human scoring subset.

Uses Ollama / Llama 3.2 with a strict rubric to independently score
each generated reply based ONLY on conversation_history and agent_reply.

Does NOT access the Golden Set labels, expected intents, or reference answers.
"""

import csv
import json
import time
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.threadmind.llm.provider import LLMProvider

SCORING_PROMPT = """You are a STRICT quality evaluator for an AI customer support agent.

You will be given:
1. A conversation history between a customer and an agent on Twitter.
2. A generated reply from the AI agent.

Your task is to score the generated reply on 4 dimensions using integer scores from 1 to 5.

## Scoring Rubric

### Correctness (1-5)
- 5: Directly addresses the customer's actual issue in their LATEST message. Completely relevant.
- 4: Addresses the issue well but misses a minor nuance.
- 3: Addresses the issue but provides a generic or partially relevant response.
- 2: Partially misses the point or addresses the wrong aspect of the issue.
- 1: Completely misses the point, answers the wrong question, or provides incorrect information.

### Groundedness (1-5)
- 5: Completely grounded. Does NOT invent tracking numbers, order IDs, refund amounts, timelines, or internal policies not present in the conversation.
- 4: Mostly grounded with very minor assumptions (e.g., standard greeting patterns).
- 3: Assumes a generic policy (e.g., "Returns take 3-5 days") without explicit context supporting it.
- 2: Makes notable unsupported claims or assumptions about the customer's situation.
- 1: Blatantly invents false facts (e.g., specific tracking numbers, locations, amounts not mentioned anywhere).

### Helpfulness (1-5)
- 5: Actively pushes toward resolution. Asks for missing info when needed. Offers clear next steps.
- 4: Helpful but could be slightly more proactive.
- 3: Provides some help but is vague or doesn't clearly advance the resolution.
- 2: Minimally helpful. Doesn't provide actionable next steps.
- 1: Unhelpful, confusing, or creates more work for the customer.

### Tone (1-5)
- 5: Empathetic, polite, professional. Natural conversational flow appropriate for customer support.
- 4: Professional and polite but slightly formulaic.
- 3: Professional but robotic, repetitive, or overly templated.
- 2: Awkward, dismissive, or inappropriately casual.
- 1: Rude, sarcastic, or completely unreadable.

## IMPORTANT RULES
- Be STRICT. Do NOT default to high scores.
- If the reply contains ANY invented tracking numbers, order IDs, refund amounts, or specific policies not grounded in the conversation, Groundedness MUST be 3 or lower.
- If the reply does not address the customer's LATEST message, Correctness MUST be 3 or lower.
- If the conversation is in a non-English language and the reply is in English, consider whether this helps or hinders the customer.
- Provide a brief reasoning (1-2 sentences) for EACH score.

## Conversation History
{conversation_history}

## Generated Agent Reply
{agent_reply}

## Your Evaluation
Return ONLY a valid JSON object with this exact structure:
{{
  "correctness_score": <int 1-5>,
  "correctness_reasoning": "<brief reasoning>",
  "groundedness_score": <int 1-5>,
  "groundedness_reasoning": "<brief reasoning>",
  "helpfulness_score": <int 1-5>,
  "helpfulness_reasoning": "<brief reasoning>",
  "tone_score": <int 1-5>,
  "tone_reasoning": "<brief reasoning>"
}}
"""


def clamp_score(val):
    """Ensure score is an integer between 1 and 5."""
    try:
        v = int(val)
        return max(1, min(5, v))
    except (TypeError, ValueError):
        return 1  # Default to worst score if unparseable


def main():
    print("=" * 60)
    print("LLM-Independent Scoring (Ollama / Llama 3.2)")
    print("=" * 60)

    # Load the 30-example subset
    csv_path = "reports/human_scoring_subset.csv"
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"Loaded {len(rows)} examples from {csv_path}")

    # Load cached judge scores for comparison
    with open("reports/judge_evaluation_results.json", "r") as f:
        judge_data = json.load(f)
    judge_by_id = {}
    for ev in judge_data["evaluations"]:
        eid = ev["example_id"]
        je = ev.get("judge_evaluation", {})
        judge_by_id[eid] = {
            "correctness": clamp_score(je.get("correctness_score", 1)),
            "groundedness": clamp_score(je.get("groundedness_score", 1)),
            "helpfulness": clamp_score(je.get("helpfulness_score", 1)),
            "tone": clamp_score(je.get("tone_score", 1)),
        }

    # Initialize LLM
    llm = LLMProvider()
    print("LLM Provider initialized.\n")

    # Score each example
    all_details = []
    scored_rows = []

    for i, row in enumerate(rows):
        eid = row["example_id"]
        conv = row["conversation_history"]
        reply = row["agent_reply"]

        prompt = SCORING_PROMPT.replace("{conversation_history}", conv)
        prompt = prompt.replace("{agent_reply}", reply)

        print(f"Scoring {i+1}/30: {eid}...", end=" ", flush=True)

        pred = llm.predict(prompt, json_mode=True)

        # Extract scores with safe fallbacks
        c = clamp_score(pred.get("correctness_score", 1))
        g = clamp_score(pred.get("groundedness_score", 1))
        h = clamp_score(pred.get("helpfulness_score", 1))
        t = clamp_score(pred.get("tone_score", 1))

        print(f"C={c}, G={g}, H={h}, T={t}")

        # Build detail record
        detail = {
            "example_id": eid,
            "independent_correctness": c,
            "independent_groundedness": g,
            "independent_helpfulness": h,
            "independent_tone": t,
            "correctness_reasoning": pred.get("correctness_reasoning", "N/A"),
            "groundedness_reasoning": pred.get("groundedness_reasoning", "N/A"),
            "helpfulness_reasoning": pred.get("helpfulness_reasoning", "N/A"),
            "tone_reasoning": pred.get("tone_reasoning", "N/A"),
            "raw_llm_output": pred,
        }
        all_details.append(detail)

        # Build scored CSV row (preserve original columns, add new ones)
        scored_row = dict(row)
        scored_row["independent_correctness_1_to_5"] = c
        scored_row["independent_groundedness_1_to_5"] = g
        scored_row["independent_helpfulness_1_to_5"] = h
        scored_row["independent_tone_1_to_5"] = t
        scored_rows.append(scored_row)

    # ---- Save outputs ----

    # 1. Save detailed JSON
    json_path = "reports/llm_independent_scoring_details.json"
    with open(json_path, "w") as f:
        json.dump(all_details, f, indent=2, default=str)
    print(f"\nSaved detailed scoring to {json_path}")

    # 2. Save scored CSV
    csv_out_path = "reports/llm_independent_scoring_subset.csv"
    fieldnames = list(rows[0].keys()) + [
        "independent_correctness_1_to_5",
        "independent_groundedness_1_to_5",
        "independent_helpfulness_1_to_5",
        "independent_tone_1_to_5",
    ]
    with open(csv_out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scored_rows)
    print(f"Saved scored CSV to {csv_out_path}")

    # ---- Compute averages ----
    dims = ["correctness", "groundedness", "helpfulness", "tone"]
    ind_scores = {d: [] for d in dims}
    judge_scores = {d: [] for d in dims}

    for detail, row in zip(all_details, rows):
        eid = row["example_id"]
        for d in dims:
            ind_scores[d].append(detail[f"independent_{d}"])
            if eid in judge_by_id:
                judge_scores[d].append(judge_by_id[eid][d])

    print("\n" + "=" * 60)
    print("AVERAGE SCORES COMPARISON")
    print("=" * 60)
    print(f"{'Dimension':<15} {'Independent':>12} {'Judge':>12} {'Delta':>8}")
    print("-" * 50)
    for d in dims:
        ind_avg = sum(ind_scores[d]) / len(ind_scores[d])
        jud_avg = sum(judge_scores[d]) / len(judge_scores[d]) if judge_scores[d] else 0
        delta = ind_avg - jud_avg
        print(f"{d.capitalize():<15} {ind_avg:>12.2f} {jud_avg:>12.2f} {delta:>+8.2f}")

    # ---- Compute Cohen's Kappa ----
    print("\n" + "=" * 60)
    print("COHEN'S KAPPA (LLM-Independent vs LLM-Judge)")
    print("=" * 60)

    try:
        from sklearn.metrics import cohen_kappa_score
        for d in dims:
            if judge_scores[d]:
                kappa = cohen_kappa_score(
                    judge_scores[d], ind_scores[d], weights="quadratic"
                )
                print(f"{d.capitalize():<15} Quadratic Kappa: {kappa:.4f}")
            else:
                print(f"{d.capitalize():<15} No judge scores available")
    except ImportError:
        print("sklearn not available. Computing manual agreement...")
        for d in dims:
            if judge_scores[d]:
                agree = sum(1 for a, b in zip(judge_scores[d], ind_scores[d]) if a == b)
                print(f"{d.capitalize():<15} Exact Agreement: {agree}/30 ({agree/30*100:.1f}%)")

    # ---- Score distribution ----
    print("\n" + "=" * 60)
    print("INDEPENDENT SCORE DISTRIBUTION")
    print("=" * 60)
    for d in dims:
        dist = {}
        for s in ind_scores[d]:
            dist[s] = dist.get(s, 0) + 1
        dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(dist.items()))
        print(f"{d.capitalize():<15} {dist_str}")


if __name__ == "__main__":
    main()
