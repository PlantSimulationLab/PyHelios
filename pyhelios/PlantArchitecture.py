"""
High-level PlantArchitecture interface for PyHelios.

This module provides a user-friendly interface to the plant architecture modeling
capabilities with graceful plugin handling and informative error messages.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from .Context import Context
from .plugins.registry import get_plugin_registry, require_plugin
from .wrappers import UPlantArchitectureWrapper as plantarch_wrapper
from .wrappers.DataTypes import vec3, vec2, int2, AxisRotation
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


class RandomParameter:
    """
    Helper class for creating RandomParameter specifications for float parameters.

    Provides convenient static methods to create parameter dictionaries with
    statistical distributions for plant architecture modeling.
    """

    @staticmethod
    def constant(value: float) -> Dict[str, Any]:
        """
        Create a constant (non-random) parameter.

        Args:
            value: The constant value

        Returns:
            Dict with constant distribution specification

        Example:
            >>> param = RandomParameter.constant(45.0)
            >>> # Returns: {'distribution': 'constant', 'parameters': [45.0]}
        """
        return {'distribution': 'constant', 'parameters': [float(value)]}

    @staticmethod
    def uniform(min_val: float, max_val: float) -> Dict[str, Any]:
        """
        Create a uniform distribution parameter.

        Args:
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            Dict with uniform distribution specification

        Raises:
            ValueError: If min_val > max_val

        Example:
            >>> param = RandomParameter.uniform(40.0, 50.0)
            >>> # Returns: {'distribution': 'uniform', 'parameters': [40.0, 50.0]}
        """
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")
        return {'distribution': 'uniform', 'parameters': [float(min_val), float(max_val)]}

    @staticmethod
    def normal(mean: float, std_dev: float) -> Dict[str, Any]:
        """
        Create a normal (Gaussian) distribution parameter.

        Args:
            mean: Mean value
            std_dev: Standard deviation

        Returns:
            Dict with normal distribution specification

        Raises:
            ValueError: If std_dev < 0

        Example:
            >>> param = RandomParameter.normal(45.0, 5.0)
            >>> # Returns: {'distribution': 'normal', 'parameters': [45.0, 5.0]}
        """
        if std_dev < 0:
            raise ValueError(f"std_dev ({std_dev}) must be >= 0")
        return {'distribution': 'normal', 'parameters': [float(mean), float(std_dev)]}

    @staticmethod
    def weibull(shape: float, scale: float) -> Dict[str, Any]:
        """
        Create a Weibull distribution parameter.

        Args:
            shape: Shape parameter (k)
            scale: Scale parameter (λ)

        Returns:
            Dict with Weibull distribution specification

        Raises:
            ValueError: If shape or scale <= 0

        Example:
            >>> param = RandomParameter.weibull(2.0, 50.0)
            >>> # Returns: {'distribution': 'weibull', 'parameters': [2.0, 50.0]}
        """
        if shape <= 0:
            raise ValueError(f"shape ({shape}) must be > 0")
        if scale <= 0:
            raise ValueError(f"scale ({scale}) must be > 0")
        return {'distribution': 'weibull', 'parameters': [float(shape), float(scale)]}


class RandomParameterInt:
    """
    Helper class for creating RandomParameter specifications for integer parameters.

    Provides convenient static methods to create parameter dictionaries with
    statistical distributions for integer-valued plant parameters.
    """

    @staticmethod
    def constant(value: int) -> Dict[str, Any]:
        """
        Create a constant (non-random) integer parameter.

        Args:
            value: The constant integer value

        Returns:
            Dict with constant distribution specification

        Example:
            >>> param = RandomParameterInt.constant(15)
            >>> # Returns: {'distribution': 'constant', 'parameters': [15.0]}
        """
        return {'distribution': 'constant', 'parameters': [float(value)]}

    @staticmethod
    def uniform(min_val: int, max_val: int) -> Dict[str, Any]:
        """
        Create a uniform distribution for integer parameter.

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Returns:
            Dict with uniform distribution specification

        Raises:
            ValueError: If min_val > max_val

        Example:
            >>> param = RandomParameterInt.uniform(10, 20)
            >>> # Returns: {'distribution': 'uniform', 'parameters': [10.0, 20.0]}
        """
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")
        return {'distribution': 'uniform', 'parameters': [float(min_val), float(max_val)]}

    @staticmethod
    def discrete(values: List[int]) -> Dict[str, Any]:
        """
        Create a discrete value distribution (random choice from list).

        Args:
            values: List of possible integer values (equal probability)

        Returns:
            Dict with discrete distribution specification

        Raises:
            ValueError: If values list is empty

        Example:
            >>> param = RandomParameterInt.discrete([1, 2, 3, 5])
            >>> # Returns: {'distribution': 'discretevalues', 'parameters': [1.0, 2.0, 3.0, 5.0]}
        """
        if not values:
            raise ValueError("values list cannot be empty")
        return {'distribution': 'discretevalues', 'parameters': [float(v) for v in values]}


def _resolve_user_path(filepath: Union[str, Path]) -> str:
    """
    Convert relative paths to absolute paths before changing working directory.

    This preserves the user's intended file location when the working directory
    is temporarily changed for C++ asset access. Absolute paths are returned unchanged.

    Args:
        filepath: File path to resolve (string or Path object)

    Returns:
        Absolute path as string
    """
    path = Path(filepath)
    if not path.is_absolute():
        return str(Path.cwd() / path)
    return str(path)


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
        ...         plant_id = plantarch.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=30)
        ...         plantarch.advanceTime(10.0)  # Grow for 10 days
    """

    def __new__(cls, context=None):
        """
        Create PlantArchitecture instance.
        Explicit __new__ to prevent ctypes contamination on Windows.
        """
        return object.__new__(cls)

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

    def __del__(self):
        """Destructor to ensure C++ resources freed even without 'with' statement."""
        if hasattr(self, '_plantarch_ptr') and self._plantarch_ptr is not None:
            try:
                plantarch_wrapper.destroyPlantArchitecture(self._plantarch_ptr)
                self._plantarch_ptr = None
            except Exception as e:
                import warnings
                warnings.warn(f"Error in PlantArchitecture.__del__: {e}")

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

    def buildPlantInstanceFromLibrary(self, base_position: vec3, age: float,
                                     build_parameters: Optional[dict] = None) -> int:
        """
        Build a plant instance from the currently loaded library model.

        Args:
            base_position: Cartesian (x,y,z) coordinates of plant base as vec3
            age: Age of the plant in days (must be >= 0)
            build_parameters: Optional dict of parameter overrides for training system parameters.
                            Examples:
                            - {'trunk_height': 2.5} - for tomato trellis height
                            - {'cordon_height': 1.8, 'cordon_radius': 1.2} - for apple training
                            - {'row_spacing': 0.75} - for grapevine VSP trellis

        Returns:
            Plant ID for the created plant instance

        Raises:
            ValueError: If age is negative or build_parameters is invalid
            PlantArchitectureError: If plant building fails
            RuntimeError: If no model has been loaded

        Example:
            >>> plant_id = plantarch.buildPlantInstanceFromLibrary(base_position=vec3(2.0, 3.0, 0.0), age=45.0)
            >>> # With custom parameters
            >>> plant_id = plantarch.buildPlantInstanceFromLibrary(
            ...     base_position=vec3(0, 0, 0),
            ...     age=30.0,
            ...     build_parameters={'trunk_height': 2.0}
            ... )
        """
        # Convert position to list for C++ interface
        position_list = [base_position.x, base_position.y, base_position.z]

        # Validate age (allow zero)
        if age < 0:
            raise ValueError(f"Age must be non-negative, got {age}")

        # Validate build_parameters
        if build_parameters is not None:
            if not isinstance(build_parameters, dict):
                raise ValueError("build_parameters must be a dict or None")
            for key, value in build_parameters.items():
                if not isinstance(key, str):
                    raise ValueError("build_parameters keys must be strings")
                if not isinstance(value, (int, float)):
                    raise ValueError("build_parameters values must be numeric (int or float)")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.buildPlantInstanceFromLibrary(
                    self._plantarch_ptr, position_list, age, build_parameters
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to build plant instance: {e}")

    def buildPlantCanopyFromLibrary(self, canopy_center: vec3,
                                  plant_spacing: vec2,
                                  plant_count: int2, age: float,
                                  build_parameters: Optional[dict] = None) -> List[int]:
        """
        Build a canopy of regularly spaced plants from the currently loaded library model.

        Args:
            canopy_center: Cartesian (x,y,z) coordinates of canopy center as vec3
            plant_spacing: Spacing between plants in x- and y-directions (meters) as vec2
            plant_count: Number of plants in x- and y-directions as int2
            age: Age of all plants in days (must be >= 0)
            build_parameters: Optional dict of parameter overrides for training system parameters.
                            Parameters are applied to all plants in the canopy.
                            Examples:
                            - {'cordon_height': 1.8} - for grapevine trellis height
                            - {'trunk_height': 2.5} - for tomato trellis systems

        Returns:
            List of plant IDs for the created plant instances

        Raises:
            ValueError: If age is negative, plant count values are not positive, or build_parameters is invalid
            PlantArchitectureError: If canopy building fails

        Example:
            >>> # 3x3 canopy with 0.5m spacing, 30-day-old plants
            >>> plant_ids = plantarch.buildPlantCanopyFromLibrary(
            ...     canopy_center=vec3(0, 0, 0),
            ...     plant_spacing=vec2(0.5, 0.5),
            ...     plant_count=int2(3, 3),
            ...     age=30.0
            ... )
            >>> # With custom parameters
            >>> plant_ids = plantarch.buildPlantCanopyFromLibrary(
            ...     canopy_center=vec3(0, 0, 0),
            ...     plant_spacing=vec2(1.5, 2.0),
            ...     plant_count=int2(5, 3),
            ...     age=45.0,
            ...     build_parameters={'cordon_height': 1.8}
            ... )
        """
        # Validate age (allow zero)
        if age < 0:
            raise ValueError(f"Age must be non-negative, got {age}")

        # Validate count values
        if plant_count.x <= 0 or plant_count.y <= 0:
            raise ValueError("Plant count values must be positive integers")

        # Validate build_parameters
        if build_parameters is not None:
            if not isinstance(build_parameters, dict):
                raise ValueError("build_parameters must be a dict or None")
            for key, value in build_parameters.items():
                if not isinstance(key, str):
                    raise ValueError("build_parameters keys must be strings")
                if not isinstance(value, (int, float)):
                    raise ValueError("build_parameters values must be numeric (int or float)")

        # Convert to lists for C++ interface
        center_list = [canopy_center.x, canopy_center.y, canopy_center.z]
        spacing_list = [plant_spacing.x, plant_spacing.y]
        count_list = [plant_count.x, plant_count.y]

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.buildPlantCanopyFromLibrary(
                    self._plantarch_ptr, center_list, spacing_list, count_list, age, build_parameters
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

    def getCurrentShootParameters(self, shoot_type_label: str) -> dict:
        """
        Get current shoot parameters for a shoot type.

        Returns a nested dictionary containing all shoot and phytomer parameters
        including RandomParameter specifications with distribution types.

        Args:
            shoot_type_label: Label for the shoot type (e.g., "stem", "branch")

        Returns:
            Dictionary with shoot parameters including:
            - Geometric parameters (max_nodes, insertion_angle_tip, etc.)
            - Growth parameters (phyllochron_min, elongation_rate_max, etc.)
            - Boolean flags (flowers_require_dormancy, etc.)
            - RandomParameter fields include 'distribution' and 'parameters' keys

        Raises:
            ValueError: If shoot_type_label is empty
            PlantArchitectureError: If parameter retrieval fails

        Example:
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>> params = plantarch.getCurrentShootParameters("stem")
            >>> print(params['max_nodes'])
            {'distribution': 'constant', 'parameters': [15.0]}
        """
        if not shoot_type_label:
            raise ValueError("Shoot type label cannot be empty")

        if not shoot_type_label.strip():
            raise ValueError("Shoot type label cannot be only whitespace")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getCurrentShootParameters(
                    self._plantarch_ptr, shoot_type_label.strip()
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get shoot parameters for '{shoot_type_label}': {e}")

    def defineShootType(self, shoot_type_label: str, parameters: dict) -> None:
        """
        Define a custom shoot type with specified parameters.

        Allows creating new shoot types or modifying existing ones by providing
        a parameter dictionary. Use getCurrentShootParameters() to get a template
        that can be modified.

        Args:
            shoot_type_label: Unique name for this shoot type
            parameters: Dictionary matching ShootParameters structure.
                       Use getCurrentShootParameters() to get proper structure.

        Raises:
            ValueError: If shoot_type_label is empty or parameters is not a dict
            PlantArchitectureError: If shoot type definition fails

        Example:
            >>> # Get existing parameters as template
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>> params = plantarch.getCurrentShootParameters("stem")
            >>>
            >>> # Modify parameters
            >>> params['max_nodes'] = {'distribution': 'constant', 'parameters': [20.0]}
            >>> params['insertion_angle_tip'] = {'distribution': 'uniform', 'parameters': [40.0, 50.0]}
            >>>
            >>> # Define new shoot type
            >>> plantarch.defineShootType("TallStem", params)
        """
        if not shoot_type_label:
            raise ValueError("Shoot type label cannot be empty")

        if not shoot_type_label.strip():
            raise ValueError("Shoot type label cannot be only whitespace")

        if not isinstance(parameters, dict):
            raise ValueError("Parameters must be a dict")

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.defineShootType(
                    self._plantarch_ptr, self.context.context, shoot_type_label.strip(), parameters
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to define shoot type '{shoot_type_label}': {e}")

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

    def getPlantAge(self, plant_id: int) -> float:
        """
        Get the current age of a plant in days.

        Args:
            plant_id: ID of the plant instance

        Returns:
            Plant age in days

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> age = plantarch.getPlantAge(plant_id)
            >>> print(f"Plant is {age} days old")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getPlantAge(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get age for plant {plant_id}: {e}")

    def getPlantHeight(self, plant_id: int) -> float:
        """
        Get the height of a plant in meters.

        Args:
            plant_id: ID of the plant instance

        Returns:
            Plant height in meters (vertical extent)

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> height = plantarch.getPlantHeight(plant_id)
            >>> print(f"Plant is {height:.2f}m tall")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getPlantHeight(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get height for plant {plant_id}: {e}")

    def getPlantLeafArea(self, plant_id: int) -> float:
        """
        Get the total leaf area of a plant in m².

        Args:
            plant_id: ID of the plant instance

        Returns:
            Total leaf area in square meters

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> leaf_area = plantarch.getPlantLeafArea(plant_id)
            >>> print(f"Total leaf area: {leaf_area:.3f} m²")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.sumPlantLeafArea(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get leaf area for plant {plant_id}: {e}")

    def setPlantPhenologicalThresholds(
        self,
        plant_id: int,
        time_to_dormancy_break: float,
        time_to_flower_initiation: float,
        time_to_flower_opening: float,
        time_to_fruit_set: float,
        time_to_fruit_maturity: float,
        time_to_dormancy: float,
        max_leaf_lifespan: float = 1e6
    ) -> None:
        """
        Set phenological timing thresholds for plant developmental stages.

        Controls the timing of key phenological events based on thermal time
        or calendar time depending on the plant model.

        Args:
            plant_id: ID of the plant instance
            time_to_dormancy_break: Degree-days or days until dormancy ends
            time_to_flower_initiation: Time until flower buds are initiated
            time_to_flower_opening: Time until flowers open
            time_to_fruit_set: Time until fruit begins developing
            time_to_fruit_maturity: Time until fruit reaches maturity
            time_to_dormancy: Time until plant enters dormancy
            max_leaf_lifespan: Maximum leaf lifespan in days (default: 1e6)

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If phenology setting fails

        Example:
            >>> # Set phenology for perennial fruit tree
            >>> plantarch.setPlantPhenologicalThresholds(
            ...     plant_id=plant_id,
            ...     time_to_dormancy_break=60,    # Spring: 60 degree-days
            ...     time_to_flower_initiation=90,  # Early spring flowering
            ...     time_to_flower_opening=105,    # Bloom period
            ...     time_to_fruit_set=120,         # Fruit set after pollination
            ...     time_to_fruit_maturity=200,    # Summer fruit maturation
            ...     time_to_dormancy=280,          # Fall dormancy
            ...     max_leaf_lifespan=180          # Deciduous - 6 month leaf life
            ... )
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.setPlantPhenologicalThresholds(
                    self._plantarch_ptr,
                    plant_id,
                    time_to_dormancy_break,
                    time_to_flower_initiation,
                    time_to_flower_opening,
                    time_to_fruit_set,
                    time_to_fruit_maturity,
                    time_to_dormancy,
                    max_leaf_lifespan
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set phenological thresholds for plant {plant_id}: {e}")

    # Collision detection methods
    def enableSoftCollisionAvoidance(self,
                                    target_object_UUIDs: Optional[List[int]] = None,
                                    target_object_IDs: Optional[List[int]] = None,
                                    enable_petiole_collision: bool = False,
                                    enable_fruit_collision: bool = False) -> None:
        """
        Enable soft collision avoidance for procedural plant growth.

        This method enables the collision detection system that guides plant growth away from
        obstacles and other plants. The system uses cone-based gap detection to find optimal
        growth directions that minimize collisions while maintaining natural plant architecture.

        Args:
            target_object_UUIDs: List of primitive UUIDs to avoid collisions with. If empty,
                                avoids all geometry in the context.
            target_object_IDs: List of compound object IDs to avoid collisions with.
            enable_petiole_collision: Enable collision detection for leaf petioles
            enable_fruit_collision: Enable collision detection for fruit organs

        Raises:
            PlantArchitectureError: If collision detection activation fails

        Note:
            Collision detection adds computational overhead. Use setStaticObstacles() to mark
            static geometry for BVH optimization and improved performance.

        Example:
            >>> # Avoid all geometry
            >>> plantarch.enableSoftCollisionAvoidance()
            >>>
            >>> # Avoid specific obstacles
            >>> obstacle_uuids = context.getAllUUIDs()
            >>> plantarch.enableSoftCollisionAvoidance(target_object_UUIDs=obstacle_uuids)
            >>>
            >>> # Enable collision detection for petioles and fruit
            >>> plantarch.enableSoftCollisionAvoidance(
            ...     enable_petiole_collision=True,
            ...     enable_fruit_collision=True
            ... )
        """
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.enableSoftCollisionAvoidance(
                    self._plantarch_ptr,
                    target_UUIDs=target_object_UUIDs,
                    target_IDs=target_object_IDs,
                    enable_petiole=enable_petiole_collision,
                    enable_fruit=enable_fruit_collision
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to enable soft collision avoidance: {e}")

    def disableCollisionDetection(self) -> None:
        """
        Disable collision detection for plant growth.

        This method turns off the collision detection system, allowing plants to grow
        without checking for obstacles. This improves performance but plants may grow
        through obstacles and other geometry.

        Raises:
            PlantArchitectureError: If disabling fails

        Example:
            >>> plantarch.disableCollisionDetection()
        """
        try:
            plantarch_wrapper.disableCollisionDetection(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to disable collision detection: {e}")

    def setSoftCollisionAvoidanceParameters(self,
                                           view_half_angle_deg: float = 80.0,
                                           look_ahead_distance: float = 0.1,
                                           sample_count: int = 256,
                                           inertia_weight: float = 0.4) -> None:
        """
        Configure parameters for soft collision avoidance algorithm.

        These parameters control the cone-based gap detection algorithm that guides
        plant growth away from obstacles. Adjusting these values allows fine-tuning
        the balance between collision avoidance and natural growth patterns.

        Args:
            view_half_angle_deg: Half-angle of detection cone in degrees (0-180).
                                Default 80° provides wide field of view.
            look_ahead_distance: Distance to look ahead for collisions in meters.
                                Larger values detect distant obstacles. Default 0.1m.
            sample_count: Number of ray samples within cone. More samples improve
                         accuracy but reduce performance. Default 256.
            inertia_weight: Weight for previous growth direction (0-1). Higher values
                           make growth smoother but less responsive. Default 0.4.

        Raises:
            ValueError: If parameters are outside valid ranges
            PlantArchitectureError: If parameter setting fails

        Example:
            >>> # Use default parameters (recommended)
            >>> plantarch.setSoftCollisionAvoidanceParameters()
            >>>
            >>> # Tune for dense canopy with close obstacles
            >>> plantarch.setSoftCollisionAvoidanceParameters(
            ...     view_half_angle_deg=60.0,  # Narrower detection cone
            ...     look_ahead_distance=0.05,   # Shorter look-ahead
            ...     sample_count=512,           # More accurate detection
            ...     inertia_weight=0.3          # More responsive to obstacles
            ... )
        """
        # Validate parameters
        if not (0 <= view_half_angle_deg <= 180):
            raise ValueError(f"view_half_angle_deg must be between 0 and 180, got {view_half_angle_deg}")
        if look_ahead_distance <= 0:
            raise ValueError(f"look_ahead_distance must be positive, got {look_ahead_distance}")
        if sample_count <= 0:
            raise ValueError(f"sample_count must be positive, got {sample_count}")
        if not (0 <= inertia_weight <= 1):
            raise ValueError(f"inertia_weight must be between 0 and 1, got {inertia_weight}")

        try:
            plantarch_wrapper.setSoftCollisionAvoidanceParameters(
                self._plantarch_ptr,
                view_half_angle_deg,
                look_ahead_distance,
                sample_count,
                inertia_weight
            )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set collision avoidance parameters: {e}")

    def setCollisionRelevantOrgans(self,
                                  include_internodes: bool = False,
                                  include_leaves: bool = True,
                                  include_petioles: bool = False,
                                  include_flowers: bool = False,
                                  include_fruit: bool = False) -> None:
        """
        Specify which plant organs participate in collision detection.

        This method allows filtering which organs are considered during collision detection,
        enabling optimization by excluding organs unlikely to cause problematic collisions.

        Args:
            include_internodes: Include stem internodes in collision detection
            include_leaves: Include leaf blades in collision detection
            include_petioles: Include leaf petioles in collision detection
            include_flowers: Include flowers in collision detection
            include_fruit: Include fruit in collision detection

        Raises:
            PlantArchitectureError: If organ filtering fails

        Example:
            >>> # Only detect collisions for stems and leaves (default behavior)
            >>> plantarch.setCollisionRelevantOrgans(
            ...     include_internodes=True,
            ...     include_leaves=True
            ... )
            >>>
            >>> # Include all organs
            >>> plantarch.setCollisionRelevantOrgans(
            ...     include_internodes=True,
            ...     include_leaves=True,
            ...     include_petioles=True,
            ...     include_flowers=True,
            ...     include_fruit=True
            ... )
        """
        try:
            plantarch_wrapper.setCollisionRelevantOrgans(
                self._plantarch_ptr,
                include_internodes,
                include_leaves,
                include_petioles,
                include_flowers,
                include_fruit
            )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set collision-relevant organs: {e}")

    def enableSolidObstacleAvoidance(self,
                                    obstacle_UUIDs: List[int],
                                    avoidance_distance: float = 0.5,
                                    enable_fruit_adjustment: bool = False,
                                    enable_obstacle_pruning: bool = False) -> None:
        """
        Enable hard obstacle avoidance for specified geometry.

        This method configures solid obstacles that plants cannot grow through. Unlike soft
        collision avoidance (which guides growth), solid obstacles cause complete growth
        termination when encountered within the avoidance distance.

        Args:
            obstacle_UUIDs: List of primitive UUIDs representing solid obstacles
            avoidance_distance: Minimum distance to maintain from obstacles (meters).
                               Growth stops if obstacles are closer. Default 0.5m.
            enable_fruit_adjustment: Adjust fruit positions away from obstacles
            enable_obstacle_pruning: Remove plant organs that penetrate obstacles

        Raises:
            ValueError: If obstacle_UUIDs is empty or avoidance_distance is non-positive
            PlantArchitectureError: If solid obstacle configuration fails

        Example:
            >>> # Simple solid obstacle avoidance
            >>> wall_uuids = [1, 2, 3, 4]  # UUIDs of wall primitives
            >>> plantarch.enableSolidObstacleAvoidance(wall_uuids)
            >>>
            >>> # Close avoidance with fruit adjustment
            >>> plantarch.enableSolidObstacleAvoidance(
            ...     obstacle_UUIDs=wall_uuids,
            ...     avoidance_distance=0.1,
            ...     enable_fruit_adjustment=True
            ... )
        """
        if not obstacle_UUIDs:
            raise ValueError("Obstacle UUIDs list cannot be empty")
        if avoidance_distance <= 0:
            raise ValueError(f"avoidance_distance must be positive, got {avoidance_distance}")

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.enableSolidObstacleAvoidance(
                    self._plantarch_ptr,
                    obstacle_UUIDs,
                    avoidance_distance,
                    enable_fruit_adjustment,
                    enable_obstacle_pruning
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to enable solid obstacle avoidance: {e}")

    def setStaticObstacles(self, target_UUIDs: List[int]) -> None:
        """
        Mark geometry as static obstacles for collision detection optimization.

        This method tells the collision detection system that certain geometry will not
        move during the simulation. The system can then build an optimized Bounding Volume
        Hierarchy (BVH) for these obstacles, significantly improving collision detection
        performance in scenes with many static obstacles.

        Args:
            target_UUIDs: List of primitive UUIDs representing static obstacles

        Raises:
            ValueError: If target_UUIDs is empty
            PlantArchitectureError: If static obstacle configuration fails

        Note:
            Call this method BEFORE enabling collision avoidance for best performance.
            Static obstacles cannot be modified or moved after being marked static.

        Example:
            >>> # Mark ground and building geometry as static
            >>> static_uuids = ground_uuids + building_uuids
            >>> plantarch.setStaticObstacles(static_uuids)
            >>> # Now enable collision avoidance
            >>> plantarch.enableSoftCollisionAvoidance()
        """
        if not target_UUIDs:
            raise ValueError("target_UUIDs list cannot be empty")

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.setStaticObstacles(self._plantarch_ptr, target_UUIDs)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set static obstacles: {e}")

    def getPlantCollisionRelevantObjectIDs(self, plant_id: int) -> List[int]:
        """
        Get object IDs of collision-relevant geometry for a specific plant.

        This method returns the subset of plant geometry that participates in collision
        detection, as filtered by setCollisionRelevantOrgans(). Useful for visualization
        and debugging collision detection behavior.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of object IDs for collision-relevant plant geometry

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> # Get collision-relevant geometry
            >>> collision_obj_ids = plantarch.getPlantCollisionRelevantObjectIDs(plant_id)
            >>> print(f"Plant has {len(collision_obj_ids)} collision-relevant objects")
            >>>
            >>> # Highlight collision geometry in visualization
            >>> for obj_id in collision_obj_ids:
            ...     context.setObjectColor(obj_id, RGBcolor(1, 0, 0))  # Red
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            return plantarch_wrapper.getPlantCollisionRelevantObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get collision-relevant object IDs for plant {plant_id}: {e}")

    # File I/O methods
    def writePlantMeshVertices(self, plant_id: int, filename: Union[str, Path]) -> None:
        """
        Write all plant mesh vertices to file for external processing.

        This method exports all vertex coordinates (x,y,z) for every primitive in the plant,
        writing one vertex per line. Useful for external processing such as computing bounding
        volumes, convex hulls, or performing custom geometric analysis.

        Args:
            plant_id: ID of the plant instance to export
            filename: Path to output file (absolute or relative to current working directory)

        Raises:
            ValueError: If plant_id is negative or filename is empty
            PlantArchitectureError: If plant doesn't exist or file cannot be written

        Example:
            >>> # Export vertices for convex hull analysis
            >>> plantarch.writePlantMeshVertices(plant_id, "plant_vertices.txt")
            >>>
            >>> # Use with Path object
            >>> from pathlib import Path
            >>> output_dir = Path("output")
            >>> output_dir.mkdir(exist_ok=True)
            >>> plantarch.writePlantMeshVertices(plant_id, output_dir / "vertices.txt")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Resolve path before changing directory
        absolute_path = _resolve_user_path(filename)

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.writePlantMeshVertices(
                    self._plantarch_ptr, plant_id, absolute_path
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to write plant mesh vertices to {filename}: {e}")

    def writePlantStructureXML(self, plant_id: int, filename: Union[str, Path]) -> None:
        """
        Save plant structure to XML file for later loading.

        This method exports the complete plant architecture to an XML file, including
        all shoots, phytomers, organs, and their properties. The saved plant can be
        reloaded later using readPlantStructureXML().

        Args:
            plant_id: ID of the plant instance to save
            filename: Path to output XML file (absolute or relative to current working directory)

        Raises:
            ValueError: If plant_id is negative or filename is empty
            PlantArchitectureError: If plant doesn't exist or file cannot be written

        Note:
            The XML format preserves the complete plant state including:
            - Shoot structure and hierarchy
            - Phytomer properties and development stage
            - Organ geometry and attributes
            - Growth parameters and phenological state

        Example:
            >>> # Save plant at current growth stage
            >>> plantarch.writePlantStructureXML(plant_id, "bean_day30.xml")
            >>>
            >>> # Later, reload the saved plant
            >>> loaded_plant_ids = plantarch.readPlantStructureXML("bean_day30.xml")
            >>> print(f"Loaded {len(loaded_plant_ids)} plants")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Resolve path before changing directory
        absolute_path = _resolve_user_path(filename)

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.writePlantStructureXML(
                    self._plantarch_ptr, plant_id, absolute_path
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to write plant structure XML to {filename}: {e}")

    def writeQSMCylinderFile(self, plant_id: int, filename: Union[str, Path]) -> None:
        """
        Export plant structure in TreeQSM cylinder format.

        This method writes the plant structure as a series of cylinders following the
        TreeQSM format (Raumonen et al., 2013). Each row represents one cylinder with
        columns for radius, length, start position, axis direction, branch topology,
        and other structural properties. Useful for biomechanical analysis and
        quantitative structure modeling.

        Args:
            plant_id: ID of the plant instance to export
            filename: Path to output file (absolute or relative, typically .txt extension)

        Raises:
            ValueError: If plant_id is negative or filename is empty
            PlantArchitectureError: If plant doesn't exist or file cannot be written

        Note:
            The TreeQSM format includes columns for:
            - Cylinder dimensions (radius, length)
            - Spatial position and orientation
            - Branch topology (parent ID, extension ID, branch ID)
            - Branch hierarchy (branch order, position in branch)
            - Quality metrics (mean absolute distance, surface coverage)

        Example:
            >>> # Export for biomechanical analysis
            >>> plantarch.writeQSMCylinderFile(plant_id, "tree_structure_qsm.txt")
            >>>
            >>> # Use with external QSM tools
            >>> import pandas as pd
            >>> qsm_data = pd.read_csv("tree_structure_qsm.txt", sep="\\t")
            >>> print(f"Tree has {len(qsm_data)} cylinders")

        References:
            Raumonen et al. (2013) "Fast Automatic Precision Tree Models from
            Terrestrial Laser Scanner Data" Remote Sensing 5(2):491-520
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Resolve path before changing directory
        absolute_path = _resolve_user_path(filename)

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.writeQSMCylinderFile(
                    self._plantarch_ptr, plant_id, absolute_path
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to write QSM cylinder file to {filename}: {e}")

    def readPlantStructureXML(self, filename: Union[str, Path], quiet: bool = False) -> List[int]:
        """
        Load plant structure from XML file.

        This method reads plant architecture data from an XML file previously saved with
        writePlantStructureXML(). The loaded plants are added to the current context
        and can be grown, modified, or analyzed like any other plants.

        Args:
            filename: Path to XML file to load (absolute or relative to current working directory)
            quiet: If True, suppress console output during loading (default: False)

        Returns:
            List of plant IDs for the loaded plant instances

        Raises:
            ValueError: If filename is empty
            PlantArchitectureError: If file doesn't exist, cannot be parsed, or loading fails

        Note:
            The XML file can contain multiple plant instances. All plants in the file
            will be loaded and their IDs returned in a list. Plant models referenced
            in the XML must be available in the plant library.

        Example:
            >>> # Load previously saved plants
            >>> plant_ids = plantarch.readPlantStructureXML("saved_canopy.xml")
            >>> print(f"Loaded {len(plant_ids)} plants")
            >>>
            >>> # Continue growing the loaded plants
            >>> plantarch.advanceTime(10.0)
            >>>
            >>> # Load quietly without console messages
            >>> plant_ids = plantarch.readPlantStructureXML("bean_day45.xml", quiet=True)
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Resolve path before changing directory
        absolute_path = _resolve_user_path(filename)

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.readPlantStructureXML(
                    self._plantarch_ptr, absolute_path, quiet
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to read plant structure XML from {filename}: {e}")

    # Custom plant building methods
    def addPlantInstance(self, base_position: vec3, current_age: float) -> int:
        """
        Create an empty plant instance for custom plant building.

        This method creates a new plant instance at the specified location without any
        shoots or organs. Use addBaseStemShoot(), appendShoot(), and addChildShoot() to
        manually construct the plant structure. This provides low-level control over
        plant architecture, enabling custom morphologies not available in the plant library.

        Args:
            base_position: Cartesian (x,y,z) coordinates of plant base as vec3
            current_age: Current age of the plant in days (must be >= 0)

        Returns:
            Plant ID for the created plant instance

        Raises:
            ValueError: If age is negative
            PlantArchitectureError: If plant creation fails

        Example:
            >>> # Create empty plant at origin
            >>> plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
            >>>
            >>> # Now add shoots to build custom plant structure
            >>> shoot_id = plantarch.addBaseStemShoot(
            ...     plant_id, 1, AxisRotation(0, 0, 0), 0.01, 0.1, 1.0, 1.0, 0.8, "mainstem"
            ... )
        """
        # Convert position to list for C++ interface
        position_list = [base_position.x, base_position.y, base_position.z]

        # Validate age
        if current_age < 0:
            raise ValueError(f"Age must be non-negative, got {current_age}")

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.addPlantInstance(
                    self._plantarch_ptr, position_list, current_age
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to add plant instance: {e}")

    def deletePlantInstance(self, plant_id: int) -> None:
        """
        Delete a plant instance and all associated geometry.

        This method removes a plant from the simulation, deleting all shoots, organs,
        and associated primitives from the context. The plant ID becomes invalid after
        deletion and should not be used in subsequent operations.

        Args:
            plant_id: ID of the plant instance to delete

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If plant deletion fails or plant doesn't exist

        Example:
            >>> # Delete a plant
            >>> plantarch.deletePlantInstance(plant_id)
            >>>
            >>> # Delete multiple plants
            >>> for pid in plant_ids_to_remove:
            ...     plantarch.deletePlantInstance(pid)
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.deletePlantInstance(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to delete plant instance {plant_id}: {e}")

    def addBaseStemShoot(self,
                        plant_id: int,
                        current_node_number: int,
                        base_rotation: AxisRotation,
                        internode_radius: float,
                        internode_length_max: float,
                        internode_length_scale_factor_fraction: float,
                        leaf_scale_factor_fraction: float,
                        radius_taper: float,
                        shoot_type_label: str) -> int:
        """
        Add a base stem shoot to a plant instance (main trunk/stem).

        This method creates the primary shoot originating from the plant base. The base stem
        is typically the main trunk or primary stem from which all other shoots branch.
        Specify growth parameters to control the shoot's morphology and development.

        **IMPORTANT - Shoot Type Requirement**: Shoot types must be defined before use. The standard
        workflow is to load a plant model first using loadPlantModelFromLibrary(), which defines
        shoot types that can then be used for custom building. The shoot_type_label must match a
        shoot type defined in the loaded model.

        Args:
            plant_id: ID of the plant instance
            current_node_number: Starting node number for this shoot (typically 1)
            base_rotation: Orientation as AxisRotation(pitch, yaw, roll) in degrees
            internode_radius: Base radius of internodes in meters (must be > 0)
            internode_length_max: Maximum internode length in meters (must be > 0)
            internode_length_scale_factor_fraction: Scale factor for internode length (0-1 typically)
            leaf_scale_factor_fraction: Scale factor for leaf size (0-1 typically)
            radius_taper: Rate of radius decrease along shoot (0-1, where 1=no taper)
            shoot_type_label: Label identifying shoot type - must match a type from loaded model

        Returns:
            Shoot ID for the created shoot

        Raises:
            ValueError: If parameters are invalid (negative IDs, non-positive dimensions, empty label)
            PlantArchitectureError: If shoot creation fails or shoot type doesn't exist

        Example:
            >>> from pyhelios import AxisRotation
            >>>
            >>> # REQUIRED: Load a plant model to define shoot types
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>>
            >>> # Create empty plant for custom building
            >>> plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
            >>>
            >>> # Add base stem using shoot type from loaded model
            >>> shoot_id = plantarch.addBaseStemShoot(
            ...     plant_id=plant_id,
            ...     current_node_number=1,
            ...     base_rotation=AxisRotation(0, 0, 0),  # Upright
            ...     internode_radius=0.01,       # 1cm radius
            ...     internode_length_max=0.1,    # 10cm max length
            ...     internode_length_scale_factor_fraction=1.0,
            ...     leaf_scale_factor_fraction=1.0,
            ...     radius_taper=0.9,            # Gradual taper
            ...     shoot_type_label="stem"      # Must match loaded model
            ... )
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if current_node_number < 0:
            raise ValueError("Current node number must be non-negative")
        if internode_radius <= 0:
            raise ValueError(f"Internode radius must be positive, got {internode_radius}")
        if internode_length_max <= 0:
            raise ValueError(f"Internode length max must be positive, got {internode_length_max}")
        if not shoot_type_label or not shoot_type_label.strip():
            raise ValueError("Shoot type label cannot be empty")

        # Convert rotation to list for C++ interface
        rotation_list = base_rotation.to_list()

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.addBaseStemShoot(
                    self._plantarch_ptr, plant_id, current_node_number, rotation_list,
                    internode_radius, internode_length_max,
                    internode_length_scale_factor_fraction, leaf_scale_factor_fraction,
                    radius_taper, shoot_type_label.strip()
                )
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() and "shoot type" in error_msg.lower():
                raise PlantArchitectureError(
                    f"Shoot type '{shoot_type_label}' not defined. "
                    f"Load a plant model first to define shoot types:\n"
                    f"  plantarch.loadPlantModelFromLibrary('bean')  # or other model\n"
                    f"Original error: {e}"
                )
            raise PlantArchitectureError(f"Failed to add base stem shoot: {e}")

    def appendShoot(self,
                   plant_id: int,
                   parent_shoot_id: int,
                   current_node_number: int,
                   base_rotation: AxisRotation,
                   internode_radius: float,
                   internode_length_max: float,
                   internode_length_scale_factor_fraction: float,
                   leaf_scale_factor_fraction: float,
                   radius_taper: float,
                   shoot_type_label: str) -> int:
        """
        Append a shoot to the end of an existing shoot.

        This method extends an existing shoot by appending a new shoot at its terminal bud.
        Useful for creating multi-segmented shoots with varying properties along their length,
        such as shoots with different growth phases or developmental stages.

        **IMPORTANT - Shoot Type Requirement**: The shoot_type_label must match a shoot type
        defined in a loaded plant model. Load a model with loadPlantModelFromLibrary() before
        calling this method.

        Args:
            plant_id: ID of the plant instance
            parent_shoot_id: ID of the parent shoot to extend
            current_node_number: Starting node number for this shoot
            base_rotation: Orientation as AxisRotation(pitch, yaw, roll) in degrees
            internode_radius: Base radius of internodes in meters (must be > 0)
            internode_length_max: Maximum internode length in meters (must be > 0)
            internode_length_scale_factor_fraction: Scale factor for internode length (0-1 typically)
            leaf_scale_factor_fraction: Scale factor for leaf size (0-1 typically)
            radius_taper: Rate of radius decrease along shoot (0-1, where 1=no taper)
            shoot_type_label: Label identifying shoot type - must match loaded model

        Returns:
            Shoot ID for the appended shoot

        Raises:
            ValueError: If parameters are invalid (negative IDs, non-positive dimensions, empty label)
            PlantArchitectureError: If shoot appending fails, parent doesn't exist, or shoot type not defined

        Example:
            >>> # Load model to define shoot types
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>>
            >>> # Append shoot with reduced size to simulate apical growth
            >>> new_shoot_id = plantarch.appendShoot(
            ...     plant_id=plant_id,
            ...     parent_shoot_id=base_shoot_id,
            ...     current_node_number=10,
            ...     base_rotation=AxisRotation(0, 0, 0),
            ...     internode_radius=0.008,      # Smaller than base
            ...     internode_length_max=0.08,   # Shorter internodes
            ...     internode_length_scale_factor_fraction=1.0,
            ...     leaf_scale_factor_fraction=0.8,  # Smaller leaves
            ...     radius_taper=0.85,
            ...     shoot_type_label="stem"
            ... )
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if parent_shoot_id < 0:
            raise ValueError("Parent shoot ID must be non-negative")
        if current_node_number < 0:
            raise ValueError("Current node number must be non-negative")
        if internode_radius <= 0:
            raise ValueError(f"Internode radius must be positive, got {internode_radius}")
        if internode_length_max <= 0:
            raise ValueError(f"Internode length max must be positive, got {internode_length_max}")
        if not shoot_type_label or not shoot_type_label.strip():
            raise ValueError("Shoot type label cannot be empty")

        # Convert rotation to list for C++ interface
        rotation_list = base_rotation.to_list()

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.appendShoot(
                    self._plantarch_ptr, plant_id, parent_shoot_id, current_node_number,
                    rotation_list, internode_radius, internode_length_max,
                    internode_length_scale_factor_fraction, leaf_scale_factor_fraction,
                    radius_taper, shoot_type_label.strip()
                )
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() and "shoot type" in error_msg.lower():
                raise PlantArchitectureError(
                    f"Shoot type '{shoot_type_label}' not defined. "
                    f"Load a plant model first to define shoot types:\n"
                    f"  plantarch.loadPlantModelFromLibrary('bean')  # or other model\n"
                    f"Original error: {e}"
                )
            raise PlantArchitectureError(f"Failed to append shoot: {e}")

    def addChildShoot(self,
                     plant_id: int,
                     parent_shoot_id: int,
                     parent_node_index: int,
                     current_node_number: int,
                     shoot_base_rotation: AxisRotation,
                     internode_radius: float,
                     internode_length_max: float,
                     internode_length_scale_factor_fraction: float,
                     leaf_scale_factor_fraction: float,
                     radius_taper: float,
                     shoot_type_label: str,
                     petiole_index: int = 0) -> int:
        """
        Add a child shoot at an axillary bud position on a parent shoot.

        This method creates a lateral branch shoot emerging from a specific node on the
        parent shoot. Child shoots enable creation of branching architectures, with control
        over branch angle, size, and which petiole position the branch emerges from (for
        plants with multiple petioles per node).

        **IMPORTANT - Shoot Type Requirement**: The shoot_type_label must match a shoot type
        defined in a loaded plant model. Load a model with loadPlantModelFromLibrary() before
        calling this method.

        Args:
            plant_id: ID of the plant instance
            parent_shoot_id: ID of the parent shoot
            parent_node_index: Index of the parent node where child emerges (0-based)
            current_node_number: Starting node number for this child shoot
            shoot_base_rotation: Orientation as AxisRotation(pitch, yaw, roll) in degrees
            internode_radius: Base radius of child shoot internodes in meters (must be > 0)
            internode_length_max: Maximum internode length in meters (must be > 0)
            internode_length_scale_factor_fraction: Scale factor for internode length (0-1 typically)
            leaf_scale_factor_fraction: Scale factor for leaf size (0-1 typically)
            radius_taper: Rate of radius decrease along shoot (0-1, where 1=no taper)
            shoot_type_label: Label identifying shoot type - must match loaded model
            petiole_index: Which petiole at the node to branch from (default: 0)

        Returns:
            Shoot ID for the created child shoot

        Raises:
            ValueError: If parameters are invalid (negative values, non-positive dimensions, empty label)
            PlantArchitectureError: If child shoot creation fails, parent doesn't exist, or shoot type not defined

        Example:
            >>> # Load model to define shoot types
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>>
            >>> # Add lateral branch at 45-degree angle from node 3
            >>> branch_id = plantarch.addChildShoot(
            ...     plant_id=plant_id,
            ...     parent_shoot_id=main_shoot_id,
            ...     parent_node_index=3,
            ...     current_node_number=1,
            ...     shoot_base_rotation=AxisRotation(45, 90, 0),  # 45° out, 90° rotation
            ...     internode_radius=0.005,      # Thinner than main stem
            ...     internode_length_max=0.06,   # Shorter internodes
            ...     internode_length_scale_factor_fraction=1.0,
            ...     leaf_scale_factor_fraction=0.9,
            ...     radius_taper=0.8,
            ...     shoot_type_label="stem"
            ... )
            >>>
            >>> # Add second branch from opposite petiole
            >>> branch_id2 = plantarch.addChildShoot(
            ...     plant_id, main_shoot_id, 3, 1, AxisRotation(45, 270, 0),
            ...     0.005, 0.06, 1.0, 0.9, 0.8, "stem", petiole_index=1
            ... )
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if parent_shoot_id < 0:
            raise ValueError("Parent shoot ID must be non-negative")
        if parent_node_index < 0:
            raise ValueError("Parent node index must be non-negative")
        if current_node_number < 0:
            raise ValueError("Current node number must be non-negative")
        if internode_radius <= 0:
            raise ValueError(f"Internode radius must be positive, got {internode_radius}")
        if internode_length_max <= 0:
            raise ValueError(f"Internode length max must be positive, got {internode_length_max}")
        if not shoot_type_label or not shoot_type_label.strip():
            raise ValueError("Shoot type label cannot be empty")
        if petiole_index < 0:
            raise ValueError(f"Petiole index must be non-negative, got {petiole_index}")

        # Convert rotation to list for C++ interface
        rotation_list = shoot_base_rotation.to_list()

        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.addChildShoot(
                    self._plantarch_ptr, plant_id, parent_shoot_id, parent_node_index,
                    current_node_number, rotation_list, internode_radius,
                    internode_length_max, internode_length_scale_factor_fraction,
                    leaf_scale_factor_fraction, radius_taper, shoot_type_label.strip(),
                    petiole_index
                )
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() and "shoot type" in error_msg.lower():
                raise PlantArchitectureError(
                    f"Shoot type '{shoot_type_label}' not defined. "
                    f"Load a plant model first to define shoot types:\n"
                    f"  plantarch.loadPlantModelFromLibrary('bean')  # or other model\n"
                    f"Original error: {e}"
                )
            raise PlantArchitectureError(f"Failed to add child shoot: {e}")

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