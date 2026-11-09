"""
Root conftest.py to configure pytest globally for PyHelios.
"""
import pytest

def pytest_ignore_collect(collection_path, config):
    """Ignore helios-core directory from test collection.

    Returns None for every other path: pytest stops at the first hook result that is not None, so returning False
    would override --ignore, collect_ignore and norecursedirs everywhere else.
    """
    if "helios-core" in str(collection_path):
        return True
    return None
