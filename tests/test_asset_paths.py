"""
Tests for pyhelios.assets.AssetPathManager environment setup.
"""

import os
import subprocess
import sys
import textwrap

import pytest

from pyhelios.assets import AssetPathManager

# Records HELIOS_BUILD at the moment the native library is opened. On Windows the
# library links the C runtime statically and snapshots the environment when it loads,
# so a HELIOS_BUILD set afterwards is invisible to the native code.
_RECORD_ENV_AT_LOAD = textwrap.dedent("""
    import ctypes, os, sys
    seen = []
    for name in ("CDLL", "WinDLL"):
        base = getattr(ctypes, name, None)
        if base is None:
            continue
        class Recording(base):
            def __init__(self, path, *a, **k):
                if "helios" in os.path.basename(str(path)).lower():
                    seen.append(os.environ.get("HELIOS_BUILD"))
                super().__init__(path, *a, **k)
        setattr(ctypes, name, Recording)
    import pyhelios
    if not seen:
        print("NOT_LOADED")
    else:
        print("AT_LOAD=" + repr(seen[0]))
""")


@pytest.mark.cross_platform
class TestHeliosBuildEnvironment:
    """HELIOS_BUILD is what the native core falls back on to resolve relative asset paths."""

    def test_helios_build_set_without_helios_core(self, tmp_path, monkeypatch):
        # A wheel install has packaged assets but no helios-core source directory.
        # HELIOS_BUILD must still point at the packaged assets; otherwise native asset
        # lookups (e.g. plugins/radiation/camera_light_models/*.obj) resolve against the
        # user's working directory and fail.
        monkeypatch.delenv("HELIOS_BUILD", raising=False)
        manager = AssetPathManager()
        monkeypatch.setattr(manager, "_find_helios_core", lambda: None)
        monkeypatch.setattr(manager, "_get_helios_build_path", lambda: tmp_path)

        manager.set_environment_variables()

        assert os.environ.get("HELIOS_BUILD") == str(tmp_path)

    def test_helios_build_not_set_when_no_build_path(self, monkeypatch):
        monkeypatch.delenv("HELIOS_BUILD", raising=False)
        manager = AssetPathManager()
        monkeypatch.setattr(manager, "_find_helios_core", lambda: None)
        monkeypatch.setattr(manager, "_get_helios_build_path", lambda: None)

        manager.set_environment_variables()

        assert "HELIOS_BUILD" not in os.environ


@pytest.mark.native_only
class TestHeliosBuildSetBeforeLibraryLoad:

    def test_helios_build_set_before_native_library_loads(self, tmp_path):
        env = {k: v for k, v in os.environ.items() if k != "HELIOS_BUILD"}
        result = subprocess.run(
            [sys.executable, "-c", _RECORD_ENV_AT_LOAD],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, result.stderr
        out = result.stdout.strip().splitlines()[-1]
        if out == "NOT_LOADED":
            pytest.skip("native library was not loaded")
        assert out != "AT_LOAD=None", "HELIOS_BUILD was not set when the native library loaded"
