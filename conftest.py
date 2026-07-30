"""
Root conftest.py to configure pytest globally for PyHelios.
"""
import pytest

def pytest_ignore_collect(collection_path, config):
    """Ignore helios-core directory from test collection."""
    if "helios-core" in str(collection_path):
        return True
    return False
