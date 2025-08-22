"""
High-level RadiationModel interface for PyHelios.

This module provides a user-friendly interface to the radiation modeling
capabilities with graceful plugin handling and informative error messages.
"""

import logging
from typing import List, Optional
from contextlib import contextmanager
from pathlib import Path
import os

from .plugins.registry import get_plugin_registry, require_plugin, graceful_plugin_fallback
from .wrappers import URadiationModelWrapper as radiation_wrapper
from .Context import Context

logger = logging.getLogger(__name__)


@contextmanager
def _radiation_working_directory():
    """
    Context manager that temporarily changes working directory to where RadiationModel assets are located.
    
    RadiationModel C++ code uses hardcoded relative paths like "plugins/radiation/cuda_compile_ptx_generated_rayGeneration.cu.ptx"
    expecting assets relative to working directory. This manager temporarily changes to the build directory
    where assets are actually located.
    
    Raises:
        RuntimeError: If build directory or RadiationModel assets are not found, indicating a build system error.
    """
    # Find the build directory containing RadiationModel assets
    current_dir = Path(__file__).parent
    repo_root = current_dir.parent
    build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
    working_dir = build_lib_dir.parent
    radiation_assets = working_dir / 'plugins' / 'radiation'
    
    # Validate that build directory and assets exist - fail fast if not
    if not build_lib_dir.exists():
        raise RuntimeError(
            f"PyHelios build directory not found at {build_lib_dir}. "
            f"Run: python build_scripts/build_helios.py --plugins radiation"
        )
    
    if not radiation_assets.exists():
        raise RuntimeError(
            f"RadiationModel assets not found at {radiation_assets}. "
            f"This indicates a build system error. The build script should copy PTX files to this location."
        )
    
    # Change to the build directory temporarily
    original_dir = os.getcwd()
    try:
        os.chdir(working_dir)
        logger.debug(f"Changed working directory to {working_dir} for RadiationModel asset access")
        yield working_dir
    finally:
        os.chdir(original_dir)
        logger.debug(f"Restored working directory to {original_dir}")


class RadiationModelError(Exception):
    """Raised when RadiationModel operations fail."""
    pass


