"""
Plugin metadata and dependency information for PyHelios.

This module defines metadata for all available Helios plugins including
dependencies, platform support, and hardware requirements.
"""

import platform
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    """Metadata for a Helios plugin."""
    name: str
    description: str
    system_dependencies: List[str]
    plugin_dependencies: List[str]
    platforms: List[str]
    gpu_required: bool
    optional: bool
    test_symbols: List[str]  # Functions to test for plugin availability


# Comprehensive metadata for all available Helios plugins
PLUGIN_METADATA: Dict[str, PluginMetadata] = {
    "weberpenntree": PluginMetadata(
        name="weberpenntree",
        description="Procedural tree generation using Weber-Penn algorithms",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=False,
        test_symbols=["buildTree", "setTreeParameters"]
    ),
    
    "canopygenerator": PluginMetadata(
        name="canopygenerator",
        description="Plant canopy generation for various species",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=False,
        test_symbols=["generateCanopy", "setCanopyParameters"]
    ),
    
    "radiation": PluginMetadata(
        name="radiation",
        description="GPU-accelerated ray tracing and radiation modeling using OptiX",
        system_dependencies=["cuda", "optix"],
        plugin_dependencies=[],
        platforms=["windows", "linux"],  # Limited macOS support
        gpu_required=True,
        optional=True,
        test_symbols=["createRadiationModel", "runRadiationModel"]
    ),
    
    "visualizer": PluginMetadata(
        name="visualizer",
        description="OpenGL-based 3D visualization and rendering",
        system_dependencies=["opengl"],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["validateTextureFile", "_ZN10Visualizer10initializeEjjibb"]
    ),
    
    "lidar": PluginMetadata(
        name="lidar",
        description="LiDAR simulation and point cloud processing",
        system_dependencies=["cuda"],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=True,
        optional=True,
        test_symbols=["runLiDARscan", "setLiDARparameters"]
    ),
    
    "aeriallidar": PluginMetadata(
        name="aeriallidar",
        description="Aerial LiDAR simulation with optional GPU acceleration",
        system_dependencies=["cuda"],
        plugin_dependencies=["lidar"],
        platforms=["windows", "linux"],
        gpu_required=True,
        optional=True,
        test_symbols=["runAerialLiDARscan", "setAerialLiDARparameters"]
    ),
    
    "energybalance": PluginMetadata(
        name="energybalance",
        description="Plant energy balance calculations and thermal modeling with optional GPU acceleration",
        system_dependencies=[],  # CUDA is optional - uses three-tier execution: GPU (CUDA), OpenMP (parallel CPU), or serial CPU
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],  # Now supports all platforms with CPU fallback
        gpu_required=False,  # GPU acceleration is optional
        optional=True,
        test_symbols=["createEnergyBalanceModel", "runEnergyBalance"]
    ),
    
    "photosynthesis": PluginMetadata(
        name="photosynthesis",
        description="Photosynthesis modeling and carbon assimilation",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["runPhotosynthesisModel", "setPhotosynthesisParameters"]
    ),
    
    "leafoptics": PluginMetadata(
        name="leafoptics",
        description="Leaf optical properties modeling using PROSPECT model",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["createLeafOptics", "destroyLeafOptics"]
    ),
    
    "stomatalconductance": PluginMetadata(
        name="stomatalconductance",
        description="Stomatal conductance modeling and gas exchange",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["createStomatalConductanceModel", "runStomatalConductanceModel"]
    ),
    
    "boundarylayerconductance": PluginMetadata(
        name="boundarylayerconductance",
        description="Boundary layer conductance modeling for heat and mass transfer",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["createBoundaryLayerConductanceModel", "runBoundaryLayerModel", "setBoundaryLayerModel"]
    ),
    
    "plantarchitecture": PluginMetadata(
        name="plantarchitecture",
        description="Advanced plant structure and architecture modeling with procedural plant library",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["createPlantArchitecture", "loadPlantModelFromLibrary", "buildPlantInstanceFromLibrary"]
    ),
    
    "planthydraulics": PluginMetadata(
        name="planthydraulics",
        description="Plant hydraulic modeling and water transport",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["runPlantHydraulicsModel", "setHydraulicsParameters"]
    ),
    
    "solarposition": PluginMetadata(
        name="solarposition",
        description="Solar position calculations and sun angle modeling",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["createSolarPosition", "getSunElevation", "getSolarFlux"]
    ),
    
    "syntheticannotation": PluginMetadata(
        name="syntheticannotation",
        description="Synthetic data annotation for machine learning applications",
        system_dependencies=[],
        plugin_dependencies=["visualizer"],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["generateAnnotations", "setAnnotationParameters"]
    ),
    
    "parameteroptimization": PluginMetadata(
        name="parameteroptimization",
        description="Parameter optimization algorithms for model calibration",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=False,
        optional=True,
        test_symbols=["runOptimization", "setOptimizationParameters"]
    ),
    
    "voxelintersection": PluginMetadata(
        name="voxelintersection",
        description="Voxel intersection operations and spatial analysis",
        system_dependencies=["cuda"],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=True,
        optional=True,
        test_symbols=["calculateVoxelIntersection", "setVoxelParameters"]
    ),
    
    "collisiondetection": PluginMetadata(
        name="collisiondetection",
        description="Collision detection with optional GPU acceleration",
        system_dependencies=[],
        plugin_dependencies=[],
        platforms=["windows", "linux"],
        gpu_required=False,
        optional=True,
        test_symbols=["runCollisionDetection", "setCollisionParameters"]
    ),
    
    "projectbuilder": PluginMetadata(
        name="projectbuilder",
        description="GUI project builder with ImGui interface",
        system_dependencies=["imgui", "opengl", "cuda"],
        plugin_dependencies=[],
        platforms=["windows", "linux", "macos"],
        gpu_required=True,
        optional=True,
        test_symbols=["initializeProjectBuilder", "runProjectBuilder"]
    )
}


def get_plugin_metadata(plugin_name: str) -> Optional[PluginMetadata]:
    """Get metadata for a specific plugin."""
    return PLUGIN_METADATA.get(plugin_name)


def get_all_plugin_names() -> List[str]:
    """Get list of all available plugin names."""
    return list(PLUGIN_METADATA.keys())




def get_platform_compatible_plugins() -> List[str]:
    """Get plugins compatible with the current platform."""
    current_platform = platform.system().lower()
    platform_map = {
        "windows": "windows",
        "linux": "linux", 
        "darwin": "macos"
    }
    
    mapped_platform = platform_map.get(current_platform, current_platform)
    
    compatible_plugins = []
    for name, metadata in PLUGIN_METADATA.items():
        if mapped_platform in metadata.platforms:
            compatible_plugins.append(name)
    
    return compatible_plugins


def get_gpu_dependent_plugins() -> List[str]:
    """Get plugins that require GPU support."""
    return [name for name, metadata in PLUGIN_METADATA.items() if metadata.gpu_required]


def get_core_plugins() -> List[str]:
    """Get core plugins that are typically always included."""
    return [name for name, metadata in PLUGIN_METADATA.items() if not metadata.optional]