import json
from src.threadmind import config

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def audit_router():
    rule_results = load_json(config.REPORTS_DIR / "baseline_rule_results.json")
    rag_results = load_json(config.REPORTS_DIR / "baseline_router_results.json") # Dense RAG results aren't saved separately, but we have baseline_rag_k3_results.json (TFIDF)
    # Actually wait, we just evaluated the Dense Retriever Recall. We never ran DenseRAG against LLM!
    # Ah! The user requested to "Compare Dense RAG and the fallback architecture". 
    # The evaluate_router_baseline.py script executed the LLM if routed_via != 'RuleBaseline', but since all went to Rule, we don't have Dense RAG predictions!
    pass

    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    golden_map = {}
    with open(golden_path, "r") as f:
        for line in f:
            r = json.loads(line)
            golden_map[r['example_id']] = r

    print("Analyzing Rule Baseline Errors...")
    errors = []
    for p in rule_results['predictions']:
        golden = golden_map[p['example_id']]
        if golden['intent_id'] != p['predicted_intent']:
            errors.append({
                "example_id": p['example_id'],
                "thread_id": golden['thread_id'],
                "expected_intent": golden['intent_id'],
                "predicted_intent": p['predicted_intent']
            })
            
    print(f"Total Errors in Rule Baseline: {len(errors)}")
    for e in errors:
        print(f"Thread ID: {e['thread_id']}, Expected: {e['expected_intent']}, Predicted: {e['predicted_intent']}")

if __name__ == "__main__":
    audit_router()