class RadiationModel:
    """
    High-level interface for radiation modeling and ray tracing.
    
    This class provides a user-friendly wrapper around the native Helios
    radiation plugin with automatic plugin availability checking and
    graceful error handling.
    """
    
    def __init__(self, context: Context):
        """
        Initialize RadiationModel with graceful plugin handling.
        
        Args:
            context: Helios Context instance
            
        Raises:
            TypeError: If context is not a Context instance
            RadiationModelError: If radiation plugin is not available
        """
        # Validate context type
        if not isinstance(context, Context):
            raise TypeError(f"RadiationModel requires a Context instance, got {type(context).__name__}")
        
        self.context = context
        self.radiation_model = None
        
        # Check plugin availability using registry
        registry = get_plugin_registry()
        
        if not registry.is_plugin_available('radiation'):
            # Get helpful information about the missing plugin
            plugin_info = registry.get_plugin_capabilities()
            available_plugins = registry.get_available_plugins()
            
            error_msg = (
                "RadiationModel requires the 'radiation' plugin which is not available.\n\n"
                "The radiation plugin provides GPU-accelerated ray tracing using OptiX.\n"
                "System requirements:\n"
                "- NVIDIA GPU with CUDA support\n"
                "- CUDA Toolkit installed\n"
                "- OptiX runtime (bundled with PyHelios)\n\n"
                "To enable radiation modeling:\n"
                "1. Build PyHelios with radiation plugin:\n"
                "   build_scripts/build_helios --plugins radiation\n"
                "2. Or use a profile that includes radiation:\n"
                "   build_scripts/build_helios --profile gpu-accelerated\n"
                f"\nCurrently available plugins: {available_plugins}"
            )
            
            # Suggest alternatives if available
            alternatives = registry.suggest_alternatives('radiation')
            if alternatives:
                error_msg += f"\n\nAlternative plugins available: {alternatives}"
                error_msg += "\nConsider using energybalance or leafoptics for thermal modeling."
            
            raise RadiationModelError(error_msg)
        
        # Plugin is available - create radiation model using working directory context manager
        try:
            with _radiation_working_directory():
                self.radiation_model = radiation_wrapper.createRadiationModel(context.getNativePtr())
                if self.radiation_model is None:
                    raise RadiationModelError(
                        "Failed to create RadiationModel instance. "
                        "This may indicate a problem with the native library or GPU initialization."
                    )
            logger.info("RadiationModel created successfully")
            
        except Exception as e:
            raise RadiationModelError(f"Failed to initialize RadiationModel: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with proper cleanup."""
        if self.radiation_model is not None:
            try:
                radiation_wrapper.destroyRadiationModel(self.radiation_model)
                logger.debug("RadiationModel destroyed successfully")
            except Exception as e:
                logger.warning(f"Error destroying RadiationModel: {e}")
    
    def get_native_ptr(self):
        """Get native pointer for advanced operations."""
        return self.radiation_model
    
    def getNativePtr(self):
        """Get native pointer for advanced operations. (Legacy naming for compatibility)"""
        return self.get_native_ptr()
    
    @require_plugin('radiation', 'disable status messages')
    def disableMessages(self):
        """Disable RadiationModel status messages."""
        radiation_wrapper.disableMessages(self.radiation_model)
    
    @require_plugin('radiation', 'enable status messages')
    def enableMessages(self):
        """Enable RadiationModel status messages."""
        radiation_wrapper.enableMessages(self.radiation_model)
    
    @require_plugin('radiation', 'add radiation band')
    def addRadiationBand(self, band_label: str, wavelength_min: float = None, wavelength_max: float = None):
        """
        Add radiation band with optional wavelength bounds.
        
        Args:
            band_label: Name/label for the radiation band
            wavelength_min: Optional minimum wavelength (μm)
            wavelength_max: Optional maximum wavelength (μm)
        """
        if wavelength_min is not None and wavelength_max is not None:
            radiation_wrapper.addRadiationBandWithWavelengths(self.radiation_model, band_label, wavelength_min, wavelength_max)
            logger.debug(f"Added radiation band {band_label}: {wavelength_min}-{wavelength_max} μm")
        else:
            radiation_wrapper.addRadiationBand(self.radiation_model, band_label)
            logger.debug(f"Added radiation band: {band_label}")
    
    @require_plugin('radiation', 'copy radiation band')
    def copyRadiationBand(self, old_label: str, new_label: str):
        """
        Copy existing radiation band to new label.
        
        Args:
            old_label: Existing band label to copy
            new_label: New label for the copied band
        """
        radiation_wrapper.copyRadiationBand(self.radiation_model, old_label, new_label)
        logger.debug(f"Copied radiation band {old_label} to {new_label}")
    
    @require_plugin('radiation', 'add radiation source')
    def addCollimatedRadiationSource(self, direction=None) -> int:
        """
        Add collimated radiation source.
        
        Args:
            direction: Optional direction vector. Can be tuple (x, y, z), vec3, or None for default direction.
            
        Returns:
            Source ID
        """
        if direction is None:
            source_id = radiation_wrapper.addCollimatedRadiationSourceDefault(self.radiation_model)
        else:
            # Handle vec3, SphericalCoord, and tuple types
            if hasattr(direction, 'x') and hasattr(direction, 'y') and hasattr(direction, 'z'):
                # vec3-like object
                x, y, z = direction.x, direction.y, direction.z
            elif hasattr(direction, 'radius') and hasattr(direction, 'elevation') and hasattr(direction, 'azimuth'):
                # SphericalCoord object - convert to Cartesian
                import math
                r = direction.radius
                elevation = direction.elevation
                azimuth = direction.azimuth
                x = r * math.cos(elevation) * math.cos(azimuth)
                y = r * math.cos(elevation) * math.sin(azimuth)
                z = r * math.sin(elevation)
            else:
                # Assume tuple-like object - validate it first
                try:
                    if len(direction) != 3:
                        raise TypeError(f"Direction must be a 3-element tuple, vec3, or SphericalCoord, got {type(direction).__name__} with {len(direction)} elements")
                    x, y, z = direction
                except (TypeError, AttributeError):
                    # Not a valid sequence type
                    raise TypeError(f"Direction must be a tuple, vec3, or SphericalCoord, got {type(direction).__name__}")
            source_id = radiation_wrapper.addCollimatedRadiationSourceVec3(self.radiation_model, x, y, z)
        
        logger.debug(f"Added collimated radiation source: ID {source_id}")
        return source_id
    
    @require_plugin('radiation', 'add spherical radiation source')
    def addSphereRadiationSource(self, position, radius: float) -> int:
        """
        Add spherical radiation source.
        
        Args:
            position: Position of the source. Can be tuple (x, y, z) or vec3.
            radius: Radius of the spherical source
            
        Returns:
            Source ID
        """
        # Handle both tuple and vec3 types
        if hasattr(position, 'x') and hasattr(position, 'y') and hasattr(position, 'z'):
            # vec3-like object
            x, y, z = position.x, position.y, position.z
        else:
            # Assume tuple-like object
            x, y, z = position
        source_id = radiation_wrapper.addSphereRadiationSource(self.radiation_model, x, y, z, radius)
        logger.debug(f"Added sphere radiation source: ID {source_id} at ({x}, {y}, {z}) with radius {radius}")
        return source_id
    
    @require_plugin('radiation', 'add sun radiation source')
    def addSunSphereRadiationSource(self, radius: float, zenith: float, azimuth: float,
                                    position_scaling: float = 1.0, angular_width: float = 0.53,
                                    flux_scaling: float = 1.0) -> int:
        """
        Add sun sphere radiation source.
        
        Args:
            radius: Radius of the sun sphere
            zenith: Zenith angle (degrees)
            azimuth: Azimuth angle (degrees)
            position_scaling: Position scaling factor
            angular_width: Angular width of the sun (degrees)
            flux_scaling: Flux scaling factor
            
        Returns:
            Source ID
        """
        source_id = radiation_wrapper.addSunSphereRadiationSource(
            self.radiation_model, radius, zenith, azimuth, position_scaling, angular_width, flux_scaling
        )
        logger.debug(f"Added sun radiation source: ID {source_id}")
        return source_id
    
    @require_plugin('radiation', 'set ray count')
    def setDirectRayCount(self, band_label: str, ray_count: int):
        """Set direct ray count for radiation band."""
        radiation_wrapper.setDirectRayCount(self.radiation_model, band_label, ray_count)
    
    @require_plugin('radiation', 'set ray count')
    def setDiffuseRayCount(self, band_label: str, ray_count: int):
        """Set diffuse ray count for radiation band."""
        radiation_wrapper.setDiffuseRayCount(self.radiation_model, band_label, ray_count)
    
    @require_plugin('radiation', 'set radiation flux')
    def setDiffuseRadiationFlux(self, label: str, flux: float):
        """Set diffuse radiation flux for band."""
        radiation_wrapper.setDiffuseRadiationFlux(self.radiation_model, label, flux)
    
    @require_plugin('radiation', 'set source flux')
    def setSourceFlux(self, source_id, label: str, flux: float):
        """Set source flux for single source or multiple sources."""
        if isinstance(source_id, (list, tuple)):
            # Multiple sources - validate each source ID
            for sid in source_id:
                if not isinstance(sid, int):
                    raise TypeError(f"Source IDs must be integers, got {type(sid).__name__}")
            radiation_wrapper.setSourceFluxMultiple(self.radiation_model, source_id, label, flux)
        else:
            # Single source - validate source ID type
            if not isinstance(source_id, int):
                raise TypeError(f"Source ID must be an integer, got {type(source_id).__name__}")
            radiation_wrapper.setSourceFlux(self.radiation_model, source_id, label, flux)
    
    @require_plugin('radiation', 'set source flux')
    def setSourceFluxMultiple(self, source_ids: List[int], label: str, flux: float):
        """Set source flux for multiple sources."""
        radiation_wrapper.setSourceFluxMultiple(self.radiation_model, source_ids, label, flux)
    
    @require_plugin('radiation', 'get source flux')
    def getSourceFlux(self, source_id: int, label: str) -> float:
        """Get source flux for band."""
        return radiation_wrapper.getSourceFlux(self.radiation_model, source_id, label)
    
    @require_plugin('radiation', 'update geometry')
    def updateGeometry(self, uuids: Optional[List[int]] = None):
        """
        Update geometry in radiation model.
        
        Args:
            uuids: Optional list of specific UUIDs to update. If None, updates all geometry.
        """
        if uuids is None:
            radiation_wrapper.updateGeometry(self.radiation_model)
            logger.debug("Updated all geometry in radiation model")
        else:
            radiation_wrapper.updateGeometryUUIDs(self.radiation_model, uuids)
            logger.debug(f"Updated {len(uuids)} geometry UUIDs in radiation model")
    
    @require_plugin('radiation', 'run radiation simulation')
    def runBand(self, band_label):
        """Run radiation simulation for single band or multiple bands."""
        if isinstance(band_label, (list, tuple)):
            # Multiple bands - validate each label
            for lbl in band_label:
                if not isinstance(lbl, str):
                    raise TypeError(f"Band labels must be strings, got {type(lbl).__name__}")
            radiation_wrapper.runBandMultiple(self.radiation_model, band_label)
            logger.info(f"Completed radiation simulation for bands: {band_label}")
        else:
            # Single band - validate label type
            if not isinstance(band_label, str):
                raise TypeError(f"Band label must be a string, got {type(band_label).__name__}")
            radiation_wrapper.runBand(self.radiation_model, band_label)
            logger.info(f"Completed radiation simulation for band: {band_label}")
    
    @require_plugin('radiation', 'run radiation simulation')
    def runBandMultiple(self, labels: List[str]):
        """Run radiation simulation for multiple bands."""
        radiation_wrapper.runBandMultiple(self.radiation_model, labels)
        logger.info(f"Completed radiation simulation for bands: {labels}")
    
    @require_plugin('radiation', 'get simulation results')
    def getTotalAbsorbedFlux(self) -> List[float]:
        """Get total absorbed flux for all primitives."""
        results = radiation_wrapper.getTotalAbsorbedFlux(self.radiation_model)
        logger.debug(f"Retrieved absorbed flux data for {len(results)} primitives")
        return results
    
    # Configuration methods
    @require_plugin('radiation', 'configure radiation simulation')
    def setScatteringDepth(self, label: str, depth: int):
        """Set scattering depth for radiation band."""
        radiation_wrapper.setScatteringDepth(self.radiation_model, label, depth)
    
    @require_plugin('radiation', 'configure radiation simulation')
    def setMinScatterEnergy(self, label: str, energy: float):
        """Set minimum scatter energy for radiation band."""
        radiation_wrapper.setMinScatterEnergy(self.radiation_model, label, energy)
    
    @require_plugin('radiation', 'configure radiation emission')
    def disableEmission(self, label: str):
        """Disable emission for radiation band."""
        radiation_wrapper.disableEmission(self.radiation_model, label)
    
    @require_plugin('radiation', 'configure radiation emission')
    def enableEmission(self, label: str):
        """Enable emission for radiation band."""
        radiation_wrapper.enableEmission(self.radiation_model, label)
    
    def getPluginInfo(self) -> dict:
        """Get information about the radiation plugin."""
        registry = get_plugin_registry()
        return registry.get_plugin_capabilities('radiation')