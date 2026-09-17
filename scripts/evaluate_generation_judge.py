import json
import time
from src.threadmind import config
from src.threadmind.llm.provider import LLMProvider

def main():
    print("Initializing LLM-as-Judge...")
    llm = LLMProvider()
    
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "judge_rubric_v1.txt"
    with open(prompt_path, "r") as f:
        prompt_template = f.read()
        
    replies_path = config.REPORTS_DIR / "generated_replies.json"
    with open(replies_path, "r") as f:
        generated_replies = json.load(f)
        
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    golden_dict = {}
    with open(golden_path, "r") as f:
        for line in f:
            r = json.loads(line)
            golden_dict[r['example_id']] = r['conversation']
            
    print(f"\nEvaluating {len(generated_replies)} replies...")
    results = []
    
    scores = {
        "correctness": [],
        "groundedness": [],
        "helpfulness": [],
        "tone": []
    }
    hallucination_count = 0
    
    for i, rep in enumerate(generated_replies):
        conv = golden_dict[rep['example_id']]
        conv_lines = []
        for m in conv:
            role = "customer" if m.get('inbound', True) else "agent"
            conv_lines.append(f"{role.capitalize()}: {m.get('text', '')}")
        conv_str = "\n".join(conv_lines)
        
        prompt = prompt_template.replace("{conversation}", conv_str)
        prompt = prompt.replace("{generated_reply}", rep['generated_reply'])
        
        pred = llm.predict(prompt)
        
        # Safe extraction
        c_score = pred.get('correctness_score', 1)
        g_score = pred.get('groundedness_score', 1)
        h_score = pred.get('helpfulness_score', 1)
        t_score = pred.get('tone_score', 1)
        
        scores['correctness'].append(c_score)
        scores['groundedness'].append(g_score)
        scores['helpfulness'].append(h_score)
        scores['tone'].append(t_score)
        
        if pred.get('has_hallucination', False) or g_score <= 2:
            hallucination_count += 1
            
        rep['judge_evaluation'] = pred
        results.append(rep)
        
        print(f"Evaluated {i+1}/{len(generated_replies)} - Scores: C:{c_score}, G:{g_score}, H:{h_score}, T:{t_score}")
            
    avg_scores = {k: sum(v)/len(v) for k, v in scores.items()}
    print("\n--- LLM-as-Judge Results ---")
    print(f"Correctness:  {avg_scores['correctness']:.2f} / 5.0")
    print(f"Groundedness: {avg_scores['groundedness']:.2f} / 5.0")
    print(f"Helpfulness:  {avg_scores['helpfulness']:.2f} / 5.0")
    print(f"Tone:         {avg_scores['tone']:.2f} / 5.0")
    print(f"Hallucination Rate: {(hallucination_count / len(generated_replies)) * 100:.2f}%")
    
    output_path = config.REPORTS_DIR / "judge_evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "averages": avg_scores,
            "hallucination_rate": (hallucination_count / len(generated_replies)),
            "evaluations": results
        }, f, indent=2)
        
if __name__ == "__main__":
    main()
