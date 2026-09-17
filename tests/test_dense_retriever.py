import pytest
from src.threadmind.rag.dense_retriever import DenseRetriever

def test_dense_retriever():
    retriever = DenseRetriever()
    assert retriever.index is not None
    assert retriever.corpus_metadata is not None
    
    conv = [
        {"author_role": "customer", "text": "Where is my refund?"}
    ]
    
    results = retriever.retrieve(conv, k=3)
    assert len(results) == 3
    assert 'score' in results[0]
    assert 'metadata' in results[0]
