#!/usr/bin/env python3
"""
Helper script to prepare PyHelios for wheel building.
This script builds native libraries and copies them to the correct location for packaging.
"""

import sys
import platform
import shutil
import glob
import os
from pathlib import Path
import subprocess
import ctypes

def validate_library(lib_path):
    """
    Validate that library is a proper PyHelios library that can be loaded.
    
    Args:
        lib_path: Path to the library file
        
    Returns:
        bool: True if library is valid and loadable, False otherwise
    """
    try:
        # Check file exists and has reasonable size
        if not lib_path.exists():
            print(f"Library file does not exist: {lib_path}")
            return False
            
        file_size = lib_path.stat().st_size
        if file_size < 1024:  # Less than 1KB is suspicious
            print(f"Library file suspiciously small ({file_size} bytes): {lib_path}")
            return False
            
        # Try to load the library
        system = platform.system()
        if system == 'Windows':
            lib = ctypes.WinDLL(str(lib_path))
        else:
            lib = ctypes.CDLL(str(lib_path))
            
        # Basic library loading is sufficient validation - don't check internal symbols
        # which may not be consistently exported across all PyHelios plugins
        print(f"[OK] Library validated: {lib_path.name}")
        return True
            
    except OSError as e:
        print(f"[ERROR] Cannot load library {lib_path.name}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error validating library {lib_path.name}: {e}")
        return False

def find_windows_dll_dependencies(lib_path, project_root):
    """
    Find and collect all required DLL dependencies for Windows wheels.

    Args:
        lib_path: Path to the main library (libhelios.dll)
        project_root: Path to project root directory

    Returns:
        List of Path objects for all required DLLs
    """
    if platform.system() != 'Windows':
        return []

    print(f"\nScanning Windows DLL dependencies for {lib_path.name}...")

    dependencies = []

    # 1. OptiX DLL (if radiation plugin is built)
    # PyHelios CMake copies OptiX DLL to build/lib/ directory for wheel packaging
    build_lib_dir = project_root / 'pyhelios_build' / 'build' / 'lib'
    optix_dlls = ['optix.6.5.0.dll', 'optix.51.dll']  # Support both versions

    for optix_dll in optix_dlls:
        optix_path = build_lib_dir / optix_dll
        if optix_path.exists():
            dependencies.append(optix_path)
            print(f"[FOUND] OptiX dependency: {optix_dll}")
            break

    # 2. CUDA Runtime DLLs (from CI environment)
    # Check common CUDA installation paths
    cuda_paths = [
        'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA',
        'C:\\Program Files (x86)\\NVIDIA GPU Computing Toolkit\\CUDA'
    ]

    cuda_dlls = ['cudart64_12.dll', 'cudart64_11.dll', 'cudart64_10.dll']  # Common versions
    for cuda_path in cuda_paths:
        cuda_root = Path(cuda_path)
        if cuda_root.exists():
            for version_dir in cuda_root.glob('v*'):
                bin_dir = version_dir / 'bin'
                if bin_dir.exists():
                    for cuda_dll in cuda_dlls:
                        cuda_dll_path = bin_dir / cuda_dll
                        if cuda_dll_path.exists():
                            dependencies.append(cuda_dll_path)
                            print(f"[FOUND] CUDA Runtime: {cuda_dll}")
                            break
                    break
            break

    # 3. Visual C++ Runtime (from Windows SDK/Visual Studio)
    vcruntime_dlls = ['vcruntime140.dll', 'msvcp140.dll', 'concrt140.dll']

    # Check system directories and Visual Studio installations
    system_paths = [
        'C:\\Windows\\System32',
        'C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Enterprise\\VC\\Redist\\MSVC',
        'C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\Enterprise\\VC\\Redist\\MSVC',
        'C:\\Program Files\\Microsoft Visual Studio\\2019\\Enterprise\\VC\\Redist\\MSVC',
        'C:\\Program Files\\Microsoft Visual Studio\\2022\\Enterprise\\VC\\Redist\\MSVC'
    ]

    for vc_dll in vcruntime_dlls:
        found = False
        for base_path in system_paths:
            base_path = Path(base_path)
            if base_path.exists():
                # Check direct path and subdirectories
                for dll_path in [base_path / vc_dll] + list(base_path.rglob(vc_dll)):
                    if dll_path.exists() and dll_path.is_file():
                        dependencies.append(dll_path)
                        print(f"[FOUND] VC++ Runtime: {vc_dll}")
                        found = True
                        break
                if found:
                    break

    # 4. Additional OptiX dependencies if found in NVIDIA directories
    nvidia_paths = [
        'C:\\Program Files\\NVIDIA Corporation\\OptiX SDK 6.5.0\\bin64',
        'C:\\ProgramData\\NVIDIA Corporation\\OptiX\\cache'
    ]

    for nvidia_path in nvidia_paths:
        nvidia_path = Path(nvidia_path)
        if nvidia_path.exists():
            for optix_file in nvidia_path.glob('*.dll'):
                if 'optix' in optix_file.name.lower():
                    dependencies.append(optix_file)
                    print(f"[FOUND] Additional OptiX: {optix_file.name}")

    print(f"Found {len(dependencies)} Windows DLL dependencies")
    return dependencies

