import pytest
from src.threadmind import config
import json

def test_training_split_exists():
    assert (config.PROCESSED_DATA_DIR / "train_split.jsonl").exists()
    assert (config.PROCESSED_DATA_DIR / "val_split.jsonl").exists()

def test_rule_baseline_metrics_format():
    path = config.REPORTS_DIR / "baseline_rule_results.json"
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
        metrics = data["metrics"]
        assert "intent_accuracy" in metrics
        assert "escalation_accuracy" in metrics
        assert "abstention_rate" in metrics

def test_tfidf_baseline_metrics_format():
    path = config.REPORTS_DIR / "baseline_tfidf_results.json"
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
        metrics = data["metrics"]
        assert "intent_accuracy" in metrics
