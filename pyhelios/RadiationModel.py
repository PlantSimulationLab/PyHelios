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
from .validation.plugins import (
    validate_wavelength_range, validate_flux_value, validate_ray_count,
    validate_direction_vector, validate_band_label, validate_source_id, validate_source_id_list
)
from .validation.plugin_decorators import (
    validate_radiation_band_params, validate_collimated_source_params, validate_sphere_source_params,
    validate_sun_sphere_params, validate_get_source_flux_params,
    validate_update_geometry_params, validate_run_band_params, validate_scattering_depth_params,
    validate_min_scatter_energy_params
)
from .Context import Context
from .assets import get_asset_manager

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
    # Try asset manager first (works for both development and wheel installations)
    asset_manager = get_asset_manager()
    working_dir = asset_manager._get_helios_build_path()
    
    if working_dir and working_dir.exists():
        radiation_assets = working_dir / 'plugins' / 'radiation'
    else:
        # For wheel installations, check packaged assets  
        current_dir = Path(__file__).parent
        packaged_build = current_dir / 'assets' / 'build'
        
        if packaged_build.exists():
            working_dir = packaged_build
            radiation_assets = working_dir / 'plugins' / 'radiation'
        else:
            # Fallback to development paths
            repo_root = current_dir.parent
            build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
            working_dir = build_lib_dir.parent
            radiation_assets = working_dir / 'plugins' / 'radiation'
            
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


class CameraProperties:
    """
    Camera properties for radiation model cameras.

    This class encapsulates the properties needed to configure a radiation camera,
    providing sensible defaults and validation for camera parameters. Updated for
    Helios v1.3.60 with camera_zoom support.
    """

    def __init__(self, camera_resolution=None, focal_plane_distance=1.0, lens_diameter=0.05,
                 HFOV=20.0, FOV_aspect_ratio=0.0, lens_focal_length=0.05,
                 sensor_width_mm=35.0, model="generic", lens_make="", lens_model="",
                 lens_specification="", exposure="auto", shutter_speed=1.0/125.0,
                 white_balance="auto", camera_zoom=1.0):
        """
        Initialize camera properties with defaults matching C++ CameraProperties.

        Args:
            camera_resolution: Camera resolution as (width, height) tuple or list. Default: (512, 512)
            focal_plane_distance: Distance from viewing plane to focal plane (working distance). Default: 1.0
            lens_diameter: Diameter of camera lens (0 = pinhole camera). Default: 0.05
            HFOV: Horizontal field of view in degrees. Default: 20.0
            FOV_aspect_ratio: Ratio of horizontal to vertical FOV. Default: 0.0 (auto-calculate from resolution)
            lens_focal_length: Camera lens optical focal length in meters (physical, not 35mm equiv). Default: 0.05 (50mm)
            sensor_width_mm: Physical sensor width in mm. Default: 35.0 (full-frame)
            model: Camera model name (e.g., "Nikon D700", "Canon EOS 5D"). Default: "generic"
            lens_make: Lens manufacturer (e.g., "Canon", "Nikon"). Default: ""
            lens_model: Lens model name (e.g., "AF-S NIKKOR 50mm f/1.8G"). Default: ""
            lens_specification: Lens specification (e.g., "50mm f/1.8"). Default: ""
            exposure: Exposure mode - "auto", "ISOXXX" (e.g., "ISO100"), or "manual". Default: "auto"
            shutter_speed: Camera shutter speed in seconds (e.g., 0.008 for 1/125s). Default: 0.008 (1/125s)
            white_balance: White balance mode - "auto" or "off". Default: "auto"
            camera_zoom: Camera optical zoom multiplier. 1.0 = no zoom, 2.0 = 2x zoom.
                        Scales effective HFOV: effective_HFOV = HFOV / camera_zoom. Default: 1.0
        """
        # Set camera resolution with validation
        ## @cond
        if camera_resolution is None:
            self.camera_resolution = (512, 512)
        else:
            if isinstance(camera_resolution, (list, tuple)) and len(camera_resolution) == 2:
                self.camera_resolution = (int(camera_resolution[0]), int(camera_resolution[1]))
            else:
                raise ValueError("camera_resolution must be a tuple or list of 2 integers")
        ## @endcond

        # Validate and set numeric properties
        if focal_plane_distance <= 0:
            raise ValueError("focal_plane_distance must be greater than 0")
        if lens_diameter < 0:
            raise ValueError("lens_diameter must be non-negative")
        if HFOV <= 0 or HFOV > 180:
            raise ValueError("HFOV must be between 0 and 180 degrees")
        if FOV_aspect_ratio < 0:
            raise ValueError("FOV_aspect_ratio must be non-negative (0 = auto-calculate)")
        if lens_focal_length <= 0:
            raise ValueError("lens_focal_length must be greater than 0")
        if sensor_width_mm <= 0:
            raise ValueError("sensor_width_mm must be greater than 0")
        if shutter_speed <= 0:
            raise ValueError("shutter_speed must be greater than 0")
        if camera_zoom <= 0:
            raise ValueError("camera_zoom must be greater than 0")

        self.focal_plane_distance = float(focal_plane_distance)
        self.lens_diameter = float(lens_diameter)
        self.HFOV = float(HFOV)
        self.FOV_aspect_ratio = float(FOV_aspect_ratio)
        self.lens_focal_length = float(lens_focal_length)
        self.sensor_width_mm = float(sensor_width_mm)
        self.shutter_speed = float(shutter_speed)
        self.camera_zoom = float(camera_zoom)

        # Validate and set string properties
        if not isinstance(model, str):
            raise ValueError("model must be a string")
        if not isinstance(lens_make, str):
            raise ValueError("lens_make must be a string")
        if not isinstance(lens_model, str):
            raise ValueError("lens_model must be a string")
        if not isinstance(lens_specification, str):
            raise ValueError("lens_specification must be a string")
        if not isinstance(exposure, str):
            raise ValueError("exposure must be a string")
        if not isinstance(white_balance, str):
            raise ValueError("white_balance must be a string")

        # Validate exposure mode
        if exposure not in ["auto", "manual"] and not exposure.startswith("ISO"):
            raise ValueError("exposure must be 'auto', 'manual', or 'ISOXXX' (e.g., 'ISO100')")

        # Validate white balance mode
        if white_balance not in ["auto", "off"]:
            raise ValueError("white_balance must be 'auto' or 'off'")

        self.model = str(model)
        self.lens_make = str(lens_make)
        self.lens_model = str(lens_model)
        self.lens_specification = str(lens_specification)
        self.exposure = str(exposure)
        self.white_balance = str(white_balance)

    def to_array(self):
        """
        Convert to array format expected by C++ interface.

        Note: Returns numeric fields only. String fields (model, lens_make, etc.) are
        currently initialized with defaults in the C++ wrapper and cannot be set via
        this interface. Use the upcoming camera library methods for full metadata control.

        Returns:
            List of 10 float values: [resolution_x, resolution_y, focal_distance, lens_diameter,
                                      HFOV, FOV_aspect_ratio, lens_focal_length, sensor_width_mm,
                                      shutter_speed, camera_zoom]
        """
        return [
            float(self.camera_resolution[0]),  # resolution_x
            float(self.camera_resolution[1]),  # resolution_y
            self.focal_plane_distance,
            self.lens_diameter,
            self.HFOV,
            self.FOV_aspect_ratio,
            self.lens_focal_length,
            self.sensor_width_mm,
            self.shutter_speed,
            self.camera_zoom
        ]

    def __repr__(self):
        return (f"CameraProperties("
                f"camera_resolution={self.camera_resolution}, "
                f"focal_plane_distance={self.focal_plane_distance}, "
                f"lens_diameter={self.lens_diameter}, "
                f"HFOV={self.HFOV}, "
                f"FOV_aspect_ratio={self.FOV_aspect_ratio}, "
                f"lens_focal_length={self.lens_focal_length}, "
                f"sensor_width_mm={self.sensor_width_mm}, "
                f"model='{self.model}', "
                f"lens_make='{self.lens_make}', "
                f"lens_model='{self.lens_model}', "
                f"lens_specification='{self.lens_specification}', "
                f"exposure='{self.exposure}', "
                f"shutter_speed={self.shutter_speed}, "
                f"white_balance='{self.white_balance}', "
                f"camera_zoom={self.camera_zoom})")


