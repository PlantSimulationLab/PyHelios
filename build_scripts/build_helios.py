#!/usr/bin/env python3
"""
Build script for compiling Helios C++ libraries for PyHelios.

This script provides cross-platform building of Helios native libraries
from the helios-core source code using CMake.
"""

import os
import sys
import subprocess
import shutil
import argparse
import platform
import re
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# Load plugin configurations directly to avoid pyhelios library loading
# We'll import the config data directly by reading and executing the files
current_dir = Path(__file__).parent.parent

# Execute plugin_metadata.py to get the configuration data
plugin_metadata_globals = {'__builtins__': __builtins__, '__name__': 'plugin_metadata'}
with open(current_dir / "pyhelios" / "config" / "plugin_metadata.py", 'r') as f:
    exec(f.read(), plugin_metadata_globals)

# Extract what we need from plugin_metadata
PLUGIN_METADATA = plugin_metadata_globals['PLUGIN_METADATA']
PluginMetadata = plugin_metadata_globals['PluginMetadata']
get_all_plugin_names = plugin_metadata_globals['get_all_plugin_names']
get_platform_compatible_plugins = plugin_metadata_globals['get_platform_compatible_plugins']

# Canonical list of plugins integrated into PyHelios
# This is the single source of truth - add new integrated plugins here
INTEGRATED_PLUGINS = [
    "visualizer",
    "weberpenntree",
    "radiation",
    "energybalance",
    "solarposition",
    "stomatalconductance",
    "photosynthesis",
    "plantarchitecture"
]

# Execute dependency_resolver.py to get PluginDependencyResolver
dependency_resolver_globals = plugin_metadata_globals.copy()  # Start with plugin_metadata context
dependency_resolver_globals['__name__'] = 'dependency_resolver'

# Read and modify the dependency_resolver source to remove relative imports
with open(current_dir / "pyhelios" / "config" / "dependency_resolver.py", 'r') as f:
    dependency_resolver_source = f.read()

# Replace the relative import with direct access to already loaded symbols
dependency_resolver_source = dependency_resolver_source.replace(
    "from .plugin_metadata import PLUGIN_METADATA, PluginMetadata, get_platform_compatible_plugins",
    "# Relative import replaced - using already loaded symbols"
)

exec(dependency_resolver_source, dependency_resolver_globals)

PluginDependencyResolver = dependency_resolver_globals['PluginDependencyResolver']


class HeliosBuildError(Exception):
    """Raised when Helios build fails."""
    pass


