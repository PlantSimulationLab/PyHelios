"""
Plugin dependency resolution for PyHelios.

This module handles automatic resolution of plugin dependencies, system requirements
validation, and conflict detection to ensure compatible plugin combinations.
"""

import glob
import os
import platform
import shutil
import subprocess
import sys
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .plugin_metadata import PLUGIN_METADATA, PluginMetadata, get_platform_compatible_plugins


class ResolutionStatus(Enum):
    """Status of dependency resolution."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ResolutionResult:
    """Result of plugin dependency resolution."""
    status: ResolutionStatus
    final_plugins: List[str]
    added_plugins: List[str]
    removed_plugins: List[str]
    warnings: List[str]
    errors: List[str]
    system_check_results: Dict[str, bool]


class PluginDependencyResolver:
    """Resolves plugin dependencies and validates system requirements."""
    
    def __init__(self):
        self.platform_plugins = get_platform_compatible_plugins()
    
    def resolve_dependencies(self, requested_plugins: List[str],
                           include_optional: bool = True,
                           strict_mode: bool = False,
                           explicitly_requested: Optional[List[str]] = None) -> ResolutionResult:
        """
        Resolve plugin dependencies and conflicts.

        Args:
            requested_plugins: List of requested plugin names
            include_optional: Whether to include optional dependencies
            strict_mode: If True, fail on any missing dependencies
            explicitly_requested: List of plugins explicitly requested by user (treated as required)

        Returns:
            ResolutionResult with final plugin list and any issues
        """
        result = ResolutionResult(
            status=ResolutionStatus.SUCCESS,
            final_plugins=[],
            added_plugins=[],
            removed_plugins=[],
            warnings=[],
            errors=[],
            system_check_results={}
        )

        # Initialize explicitly requested plugins list
        if explicitly_requested is None:
            explicitly_requested = []
        
        # Validate requested plugins exist
        valid_plugins, invalid_plugins = self._validate_plugins(requested_plugins)
        if invalid_plugins:
            result.errors.extend([f"Unknown plugin: {p}" for p in invalid_plugins])
            if strict_mode:
                result.status = ResolutionStatus.ERROR
                return result
        
        # Filter by platform compatibility
        platform_compatible = [p for p in valid_plugins if p in self.platform_plugins]
        platform_incompatible = [p for p in valid_plugins if p not in self.platform_plugins]
        
        if platform_incompatible:
            result.removed_plugins.extend(platform_incompatible)
            result.warnings.extend([
                f"Plugin '{p}' not supported on {platform.system()}" 
                for p in platform_incompatible
            ])
        
        # Add plugin dependencies
        final_plugins = set(platform_compatible)
        for plugin in platform_compatible:
            deps = self._get_plugin_dependencies(plugin)
            new_deps = [d for d in deps if d not in final_plugins]
            final_plugins.update(deps)
            result.added_plugins.extend(new_deps)
        
        # Validate system dependencies
        system_results = self._check_system_dependencies(list(final_plugins))
        result.system_check_results = system_results
        
        # Handle plugins with failed system dependencies according to fail-fast philosophy
        failed_plugins = []
        for plugin in list(final_plugins):
            plugin_metadata = PLUGIN_METADATA[plugin]
            for sys_dep in plugin_metadata.system_dependencies:
                if not system_results.get(sys_dep, False):
                    failed_plugins.append(plugin)

                    # FAIL-FAST: Non-optional plugins OR explicitly requested plugins MUST cause build failure
                    is_explicitly_requested = plugin in explicitly_requested
                    if not plugin_metadata.optional or strict_mode or is_explicitly_requested:
                        error_msg = self._get_dependency_error_message(plugin, sys_dep, is_explicitly_requested)
                        result.errors.append(error_msg)
                    else:
                        # Optional plugins can be gracefully excluded with user awareness
                        warning_msg = self._get_dependency_warning_message(plugin, sys_dep)
                        result.warnings.append(warning_msg)
                    break

        # Remove failed plugins from final list
        final_plugins -= set(failed_plugins)
        result.removed_plugins.extend(failed_plugins)
        
        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(list(final_plugins))
        if circular_deps:
            result.warnings.append(f"Circular dependencies detected: {circular_deps}")
        
        result.final_plugins = sorted(list(final_plugins))
        
        # Set overall status
        if result.errors:
            result.status = ResolutionStatus.ERROR
        elif result.warnings:
            result.status = ResolutionStatus.WARNING
            
        return result
    
    def _validate_plugins(self, plugins: List[str]) -> Tuple[List[str], List[str]]:
        """Separate valid and invalid plugin names."""
        valid = [p for p in plugins if p in PLUGIN_METADATA]
        invalid = [p for p in plugins if p not in PLUGIN_METADATA]
        return valid, invalid
    
    def _get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """Get all dependencies for a plugin recursively."""
        if plugin_name not in PLUGIN_METADATA:
            return []
        
        metadata = PLUGIN_METADATA[plugin_name]
        dependencies = set(metadata.plugin_dependencies)
        
        # Recursively add dependencies of dependencies
        for dep in metadata.plugin_dependencies:
            if dep in PLUGIN_METADATA:
                sub_deps = self._get_plugin_dependencies(dep)
                dependencies.update(sub_deps)
        
        return list(dependencies)
    
    def _detect_circular_dependencies(self, plugins: List[str]) -> List[str]:
        """Detect circular dependencies in plugin list."""
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(plugin: str) -> bool:
            if plugin in rec_stack:
                return True
            if plugin in visited:
                return False
            
            visited.add(plugin)
            rec_stack.add(plugin)
            
            if plugin in PLUGIN_METADATA:
                for dep in PLUGIN_METADATA[plugin].plugin_dependencies:
                    if dep in plugins and has_cycle(dep):
                        return True
            
            rec_stack.remove(plugin)
            return False
        
        circular = []
        for plugin in plugins:
            if plugin not in visited and has_cycle(plugin):
                circular.append(plugin)
        
        return circular
    
    def _check_system_dependencies(self, plugins: List[str]) -> Dict[str, bool]:
        """Check availability of system dependencies."""
        all_deps = set()
        for plugin in plugins:
            if plugin in PLUGIN_METADATA:
                all_deps.update(PLUGIN_METADATA[plugin].system_dependencies)
        
        results = {}
        for dep in all_deps:
            results[dep] = self._check_system_dependency(dep)
        
        return results
    
    def _check_system_dependency(self, dependency: str) -> bool:
        """Check if a specific system dependency is available."""
        checkers = {
            "cuda": self._check_cuda,
            "optix": self._check_optix,
            "opengl": self._check_opengl,
            "glfw": self._check_glfw,
            "glew": self._check_glew,
            "freetype": self._check_freetype,
            "imgui": self._check_imgui,
            "x11": self._check_x11
        }
        
        checker = checkers.get(dependency)
        if checker:
            try:
                return checker()
            except Exception:
                return False
        
        # For unknown dependencies, assume available
        return True
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available."""
        import os

        # First try nvcc command (most reliable when available)
        try:
            result = subprocess.run(["nvcc", "--version"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

        # Fallback: Check for CUDA libraries and headers in common locations
        # Check CUDA environment variables first (set by CI and most installations)
        cuda_env_vars = ["CUDA_PATH", "CUDA_HOME", "CUDA_ROOT", "CUDAHOME"]
        for env_var in cuda_env_vars:
            cuda_path = os.environ.get(env_var)
            if cuda_path and os.path.exists(cuda_path):
                # Verify it's a real CUDA installation by checking for nvcc
                nvcc_name = "nvcc.exe" if platform.system() == "Windows" else "nvcc"
                nvcc_path = os.path.join(cuda_path, "bin", nvcc_name)
                if os.path.exists(nvcc_path):
                    return True

        # Fallback: Check standard installation paths
        cuda_paths = [
            "/usr/local/cuda",
            "/opt/cuda",
            "/usr/lib/x86_64-linux-gnu",
            "/usr/lib64",
            # Windows CI installs CUDA 12.6, so check current and recent versions
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.6",
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.5",
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.4",
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.3",
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.2",
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.1",
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.0",
            "/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8"
        ]

        for cuda_path in cuda_paths:
            # Check for CUDA runtime library
            if platform.system() == "Windows":
                lib_patterns = ["cudart64*.lib", "cudart*.lib", "cudart64*.dll", "cudart*.dll"]
                lib_dirs = [os.path.join(cuda_path, "lib", "x64"), os.path.join(cuda_path, "bin")]
            else:
                lib_patterns = ["libcudart.so*", "libcuda.so*"]
                lib_dirs = [os.path.join(cuda_path, "lib64"), os.path.join(cuda_path, "lib"), cuda_path]

            for lib_dir in lib_dirs:
                if os.path.exists(lib_dir):
                    for pattern in lib_patterns:
                        matches = glob.glob(os.path.join(lib_dir, pattern))
                        if matches:
                            return True

        return False
    
    def _check_optix(self) -> bool:
        """Check if OptiX is available."""
        # OptiX is typically bundled with PyHelios, so check for CUDA instead
        return self._check_cuda()
    
    def _check_opengl(self) -> bool:
        """Check if OpenGL is available."""
        system = platform.system()
        if system == "Windows":
            # OpenGL is typically available on Windows
            return True
        elif system == "Darwin":  # macOS
            # OpenGL is available on macOS
            return True
        else:  # Linux
            # First try utility commands if available
            if (shutil.which("glxinfo") is not None or
                any(shutil.which(cmd) for cmd in ["nvidia-smi", "amdgpu-pro-info"])):
                return True

            # Fallback: Check for OpenGL libraries directly
            opengl_lib_paths = [
                "/usr/lib/x86_64-linux-gnu",
                "/usr/lib64",
                "/usr/lib",
                "/lib/x86_64-linux-gnu",
                "/lib64",
                "/lib"
            ]

            opengl_libs = ["libGL.so*", "libOpenGL.so*", "libEGL.so*"]

            for lib_path in opengl_lib_paths:
                if os.path.exists(lib_path):
                    for lib_pattern in opengl_libs:
                        if glob.glob(os.path.join(lib_path, lib_pattern)):
                            return True

            # Also check for Mesa development headers (indicates OpenGL dev environment)
            header_paths = [
                "/usr/include/GL/gl.h",
                "/usr/include/GL/glx.h",
                "/usr/include/EGL/egl.h"
            ]

            for header_path in header_paths:
                if os.path.exists(header_path):
                    return True

            return False
    
    def _check_glfw(self) -> bool:
        """Check if GLFW is available."""
        # GLFW is typically built as part of the project
        return True
    
    def _check_glew(self) -> bool:
        """Check if GLEW is available."""
        # GLEW is typically built as part of the project
        return True
    
    def _check_freetype(self) -> bool:
        """Check if FreeType is available."""
        # Check for system FreeType first
        if shutil.which("freetype-config") is not None:
            return True
        
        # Check for bundled FreeType in visualizer plugin
        try:
            import os
            # Try multiple possible locations for the FreeType bundle
            possible_paths = [
                # From dependency_resolver.py location
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "helios-core", "plugins", "visualizer", "lib", "freetype-2.7"),
                # From build script working directory
                os.path.join(os.getcwd(), "helios-core", "plugins", "visualizer", "lib", "freetype-2.7"),
                # From PyHelios project root
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "helios-core", "plugins", "visualizer", "lib", "freetype-2.7")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return True
            
            return False
        except Exception:
            return False
    
    def _check_imgui(self) -> bool:
        """Check if ImGui is available."""
        # ImGui is typically built as part of the project
        return True
    
    def _check_x11(self) -> bool:
        """Check if X11 is available (Linux only)."""
        if platform.system() != "Linux":
            return True  # Not required on other platforms
        
        x11_paths = ["/usr/lib/x86_64-linux-gnu/libX11.so", 
                    "/usr/lib/libX11.so", 
                    "/usr/local/lib/libX11.so"]
        return any(os.path.exists(path) for path in x11_paths)
    
    def suggest_alternatives(self, failed_plugins: List[str]) -> List[str]:
        """Suggest alternative plugins when some fail to load."""
        suggestions = []
        
        # Alternative suggestions based on failed plugins
        alternatives = {
            "radiation": ["energybalance", "leafoptics"],
            "visualizer": ["syntheticannotation"],
            "aeriallidar": ["lidar"],
            "collisiondetection": ["voxelintersection"],
            "projectbuilder": []
        }
        
        for failed in failed_plugins:
            if failed in alternatives:
                suggestions.extend(alternatives[failed])
        
        # Remove duplicates and already requested plugins
        suggestions = list(set(suggestions))
        return suggestions
    
    def get_dependency_graph(self, plugins: List[str]) -> Dict[str, List[str]]:
        """Build dependency graph for visualization/debugging."""
        graph = {}
        for plugin in plugins:
            if plugin in PLUGIN_METADATA:
                graph[plugin] = PLUGIN_METADATA[plugin].plugin_dependencies
            else:
                graph[plugin] = []
        return graph
    
    def validate_configuration(self, plugins: List[str]) -> Dict[str, any]:
        """Comprehensive validation of plugin configuration."""
        valid, invalid = self._validate_plugins(plugins)
        platform_compatible = [p for p in valid if p in self.platform_plugins]
        system_deps = self._check_system_dependencies(platform_compatible)
        
        return {
            "valid_plugins": valid,
            "invalid_plugins": invalid,
            "platform_compatible": platform_compatible,
            "platform_incompatible": [p for p in valid if p not in platform_compatible],
            "system_dependencies": system_deps,
            "gpu_required": any(PLUGIN_METADATA[p].gpu_required for p in platform_compatible),
            "total_requested": len(plugins),
            "total_valid": len(valid)
        }

    def _get_dependency_error_message(self, plugin: str, dependency: str, explicitly_requested: bool = False) -> str:
        """Generate clear, actionable error message for missing required dependencies."""
        plugin_metadata = PLUGIN_METADATA[plugin]

        if explicitly_requested:
            error_msg = f"CRITICAL: Explicitly requested plugin '{plugin}' cannot be built due to missing system dependency '{dependency}'"
        else:
            error_msg = f"CRITICAL: Required plugin '{plugin}' cannot be built due to missing system dependency '{dependency}'"

        # Provide specific installation instructions based on dependency and platform
        system = platform.system()
        if dependency == "opengl":
            if system == "Linux":
                error_msg += (
                    f"\n\nOpenGL is required for the visualizer plugin on Linux.\n"
                    f"Install OpenGL development libraries:\n"
                    f"  Ubuntu/Debian: sudo apt-get install libgl1-mesa-dev libglu1-mesa-dev\n"
                    f"  CentOS/RHEL:   sudo yum install mesa-libGL-devel mesa-libGLU-devel\n"
                    f"  Fedora:        sudo dnf install mesa-libGL-devel mesa-libGLU-devel\n\n"
                    f"Alternatively, you can:\n"
                    f"1. Use --exclude visualizer to build without visualization\n"
                    f"2. Install graphics drivers that include OpenGL support\n"
                    f"3. Set up a virtual display with software rendering (for headless systems)"
                )
            elif system == "Darwin":  # macOS
                error_msg += (
                    f"\n\nOpenGL should be available on macOS by default.\n"
                    f"This error may indicate:\n"
                    f"1. Xcode Command Line Tools not installed: xcode-select --install\n"
                    f"2. macOS version too old (requires macOS 10.12+)\n"
                    f"3. Graphics driver issues"
                )
            else:  # Windows
                error_msg += (
                    f"\n\nOpenGL should be available on Windows by default.\n"
                    f"This error may indicate graphics driver issues.\n"
                    f"Update your graphics drivers from your GPU manufacturer."
                )

        elif dependency == "cuda":
            error_msg += (
                f"\n\nCUDA is required for GPU-accelerated functionality.\n"
                f"Install NVIDIA CUDA Toolkit:\n"
                f"1. Download from https://developer.nvidia.com/cuda-downloads\n"
                f"2. Ensure compatible NVIDIA GPU (Compute Capability 3.5+)\n"
                f"3. Verify installation: nvcc --version\n\n"
                f"Alternatively, exclude GPU plugins with --nogpu flag."
            )

        elif dependency == "optix":
            error_msg += (
                f"\n\nOptiX is required for advanced ray tracing functionality.\n"
                f"OptiX requires CUDA and compatible NVIDIA GPU.\n"
                f"OptiX SDK is typically bundled with PyHelios builds.\n"
                f"Ensure CUDA is properly installed first."
            )

        if explicitly_requested:
            error_msg += f"\n\nPlugin '{plugin}' was explicitly requested and cannot be excluded."
            error_msg += f"\nBuild cannot proceed without this plugin. Use --exclude {plugin} to build without it."
        else:
            error_msg += f"\n\nPlugin '{plugin}' is marked as required (optional=False) and cannot be excluded."
            error_msg += f"\nBuild cannot proceed without this plugin."

        return error_msg

    def _get_dependency_warning_message(self, plugin: str, dependency: str) -> str:
        """Generate informative warning message for missing optional dependencies."""
        return (
            f"Optional plugin '{plugin}' disabled: missing system dependency '{dependency}'. "
            f"Install {dependency} to enable this plugin, or continue without it."
        )