def copy_assets_for_packaging(project_root):
    """
    Copy Helios assets to pyhelios/assets/build for packaging in wheels.
    
    Args:
        project_root: Path to project root directory
    """
    print("\nCopying assets for packaging...")
    
    # Source directories
    build_dir = project_root / 'pyhelios_build' / 'build'
    helios_core = project_root / 'helios-core'
    
    # Destination: pyhelios/assets/build
    dest_assets_dir = project_root / 'pyhelios' / 'assets' / 'build'
    dest_assets_dir.mkdir(parents=True, exist_ok=True)
    
    total_copied = 0
    
    # 1. Copy core lib/images directory from build
    core_images_src = build_dir / 'lib' / 'images'
    if core_images_src.exists():
        core_images_dest = dest_assets_dir / 'lib' / 'images'
        if core_images_dest.exists():
            shutil.rmtree(core_images_dest)
        shutil.copytree(core_images_src, core_images_dest)
        image_count = len(list(core_images_dest.glob('*')))
        print(f"[OK] Copied {image_count} core images to lib/images/")
        total_copied += image_count
    else:
        print(f"Warning: No core images found at {core_images_src}")
    
    # 2. Copy plugin assets from helios-core source
    if not helios_core.exists():
        print(f"Warning: helios-core directory not found at {helios_core}")
        return
    
    plugins_src_dir = helios_core / 'plugins'
    plugins_dest_dir = dest_assets_dir / 'plugins'
    
    if plugins_dest_dir.exists():
        shutil.rmtree(plugins_dest_dir)
    plugins_dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Asset types to look for in each plugin
    asset_patterns = {
        'shaders': ['*.glsl', '*.vert', '*.frag', '*.geom', '*.comp'],
        'textures': ['*.png', '*.jpg', '*.jpeg', '*.tiff', '*.bmp'],
        'fonts': ['*.ttf', '*.otf', '*.woff', '*.woff2'],
        'leaves': ['*.xml', '*.obj', '*.ply'],
        'wood': ['*.xml', '*.obj', '*.ply'],
        'xml': ['*.xml'],
        'spectral_data': ['*.csv', '*.txt', '*.dat'],
        'data': ['*.csv', '*.txt', '*.dat', '*.json'],
        'camera_light_models': ['*.xml', '*.json']
    }
    
    # Plugin-specific asset directory mappings (actual directory names in helios-core)
    # Only include plugins that are integrated with PyHelios
    plugin_asset_dirs = {
        'weberpenntree': ['leaves', 'wood', 'xml'],
        'visualizer': ['textures', 'shaders'],
        'plantarchitecture': ['assets/textures', 'assets/obj'],
        # NOTE: canopygenerator is not integrated with PyHelios - assets not needed
    }

    # Add radiation assets only on platforms that build GPU plugins (Windows/Linux)
    if platform.system() != 'Darwin':  # Exclude radiation on macOS
        radiation_assets = []

        # Add spectral data if it exists
        if Path(plugins_src_dir / 'radiation' / 'spectral_data').exists():
            radiation_assets.append('spectral_data')

        # Copy generated PTX files from build directory (critical for OptiX functionality)
        radiation_build_dir = build_dir / 'plugins' / 'radiation'
        if radiation_build_dir.exists():
            # Copy generated PTX files from build directory
            plugin_dest = dest_assets_dir / 'plugins' / 'radiation'
            plugin_dest.mkdir(parents=True, exist_ok=True)

            ptx_files = list(radiation_build_dir.glob('*.ptx'))
            if ptx_files:
                ptx_copied = 0
                for ptx_file in ptx_files:
                    try:
                        shutil.copy2(ptx_file, plugin_dest / ptx_file.name)
                        print(f"[OK] Copied PTX file: {ptx_file.name}")
                        ptx_copied += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to copy PTX file {ptx_file.name}: {e}")

                if ptx_copied > 0:
                    print(f"[OK] Successfully copied {ptx_copied} PTX files for radiation plugin")
                    total_copied += ptx_copied
            else:
                print(f"[WARNING] No PTX files found in radiation build directory: {radiation_build_dir}")
        else:
            print(f"[WARNING] Radiation build directory not found: {radiation_build_dir}")

        if radiation_assets:
            plugin_asset_dirs['radiation'] = radiation_assets
    
    # Process each plugin directory
    for plugin_dir in plugins_src_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
            
        plugin_name = plugin_dir.name
        plugin_assets_copied = 0
        
        # Get asset directories for this plugin
        asset_dirs = plugin_asset_dirs.get(plugin_name, [])
        if not asset_dirs:
            continue
            
        plugin_dest = plugins_dest_dir / plugin_name
        plugin_dest.mkdir(exist_ok=True)
        
        # Copy assets from each specified directory
        for asset_dir_path in asset_dirs:
            asset_src = plugin_dir / asset_dir_path
            if not asset_src.exists():
                continue

            # For nested paths, preserve the directory structure
            if '/' in asset_dir_path:
                # Create nested destination path to preserve structure
                asset_dest = plugin_dest / asset_dir_path
            else:
                # Use just the final directory name for flat directories
                asset_dir_name = asset_dir_path.split('/')[-1]
                asset_dest = plugin_dest / asset_dir_name

            # Ensure parent directories exist
            asset_dest.parent.mkdir(parents=True, exist_ok=True)

            if asset_dest.exists():
                shutil.rmtree(asset_dest)
            shutil.copytree(asset_src, asset_dest)
            
            # Count files copied
            files_copied = sum(1 for _ in asset_dest.rglob('*') if _.is_file())
            plugin_assets_copied += files_copied
        
        if plugin_assets_copied > 0:
            print(f"[OK] Copied {plugin_assets_copied} assets from {plugin_name} plugin")
            total_copied += plugin_assets_copied
    
    if total_copied > 0:
        print(f"[OK] Successfully copied {total_copied} total assets for packaging")
    else:
        print("Warning: No assets found to copy")

    # Note: Asset directories should NOT have __init__.py files as they are data directories,
    # not Python packages. setuptools handles them correctly via package_data configuration.

    print(f"[OK] Assets packaged in {dest_assets_dir}")

