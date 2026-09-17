import time
import sys
sys.path.append(".")
from src.threadmind.rag.dense_retriever import DenseRetriever

retriever = DenseRetriever()

queries = [
    "I was charged twice for my order and need a refund.",
    "Where is my package? It was supposed to arrive yesterday?",
    "I received the wrong item and want to return it.",
    "I cannot log into my account.",
    "My Alexa is not responding."
]

for query in queries:
    conv = [{"author": "customer", "inbound": True, "text": query}]
    start = time.time()
    results = retriever.retrieve(conv, k=3)
    end = time.time()
    
    print(f"QUERY: {query}")
    print(f"EXECUTION TIME: {end - start:.2f}s")
    for i, res in enumerate(results):
        score = res['score']
        metadata = res['metadata']
        text = metadata.get('conversation', '')[:150] + "..."
        print(f"  RESULT {i+1}:")
        print(f"    SCORE: {score}")
        print(f"    TEXT: {text}")
    print("\n")
