import os
import sys
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.threadmind import config
from src.threadmind.rag.dense_retriever import DenseRetriever
from src.threadmind.llm.provider import LLMProvider
from src.threadmind.router.fallback_router import FallbackRouter

def load_golden():
    gs = []
    with open(config.PROCESSED_DATA_DIR / "golden_set.jsonl", "r") as f:
        for line in f:
            gs.append(json.loads(line))
    return gs

def build_generation_prompt(conversation, intent, retrieved_docs):
    conv_str = json.dumps(conversation, indent=2)
    ev_str = ""
    for i, d in enumerate(retrieved_docs):
        ev_str += f"--- Example {i+1} ---\n{json.dumps(d['metadata']['conversation'], indent=2)}\n\n"
        
    prompt = f"""You are an expert Amazon Customer Support AI agent.
Your task is to generate a grounded, empathetic, and professional response to the customer, OR escalate the issue if you lack sufficient information or authority.

Intent: {intent}

Customer Conversation:
{conv_str}

Retrieved Historical Evidence (for tone and policy grounding):
{ev_str}

Respond in STRICT JSON format:
{{
  "response": "Your generated Amazon customer support response. If escalating, explain why to the customer politely.",
  "escalation": "AUTO_HANDLE or ESCALATE",
  "escalation_reason": "Explanation of why you chose to auto-handle or escalate."
}}

Rules:
- NEVER invent refund amounts, delivery dates, or personal account details.
- You do NOT have access to a database or user accounts. You cannot look up orders, process refunds, or secure accounts.
- ESCALATION POLICY: You MUST output "ESCALATE" for the escalation field if the customer's request involves ANY of the following:
  1) An order number or tracking ID.
  2) A refund, charge, billing dispute, or unrecognized transaction.
  3) Unauthorized account access, account security, or hacked accounts.
  4) Changing account details, payment methods, or passwords.
  Do NOT attempt to auto-handle these. You CANNOT process these requests. Output "ESCALATE" immediately.
- Only output "AUTO_HANDLE" for general troubleshooting, FAQs, or generic return policy questions that do not require account access.
- Maintain Amazon brand voice (polite, helpful, concise).
"""
    return prompt

def build_judge_prompt(conversation, intent, retrieved_docs, generated_response):
    conv_str = json.dumps(conversation, indent=2)
    ev_str = ""
    for i, d in enumerate(retrieved_docs):
        ev_str += f"--- Example {i+1} ---\n{json.dumps(d['metadata']['conversation'], indent=2)}\n\n"
        
    prompt = f"""You are an expert LLM-as-judge evaluating an Amazon Customer Support AI agent.
Evaluate the following generated response based on the conversation and retrieved evidence.

Intent: {intent}
Conversation: {conv_str}
Retrieved Evidence: {ev_str}

Generated Response: {generated_response}

Score the response on a scale of 1-5 (1 = terrible, 5 = perfect) for each category, and provide a short rationale.
Respond in STRICT JSON format:
{{
  "correctness": <int>,
  "groundedness": <int>,
  "relevance": <int>,
  "helpfulness": <int>,
  "brand_consistency": <int>,
  "hallucination_risk": <int (1=high risk, 5=no risk)>,
  "rationale": "Short explanation of the scores."
}}
"""
    return prompt