def build_and_prepare(build_args):
    """Build native libraries and copy them to pyhelios/plugins for packaging."""
    print("Building native libraries for wheel...")
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Validate environment
    print(f"Script directory: {script_dir}")
    print(f"Project root: {project_root}")
    print(f"Platform: {platform.system()}")
    print(f"Python executable: {sys.executable}")
    
    # Check required files exist
    build_script = script_dir / 'build_helios.py'
    if not build_script.exists():
        print(f"ERROR: build_helios.py not found at {build_script}")
        sys.exit(1)
    
    helios_core = project_root / 'helios-core'
    if not helios_core.exists():
        print(f"ERROR: helios-core submodule not found at {helios_core}")
        print("Available directories:")
        for item in project_root.iterdir():
            if item.is_dir():
                print(f"  {item.name}/")
        sys.exit(1)
    
    # Build native libraries
    build_cmd = [sys.executable, str(build_script)] + build_args
    print(f"Running build command: {' '.join(build_cmd)}")
    
    try:
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True, cwd=project_root)
        print("Native libraries built successfully")
        if result.stdout:
            print("Build stdout:", result.stdout[-500:])  # Last 500 chars
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"Build stdout: {e.stdout}")
        if e.stderr:
            print(f"Build stderr: {e.stderr}")
        sys.exit(1)
    
    # Copy built libraries to packaging location
    build_lib_dir = project_root / 'pyhelios_build' / 'build' / 'lib'
    plugins_dir = project_root / 'pyhelios' / 'plugins'
    
    if not build_lib_dir.exists():
        print(f"Warning: Build directory {build_lib_dir} does not exist")
        return
        
    # Verify source plugins directory exists (should contain Python files)
    if not plugins_dir.exists():
        print(f"ERROR: Source plugins directory not found: {plugins_dir}")
        print("The pyhelios/plugins/ directory with Python source files must exist")
        sys.exit(1)
        
    # Verify it has the required Python files
    py_files = list(plugins_dir.glob('*.py'))
    if not py_files:
        print(f"ERROR: No Python files found in plugins directory: {plugins_dir}")
        print("The plugins directory must contain __init__.py and other Python source files")
        sys.exit(1)
        
    print(f"Found {len(py_files)} Python source files in plugins directory")
    
    # Remove any existing binary libraries from the source directory
    # (These should not be there, but clean up just in case)
    system = platform.system()
    if system == 'Windows':
        old_libs = list(plugins_dir.glob('*.dll'))
    elif system == 'Darwin':
        old_libs = list(plugins_dir.glob('*.dylib'))
    else:
        old_libs = list(plugins_dir.glob('*.so*'))
        
    for old_lib in old_libs:
        print(f"Removing old library: {old_lib.name}")
        old_lib.unlink()
    
    # Platform-specific library extensions
    system = platform.system()
    if system == 'Windows':
        patterns = ['*.dll']
    elif system == 'Darwin':  # macOS
        patterns = ['*.dylib']
    else:  # Linux and others
        patterns = ['*.so', '*.so.*']
    
    # Find and validate libraries
    found_libraries = []
    for pattern in patterns:
        for lib_file in build_lib_dir.glob(pattern):
            found_libraries.append(lib_file)
    
    if not found_libraries:
        print(f"ERROR: No libraries found matching patterns {patterns} in {build_lib_dir}")
        print("Available files in build directory:")
        try:
            for item in build_lib_dir.iterdir():
                print(f"  - {item.name}")
        except:
            print("  (cannot list directory contents)")
        sys.exit(1)
    
    # Copy and validate libraries
    copied_count = 0
    failed_count = 0
    
    for lib_file in found_libraries:
        print(f"\nProcessing library: {lib_file.name}")
        
        # Validate library before copying
        if not validate_library(lib_file):
            print(f"[WARNING] Skipping invalid library: {lib_file.name}")
            failed_count += 1
            continue
            
        # Copy library
        dest_file = plugins_dir / lib_file.name
        try:
            shutil.copy2(lib_file, dest_file)
            print(f"[OK] Copied: {lib_file.name} -> {dest_file}")
            
            # Verify copied file
            if not dest_file.exists() or dest_file.stat().st_size != lib_file.stat().st_size:
                print(f"[ERROR] Copy verification failed for {lib_file.name}")
                failed_count += 1
                continue
                
            copied_count += 1
            
        except (OSError, PermissionError) as e:
            print(f"[ERROR] Failed to copy {lib_file.name}: {e}")
            failed_count += 1
    
    # Summary
    print(f"\n=== Library Copy Summary ===")
    print(f"Found: {len(found_libraries)} libraries")
    print(f"Copied: {copied_count} libraries")
    print(f"Failed: {failed_count} libraries")
    
    if copied_count == 0:
        print("ERROR: No libraries were successfully copied!")
        sys.exit(1)
    elif failed_count > 0:
        print(f"WARNING: {failed_count} libraries could not be copied")
        # Continue anyway - some failures might be acceptable
    
    print(f"[OK] Successfully prepared {copied_count} libraries for packaging")

    # Windows-specific: Bundle additional DLL dependencies
    if system == 'Windows' and copied_count > 0:
        print(f"\n=== Windows DLL Dependency Bundling ===")

        # Find the main library (usually libhelios.dll or helios.dll)
        main_library = None
        for lib_file in found_libraries:
            if 'helios' in lib_file.name.lower() and lib_file.suffix == '.dll':
                main_library = lib_file
                break

        if main_library:
            # Find all required DLL dependencies
            dependencies = find_windows_dll_dependencies(main_library, project_root)

            dependency_copied = 0
            dependency_failed = 0

            for dep_dll in dependencies:
                try:
                    dest_dll = plugins_dir / dep_dll.name

                    # Skip if already exists (avoid overwriting main libraries)
                    if dest_dll.exists():
                        print(f"[SKIP] Dependency already bundled: {dep_dll.name}")
                        continue

                    shutil.copy2(dep_dll, dest_dll)
                    print(f"[OK] Bundled dependency: {dep_dll.name}")
                    dependency_copied += 1

                except (OSError, PermissionError) as e:
                    print(f"[ERROR] Failed to bundle critical dependency {dep_dll.name}: {e}")
                    print(f"This dependency is required for libhelios.dll to load properly on Windows systems")
                    print(f"without development tools installed. The wheel will not work correctly.")
                    dependency_failed += 1

            print(f"\n=== Dependency Bundle Summary ===")
            print(f"Found: {len(dependencies)} DLL dependencies")
            print(f"Bundled: {dependency_copied} dependencies")
            print(f"Failed: {dependency_failed} dependencies")

            # Fail-fast: If critical dependencies are missing, the wheel is broken
            if len(dependencies) > 0 and dependency_copied == 0:
                print(f"[ERROR] CRITICAL: No Windows DLL dependencies were bundled!")
                print(f"This means the wheel will fail to load on systems without development tools.")
                print(f"Required dependencies: {[dep.name for dep in dependencies]}")
                print(f"The wheel build cannot continue with missing critical dependencies.")
                sys.exit(1)
            elif dependency_failed > 0:
                print(f"[ERROR] CRITICAL: {dependency_failed} critical dependencies could not be bundled!")
                print(f"The wheel will not work properly on clean Windows systems.")
                print(f"All dependencies must be bundled for the wheel to function correctly.")
                sys.exit(1)
            else:
                print(f"[OK] All {dependency_copied} Windows DLL dependencies bundled successfully")
        else:
            print(f"[WARNING] Could not find main Helios library for dependency analysis")

    # Copy assets for packaging
    copy_assets_for_packaging(project_root)

