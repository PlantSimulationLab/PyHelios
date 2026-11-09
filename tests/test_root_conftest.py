"""The root conftest's collection hook must leave every path it does not own to pytest's own ignore options."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# The root conftest belongs to a source checkout; the wheel tests copy only tests/ into an isolated directory.
pytestmark = pytest.mark.skipif(not (ROOT / "conftest.py").is_file(), reason="no repository-root conftest.py (not a source checkout)")


def _root_conftest():
    spec = importlib.util.spec_from_file_location("pyhelios_root_conftest", ROOT / "conftest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.cross_platform
def test_hook_ignores_helios_core():
    assert _root_conftest().pytest_ignore_collect(ROOT / "helios-core" / "core" / "tests", None) is True


@pytest.mark.cross_platform
def test_hook_does_not_decide_other_paths():
    # pytest_ignore_collect stops at the first result that is not None, so answering False here overrides --ignore,
    # collect_ignore and norecursedirs for every other path: tests/manual, which pytest.ini and tests/conftest.py both
    # exclude, was collected and failed on its extra dependencies.
    assert _root_conftest().pytest_ignore_collect(ROOT / "tests" / "manual" / "test_example.py", None) is None
