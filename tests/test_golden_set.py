import json
import pytest
from src.threadmind import config

@pytest.fixture
def golden_set():
    filepath = config.PROCESSED_DATA_DIR / "golden_set.jsonl"
    if not filepath.exists():
        pytest.skip("Golden set not generated yet.")
    
    records = []
    with open(filepath, "r") as f:
        for line in f:
            records.append(json.loads(line))
    return records

def test_golden_set_size_and_schema(golden_set):
    # Expecting around 200 examples
    assert 150 <= len(golden_set) <= 250, "Golden set should be between 150 and 250 examples"
    
    # Check schema
    for record in golden_set:
        assert "example_id" in record
        assert "thread_id" in record
        assert "intent_id" in record
        assert "conversation" in record
        assert "expected_behavior" in record
        assert "difficulty" in record
        assert "metadata" in record
        
        assert "semantic_ambiguity" in record["metadata"]
        assert "structural_complexity" in record["metadata"]
        assert "context_dependent" in record["metadata"]
        assert record["metadata"]["structural_complexity"] in ["simple", "branched", "incomplete"]
        
        assert len(record["conversation"]) >= 2, "Conversation must have at least 2 messages"

def test_golden_set_unique_ids(golden_set):
    example_ids = [r["example_id"] for r in golden_set]
    thread_ids = [r["thread_id"] for r in golden_set]
    
    assert len(example_ids) == len(set(example_ids)), "Example IDs must be unique"
    assert len(thread_ids) == len(set(thread_ids)), "Thread IDs must be unique"

def test_golden_set_escalation_schema(golden_set):
    for r in golden_set:
        escalation = r["expected_behavior"].get("escalation")
        assert escalation in ["no_escalation", "clarification_needed", "human_review_recommended"], "Invalid escalation label"

def test_golden_set_deterministic_difficulty(golden_set):
    for r in golden_set:
        assert r["difficulty"] in ["easy", "medium", "hard", "ambiguous"]
