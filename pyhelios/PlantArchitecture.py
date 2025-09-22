"""
High-level PlantArchitecture interface for PyHelios.

This module provides a user-friendly interface to the plant architecture modeling
capabilities with graceful plugin handling and informative error messages.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Union

from .Context import Context
from .plugins.registry import get_plugin_registry, require_plugin
from .wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from .wrappers.DataTypes import vec3, vec2, int2
try:
    from .validation.datatypes import validate_vec3, validate_vec2, validate_int2
except ImportError:
    # Fallback validation functions for when validation module is not available
    def validate_vec3(value, name, func):
        if hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
            return value
        if isinstance(value, (list, tuple)) and len(value) == 3:
            from .wrappers.DataTypes import vec3
            return vec3(*value)
        raise ValueError(f"{name} must be vec3 or 3-element list/tuple")

    def validate_vec2(value, name, func):
        if hasattr(value, 'x') and hasattr(value, 'y'):
            return value
        if isinstance(value, (list, tuple)) and len(value) == 2:
            from .wrappers.DataTypes import vec2
            return vec2(*value)
        raise ValueError(f"{name} must be vec2 or 2-element list/tuple")

    def validate_int2(value, name, func):
        if hasattr(value, 'x') and hasattr(value, 'y'):
            return value
        if isinstance(value, (list, tuple)) and len(value) == 2:
            from .wrappers.DataTypes import int2
            return int2(*value)
        raise ValueError(f"{name} must be int2 or 2-element list/tuple")
from .validation.core import validate_positive_value
from .assets import get_asset_manager

logger = logging.getLogger(__name__)


@contextmanager
def _plantarchitecture_working_directory():
    """
    Context manager that temporarily changes working directory to where PlantArchitecture assets are located.

    PlantArchitecture C++ code uses hardcoded relative paths like "plugins/plantarchitecture/assets/textures/"
    expecting assets relative to working directory. This manager temporarily changes to the build directory
    where assets are actually located.

    Raises:
        RuntimeError: If build directory or PlantArchitecture assets are not found, indicating a build system error.
    """
    # Find the build directory containing PlantArchitecture assets
    # Try asset manager first (works for both development and wheel installations)
    asset_manager = get_asset_manager()
    working_dir = asset_manager._get_helios_build_path()

    if working_dir and working_dir.exists():
        plantarch_assets = working_dir / 'plugins' / 'plantarchitecture'
    else:
        # For wheel installations, check packaged assets
        current_dir = Path(__file__).parent
        packaged_build = current_dir / 'assets' / 'build'

        if packaged_build.exists():
            working_dir = packaged_build
            plantarch_assets = working_dir / 'plugins' / 'plantarchitecture'
        else:
            # Fallback to development paths
            repo_root = current_dir.parent
            build_lib_dir = repo_root / 'pyhelios_build' / 'build' / 'lib'
            working_dir = build_lib_dir.parent
            plantarch_assets = working_dir / 'plugins' / 'plantarchitecture'

            if not build_lib_dir.exists():
                raise RuntimeError(
                    f"PyHelios build directory not found at {build_lib_dir}. "
                    f"PlantArchitecture requires native libraries to be built. "
                    f"Run: build_scripts/build_helios --plugins plantarchitecture"
                )

    if not plantarch_assets.exists():
        raise RuntimeError(
            f"PlantArchitecture assets not found at {plantarch_assets}. "
            f"Build system failed to copy PlantArchitecture assets. "
            f"Run: build_scripts/build_helios --clean --plugins plantarchitecture"
        )

    # Verify essential assets exist
    assets_dir = plantarch_assets / 'assets'
    if not assets_dir.exists():
        raise RuntimeError(
            f"PlantArchitecture assets directory not found: {assets_dir}. "
            f"Essential assets missing. Rebuild with: "
            f"build_scripts/build_helios --clean --plugins plantarchitecture"
        )

    # Change to the build directory temporarily
    original_dir = os.getcwd()
    try:
        os.chdir(working_dir)
        logger.debug(f"Changed working directory to {working_dir} for PlantArchitecture asset access")
        yield working_dir
    finally:
        os.chdir(original_dir)
        logger.debug(f"Restored working directory to {original_dir}")


class PlantArchitectureError(Exception):
    """Raised when PlantArchitecture operations fail."""
    pass


def is_plantarchitecture_available():
    """
    Check if PlantArchitecture plugin is available for use.

    Returns:
        bool: True if PlantArchitecture can be used, False otherwise
    """
    try:
        # Check plugin registry
        plugin_registry = get_plugin_registry()
        if not plugin_registry.is_plugin_available('plantarchitecture'):
            return False

        # Check if wrapper functions are available
        if not plantarch_wrapper._PLANTARCHITECTURE_FUNCTIONS_AVAILABLE:
            return False

        return True
    except Exception:
        return False


class PlantArchitecture:
    """
    High-level interface for plant architecture modeling and procedural plant generation.

    PlantArchitecture provides access to the comprehensive plant library with 25+ plant models
    including trees (almond, apple, olive, walnut), crops (bean, cowpea, maize, rice, soybean),
    and other plants. This class enables procedural plant generation, time-based growth
    simulation, and plant community modeling.

    This class requires the native Helios library built with PlantArchitecture support.
    Use context managers for proper resource cleanup.

    Example:
        >>> with Context() as context:
        ...     with PlantArchitecture(context) as plantarch:
        ...         plantarch.loadPlantModelFromLibrary("bean")
        ...         plant_id = plantarch.buildPlantInstanceFromLibrary([0, 0, 0], age=30)
        ...         plantarch.advanceTime(10.0)  # Grow for 10 days
    """

    def __init__(self, context: Context):
        """
        Initialize PlantArchitecture with a Helios context.

        Args:
            context: Active Helios Context instance

        Raises:
            PlantArchitectureError: If plugin not available in current build
            RuntimeError: If plugin initialization fails
        """
        # Check plugin availability
        registry = get_plugin_registry()
        if not registry.is_plugin_available('plantarchitecture'):
            raise PlantArchitectureError(
                "PlantArchitecture not available in current Helios library. "
                "Rebuild PyHelios with PlantArchitecture support:\n"
                "  build_scripts/build_helios --plugins plantarchitecture\n"
                "\n"
                "System requirements:\n"
                f"  - Platforms: Windows, Linux, macOS\n"
                "  - Dependencies: Extensive asset library (textures, OBJ models)\n"
                "  - GPU: Not required\n"
                "\n"
                "Plant library includes 25+ models: almond, apple, bean, cowpea, maize, "
                "rice, soybean, tomato, wheat, and many others."
            )

        self.context = context
        self._plantarch_ptr = None

        # Create PlantArchitecture instance with asset-aware working directory
        with _plantarchitecture_working_directory():
            self._plantarch_ptr = plantarch_wrapper.createPlantArchitecture(context.getNativePtr())

        if not self._plantarch_ptr:
            raise PlantArchitectureError("Failed to initialize PlantArchitecture")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if hasattr(self, '_plantarch_ptr') and self._plantarch_ptr:
            plantarch_wrapper.destroyPlantArchitecture(self._plantarch_ptr)
            self._plantarch_ptr = None

    def loadPlantModelFromLibrary(self, plant_label: str) -> None:
        """
        Load a plant model from the built-in library.

        Args:
            plant_label: Plant model identifier from library. Available models include:
                       "almond", "apple", "bean", "bindweed", "butterlettuce", "capsicum",
                       "cheeseweed", "cowpea", "easternredbud", "grapevine_VSP", "maize",
                       "olive", "pistachio", "puncturevine", "rice", "sorghum", "soybean",
                       "strawberry", "sugarbeet", "tomato", "cherrytomato", "walnut", "wheat"

        Raises:
            ValueError: If plant_label is empty or invalid
            PlantArchitectureError: If model loading fails

        Example:
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>> plantarch.loadPlantModelFromLibrary("almond")
        """
        if not plant_label:
            raise ValueError("Plant label cannot be empty")

        if not plant_label.strip():
            raise ValueError("Plant label cannot be only whitespace")

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.loadPlantModelFromLibrary(self._plantarch_ptr, plant_label.strip())
        except Exception as e:
            raise PlantArchitectureError(f"Failed to load plant model '{plant_label}': {e}")

    def buildPlantInstanceFromLibrary(self, base_position: Union[vec3, List[float]], age: float) -> int:
        """
        Build a plant instance from the currently loaded library model.

        Args:
            base_position: Cartesian (x,y,z) coordinates of plant base
            age: Age of the plant in days (must be >= 0)

        Returns:
            Plant ID for the created plant instance

        Raises:
            ValueError: If position format is invalid or age is negative
            PlantArchitectureError: If plant building fails
            RuntimeError: If no model has been loaded

        Example:
            >>> plant_id = plantarch.buildPlantInstanceFromLibrary([2.0, 3.0, 0.0], age=45.0)
            >>> plant_id = plantarch.buildPlantInstanceFromLibrary(vec3(0, 0, 0), age=30.0)
        """
        # Validate and convert position
        position = validate_vec3(base_position, 'base_position', 'buildPlantInstanceFromLibrary')
        position_list = [position.x, position.y, position.z]

        # Validate age (allow zero)
        if age < 0:
            raise ValueError(f"Age must be non-negative, got {age}")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.buildPlantInstanceFromLibrary(
                    self._plantarch_ptr, position_list, age
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to build plant instance: {e}")

    def buildPlantCanopyFromLibrary(self, canopy_center: Union[vec3, List[float]],
                                  plant_spacing: Union[vec2, List[float]],
                                  plant_count: Union[int2, List[int]], age: float) -> List[int]:
        """
        Build a canopy of regularly spaced plants from the currently loaded library model.

        Args:
            canopy_center: Cartesian (x,y,z) coordinates of canopy center
            plant_spacing: Spacing between plants in x- and y-directions (meters)
            plant_count: Number of plants in x- and y-directions
            age: Age of all plants in days (must be >= 0)

        Returns:
            List of plant IDs for the created plant instances

        Raises:
            ValueError: If parameters have invalid format, values, or age is negative
            PlantArchitectureError: If canopy building fails

        Example:
            >>> # 3x3 canopy with 0.5m spacing, 30-day-old plants
            >>> plant_ids = plantarch.buildPlantCanopyFromLibrary(
            ...     canopy_center=[0, 0, 0],
            ...     plant_spacing=[0.5, 0.5],
            ...     plant_count=[3, 3],
            ...     age=30.0
            ... )
        """
        # Validate and convert parameters
        center = validate_vec3(canopy_center, 'canopy_center', 'buildPlantCanopyFromLibrary')
        spacing = validate_vec2(plant_spacing, 'plant_spacing', 'buildPlantCanopyFromLibrary')
        count = validate_int2(plant_count, 'plant_count', 'buildPlantCanopyFromLibrary')
        # Validate age (allow zero)
        if age < 0:
            raise ValueError(f"Age must be non-negative, got {age}")

        # Convert to lists
        center_list = [center.x, center.y, center.z]
        spacing_list = [spacing.x, spacing.y]
        count_list = [count.x, count.y]

        # Validate count values
        if count.x <= 0 or count.y <= 0:
            raise ValueError("Plant count values must be positive integers")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.buildPlantCanopyFromLibrary(
                    self._plantarch_ptr, center_list, spacing_list, count_list, age
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to build plant canopy: {e}")

    def advanceTime(self, dt: float) -> None:
        """
        Advance time for plant growth and development.

        This method updates all plants in the simulation, potentially adding new phytomers,
        growing existing organs, transitioning phenological stages, and updating plant geometry.

        Args:
            dt: Time step to advance in days (must be >= 0)

        Raises:
            ValueError: If dt is negative
            PlantArchitectureError: If time advancement fails

        Note:
            Large time steps are more efficient than many small steps. The timestep value
            can be larger than the phyllochron, allowing multiple phytomers to be produced
            in a single call.

        Example:
            >>> plantarch.advanceTime(10.0)  # Advance 10 days
            >>> plantarch.advanceTime(0.5)   # Advance 12 hours
        """
        # Validate time step (allow zero)
        if dt < 0:
            raise ValueError(f"Time step must be non-negative, got {dt}")

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.advanceTime(self._plantarch_ptr, dt)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to advance time by {dt} days: {e}")

    def getAvailablePlantModels(self) -> List[str]:
        """
        Get list of all available plant models in the library.

        Returns:
            List of plant model names available for loading

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> models = plantarch.getAvailablePlantModels()
            >>> print(f"Available models: {', '.join(models)}")
            Available models: almond, apple, bean, cowpea, maize, rice, soybean, tomato, wheat, ...
        """
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAvailablePlantModels(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get available plant models: {e}")

    def getAllPlantObjectIDs(self, plant_id: int) -> List[int]:
        """
        Get all object IDs for a specific plant.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of object IDs comprising the plant

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> object_ids = plantarch.getAllPlantObjectIDs(plant_id)
            >>> print(f"Plant has {len(object_ids)} objects")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            return plantarch_wrapper.getAllPlantObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get object IDs for plant {plant_id}: {e}")

    def getAllPlantUUIDs(self, plant_id: int) -> List[int]:
        """
        Get all primitive UUIDs for a specific plant.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of primitive UUIDs comprising the plant

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> uuids = plantarch.getAllPlantUUIDs(plant_id)
            >>> print(f"Plant has {len(uuids)} primitives")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            return plantarch_wrapper.getAllPlantUUIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get UUIDs for plant {plant_id}: {e}")

    def is_available(self) -> bool:
        """
        Check if PlantArchitecture is available in current build.

        Returns:
            True if plugin is available, False otherwise
        """
        return is_plantarchitecture_available()


# Convenience function
def create_plant_architecture(context: Context) -> PlantArchitecture:
    """
    Create PlantArchitecture instance with context.

    Args:
        context: Helios Context

    Returns:
        PlantArchitecture instance

    Example:
        >>> context = Context()
        >>> plantarch = create_plant_architecture(context)
    """
    return PlantArchitecture(context)