def main():
    print("Running Amazon Response Generation and LLM-as-Judge Evaluation...")
    gs = load_golden()
    
    retriever = DenseRetriever()
    llm = LLMProvider()
    router = FallbackRouter()
    
    results = []
    total = len(gs)
    successful = 0
    failed = 0
    
    # Track escalation policy metrics
    escalation_stats = {"AUTO_HANDLE": 0, "ESCALATE": 0}
    
    for i, item in enumerate(gs):
        try:
            conv = item["conversation"]
            # Predict intent using V2
            v2_pred = router.predict(conv)["predicted_intent"]
            
            # Retrieve evidence
            docs = retriever.retrieve(conv, k=3)
            
            # Generate response
            gen_prompt = build_generation_prompt(conv, v2_pred, docs)
            gen_res = llm.predict(gen_prompt, json_mode=True)
            
            if "error" in gen_res:
                raise Exception(gen_res["error"])
                
            response_text = gen_res.get("response", "")
            escalation = gen_res.get("escalation", "ESCALATE")
            reason = gen_res.get("escalation_reason", "")
            
            escalation_stats[escalation] = escalation_stats.get(escalation, 0) + 1
            
            # Judge response
            judge_prompt = build_judge_prompt(conv, v2_pred, docs, response_text)
            judge_res = llm.predict(judge_prompt, json_mode=True)
            
            if "error" in judge_res:
                raise Exception(judge_res["error"])
                
            results.append({
                "thread_id": item["thread_id"],
                "expected_intent": item["intent_id"],
                "predicted_intent": v2_pred,
                "generated_response": response_text,
                "escalation_decision": escalation,
                "escalation_reason": reason,
                "judge_scores": {
                    "correctness": judge_res.get("correctness", 1),
                    "groundedness": judge_res.get("groundedness", 1),
                    "relevance": judge_res.get("relevance", 1),
                    "helpfulness": judge_res.get("helpfulness", 1),
                    "brand_consistency": judge_res.get("brand_consistency", 1),
                    "hallucination_risk": judge_res.get("hallucination_risk", 1)
                },
                "judge_rationale": judge_res.get("rationale", "")
            })
            successful += 1
            
        except Exception as e:
            failed += 1
            results.append({
                "thread_id": item["thread_id"],
                "error": str(e)
            })
            
        if (i+1) % 10 == 0:
            print(f"Processed {i+1}/{total}...")
            
    # Calculate average scores
    avg_scores = {
        "correctness": 0, "groundedness": 0, "relevance": 0,
        "helpfulness": 0, "brand_consistency": 0, "hallucination_risk": 0
    }
    valid_judgments = 0
    for r in results:
        if "judge_scores" in r:
            valid_judgments += 1
            for k, v in r["judge_scores"].items():
                if isinstance(v, (int, float)):
                    avg_scores[k] += v
                    
    if valid_judgments > 0:
        for k in avg_scores:
            avg_scores[k] /= valid_judgments
            
    audit_md = f"""# LLM-as-Judge Response Evaluation

## Coverage
- **Total Cases**: {total}
- **Successful Eval**: {successful}
- **Failed Eval**: {failed}
- **Effective Coverage**: {(successful/total)*100:.1f}%

## Escalation Policy (Auto-Handle vs Escalate)
- **AUTO_HANDLE**: {escalation_stats.get('AUTO_HANDLE', 0)} ({(escalation_stats.get('AUTO_HANDLE', 0)/total)*100:.1f}%)
- **ESCALATE**: {escalation_stats.get('ESCALATE', 0)} ({(escalation_stats.get('ESCALATE', 0)/total)*100:.1f}%)

## Average Judge Scores (1-5)
- **Correctness**: {avg_scores['correctness']:.2f}
- **Groundedness**: {avg_scores['groundedness']:.2f}
- **Relevance**: {avg_scores['relevance']:.2f}
- **Helpfulness**: {avg_scores['helpfulness']:.2f}
- **Brand Consistency**: {avg_scores['brand_consistency']:.2f}
- **Hallucination Risk (Higher = Safer)**: {avg_scores['hallucination_risk']:.2f}

## Human Agreement
No human-agreement conclusion can be made from autonomous QA decisions alone. The autonomous QA operates strictly as an independent evaluation layer and does not substitute for human judgment. Human review data from Phase 16H forms a separate signal.
"""
    
    with open(config.REPORTS_DIR / "amazon_response_evaluation.md", "w") as f:
        f.write(audit_md)
        
    with open(config.REPORTS_DIR / "amazon_response_evaluation.json", "w") as f:
        json.dump({
            "coverage": {"total": total, "successful": successful, "failed": failed},
            "escalation_stats": escalation_stats,
            "avg_scores": avg_scores,
            "results": results
        }, f, indent=2)

    print("Response Evaluation complete.")

if __name__ == "__main__":
    main()