def main():
    """Main entry point."""
    if len(sys.argv) < 2 or '--help' in sys.argv or '-h' in sys.argv:
        print("prepare_wheel.py - Build PyHelios native libraries and prepare for wheel packaging")
        print()
        print("Usage: python prepare_wheel.py <build_args...>")
        print("Examples:")
        print("  python prepare_wheel.py --buildmode release --nogpu --verbose")
        print("  python prepare_wheel.py --plugins weberpenntree,visualizer")
        print("  python prepare_wheel.py --exclude radiation --buildmode debug")
        print()
        print("This script:")
        print("  1. Calls build_scripts/build_helios.py with the provided arguments")
        print("  2. Copies built libraries to pyhelios/plugins/ for wheel packaging")
        print("  3. Copies required assets to pyhelios/assets/build/")
        print("  4. Validates libraries can be loaded properly")
        print()
        print("Common build arguments:")
        print("  --buildmode {debug,release,relwithdebinfo}  CMake build type")
        print("  --nogpu                                     Exclude GPU plugins")
        print("  --novis                                     Exclude visualization plugins")
        print("  --plugins <plugin1,plugin2,...>            Specific plugins to build")
        print("  --exclude <plugin1,plugin2,...>            Plugins to exclude")
        print("  --clean                                     Clean build artifacts first")
        print("  --verbose                                   Verbose output")
        print()
        print("For complete build argument options, run:")
        print("  python build_scripts/build_helios.py --help")
        print()
        print("For list of integrated plugins, run:")
        print("  python build_scripts/build_helios.py --list-plugins")
        print("For list of all helios-core plugins, run:")
        print("  python build_scripts/build_helios.py --list-all-plugins")
        sys.exit(0 if '--help' in sys.argv or '-h' in sys.argv else 1)
    
    build_args = sys.argv[1:]
    build_and_prepare(build_args)

if __name__ == '__main__':
    main()