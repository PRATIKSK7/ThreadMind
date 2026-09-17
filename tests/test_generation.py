import pytest
from unittest.mock import patch, MagicMock
from src.threadmind.llm.provider import LLMProvider
import json

@pytest.fixture
def llm_provider():
    # Use a dummy provider for testing
    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda k, d=None: "ollama" if k == "LLM_PROVIDER" else d
        provider = LLMProvider()
        return provider

def test_ollama_failure_handling(llm_provider):
    """Test that the system gracefully handles an Ollama connection failure."""
    with patch('requests.post') as mock_post:
        # Mock a connection error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        
        result = llm_provider.predict("Test prompt", json_mode=False)
        assert "error" in result
        assert "Failed to connect" in result["error"]

def test_malformed_llm_json_output(llm_provider):
    """Test that the LLM-as-Judge correctly recovers from malformed JSON."""
    with patch('requests.post') as mock_post:
        # Mock a response that returns invalid JSON
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "This is not valid JSON { missing quotes: 1 }"}}
        mock_post.return_value = mock_response
        
        result = llm_provider.predict("Evaluate this", json_mode=True)
        assert "error" in result
        assert "Failed to parse JSON" in result["error"]

def test_empty_retrieval_handling():
    """Test that reply generation handles empty FAISS retrieval without crashing."""
    from scripts.generate_replies import format_few_shot
    
    empty_docs = []
    formatted = format_few_shot(empty_docs)
    assert formatted == ""

def test_unsafe_unsupported_generation():
    """Test that the prompt includes constraints against unsafe/unsupported generation."""
    with open("src/threadmind/llm/prompts/reply_generation_v1.txt", "r") as f:
        prompt = f.read()
    
    assert "DO NOT invent policies" in prompt or "do not invent" in prompt.lower() or "do not hallucinate" in prompt.lower() or "do not promise" in prompt.lower()