class HeliosBuilder:
    """Builder for Helios C++ libraries across platforms."""
    
    # Platform-specific build configurations
    PLATFORM_CONFIG = {
        'Windows': {
            'lib_name': 'libhelios.dll',  # Shared library for ctypes
            'build_type': 'Release',
            'generator': None,  # Will be auto-detected
            'cmake_args': [],  # Will be set based on architecture
            'build_args': ['--config', 'Release'],
        },
        'Darwin': {  # macOS
            'lib_name': 'libhelios.dylib',  # Shared library for ctypes
            'build_type': 'Release',
            'generator': 'Unix Makefiles',
            'cmake_args': ['-DCMAKE_BUILD_TYPE=Release'],
            'build_args': [],
        },
        'Linux': {
            'lib_name': 'libhelios.so',  # Shared library for ctypes
            'build_type': 'Release', 
            'generator': 'Unix Makefiles',
            'cmake_args': ['-DCMAKE_BUILD_TYPE=Release'],
            'build_args': [],
        }
    }
    
    def __init__(self, helios_root, output_dir, plugins=None, buildmode='release', explicitly_requested_plugins=None):
        """
        Initialize the Helios builder.

        Args:
            helios_root: Path to helios-core directory
            output_dir: Directory where built libraries should be placed
            plugins: List of plugins to build
            buildmode: Build mode ('debug', 'release', 'relwithdebinfo')
            explicitly_requested_plugins: List of plugins explicitly requested by user (for fail-fast behavior)
        """
        self.helios_root = Path(helios_root)
        self.output_dir = Path(output_dir)
        self.platform_name = platform.system()
        self.architecture = self._detect_architecture()
        
        # Helios-style project structure
        self.repo_root = self.helios_root.parent
        self.source_dir = self.repo_root / 'pyhelios_build'
        self.build_dir = self.source_dir / 'build'
        
        self.buildmode = buildmode.title()  # Convert to CMake format (Debug, Release, RelWithDebInfo)
        
        if self.platform_name not in self.PLATFORM_CONFIG:
            raise HeliosBuildError("Unsupported platform: {}".format(self.platform_name))
        
        # Get base config and update for architecture and build mode
        self.config = self.PLATFORM_CONFIG[self.platform_name].copy()
        self._configure_for_architecture()
        self._update_config_for_buildmode()
        
        # Set plugins
        self.selected_plugins = plugins if plugins else []
        self.explicitly_requested_plugins = explicitly_requested_plugins if explicitly_requested_plugins else []
        self.dependency_resolver = PluginDependencyResolver()
    
    def _detect_architecture(self) -> str:
        """Detect the target architecture for wheel building (Python target, not system)."""
        import sysconfig
        import os
        
        # Check if we're in a cibuildwheel environment - use Python target architecture
        if os.environ.get('CIBUILDWHEEL') == '1':
            print("Detected cibuildwheel environment - using Python target architecture")
            
            # First check for platform override from cibuildwheel
            auditwheel_plat = os.environ.get('AUDITWHEEL_PLAT', '')
            if auditwheel_plat:
                if 'arm64' in auditwheel_plat:
                    print("AUDITWHEEL_PLAT indicates arm64: {}".format(auditwheel_plat))
                    return 'arm64'
                elif 'x86_64' in auditwheel_plat:
                    print("AUDITWHEEL_PLAT indicates x86_64: {}".format(auditwheel_plat))
                    return 'x64'
            
            # Use enhanced detection method for Python 3.8 compatibility on Apple Silicon
            # Check HOST_GNU_TYPE which is more reliable than sysconfig.get_platform()
            config_vars = sysconfig.get_config_vars()
            host_gnu_type = config_vars.get('HOST_GNU_TYPE', '')
            print("Python HOST_GNU_TYPE: {}".format(host_gnu_type))
            
            if host_gnu_type and 'arm64' in host_gnu_type and 'apple' in host_gnu_type:
                print("Detected native ARM64 Python interpreter")
                return 'arm64'
            elif host_gnu_type and 'x86_64' in host_gnu_type:
                print("Detected x86_64 Python interpreter (may be running under Rosetta)")
                return 'x64'
            
            # Fallback to sysconfig platform detection  
            platform_str = sysconfig.get_platform()
            print("Python target platform from sysconfig: {}".format(platform_str))
            
            # For Python 3.8 on Apple Silicon, test ctypes architecture expectations
            # since ctypes may expect x86_64 even if sysconfig reports arm64
            if 'arm64' in platform_str:
                print("WARNING: Python 3.8 on Apple Silicon detected - testing ctypes compatibility")
                ctypes_arch = self._test_ctypes_architecture()
                if ctypes_arch:
                    print("ctypes architecture test result: {}".format(ctypes_arch))
                    return ctypes_arch
                else:
                    print("ctypes architecture test failed - falling back to ARM64")
                    return 'arm64'
            elif 'x86_64' in platform_str:
                return 'x64'
        
        # For macOS outside cibuildwheel, check system architecture
        if self.platform_name == 'Darwin':
            # On Apple Silicon, we might be running under Rosetta
            # Check native architecture using sysctl
            import subprocess
            try:
                # Check if we're running on Apple Silicon natively
                result = subprocess.run(['sysctl', '-n', 'hw.optional.arm64'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip() == '1':
                    return 'arm64'  # Native Apple Silicon
                else:
                    return 'x64'   # Intel Mac
            except:
                # Fallback to platform.machine()
                pass
        
        # Standard detection for other platforms
        machine = platform.machine().lower()
        
        # Normalize common architecture names
        if machine in ('x86_64', 'amd64', 'x64'):
            return 'x64'
        elif machine in ('arm64', 'aarch64'):
            return 'arm64'
        elif machine in ('i386', 'i686', 'x86'):
            return 'x86'
        elif machine.startswith('arm'):
            return 'arm'
        else:
            # Try Python's architecture detection as fallback
            import struct
            bits = struct.calcsize('P') * 8
            if bits == 64:
                # Default to x64 for 64-bit if unknown
                print(f"Warning: Unknown architecture '{machine}', assuming x64")
                return 'x64'
            else:
                print(f"Warning: Unknown architecture '{machine}', assuming x86")
                return 'x86'
    
    def _test_ctypes_architecture(self) -> Optional[str]:
        """Test what architecture ctypes expects by attempting to load system libraries."""
        import ctypes
        import os
        
        if self.platform_name != 'Darwin':
            return None
        
        # Test loading system libraries to determine ctypes architecture expectations
        try:
            # Try to load system C library - this should always be available
            libc_paths = [
                '/usr/lib/libc.dylib',  # System library path
                '/usr/lib/libSystem.dylib',  # Another system library
            ]
            
            for lib_path in libc_paths:
                if os.path.exists(lib_path):
                    try:
                        # Try to load the library - this will fail if architecture mismatch
                        lib = ctypes.CDLL(lib_path)
                        print(f"Successfully loaded system library: {lib_path}")
                        
                        # If we can load system libraries, check their architecture
                        import subprocess
                        try:
                            result = subprocess.run(['file', lib_path], 
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode == 0:
                                output = result.stdout.lower()
                                if 'arm64' in output:
                                    print("System libraries are ARM64 - ctypes expects arm64")
                                    return 'arm64'
                                elif 'x86_64' in output:
                                    print("System libraries are x86_64 - ctypes expects x86_64")
                                    return 'x64'
                        except:
                            pass
                            
                        # Fallback: if we can load it, assume it matches Python architecture
                        return None  # Let caller decide
                        
                    except OSError as e:
                        print(f"Failed to load {lib_path}: {e}")
                        # Architecture mismatch - continue to next library
                        continue
            
            print("Could not determine ctypes architecture from system libraries")
            return None
            
        except Exception as e:
            print(f"ctypes architecture test failed: {e}")
            return None
    
    def _detect_visual_studio_version(self) -> Tuple[str, str]:
        """Detect available Visual Studio version and return (generator, architecture)."""
        # List of Visual Studio generators to try (newest first)
        vs_generators = [
            ('Visual Studio 17 2022', 'x64' if self.architecture == 'x64' else 'Win32'),
            ('Visual Studio 16 2019', 'x64' if self.architecture == 'x64' else 'Win32'),
            ('Visual Studio 15 2017', 'x64' if self.architecture == 'x64' else 'Win32'),
            ('Visual Studio 14 2015', 'x64' if self.architecture == 'x64' else 'Win32'),
        ]
        
        # For ARM64 on Windows, only VS 2022 supports it well
        if self.architecture == 'arm64':
            vs_generators = [
                ('Visual Studio 17 2022', 'ARM64'),
            ]
        
        for generator, arch_flag in vs_generators:
            try:
                # Test if this generator is available
                test_cmd = ['cmake', '--help']
                result = subprocess.run(test_cmd, capture_output=True, text=True)
                if generator in result.stdout:
                    print(f"Detected Visual Studio generator: {generator} (architecture: {arch_flag})")
                    return generator, arch_flag
            except subprocess.CalledProcessError:
                continue
        
        # Fallback to default if none detected
        print("Warning: Could not detect Visual Studio version, using default VS 2019")
        return 'Visual Studio 16 2019', 'x64' if self.architecture == 'x64' else 'Win32'
    
    def _is_manylinux_container(self) -> bool:
        """Detect if running in a manylinux container."""
        try:
            # Check for manylinux indicator files/environment
            import os
            
            # Check environment variable used by cibuildwheel
            if os.environ.get('CIBUILDWHEEL') == '1':
                return True
            
            # Check for manylinux tag files
            manylinux_files = [
                '/etc/centos-release',
                '/etc/redhat-release',
                '/opt/python'  # manylinux containers have Python in /opt/python
            ]
            
            for indicator in manylinux_files:
                if Path(indicator).exists():
                    # Additional check - verify this is a manylinux environment
                    if 'centos' in str(Path('/etc/centos-release')).lower() if Path('/etc/centos-release').exists() else False:
                        return True
                    if Path('/opt/python').exists():
                        return True
            
            return False
        except Exception:
            return False
    
    def _apply_manylinux_zlib_fixes(self) -> None:
        """Apply zlib compatibility fixes for manylinux containers."""
        print("Detected manylinux container - zlib fixes applied via CMake configuration")
        
        # Set environment variable for CMake to detect manylinux
        import os
        os.environ['CIBUILDWHEEL'] = '1'
        
        print("Manylinux environment configured for CMake")
    
    def _configure_for_architecture(self):
        """Configure build settings based on detected architecture."""
        print(f"Detected architecture: {self.architecture}")
        
        if self.platform_name == 'Windows':
            # Auto-detect Visual Studio and set architecture
            generator, arch_flag = self._detect_visual_studio_version()
            self.config['generator'] = generator
            self.config['cmake_args'] = ['-A', arch_flag]
            
        elif self.platform_name == 'Darwin':  # macOS
            # Check if CMAKE_OSX_ARCHITECTURES is already set in environment (e.g., by cibuildwheel)
            env_cmake_arch = os.environ.get('CMAKE_OSX_ARCHITECTURES')
            if env_cmake_arch:
                self.config['cmake_args'].append(f'-DCMAKE_OSX_ARCHITECTURES={env_cmake_arch}')
                print(f"Using CMAKE_OSX_ARCHITECTURES from environment: {env_cmake_arch}")
                # Update our internal architecture tracking to match environment
                if env_cmake_arch == 'arm64':
                    self.architecture = 'arm64'
                    print("Configuring for Apple Silicon (ARM64) - from environment")
                else:
                    self.architecture = 'x64'  
                    print("Configuring for Intel Mac (x86_64) - from environment")
            elif self.architecture == 'arm64':
                # Apple Silicon - set CMAKE_OSX_ARCHITECTURES
                self.config['cmake_args'].append('-DCMAKE_OSX_ARCHITECTURES=arm64')
                print("Configuring for Apple Silicon (ARM64)")
            else:
                # Intel Mac - handle both 'x64' and 'x86_64' internally
                self.config['cmake_args'].append('-DCMAKE_OSX_ARCHITECTURES=x86_64')
                print("Configuring for Intel Mac (x86_64)")
                
        elif self.platform_name == 'Linux':
            # Check for manylinux container and apply zlib compatibility fixes
            if self._is_manylinux_container():
                self._apply_manylinux_zlib_fixes()
            
            if self.architecture == 'arm64':
                # ARM64 Linux - may need cross-compilation flags
                self.config['cmake_args'].extend([
                    '-DCMAKE_SYSTEM_PROCESSOR=aarch64',
                    '-DCMAKE_C_FLAGS=-march=armv8-a',
                    '-DCMAKE_CXX_FLAGS=-march=armv8-a'
                ])
                print("Configuring for ARM64 Linux")
            else:
                # x86_64 Linux (default)
                print("Configuring for x86_64 Linux")

    def get_optix_path(self) -> Optional[Path]:
        """Get platform-specific OptiX path."""
        optix_base = self.helios_root / 'plugins' / 'radiation' / 'lib' / 'OptiX'

        system = platform.system()
        if system == "Windows":
            # Check for Windows OptiX versions (prefer newer)
            for version in ["windows64-6.5.0", "windows64-5.1.1"]:
                optix_path = optix_base / version
                if optix_path.exists():
                    return optix_path
        elif system == "Linux":
            # Check for Linux OptiX versions (prefer newer)
            for version in ["linux64-6.5.0", "linux64-5.1.0"]:
                optix_path = optix_base / version
                if optix_path.exists():
                    return optix_path
        elif system == "Darwin":
            # macOS does not support NVIDIA GPUs - no OptiX support
            return None

        return None

    def clean_build_artifacts(self) -> None:
        """
        Clean all build artifacts for a fresh build.
        
        This removes both intermediate build artifacts and final packaged files
        that are generated during the build and wheel preparation process.
        """
        print("[CLEAN] Cleaning all build artifacts...")
        cleaned_items = []
        
        # Remove the build directory - this contains all intermediate build artifacts
        if self.build_dir.exists():
            print(f"Removing build directory: {self.build_dir}")
            shutil.rmtree(self.build_dir)
            cleaned_items.append("build artifacts")
        else:
            print(f"Build directory does not exist: {self.build_dir}")
        
        # Also clean packaged artifacts from wheel preparation
        repo_root = self.helios_root.parent
        
        # Remove packaged native libraries (copied by prepare_wheel.py)
        # Only remove binary libraries, preserve Python source files
        packaged_plugins = repo_root / 'pyhelios' / 'plugins'
        if packaged_plugins.exists():
            binary_extensions = ['.so', '.dll', '.dylib']
            removed_count = 0
            for ext in binary_extensions:
                for binary_file in packaged_plugins.glob(f'*{ext}'):
                    print(f"Removing binary library: {binary_file}")
                    binary_file.unlink()
                    removed_count += 1
            if removed_count > 0:
                cleaned_items.append(f"{removed_count} binary libraries")
            else:
                print("No binary libraries found to remove")
        
        # Remove packaged assets (copied by prepare_wheel.py)
        packaged_assets = repo_root / 'pyhelios' / 'assets' / 'build'
        if packaged_assets.exists():
            print(f"Removing packaged assets: {packaged_assets}")
            shutil.rmtree(packaged_assets)
            cleaned_items.append("packaged assets")
        
        # Note: _stub.c is a source file that should NOT be removed during cleaning
        # It's required for wheel building and should be committed to the repository
        
        if cleaned_items:
            print(f"[OK] Cleaned: {', '.join(cleaned_items)}")
        else:
            print("[OK] No artifacts found to clean")
        
        print("[OK] Build artifacts cleaning completed")
    
    def _update_config_for_buildmode(self):
        """Update configuration based on build mode."""
        if self.platform_name == 'Windows':
            # Windows uses multi-config generators
            self.config['build_args'] = ['--config', self.buildmode]
        else:
            # Unix systems use single-config generators
            cmake_build_type = f'-DCMAKE_BUILD_TYPE={self.buildmode}'
            # Replace existing CMAKE_BUILD_TYPE if present
            self.config['cmake_args'] = [arg for arg in self.config['cmake_args'] 
                                        if not arg.startswith('-DCMAKE_BUILD_TYPE')]
            self.config['cmake_args'].append(cmake_build_type)
    
    def resolve_plugin_selection(self) -> List[str]:
        """
        Resolve plugin dependencies and validate selection.
        
        Returns:
            Final list of plugins to build after dependency resolution
        """
        print(f"Resolving plugin dependencies for: {self.selected_plugins}")
        
        result = self.dependency_resolver.resolve_dependencies(
            self.selected_plugins,
            include_optional=True,
            strict_mode=False,
            explicitly_requested=self.explicitly_requested_plugins
        )
        
        if result.errors:
            for error in result.errors:
                print(f"[ERROR] {error}")
            raise HeliosBuildError("Plugin dependency resolution failed")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"[WARN] {warning}")
        
        if result.added_plugins:
            print(f"[OK] Added dependencies: {result.added_plugins}")
        
        if result.removed_plugins:
            print(f"[EXCLUDED] Removed incompatible plugins: {result.removed_plugins}")
        
        print(f"[OK] Final plugin selection: {result.final_plugins}")
        return result.final_plugins
    
    def validate_plugin_availability(self, plugins: List[str]) -> None:
        """
        Validate that all plugins exist in helios-core.
        
        Args:
            plugins: List of plugin names to validate
        """
        helios_plugins_dir = self.helios_root / 'plugins'
        missing_plugins = []
        
        for plugin in plugins:
            plugin_dir = helios_plugins_dir / plugin
            if not plugin_dir.exists():
                missing_plugins.append(plugin)
        
        if missing_plugins:
            print(f"[ERROR] Missing plugins in helios-core: {missing_plugins}")
            print(f"Available plugins in {helios_plugins_dir}:")
            if helios_plugins_dir.exists():
                available = [p.name for p in helios_plugins_dir.iterdir() if p.is_dir()]
                for plugin in sorted(available):
                    print(f"  - {plugin}")
            raise HeliosBuildError(f"Required plugins not found in helios-core: {missing_plugins}")
        
        print(f"[OK] All plugins available in helios-core: {plugins}")
    
    def generate_cmake_plugin_config(self, plugins: List[str]) -> Path:
        """
        Generate CMake configuration file for selected plugins.
        
        Args:
            plugins: List of plugins to configure
            
        Returns:
            Path to generated CMake configuration file
        """
        config_content = [
            "# Auto-generated plugin configuration for PyHelios",
            "# Generated by build_helios.py",
            "",
            f"# Selected plugins: {', '.join(plugins)}",
            f"set(PLUGINS \"{';'.join(plugins)}\")",
            "",
            "# Plugin-specific compile definitions"
        ]
        
        # Add compile definitions for each plugin
        for plugin in plugins:
            plugin_upper = plugin.upper()
            config_content.append(f"add_compile_definitions({plugin_upper}_PLUGIN_AVAILABLE)")
        
        # Add special handling for radiation plugin
        if "radiation" in plugins:
            config_content.extend([
                "",
                "# Radiation plugin configuration",
                "# Enable OptiX for GPU-accelerated ray tracing",
                "# Comment out the next line to disable OptiX",
                "# add_compile_definitions(HELIOS_NO_OPTIX)"
            ])
        else:
            config_content.extend([
                "",
                "# Radiation plugin not selected - disable OptiX",
                "add_compile_definitions(HELIOS_NO_OPTIX)"
            ])
        
        config_content.extend([
            "",
            "# Force position-independent code for shared library creation",
            "set(CMAKE_POSITION_INDEPENDENT_CODE ON)",
            ""
        ])
        
        # Write configuration to CMake file
        config_file = self.build_dir / "plugin_config.cmake"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            f.write('\n'.join(config_content))
        
        print(f"[OK] Generated plugin configuration: {config_file}")
        return config_file
    
    def check_prerequisites(self) -> None:
        """Check that required tools are available."""
        # Check for CMake
        try:
            result = subprocess.run(['cmake', '--version'], 
                                  capture_output=True, text=True, check=True)
            cmake_version = result.stdout.split()[2]
            print(f"Found CMake: {cmake_version}")
            
            # Check minimum CMake version for architecture support
            if self.architecture == 'arm64' and self.platform_name == 'Darwin':
                major, minor = cmake_version.split('.')[:2]
                if int(major) < 3 or (int(major) == 3 and int(minor) < 20):
                    print(f"Warning: CMake {cmake_version} may have limited Apple Silicon support. Consider upgrading to 3.20+")
                    
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise HeliosBuildError("CMake not found. Please install CMake.")
        
        # Check for compiler
        if self.platform_name == 'Windows':
            # Improved Visual Studio detection
            vs_found = False
            try:
                # Try multiple methods to find Visual Studio
                methods = [
                    ['where', 'cl'],
                    ['where', 'devenv'],
                    ['where', 'MSBuild']
                ]
                
                for method in methods:
                    try:
                        result = subprocess.run(method, capture_output=True, check=True, text=True)
                        print(f"Found Visual Studio component: {method[1]}")
                        vs_found = True
                        break
                    except subprocess.CalledProcessError:
                        continue
                        
                if not vs_found:
                    # Check for Build Tools via registry or common paths
                    common_vs_paths = [
                        r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe',
                        r'C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe',
                        r'C:\Program Files\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe',
                        r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe'
                    ]
                    
                    for vs_path in common_vs_paths:
                        if os.path.exists(vs_path):
                            print(f"Found Visual Studio at: {vs_path}")
                            vs_found = True
                            break
                            
                if not vs_found:
                    print("Warning: Visual Studio not detected via standard methods")
                    print("Please ensure Visual Studio 2019+ or Build Tools are installed")
                    if self.architecture == 'arm64':
                        print("Note: ARM64 support requires Visual Studio 2022 or newer")
                        
            except Exception as e:
                print(f"Warning: Error checking for Visual Studio: {e}")
                
        else:
            # Check for GCC/Clang on Unix systems with architecture awareness
            compiler_found = False
            try:
                result = subprocess.run(['gcc', '--version'], 
                                      capture_output=True, text=True, check=True)
                gcc_version = result.stdout.split('\n')[0]
                print(f"Found GCC: {gcc_version}")
                
                # Check cross-compilation support for ARM64
                if self.architecture == 'arm64' and self.platform_name == 'Linux':
                    try:
                        subprocess.run(['gcc', '-march=armv8-a', '--help'], 
                                     capture_output=True, check=True)
                        print("GCC supports ARM64 compilation")
                    except subprocess.CalledProcessError:
                        print("Warning: GCC may not support ARM64 compilation flags")
                        
                compiler_found = True
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    result = subprocess.run(['clang', '--version'], 
                                          capture_output=True, text=True, check=True)
                    clang_version = result.stdout.split('\n')[0]
                    print(f"Found Clang: {clang_version}")
                    compiler_found = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
                    
            if not compiler_found:
                raise HeliosBuildError("No suitable compiler found (gcc or clang)")
        
        # Check that source directory exists
        if not self.source_dir.exists():
            raise HeliosBuildError(f"PyHelios source directory not found: {self.source_dir}")
        
        pyhelios_cmake = self.source_dir / 'CMakeLists.txt'
        if not pyhelios_cmake.exists():
            raise HeliosBuildError(f"PyHelios build CMakeLists.txt not found: {pyhelios_cmake}")
        
        core_cmake_project = self.helios_root / 'core' / 'CMake_project.cmake'
        if not core_cmake_project.exists():
            raise HeliosBuildError(f"Helios CMake_project.cmake not found: {core_cmake_project}")
        
        print(f"Prerequisites check passed (Platform: {self.platform_name}, Architecture: {self.architecture})")
        if self.platform_name == 'Windows':
            print(f"Using CMake generator: {self.config['generator']}")
            print(f"Target architecture: {self.config['cmake_args'][1] if len(self.config['cmake_args']) > 1 else 'default'}")
    
    def setup_build_directory(self) -> None:
        """Set up the build directory."""
        if self.build_dir.exists():
            print(f"Build directory exists, skipping cleanup: {self.build_dir}")
        else:
            self.build_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created build directory: {self.build_dir}")
    
    def run_cmake_configure(self, additional_args: Optional[List[str]] = None) -> None:
        """Run CMake configuration."""
        # Use relative path from build directory to source directory to avoid path interpretation issues
        # Since build_dir = source_dir / 'build', the relative path from build to source is '..'
        source_path = '..' if self.build_dir.parent == self.source_dir else str(self.source_dir)
        
        cmake_cmd = [
            'cmake',
            source_path,  # Use relative path to PyHelios source directory
            '-G', self.config['generator']
        ]
        
        # Add platform-specific arguments
        cmake_cmd.extend(self.config['cmake_args'])
        
        # OpenMP handling is now managed via CMAKE_DISABLE_FIND_PACKAGE_OpenMP environment variable
        # for cibuildwheel cross-compilation scenarios
        
        # Add architecture-specific flags for cross-platform compatibility
        if self.platform_name != 'Windows':
            # Ensure PIC for shared libraries on Unix systems
            cmake_cmd.extend([
                '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
                '-DCMAKE_CXX_FLAGS=-fPIC',
                '-DCMAKE_C_FLAGS=-fPIC'
            ])
        
        # Add additional arguments if provided
        if additional_args:
            cmake_cmd.extend(additional_args)
        
        # Add PyHelios-specific options
        if self.platform_name == 'Windows':
            # On Windows, disable shared libs for dependencies but enable for PyHelios
            cmake_cmd.extend([
                '-DBUILD_SHARED_LIBS=OFF',  # Static dependencies to avoid DLL hell
                '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded',  # Static MSVC runtime
                '-DZLIB_ROOT=',  # Use bundled zlib
                '-DPNG_BUILD_ZLIB=ON',  # Build PNG with bundled zlib
                '-DPNG_SHARED=OFF',  # Static libpng
                '-DJPEG_BUILD_SHARED=OFF',  # Static libjpeg
            ])
        else:
            cmake_cmd.extend([
                '-DBUILD_SHARED_LIBS=ON',  # Build as shared library on Unix
            ])
        
        # Windows-specific workaround for zlib resource compilation issue
        if self.platform_name == 'Windows':
            # The RC compiler fails on win32/zlib1.rc due to C syntax in included headers
            # Patch zlib CMakeLists.txt to disable the problematic shared library target
            self._patch_zlib_cmake_for_windows()
            
            # Disable resource compilation entirely if CMAKE_RC_COMPILER is not set
            if not os.environ.get('CMAKE_RC_COMPILER'):
                cmake_cmd.extend(['-DCMAKE_RC_COMPILER='])  # Empty RC compiler disables resource compilation
        
        print(f"Running CMake configure: {' '.join(cmake_cmd)}")
        print(f"Working directory: {self.build_dir}")
        print(f"Source directory (relative): {source_path} -> {self.source_dir}")
        
        try:
            subprocess.run(cmake_cmd, cwd=self.build_dir, check=True)
            print("CMake configuration completed successfully")
        except subprocess.CalledProcessError as e:
            raise HeliosBuildError(f"CMake configuration failed: {e}")
    
    def run_cmake_build(self) -> None:
        """Run CMake build."""
        cmake_cmd = ['cmake', '--build', '.']
        
        # Add platform-specific build arguments
        cmake_cmd.extend(self.config['build_args'])
        
        # Add parallel build if supported
        if self.platform_name != 'Windows':
            import multiprocessing
            cmake_cmd.extend(['-j', str(multiprocessing.cpu_count())])
        
        print(f"Running CMake build: {' '.join(cmake_cmd)}")
        
        try:
            subprocess.run(cmake_cmd, cwd=self.build_dir, check=True)
            print("CMake build completed successfully")
        except subprocess.CalledProcessError as e:
            raise HeliosBuildError(f"CMake build failed: {e}")
    
    def find_built_library(self) -> Path:
        """Find the built library in the build directory."""
        lib_name = self.config['lib_name']
        
        # Common locations where the library might be
        search_paths = [
            self.build_dir / lib_name,
            self.build_dir / 'Release' / lib_name,
            self.build_dir / 'Debug' / lib_name,
            self.build_dir / 'lib' / lib_name,
            self.build_dir / 'core_shared' / lib_name,  # Our custom build location
            self.build_dir / 'core_shared' / 'Release' / lib_name,
            self.build_dir / 'core_shared' / 'Debug' / lib_name,
        ]
        
        for path in search_paths:
            if path.exists():
                print(f"Found built library: {path}")
                return path
        
        # If not found in expected locations, search recursively
        print(f"Library not found in expected locations, searching recursively...")
        for path in self.build_dir.rglob(lib_name):
            print(f"Found built library: {path}")
            return path
            
        # If shared library not found, look for static library as fallback
        if self.platform_name in ['Darwin', 'Linux']:
            static_lib = 'libhelios.a'
            static_paths = [
                self.build_dir / 'lib' / static_lib,
                self.build_dir / static_lib,
            ]
            for path in static_paths:
                if path.exists():
                    print(f"Found static library (will need conversion): {path}")
                    return path
            
            # Search recursively for static library
            for path in self.build_dir.rglob(static_lib):
                print(f"Found static library (will need conversion): {path}")
                return path
        
        raise HeliosBuildError(f"Built library {lib_name} not found in build directory")
    
    def _check_windows_dll_dependencies(self, dll_path: Path) -> Dict[str, bool]:
        """
        Check Windows DLL dependencies using dumpbin if available.
        
        Args:
            dll_path: Path to the DLL to check
            
        Returns:
            Dictionary of dependency name -> found status
        """
        dependencies = {}
        
        try:
            # Try using dumpbin to check dependencies
            result = subprocess.run(
                ['dumpbin', '/dependents', str(dll_path)], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                in_dependencies = False
                
                for line in lines:
                    line = line.strip()
                    if 'Image has the following dependencies:' in line:
                        in_dependencies = True
                        continue
                    elif in_dependencies and line:
                        if line.endswith('.dll'):
                            dep_name = line.lower()
                            # Check if this is a system DLL that should be available
                            system_dlls = {
                                'kernel32.dll', 'user32.dll', 'gdi32.dll', 'advapi32.dll',
                                'msvcrt.dll', 'vcruntime140.dll', 'msvcp140.dll', 'ucrtbase.dll'
                            }
                            
                            if dep_name in system_dlls:
                                dependencies[dep_name] = True  # Assume system DLLs are available
                            else:
                                # Check if the DLL exists in system paths
                                try:
                                    result_check = subprocess.run(
                                        ['where', dep_name], capture_output=True
                                    )
                                    dependencies[dep_name] = result_check.returncode == 0
                                except:
                                    dependencies[dep_name] = False
                        elif line.startswith('Summary'):
                            break
                            
            print(f"DLL dependencies for {dll_path.name}:")
            for dep, found in dependencies.items():
                status = "OK" if found else "MISSING"
                print(f"  [{status}] {dep}")
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            print(f"Could not check DLL dependencies (dumpbin not available)")
            
        return dependencies

    def _validate_library_loadable(self, library_path: Path) -> None:
        """
        Validate that the library can be loaded by ctypes.
        
        Implements fail-fast philosophy - if the library cannot be loaded,
        fail immediately with a clear error message rather than allowing
        silent failures at runtime.
        
        Args:
            library_path: Path to the library to validate
            
        Raises:
            HeliosBuildError: If library cannot be loaded by ctypes
        """
        try:
            import ctypes
            
            # Check dependencies before attempting to load (Windows only)
            if self.platform_name == 'Windows':
                print(f"Checking Windows DLL dependencies for: {library_path.name}")
                dependencies = self._check_windows_dll_dependencies(library_path)
                missing_deps = [dep for dep, found in dependencies.items() if not found]
                
                if missing_deps:
                    print(f"WARNING: Missing dependencies detected: {missing_deps}")
                    print("This may cause ctypes loading to fail")
                
                # Test Windows DLL loading
                test_lib = ctypes.WinDLL(str(library_path))
            else:
                # Test Unix shared library loading
                test_lib = ctypes.CDLL(str(library_path))
            
            # If we get here, the library loaded successfully
            print(f"[OK] Library validation passed: {library_path} can be loaded by ctypes")
            
        except Exception as e:
            # FAIL-FAST: Library cannot be loaded by ctypes
            if self.platform_name == 'Windows':
                # Windows-specific error handling and dependency checking
                error_msg = (
                    f"CRITICAL: Built Windows DLL cannot be loaded by ctypes: {library_path}\n"
                    f"Load error: {e}\n\n"
                    f"This indicates missing DLL dependencies. Common causes:\n\n"
                    f"1. Visual C++ Runtime Libraries missing\n"
                    f"2. Static linking not configured properly\n"
                    f"3. Third-party dependencies (zlib, libpng, etc.) not embedded\n"
                    f"4. Architecture mismatch (x86 vs x64)\n\n"
                    f"Windows-specific solutions:\n"
                    f"1. Install Visual C++ Redistributable (vcredist)\n"
                    f"2. Use static linking: -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded\n"
                    f"3. Ensure -DBUILD_SHARED_LIBS=OFF for dependencies\n"
                    f"4. Check DLL dependencies with 'dumpbin /dependents {library_path.name}'\n"
                    f"5. Verify architecture matches Python (x86 vs x64)\n\n"
                    f"The built DLL has missing dependencies and cannot be used."
                )
            else:
                # Unix error handling
                error_msg = (
                    f"CRITICAL: Built library cannot be loaded by ctypes: {library_path}\n"
                    f"Load error: {e}\n\n"
                    f"This is a fatal build error. PyHelios requires libraries that can be loaded by ctypes.\n\n"
                    f"Possible causes:\n"
                    f"1. Static library (.a) was created instead of shared library (.dylib/.so/.dll)\n"
                    f"2. Missing dependencies or incorrect linking\n"
                    f"3. Architecture mismatch (x86 vs ARM64)\n"
                    f"4. Corrupted library file\n\n"
                    f"Solutions:\n"
                    f"1. Ensure CMake builds shared libraries: -DBUILD_SHARED_LIBS=ON\n"
                    f"2. Check that all dependencies are available\n"
                    f"3. Rebuild with correct architecture flags\n"
                    f"4. Verify library dependencies with 'otool -L' (macOS) or 'ldd' (Linux)\n\n"
                    f"This build cannot proceed with an unusable library."
                )
            raise HeliosBuildError(error_msg)
    
    def copy_to_output(self, library_path: Path) -> Path:
        """Copy built library to output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # First, check for CMake-built shared library from pyhelios_shared target
        cmake_shared_lib = None
        if self.platform_name == 'Darwin':
            cmake_shared_lib = self.build_dir / 'lib' / 'libhelios.dylib'
        elif self.platform_name == 'Linux':
            cmake_shared_lib = self.build_dir / 'lib' / 'libhelios.so'
        elif self.platform_name == 'Windows':
            cmake_shared_lib = self.build_dir / 'lib' / 'libhelios.dll'
        
        if cmake_shared_lib and cmake_shared_lib.exists():
            print(f"Found CMake-built shared library: {cmake_shared_lib}")
            output_path = self.output_dir / cmake_shared_lib.name
            
            # Only copy if source and destination are different
            if cmake_shared_lib.resolve() != output_path.resolve():
                shutil.copy2(cmake_shared_lib, output_path)
                print(f"Copied CMake-built library to: {output_path}")
            else:
                print(f"Library is already in target location: {output_path}")
            
            # Validate that the library can be loaded by ctypes
            self._validate_library_loadable(output_path)
            return output_path
        
        # Fallback: Check if we found a static library but need a shared library
        if library_path.name == 'libhelios.a' and self.platform_name in ['Darwin', 'Linux']:
            print("Found static library but PyHelios needs shared library for ctypes")
            print("CMake-built shared library not found, attempting manual conversion...")
            print("WARNING: Manual conversion is deprecated. Consider ensuring CMake builds shared libraries properly.")
            
            # Create shared library from static library
            shared_lib_name = self.config['lib_name']
            output_path = self.output_dir / shared_lib_name
            
            try:
                if self.platform_name == 'Darwin':
                    # macOS: Use clang++ to create shared library with modern approach
                    build_lib_dir = self.build_dir / 'lib'
                    
                    # Clean libraries by removing duplicate test objects (modern approach)
                    cleaned_libs = self._clean_duplicate_symbols(library_path, build_lib_dir)
                    
                    cmd = [
                        'clang++', '-dynamiclib', '-o', str(output_path),
                        '-Wl,-force_load', str(cleaned_libs['main']),  # Use force_load for better control
                        '-L/opt/homebrew/lib',  # Homebrew library path
                        '-L/usr/local/lib',     # Alternative library path
                        '-ljpeg', '-lpng', '-lz', '-lstdc++',
                        '-framework', 'OpenGL',  # OpenGL framework for visualizer
                        '-lbz2'  # BZ2 library for FreeType
                    ]
                    
                    # Include cleaned plugin libraries
                    for lib_path in cleaned_libs['plugins']:
                        cmd.extend(['-Wl,-force_load', str(lib_path)])
                        print(f"Including cleaned plugin library: {lib_path.name}")
                    
                    # Include plugin dependencies
                    for lib_path in cleaned_libs['dependencies']:
                        if lib_path.suffix == '.dylib':
                            # For shared libraries, copy to output dir and link with proper path
                            dest_lib = self.output_dir / lib_path.name
                            shutil.copy2(lib_path, dest_lib)
                            
                            if 'libglfw' in lib_path.name:
                                # Link to the copied version and set rpath to find it locally
                                cmd.append(str(dest_lib))
                                cmd.extend(['-Wl,-rpath,@loader_path'])
                                print(f"Including GLFW dependency (with local rpath): {lib_path.name}")
                            else:
                                cmd.append(str(dest_lib))
                                print(f"Including shared dependency: {lib_path.name} (copied to output)")
                        else:
                            # For static libraries, use force_load to embed
                            cmd.extend(['-Wl,-force_load', str(lib_path)])
                            print(f"Including static dependency: {lib_path.name}")
                    
                    # Include additional static libraries (like static GLFW)
                    for lib_path in cleaned_libs['static_libs']:
                        cmd.extend(['-Wl,-force_load', str(lib_path)])
                        print(f"Including additional static library: {lib_path.name}")
                        
                else:  # Linux
                    # Linux: Use gcc to create shared library, linking bundled PNG and Z libraries
                    build_lib_dir = self.build_dir / 'lib'
                    libpng_path = build_lib_dir / 'libpng16.a'
                    libz_path = build_lib_dir / 'libz.a'
                    libjpeg_path = build_lib_dir / 'libjpeg.a'
                    
                    # Look for pyhelios_interface object file
                    interface_obj_path = self.build_dir / 'CMakeFiles' / 'pyhelios_build.dir' / 'pyhelios_interface.cpp.o'
                    
                    # Check if interface object was compiled with PIC, recompile if needed
                    interface_obj_pic_path = None
                    if interface_obj_path.exists():
                        # Check if the object was compiled with PIC by trying to use it
                        test_cmd = ['gcc', '-shared', '-o', '/tmp/test_pic.so', str(interface_obj_path)]
                        test_result = subprocess.run(test_cmd, capture_output=True, text=True)
                        if test_result.returncode == 0:
                            print(f"Found PyHelios interface object (PIC-compatible): {interface_obj_path}")
                            interface_obj_pic_path = interface_obj_path
                        else:
                            print(f"Interface object needs PIC recompilation: {interface_obj_path}")
                            # Recompile with PIC
                            interface_src = self.source_dir / 'pyhelios_interface.cpp'
                            interface_obj_pic_path = self.build_dir / 'pyhelios_interface_pic.o'
                            
                            pic_cmd = [
                                'g++', '-fPIC', '-c', 
                                f'-I{self.helios_root}/core/include',
                                f'-I{self.helios_root}/core/src', 
                                f'-I{self.helios_root}/core/lib',
                                f'-I{self.helios_root}/core/lib/pugixml',
                                f'-I{self.helios_root}/plugins/radiation/include',
                                f'-I{self.helios_root}/plugins/radiation/lib/json',
                                f'-I{self.get_optix_path()}/include' if self.get_optix_path() else f'-I{self.helios_root}/plugins/radiation/lib/OptiX/linux64-6.5.0/include',
                                '-DNDEBUG', '-O3',
                                str(interface_src), '-o', str(interface_obj_pic_path)
                            ]
                            
                            print(f"Recompiling interface with PIC: {' '.join(pic_cmd)}")
                            pic_result = subprocess.run(pic_cmd, capture_output=True, text=True)
                            if pic_result.returncode != 0:
                                print(f"PIC recompilation failed: {pic_result.stderr}")
                                interface_obj_pic_path = None
                        
                        # Clean up test file
                        try:
                            os.remove('/tmp/test_pic.so')
                        except:
                            pass
                    else:
                        print(f"Warning: PyHelios interface object not found at: {interface_obj_path}")
                    
                    cmd = [
                        'gcc', '-shared', '-fPIC', '-o', str(output_path),
                        '-Wl,--whole-archive', str(library_path), '-Wl,--no-whole-archive',
                        '-lstdc++', '-lgomp'
                    ]
                    
                    # Add PIC-compiled interface object if available
                    if interface_obj_pic_path:
                        cmd.append(str(interface_obj_pic_path))
                    
                    # Add bundled libraries if they exist
                    if libpng_path.exists():
                        cmd.extend(['-Wl,--whole-archive', str(libpng_path), '-Wl,--no-whole-archive'])
                    if libz_path.exists():
                        cmd.extend(['-Wl,--whole-archive', str(libz_path), '-Wl,--no-whole-archive'])  
                    if libjpeg_path.exists():
                        cmd.extend(['-Wl,--whole-archive', str(libjpeg_path), '-Wl,--no-whole-archive'])
                    
                    # Add radiation plugin if it exists (WITH OptiX dynamic linking)
                    radiation_lib_path = build_lib_dir / 'libradiation.a'
                    if radiation_lib_path.exists():
                        print(f"Found radiation plugin library: {radiation_lib_path}")
                        print("Note: Adding radiation plugin WITH OptiX dynamic linking")
                        # Use selective linking to avoid doctest symbol conflicts
                        cmd.extend(['-Wl,--whole-archive', str(radiation_lib_path), '-Wl,--no-whole-archive', '-Wl,--allow-multiple-definition'])
                        
                        # Add OptiX DYNAMIC linking (not static) - following RadiationServer approach
                        optix_path = self.get_optix_path()
                        if optix_path:
                            system = platform.system()
                            if system == "Windows":
                                # Windows OptiX import library
                                optix_lib_path = optix_path / 'lib64' / 'optix.6.5.0.lib'
                                optix_lib_alt = optix_path / 'lib64' / 'optix.lib'
                                if optix_lib_path.exists():
                                    optix_lib_to_use = optix_lib_path
                                elif optix_lib_alt.exists():
                                    optix_lib_to_use = optix_lib_alt
                                else:
                                    optix_lib_to_use = None
                            else:
                                # Linux/macOS OptiX library
                                optix_lib_path = optix_path / 'lib64' / 'liboptix.so.6.5.0'
                                optix_lib_alt = optix_path / 'lib64' / 'liboptix.so'
                                if optix_lib_path.exists():
                                    optix_lib_to_use = optix_lib_path
                                elif optix_lib_alt.exists():
                                    optix_lib_to_use = optix_lib_alt
                                else:
                                    optix_lib_to_use = None
                        else:
                            optix_lib_to_use = None

                        if optix_lib_to_use and optix_lib_to_use.exists():
                            print(f"Found OptiX library: {optix_lib_to_use}")
                            print("Adding OptiX shared library to link command")

                            # Add OptiX library directly to link command
                            cmd.append(str(optix_lib_to_use))
                            
                            # Set RPATH so runtime linker can find OptiX library (Unix only)
                            if system != "Windows":
                                cmd.extend([f'-Wl,-rpath,{self.output_dir}'])
                            
                            # Copy OptiX runtime files to plugins directory
                            if system == "Windows":
                                # For Windows, we need to find and copy the DLL (separate from .lib)
                                # OptiX DLLs are typically in system PATH or CUDA installation
                                print("Windows OptiX: .lib file linked, DLL should be in system PATH")
                            else:
                                # Unix systems: copy the shared library
                                optix_dest = self.output_dir / optix_lib_to_use.name
                                shutil.copy2(optix_lib_to_use, optix_dest)
                                print(f"Copied OptiX library to: {optix_dest}")

                                # Also copy the symlink target for Unix systems
                                optix_symlink = optix_path / 'lib64' / 'liboptix.so'
                                if optix_symlink.exists():
                                    optix_symlink_dest = self.output_dir / 'liboptix.so'
                                    shutil.copy2(optix_symlink, optix_symlink_dest)
                                    print(f"Copied OptiX symlink to: {optix_symlink_dest}")
                        else:
                            if optix_path:
                                print(f"OptiX library not found in: {optix_path / 'lib64'}")
                            else:
                                print("No OptiX installation found for this platform")
                        
                        # Add CUDA library paths if CUDA_HOME is set
                        import os
                        if 'CUDA_HOME' in os.environ:
                            cuda_lib_dir = Path(os.environ['CUDA_HOME']) / 'lib64'
                            if cuda_lib_dir.exists():
                                cmd.extend([f'-L{cuda_lib_dir}', '-lcudart_static', '-ldl', '-lrt', '-lpthread'])
                            else:
                                cmd.extend(['-lcudart'])
                        else:
                            cmd.extend(['-lcudart'])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"Successfully converted static to shared library: {output_path}")
                    print(f"All dependencies bundled locally in: {self.output_dir}")
                else:
                    print(f"Linking command failed with return code {result.returncode}")
                    print(f"Command: {' '.join(cmd)}")
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                    raise subprocess.CalledProcessError(result.returncode, cmd)
                
            except subprocess.CalledProcessError as e:
                # FAIL-FAST: Do not silently fall back to broken static library
                error_msg = (
                    f"Failed to convert static library to shared library for ctypes compatibility:\n"
                    f"Command failed: {' '.join(cmd)}\n"
                    f"Error: {e}\n\n"
                    f"CRITICAL: PyHelios requires shared libraries (.dylib) for ctypes loading. "
                    f"Static libraries (.a) cannot be loaded by ctypes on macOS.\n\n"
                    f"Solutions:\n"
                    f"1. Install required dependencies: brew install jpeg libpng\n"
                    f"2. Ensure CMake builds shared libraries: -DBUILD_SHARED_LIBS=ON\n"
                    f"3. Check that build system creates .dylib instead of .a files\n\n"
                    f"This is a build system error, not a runtime warning."
                )
                raise HeliosBuildError(error_msg)
                
        else:
            # Normal case: copy the library directly
            # FAIL-FAST: Ensure we never copy static libraries as final output on macOS/Linux
            if (self.platform_name in ['Darwin', 'Linux'] and 
                library_path.name.endswith('.a')):
                raise HeliosBuildError(
                    f"CRITICAL: Attempting to copy static library as final output: {library_path}\n"
                    f"Static libraries (.a) cannot be loaded by ctypes on {self.platform_name}.\n"
                    f"PyHelios requires shared libraries (.dylib on macOS, .so on Linux).\n\n"
                    f"This indicates a build system error where the shared library conversion failed\n"
                    f"but no error was properly detected. Check the CMake configuration and ensure\n"
                    f"BUILD_SHARED_LIBS=ON is set properly."
                )
            
            output_path = self.output_dir / library_path.name
            shutil.copy2(library_path, output_path)
            print(f"Copied library to: {output_path}")
        
        # Validate that the copied library can be loaded by ctypes (FAIL-FAST validation)
        self._validate_library_loadable(output_path)

        # Also copy any additional required files
        if self.platform_name == 'Windows':
            # Look for PDB files for debugging
            pdb_path = library_path.with_suffix('.pdb')
            if pdb_path.exists():
                shutil.copy2(pdb_path, self.output_dir / pdb_path.name)
                print(f"Copied debug symbols: {pdb_path}")
        
        return output_path

    def _clean_duplicate_symbols(self, main_lib_path: Path, build_lib_dir: Path) -> Dict[str, Any]:
        """
        Clean duplicate symbols from static libraries by removing test objects.
        Uses modern archive manipulation to resolve doctest symbol conflicts.
        
        Args:
            main_lib_path: Path to main libhelios.a library
            build_lib_dir: Directory containing all built libraries
            
        Returns:
            Dict with 'main', 'plugins', and 'dependencies' library paths
        """
        import tempfile
        import shutil
        
        print("Cleaning duplicate symbols from static libraries...")
        
        # Create temporary directory for clean libraries
        temp_dir = Path(tempfile.mkdtemp(prefix='pyhelios_clean_'))
        
        try:
            # Define libraries to process
            plugin_names = ['libvisualizer.a', 'libradiation.a', 'libweberpenntree.a', 
                          'libcanopygenerator.a', 'liblidar.a', 'libsolarposition.a']
            visualizer_deps = ['libfreetype.a', 'libGLEW.a']
            
            # Add PyHelios interface library if it exists
            interface_lib = build_lib_dir / 'libpyhelios_interface.a'
            if interface_lib.exists():
                visualizer_deps.append('libpyhelios_interface.a')
            
            result = {'main': None, 'plugins': [], 'dependencies': [], 'static_libs': []}
            
            # Clean main library (keep doctest symbols here)
            main_clean = temp_dir / 'libhelios_clean.a'
            shutil.copy2(main_lib_path, main_clean)
            result['main'] = main_clean
            print(f"Main library: {main_clean.name}")
            
            # Process plugin libraries (remove doctest symbols from these)
            for plugin_name in plugin_names:
                plugin_lib = build_lib_dir / plugin_name
                if plugin_lib.exists():
                    cleaned_plugin = self._remove_duplicate_objects(plugin_lib, temp_dir)
                    if cleaned_plugin:
                        result['plugins'].append(cleaned_plugin)
                        
                        # Add visualizer dependencies
                        if plugin_name == 'libvisualizer.a':
                            for dep_name in visualizer_deps:
                                dep_lib = build_lib_dir / dep_name
                                if dep_lib.exists():
                                    result['dependencies'].append(dep_lib)
                            
                            # Add GLFW library (built with Helios)
                            # First try static library (preferred for embedding)
                            glfw_static = build_lib_dir / 'libglfw3.a'
                            if glfw_static.exists():
                                result['static_libs'].append(glfw_static)
                                print(f"  Found GLFW static library: {glfw_static.name}")
                            else:
                                # Fall back to shared library if static not available
                                glfw_shared = build_lib_dir / 'libglfw.3.3.dylib'
                                if glfw_shared.exists():
                                    result['dependencies'].append(glfw_shared)
                                    print(f"  Found GLFW shared library: {glfw_shared.name}")
                                else:
                                    # Try alternative GLFW shared library paths
                                    for glfw_name in ['libglfw.dylib', 'libglfw.3.dylib']:
                                        glfw_alt = build_lib_dir / glfw_name
                                        if glfw_alt.exists():
                                            result['dependencies'].append(glfw_alt)
                                            print(f"  Found GLFW shared library: {glfw_alt.name}")
                                            break
            
            return result
            
        except Exception as e:
            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise RuntimeError(f"Failed to clean duplicate symbols: {e}")
    
    def _remove_duplicate_objects(self, library_path: Path, temp_dir: Path) -> Optional[Path]:
        """
        Remove duplicate test objects from a static library.
        
        Args:
            library_path: Path to the static library to clean
            temp_dir: Temporary directory for processing
            
        Returns:
            Path to cleaned library or None if failed
        """
        try:
            lib_name = library_path.stem + '_clean.a'
            cleaned_lib = temp_dir / lib_name
            extract_dir = temp_dir / f'extract_{library_path.stem}'
            extract_dir.mkdir(exist_ok=True)
            
            # Extract all objects from the library
            result = subprocess.run(['ar', 'x', str(library_path)], 
                                  cwd=extract_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Warning: Failed to extract {library_path.name}: {result.stderr}")
                return None
            
            # Remove duplicate test objects (doctest symbols)
            test_objects = list(extract_dir.glob('*selfTest*')) + list(extract_dir.glob('*doctest*'))
            for obj_file in test_objects:
                obj_file.unlink()
                print(f"  Removed duplicate test object: {obj_file.name}")
            
            # Get remaining objects
            remaining_objects = list(extract_dir.glob('*.o'))
            if not remaining_objects:
                print(f"Warning: No objects remaining in {library_path.name} after cleaning")
                return None
            
            # Create cleaned library
            ar_cmd = ['ar', 'rcs', str(cleaned_lib)] + [str(obj) for obj in remaining_objects]
            result = subprocess.run(ar_cmd, capture_output=True, text=True, cwd=extract_dir)
            if result.returncode != 0:
                print(f"Warning: Failed to create cleaned library {lib_name}: {result.stderr}")
                return None
            
            print(f"  Created cleaned library: {lib_name}")
            return cleaned_lib
            
        except Exception as e:
            print(f"Warning: Failed to clean {library_path.name}: {e}")
            return None
    
    def _fix_dylib_dependencies(self, dylib_path: Path) -> None:
        """
        Fix dylib install names to point to local copies.
        
        Args:
            dylib_path: Path to the dylib to fix
        """
        try:
            # Get current dependencies
            result = subprocess.run(['otool', '-L', str(dylib_path)], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Warning: Could not check dependencies of {dylib_path}")
                return
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip first line (the file itself)
            
            for line in lines:
                line = line.strip()
                if '@rpath/libglfw' in line:
                    # Extract the dependency path
                    dep_path = line.split()[0]
                    new_path = f"@loader_path/{Path(dep_path).name}"
                    
                    # Change the install name
                    install_result = subprocess.run([
                        'install_name_tool', '-change', dep_path, new_path, str(dylib_path)
                    ], capture_output=True, text=True)
                    
                    if install_result.returncode == 0:
                        print(f"Fixed dependency: {dep_path} -> {new_path}")
                    else:
                        print(f"Warning: Failed to fix dependency {dep_path}: {install_result.stderr}")
                        
        except Exception as e:
            print(f"Warning: Failed to fix dylib dependencies: {e}")
    
    def copy_ptx_files(self) -> None:
        """Copy OptiX PTX files to PyHelios installation directory."""
        # OptiX looks for PTX files in plugins/radiation/ relative to the working directory
        ptx_source_dir = self.build_dir / 'plugins' / 'radiation'
        if not ptx_source_dir.exists():
            if 'radiation' in self.selected_plugins:
                raise RuntimeError(
                    "CRITICAL: Radiation plugin was requested but OptiX PTX files not found!\n\n"
                    "The radiation plugin requires OptiX for GPU acceleration.\n"
                    "OptiX PTX files should be generated during CMake build.\n\n"
                    "To fix this issue:\n"
                    "1. Ensure CUDA toolkit is properly installed\n"
                    "2. Verify OptiX is available in helios-core/plugins/radiation/lib/OptiX/\n"
                    "3. Check CMake configuration enables OptiX compilation\n"
                    "4. Run build with --clean to rebuild from scratch\n\n"
                    f"Expected PTX directory: {ptx_source_dir}\n"
                    "PyHelios follows fail-fast policy - builds must fail when dependencies are missing."
                )
            else:
                # Radiation plugin not selected - this is expected
                print("Radiation plugin not selected - skipping PTX file copy")
                return

        ptx_files = list(ptx_source_dir.glob('*.ptx'))
        if not ptx_files:
            if 'radiation' in self.selected_plugins:
                raise RuntimeError(
                    "CRITICAL: Radiation plugin build completed but no PTX files generated!\n\n"
                    "This indicates OptiX compilation failed during CMake build.\n"
                    "PTX files are required for GPU-accelerated ray tracing.\n\n"
                    "To fix this issue:\n"
                    "1. Check CMake build logs for OptiX compilation errors\n"
                    "2. Verify CUDA nvcc compiler is available and working\n"
                    "3. Ensure OptiX SDK is properly configured\n"
                    "4. Run build with --verbose to see detailed compilation output\n\n"
                    f"Build directory checked: {ptx_source_dir}\n"
                    "PyHelios follows fail-fast policy - incomplete builds are not acceptable."
                )
            else:
                print("Radiation plugin not selected - no PTX files expected")
                return
            
        # Copy PTX files to PyHelios installation directory
        # RadiationModel will copy them to working directory as needed
        pyhelios_root = self.output_dir.parent.parent
        ptx_dest_dir = pyhelios_root / 'plugins' / 'radiation'
        ptx_dest_dir.mkdir(parents=True, exist_ok=True)
        
        for ptx_file in ptx_files:
            dest_file = ptx_dest_dir / ptx_file.name
            shutil.copy2(ptx_file, dest_file)
            
        print(f"Copied {len(ptx_files)} PTX files to: {ptx_dest_dir}")
        print("RadiationModel will copy these to working directory as needed")
    
    def build(self, cmake_args: Optional[List[str]] = None) -> Path:
        """
        Build Helios library for current platform.
        
        Args:
            cmake_args: Additional CMake arguments
            
        Returns:
            Path to the built library in output directory
        """
        print(f"Building Helios library for {self.platform_name}")
        print(f"Requested plugins: {self.selected_plugins}")
        
        # Resolve plugin dependencies
        final_plugins = self.resolve_plugin_selection()
        
        # Validate plugins exist in helios-core
        self.validate_plugin_availability(final_plugins)
        
        # Generate plugin configuration
        plugin_config_file = self.generate_cmake_plugin_config(final_plugins)
        
        self.check_prerequisites()
        self.setup_build_directory()
        
        # Add plugin configuration to CMake args  
        if cmake_args is None:
            cmake_args = []
        # Use absolute path for plugin config file to avoid path resolution issues
        plugin_config_absolute = str(plugin_config_file.absolute())
        cmake_args.append(f"-DPYHELIOS_PLUGIN_CONFIG={plugin_config_absolute}")
        
        self.run_cmake_configure(cmake_args)
        self.run_cmake_build()
        
        library_path = self.find_built_library()
        output_library = self.copy_to_output(library_path)
        self.copy_ptx_files()
        print(f"Build completed successfully: {output_library}")
        print(f"Built with plugins: {final_plugins}")
        return output_library

    def _patch_zlib_cmake_for_windows(self) -> None:
        """
        Patch zlib's CMakeLists.txt on Windows to disable the shared library target
        that causes resource compilation errors with win32/zlib1.rc.
        """
        zlib_cmake_path = self.helios_root / "core" / "lib" / "zlib" / "CMakeLists.txt"
        
        if not zlib_cmake_path.exists():
            print("Warning: zlib CMakeLists.txt not found, skipping patch")
            return
            
        print("Patching zlib CMakeLists.txt to disable shared library on Windows...")
        
        try:
            # Read the original file
            with open(zlib_cmake_path, 'r') as f:
                content = f.read()
            
            # Check if already patched (to avoid double-patching)
            if "# PYHELIOS PATCH: Disabled shared library" in content:
                print("zlib CMakeLists.txt already patched")
                return
        except Exception as e:
            print(f"Warning: Failed to read zlib CMakeLists.txt: {e}")
            return
            
        # Patch: comment out the shared library creation and related lines
        patches = [
            # Comment out the shared library creation
            ("add_library(zlib SHARED", "# PYHELIOS PATCH: Disabled shared library\n# add_library(zlib SHARED"),
            # Comment out the include directories for shared lib
            ("target_include_directories(zlib PUBLIC", "# target_include_directories(zlib PUBLIC"),
            # Comment out all properties for shared lib
            ("set_target_properties(zlib PROPERTIES DEFINE_SYMBOL ZLIB_DLL)", "# set_target_properties(zlib PROPERTIES DEFINE_SYMBOL ZLIB_DLL)"),
            ("set_target_properties(zlib PROPERTIES SOVERSION 1)", "# set_target_properties(zlib PROPERTIES SOVERSION 1)"),
            ("    set_target_properties(zlib PROPERTIES VERSION ${ZLIB_FULL_VERSION})", "    # set_target_properties(zlib PROPERTIES VERSION ${ZLIB_FULL_VERSION})"),
            ("   set_target_properties(zlib zlibstatic PROPERTIES OUTPUT_NAME z)", "   set_target_properties(zlibstatic PROPERTIES OUTPUT_NAME z)"),
            ("     set_target_properties(zlib PROPERTIES LINK_FLAGS", "     # set_target_properties(zlib PROPERTIES LINK_FLAGS"),
            ("    set_target_properties(zlib PROPERTIES SUFFIX \"1.dll\")", "    # set_target_properties(zlib PROPERTIES SUFFIX \"1.dll\")"),
            # Update install targets to exclude zlib shared library
            ("    install(TARGETS zlib zlibstatic", "    install(TARGETS zlibstatic"),
            # Add static runtime linking for zlib
            ("add_library(zlibstatic STATIC ${ZLIB_SRCS} ${ZLIB_PUBLIC_HDRS} ${ZLIB_PRIVATE_HDRS})", 
             "add_library(zlibstatic STATIC ${ZLIB_SRCS} ${ZLIB_PUBLIC_HDRS} ${ZLIB_PRIVATE_HDRS})\n# PYHELIOS PATCH: Use static MSVC runtime\nif(MSVC)\n    set_target_properties(zlibstatic PROPERTIES MSVC_RUNTIME_LIBRARY \"MultiThreaded$<$<CONFIG:Debug>:Debug>\")\nendif()"),
            # Disable problematic resource compilation
            ("if(NOT MINGW)\n    set(ZLIB_DLL_SRCS\n        win32/zlib1.rc # If present will override custom build rule below.\n    )\nendif()",
             "# PYHELIOS PATCH: Disable resource compilation to avoid RC errors\n# if(NOT MINGW)\n#     set(ZLIB_DLL_SRCS\n#         win32/zlib1.rc # If present will override custom build rule below.\n#     )\n# endif()"),
        ]
        
        for old, new in patches:
            if old in content:
                content = content.replace(old, new)
                print(f"  Patched: {old[:50]}...")
        
        # Write the patched file back
        try:
            with open(zlib_cmake_path, 'w') as f:
                f.write(content)
            print("zlib CMakeLists.txt patched successfully")
        except Exception as e:
            print(f"Warning: Failed to write patched zlib CMakeLists.txt: {e}")
            raise HeliosBuildError(f"Could not patch zlib CMakeLists.txt: {e}")


def get_default_plugins() -> List[str]:
    """
    Get the default set of plugins (only the currently integrated plugins).

    Currently integrated plugins in PyHelios:
    - visualizer: OpenGL-based 3D visualization
    - weberpenntree: Procedural tree generation
    - radiation: OptiX-accelerated ray tracing (GPU optional)
    - energybalance: GPU-accelerated thermal modeling and energy balance
    - solarposition: Solar position calculations and sun angle modeling
    - photosynthesis: Photosynthesis modeling and carbon assimilation
    - plantarchitecture: Advanced plant structure and architecture modeling with procedural plant library

    Returns:
        List of default plugins
    """
    # Return the plugins that are actually integrated into PyHelios
    integrated_plugins = INTEGRATED_PLUGINS
    
    # Filter by platform compatibility
    default_plugins = []
    platform_name = platform.system().lower()
    if platform_name == "darwin":
        platform_name = "macos"
    
    for plugin in integrated_plugins:
        if plugin in PLUGIN_METADATA:
            metadata = PLUGIN_METADATA[plugin]
            if platform_name in metadata.platforms:
                default_plugins.append(plugin)
    
    return sorted(default_plugins)


def parse_plugin_selection(args) -> List[str]:
    """
    Parse plugin selection from command line arguments.
    
    Returns:
        List of plugins to build
    """
    # 1. Start with explicit plugins or default set
    if args.plugins:
        # Handle comma-separated plugin lists within arguments
        selected_plugins = []
        for plugin_arg in args.plugins:
            if ',' in plugin_arg:
                selected_plugins.extend([p.strip() for p in plugin_arg.split(',')])
            else:
                selected_plugins.append(plugin_arg.strip())
    else:
        selected_plugins = get_default_plugins()
    
    # 2. Apply exclusion flags
    if args.nogpu:
        # Remove GPU-dependent plugins
        gpu_plugins = [p for p in selected_plugins 
                      if PLUGIN_METADATA.get(p, PluginMetadata("", "", [], [], [], False, True, [])).gpu_required]
        selected_plugins = [p for p in selected_plugins 
                          if not PLUGIN_METADATA.get(p, PluginMetadata("", "", [], [], [], False, True, [])).gpu_required]
        if gpu_plugins:
            print(f"[EXCLUDED] GPU-dependent plugins excluded (--nogpu): {gpu_plugins}")
    
    if args.novis:
        # Remove visualization plugins
        vis_plugins = [p for p in selected_plugins 
                      if any(dep in ["opengl", "glfw", "imgui"] 
                           for dep in PLUGIN_METADATA.get(p, PluginMetadata("", "", [], [], [], False, True, [])).system_dependencies)]
        selected_plugins = [p for p in selected_plugins 
                          if not any(dep in ["opengl", "glfw", "imgui"] 
                                   for dep in PLUGIN_METADATA.get(p, PluginMetadata("", "", [], [], [], False, True, [])).system_dependencies)]
        if vis_plugins:
            print(f"[EXCLUDED] Visualization plugins excluded (--novis): {vis_plugins}")
    
    # 3. Apply additional exclusions
    if args.exclude:
        excluded_plugins = [p for p in selected_plugins if p in args.exclude]
        selected_plugins = [p for p in selected_plugins if p not in args.exclude]
        if excluded_plugins:
            print(f"[EXCLUDED] Explicitly excluded plugins (--exclude): {excluded_plugins}")
    
    
    # 4. Check environment variables for additional exclusions
    if os.environ.get('PYHELIOS_EXCLUDE_GPU', '').lower() in ['1', 'true', 'yes']:
        env_gpu_plugins = [p for p in selected_plugins 
                          if PLUGIN_METADATA.get(p, PluginMetadata("", "", [], [], [], False, True, [])).gpu_required]
        selected_plugins = [p for p in selected_plugins 
                          if not PLUGIN_METADATA.get(p, PluginMetadata("", "", [], [], [], False, True, [])).gpu_required]
        if env_gpu_plugins:
            print(f"[EXCLUDED] GPU-dependent plugins excluded (PYHELIOS_EXCLUDE_GPU): {env_gpu_plugins}")
    
    # 5. Return final plugin list
    return selected_plugins


def interactive_plugin_selection() -> List[str]:
    """Interactive plugin selection for users."""
    print("\nPyHelios Plugin Selection")
    print("=" * 25)
    
    print("1. Default (all non-GPU, non-visualization plugins)")
    print("2. Include GPU plugins (requires CUDA)")
    print("3. Include visualization plugins (requires OpenGL)")
    print("4. Include all plugins")
    print("5. Custom selection")
    print("6. List all available plugins")
    
    while True:
        try:
            choice = input("\nSelect option [1-6]: ").strip()
            
            if choice == "1":
                return get_default_plugins()
            elif choice == "2":
                plugins = get_default_plugins()
                # Add GPU plugins
                for name, metadata in PLUGIN_METADATA.items():
                    if metadata.gpu_required and name not in plugins:
                        plugins.append(name)
                return sorted(plugins)
            elif choice == "3":
                plugins = get_default_plugins()
                # Add visualization plugins
                for name, metadata in PLUGIN_METADATA.items():
                    if any(dep in ["opengl", "glfw", "imgui"] for dep in metadata.system_dependencies) and name not in plugins:
                        plugins.append(name)
                return sorted(plugins)
            elif choice == "4":
                return sorted(get_platform_compatible_plugins())
            elif choice == "5":
                print("\nEnter plugins separated by commas:")
                print(f"Available: {', '.join(sorted(get_platform_compatible_plugins()))}")
                custom_input = input("Plugins: ").strip()
                return [p.strip() for p in custom_input.split(',') if p.strip()]
            elif choice == "6":
                print("\nAvailable plugins:")
                compatible_plugins = get_platform_compatible_plugins()
                integrated_plugins = INTEGRATED_PLUGINS

                for plugin in sorted(get_all_plugin_names()):
                    metadata = PLUGIN_METADATA[plugin]

                    # Plugin status indicators
                    if plugin not in compatible_plugins:
                        status = "-"  # Platform incompatible
                    elif plugin not in integrated_plugins:
                        status = "?"  # Available in helios-core but not integrated into PyHelios
                    else:
                        status = "+"  # Fully integrated and compatible

                    gpu = " (GPU)" if metadata.gpu_required else ""
                    vis = " (VIS)" if any(dep in ["opengl", "glfw", "imgui"] for dep in metadata.system_dependencies) else ""
                    print(f"  {status} {plugin}{gpu}{vis} - {metadata.description}")
                    if plugin not in integrated_plugins:
                        print(f"      (Available in helios-core but not integrated into PyHelios)")

                print("\nLegend: + Integrated, ? Not integrated, - Incompatible")
                continue
            else:
                print("Invalid choice. Please enter 1-6")
                
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)


def main():
    """Main entry point for build script."""
    parser = argparse.ArgumentParser(
        description="Build Helios C++ libraries for PyHelios with flexible plugin selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Build Examples:
  %(prog)s                                    # Default build (non-GPU, non-vis plugins)
  %(prog)s --plugins radiation,visualizer    # Specific plugins
  %(prog)s --nogpu                          # Exclude GPU plugins
  %(prog)s --novis                          # Exclude visualization plugins
  %(prog)s --buildmode debug                # Debug build
  %(prog)s --interactive                    # Interactive selection
  %(prog)s --list-plugins                   # List available plugins
        """
    )
    
    # Basic options
    parser.add_argument('--helios-root', type=Path, 
                       help='Path to helios-core directory (default: ../helios-core)')
    parser.add_argument('--output-dir', type=Path,
                       help='Output directory for built libraries (default: ../pyhelios/plugins)')
    parser.add_argument('--cmake-args', action='append', default=[],
                       help='Additional CMake arguments (can be specified multiple times)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    # Build configuration
    build_group = parser.add_argument_group('Build Configuration')
    build_group.add_argument('--buildmode', choices=['debug', 'release', 'relwithdebinfo'], 
                            default='release', help='CMake build type (default: release)')
    build_group.add_argument('--clean', action='store_true',
                            help='Clean all build artifacts before building (removes pyhelios_build/, pyhelios/plugins/, pyhelios/assets/build/)')
    build_group.add_argument('--nogpu', action='store_true',
                            help='Exclude GPU-dependent plugins (radiation, energybalance, etc.)')
    build_group.add_argument('--novis', action='store_true', 
                            help='Exclude visualization plugins (visualizer, projectbuilder)')
    
    # Plugin selection options
    plugin_group = parser.add_argument_group('Plugin Selection')
    plugin_group.add_argument('--plugins', nargs='*', metavar='PLUGIN',
                             help='Explicit list of plugins to build')
    plugin_group.add_argument('--exclude', nargs='*', metavar='PLUGIN', default=[],
                             help='Additional plugins to exclude from selection')
    plugin_group.add_argument('--config', type=Path,
                             help='Configuration file (default: pyhelios_config.yaml)')
    plugin_group.add_argument('--interactive', action='store_true',
                             help='Interactive plugin selection')
    
    # Information options
    info_group = parser.add_argument_group('Information')
    info_group.add_argument('--list-plugins', action='store_true',
                           help='List PyHelios integrated plugins and exit')
    info_group.add_argument('--list-all-plugins', action='store_true',
                           help='List all helios-core plugins (including non-integrated) and exit')
    info_group.add_argument('--validate-config', action='store_true',
                           help='Validate configuration without building')
    info_group.add_argument('--discover', action='store_true',
                           help='Discover recommended configuration for this system')
    
    args = parser.parse_args()
    
    # Handle information commands
    if args.list_plugins:
        print("PyHelios Integrated Plugins:")
        print("=" * 30)
        compatible_plugins = get_platform_compatible_plugins()
        integrated_plugins = INTEGRATED_PLUGINS

        for plugin in sorted(integrated_plugins):
            if plugin in PLUGIN_METADATA:
                metadata = PLUGIN_METADATA[plugin]
                status = "+" if plugin in compatible_plugins else "-"
                gpu = " (GPU)" if metadata.gpu_required else ""
                print(f"{status} {plugin}{gpu}")
                print(f"  {metadata.description}")
                if metadata.system_dependencies:
                    print(f"  Dependencies: {', '.join(metadata.system_dependencies)}")
                if plugin not in compatible_plugins:
                    print("  Status: Not supported on this platform")
                print()

        print("Legend:")
        print("  + Available and platform compatible")
        print("  - Not supported on this platform")
        print("\nUse --list-all-plugins to see all helios-core plugins (including non-integrated)")
        return 0

    if args.list_all_plugins:
        print("All Helios-Core Plugins:")
        print("=" * 25)
        compatible_plugins = get_platform_compatible_plugins()
        integrated_plugins = INTEGRATED_PLUGINS

        for plugin in sorted(get_all_plugin_names()):
            metadata = PLUGIN_METADATA[plugin]

            # Plugin status indicators
            if plugin not in compatible_plugins:
                status = "-"  # Platform incompatible
            elif plugin not in integrated_plugins:
                status = "?"  # Available in helios-core but not integrated into PyHelios
            else:
                status = "+"  # Fully integrated and compatible

            gpu = " (GPU)" if metadata.gpu_required else ""
            print(f"{status} {plugin}{gpu}")
            print(f"  {metadata.description}")
            if metadata.system_dependencies:
                print(f"  Dependencies: {', '.join(metadata.system_dependencies)}")
            if plugin not in integrated_plugins:
                print("  Status: Available in helios-core but not yet integrated into PyHelios")
            print()

        print("Legend:")
        print("  + Fully integrated and platform compatible")
        print("  ? Available in helios-core but not integrated into PyHelios")
        print("  - Platform incompatible")
        return 0
    
    if args.discover:
        resolver = PluginDependencyResolver()
        
        # Check GPU availability
        gpu_available = resolver._check_cuda()
        print(f"GPU/CUDA available: {'+' if gpu_available else '-'}")
        
        # Recommend build configuration
        print("\nRecommended build configuration:")
        if gpu_available:
            print("  Build with GPU plugins: build_scripts/build_helios")
        else:
            print("  Build without GPU: build_scripts/build_helios --nogpu")
        
        # Get default plugins and validate
        recommended_plugins = get_default_plugins()
        validation = resolver.validate_configuration(recommended_plugins)
        
        print(f"\nDefault plugins: {recommended_plugins}")
        print(f"Platform compatible: {validation['platform_compatible']}")
        
        if validation['platform_incompatible']:
            print(f"Platform incompatible: {validation['platform_incompatible']}")
        
        if validation['system_dependencies']:
            print("System dependencies:")
            for dep, available in validation['system_dependencies'].items():
                status = "+" if available else "-"
                print(f"  {status} {dep}")
        
        print("\nTo customize:")
        print("  --plugins PLUGIN1,PLUGIN2  # Specific plugins")
        print("  --nogpu                     # Exclude GPU plugins")
        print("  --novis                     # Exclude visualization plugins")
        print("  --buildmode debug           # Debug build")
        
        return 0
    
    # Handle validation command
    if args.validate_config:
        plugins = parse_plugin_selection(args)
        resolver = PluginDependencyResolver()
        validation = resolver.validate_configuration(plugins)
        
        print("Configuration Validation Results:")
        print("=" * 35)
        print(f"Requested plugins: {plugins}")
        print(f"Valid plugins: {validation['valid_plugins']}")
        if validation['invalid_plugins']:
            print(f"[ERROR] Invalid plugins: {validation['invalid_plugins']}")
        print(f"Platform compatible: {validation['platform_compatible']}")
        if validation['platform_incompatible']:
            print(f"[WARN] Platform incompatible: {validation['platform_incompatible']}")
        
        if validation['system_dependencies']:
            print("\nSystem Dependencies:")
            for dep, available in validation['system_dependencies'].items():
                status = "+" if available else "-"
                print(f"  {status} {dep}")
        
        gpu_required = validation['gpu_required']
        print(f"\nGPU required: {'Yes' if gpu_required else 'No'}")
        
        if validation['invalid_plugins'] or (gpu_required and not resolver._check_cuda()):
            print("\n[ERROR] Configuration has issues")
            return 1
        else:
            print("\n[OK] Configuration is valid")
            return 0
    
    # Determine plugin selection
    if args.interactive:
        plugins = interactive_plugin_selection()
        explicitly_requested_plugins = plugins.copy()  # Interactive selections are explicit
    else:
        plugins = parse_plugin_selection(args)
        # Track explicitly requested plugins (from --plugins argument)
        if args.plugins:
            explicitly_requested_plugins = []
            for plugin_arg in args.plugins:
                if ',' in plugin_arg:
                    explicitly_requested_plugins.extend([p.strip() for p in plugin_arg.split(',')])
                else:
                    explicitly_requested_plugins.append(plugin_arg.strip())
        else:
            # FAIL-FAST: Default plugins should be treated as explicitly requested
            # to prevent silent fallbacks when dependencies are missing
            explicitly_requested_plugins = plugins.copy()  # Default plugins are explicitly requested

    # Apply exclusions
    if args.exclude:
        original_count = len(plugins)
        plugins = [p for p in plugins if p not in args.exclude]
        excluded_count = original_count - len(plugins)
        if excluded_count > 0:
            print(f"Excluded {excluded_count} plugins: {args.exclude}")
    
    # Default paths relative to script location
    script_dir = Path(__file__).parent
    if args.helios_root is None:
        args.helios_root = script_dir.parent / 'helios-core'
    if args.output_dir is None:
        # Keep generated libraries in build directory by default
        args.output_dir = script_dir.parent / 'pyhelios_build' / 'build' / 'lib'
    
    try:
        builder = HeliosBuilder(args.helios_root, args.output_dir, plugins, args.buildmode, explicitly_requested_plugins)
        
        # Handle clean option
        if args.clean:
            builder.clean_build_artifacts()
        
        output_library = builder.build(args.cmake_args)
        
        print("\n[OK] Build completed successfully!")
        print(f"Built library: {output_library}")
        print(f"Platform: {platform.system()}")
        
        # Verify the library can be loaded
        try:
            import ctypes
            import os
            
            # For Linux/macOS, set LD_LIBRARY_PATH to include the output directory
            if platform.system() != 'Windows':
                original_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
                if str(args.output_dir) not in original_ld_path:
                    new_ld_path = f"{args.output_dir}:{original_ld_path}" if original_ld_path else str(args.output_dir)
                    os.environ['LD_LIBRARY_PATH'] = new_ld_path
                    print(f"Set LD_LIBRARY_PATH to include: {args.output_dir}")
            
            if platform.system() == 'Windows':
                lib = ctypes.WinDLL(str(output_library))
            else:
                lib = ctypes.CDLL(str(output_library))
            print("[OK] Library can be loaded successfully")
            
            # Note: LD_LIBRARY_PATH setup script no longer needed
            # PyHelios automatically discovers libraries in the build directory
                
        except Exception as e:
            print(f"[WARN] Could not load built library: {e}")
            if platform.system() != 'Windows':
                print("   Try setting LD_LIBRARY_PATH and running again:")
                print(f"   export LD_LIBRARY_PATH=\"{args.output_dir}:$LD_LIBRARY_PATH\"")
                print(f"   python3 -c \"from pyhelios import Context; print('Success!')\"")
        
        return 0
        
    except HeliosBuildError as e:
        print(f"[ERROR] Build failed: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())