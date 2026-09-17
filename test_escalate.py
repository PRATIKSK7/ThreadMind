import requests

q = "What is the exact status of order 123-4567890-1234567? I need to know the specific delivery date and carrier."
r = requests.post("http://localhost:5001/api/playground/analyze", json={"query": q})
data = r.json()
print(f"RESPONSE: {data.get('response')}")
print(f"ESCALATE: {data.get('escalate')}")
print(f"ESCALATION REASON: {data.get('escalation_reason')}")
