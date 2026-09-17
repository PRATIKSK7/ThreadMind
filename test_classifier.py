import json
import time
import sys
import warnings

# Suppress sklearn/transformers warnings for clean output
warnings.filterwarnings("ignore")

sys.path.append(".")
from src.threadmind.router.fallback_router import FallbackRouter

router = FallbackRouter()

tests = [
    "I was charged twice for my order and need a refund.",
    "Where is my package? It was supposed to arrive yesterday.",
    "My Alexa is not responding.",
    "I cannot log into my account after changing my password.",
    "I received the wrong item and want to return it.",
    # generalization tests
    "I've been billed two times for the same purchase.",
    "Why has my delivery still not arrived?",
    "My Echo device isn't answering me.",
    "Password changed and now I can't access my account.",
    "How can I send back the incorrect product?"
]

for t in tests:
    conv = [{"author": "customer", "inbound": True, "text": t}]
    start = time.time()
    res = router.predict(conv)
    end = time.time()
    
    print(f"INPUT: {t}")
    print(f"PREDICTED INTENT: {res.get('predicted_intent')}")
    print(f"CONFIDENCE: {res.get('confidence')}")
    print(f"ROUTED VIA: {res.get('routed_via')}")
    print(f"EXECUTION TIME: {end - start:.2f}s\n")
