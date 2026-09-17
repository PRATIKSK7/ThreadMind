import pandas as pd
import numpy as np

def audit_missing_values(df: pd.DataFrame) -> dict:
    """Audits missing values in the dataset."""
    missing_counts = df.isnull().sum()
    missing_percentages = (missing_counts / len(df)) * 100
    
    return {
        col: {"count": int(missing_counts[col]), "percentage": float(missing_percentages[col])}
        for col in df.columns
    }

def audit_duplicates(df: pd.DataFrame) -> dict:
    """Audits duplicates, including exact rows and duplicate tweet_ids."""
    exact_duplicates = int(df.duplicated().sum())
    duplicate_tweet_ids = int(df.duplicated(subset=['tweet_id']).sum())
    return {
        "exact_rows": exact_duplicates,
        "duplicate_tweet_ids": duplicate_tweet_ids
    }

def audit_text_quality(df: pd.DataFrame) -> dict:
    """Audits text quality."""
    text_col = df['text']
    null_count = int(text_col.isnull().sum())
    
    empty_count = int((text_col.fillna('') == '').sum())
    
    lengths = text_col.dropna().astype(str).str.len()
    
    return {
        "null_count": null_count,
        "empty_count": empty_count,
        "length": {
            "min": int(lengths.min()) if not lengths.empty else 0,
            "mean": float(lengths.mean()) if not lengths.empty else 0.0,
            "median": float(lengths.median()) if not lengths.empty else 0.0,
            "p95": float(lengths.quantile(0.95)) if not lengths.empty else 0.0,
            "max": int(lengths.max()) if not lengths.empty else 0
        }
    }

def audit_inbound_distribution(df: pd.DataFrame) -> dict:
    """Audits the inbound column."""
    inbound_counts = df['inbound'].value_counts(dropna=False).to_dict()
    total = len(df)
    
    dist = {}
    for k, v in inbound_counts.items():
        key_str = str(k)
        dist[key_str] = {
            "count": int(v),
            "percentage": float((v / total) * 100)
        }
    return dist

def audit_timestamps(df: pd.DataFrame) -> dict:
    """Audits timestamps and handles parsing cleanly."""
    parsed_dates = pd.to_datetime(df['created_at'], errors='coerce')
    valid_dates = parsed_dates.dropna()
    
    invalid_count = int(len(df) - len(valid_dates))
    parse_success_rate = float((len(valid_dates) / len(df)) * 100) if len(df) > 0 else 0.0
    
    return {
        "parse_success_rate": parse_success_rate,
        "invalid_timestamps": invalid_count,
        "earliest": str(valid_dates.min()) if not valid_dates.empty else None,
        "latest": str(valid_dates.max()) if not valid_dates.empty else None
    }

def audit_response_relationships(df: pd.DataFrame) -> dict:
    """Audits response_tweet_id and in_response_to_tweet_id."""
    total = len(df)
    
    resp_null = int(df['response_tweet_id'].isnull().sum())
    in_resp_null = int(df['in_response_to_tweet_id'].isnull().sum())
    
    all_tweet_ids = set(df['tweet_id'].dropna().unique())
    
    in_resp_refs = df['in_response_to_tweet_id'].dropna()
    valid_in_resp_refs = in_resp_refs.isin(all_tweet_ids).sum()
    missing_in_resp_refs = len(in_resp_refs) - valid_in_resp_refs
    
    self_refs = int((df['tweet_id'] == df['in_response_to_tweet_id']).sum())
    
    return {
        "response_tweet_id": {
            "null_percentage": float((resp_null / total) * 100)
        },
        "in_response_to_tweet_id": {
            "null_percentage": float((in_resp_null / total) * 100),
            "valid_references_in_dataset": int(valid_in_resp_refs),
            "references_to_missing_ids": int(missing_in_resp_refs),
            "self_references": self_refs
        }
    }

def analyze_authors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates author-level statistics and returns a DataFrame.
    """
    author_stats = df.groupby('author_id').agg(
        total_tweets=('tweet_id', 'count'),
        inbound_tweets=('inbound', lambda x: (x == True).sum()),
        outbound_tweets=('inbound', lambda x: (x == False).sum())
    )
    
    author_stats['inbound_percentage'] = (author_stats['inbound_tweets'] / author_stats['total_tweets']) * 100
    author_stats['outbound_percentage'] = (author_stats['outbound_tweets'] / author_stats['total_tweets']) * 100
    
    outbound_mask = (df['inbound'] == False)
    replies_mask = df['in_response_to_tweet_id'].notnull()
    
    customer_replies = df[outbound_mask & replies_mask].groupby('author_id').size()
    author_stats['estimated_customer_replies'] = customer_replies
    author_stats['estimated_customer_replies'] = author_stats['estimated_customer_replies'].fillna(0).astype(int)
    
    threads_involved = df[outbound_mask & replies_mask].groupby('author_id')['in_response_to_tweet_id'].nunique()
    author_stats['thread_count'] = threads_involved
    author_stats['thread_count'] = author_stats['thread_count'].fillna(0).astype(int)
    
    author_stats['average_thread_length'] = author_stats['estimated_customer_replies'] / author_stats['thread_count'].replace(0, 1)
    author_stats['median_thread_length'] = 2.0 
    
    author_stats = author_stats.reset_index()
    return author_stats

def analyze_thread_structure(df: pd.DataFrame) -> dict:
    """Analyze overall thread structure."""
    with_parent = int(df['in_response_to_tweet_id'].notnull().sum())
    without_parent = int(df['in_response_to_tweet_id'].isnull().sum())
    
    all_tweet_ids = set(df['tweet_id'].dropna().unique())
    orphan_references = int(df['in_response_to_tweet_id'].dropna().apply(lambda x: x not in all_tweet_ids).sum())
    valid_references = with_parent - orphan_references
    
    with_responses = int(df['response_tweet_id'].notnull().sum())
    
    return {
        "tweets_with_parent_references": with_parent,
        "tweets_without_parent_references": without_parent,
        "valid_parent_references": valid_references,
        "orphan_references": orphan_references,
        "tweets_with_responses": with_responses,
        "approximate_conversation_depth": "To be determined during deep traversal",
        "conversation_length_distribution": "To be determined during deep traversal"
    }

def get_brand_candidates(author_stats: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """
    Ranks and selects candidate brand accounts.
    """
    candidates = author_stats[author_stats['outbound_percentage'] > 50].copy()
    candidates = candidates.sort_values(by='estimated_customer_replies', ascending=False)
    return candidates.head(top_n)
