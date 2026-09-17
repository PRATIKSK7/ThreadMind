import pandas as pd
import numpy as np
from src.threadmind.data import threads

def test_simple_conversation():
    df = pd.DataFrame({
        'tweet_id': ['1', '2'],
        'author_id': ['CUST1', 'BRAND1'],
        'inbound': [True, False],
        'created_at': ['2023-01-01 10:00:00', '2023-01-01 10:05:00'],
        'text': ['Hi', 'Hello'],
        'in_response_to_tweet_id': [np.nan, '1']
    })
    
    th = threads.build_threads_from_dataframe(df)
    assert len(th) == 1
    assert th[0]['metadata']['message_count'] == 2
    assert th[0]['metadata']['turn_count'] == 2
    assert th[0]['metadata']['has_missing_parent'] is False
    assert th[0]['metadata']['branch_detected'] is False

def test_missing_parent():
    df = pd.DataFrame({
        'tweet_id': ['2', '3'],
        'author_id': ['BRAND1', 'CUST1'],
        'inbound': [False, True],
        'created_at': ['2023-01-01 10:05:00', '2023-01-01 10:10:00'],
        'text': ['Hello', 'Thanks'],
        'in_response_to_tweet_id': ['1', '2'] # 1 does not exist
    })
    
    th = threads.build_threads_from_dataframe(df)
    assert len(th) == 1
    assert th[0]['metadata']['has_missing_parent'] is True
    assert th[0]['metadata']['message_count'] == 2

def test_branching():
    df = pd.DataFrame({
        'tweet_id': ['1', '2', '3'],
        'author_id': ['CUST1', 'BRAND1', 'BRAND2'],
        'inbound': [True, False, False],
        'created_at': ['2023-01-01 10:00:00', '2023-01-01 10:05:00', '2023-01-01 10:06:00'],
        'text': ['Hi', 'Hello', 'Also hello'],
        'in_response_to_tweet_id': [np.nan, '1', '1']
    })
    
    th = threads.build_threads_from_dataframe(df)
    assert len(th) == 1
    assert th[0]['metadata']['branch_detected'] is True
    assert th[0]['metadata']['message_count'] == 3

def test_cycle_protection():
    df = pd.DataFrame({
        'tweet_id': ['1', '2'],
        'author_id': ['CUST1', 'BRAND1'],
        'inbound': [True, False],
        'created_at': ['2023-01-01 10:00:00', '2023-01-01 10:05:00'],
        'text': ['Hi', 'Hello'],
        'in_response_to_tweet_id': ['2', '1'] # cycle!
    })
    
    th = threads.build_threads_from_dataframe(df)
    assert len(th) == 0

def test_deterministic_id():
    df1 = pd.DataFrame({
        'tweet_id': ['999'], 'author_id': ['A'], 'inbound': [True], 'created_at': ['2023-01-01'], 'text': ['Hi'], 'in_response_to_tweet_id': [np.nan]
    })
    th1 = threads.build_threads_from_dataframe(df1)
    
    df2 = pd.DataFrame({
        'tweet_id': ['999'], 'author_id': ['A'], 'inbound': [True], 'created_at': ['2023-01-01'], 'text': ['Hi'], 'in_response_to_tweet_id': [np.nan]
    })
    th2 = threads.build_threads_from_dataframe(df2)
    
    assert th1[0]['thread_id'] == th2[0]['thread_id']
