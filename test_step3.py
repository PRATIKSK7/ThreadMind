import requests
import json
import time

queries = [
    "I received the wrong item and want to return it.",
    "My Alexa is not responding.",
    "I need you to refund me $50 right now to my card ending in 1234."
]

print("Waiting for server to start...")
time.sleep(5)

for q in queries:
    print(f"\n--- QUERY: {q} ---")
    try:
        r = requests.post("http://localhost:5001/api/playground/analyze", json={"query": q})
        if r.status_code == 200:
            data = r.json()
            print(f"RESPONSE: {data.get('response')}")
            print(f"ESCALATE: {data.get('escalate')}")
            print(f"ESCALATION REASON: {data.get('escalation_reason')}")
        else:
            print(f"ERROR: {r.status_code} {r.text}")
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
