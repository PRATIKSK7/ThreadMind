import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root resolution (assumes this file is in src/threadmind/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data directory paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Other standard directories
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Default random seed for reproducibility
DEFAULT_RANDOM_SEED = 42

def get_env_var(key: str, default: str = None) -> str:
    """Safely fetch an environment variable."""
    return os.environ.get(key, default)