class CameraMetadata:
    """
    Metadata for radiation camera image export (Helios v1.3.58+).

    This class encapsulates comprehensive metadata for camera images including
    camera properties, location, acquisition settings, image processing, and
    agronomic properties derived from plant architecture data.
    """

    class CameraPropertiesMetadata:
        """Camera intrinsic properties for metadata export."""
        def __init__(self, height=512, width=512, channels=3, type="rgb",
                     focal_length=50.0, aperture="f/2.8", sensor_width=35.0,
                     sensor_height=24.0, model="generic", lens_make="",
                     lens_model="", lens_specification="", exposure="auto",
                     shutter_speed=0.008, white_balance="auto"):
            self.height = int(height)
            self.width = int(width)
            self.channels = int(channels)
            self.type = str(type)
            self.focal_length = float(focal_length)
            self.aperture = str(aperture)
            self.sensor_width = float(sensor_width)
            self.sensor_height = float(sensor_height)
            self.model = str(model)
            self.lens_make = str(lens_make)
            self.lens_model = str(lens_model)
            self.lens_specification = str(lens_specification)
            self.exposure = str(exposure)
            self.shutter_speed = float(shutter_speed)
            self.white_balance = str(white_balance)

    class LocationProperties:
        """Geographic location properties."""
        def __init__(self, latitude=0.0, longitude=0.0):
            self.latitude = float(latitude)
            self.longitude = float(longitude)

    class AcquisitionProperties:
        """Image acquisition properties."""
        def __init__(self, date="", time="", UTC_offset=0.0, camera_height_m=0.0,
                     camera_angle_deg=0.0, light_source="sunlight"):
            self.date = str(date)
            self.time = str(time)
            self.UTC_offset = float(UTC_offset)
            self.camera_height_m = float(camera_height_m)
            self.camera_angle_deg = float(camera_angle_deg)
            self.light_source = str(light_source)

    class ImageProcessingProperties:
        """Image processing corrections applied to the image."""
        def __init__(self, saturation_adjustment=1.0, brightness_adjustment=1.0,
                     contrast_adjustment=1.0, color_space="linear"):
            self.saturation_adjustment = float(saturation_adjustment)
            self.brightness_adjustment = float(brightness_adjustment)
            self.contrast_adjustment = float(contrast_adjustment)
            self.color_space = str(color_space)

    class AgronomicProperties:
        """Agronomic properties derived from plant architecture data."""
        def __init__(self, plant_species=None, plant_count=None, plant_height_m=None,
                     plant_age_days=None, plant_stage=None, leaf_area_m2=None,
                     weed_pressure=""):
            self.plant_species = plant_species if plant_species is not None else []
            self.plant_count = plant_count if plant_count is not None else []
            self.plant_height_m = plant_height_m if plant_height_m is not None else []
            self.plant_age_days = plant_age_days if plant_age_days is not None else []
            self.plant_stage = plant_stage if plant_stage is not None else []
            self.leaf_area_m2 = leaf_area_m2 if leaf_area_m2 is not None else []
            self.weed_pressure = str(weed_pressure)

    def __init__(self, path=""):
        """
        Initialize CameraMetadata with default values.

        Args:
            path: Full path to the associated image file. Default: ""
        """
        self.path = str(path)
        self.camera_properties = self.CameraPropertiesMetadata()
        self.location_properties = self.LocationProperties()
        self.acquisition_properties = self.AcquisitionProperties()
        self.image_processing = self.ImageProcessingProperties()
        self.agronomic_properties = self.AgronomicProperties()

    def __repr__(self):
        return (f"CameraMetadata(path='{self.path}', "
                f"camera={self.camera_properties.model}, "
                f"resolution={self.camera_properties.width}x{self.camera_properties.height}, "
                f"location=({self.location_properties.latitude},{self.location_properties.longitude}))")


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
                "2. Or build with multiple plugins:\n"
                "   build_scripts/build_helios --plugins radiation,visualizer,weberpenntree\n"
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
            finally:
                self.radiation_model = None  # Prevent double deletion

    def __del__(self):
        """Destructor to ensure GPU resources freed even without 'with' statement."""
        if hasattr(self, 'radiation_model') and self.radiation_model is not None:
            try:
                radiation_wrapper.destroyRadiationModel(self.radiation_model)
                self.radiation_model = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in RadiationModel.__del__: {e}")

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
        # Validate inputs
        validate_band_label(band_label, "band_label", "addRadiationBand")
        if wavelength_min is not None and wavelength_max is not None:
            validate_wavelength_range(wavelength_min, wavelength_max, "wavelength_min", "wavelength_max", "addRadiationBand")
            radiation_wrapper.addRadiationBandWithWavelengths(self.radiation_model, band_label, wavelength_min, wavelength_max)
            logger.debug(f"Added radiation band {band_label}: {wavelength_min}-{wavelength_max} μm")
        else:
            radiation_wrapper.addRadiationBand(self.radiation_model, band_label)
            logger.debug(f"Added radiation band: {band_label}")
    
    @require_plugin('radiation', 'copy radiation band')
    @validate_radiation_band_params
    def copyRadiationBand(self, old_label: str, new_label: str, wavelength_min: float = None, wavelength_max: float = None):
        """
        Copy existing radiation band to new label, optionally with new wavelength range.

        Args:
            old_label: Existing band label to copy
            new_label: New label for the copied band
            wavelength_min: Optional minimum wavelength for new band (μm)
            wavelength_max: Optional maximum wavelength for new band (μm)

        Example:
            >>> # Copy band with same wavelength range
            >>> radiation.copyRadiationBand("SW", "SW_copy")
            >>>
            >>> # Copy band with different wavelength range
            >>> radiation.copyRadiationBand("full_spectrum", "PAR", 400, 700)
        """
        if wavelength_min is not None and wavelength_max is not None:
            validate_wavelength_range(wavelength_min, wavelength_max, "wavelength_min", "wavelength_max", "copyRadiationBand")

        radiation_wrapper.copyRadiationBand(self.radiation_model, old_label, new_label, wavelength_min, wavelength_max)
        if wavelength_min is not None:
            logger.debug(f"Copied radiation band {old_label} to {new_label} with wavelengths {wavelength_min}-{wavelength_max} μm")
        else:
            logger.debug(f"Copied radiation band {old_label} to {new_label}")
    
    @require_plugin('radiation', 'add radiation source')
    @validate_collimated_source_params
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
    @validate_sphere_source_params
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
    @validate_sun_sphere_params
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

    @require_plugin('radiation', 'set source position')
    def setSourcePosition(self, source_id: int, position):
        """
        Set position of a radiation source.

        Allows dynamic repositioning of radiation sources during simulation,
        useful for time-series modeling or moving light sources.

        Args:
            source_id: ID of the radiation source
            position: New position as vec3, SphericalCoord, or list/tuple [x, y, z]

        Example:
            >>> source_id = radiation.addCollimatedRadiationSource()
            >>> radiation.setSourcePosition(source_id, [10, 20, 30])
            >>> from pyhelios.types import vec3
            >>> radiation.setSourcePosition(source_id, vec3(15, 25, 35))
        """
        if not isinstance(source_id, int) or source_id < 0:
            raise ValueError(f"Source ID must be a non-negative integer, got {source_id}")
        radiation_wrapper.setSourcePosition(self.radiation_model, source_id, position)
        logger.debug(f"Updated position for radiation source {source_id}")

    @require_plugin('radiation', 'add rectangle radiation source')
    def addRectangleRadiationSource(self, position, size, rotation) -> int:
        """
        Add a rectangle (planar) radiation source.

        Rectangle sources are ideal for modeling artificial lighting such as
        LED panels, grow lights, or window light sources.

        Args:
            position: Center position as vec3 or list [x, y, z]
            size: Rectangle dimensions as vec2 or list [width, height]
            rotation: Rotation vector as vec3 or list [rx, ry, rz] (Euler angles in radians)

        Returns:
            Source ID

        Example:
            >>> from pyhelios.types import vec3, vec2
            >>> source_id = radiation.addRectangleRadiationSource(
            ...     position=vec3(0, 0, 5),
            ...     size=vec2(2, 1),
            ...     rotation=vec3(0, 0, 0)
            ... )
            >>> radiation.setSourceFlux(source_id, "PAR", 500.0)
        """
        return radiation_wrapper.addRectangleRadiationSource(self.radiation_model, position, size, rotation)

    @require_plugin('radiation', 'add disk radiation source')
    def addDiskRadiationSource(self, position, radius: float, rotation) -> int:
        """
        Add a disk (circular planar) radiation source.

        Disk sources are useful for modeling circular light sources such as
        spotlights, circular LED arrays, or solar simulators.

        Args:
            position: Center position as vec3 or list [x, y, z]
            radius: Disk radius
            rotation: Rotation vector as vec3 or list [rx, ry, rz] (Euler angles in radians)

        Returns:
            Source ID

        Example:
            >>> from pyhelios.types import vec3
            >>> source_id = radiation.addDiskRadiationSource(
            ...     position=vec3(0, 0, 5),
            ...     radius=1.5,
            ...     rotation=vec3(0, 0, 0)
            ... )
            >>> radiation.setSourceFlux(source_id, "PAR", 300.0)
        """
        if radius <= 0:
            raise ValueError(f"Radius must be positive, got {radius}")
        return radiation_wrapper.addDiskRadiationSource(self.radiation_model, position, radius, rotation)

    # Source spectrum methods
    @require_plugin('radiation', 'manage source spectrum')
    def setSourceSpectrum(self, source_id, spectrum):
        """
        Set radiation spectrum for source(s).

        Spectral distributions define how radiation intensity varies with wavelength,
        essential for realistic modeling of different light sources (sunlight, LEDs, etc.).

        Args:
            source_id: Source ID (int) or list of source IDs
            spectrum: Either:
                - Spectrum data as list of (wavelength, value) tuples
                - Global data label string

        Example:
            >>> # Define custom LED spectrum
            >>> led_spectrum = [
            ...     (400, 0.0), (450, 0.3), (500, 0.8),
            ...     (550, 0.5), (600, 0.2), (700, 0.0)
            ... ]
            >>> radiation.setSourceSpectrum(source_id, led_spectrum)
            >>>
            >>> # Use predefined spectrum from global data
            >>> radiation.setSourceSpectrum(source_id, "D65_illuminant")
            >>>
            >>> # Apply same spectrum to multiple sources
            >>> radiation.setSourceSpectrum([src1, src2, src3], led_spectrum)
        """
        radiation_wrapper.setSourceSpectrum(self.radiation_model, source_id, spectrum)
        logger.debug(f"Set spectrum for source(s) {source_id}")

    @require_plugin('radiation', 'configure source spectrum')
    def setSourceSpectrumIntegral(self, source_id: int, source_integral: float,
                                  wavelength_min: float = None, wavelength_max: float = None):
        """
        Set source spectrum integral value.

        Normalizes the spectrum so that its integral equals the specified value,
        useful for calibrating source intensity.

        Args:
            source_id: Source ID
            source_integral: Target integral value
            wavelength_min: Optional minimum wavelength for integration range
            wavelength_max: Optional maximum wavelength for integration range

        Example:
            >>> radiation.setSourceSpectrumIntegral(source_id, 1000.0)
            >>> radiation.setSourceSpectrumIntegral(source_id, 500.0, 400, 700)  # PAR range
        """
        if not isinstance(source_id, int) or source_id < 0:
            raise ValueError(f"Source ID must be a non-negative integer, got {source_id}")
        if source_integral < 0:
            raise ValueError(f"Source integral must be non-negative, got {source_integral}")

        radiation_wrapper.setSourceSpectrumIntegral(self.radiation_model, source_id, source_integral,
                                                    wavelength_min, wavelength_max)
        logger.debug(f"Set spectrum integral for source {source_id}: {source_integral}")

    # Spectrum integration and analysis methods
    @require_plugin('radiation', 'integrate spectrum')
    def integrateSpectrum(self, object_spectrum, wavelength_min: float = None,
                         wavelength_max: float = None, source_id: int = None,
                         camera_spectrum=None) -> float:
        """
        Integrate spectrum with optional source/camera spectra and wavelength range.

        This unified method handles multiple integration scenarios:
        - Basic: Total spectrum integration
        - Range: Integration over wavelength range
        - Source: Integration weighted by source spectrum
        - Camera: Integration weighted by camera spectral response
        - Full: Integration with both source and camera spectra

        Args:
            object_spectrum: Object spectrum as list of (wavelength, value) tuples/vec2
            wavelength_min: Optional minimum wavelength for integration range
            wavelength_max: Optional maximum wavelength for integration range
            source_id: Optional source ID for source spectrum weighting
            camera_spectrum: Optional camera spectrum for camera response weighting

        Returns:
            Integrated value

        Example:
            >>> leaf_reflectance = [(400, 0.1), (500, 0.4), (600, 0.6), (700, 0.5)]
            >>>
            >>> # Total integration
            >>> total = radiation.integrateSpectrum(leaf_reflectance)
            >>>
            >>> # PAR range (400-700nm)
            >>> par = radiation.integrateSpectrum(leaf_reflectance, 400, 700)
            >>>
            >>> # With source spectrum
            >>> source_weighted = radiation.integrateSpectrum(
            ...     leaf_reflectance, 400, 700, source_id=sun_source
            ... )
            >>>
            >>> # With camera response
            >>> camera_response = [(400, 0.2), (550, 1.0), (700, 0.3)]
            >>> camera_weighted = radiation.integrateSpectrum(
            ...     leaf_reflectance, camera_spectrum=camera_response
            ... )
        """
        return radiation_wrapper.integrateSpectrum(self.radiation_model, object_spectrum,
                                                  wavelength_min, wavelength_max,
                                                  source_id, camera_spectrum)

    @require_plugin('radiation', 'integrate source spectrum')
    def integrateSourceSpectrum(self, source_id: int, wavelength_min: float, wavelength_max: float) -> float:
        """
        Integrate source spectrum over wavelength range.

        Args:
            source_id: Source ID
            wavelength_min: Minimum wavelength
            wavelength_max: Maximum wavelength

        Returns:
            Integrated source spectrum value

        Example:
            >>> par_flux = radiation.integrateSourceSpectrum(source_id, 400, 700)
        """
        if not isinstance(source_id, int) or source_id < 0:
            raise ValueError(f"Source ID must be a non-negative integer, got {source_id}")
        return radiation_wrapper.integrateSourceSpectrum(self.radiation_model, source_id,
                                                        wavelength_min, wavelength_max)

    # Spectral manipulation methods
    @require_plugin('radiation', 'scale spectrum')
    def scaleSpectrum(self, existing_label: str, new_label_or_scale, scale_factor: float = None):
        """
        Scale spectrum in-place or to new label.

        Useful for adjusting spectrum intensities or creating variations of
        existing spectra for sensitivity analysis.

        Supports two call patterns:
        - scaleSpectrum("label", scale) -> scales in-place
        - scaleSpectrum("existing", "new", scale) -> creates new scaled spectrum

        Args:
            existing_label: Existing global data label
            new_label_or_scale: Either new label string (if creating new) or scale factor (if in-place)
            scale_factor: Scale factor (required only if new_label_or_scale is a string)

        Example:
            >>> # In-place scaling
            >>> radiation.scaleSpectrum("leaf_reflectance", 1.2)
            >>>
            >>> # Create new scaled spectrum
            >>> radiation.scaleSpectrum("leaf_reflectance", "scaled_leaf", 1.5)
        """
        if not isinstance(existing_label, str) or not existing_label.strip():
            raise ValueError("Existing label must be a non-empty string")

        radiation_wrapper.scaleSpectrum(self.radiation_model, existing_label,
                                       new_label_or_scale, scale_factor)
        logger.debug(f"Scaled spectrum '{existing_label}'")

    @require_plugin('radiation', 'scale spectrum randomly')
    def scaleSpectrumRandomly(self, existing_label: str, new_label: str,
                             min_scale: float, max_scale: float):
        """
        Scale spectrum with random factor and store as new label.

        Useful for creating stochastic variations in spectral properties for
        Monte Carlo simulations or uncertainty quantification.

        Args:
            existing_label: Existing global data label
            new_label: New global data label for scaled spectrum
            min_scale: Minimum scale factor
            max_scale: Maximum scale factor

        Example:
            >>> # Create random variation of leaf reflectance
            >>> radiation.scaleSpectrumRandomly("leaf_base", "leaf_variant", 0.8, 1.2)
        """
        if not isinstance(existing_label, str) or not existing_label.strip():
            raise ValueError("Existing label must be a non-empty string")
        if not isinstance(new_label, str) or not new_label.strip():
            raise ValueError("New label must be a non-empty string")
        if min_scale >= max_scale:
            raise ValueError(f"min_scale ({min_scale}) must be less than max_scale ({max_scale})")

        radiation_wrapper.scaleSpectrumRandomly(self.radiation_model, existing_label, new_label,
                                               min_scale, max_scale)
        logger.debug(f"Scaled spectrum '{existing_label}' randomly to '{new_label}'")

    @require_plugin('radiation', 'blend spectra')
    def blendSpectra(self, new_label: str, spectrum_labels: List[str], weights: List[float]):
        """
        Blend multiple spectra with specified weights.

        Creates weighted combination of spectra, useful for mixing material properties
        or creating composite light sources.

        Args:
            new_label: New global data label for blended spectrum
            spectrum_labels: List of spectrum labels to blend
            weights: List of weights (must sum to reasonable values, same length as labels)

        Example:
            >>> # Mix two leaf types (70% type A, 30% type B)
            >>> radiation.blendSpectra("mixed_leaf",
            ...     ["leaf_type_a", "leaf_type_b"],
            ...     [0.7, 0.3]
            ... )
        """
        if not isinstance(new_label, str) or not new_label.strip():
            raise ValueError("New label must be a non-empty string")
        if len(spectrum_labels) != len(weights):
            raise ValueError(f"Number of labels ({len(spectrum_labels)}) must match number of weights ({len(weights)})")
        if not spectrum_labels:
            raise ValueError("At least one spectrum label required")

        radiation_wrapper.blendSpectra(self.radiation_model, new_label, spectrum_labels, weights)
        logger.debug(f"Blended {len(spectrum_labels)} spectra into '{new_label}'")

    @require_plugin('radiation', 'blend spectra randomly')
    def blendSpectraRandomly(self, new_label: str, spectrum_labels: List[str]):
        """
        Blend multiple spectra with random weights.

        Creates random combinations of spectra, useful for generating diverse
        material properties in stochastic simulations.

        Args:
            new_label: New global data label for blended spectrum
            spectrum_labels: List of spectrum labels to blend

        Example:
            >>> # Create random mixture of leaf spectra
            >>> radiation.blendSpectraRandomly("random_leaf",
            ...     ["young_leaf", "mature_leaf", "senescent_leaf"]
            ... )
        """
        if not isinstance(new_label, str) or not new_label.strip():
            raise ValueError("New label must be a non-empty string")
        if not spectrum_labels:
            raise ValueError("At least one spectrum label required")

        radiation_wrapper.blendSpectraRandomly(self.radiation_model, new_label, spectrum_labels)
        logger.debug(f"Blended {len(spectrum_labels)} spectra randomly into '{new_label}'")

    # Spectral interpolation methods
    @require_plugin('radiation', 'interpolate spectrum from data')
    def interpolateSpectrumFromPrimitiveData(self, primitive_uuids: List[int],
                                            spectra_labels: List[str], values: List[float],
                                            primitive_data_query_label: str,
                                            primitive_data_radprop_label: str):
        """
        Interpolate spectral properties based on primitive data values.

        Automatically assigns spectra to primitives by interpolating between
        reference spectra based on continuous data values (e.g., age, moisture, etc.).

        Args:
            primitive_uuids: List of primitive UUIDs to assign spectra
            spectra_labels: List of reference spectrum labels
            values: List of data values corresponding to each spectrum
            primitive_data_query_label: Primitive data label containing query values
            primitive_data_radprop_label: Primitive data label to store assigned spectra

        Example:
            >>> # Assign leaf reflectance based on age
            >>> leaf_patches = context.getAllUUIDs("patch")
            >>> radiation.interpolateSpectrumFromPrimitiveData(
            ...     primitive_uuids=leaf_patches,
            ...     spectra_labels=["young_leaf", "mature_leaf", "old_leaf"],
            ...     values=[0.0, 50.0, 100.0],  # Days since emergence
            ...     primitive_data_query_label="leaf_age",
            ...     primitive_data_radprop_label="reflectance"
            ... )
        """
        if not isinstance(primitive_uuids, (list, tuple)) or not primitive_uuids:
            raise ValueError("Primitive UUIDs must be a non-empty list")
        if not isinstance(spectra_labels, (list, tuple)) or not spectra_labels:
            raise ValueError("Spectra labels must be a non-empty list")
        if not isinstance(values, (list, tuple)) or not values:
            raise ValueError("Values must be a non-empty list")
        if len(spectra_labels) != len(values):
            raise ValueError(f"Number of spectra ({len(spectra_labels)}) must match number of values ({len(values)})")

        radiation_wrapper.interpolateSpectrumFromPrimitiveData(
            self.radiation_model, primitive_uuids, spectra_labels, values,
            primitive_data_query_label, primitive_data_radprop_label
        )
        logger.debug(f"Interpolated spectra for {len(primitive_uuids)} primitives")

    @require_plugin('radiation', 'interpolate spectrum from object data')
    def interpolateSpectrumFromObjectData(self, object_ids: List[int],
                                         spectra_labels: List[str], values: List[float],
                                         object_data_query_label: str,
                                         primitive_data_radprop_label: str):
        """
        Interpolate spectral properties based on object data values.

        Automatically assigns spectra to object primitives by interpolating between
        reference spectra based on continuous object-level data values.

        Args:
            object_ids: List of object IDs
            spectra_labels: List of reference spectrum labels
            values: List of data values corresponding to each spectrum
            object_data_query_label: Object data label containing query values
            primitive_data_radprop_label: Primitive data label to store assigned spectra

        Example:
            >>> # Assign tree reflectance based on health index
            >>> tree_ids = [tree1_id, tree2_id, tree3_id]
            >>> radiation.interpolateSpectrumFromObjectData(
            ...     object_ids=tree_ids,
            ...     spectra_labels=["healthy_tree", "stressed_tree", "diseased_tree"],
            ...     values=[1.0, 0.5, 0.0],  # Health index
            ...     object_data_query_label="health_index",
            ...     primitive_data_radprop_label="reflectance"
            ... )
        """
        if not isinstance(object_ids, (list, tuple)) or not object_ids:
            raise ValueError("Object IDs must be a non-empty list")
        if not isinstance(spectra_labels, (list, tuple)) or not spectra_labels:
            raise ValueError("Spectra labels must be a non-empty list")
        if not isinstance(values, (list, tuple)) or not values:
            raise ValueError("Values must be a non-empty list")
        if len(spectra_labels) != len(values):
            raise ValueError(f"Number of spectra ({len(spectra_labels)}) must match number of values ({len(values)})")

        radiation_wrapper.interpolateSpectrumFromObjectData(
            self.radiation_model, object_ids, spectra_labels, values,
            object_data_query_label, primitive_data_radprop_label
        )
        logger.debug(f"Interpolated spectra for {len(object_ids)} objects")

    @require_plugin('radiation', 'set ray count')
    def setDirectRayCount(self, band_label: str, ray_count: int):
        """Set direct ray count for radiation band."""
        validate_band_label(band_label, "band_label", "setDirectRayCount")
        validate_ray_count(ray_count, "ray_count", "setDirectRayCount")
        radiation_wrapper.setDirectRayCount(self.radiation_model, band_label, ray_count)
    
    @require_plugin('radiation', 'set ray count')
    def setDiffuseRayCount(self, band_label: str, ray_count: int):
        """Set diffuse ray count for radiation band."""
        validate_band_label(band_label, "band_label", "setDiffuseRayCount")
        validate_ray_count(ray_count, "ray_count", "setDiffuseRayCount")
        radiation_wrapper.setDiffuseRayCount(self.radiation_model, band_label, ray_count)
    
    @require_plugin('radiation', 'set radiation flux')
    def setDiffuseRadiationFlux(self, label: str, flux: float):
        """Set diffuse radiation flux for band."""
        validate_band_label(label, "label", "setDiffuseRadiationFlux")
        validate_flux_value(flux, "flux", "setDiffuseRadiationFlux")
        radiation_wrapper.setDiffuseRadiationFlux(self.radiation_model, label, flux)

    @require_plugin('radiation', 'configure diffuse radiation')
    def setDiffuseRadiationExtinctionCoeff(self, label: str, K: float, peak_direction):
        """
        Set diffuse radiation extinction coefficient with directional bias.

        Models directionally-biased diffuse radiation (e.g., sky radiation with zenith peak).

        Args:
            label: Band label
            K: Extinction coefficient
            peak_direction: Peak direction as vec3, SphericalCoord, or list [x, y, z]

        Example:
            >>> from pyhelios.types import vec3
            >>> radiation.setDiffuseRadiationExtinctionCoeff("SW", 0.5, vec3(0, 0, 1))
        """
        validate_band_label(label, "label", "setDiffuseRadiationExtinctionCoeff")
        if K < 0:
            raise ValueError(f"Extinction coefficient must be non-negative, got {K}")
        radiation_wrapper.setDiffuseRadiationExtinctionCoeff(self.radiation_model, label, K, peak_direction)
        logger.debug(f"Set diffuse extinction coefficient for band '{label}': K={K}")

    @require_plugin('radiation', 'query diffuse flux')
    def getDiffuseFlux(self, band_label: str) -> float:
        """
        Get diffuse flux for band.

        Args:
            band_label: Band label

        Returns:
            Diffuse flux value

        Example:
            >>> flux = radiation.getDiffuseFlux("SW")
        """
        validate_band_label(band_label, "band_label", "getDiffuseFlux")
        return radiation_wrapper.getDiffuseFlux(self.radiation_model, band_label)

    @require_plugin('radiation', 'configure diffuse spectrum')
    def setDiffuseSpectrum(self, band_label, spectrum_label: str):
        """
        Set diffuse spectrum from global data label.

        Args:
            band_label: Band label (string) or list of band labels
            spectrum_label: Spectrum global data label

        Example:
            >>> radiation.setDiffuseSpectrum("SW", "sky_spectrum")
            >>> radiation.setDiffuseSpectrum(["SW", "NIR"], "sky_spectrum")
        """
        if isinstance(band_label, str):
            validate_band_label(band_label, "band_label", "setDiffuseSpectrum")
        else:
            for label in band_label:
                validate_band_label(label, "band_label", "setDiffuseSpectrum")
        if not isinstance(spectrum_label, str) or not spectrum_label.strip():
            raise ValueError("Spectrum label must be a non-empty string")

        radiation_wrapper.setDiffuseSpectrum(self.radiation_model, band_label, spectrum_label)
        logger.debug(f"Set diffuse spectrum for band(s) {band_label}")

    @require_plugin('radiation', 'configure diffuse spectrum')
    def setDiffuseSpectrumIntegral(self, spectrum_integral: float, wavelength_min: float = None,
                                   wavelength_max: float = None, band_label: str = None):
        """
        Set diffuse spectrum integral.

        Args:
            spectrum_integral: Integral value
            wavelength_min: Optional minimum wavelength
            wavelength_max: Optional maximum wavelength
            band_label: Optional specific band label (None for all bands)

        Example:
            >>> radiation.setDiffuseSpectrumIntegral(1000.0)  # All bands
            >>> radiation.setDiffuseSpectrumIntegral(500.0, 400, 700, band_label="PAR")  # Specific band
        """
        if spectrum_integral < 0:
            raise ValueError(f"Spectrum integral must be non-negative, got {spectrum_integral}")
        if band_label is not None:
            validate_band_label(band_label, "band_label", "setDiffuseSpectrumIntegral")

        radiation_wrapper.setDiffuseSpectrumIntegral(self.radiation_model, spectrum_integral,
                                                     wavelength_min, wavelength_max, band_label)
        logger.debug(f"Set diffuse spectrum integral: {spectrum_integral}")

    @require_plugin('radiation', 'set source flux')
    def setSourceFlux(self, source_id, label: str, flux: float):
        """Set source flux for single source or multiple sources."""
        validate_band_label(label, "label", "setSourceFlux")
        validate_flux_value(flux, "flux", "setSourceFlux")
        
        if isinstance(source_id, (list, tuple)):
            # Multiple sources
            validate_source_id_list(list(source_id), "source_id", "setSourceFlux")
            radiation_wrapper.setSourceFluxMultiple(self.radiation_model, source_id, label, flux)
        else:
            # Single source
            validate_source_id(source_id, "source_id", "setSourceFlux")
            radiation_wrapper.setSourceFlux(self.radiation_model, source_id, label, flux)
    
    
    @require_plugin('radiation', 'get source flux')
    @validate_get_source_flux_params
    def getSourceFlux(self, source_id: int, label: str) -> float:
        """Get source flux for band."""
        return radiation_wrapper.getSourceFlux(self.radiation_model, source_id, label)
    
    @require_plugin('radiation', 'update geometry')
    @validate_update_geometry_params
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
    @validate_run_band_params
    def runBand(self, band_label):
        """
        Run radiation simulation for single band or multiple bands.
        
        PERFORMANCE NOTE: When simulating multiple radiation bands, it is HIGHLY RECOMMENDED
        to run all bands in a single call (e.g., runBand(["PAR", "NIR", "SW"])) rather than
        sequential single-band calls. This provides significant computational efficiency gains
        because:
        
        - GPU ray tracing setup is done once for all bands
        - Scene geometry acceleration structures are reused
        - OptiX kernel launches are batched together
        - Memory transfers between CPU/GPU are minimized
        
        Example:
            # EFFICIENT - Single call for multiple bands
            radiation.runBand(["PAR", "NIR", "SW"])
            
            # INEFFICIENT - Sequential single-band calls  
            radiation.runBand("PAR")
            radiation.runBand("NIR") 
            radiation.runBand("SW")
        
        Args:
            band_label: Single band name (str) or list of band names for multi-band simulation
        """
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
    
    
    @require_plugin('radiation', 'get simulation results')
    def getTotalAbsorbedFlux(self) -> List[float]:
        """Get total absorbed flux for all primitives."""
        results = radiation_wrapper.getTotalAbsorbedFlux(self.radiation_model)
        logger.debug(f"Retrieved absorbed flux data for {len(results)} primitives")
        return results

    # Band query methods
    @require_plugin('radiation', 'check band existence')
    def doesBandExist(self, label: str) -> bool:
        """
        Check if a radiation band exists.

        Args:
            label: Name/label of the radiation band to check

        Returns:
            True if band exists, False otherwise

        Example:
            >>> radiation.addRadiationBand("SW")
            >>> radiation.doesBandExist("SW")
            True
            >>> radiation.doesBandExist("nonexistent")
            False
        """
        validate_band_label(label, "label", "doesBandExist")
        return radiation_wrapper.doesBandExist(self.radiation_model, label)

    # Advanced source management methods
    @require_plugin('radiation', 'manage radiation sources')
    def deleteRadiationSource(self, source_id: int):
        """
        Delete a radiation source.

        Args:
            source_id: ID of the radiation source to delete

        Example:
            >>> source_id = radiation.addCollimatedRadiationSource()
            >>> radiation.deleteRadiationSource(source_id)
        """
        if not isinstance(source_id, int) or source_id < 0:
            raise ValueError(f"Source ID must be a non-negative integer, got {source_id}")
        radiation_wrapper.deleteRadiationSource(self.radiation_model, source_id)
        logger.debug(f"Deleted radiation source {source_id}")

    @require_plugin('radiation', 'query radiation sources')
    def getSourcePosition(self, source_id: int):
        """
        Get position of a radiation source.

        Args:
            source_id: ID of the radiation source

        Returns:
            vec3 position of the source

        Example:
            >>> source_id = radiation.addCollimatedRadiationSource()
            >>> position = radiation.getSourcePosition(source_id)
            >>> print(f"Source at: {position}")
        """
        if not isinstance(source_id, int) or source_id < 0:
            raise ValueError(f"Source ID must be a non-negative integer, got {source_id}")
        position_list = radiation_wrapper.getSourcePosition(self.radiation_model, source_id)
        from .wrappers.DataTypes import vec3
        return vec3(position_list[0], position_list[1], position_list[2])

    # Advanced simulation methods
    @require_plugin('radiation', 'get sky energy')
    def getSkyEnergy(self) -> float:
        """
        Get total sky energy.

        Returns:
            Total sky energy value

        Example:
            >>> energy = radiation.getSkyEnergy()
            >>> print(f"Sky energy: {energy}")
        """
        return radiation_wrapper.getSkyEnergy(self.radiation_model)

    @require_plugin('radiation', 'calculate G-function')
    def calculateGtheta(self, view_direction) -> float:
        """
        Calculate G-function (geometry factor) for given view direction.

        The G-function describes the geometric relationship between leaf area
        distribution and viewing direction, important for canopy radiation modeling.

        Args:
            view_direction: View direction as vec3 or list/tuple [x, y, z]

        Returns:
            G-function value

        Example:
            >>> from pyhelios.types import vec3
            >>> g_value = radiation.calculateGtheta(vec3(0, 0, 1))
            >>> print(f"G-function: {g_value}")
        """
        context_ptr = self.context.getNativePtr()
        return radiation_wrapper.calculateGtheta(self.radiation_model, context_ptr, view_direction)

    @require_plugin('radiation', 'configure output data')
    def optionalOutputPrimitiveData(self, label: str):
        """
        Enable optional primitive data output.

        Args:
            label: Name/label of the primitive data to output

        Example:
            >>> radiation.optionalOutputPrimitiveData("temperature")
        """
        validate_band_label(label, "label", "optionalOutputPrimitiveData")
        radiation_wrapper.optionalOutputPrimitiveData(self.radiation_model, label)
        logger.debug(f"Enabled optional output for primitive data: {label}")

    @require_plugin('radiation', 'configure boundary conditions')
    def enforcePeriodicBoundary(self, boundary: str):
        """
        Enforce periodic boundary conditions.

        Periodic boundaries are useful for large-scale simulations to reduce
        edge effects by wrapping radiation at domain boundaries.

        Args:
            boundary: Boundary specification string (e.g., "xy", "xyz", "x", "y", "z")

        Example:
            >>> radiation.enforcePeriodicBoundary("xy")
        """
        if not isinstance(boundary, str) or not boundary:
            raise ValueError("Boundary specification must be a non-empty string")
        radiation_wrapper.enforcePeriodicBoundary(self.radiation_model, boundary)
        logger.debug(f"Enforced periodic boundary: {boundary}")

    # Configuration methods
    @require_plugin('radiation', 'configure radiation simulation')
    @validate_scattering_depth_params
    def setScatteringDepth(self, label: str, depth: int):
        """Set scattering depth for radiation band."""
        radiation_wrapper.setScatteringDepth(self.radiation_model, label, depth)
    
    @require_plugin('radiation', 'configure radiation simulation')
    @validate_min_scatter_energy_params
    def setMinScatterEnergy(self, label: str, energy: float):
        """Set minimum scatter energy for radiation band."""
        radiation_wrapper.setMinScatterEnergy(self.radiation_model, label, energy)
    
    @require_plugin('radiation', 'configure radiation emission')
    def disableEmission(self, label: str):
        """Disable emission for radiation band."""
        validate_band_label(label, "label", "disableEmission")
        radiation_wrapper.disableEmission(self.radiation_model, label)
    
    @require_plugin('radiation', 'configure radiation emission')
    def enableEmission(self, label: str):
        """Enable emission for radiation band."""
        validate_band_label(label, "label", "enableEmission")
        radiation_wrapper.enableEmission(self.radiation_model, label)
    
    #=============================================================================
    # Camera and Image Functions (v1.3.47)
    #=============================================================================

    @require_plugin('radiation', 'add radiation camera')
    def addRadiationCamera(self, camera_label: str, band_labels: List[str], position, lookat_or_direction,
                          camera_properties=None, antialiasing_samples: int = 100):
        """
        Add a radiation camera to the simulation.

        Args:
            camera_label: Unique label string for the camera
            band_labels: List of radiation band labels for the camera
            position: Camera position as vec3 object
            lookat_or_direction: Either:
                - Lookat point as vec3 object
                - SphericalCoord for viewing direction
            camera_properties: CameraProperties instance or None for defaults
            antialiasing_samples: Number of antialiasing samples (default: 100)

        Raises:
            ValidationError: If parameters are invalid or have wrong types
            RadiationModelError: If camera creation fails

        Example:
            >>> from pyhelios import vec3, CameraProperties
            >>> # Create camera looking at origin from above
            >>> camera_props = CameraProperties(camera_resolution=(1024, 1024))
            >>> radiation_model.addRadiationCamera("main_camera", ["red", "green", "blue"],
            ...                                   position=vec3(0, 0, 5), lookat_or_direction=vec3(0, 0, 0),
            ...                                   camera_properties=camera_props)
        """
        # Import here to avoid circular imports
        from .wrappers import URadiationModelWrapper as radiation_wrapper
        from .wrappers.DataTypes import SphericalCoord, vec3, make_vec3
        from .validation.plugins import validate_camera_label, validate_band_labels_list, validate_antialiasing_samples

        # Validate basic parameters
        validated_label = validate_camera_label(camera_label, "camera_label", "addRadiationCamera")
        validated_bands = validate_band_labels_list(band_labels, "band_labels", "addRadiationCamera")
        validated_samples = validate_antialiasing_samples(antialiasing_samples, "antialiasing_samples", "addRadiationCamera")

        # Validate position (must be vec3)
        if not (hasattr(position, 'x') and hasattr(position, 'y') and hasattr(position, 'z')):
            raise TypeError("position must be a vec3 object. Use vec3(x, y, z) to create one.")
        validated_position = position

        # Validate lookat_or_direction (must be vec3 or SphericalCoord)
        if hasattr(lookat_or_direction, 'radius') and hasattr(lookat_or_direction, 'elevation'):
            validated_direction = lookat_or_direction  # SphericalCoord
        elif hasattr(lookat_or_direction, 'x') and hasattr(lookat_or_direction, 'y') and hasattr(lookat_or_direction, 'z'):
            validated_direction = lookat_or_direction  # vec3
        else:
            raise TypeError("lookat_or_direction must be a vec3 or SphericalCoord object. Use vec3(x, y, z) or SphericalCoord to create one.")

        # Set up camera properties
        if camera_properties is None:
            camera_properties = CameraProperties()

        # Call appropriate wrapper function based on direction type
        try:
            if hasattr(validated_direction, 'radius') and hasattr(validated_direction, 'elevation'):
                # SphericalCoord case
                direction_coords = validated_direction.to_list()
                if len(direction_coords) >= 3:
                    # Use only radius, elevation, azimuth (first 3 elements)
                    radius, elevation, azimuth = direction_coords[0], direction_coords[1], direction_coords[2]
                else:
                    raise ValueError("SphericalCoord must have at least radius, elevation, and azimuth")

                radiation_wrapper.addRadiationCameraSpherical(
                    self.radiation_model,
                    validated_label,
                    validated_bands,
                    validated_position.x, validated_position.y, validated_position.z,
                    radius, elevation, azimuth,
                    camera_properties.to_array(),
                    validated_samples
                )
            else:
                # vec3 case
                radiation_wrapper.addRadiationCameraVec3(
                    self.radiation_model,
                    validated_label,
                    validated_bands,
                    validated_position.x, validated_position.y, validated_position.z,
                    validated_direction.x, validated_direction.y, validated_direction.z,
                    camera_properties.to_array(),
                    validated_samples
                )

        except Exception as e:
            raise RadiationModelError(f"Failed to add radiation camera '{validated_label}': {e}")

    @require_plugin('radiation', 'manage camera position')
    def setCameraPosition(self, camera_label: str, position):
        """
        Set camera position.

        Allows dynamic camera repositioning during simulation, useful for
        time-series captures or multi-view imaging.

        Args:
            camera_label: Camera label string
            position: Camera position as vec3 or list [x, y, z]

        Example:
            >>> radiation.setCameraPosition("cam1", [0, 0, 10])
            >>> from pyhelios.types import vec3
            >>> radiation.setCameraPosition("cam1", vec3(5, 5, 10))
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        radiation_wrapper.setCameraPosition(self.radiation_model, camera_label, position)
        logger.debug(f"Updated camera '{camera_label}' position")

    @require_plugin('radiation', 'query camera position')
    def getCameraPosition(self, camera_label: str):
        """
        Get camera position.

        Args:
            camera_label: Camera label string

        Returns:
            vec3 position of the camera

        Example:
            >>> position = radiation.getCameraPosition("cam1")
            >>> print(f"Camera at: {position}")
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        position_list = radiation_wrapper.getCameraPosition(self.radiation_model, camera_label)
        from .wrappers.DataTypes import vec3
        return vec3(position_list[0], position_list[1], position_list[2])

    @require_plugin('radiation', 'manage camera lookat')
    def setCameraLookat(self, camera_label: str, lookat):
        """
        Set camera lookat point.

        Args:
            camera_label: Camera label string
            lookat: Lookat point as vec3 or list [x, y, z]

        Example:
            >>> radiation.setCameraLookat("cam1", [0, 0, 0])
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        radiation_wrapper.setCameraLookat(self.radiation_model, camera_label, lookat)
        logger.debug(f"Updated camera '{camera_label}' lookat point")

    @require_plugin('radiation', 'query camera lookat')
    def getCameraLookat(self, camera_label: str):
        """
        Get camera lookat point.

        Args:
            camera_label: Camera label string

        Returns:
            vec3 lookat point

        Example:
            >>> lookat = radiation.getCameraLookat("cam1")
            >>> print(f"Camera looking at: {lookat}")
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        lookat_list = radiation_wrapper.getCameraLookat(self.radiation_model, camera_label)
        from .wrappers.DataTypes import vec3
        return vec3(lookat_list[0], lookat_list[1], lookat_list[2])

    @require_plugin('radiation', 'manage camera orientation')
    def setCameraOrientation(self, camera_label: str, direction):
        """
        Set camera orientation.

        Args:
            camera_label: Camera label string
            direction: View direction as vec3, SphericalCoord, or list [x, y, z]

        Example:
            >>> radiation.setCameraOrientation("cam1", [0, 0, 1])
            >>> from pyhelios.types import SphericalCoord
            >>> radiation.setCameraOrientation("cam1", SphericalCoord(1.0, 45.0, 90.0))
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        radiation_wrapper.setCameraOrientation(self.radiation_model, camera_label, direction)
        logger.debug(f"Updated camera '{camera_label}' orientation")

    @require_plugin('radiation', 'query camera orientation')
    def getCameraOrientation(self, camera_label: str):
        """
        Get camera orientation.

        Args:
            camera_label: Camera label string

        Returns:
            SphericalCoord orientation [radius, elevation, azimuth]

        Example:
            >>> orientation = radiation.getCameraOrientation("cam1")
            >>> print(f"Camera orientation: {orientation}")
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        orientation_list = radiation_wrapper.getCameraOrientation(self.radiation_model, camera_label)
        from .wrappers.DataTypes import SphericalCoord
        return SphericalCoord(orientation_list[0], orientation_list[1], orientation_list[2])

    @require_plugin('radiation', 'query cameras')
    def getAllCameraLabels(self) -> List[str]:
        """
        Get all camera labels.

        Returns:
            List of all camera label strings

        Example:
            >>> cameras = radiation.getAllCameraLabels()
            >>> print(f"Available cameras: {cameras}")
        """
        return radiation_wrapper.getAllCameraLabels(self.radiation_model)

    @require_plugin('radiation', 'configure camera spectral response')
    def setCameraSpectralResponse(self, camera_label: str, band_label: str, global_data: str):
        """
        Set camera spectral response from global data.

        Args:
            camera_label: Camera label
            band_label: Band label
            global_data: Global data label for spectral response curve

        Example:
            >>> radiation.setCameraSpectralResponse("cam1", "red", "sensor_red_response")
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        validate_band_label(band_label, "band_label", "setCameraSpectralResponse")
        if not isinstance(global_data, str) or not global_data.strip():
            raise ValueError("Global data label must be a non-empty string")

        radiation_wrapper.setCameraSpectralResponse(self.radiation_model, camera_label, band_label, global_data)
        logger.debug(f"Set spectral response for camera '{camera_label}', band '{band_label}'")

    @require_plugin('radiation', 'configure camera from library')
    def setCameraSpectralResponseFromLibrary(self, camera_label: str, camera_library_name: str):
        """
        Set camera spectral response from standard camera library.

        Uses pre-defined spectral response curves for common cameras.

        Args:
            camera_label: Camera label
            camera_library_name: Standard camera name (e.g., "iPhone13", "NikonD850", "CanonEOS5D")

        Example:
            >>> radiation.setCameraSpectralResponseFromLibrary("cam1", "iPhone13")
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        if not isinstance(camera_library_name, str) or not camera_library_name.strip():
            raise ValueError("Camera library name must be a non-empty string")

        radiation_wrapper.setCameraSpectralResponseFromLibrary(self.radiation_model, camera_label, camera_library_name)
        logger.debug(f"Set camera '{camera_label}' response from library: {camera_library_name}")

    @require_plugin('radiation', 'get camera pixel data')
    def getCameraPixelData(self, camera_label: str, band_label: str) -> List[float]:
        """
        Get camera pixel data for specific band.

        Retrieves raw pixel values for programmatic access and analysis.

        Args:
            camera_label: Camera label
            band_label: Band label

        Returns:
            List of pixel values

        Example:
            >>> pixels = radiation.getCameraPixelData("cam1", "red")
            >>> print(f"Mean pixel value: {sum(pixels)/len(pixels)}")
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        validate_band_label(band_label, "band_label", "getCameraPixelData")

        return radiation_wrapper.getCameraPixelData(self.radiation_model, camera_label, band_label)

    @require_plugin('radiation', 'set camera pixel data')
    def setCameraPixelData(self, camera_label: str, band_label: str, pixel_data: List[float]):
        """
        Set camera pixel data for specific band.

        Allows programmatic modification of pixel values.

        Args:
            camera_label: Camera label
            band_label: Band label
            pixel_data: List of pixel values

        Example:
            >>> pixels = radiation.getCameraPixelData("cam1", "red")
            >>> modified_pixels = [p * 1.2 for p in pixels]  # Brighten by 20%
            >>> radiation.setCameraPixelData("cam1", "red", modified_pixels)
        """
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise ValueError("Camera label must be a non-empty string")
        validate_band_label(band_label, "band_label", "setCameraPixelData")
        if not isinstance(pixel_data, (list, tuple)):
            raise ValueError("Pixel data must be a list or tuple")

        radiation_wrapper.setCameraPixelData(self.radiation_model, camera_label, band_label, pixel_data)
        logger.debug(f"Set pixel data for camera '{camera_label}', band '{band_label}': {len(pixel_data)} pixels")

    # =========================================================================
    # Camera Library Functions (v1.3.58+)
    # =========================================================================

    @require_plugin('radiation', 'add camera from library')
    def addRadiationCameraFromLibrary(self, camera_label: str, library_camera_label: str,
                                       position, lookat, antialiasing_samples: int = 1,
                                       band_labels: Optional[List[str]] = None):
        """
        Add radiation camera loading all properties from camera library.

        Loads camera intrinsic parameters (resolution, FOV, sensor size) and spectral
        response data from the camera library XML file. This is the recommended way to
        create realistic cameras with proper spectral responses.

        Args:
            camera_label: Label for the camera instance
            library_camera_label: Label of camera in library (e.g., "Canon_20D", "iPhone11", "NikonD700")
            position: Camera position as vec3 or (x, y, z) tuple
            lookat: Lookat point as vec3 or (x, y, z) tuple
            antialiasing_samples: Number of ray samples per pixel. Default: 1
            band_labels: Optional custom band labels. If None, uses library defaults.

        Raises:
            RadiationModelError: If operation fails
            ValueError: If parameters are invalid

        Note:
            Available cameras in plugins/radiation/camera_library/camera_library.xml include:
            - Canon_20D, Nikon_D700, Nikon_D50
            - iPhone11, iPhone12ProMAX
            - Additional cameras available in library

        Example:
            >>> radiation.addRadiationCameraFromLibrary(
            ...     camera_label="cam1",
            ...     library_camera_label="iPhone11",
            ...     position=(0, -5, 1),
            ...     lookat=(0, 0, 0.5),
            ...     antialiasing_samples=10
            ... )
        """
        validate_band_label(camera_label, "camera_label", "addRadiationCameraFromLibrary")

        try:
            radiation_wrapper.addRadiationCameraFromLibrary(
                self.radiation_model, camera_label, library_camera_label,
                position, lookat, antialiasing_samples, band_labels
            )
            logger.info(f"Added camera '{camera_label}' from library '{library_camera_label}'")
        except Exception as e:
            raise RadiationModelError(f"Failed to add camera from library: {e}")

    @require_plugin('radiation', 'update camera parameters')
    def updateCameraParameters(self, camera_label: str, camera_properties: CameraProperties):
        """
        Update camera parameters for an existing camera.

        Allows modification of camera properties after creation while preserving
        position, lookat direction, and spectral band configuration.

        Args:
            camera_label: Label for the camera to update
            camera_properties: CameraProperties instance with new parameters

        Raises:
            RadiationModelError: If operation fails or camera doesn't exist
            ValueError: If parameters are invalid

        Note:
            FOV_aspect_ratio is automatically recalculated from camera_resolution.
            Camera position and lookat are preserved.

        Example:
            >>> props = CameraProperties(
            ...     camera_resolution=(1920, 1080),
            ...     HFOV=35.0,
            ...     lens_focal_length=0.085  # 85mm lens
            ... )
            >>> radiation.updateCameraParameters("cam1", props)
        """
        validate_band_label(camera_label, "camera_label", "updateCameraParameters")

        if not isinstance(camera_properties, CameraProperties):
            raise ValueError("camera_properties must be a CameraProperties instance")

        try:
            radiation_wrapper.updateCameraParameters(self.radiation_model, camera_label, camera_properties)
            logger.debug(f"Updated parameters for camera '{camera_label}'")
        except Exception as e:
            raise RadiationModelError(f"Failed to update camera parameters: {e}")

    @require_plugin('radiation', 'enable camera metadata')
    def enableCameraMetadata(self, camera_labels):
        """
        Enable automatic JSON metadata file writing for camera(s).

        When enabled, writeCameraImage() automatically creates a JSON metadata file
        alongside the image containing comprehensive camera and scene information.

        Args:
            camera_labels: Single camera label (str) or list of camera labels (List[str])

        Raises:
            RadiationModelError: If operation fails
            ValueError: If parameters are invalid

        Note:
            Metadata includes:
            - Camera properties (model, lens, sensor specs)
            - Geographic location (latitude, longitude)
            - Acquisition settings (date, time, exposure, white balance)
            - Agronomic data (plant species, heights, phenology stages)

        Example:
            >>> # Enable for single camera
            >>> radiation.enableCameraMetadata("cam1")
            >>>
            >>> # Enable for multiple cameras
            >>> radiation.enableCameraMetadata(["cam1", "cam2", "cam3"])
        """
        try:
            radiation_wrapper.enableCameraMetadata(self.radiation_model, camera_labels)
            if isinstance(camera_labels, str):
                logger.info(f"Enabled metadata for camera '{camera_labels}'")
            else:
                logger.info(f"Enabled metadata for {len(camera_labels)} cameras")
        except Exception as e:
            raise RadiationModelError(f"Failed to enable camera metadata: {e}")

    @require_plugin('radiation', 'write camera images')
    def writeCameraImage(self, camera: str, bands: List[str], imagefile_base: str,
                          image_path: str = "./", frame: int = -1,
                          flux_to_pixel_conversion: float = 1.0) -> str:
        """
        Write camera image to file and return output filename.
        
        Args:
            camera: Camera label
            bands: List of band labels to include in the image
            imagefile_base: Base filename for output
            image_path: Output directory path (default: current directory)
            frame: Frame number to write (-1 for all frames)
            flux_to_pixel_conversion: Conversion factor from flux to pixel values
            
        Returns:
            Output filename string
            
        Raises:
            RadiationModelError: If camera image writing fails
            TypeError: If parameters have incorrect types
        """
        # Validate inputs
        if not isinstance(camera, str) or not camera.strip():
            raise TypeError("Camera label must be a non-empty string")
        if not isinstance(bands, list) or not bands:
            raise TypeError("Bands must be a non-empty list of strings")
        if not all(isinstance(band, str) and band.strip() for band in bands):
            raise TypeError("All band labels must be non-empty strings")
        if not isinstance(imagefile_base, str) or not imagefile_base.strip():
            raise TypeError("Image file base must be a non-empty string")
        if not isinstance(image_path, str):
            raise TypeError("Image path must be a string")
        if not isinstance(frame, int):
            raise TypeError("Frame must be an integer")
        if not isinstance(flux_to_pixel_conversion, (int, float)) or flux_to_pixel_conversion <= 0:
            raise TypeError("Flux to pixel conversion must be a positive number")
        
        filename = radiation_wrapper.writeCameraImage(
            self.radiation_model, camera, bands, imagefile_base, 
            image_path, frame, flux_to_pixel_conversion)
        
        logger.info(f"Camera image written to: {filename}")
        return filename
    
    @require_plugin('radiation', 'write normalized camera images')
    def writeNormCameraImage(self, camera: str, bands: List[str], imagefile_base: str,
                               image_path: str = "./", frame: int = -1) -> str:
        """
        Write normalized camera image to file and return output filename.
        
        Args:
            camera: Camera label
            bands: List of band labels to include in the image
            imagefile_base: Base filename for output
            image_path: Output directory path (default: current directory)
            frame: Frame number to write (-1 for all frames)
            
        Returns:
            Output filename string
            
        Raises:
            RadiationModelError: If normalized camera image writing fails
            TypeError: If parameters have incorrect types
        """
        # Validate inputs
        if not isinstance(camera, str) or not camera.strip():
            raise TypeError("Camera label must be a non-empty string")
        if not isinstance(bands, list) or not bands:
            raise TypeError("Bands must be a non-empty list of strings")
        if not all(isinstance(band, str) and band.strip() for band in bands):
            raise TypeError("All band labels must be non-empty strings")
        if not isinstance(imagefile_base, str) or not imagefile_base.strip():
            raise TypeError("Image file base must be a non-empty string")
        if not isinstance(image_path, str):
            raise TypeError("Image path must be a string")
        if not isinstance(frame, int):
            raise TypeError("Frame must be an integer")
        
        filename = radiation_wrapper.writeNormCameraImage(
            self.radiation_model, camera, bands, imagefile_base, image_path, frame)
        
        logger.info(f"Normalized camera image written to: {filename}")
        return filename
    
    @require_plugin('radiation', 'write camera image data')
    def writeCameraImageData(self, camera: str, band: str, imagefile_base: str,
                               image_path: str = "./", frame: int = -1):
        """
        Write camera image data to file (ASCII format).
        
        Args:
            camera: Camera label
            band: Band label
            imagefile_base: Base filename for output
            image_path: Output directory path (default: current directory)
            frame: Frame number to write (-1 for all frames)
            
        Raises:
            RadiationModelError: If camera image data writing fails
            TypeError: If parameters have incorrect types
        """
        # Validate inputs
        if not isinstance(camera, str) or not camera.strip():
            raise TypeError("Camera label must be a non-empty string")
        if not isinstance(band, str) or not band.strip():
            raise TypeError("Band label must be a non-empty string")
        if not isinstance(imagefile_base, str) or not imagefile_base.strip():
            raise TypeError("Image file base must be a non-empty string")
        if not isinstance(image_path, str):
            raise TypeError("Image path must be a string")
        if not isinstance(frame, int):
            raise TypeError("Frame must be an integer")
        
        radiation_wrapper.writeCameraImageData(
            self.radiation_model, camera, band, imagefile_base, image_path, frame)
        
        logger.info(f"Camera image data written for camera {camera}, band {band}")
    
    @require_plugin('radiation', 'write image bounding boxes')
    def writeImageBoundingBoxes(self, camera_label: str,
                                  primitive_data_labels=None, object_data_labels=None,
                                  object_class_ids=None, image_file: str = "",
                                  classes_txt_file: str = "classes.txt",
                                  image_path: str = "./"):
        """
        Write image bounding boxes for object detection training.
        
        Supports both single and multiple data labels. Either provide primitive_data_labels
        or object_data_labels, not both.
        
        Args:
            camera_label: Camera label
            primitive_data_labels: Single primitive data label (str) or list of primitive data labels
            object_data_labels: Single object data label (str) or list of object data labels  
            object_class_ids: Single class ID (int) or list of class IDs (must match data labels)
            image_file: Image filename
            classes_txt_file: Classes definition file (default: "classes.txt")
            image_path: Image output path (default: current directory)
            
        Raises:
            RadiationModelError: If bounding box writing fails
            TypeError: If parameters have incorrect types
            ValueError: If both primitive and object data labels are provided, or neither
        """
        # Validate exclusive parameter usage
        if primitive_data_labels is not None and object_data_labels is not None:
            raise ValueError("Cannot specify both primitive_data_labels and object_data_labels")
        if primitive_data_labels is None and object_data_labels is None:
            raise ValueError("Must specify either primitive_data_labels or object_data_labels")
        
        # Validate common parameters
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise TypeError("Camera label must be a non-empty string")
        if not isinstance(image_file, str) or not image_file.strip():
            raise TypeError("Image file must be a non-empty string")
        if not isinstance(classes_txt_file, str):
            raise TypeError("Classes txt file must be a string")
        if not isinstance(image_path, str):
            raise TypeError("Image path must be a string")
        
        # Handle primitive data labels
        if primitive_data_labels is not None:
            if isinstance(primitive_data_labels, str):
                # Single label
                if not isinstance(object_class_ids, int):
                    raise TypeError("For single primitive data label, object_class_ids must be an integer")
                radiation_wrapper.writeImageBoundingBoxes(
                    self.radiation_model, camera_label, primitive_data_labels, 
                    object_class_ids, image_file, classes_txt_file, image_path)
                logger.info(f"Image bounding boxes written for primitive data: {primitive_data_labels}")
            
            elif isinstance(primitive_data_labels, list):
                # Multiple labels
                if not isinstance(object_class_ids, list):
                    raise TypeError("For multiple primitive data labels, object_class_ids must be a list")
                if len(primitive_data_labels) != len(object_class_ids):
                    raise ValueError("primitive_data_labels and object_class_ids must have the same length")
                if not all(isinstance(lbl, str) and lbl.strip() for lbl in primitive_data_labels):
                    raise TypeError("All primitive data labels must be non-empty strings")
                if not all(isinstance(cid, int) for cid in object_class_ids):
                    raise TypeError("All object class IDs must be integers")
                
                radiation_wrapper.writeImageBoundingBoxesVector(
                    self.radiation_model, camera_label, primitive_data_labels, 
                    object_class_ids, image_file, classes_txt_file, image_path)
                logger.info(f"Image bounding boxes written for {len(primitive_data_labels)} primitive data labels")
            else:
                raise TypeError("primitive_data_labels must be a string or list of strings")
        
        # Handle object data labels  
        elif object_data_labels is not None:
            if isinstance(object_data_labels, str):
                # Single label
                if not isinstance(object_class_ids, int):
                    raise TypeError("For single object data label, object_class_ids must be an integer")
                radiation_wrapper.writeImageBoundingBoxes_ObjectData(
                    self.radiation_model, camera_label, object_data_labels, 
                    object_class_ids, image_file, classes_txt_file, image_path)
                logger.info(f"Image bounding boxes written for object data: {object_data_labels}")
            
            elif isinstance(object_data_labels, list):
                # Multiple labels
                if not isinstance(object_class_ids, list):
                    raise TypeError("For multiple object data labels, object_class_ids must be a list")
                if len(object_data_labels) != len(object_class_ids):
                    raise ValueError("object_data_labels and object_class_ids must have the same length")
                if not all(isinstance(lbl, str) and lbl.strip() for lbl in object_data_labels):
                    raise TypeError("All object data labels must be non-empty strings")
                if not all(isinstance(cid, int) for cid in object_class_ids):
                    raise TypeError("All object class IDs must be integers")
                
                radiation_wrapper.writeImageBoundingBoxes_ObjectDataVector(
                    self.radiation_model, camera_label, object_data_labels, 
                    object_class_ids, image_file, classes_txt_file, image_path)
                logger.info(f"Image bounding boxes written for {len(object_data_labels)} object data labels")
            else:
                raise TypeError("object_data_labels must be a string or list of strings")
    
    @require_plugin('radiation', 'write image segmentation masks')
    def writeImageSegmentationMasks(self, camera_label: str,
                                      primitive_data_labels=None, object_data_labels=None,
                                      object_class_ids=None, json_filename: str = "",
                                      image_file: str = "", append_file: bool = False):
        """
        Write image segmentation masks in COCO JSON format.
        
        Supports both single and multiple data labels. Either provide primitive_data_labels
        or object_data_labels, not both.
        
        Args:
            camera_label: Camera label
            primitive_data_labels: Single primitive data label (str) or list of primitive data labels
            object_data_labels: Single object data label (str) or list of object data labels
            object_class_ids: Single class ID (int) or list of class IDs (must match data labels)
            json_filename: JSON output filename
            image_file: Image filename
            append_file: Whether to append to existing JSON file
            
        Raises:
            RadiationModelError: If segmentation mask writing fails
            TypeError: If parameters have incorrect types
            ValueError: If both primitive and object data labels are provided, or neither
        """
        # Validate exclusive parameter usage
        if primitive_data_labels is not None and object_data_labels is not None:
            raise ValueError("Cannot specify both primitive_data_labels and object_data_labels")
        if primitive_data_labels is None and object_data_labels is None:
            raise ValueError("Must specify either primitive_data_labels or object_data_labels")
        
        # Validate common parameters
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise TypeError("Camera label must be a non-empty string")
        if not isinstance(json_filename, str) or not json_filename.strip():
            raise TypeError("JSON filename must be a non-empty string")
        if not isinstance(image_file, str) or not image_file.strip():
            raise TypeError("Image file must be a non-empty string")
        if not isinstance(append_file, bool):
            raise TypeError("append_file must be a boolean")
        
        # Handle primitive data labels
        if primitive_data_labels is not None:
            if isinstance(primitive_data_labels, str):
                # Single label
                if not isinstance(object_class_ids, int):
                    raise TypeError("For single primitive data label, object_class_ids must be an integer")
                radiation_wrapper.writeImageSegmentationMasks(
                    self.radiation_model, camera_label, primitive_data_labels, 
                    object_class_ids, json_filename, image_file, append_file)
                logger.info(f"Image segmentation masks written for primitive data: {primitive_data_labels}")
            
            elif isinstance(primitive_data_labels, list):
                # Multiple labels
                if not isinstance(object_class_ids, list):
                    raise TypeError("For multiple primitive data labels, object_class_ids must be a list")
                if len(primitive_data_labels) != len(object_class_ids):
                    raise ValueError("primitive_data_labels and object_class_ids must have the same length")
                if not all(isinstance(lbl, str) and lbl.strip() for lbl in primitive_data_labels):
                    raise TypeError("All primitive data labels must be non-empty strings")
                if not all(isinstance(cid, int) for cid in object_class_ids):
                    raise TypeError("All object class IDs must be integers")
                
                radiation_wrapper.writeImageSegmentationMasksVector(
                    self.radiation_model, camera_label, primitive_data_labels, 
                    object_class_ids, json_filename, image_file, append_file)
                logger.info(f"Image segmentation masks written for {len(primitive_data_labels)} primitive data labels")
            else:
                raise TypeError("primitive_data_labels must be a string or list of strings")
        
        # Handle object data labels
        elif object_data_labels is not None:
            if isinstance(object_data_labels, str):
                # Single label
                if not isinstance(object_class_ids, int):
                    raise TypeError("For single object data label, object_class_ids must be an integer")
                radiation_wrapper.writeImageSegmentationMasks_ObjectData(
                    self.radiation_model, camera_label, object_data_labels, 
                    object_class_ids, json_filename, image_file, append_file)
                logger.info(f"Image segmentation masks written for object data: {object_data_labels}")
            
            elif isinstance(object_data_labels, list):
                # Multiple labels
                if not isinstance(object_class_ids, list):
                    raise TypeError("For multiple object data labels, object_class_ids must be a list")
                if len(object_data_labels) != len(object_class_ids):
                    raise ValueError("object_data_labels and object_class_ids must have the same length")
                if not all(isinstance(lbl, str) and lbl.strip() for lbl in object_data_labels):
                    raise TypeError("All object data labels must be non-empty strings")
                if not all(isinstance(cid, int) for cid in object_class_ids):
                    raise TypeError("All object class IDs must be integers")
                
                radiation_wrapper.writeImageSegmentationMasks_ObjectDataVector(
                    self.radiation_model, camera_label, object_data_labels, 
                    object_class_ids, json_filename, image_file, append_file)
                logger.info(f"Image segmentation masks written for {len(object_data_labels)} object data labels")
            else:
                raise TypeError("object_data_labels must be a string or list of strings")
    
    @require_plugin('radiation', 'auto-calibrate camera image')
    def autoCalibrateCameraImage(self, camera_label: str, red_band_label: str,
                                   green_band_label: str, blue_band_label: str,
                                   output_file_path: str, print_quality_report: bool = False,
                                   algorithm: str = "MATRIX_3X3_AUTO",
                                   ccm_export_file_path: str = "") -> str:
        """
        Auto-calibrate camera image with color correction and return output filename.
        
        Args:
            camera_label: Camera label
            red_band_label: Red band label
            green_band_label: Green band label  
            blue_band_label: Blue band label
            output_file_path: Output file path
            print_quality_report: Whether to print quality report
            algorithm: Color correction algorithm ("DIAGONAL_ONLY", "MATRIX_3X3_AUTO", "MATRIX_3X3_FORCE")
            ccm_export_file_path: Path to export color correction matrix (optional)
            
        Returns:
            Output filename string
            
        Raises:
            RadiationModelError: If auto-calibration fails
            TypeError: If parameters have incorrect types
            ValueError: If algorithm is not valid
        """
        # Validate inputs
        if not isinstance(camera_label, str) or not camera_label.strip():
            raise TypeError("Camera label must be a non-empty string")
        if not isinstance(red_band_label, str) or not red_band_label.strip():
            raise TypeError("Red band label must be a non-empty string")
        if not isinstance(green_band_label, str) or not green_band_label.strip():
            raise TypeError("Green band label must be a non-empty string")
        if not isinstance(blue_band_label, str) or not blue_band_label.strip():
            raise TypeError("Blue band label must be a non-empty string")
        if not isinstance(output_file_path, str) or not output_file_path.strip():
            raise TypeError("Output file path must be a non-empty string")
        if not isinstance(print_quality_report, bool):
            raise TypeError("print_quality_report must be a boolean")
        if not isinstance(ccm_export_file_path, str):
            raise TypeError("ccm_export_file_path must be a string")
        
        # Map algorithm string to integer (using MATRIX_3X3_AUTO = 1 as default)
        algorithm_map = {
            "DIAGONAL_ONLY": 0,
            "MATRIX_3X3_AUTO": 1,
            "MATRIX_3X3_FORCE": 2
        }
        
        if algorithm not in algorithm_map:
            raise ValueError(f"Invalid algorithm: {algorithm}. Must be one of: {list(algorithm_map.keys())}")
        
        algorithm_int = algorithm_map[algorithm]
        
        filename = radiation_wrapper.autoCalibrateCameraImage(
            self.radiation_model, camera_label, red_band_label, green_band_label,
            blue_band_label, output_file_path, print_quality_report, 
            algorithm_int, ccm_export_file_path)
        
        logger.info(f"Auto-calibrated camera image written to: {filename}")
        return filename
    
    def getPluginInfo(self) -> dict:
        """Get information about the radiation plugin."""
        registry = get_plugin_registry()
        return registry.get_plugin_capabilities('radiation')