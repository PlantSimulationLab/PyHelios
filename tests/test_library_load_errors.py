"""Regression tests for library load error reporting (issue #17).

When the native library file exists but dlopen fails on a missing system
dependency, the error must report that dependency. It previously reported
"Expected files: ... Available library files: [...]" and told users to
rebuild, which describes a file-not-found condition that did not occur.
"""

import os
import sys
import pytest
from unittest.mock import patch

from pyhelios.plugins.loader import CrossPlatformLibraryLoader, LibraryLoadError


@pytest.mark.cross_platform
class TestMissingSystemLibraryError:
    """The loader must surface the real dlopen failure, not a rebuild hint."""

    def _loader_failing_with(self, tmp_path, message):
        """Build a loader whose plugin dir holds a library that fails to load."""
        loader = CrossPlatformLibraryLoader(str(tmp_path))
        loader.platform_name = 'Linux'

        # The library file exists - only loading it fails.
        (tmp_path / 'libhelios.so').write_bytes(b'\x7fELF stub')

        def failing_loader(path):
            raise OSError(message)

        loader._library_config['Linux'] = {
            'primary': 'libCHelios.so',
            'loader': failing_loader,
            'alternatives': ['libhelios.so', 'CHelios.so'],
            'dependencies': [],
        }
        return loader

    def test_reports_missing_shared_library_name(self, tmp_path):
        """The missing .so name must appear in the error message."""
        loader = self._loader_failing_with(
            tmp_path, 'libGL.so.1: cannot open shared object file: No such file or directory'
        )

        with pytest.raises(LibraryLoadError) as exc_info:
            loader.load_library()

        message = str(exc_info.value)
        assert 'libGL.so.1' in message, (
            f"Error must name the missing system library. Got:\n{message}"
        )

    def test_does_not_claim_library_file_is_missing(self, tmp_path):
        """A present-but-unloadable library must not be reported as absent."""
        loader = self._loader_failing_with(
            tmp_path, 'libGL.so.1: cannot open shared object file: No such file or directory'
        )

        with pytest.raises(LibraryLoadError) as exc_info:
            loader.load_library()

        message = str(exc_info.value)
        assert 'Expected files:' not in message, (
            f"Must not imply the library file is missing when it exists. Got:\n{message}"
        )
        assert 'build_helios' not in message, (
            f"Rebuilding does not fix a missing system dependency. Got:\n{message}"
        )

    def test_suggests_package_install_for_known_library(self, tmp_path):
        """Known GL/X11 libraries get an actionable install hint."""
        loader = self._loader_failing_with(
            tmp_path, 'libGL.so.1: cannot open shared object file: No such file or directory'
        )

        with pytest.raises(LibraryLoadError) as exc_info:
            loader.load_library()

        message = str(exc_info.value)
        assert 'libgl1' in message, (
            f"Error should name the Debian package providing libGL. Got:\n{message}"
        )

    def test_missing_library_file_still_suggests_rebuild(self, tmp_path):
        """A genuinely absent library keeps the original rebuild guidance."""
        loader = CrossPlatformLibraryLoader(str(tmp_path))
        loader.platform_name = 'Linux'  # tmp_path is empty - no library present

        with pytest.raises(LibraryLoadError) as exc_info:
            loader.load_library()

        message = str(exc_info.value)
        assert 'Expected files:' in message
        assert 'build_helios' in message


@pytest.mark.cross_platform
class TestMissingLibraryExtraction:
    """Unit coverage for parsing loader error messages."""

    def test_extracts_linux_dlopen_error(self):
        failures = [('/x/libhelios.so',
                     OSError('libSM.so.6: cannot open shared object file: No such file or directory'))]
        assert CrossPlatformLibraryLoader._extract_missing_libraries(failures) == ['libSM.so.6']

    def test_extracts_macos_dyld_error(self):
        failures = [('/x/libhelios.dylib',
                     OSError('Library not loaded: @rpath/libfoo.dylib'))]
        assert CrossPlatformLibraryLoader._extract_missing_libraries(failures) == ['libfoo.dylib']

    def test_ignores_unrelated_errors(self):
        failures = [('/x/libhelios.so', OSError('invalid ELF header'))]
        assert CrossPlatformLibraryLoader._extract_missing_libraries(failures) == []

    def test_deduplicates_repeated_libraries(self):
        msg = 'libGL.so.1: cannot open shared object file: No such file or directory'
        failures = [('/x/a.so', OSError(msg)), ('/x/b.so', OSError(msg))]
        assert CrossPlatformLibraryLoader._extract_missing_libraries(failures) == ['libGL.so.1']
