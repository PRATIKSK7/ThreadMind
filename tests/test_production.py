import os
import json
import pytest
from unittest.mock import patch, MagicMock
import requests
from src.threadmind.router.fallback_router import FallbackRouter
from src.threadmind.llm.provider import LLMProvider

@pytest.fixture
def router():
    # Instantiate once per session/module to save FAISS loading time if possible,
    # but for isolation we'll just instantiate per test. It takes ~1-2s.
    return FallbackRouter(k=1)

def test_empty_and_short_inputs(router):
    # Empty conversation — the router should not crash and should return a valid intent
    res1 = router.predict([])
    assert 'predicted_intent' in res1
    assert isinstance(res1['predicted_intent'], str)
    
    # Very short single word — should not crash, may route via TF-IDF or rules
    res2 = router.predict([{"author_role": "customer", "text": "Hi"}])
    assert 'predicted_intent' in res2
    assert isinstance(res2['predicted_intent'], str)

def test_multiple_conflicting_intents(router):
    # With TF-IDF confidence router, this input may be resolved by rules or TF-IDF
    # if confidence is high enough, or routed to LLM if below threshold.
    conv = [{"author_role": "customer", "text": "I was charged for prime video but I want a refund."}]
    
    with patch.object(router.llm, 'predict', return_value={"predicted_intent": "account_billing"}):
        res = router.predict(conv)
        # Must have a valid routing path and intent
        assert res['routed_via'] in ("RuleBaseline", "TFIDFBaseline", "DenseRAG_LLM")
        assert 'predicted_intent' in res
        assert isinstance(res['predicted_intent'], str)

@patch('requests.post')
def test_ollama_unavailable(mock_post):
    # Mock connection error
    mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")
    
    provider = LLMProvider()
    provider.provider = "ollama"
    provider.model = "llama3.2"
    
    # Predict should catch the error and return an error dict, NOT crash
    result = provider.predict("Test prompt")
    assert "error" in result
    assert "Failed to connect" in result["error"]
    
@patch('requests.post')
def test_malformed_llm_json(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "This is not json"}}
    mock_post.return_value = mock_response
    
    provider = LLMProvider()
    provider.provider = "ollama"
    
    result = provider.predict("Test prompt")
    assert "error" in result
    assert "Failed to parse JSON" in result["error"]

def test_fallback_router_safe_failure(router):
    # Use an ambiguous input that rules/TF-IDF won't resolve confidently
    conv = [{"author_role": "customer", "text": "xyzzy foobarbaz nonsense gibberish"}]
    
    # If LLM returns an error, FallbackRouter should gracefully handle it.
    with patch.object(router.llm, 'predict', return_value={"error": "Ollama crashed"}):
        res = router.predict(conv)
        # Must have a valid intent (either from TF-IDF or safe fallback)
        assert 'predicted_intent' in res
        assert isinstance(res['predicted_intent'], str)
        # If it reached the LLM path, it should have defaulted to other_support
        if res.get('routed_via') == 'DenseRAG_LLM':
            assert res['predicted_intent'] == 'other_support'

@patch.object(FallbackRouter, '__init__', lambda self, k=3: None)
def test_retrieval_failure():
    # If FAISS crashes or returns empty, the router should still function
    router = FallbackRouter(k=3)
    router.k = 3
    router.confidence_threshold = 0.95
    router.rule_system = MagicMock()
    router.rule_system.predict.return_value = {"predicted_intent": "other_support"}
    
    # TF-IDF returns low confidence so it falls through to LLM
    router.tfidf_system = MagicMock()
    router.tfidf_system.predict.return_value = {
        "predicted_intent": "other_support", "confidence": 0.3
    }
    
    router.retriever = MagicMock()
    router.retriever.retrieve.return_value = [] # Empty retrieval
    
    router.llm = MagicMock()
    router.llm.predict.return_value = {"predicted_intent": "account_billing"}
    
    router.prompt_template = "{few_shot_examples}\n{conversation}"
    
    res = router.predict([{"author_role": "customer", "text": "I want a refund for prime video"}])
    assert res['predicted_intent'] == "account_billing"
    assert res['routed_via'] == "DenseRAG_LLM"

def test_api_key_leakage_and_local_config():
    # Ensure system is configured for local Ollama, not OpenAI
    provider = os.getenv("LLM_PROVIDER", "ollama")
    assert provider.lower() == "ollama", "LLM_PROVIDER must be ollama for production"
    
    # Should not require LLM_API_KEY if using ollama
    if 'LLM_API_KEY' in os.environ:
        del os.environ['LLM_API_KEY']
        
    p = LLMProvider()
    assert p.provider == "ollama"
    # Doesn't crash on init without API key
    
def test_very_long_conversation(router):
    # Should not crash on extremely long conversations (though LLM might truncate context)
    conv = [{"author_role": "customer", "text": "Help me " * 100}] * 10
    
    # We mock LLM to prevent long inference
    with patch.object(router.llm, 'predict', return_value={"predicted_intent": "other_support"}):
        res = router.predict(conv)
        assert res['predicted_intent'] == 'other_support'
