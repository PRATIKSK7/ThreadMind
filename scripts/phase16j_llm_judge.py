import os
import sys
import json
import csv
from collections import defaultdict

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
- If the customer asks for account-specific details you don't have, you MUST escalate.
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

def process_example(item, llm, router, retriever):
    try:
        conv = item["conversation"]
        v2_pred = router.predict(conv)["predicted_intent"]
        docs = retriever.retrieve(conv, k=3)
        
        gen_prompt = build_generation_prompt(conv, v2_pred, docs)
        gen_res = llm.predict(gen_prompt, json_mode=True)
        
        if "error" in gen_res:
            raise Exception(gen_res["error"])
            
        response_text = gen_res.get("response", "")
        escalation = gen_res.get("escalation", "ESCALATE")
        reason = gen_res.get("escalation_reason", "")
        evidence_used = gen_res.get("evidence_used", "")
        
        judge_prompt = build_judge_prompt(conv, v2_pred, docs, response_text)
        judge_res = llm.predict(judge_prompt, json_mode=True)
        
        if "error" in judge_res:
            raise Exception(judge_res["error"])
            
        return {
            "thread_id": item["thread_id"],
            "expected_intent": item["intent_id"],
            "predicted_intent": v2_pred,
            "generated_response": response_text,
            "escalation_decision": escalation,
            "escalation_reason": reason,
            "evidence_used": evidence_used,
            "judge_scores": {
                "correctness": judge_res.get("correctness", 1),
                "groundedness": judge_res.get("groundedness", 1),
                "relevance": judge_res.get("relevance", 1),
                "helpfulness": judge_res.get("helpfulness", 1),
                "brand_consistency": judge_res.get("brand_consistency", 1),
                "hallucination_risk": judge_res.get("hallucination_risk", 1)
            },
            "judge_rationale": judge_res.get("rationale", "")
        }
    except Exception as e:
        return {
            "thread_id": item["thread_id"],
            "error": str(e)
        }

def main():
    print("Running Phase 16J LLM-as-Judge Evaluation (Sequential)...")
    gs = load_golden()
    
    retriever = DenseRetriever()
    llm = LLMProvider()
    router = FallbackRouter()
    
    checkpoint_file = config.REPORTS_DIR / "phase16j_llm_judge_results.json"
    results = []
    
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
                results = data.get("results", [])
        except Exception:
            results = []
            
    processed_ids = {r.get("thread_id") for r in results if r.get("thread_id") is not None}
    
    total = len(gs)
    cached = len(processed_ids)
    new_inferences = 0
    failed = len([r for r in results if "error" in r])
    
    print(f"Resuming with {cached} already processed examples...")
    
    for i, item in enumerate(gs):
        if item["thread_id"] in processed_ids:
            continue
            
        r = process_example(item, llm, router, retriever)
        results.append(r)
        processed_ids.add(item["thread_id"])
        
        if "error" in r:
            failed += 1
        else:
            new_inferences += 1
            
        # Checkpoint immediately
        with open(checkpoint_file, "w") as f:
            json.dump({"results": results}, f, indent=2)
            
        print(f"LLM JUDGE PROGRESS: {len(processed_ids)}/{total}")
        print(f"CACHE HITS: {cached}")
        print(f"NEW INFERENCES: {new_inferences}")
        print(f"FAILED: {failed}")
        print("---")
        
    # Final aggregations
    successful = len([r for r in results if "error" not in r])
    escalation_stats = {"AUTO_HANDLE": 0, "ESCALATE": 0}
    avg_scores = defaultdict(float)
    
    for r in results:
        if "error" not in r:
            esc = r.get("escalation_decision", "ESCALATE")
            if "ESCALATE" in esc: esc = "ESCALATE"
            elif "AUTO" in esc: esc = "AUTO_HANDLE"
            else: esc = "ESCALATE"
            escalation_stats[esc] = escalation_stats.get(esc, 0) + 1
            
            for k, v in r.get("judge_scores", {}).items():
                avg_scores[k] += v
                
    if successful > 0:
        for k in avg_scores:
            avg_scores[k] /= successful
            
    # Save CSV
    csv_rows = []
    for r in results:
        if "error" in r:
            csv_rows.append({"thread_id": r["thread_id"], "error": r["error"]})
        else:
            row = {
                "thread_id": r["thread_id"],
                "expected_intent": r["expected_intent"],
                "predicted_intent": r["predicted_intent"],
                "generated_response": r.get("generated_response", "").replace('\n', ' '),
                "escalation_decision": r.get("escalation_decision", ""),
                "escalation_reason": r.get("escalation_reason", ""),
                "evidence_used": r.get("evidence_used", ""),
                "judge_rationale": r.get("judge_rationale", "")
            }
            row.update(r.get("judge_scores", {}))
            csv_rows.append(row)
            
    if csv_rows:
        keys = list(csv_rows[0].keys())
        with open(config.REPORTS_DIR / "phase16j_llm_judge_results.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in csv_rows:
                writer.writerow(r)
                
    # Save JSON
    with open(checkpoint_file, "w") as f:
        json.dump({
            "coverage": {"total": total, "successful": successful, "failed": failed},
            "escalation_stats": escalation_stats,
            "avg_scores": avg_scores,
            "results": results
        }, f, indent=2)
        
    # Save MD
    md = f"""# LLM-as-Judge Evaluation (Amazon Brand)

## Coverage
- **Total Cases**: {total}
- **Successful Eval**: {successful}
- **Failed Eval**: {failed}
- **Effective Coverage**: {(successful/total)*100:.1f}% if total > 0 else 0%

## Escalation Policy (Auto-Handle vs Escalate)
- **AUTO_HANDLE**: {escalation_stats.get('AUTO_HANDLE', 0)}
- **ESCALATE_TO_HUMAN**: {escalation_stats.get('ESCALATE', 0)}

## Average Judge Scores (1-5)
- **Correctness**: {avg_scores.get('correctness', 0):.2f}
- **Groundedness**: {avg_scores.get('groundedness', 0):.2f}
- **Relevance**: {avg_scores.get('relevance', 0):.2f}
- **Helpfulness**: {avg_scores.get('helpfulness', 0):.2f}
- **Brand Consistency**: {avg_scores.get('brand_consistency', 0):.2f}
- **Hallucination Risk (Higher = Safer)**: {avg_scores.get('hallucination_risk', 0):.2f}

## Human Agreement
No human-agreement conclusion can be made from autonomous QA decisions alone.
"""
    with open(config.REPORTS_DIR / "phase16j_llm_judge.md", "w") as f:
        f.write(md)
        
    print("LLM-as-Judge evaluation complete.")

if __name__ == "__main__":
    main()
