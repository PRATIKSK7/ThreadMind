from pathlib import Path
from src.threadmind import config

def test_configuration_imports_successfully():
    """Test that the configuration module imports and contains expected variables."""
    assert config.PROJECT_ROOT is not None
    assert config.DEFAULT_RANDOM_SEED == 42

def test_project_root_resolution():
    """Test that PROJECT_ROOT correctly resolves to the root directory."""
    assert (config.PROJECT_ROOT / "src").is_dir()
    assert (config.PROJECT_ROOT / "src" / "threadmind").is_dir()
    assert (config.PROJECT_ROOT / "tests").is_dir()

def test_expected_directories_exist():
    """Test that expected project directories are available."""
    assert config.DATA_DIR.is_dir()
    assert config.RAW_DATA_DIR.is_dir()
    assert config.PROCESSED_DATA_DIR.is_dir()
    assert config.EXPERIMENTS_DIR.is_dir()
    assert config.REPORTS_DIR.is_dir()
