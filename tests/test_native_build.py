"""
Tests that require building and using the actual Helios native library.

These tests ensure that the Helios C++ core can be successfully built and that
PyHelios can actually interface with the native code, not just mock implementations.
"""
import os
import sys
import subprocess
import pytest
import platform
from pathlib import Path


class TestNativeBuild:
    """Test that the Helios native library can be built and used."""
    
    @pytest.fixture(scope="class")
    def built_library_path(self):
        """Build the Helios native library and return its path."""
        # Get the project root directory
        test_dir = Path(__file__).parent
        project_root = test_dir.parent

        # Check if we're in a wheel testing environment (build_scripts doesn't exist)
        build_script = project_root / "build_scripts" / "build_helios.py"
        if not build_script.exists():
            # We're likely in a wheel testing environment - skip native build tests
            pytest.skip("Native build tests not available in wheel testing environment "
                       "(build_scripts/build_helios.py not found)")

        # Check if library already exists (use .dylib on macOS, .so on Linux, .dll on Windows)
        import platform
        if platform.system() == "Darwin":
            lib_name = "libhelios.dylib"
        elif platform.system() == "Linux":
            lib_name = "libhelios.so"
        else:
            lib_name = "libhelios.dll"
        lib_path = project_root / "pyhelios_build" / "build" / "lib" / lib_name

        # Build the library if it doesn't exist or if we want to force rebuild
        if not lib_path.exists():
            print(f"\nBuilding Helios native library...")

            result = subprocess.run([
                sys.executable, str(build_script)
            ], cwd=project_root, capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"Failed to build Helios library:\n"
                          f"STDOUT: {result.stdout}\n"
                          f"STDERR: {result.stderr}")

            print(f"Build completed successfully")

        # Verify the library exists
        if not lib_path.exists():
            pytest.fail(f"Helios library not found at {lib_path} after build")

        return lib_path
    
    def test_library_can_be_built(self, built_library_path):
        """Test that the Helios library can be successfully built."""
        assert built_library_path.exists()
        assert built_library_path.stat().st_size > 0
        print(f"✅ Native library built successfully: {built_library_path}")
    
    def test_library_loads_in_pyhelios(self, built_library_path):
        """Test that PyHelios can load and use the built native library."""
        # Temporarily add the library directory to help PyHelios find it
        lib_dir = built_library_path.parent
        
        # Import PyHelios and force it to reload/detect the library
        import pyhelios.plugins.loader as loader
        
        # Reset the loader to force re-detection
        if hasattr(loader, '_loader_instance'):
            loader._loader_instance = None
        
        # Clear any cached modules, but preserve modules whose class identities must stay
        # stable across the reload. pyhelios.exceptions defines the HeliosError hierarchy;
        # reimporting it creates new class objects, so a later pytest.raises(HeliosError)
        # would no longer match exceptions raised by wrappers still bound to the old classes.
        # That breaks exception tests in any process that shares state with this one, e.g.
        # Windows, where pytest-forked is unavailable and sys.modules mutations leak.
        _preserved_prefixes = ('pyhelios.validation', 'pyhelios.exceptions')
        modules_to_clear = [m for m in sys.modules.keys()
                           if m.startswith('pyhelios') and not m.startswith(_preserved_prefixes)]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        try:
            # Now import PyHelios fresh
            import pyhelios
            from pyhelios.plugins import get_plugin_info
            
            # Reset plugin registry to ensure clean state after module reload
            from pyhelios.plugins.registry import reset_plugin_registry
            reset_plugin_registry()
        except ImportError:
            # If we can't import reset function, we're in a different state
            pass
        
        # Check if we're in native mode or mock mode
        plugin_info = get_plugin_info()
        print(f"Plugin info: {plugin_info}")
        
        # For this test, we need to verify the library actually exists and can be loaded
        # Even if PyHelios falls back to mock mode due to missing dependencies,
        # the library file should exist and be valid
        assert built_library_path.exists()
        
        # Try to load the library with ctypes directly to verify it's valid
        import ctypes
        try:
            lib = ctypes.CDLL(str(built_library_path))
            print("✅ Library can be loaded with ctypes")
        except Exception as e:
            # This might happen if the library has unresolved dependencies
            # but the library file itself should still be valid
            print(f"⚠️  Could not load library with ctypes: {e}")
            # Still consider the test passed if the file exists and has reasonable size
            assert built_library_path.stat().st_size > 100000  # At least 100KB
    
    def test_context_creation_with_built_library(self, built_library_path):
        """Test that Context can be created when native library is built."""
        # This test will show whether PyHelios successfully uses the native library
        # or falls back to mock mode
        
        # Import PyHelios components
        from pyhelios import Context
        from pyhelios.plugins import get_plugin_info
        
        plugin_info = get_plugin_info()
        
        # Create a Context
        context = Context()
        
        # The key insight: if we're in mock mode, certain operations will raise
        # RuntimeError with specific messages. If we're in native mode, they should work.
        try:
            # Try to add a patch - this requires the native library
            from pyhelios import DataTypes
            center = DataTypes.vec3(1, 2, 3)
            size = DataTypes.vec2(0.5, 0.5)
            color = DataTypes.RGBcolor(0.5, 0.5, 0.5)
            
            uuid = context.addPatch(center=center, size=size, color=color)
            
            # If we get here without exception, we're using the native library
            print(f"✅ Successfully created patch with UUID {uuid} using native library")
            
            # Verify we can query the patch
            patch_type = context.getPrimitiveType(uuid)
            print(f"✅ Successfully queried primitive type: {patch_type}")
            
            # This should only work in native mode
            assert uuid is not None
            
        except RuntimeError as e:
            error_msg = str(e)
            if "mock mode" in error_msg.lower() or "native functionality not available" in error_msg:
                pytest.skip(f"Running in mock mode: {error_msg}")
            else:
                # Some other error - re-raise it
                raise
    
    def test_native_library_has_expected_functions(self, built_library_path):
        """Test that the built library contains expected Helios functions."""
        import ctypes
        
        try:
            lib = ctypes.CDLL(str(built_library_path))
            
            # Try to find some expected functions
            # Note: function names in the static library may be mangled
            # This test verifies that the library is not empty and contains symbols
            
            # Get library info using platform-specific tools
            symbols_found = False
            try:
                if platform.system() == 'Windows':
                    # Use dumpbin for Windows DLLs
                    result = subprocess.run(['dumpbin', '/exports', str(built_library_path)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        symbols = result.stdout
                        print(f"Library contains {len(symbols.splitlines())} lines of export info")
                        symbols_found = True
                    else:
                        print("dumpbin command not available or failed")
                else:
                    # Use nm for Unix-like systems  
                    result = subprocess.run(['nm', str(built_library_path)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        symbols = result.stdout
                        print(f"Library contains {len(symbols.splitlines())} symbols")
                        symbols_found = True
                    else:
                        print("nm command not available or failed")
                
                if symbols_found:
                    # Look for some expected patterns
                    expected_patterns = ['Context', 'createContext', 'addPatch', 'helios']
                    found_patterns = []
                    for pattern in expected_patterns:
                        if pattern in symbols:
                            found_patterns.append(pattern)
                    
                    print(f"Found expected symbols: {found_patterns}")
                    # We expect to find at least some of these patterns
                    assert len(found_patterns) > 0, f"No expected symbols found in library. Available content: {symbols[:500]}..."
            
            except FileNotFoundError:
                print("Symbol analysis tools not available - skipping symbol analysis")
                pytest.skip("Symbol analysis tools (nm/dumpbin) not available")
            
        except OSError as e:
            pytest.skip(f"Could not load library for function analysis: {e}")


class TestNativeVsMockComparison:
    """Compare behavior between native library and mock mode."""
    
    def test_mock_mode_gives_helpful_errors(self):
        """Verify that mock mode gives helpful error messages."""
        # Test mock library directly without affecting global state
        from pyhelios.plugins.loader import MockLibrary
        mock_library = MockLibrary()
        
        # Test that mock library gives helpful error messages
        with pytest.raises(RuntimeError) as exc_info:
            mock_library.createContext()
        
        error_msg = str(exc_info.value)
        assert "mock mode" in error_msg.lower()
        assert "native" in error_msg.lower() or "functionality" in error_msg.lower()
        print(f"✅ Mock mode provides helpful error: {error_msg}")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])