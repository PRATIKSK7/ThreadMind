import pandas as pd
from pathlib import Path
from src.threadmind import config

def load_twcs_dataset(file_path: Path = None) -> pd.DataFrame:
    """
    Loads the raw Twitter Customer Support dataset.
    Enforces string datatypes for all identifiers to prevent precision loss.
    """
    if file_path is None:
        file_path = config.RAW_DATA_DIR / "twcs.csv"
        
    if not file_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {file_path}")
        
    # Explicitly define string types for identifiers to avoid float conversions
    dtype_mapping = {
        'tweet_id': str,
        'author_id': str,
        'response_tweet_id': str,
        'in_response_to_tweet_id': str
    }
    
    # Read the CSV
    df = pd.read_csv(file_path, dtype=dtype_mapping)
    
    # Expected columns
    expected_cols = {
        'tweet_id', 'author_id', 'inbound', 'created_at', 
        'text', 'response_tweet_id', 'in_response_to_tweet_id'
    }
    
    missing_cols = expected_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Dataset missing expected columns: {missing_cols}")
        
    return df
