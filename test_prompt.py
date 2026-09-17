from src.threadmind.llm.provider import LLMProvider

llm = LLMProvider()

queries = [
    "What is the exact status of order 123-4567890-1234567?",
    "Someone accessed my account and I need help securing it.",
    "I was charged something I don't recognize. Fix it.",
    "My Alexa is not responding."
]

for q in queries:
    prompt = f"""You are an expert Amazon Customer Support AI agent.
Your task is to generate a grounded, empathetic, and professional response to the customer, OR escalate the issue if you lack sufficient information or authority.

Intent: unknown

Customer Conversation:
[
  {{
    "author": "customer",
    "inbound": true,
    "text": "{q}"
  }}
]

Retrieved Historical Evidence (for tone and policy grounding):


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
    print(f"\n--- QUERY: {q} ---")
    res = llm.predict(prompt, json_mode=True)
    print(f"ESCALATE: {res.get('escalation')}")
    print(f"REASON: {res.get('escalation_reason')}")
