import json

with open('.cache/retrieval_results_pilot.json', 'r') as f:
    results = json.load(f)
    
for i, docs in enumerate(results):
    scores = [f"{d['score']:.4f}" for d in docs]
    print(f"Query {i+1}: {', '.join(scores)}")
