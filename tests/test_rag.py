import pytest
import os
import json
from src.threadmind import config
from src.threadmind.rag.tfidf_retriever import TFIDFRetriever

def test_tfidf_retriever_initializes():
    """Test that the retriever can initialize and load its index"""
    retriever = TFIDFRetriever()
    assert retriever.vectorizer is not None
    assert retriever.tfidf_matrix is not None
    assert len(retriever.corpus_metadata) > 0

def test_tfidf_retriever_retrieve():
    """Test that retrieve returns exactly k results with correct keys"""
    retriever = TFIDFRetriever()
    dummy_conversation = [
        {"author_role": "customer", "text": "Where is my package?"}
    ]
    
    results = retriever.retrieve(dummy_conversation, k=3)
    
    assert len(results) == 3
    for res in results:
        assert "score" in res
        assert "metadata" in res
        meta = res["metadata"]
        assert "thread_id" in meta
        assert "intent_id" in meta
        assert "conversation" in meta

def test_rag_prompt_template_exists_and_contracts():
    """Test that the RAG prompt template file exists, has correct placeholders, and includes required instructions"""
    prompt_path = config.PROJECT_ROOT / "src" / "threadmind" / "llm" / "prompts" / "rag_classification_v1.txt"
    assert os.path.exists(prompt_path)
    
    with open(prompt_path, "r") as f:
        content = f.read()
        
    assert "{few_shot_examples}" in content
    assert "{conversation}" in content
    
    # Check for Label-Selection Discipline (Variant 2 regression protection)
    assert "# Label-Selection Discipline" in content
    assert "Compare the conversation against the retrieved examples" in content
    assert "Prioritize semantic/user-goal similarity" in content
    
    # Check JSON output contract remains intact
    assert "# Output Schema" in content
    assert '"predicted_intent"' in content
    assert '"predicted_escalation"' in content

def test_retrieval_corpus_leakage():
    """Test that the retrieval corpus has zero overlap with golden set"""
    golden_path = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    corpus_path = config.PROCESSED_DATA_DIR / "retrieval_corpus.jsonl"
    
    golden_ids = set()
    with open(golden_path, "r") as f:
        for line in f:
            golden_ids.add(json.loads(line)["thread_id"])
            
    with open(corpus_path, "r") as f:
        for line in f:
            corpus_id = json.loads(line)["thread_id"]
            assert corpus_id not in golden_ids, f"Leakage detected for {corpus_id}"
