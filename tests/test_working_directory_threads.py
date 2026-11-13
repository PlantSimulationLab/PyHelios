"""
Regression tests for the process-global working-directory switch used for native asset lookup.

Several plugin wrappers change into the build directory around native calls because parts of
Helios open asset files by bare relative path. The working directory belongs to the whole process,
so overlapping calls from two threads used to restore it out of order: the first thread to finish
moved the directory out from under the second while it was still inside a native call, and the
second then "restored" the build directory, stranding the process there (GitHub issue #22).
"""

import importlib
import os
import threading

import pytest


WRAPPERS = {
    "plantarchitecture": ("pyhelios.PlantArchitecture", "_plantarchitecture_working_directory"),
    "leafoptics": ("pyhelios.LeafOptics", "_leafoptics_working_directory"),
    "radiation": ("pyhelios.RadiationModel", "_radiation_working_directory"),
    "solarposition": ("pyhelios.SolarPosition", "_solarposition_working_directory"),
    "visualizer": ("pyhelios.Visualizer", "_visualizer_working_directory"),
    "weberpenntree": ("pyhelios.WeberPennTree", "_weberpenntree_working_directory"),
}

THREAD_TIMEOUT = 30


def _wrapper(key):
    module_name, function_name = WRAPPERS[key]
    return getattr(importlib.import_module(module_name), function_name)


def _build_dir_or_skip(key):
    """Enter the wrapper once on its own to learn the directory it switches to."""
    before = os.getcwd()
    try:
        with _wrapper(key)():
            build_dir = os.getcwd()
    except Exception as e:  # assets missing from this build
        pytest.skip(f"{key} working-directory wrapper unusable in this build: {e}")
    assert os.getcwd() == before
    if os.path.realpath(build_dir) == os.path.realpath(before):
        pytest.skip(f"{key} wrapper does not change directory in this build")
    return build_dir


def _overlap(first_key, second_key):
    """
    Run two wrappers on two threads with interleaved, non-nested lifetimes:

        A enters, B enters, A exits, B checks the directory, B exits.

    Returns the working directory B observed after A had exited.
    """
    first, second = _wrapper(first_key), _wrapper(second_key)
    a_inside, b_inside, a_done = threading.Event(), threading.Event(), threading.Event()
    observed = {}
    errors = []

    def thread_a():
        try:
            with first():
                a_inside.set()
                assert b_inside.wait(THREAD_TIMEOUT)
        except BaseException as e:
            errors.append(e)
            b_inside.set()
        finally:
            a_inside.set()
            a_done.set()

    def thread_b():
        try:
            assert a_inside.wait(THREAD_TIMEOUT)
            with second():
                b_inside.set()
                assert a_done.wait(THREAD_TIMEOUT)
                observed["cwd"] = os.getcwd()
        except BaseException as e:
            errors.append(e)
        finally:
            b_inside.set()

    threads = [threading.Thread(target=thread_a), threading.Thread(target=thread_b)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(THREAD_TIMEOUT)
        assert not t.is_alive(), "overlapping working-directory threads deadlocked"
    if errors:
        raise errors[0]
    return observed["cwd"]


@pytest.mark.native_only
class TestOverlappingWorkingDirectoryWrappers:
    """Overlapping wrapper calls must keep the build directory for the duration and restore on last exit."""

    @pytest.mark.parametrize("key", sorted(WRAPPERS))
    def test_same_wrapper_on_two_threads(self, key, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        build_dir = _build_dir_or_skip(key)

        observed = _overlap(key, key)

        assert os.path.realpath(observed) == os.path.realpath(build_dir), (
            "the second thread lost the build directory while still inside its native call"
        )
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path), (
            "the process working directory was left changed after both calls finished"
        )

    @pytest.mark.parametrize("first_key,second_key", [
        ("plantarchitecture", "radiation"),
        ("visualizer", "plantarchitecture"),
        ("solarposition", "leafoptics"),
    ])
    def test_different_wrappers_on_two_threads(self, first_key, second_key, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        build_dir = _build_dir_or_skip(first_key)
        _build_dir_or_skip(second_key)

        observed = _overlap(first_key, second_key)

        assert os.path.realpath(observed) == os.path.realpath(build_dir)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path)


@pytest.mark.cross_platform
class TestBuildWorkingDirectoryHelper:
    """The shared helper itself, exercised against temporary directories."""

    @pytest.fixture
    def helper(self):
        from pyhelios.assets import working_directory
        return working_directory.build_working_directory

    def test_switches_and_restores(self, helper, tmp_path, monkeypatch):
        start = tmp_path / "start"
        build = tmp_path / "build"
        start.mkdir()
        build.mkdir()
        monkeypatch.chdir(start)

        with helper(build):
            assert os.path.realpath(os.getcwd()) == os.path.realpath(build)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(start)

    def test_non_nested_exits_restore_only_on_last(self, helper, tmp_path, monkeypatch):
        start = tmp_path / "start"
        build = tmp_path / "build"
        start.mkdir()
        build.mkdir()
        monkeypatch.chdir(start)

        a, b = helper(build), helper(build)
        a.__enter__()
        b.__enter__()
        a.__exit__(None, None, None)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(build)
        b.__exit__(None, None, None)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(start)

    def test_restores_when_body_raises(self, helper, tmp_path, monkeypatch):
        build = tmp_path / "build"
        build.mkdir()
        monkeypatch.chdir(tmp_path)

        with pytest.raises(KeyError):
            with helper(build):
                raise KeyError("boom")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path)

    def test_conflicting_directory_while_active_raises(self, helper, tmp_path, monkeypatch):
        build = tmp_path / "build"
        other = tmp_path / "other"
        build.mkdir()
        other.mkdir()
        monkeypatch.chdir(tmp_path)

        with helper(build):
            with pytest.raises(RuntimeError, match="already switched"):
                with helper(other):
                    pass
            assert os.path.realpath(os.getcwd()) == os.path.realpath(build)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path)

    def test_missing_directory_leaves_state_clean(self, helper, tmp_path, monkeypatch):
        build = tmp_path / "build"
        build.mkdir()
        monkeypatch.chdir(tmp_path)

        with pytest.raises(OSError):
            with helper(tmp_path / "does_not_exist"):
                pass
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path)

        with helper(build):
            assert os.path.realpath(os.getcwd()) == os.path.realpath(build)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(tmp_path)
