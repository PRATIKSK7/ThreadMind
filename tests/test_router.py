import pytest
from src.threadmind.router.fallback_router import FallbackRouter

def test_router_initializes():
    router = FallbackRouter(k=3)
    assert router.rule_system is not None
    assert router.retriever is not None
    assert router.llm is not None

def test_rule_first_routing():
    router = FallbackRouter(k=3)
    
    # Example that should confidently trigger the RuleBaseline
    simple_conv = [
        {"author_role": "customer", "text": "WHERE IS MY REFUND FOR THE RETURN"},
        {"author_role": "brand", "text": "I can process a refund."}
    ]
    
    # We mock the LLM predict so it crashes if it gets called, ensuring it routed via Rule
    def mock_predict(*args, **kwargs):
        raise AssertionError("LLM should not be called for confident rule.")
    
    router.llm.predict = mock_predict
    
    res = router.predict(simple_conv)
    assert res['predicted_intent'] != 'other_support'
    assert res['routed_via'] == 'RuleBaseline'
