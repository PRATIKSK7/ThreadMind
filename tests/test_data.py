import pandas as pd
import numpy as np
from pathlib import Path
from src.threadmind.data import loader, audit

def test_loader_schema_validation(tmp_path):
    # Create invalid synthetic CSV
    csv_file = tmp_path / "invalid.csv"
    pd.DataFrame({"wrong_col": [1]}).to_csv(csv_file, index=False)
    
    try:
        loader.load_twcs_dataset(csv_file)
        assert False, "Should have raised ValueError due to missing columns"
    except ValueError:
        pass

def test_loader_identifier_handling(tmp_path):
    csv_file = tmp_path / "test_twcs.csv"
    # Create synthetic data where numbers might be cast to floats if not careful
    df_synthetic = pd.DataFrame({
        'tweet_id': ['1234567890123456789'],
        'author_id': ['9876543210987654321'],
        'inbound': ['True'],
        'created_at': ['Tue Oct 31 22:10:47 +0000 2017'],
        'text': ['Hello'],
        'response_tweet_id': ['2,3'],
        'in_response_to_tweet_id': ['']
    })
    df_synthetic.to_csv(csv_file, index=False)
    
    df_loaded = loader.load_twcs_dataset(csv_file)
    assert pd.api.types.is_string_dtype(df_loaded['tweet_id'])
    assert df_loaded['tweet_id'].iloc[0] == '1234567890123456789'
    
def test_missing_value_audit():
    df = pd.DataFrame({
        'col1': [1, np.nan, 3],
        'col2': ['A', 'B', 'C']
    })
    res = audit.audit_missing_values(df)
    assert res['col1']['count'] == 1
    assert res['col2']['count'] == 0

def test_duplicate_detection():
    df = pd.DataFrame({
        'tweet_id': ['1', '2', '2'],
        'text': ['A', 'B', 'B']
    })
    res = audit.audit_duplicates(df)
    assert res['exact_rows'] == 1
    assert res['duplicate_tweet_ids'] == 1

def test_parent_reference_validation():
    df = pd.DataFrame({
        'tweet_id': ['1', '2', '3'],
        'response_tweet_id': [np.nan, '3', np.nan],
        'in_response_to_tweet_id': [np.nan, '1', '999'] # 999 is missing
    })
    res = audit.audit_response_relationships(df)
    assert res['in_response_to_tweet_id']['valid_references_in_dataset'] == 1
    assert res['in_response_to_tweet_id']['references_to_missing_ids'] == 1

def test_author_stats():
    df = pd.DataFrame({
        'tweet_id': ['1', '2', '3', '4'],
        'author_id': ['A', 'A', 'B', 'A'],
        'inbound': [True, False, True, False],
        'in_response_to_tweet_id': [np.nan, '1', np.nan, '3']
    })
    stats = audit.analyze_authors(df)
    
    author_a = stats[stats['author_id'] == 'A'].iloc[0]
    assert author_a['total_tweets'] == 3
    assert author_a['inbound_tweets'] == 1
    assert author_a['outbound_tweets'] == 2
    assert author_a['estimated_customer_replies'] == 2
    assert author_a['thread_count'] == 2
