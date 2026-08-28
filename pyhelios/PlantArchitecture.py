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

from .Context import Context, check_context_alive
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
from .plant_architecture_params import (
    ShootParameters,
    CarbohydrateParameters,
    NitrogenParameters,
    RandomParameter,
    RandomParameterFloat,
    RandomParameterInt,
)

logger = logging.getLogger(__name__)


# Build parameters accepted by each library plant model, mirroring the
# getParameterValue(current_build_parameters, ...) calls in PlantLibrary.cpp. Models absent
# from this table read no build parameters at all. The native library silently ignores keys
# it does not recognize, so PyHelios validates against this table to keep a typo or a
# wrong-species key from producing a plant that quietly used defaults.
_BUILD_PARAMETERS_BY_MODEL: Dict[str, frozenset] = {
    "almond": frozenset({"trunk_height", "num_scaffolds", "scaffold_angle"}),
    "almond_aldrich": frozenset({"trunk_height", "num_scaffolds", "scaffold_angle"}),
    "almond_wood_colony": frozenset({"trunk_height", "num_scaffolds", "scaffold_angle"}),
    "apple": frozenset({"trunk_height", "num_scaffolds", "scaffold_angle"}),
    "grapevine_VSP": frozenset({"trunk_height", "vine_spacing"}),
    "grapevine_wye": frozenset(
        {"trunk_height", "vine_spacing", "cordon_spacing", "catch_wire_height"}
    ),
    "pistachio": frozenset({"trunk_height", "num_scaffolds", "scaffold_angle"}),
    "walnut": frozenset({"trunk_height", "num_scaffolds", "scaffold_angle"}),
}

# Every build parameter name recognized by any model, for error messages when the current
# model is unknown.
_ALL_BUILD_PARAMETERS = frozenset().union(*_BUILD_PARAMETERS_BY_MODEL.values())


def _validate_build_parameters(build_parameters: Optional[dict], plant_model: Optional[str]) -> None:
    """Reject build parameter keys the loaded plant model will not read.

    The native library looks each key up in a map and falls back to a default when it is
    absent, so an unrecognized key is silently discarded. Raising here instead keeps a
    misspelled or wrong-species parameter from being mistaken for one that took effect.

    Args:
        build_parameters: Mapping supplied by the caller, or None.
        plant_model: Label of the currently loaded model, or None if no model has been
            loaded through this instance.

    Raises:
        ValueError: If build_parameters is not a dict of str -> number, or contains a key
            the loaded model does not accept.
    """
    if build_parameters is None:
        return

    if not isinstance(build_parameters, dict):
        raise ValueError("build_parameters must be a dict or None")

    for key, value in build_parameters.items():
        if not isinstance(key, str):
            raise ValueError("build_parameters keys must be strings")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("build_parameters values must be numeric (int or float)")

    if not build_parameters:
        return

    # An unrecognized model label cannot be checked against a specific list. Fall back to
    # the union so an outright typo is still caught, rather than skipping validation.
    if plant_model is not None:
        accepted = _BUILD_PARAMETERS_BY_MODEL.get(plant_model, frozenset())
        model_description = f"Plant model '{plant_model}'"
    else:
        accepted = _ALL_BUILD_PARAMETERS
        model_description = "No plant model has been loaded through this instance, so"

    unknown = sorted(set(build_parameters) - accepted)
    if not unknown:
        return

    if accepted:
        accepted_description = f"accepts only: {', '.join(sorted(accepted))}"
    else:
        accepted_description = "accepts no build parameters"

    raise ValueError(
        f"Unknown build parameter(s) {', '.join(repr(k) for k in unknown)}. "
        f"{model_description} {accepted_description}. "
        f"Unrecognized parameters are ignored by the native library, so they would "
        f"otherwise have no effect."
    )


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
        # Label passed to the most recent loadPlantModelFromLibrary(), used to validate
        # build parameters against the model that actually consumes them.
        self._current_plant_model = None

        # Create PlantArchitecture instance with asset-aware working directory
        with _plantarchitecture_working_directory():
            self._plantarch_ptr = plantarch_wrapper.createPlantArchitecture(context.getNativePtr())

        if not self._plantarch_ptr:
            raise PlantArchitectureError("Failed to initialize PlantArchitecture")

    def _check_context_alive(self):
        """Raise if the owning Context has been destroyed (see Context.check_context_alive)."""
        check_context_alive(getattr(self, "context", None), "PlantArchitecture")

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

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.loadPlantModelFromLibrary(self._plantarch_ptr, plant_label.strip())
        except Exception as e:
            raise PlantArchitectureError(f"Failed to load plant model '{plant_label}': {e}")

        self._current_plant_model = plant_label.strip()

    def buildPlantInstanceFromLibrary(self, base_position: vec3, age: float,
                                     build_parameters: Optional[dict] = None) -> int:
        """
        Build a plant instance from the currently loaded library model.

        Args:
            base_position: Cartesian (x,y,z) coordinates of plant base as vec3
            age: Age of the plant in days (must be >= 0)
            build_parameters: Optional dict of parameter overrides for training system
                            parameters. Only some models read them, and a key the model does
                            not accept raises ValueError rather than being ignored:
                            - almond, almond_aldrich, almond_wood_colony, apple, pistachio,
                              walnut: trunk_height, num_scaffolds, scaffold_angle
                            - grapevine_VSP: trunk_height, vine_spacing
                            - grapevine_wye: trunk_height, vine_spacing, cordon_spacing,
                              catch_wire_height
                            All other models read no build parameters.

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
        # Parameter type validation
        if not isinstance(base_position, vec3):
            raise ValueError(f"base_position must be a vec3, got {type(base_position).__name__}")

        # Convert position to list for C++ interface
        position_list = [base_position.x, base_position.y, base_position.z]

        # Validate age (allow zero)
        if age < 0:
            raise ValueError(f"Age must be non-negative, got {age}")

        _validate_build_parameters(build_parameters, self._current_plant_model)

        self._check_context_alive()
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
                                  germination_rate: float = 1.0,
                                  build_parameters: Optional[dict] = None) -> List[int]:
        """
        Build a canopy of regularly spaced plants from the currently loaded library model.

        Args:
            canopy_center: Cartesian (x,y,z) coordinates of canopy center as vec3
            plant_spacing: Spacing between plants in x- and y-directions (meters) as vec2
            plant_count: Number of plants in x- and y-directions as int2
            age: Age of all plants in days (must be >= 0)
            germination_rate: Probability that each plant position will be occupied (0 to 1).
                            A value of 1.0 means all positions are filled; 0.5 means roughly
                            half the positions will have plants. Default is 1.0.
            build_parameters: Optional dict of parameter overrides for training system
                            parameters, applied to every plant in the canopy. Only some models
                            read them, and a key the model does not accept raises ValueError
                            rather than being ignored. See buildPlantInstanceFromLibrary() for
                            the per-model list.

        Returns:
            List of plant IDs for the created plant instances

        Raises:
            ValueError: If age is negative, germination_rate is not in [0, 1],
                       plant count values are not positive, or build_parameters is invalid
            PlantArchitectureError: If canopy building fails

        Example:
            >>> # 3x3 canopy with 0.5m spacing, 30-day-old plants
            >>> plant_ids = plantarch.buildPlantCanopyFromLibrary(
            ...     canopy_center=vec3(0, 0, 0),
            ...     plant_spacing=vec2(0.5, 0.5),
            ...     plant_count=int2(3, 3),
            ...     age=30.0
            ... )
            >>> # With 80% germination rate and custom parameters
            >>> plant_ids = plantarch.buildPlantCanopyFromLibrary(
            ...     canopy_center=vec3(0, 0, 0),
            ...     plant_spacing=vec2(1.5, 2.0),
            ...     plant_count=int2(5, 3),
            ...     age=45.0,
            ...     germination_rate=0.8,
            ...     build_parameters={'trunk_height': 1.8}
            ... )
        """
        # Parameter type validation
        if not isinstance(canopy_center, vec3):
            raise ValueError(f"canopy_center must be a vec3, got {type(canopy_center).__name__}")
        if not isinstance(plant_spacing, vec2):
            raise ValueError(f"plant_spacing must be a vec2, got {type(plant_spacing).__name__}")
        if not isinstance(plant_count, int2):
            raise ValueError(f"plant_count must be an int2, got {type(plant_count).__name__}")

        # Validate age (allow zero)
        if age < 0:
            raise ValueError(f"Age must be non-negative, got {age}")

        # Validate germination rate
        if not isinstance(germination_rate, (int, float)):
            raise ValueError(f"germination_rate must be a number, got {type(germination_rate).__name__}")
        if germination_rate < 0 or germination_rate > 1:
            raise ValueError(f"germination_rate must be between 0 and 1, got {germination_rate}")

        # Validate count values
        if plant_count.x <= 0 or plant_count.y <= 0:
            raise ValueError("Plant count values must be positive integers")

        _validate_build_parameters(build_parameters, self._current_plant_model)

        # Convert to lists for C++ interface
        center_list = [canopy_center.x, canopy_center.y, canopy_center.z]
        spacing_list = [plant_spacing.x, plant_spacing.y]
        count_list = [plant_count.x, plant_count.y]

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.buildPlantCanopyFromLibrary(
                    self._plantarch_ptr, center_list, spacing_list, count_list, age,
                    germination_rate, build_parameters
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to build plant canopy: {e}")

    def advanceTime(self, dt: float, plant_id: Optional[int] = None,
                    plant_ids: Optional[List[int]] = None,
                    years: Optional[int] = None) -> None:
        """
        Advance time for plant growth and development.

        Updates plants in the simulation, potentially adding new phytomers, growing
        existing organs, transitioning phenological stages, and updating plant geometry.

        By default every plant advances together. Pass plant_id or plant_ids to advance a
        subset, which is what staggered planting dates and mixed-age stands require.

        Args:
            dt: Time step to advance in days (must be >= 0)
            plant_id: Advance only this plant. Mutually exclusive with plant_ids.
            plant_ids: Advance only these plants. Mutually exclusive with plant_id.
            years: Advance this many whole years in addition to dt days. Applies to all
                plants and cannot be combined with plant_id or plant_ids.

        Raises:
            ValueError: If dt or years is negative, or selectors are combined
            PlantArchitectureError: If time advancement fails

        Note:
            Large time steps are more efficient than many small steps. The timestep value
            can be larger than the phyllochron, allowing multiple phytomers to be produced
            in a single call.

        Example:
            >>> plantarch.advanceTime(10.0)                     # all plants, 10 days
            >>> plantarch.advanceTime(10.0, plant_id=early)     # one plant only
            >>> plantarch.advanceTime(10.0, plant_ids=[a, b])   # a subset
            >>> plantarch.advanceTime(0.0, years=4)             # all plants, 4 years
        """
        if dt < 0:
            raise ValueError(f"Time step must be non-negative, got {dt}")

        selectors = sum(x is not None for x in (plant_id, plant_ids, years))
        if selectors > 1:
            raise ValueError("Pass at most one of plant_id, plant_ids, or years")

        if plant_id is not None and plant_id < 0:
            raise ValueError(f"plant_id must be non-negative, got {plant_id}")
        if plant_ids is not None and any(pid < 0 for pid in plant_ids):
            raise ValueError("plant_ids must all be non-negative")
        if years is not None and years < 0:
            raise ValueError(f"years must be non-negative, got {years}")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                if plant_id is not None:
                    plantarch_wrapper.advanceTimeForPlant(self._plantarch_ptr, plant_id, dt)
                elif plant_ids is not None:
                    if not plant_ids:
                        return
                    plantarch_wrapper.advanceTimeForPlants(self._plantarch_ptr, plant_ids, dt)
                elif years is not None:
                    plantarch_wrapper.advanceTimeYears(self._plantarch_ptr, years, dt)
                else:
                    plantarch_wrapper.advanceTime(self._plantarch_ptr, dt)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to advance time by {dt} days: {e}")

    def enableAttractionPoints(self, points: List[vec3],
                               plant_id: Optional[int] = None,
                               view_half_angle_deg: Optional[float] = None,
                               look_ahead_distance: float = 0.1,
                               attraction_weight: float = 0.6) -> None:
        """
        Steer shoot growth toward a set of target points.

        Attraction points are the counterpart to collision avoidance: collision tells a
        plant what to grow around, attraction tells it what to grow toward. This is how
        trellis wires, espalier targets and greenhouse supports are modelled.

        Steering applies to growth that happens after this call, since the direction is
        chosen as each phytomer is constructed. Enable the points before advanceTime().

        Args:
            points: Target locations as a list of vec3
            plant_id: Apply to this plant only. Applies to every plant when None.
            view_half_angle_deg: Half-angle of the search cone in degrees. Defaults to
                45 for the global form and 80 for the per-plant form, matching the
                native defaults, which differ between the two.
            look_ahead_distance: How far ahead a shoot tip looks, in meters
            attraction_weight: Strength of the steering, 0 to 1

        Raises:
            ValueError: If points is empty or contains a non-vec3, or plant_id is negative
            PlantArchitectureError: If the operation fails

        Example:
            >>> wires = [vec3(x, 0, 2.1) for x in range(0, 10)]
            >>> plantarch.enableAttractionPoints(wires)
        """
        self._validate_attraction_points(points)
        if plant_id is not None and plant_id < 0:
            raise ValueError(f"plant_id must be non-negative, got {plant_id}")

        if view_half_angle_deg is None:
            view_half_angle_deg = 45.0 if plant_id is None else 80.0

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.enableAttractionPoints(
                    self._plantarch_ptr, plant_id, points,
                    view_half_angle_deg, look_ahead_distance, attraction_weight
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to enable attraction points: {e}")

    def disableAttractionPoints(self, plant_id: Optional[int] = None) -> None:
        """
        Stop steering growth toward attraction points.

        Args:
            plant_id: Disable for this plant only. Disables globally when None.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the operation fails
        """
        if plant_id is not None and plant_id < 0:
            raise ValueError(f"plant_id must be non-negative, got {plant_id}")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.disableAttractionPoints(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to disable attraction points: {e}")

    def updateAttractionPoints(self, points: List[vec3],
                               plant_id: Optional[int] = None) -> None:
        """
        Replace the current attraction point set.

        Args:
            points: Replacement target locations as a list of vec3
            plant_id: Update this plant only. Updates globally when None.

        Raises:
            ValueError: If points is empty or contains a non-vec3, or plant_id is negative
            PlantArchitectureError: If the operation fails
        """
        self._validate_attraction_points(points)
        if plant_id is not None and plant_id < 0:
            raise ValueError(f"plant_id must be non-negative, got {plant_id}")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.updateAttractionPoints(self._plantarch_ptr, plant_id, points)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to update attraction points: {e}")

    def appendAttractionPoints(self, points: List[vec3],
                               plant_id: Optional[int] = None) -> None:
        """
        Add to the current attraction point set.

        Args:
            points: Additional target locations as a list of vec3
            plant_id: Append for this plant only. Appends globally when None.

        Raises:
            ValueError: If points is empty or contains a non-vec3, or plant_id is negative
            PlantArchitectureError: If the operation fails
        """
        self._validate_attraction_points(points)
        if plant_id is not None and plant_id < 0:
            raise ValueError(f"plant_id must be non-negative, got {plant_id}")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.appendAttractionPoints(self._plantarch_ptr, plant_id, points)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to append attraction points: {e}")

    def setAttractionParameters(self, view_half_angle_deg: float,
                                look_ahead_distance: float,
                                attraction_weight: float,
                                obstacle_reduction_factor: float = 0.75,
                                plant_id: Optional[int] = None) -> None:
        """
        Tune how strongly attraction points steer growth.

        Args:
            view_half_angle_deg: Half-angle of the search cone in degrees
            look_ahead_distance: How far ahead a shoot tip looks, in meters
            attraction_weight: Strength of the steering, 0 to 1
            obstacle_reduction_factor: Scales attraction where an obstacle intervenes
            plant_id: Apply to this plant only. Applies globally when None.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the operation fails
        """
        if plant_id is not None and plant_id < 0:
            raise ValueError(f"plant_id must be non-negative, got {plant_id}")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.setAttractionParameters(
                    self._plantarch_ptr, plant_id, view_half_angle_deg,
                    look_ahead_distance, attraction_weight, obstacle_reduction_factor
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set attraction parameters: {e}")

    @staticmethod
    def _validate_attraction_points(points) -> None:
        """Reject point sets the native layer would misread or silently ignore."""
        if not isinstance(points, (list, tuple)):
            raise ValueError(
                f"points must be a list of vec3, got {type(points).__name__}"
            )
        if not points:
            raise ValueError("points cannot be empty")
        for index, point in enumerate(points):
            if not isinstance(point, vec3):
                raise ValueError(
                    f"points[{index}] must be a vec3, got {type(point).__name__}"
                )

    def setProgressCallback(self, callback):
        """Set a callback to receive progress updates during long-running operations.

        The callback fires during advanceTime() and adjustFruitForObstacleCollision()
        as the underlying ProgressBar updates.

        Args:
            callback: A callable(progress: float, message: str) where progress is
                      in [0, 1], or None to clear the callback.

        Raises:
            ValueError: If callback is not callable and not None.
        """
        if callback is not None:
            if not callable(callback):
                raise ValueError(
                    f"callback must be callable or None, got {type(callback).__name__}"
                )

            def _c_callback(progress, message_bytes):
                msg = message_bytes.decode('utf-8') if isinstance(message_bytes, bytes) else str(message_bytes)
                callback(progress, msg)

            self._check_context_alive()
            self._progress_callback_ref = plantarch_wrapper.PROGRESS_CALLBACK(_c_callback)
            self._check_context_alive()
            plantarch_wrapper.setProgressCallback(self._plantarch_ptr, self._progress_callback_ref)
        else:
            self._check_context_alive()
            plantarch_wrapper.setProgressCallback(self._plantarch_ptr, None)
            self._progress_callback_ref = None

    def setCancelFlag(self, cancel_flag):
        """Register an external cancellation flag polled during long plant builds.

        ``cancel_flag`` is a ctypes.c_int that, when set non-zero from another
        thread, stops the canopy build loop and the advanceTime() growth loop
        between plants/timesteps — so a long generation can be aborted mid-build
        (returning whatever was built so far). Set it before the build call; pass
        None to clear. The flag is caller-owned and must outlive the build.
        """
        self._check_context_alive()
        plantarch_wrapper.setCancelFlag(self._plantarch_ptr, cancel_flag)

    def getCurrentShootParameters(self, shoot_type_label: str, return_typed: bool = False):
        """
        Get current shoot parameters for a shoot type.

        Returns the full nested shoot and phytomer parameter set, including the
        internode/petiole/leaf/peduncle/inflorescence sub-structures and the leaf
        prototype. Every numeric field is a RandomParameter spec with a
        'distribution' and 'parameters'.

        Args:
            shoot_type_label: Label for the shoot type. Labels are species-specific,
                e.g. "trifoliate" (bean), "trunk"/"scaffold" (almond).
            return_typed: If True, return a typed
                :class:`pyhelios.plant_architecture_params.ShootParameters`
                object instead of a plain nested dict.

        Returns:
            A nested ``dict`` (default) or a ``ShootParameters`` object containing:
            - Geometric parameters (max_nodes, insertion_angle_tip, etc.)
            - Growth parameters (phyllochron_min, elongation_rate_max, etc.)
            - Boolean flags (flowers_require_dormancy, etc.)
            - ``phytomer_parameters`` with nested internode/petiole/leaf/peduncle/
              inflorescence parameters and the leaf prototype

        Raises:
            ValueError: If shoot_type_label is empty
            PlantArchitectureError: If parameter retrieval fails

        Example:
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>> params = plantarch.getCurrentShootParameters("trifoliate")
            >>> print(params['max_nodes'])
            {'distribution': 'constant', 'parameters': [25.0]}
            >>> print(params['phytomer_parameters']['leaf']['pitch'])
            {'distribution': 'normal', 'parameters': [0.0, 20.0]}
        """
        if not shoot_type_label:
            raise ValueError("Shoot type label cannot be empty")

        if not shoot_type_label.strip():
            raise ValueError("Shoot type label cannot be only whitespace")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                params = plantarch_wrapper.getCurrentShootParameters(
                    self._plantarch_ptr, shoot_type_label.strip()
                )
        except Exception as e:
            # An unknown label is the common case here, and the native error does not say
            # which labels exist. Name them so the caller does not have to guess.
            available = ""
            try:
                labels = self.listShootTypeLabels()
                if labels:
                    available = f" Available shoot types: {', '.join(sorted(labels))}."
            except Exception:
                pass
            raise PlantArchitectureError(f"{e}.{available}")

        return ShootParameters.from_dict(params) if return_typed else params

    def defineShootType(self, shoot_type_label: str, parameters: Union[dict, ShootParameters]) -> None:
        """
        Define a custom shoot type with specified parameters.

        Allows creating new shoot types or modifying existing ones. Pass either a
        nested parameter ``dict`` (use :meth:`getCurrentShootParameters` as a
        template) or a typed
        :class:`pyhelios.plant_architecture_params.ShootParameters` object.

        Redefining an existing library shoot type preserves that species' built-in
        phytomer creation and callback functions, so species-specific organ behavior
        (such as maize forming ears rather than a tassel at every node) is retained.

        Args:
            shoot_type_label: Unique name for this shoot type
            parameters: A nested dict matching the ShootParameters structure, or a
                ShootParameters object.

        Raises:
            ValueError: If shoot_type_label is empty, or parameters is not a dict
                or ShootParameters
            PlantArchitectureError: If shoot type definition fails

        Example:
            >>> from pyhelios.plant_architecture_params import ShootParameters, RandomParameterFloat
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>> sp = plantarch.getCurrentShootParameters("trifoliate", return_typed=True)
            >>> sp.max_nodes = RandomParameterFloat.constant(20)
            >>> sp.phytomer_parameters.leaf.pitch = RandomParameterFloat.uniform(40, 50)
            >>> plantarch.defineShootType("TallStem", sp)
        """
        if not shoot_type_label:
            raise ValueError("Shoot type label cannot be empty")

        if not shoot_type_label.strip():
            raise ValueError("Shoot type label cannot be only whitespace")

        if isinstance(parameters, ShootParameters):
            parameters = parameters.to_dict()
        elif not isinstance(parameters, dict):
            raise ValueError(
                f"Parameters must be a dict or ShootParameters, got {type(parameters).__name__}"
            )

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.defineShootType(
                    self._plantarch_ptr, self.context.context, shoot_type_label.strip(), parameters
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to define shoot type '{shoot_type_label}': {e}")

    def getDefaultCarbohydrateParameters(self, return_typed: bool = False):
        """
        Get a default-constructed set of carbohydrate-model parameters.

        The native API exposes no per-plant getter for carbohydrate parameters, so
        this returns the C++ defaults as a template to modify and apply via
        :meth:`setPlantCarbohydrateParameters`.

        Args:
            return_typed: If True, return a typed
                :class:`pyhelios.plant_architecture_params.CarbohydrateParameters`.

        Returns:
            A flat ``dict`` (default) or ``CarbohydrateParameters`` object.
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                params = plantarch_wrapper.getDefaultCarbohydrateParameters()
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get default carbohydrate parameters: {e}")
        return CarbohydrateParameters.from_dict(params) if return_typed else params

    def setPlantCarbohydrateParameters(self, plant_id: int, parameters: Union[dict, CarbohydrateParameters]) -> None:
        """
        Set carbohydrate-model parameters for a plant.

        Args:
            plant_id: Target plant instance ID
            parameters: A flat dict or a CarbohydrateParameters object.

        Raises:
            ValueError: If parameters is not a dict or CarbohydrateParameters
            PlantArchitectureError: If the operation fails
        """
        if isinstance(parameters, CarbohydrateParameters):
            parameters = parameters.to_dict()
        elif not isinstance(parameters, dict):
            raise ValueError(
                f"Parameters must be a dict or CarbohydrateParameters, got {type(parameters).__name__}"
            )
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.setPlantCarbohydrateParameters(self._plantarch_ptr, plant_id, parameters)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set carbohydrate parameters for plant {plant_id}: {e}")

    def getDefaultNitrogenParameters(self, return_typed: bool = False):
        """
        Get a default-constructed set of nitrogen-model parameters.

        The native API exposes no per-plant getter for nitrogen parameters, so this
        returns the C++ defaults as a template to modify and apply via
        :meth:`setPlantNitrogenParameters`.

        Args:
            return_typed: If True, return a typed
                :class:`pyhelios.plant_architecture_params.NitrogenParameters`.

        Returns:
            A flat ``dict`` (default) or ``NitrogenParameters`` object.
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                params = plantarch_wrapper.getDefaultNitrogenParameters()
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get default nitrogen parameters: {e}")
        return NitrogenParameters.from_dict(params) if return_typed else params

    def setPlantNitrogenParameters(self, plant_id: int, parameters: Union[dict, NitrogenParameters]) -> None:
        """
        Set nitrogen-model parameters for a plant.

        Args:
            plant_id: Target plant instance ID
            parameters: A flat dict or a NitrogenParameters object.

        Raises:
            ValueError: If parameters is not a dict or NitrogenParameters
            PlantArchitectureError: If the operation fails
        """
        if isinstance(parameters, NitrogenParameters):
            parameters = parameters.to_dict()
        elif not isinstance(parameters, dict):
            raise ValueError(
                f"Parameters must be a dict or NitrogenParameters, got {type(parameters).__name__}"
            )
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.setPlantNitrogenParameters(self._plantarch_ptr, plant_id, parameters)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set nitrogen parameters for plant {plant_id}: {e}")

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
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAvailablePlantModels(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get available plant models: {e}")

    def listShootTypeLabels(self, plant_model: Optional[str] = None,
                            plant_id: Optional[int] = None) -> List[str]:
        """
        Get the shoot type labels defined for a plant model.

        Shoot type labels are species-specific strings such as "trunk" or "scaffold", and
        every shoot-parameter call takes one. Use this to discover the valid labels rather
        than guessing them.

        Args:
            plant_model: Query this library model without changing the currently loaded
                one. Use getAvailablePlantModels() for valid names. Mutually exclusive
                with plant_id.
            plant_id: Query the shoot types captured by this plant instance when it was
                created. Mutually exclusive with plant_model.

        With neither argument, queries the currently loaded model, which requires a prior
        call to loadPlantModelFromLibrary().

        Returns:
            List of shoot type label strings.

        Raises:
            ValueError: If both plant_model and plant_id are given, or plant_id is negative
            PlantArchitectureError: If no model is loaded, or the model or plant is unknown

        Example:
            >>> plantarch.loadPlantModelFromLibrary("almond")
            >>> plantarch.listShootTypeLabels()
            ['proleptic', 'scaffold', 'sylleptic', 'trunk']
            >>> plantarch.listShootTypeLabels(plant_model="bean")
            ['trifoliate', 'unifoliate']
        """
        if plant_model is not None and plant_id is not None:
            raise ValueError("Pass either plant_model or plant_id, not both")
        if plant_id is not None and plant_id < 0:
            raise ValueError(f"plant_id must be non-negative, got {plant_id}")
        if plant_model is not None and not plant_model.strip():
            raise ValueError("plant_model cannot be empty or only whitespace")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.listShootTypeLabels(
                    self._plantarch_ptr,
                    plant_model.strip() if plant_model is not None else None,
                    plant_id,
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to list shoot type labels: {e}")

    def getAllUUIDs(self) -> List[int]:
        """
        Get UUIDs of every plant primitive in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        Returns:
            List of primitive UUIDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllUUIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllUUIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get primitive UUIDs: {e}")

    def getAllLeafUUIDs(self) -> List[int]:
        """
        Get UUIDs of every leaf primitive in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        Returns:
            List of leaf primitive UUIDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllLeafUUIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllLeafUUIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get leaf primitive UUIDs: {e}")

    def getAllInternodeUUIDs(self) -> List[int]:
        """
        Get UUIDs of every internode primitive in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        Returns:
            List of internode primitive UUIDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllInternodeUUIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllInternodeUUIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get internode primitive UUIDs: {e}")

    def getAllPetioleUUIDs(self) -> List[int]:
        """
        Get UUIDs of every petiole primitive in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        Returns:
            List of petiole primitive UUIDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllPetioleUUIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllPetioleUUIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get petiole primitive UUIDs: {e}")

    def getAllPeduncleUUIDs(self) -> List[int]:
        """
        Get UUIDs of every peduncle primitive in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        An empty list means no plant has reached the corresponding growth stage,
        which is a legitimate result rather than a failure.

        Returns:
            List of peduncle primitive UUIDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllPeduncleUUIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllPeduncleUUIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get peduncle primitive UUIDs: {e}")

    def getAllFlowerUUIDs(self) -> List[int]:
        """
        Get UUIDs of every flower primitive in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        An empty list means no plant has reached the corresponding growth stage,
        which is a legitimate result rather than a failure.

        Returns:
            List of flower primitive UUIDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllFlowerUUIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllFlowerUUIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get flower primitive UUIDs: {e}")

    def getAllFruitUUIDs(self) -> List[int]:
        """
        Get UUIDs of every fruit primitive in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        An empty list means no plant has reached the corresponding growth stage,
        which is a legitimate result rather than a failure.

        Returns:
            List of fruit primitive UUIDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllFruitUUIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllFruitUUIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get fruit primitive UUIDs: {e}")

    def getAllObjectIDs(self) -> List[int]:
        """
        Get object IDs of every plant compound object in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        Returns:
            List of object IDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllObjectIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllObjectIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get object IDs: {e}")

    def getAllPlantIDs(self) -> List[int]:
        """
        Get IDs of every plant instance in the model.

        Spans every plant, unlike the per-plant getters, which is what canopy-wide work
        such as assigning optical properties or reading flux by organ type needs.

        Returns:
            List of plant IDs

        Raises:
            PlantArchitectureError: If retrieval fails

        Example:
            >>> ids = plantarch.getAllPlantIDs()
        """
        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getAllPlantIDs(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get plant IDs: {e}")

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

        self._check_context_alive()
        try:
            return plantarch_wrapper.getAllPlantObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get object IDs for plant {plant_id}: {e}")

    def getPlantLeafObjectIDs(self, plant_id: int) -> List[int]:
        """
        Get object IDs for all leaf objects on a specific plant.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of object IDs, one per leaf

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Warning:
            Do **not** pair this result positionally with :meth:`getPlantLeafBases`.
            The two are built by independent traversals of the shoot tree, so their
            index correspondence is not guaranteed by the native API.

        Example:
            >>> leaf_ids = plantarch.getPlantLeafObjectIDs(plant_id)
            >>> print(f"Plant has {len(leaf_ids)} leaves")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantLeafObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get leaf object IDs for plant {plant_id}: {e}")

    def getPlantPetioleObjectIDs(self, plant_id: int) -> List[int]:
        """
        Get object IDs for all petiole objects on a specific plant.

        Petioles are the stalks attaching leaves to the stem, so this is the
        structural counterpart to :meth:`getPlantLeafObjectIDs`.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of object IDs, one per petiole

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> petiole_ids = plantarch.getPlantPetioleObjectIDs(plant_id)
            >>> print(f"Plant has {len(petiole_ids)} petioles")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantPetioleObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get petiole object IDs for plant {plant_id}: {e}")

    def getPlantPeduncleObjectIDs(self, plant_id: int) -> List[int]:
        """
        Get object IDs for all peduncle objects on a specific plant.

        Peduncles are the stalks bearing flowers and fruit.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of object IDs, one per peduncle. Empty if the plant has not
            reached its reproductive stage, which is a normal result rather than
            an error.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> peduncle_ids = plantarch.getPlantPeduncleObjectIDs(plant_id)
            >>> print(f"Plant has {len(peduncle_ids)} peduncles")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantPeduncleObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get peduncle object IDs for plant {plant_id}: {e}")

    def getPlantFlowerObjectIDs(self, plant_id: int) -> List[int]:
        """
        Get object IDs for all flower (inflorescence) objects on a specific plant.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of object IDs, one per flower. Empty if the plant has not
            flowered -- or has already flowered and set fruit, since flowers are
            replaced by fruit as growth proceeds. Both are normal results rather
            than errors.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> flower_ids = plantarch.getPlantFlowerObjectIDs(plant_id)
            >>> print(f"Plant has {len(flower_ids)} flowers")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantFlowerObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get flower object IDs for plant {plant_id}: {e}")

    def getPlantFruitObjectIDs(self, plant_id: int) -> List[int]:
        """
        Get object IDs for all fruit objects on a specific plant.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of object IDs, one per fruit. Empty if the plant has not
            fruited, which is a normal result rather than an error -- fruit
            appear only once a plant reaches the reproductive stage, so a plant
            built at a young age or from a model with no fruit yields ``[]``.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> fruit_ids = plantarch.getPlantFruitObjectIDs(plant_id)
            >>> print(f"Plant has {len(fruit_ids)} fruit")
            >>> # Object IDs are Context object IDs, so the usual queries apply:
            >>> uuids = context.getObjectPrimitiveUUIDs(fruit_ids[0])
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantFruitObjectIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get fruit object IDs for plant {plant_id}: {e}")

    def getPlantLeafBases(self, plant_id: int) -> List[vec3]:
        """
        Get the attachment base position of every leaf on a specific plant.

        The base is where the leaf attaches to its petiole, not the leaf centroid.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of vec3 base positions, one per leaf

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Warning:
            Do **not** pair this result positionally with
            :meth:`getPlantLeafObjectIDs`. The two are built by independent
            traversals of the shoot tree, so their index correspondence is not
            guaranteed by the native API. (helios-core has an internal
            ``getPlantLeafObjectIDsAndBases()`` that gathers both in one traversal
            for exactly this reason, but it is protected and not callable from here.)

        Example:
            >>> bases = plantarch.getPlantLeafBases(plant_id)
            >>> print(f"First leaf attaches at {bases[0]}")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            flat = plantarch_wrapper.getPlantLeafBases(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get leaf bases for plant {plant_id}: {e}")

        return [vec3(float(flat[i]), float(flat[i + 1]), float(flat[i + 2]))
                for i in range(0, len(flat), 3)]

    def getAllPlantUUIDs(self, plant_id: int, include_hidden: bool = False) -> List[int]:
        """
        Get all primitive UUIDs for a specific plant.

        Args:
            plant_id: ID of the plant instance
            include_hidden: If True, also include UUIDs of hidden prototype
                primitives managed by this PlantArchitecture instance.

        Returns:
            List of primitive UUIDs comprising the plant (and optionally hidden prototypes)

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> uuids = plantarch.getAllPlantUUIDs(plant_id)
            >>> print(f"Plant has {len(uuids)} primitives")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            return plantarch_wrapper.getAllPlantUUIDs(self._plantarch_ptr, plant_id, include_hidden)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get UUIDs for plant {plant_id}: {e}")

    def getAllShootIDs(self, plant_id: int) -> List[int]:
        """
        Get the IDs of all shoots belonging to a plant.

        Shoot IDs are contiguous 0-based indices into the plant's shoot tree, in creation
        order; shoot 0 is always the base stem. The returned IDs can be passed to
        :meth:`getShoot`, :meth:`getShootChildIDs`, etc.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of shoot IDs for the plant
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getAllPlantShootIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get shoot IDs for plant {plant_id}: {e}")

    def getShoot(self, plant_id: int, shoot_id: int) -> Dict[str, Any]:
        """
        Get a read-only view of a shoot's topology.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant (see :meth:`getAllShootIDs`)

        Returns:
            A dict with keys ``rank``, ``parent_shoot_id`` (-1 for the base stem),
            ``parent_node_index``, and ``node_count``.
        """
        if plant_id < 0 or shoot_id < 0:
            raise ValueError("Plant ID and shoot ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantShootTopology(self._plantarch_ptr, plant_id, shoot_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get shoot {shoot_id} of plant {plant_id}: {e}")

    def getShootChildIDs(self, plant_id: int, shoot_id: int) -> List[int]:
        """Get the child shoot IDs of a shoot (flattened across parent node indices)."""
        if plant_id < 0 or shoot_id < 0:
            raise ValueError("Plant ID and shoot ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantShootChildIDs(self._plantarch_ptr, plant_id, shoot_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get child shoots of shoot {shoot_id}, plant {plant_id}: {e}")

    def getParentShootID(self, plant_id: int, shoot_id: int) -> int:
        """
        Get the ID of the shoot a shoot grew from.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant (see :meth:`getAllShootIDs`)

        Returns:
            ID of the parent shoot, or -1 if this is the base stem shoot.

        Note:
            A pruned shoot still reports the parent it grew from, even though it is no
            longer listed among that parent's children.

        Example:
            >>> parent = plantarch.getParentShootID(plant_id, shoot_id=3)
        """
        return self._shootScalarQuery("getParentShootID", plant_id, shoot_id, "parent shoot ID")

    def getShootRank(self, plant_id: int, shoot_id: int) -> int:
        """
        Get the branching rank of a shoot.

        Rank is the botanical branching order: the base stem is rank 0, a branch off it
        is rank 1, and so on. A shoot created by :meth:`appendShoot` continues its
        parent's axis rather than branching from it, so it keeps the parent's rank.
        Rank is therefore not the same as :meth:`getShootDepth`.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant

        Returns:
            Branching rank of the shoot.

        Example:
            >>> rank = plantarch.getShootRank(plant_id, shoot_id=3)
        """
        return self._shootScalarQuery("getShootRank", plant_id, shoot_id, "shoot rank")

    def getShootDepth(self, plant_id: int, shoot_id: int) -> int:
        """
        Get the number of shoots between a shoot and the base stem shoot.

        The base stem has depth 0, its children depth 1, and so on. Unlike
        :meth:`getShootRank` this counts every step in the shoot tree, including axis
        continuations created by :meth:`appendShoot`.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant

        Returns:
            Number of steps from this shoot to the base stem shoot.
        """
        return self._shootScalarQuery("getShootDepth", plant_id, shoot_id, "shoot depth")

    def isShootPruned(self, plant_id: int, shoot_id: int) -> bool:
        """
        Report whether a shoot has been pruned away entirely.

        :meth:`pruneBranch` called with ``node_index=0`` removes all of a shoot's
        phytomers and geometry but keeps the shoot in the plant's tree so that shoot IDs
        stay stable. Such a shoot is still returned by :meth:`getAllShootIDs` but is
        inert: it has zero nodes, contributes no leaf area, and cannot be queried for
        geometry. Use this to skip those shoots when walking :meth:`getAllShootIDs`.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant

        Returns:
            True if the shoot was pruned away and no longer forms part of the plant.

        Example:
            >>> live = [s for s in plantarch.getAllShootIDs(plant_id)
            ...         if not plantarch.isShootPruned(plant_id, s)]
        """
        return self._shootScalarQuery("isShootPruned", plant_id, shoot_id, "pruned state")

    def getPathToRoot(self, plant_id: int, shoot_id: int) -> List[int]:
        """
        Get the chain of shoots connecting a shoot to the base stem shoot.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant

        Returns:
            Shoot IDs ordered from the given shoot to the base stem shoot, including
            both. For the base stem shoot this is a single element.

        Example:
            >>> path = plantarch.getPathToRoot(plant_id, shoot_id=5)
        """
        return self._shootScalarQuery("getPathToRoot", plant_id, shoot_id, "path to root")

    def getChildShootIDs(self, plant_id: int, shoot_id: int) -> List[int]:
        """
        Get the shoots that grew directly out of a shoot.

        Ordered by the node they attach to. This includes shoots created by
        :meth:`appendShoot`, which continue the parent's axis rather than branching from
        it; compare their :meth:`getShootRank` with the parent's to tell the two apart.
        Pruned shoots are not included.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant

        Returns:
            IDs of the direct children of the shoot, empty if it has none.
        """
        return self._shootScalarQuery("getChildShootIDs", plant_id, shoot_id, "child shoot IDs")

    def getAllDescendantShootIDs(self, plant_id: int, shoot_id: int) -> List[int]:
        """
        Get every shoot descending from a shoot.

        Collected depth-first, so a shoot is always listed before its own descendants.
        The shoot itself is not included, and pruned shoots are omitted.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot whose descendants to collect

        Returns:
            IDs of all descendants of the shoot, empty if it has none.

        Example:
            >>> descendants = plantarch.getAllDescendantShootIDs(plant_id, shoot_id=1)
            >>> print(f"Branch carries {len(descendants)} sub-shoots")
        """
        return self._shootScalarQuery("getAllDescendantShootIDs", plant_id, shoot_id,
                                      "descendant shoot IDs")

    def getShootHierarchyMap(self, plant_id: int) -> Dict[int, List[int]]:
        """
        Get the parent-to-children structure of a plant.

        Only shoots that actually have children appear as keys. Pruned shoots appear
        neither as keys nor among the children.

        Args:
            plant_id: ID of the plant instance

        Returns:
            Dict mapping shoot ID to the IDs of its direct children.

        Example:
            >>> hierarchy = plantarch.getShootHierarchyMap(plant_id)
            >>> print(f"{len(hierarchy)} shoots carry branches")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getShootHierarchyMap(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get shoot hierarchy of plant {plant_id}: {e}")

    def _shootScalarQuery(self, wrapper_fn_name: str, plant_id: int, shoot_id: int,
                          description: str):
        """Shared body for the per-shoot hierarchy accessors."""
        if plant_id < 0 or shoot_id < 0:
            raise ValueError("Plant ID and shoot ID must be non-negative")
        self._check_context_alive()
        try:
            return getattr(plantarch_wrapper, wrapper_fn_name)(
                self._plantarch_ptr, plant_id, shoot_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get {description} of shoot {shoot_id}, plant {plant_id}: {e}")

    def getShootInternodeVertices(self, plant_id: int, shoot_id: int) -> List[tuple]:
        """Get the woody internode polyline vertices of a shoot as a list of (x, y, z) tuples."""
        if plant_id < 0 or shoot_id < 0:
            raise ValueError("Plant ID and shoot ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantShootInternodeVertices(self._plantarch_ptr, plant_id, shoot_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get internode vertices of shoot {shoot_id}, plant {plant_id}: {e}")

    def getShootInternodeRadii(self, plant_id: int, shoot_id: int) -> List[float]:
        """Get the per-vertex woody internode radii of a shoot."""
        if plant_id < 0 or shoot_id < 0:
            raise ValueError("Plant ID and shoot ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantShootInternodeRadii(self._plantarch_ptr, plant_id, shoot_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get internode radii of shoot {shoot_id}, plant {plant_id}: {e}")

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

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.getPlantAge(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get age for plant {plant_id}: {e}")

    def getPlantMaxAge(self, plant_id: int) -> float:
        """
        Get the maximum age of a plant, beyond which it stops growing.

        Args:
            plant_id: ID of the plant instance

        Returns:
            Maximum plant age in days. See :meth:`setPlantMaxAge`.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If retrieval fails

        Example:
            >>> max_age = plantarch.getPlantMaxAge(plant_id)
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getPlantMaxAge(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get maximum age of plant {plant_id}: {e}")

    def setPlantMaxAge(self, plant_id: int, max_age: float) -> None:
        """
        Set the maximum age of a plant, beyond which it stops growing.

        Once a plant's age reaches this value, :meth:`advanceTime` stops advancing it and
        its geometry becomes static. The default is 999 days. Every plant model in the
        library sets its own value as part of its builder (an apple tree, for example,
        uses 1460 days), but a plant assembled manually with :meth:`addPlantInstance`
        keeps the default and so silently stops growing after 999 days.

        Setting a maximum age below the plant's current age is permitted, and freezes the
        plant at its current form.

        Args:
            plant_id: ID of the plant instance
            max_age: Maximum age of the plant in days. Must be non-negative.

        Raises:
            ValueError: If plant_id is negative or max_age is negative
            PlantArchitectureError: If the plant does not exist

        Example:
            >>> plantarch.setPlantMaxAge(plant_id, 1460.0)
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if max_age < 0:
            raise ValueError(f"Maximum age must be non-negative, got {max_age}")
        self._check_context_alive()
        try:
            plantarch_wrapper.setPlantMaxAge(self._plantarch_ptr, plant_id, max_age)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to set maximum age of plant {plant_id}: {e}")

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

        self._check_context_alive()
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

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.sumPlantLeafArea(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get leaf area for plant {plant_id}: {e}")

    def optionalOutputObjectData(self, object_data_labels: Union[str, List[str]]) -> None:
        """
        Enable optional output object data to be written to the Context.

        By default, the plant architecture model only writes a minimal set of
        object data. This method enables additional object data fields so that
        they are available on the Context's compound objects after building.

        Args:
            object_data_labels: A single label or a list of labels to enable.
                Valid labels include: "age", "rank", "plantID", "plant_name",
                "plant_height", "plant_type", "phenology_stage", "leafID",
                "peduncleID", "closedflowerID", "openflowerID", "fruitID",
                "carbohydrate_concentration". The special label "all" enables
                every available field.

        Raises:
            ValueError: If a label is empty or not a string
            PlantArchitectureError: If an invalid label is supplied or the
                operation otherwise fails

        Example:
            >>> plantarch.optionalOutputObjectData("age")
            >>> plantarch.optionalOutputObjectData(["rank", "plant_height"])
            >>> plantarch.optionalOutputObjectData("all")
        """
        if isinstance(object_data_labels, str):
            labels = [object_data_labels]
        else:
            labels = list(object_data_labels)

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                for label in labels:
                    plantarch_wrapper.optionalOutputObjectData(self._plantarch_ptr, label)
        except ValueError:
            raise
        except Exception as e:
            raise PlantArchitectureError(f"Failed to enable optional output object data: {e}")

    def setPlantPhenologicalThresholds(
        self,
        plant_id: int,
        time_to_dormancy_break: float,
        time_to_flower_initiation: float,
        time_to_flower_opening: float,
        time_to_fruit_set: float,
        time_to_fruit_maturity: float,
        time_to_dormancy: float,
        max_leaf_lifespan: float = 1e6,
        is_evergreen: bool = False
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
            is_evergreen: If True, the plant retains leaves through dormancy
                instead of shedding them at senescence (default: False)

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

        self._check_context_alive()
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
                    max_leaf_lifespan,
                    is_evergreen
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to set phenological thresholds for plant {plant_id}: {e}")

    def disablePlantPhenology(self, plant_id: int) -> None:
        """
        Disable phenological progression for a plant.

        The plant continues to grow, but no phenological stage is ever scheduled: it does not
        enter dormancy, and flower and fruit stages are skipped. This is the explicit form of the
        state a plant is already in when :meth:`setPlantPhenologicalThresholds` has never been
        called on it, so it is mainly useful for turning phenology back off on a plant that had
        thresholds set earlier.

        Args:
            plant_id: Identifier of the plant whose phenology is to be disabled

        Warning:
            helios-core's ``disablePlantPhenology()`` sets ``dd_to_fruit_maturity`` to ``-1``,
            whereas the "no phenology scheduled" default for that field is ``1e6``. The field is
            used as a divisor in the fruit-growth branch of ``advanceTime()``, which is gated only
            on a bud being in the ``BUD_FRUITING`` state, and ``appendPhytomerToShoot()`` can set
            that state from shoot structure alone. On a plant that already has a fruiting bud, a
            subsequent ``advanceTime()`` can therefore compute a negative fruit scale factor. Avoid
            calling this on a plant with fruiting buds until it is fixed upstream; a plant that
            never had thresholds set is already in the no-phenology state and does not need it.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If disabling phenology fails

        Example:
            >>> plantarch.setPlantPhenologicalThresholds(plant_id, 60, 90, 105, 120, 200, 280)
            >>> plantarch.disablePlantPhenology(plant_id)  # growth only, no dormancy or fruiting
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.disablePlantPhenology(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to disable phenology for plant {plant_id}: {e}")

    # Dormancy control methods
    def makePlantDormant(self, plant_id: int) -> None:
        """
        Force a plant into a dormant state immediately.

        This is the direct equivalent of ``makePlantDormant()`` in helios-core, as called by the
        library builders such as ``buildAppleTree()``. It is the counterpart to scheduling dormancy
        through :meth:`setPlantPhenologicalThresholds`: this forces the state now, rather than
        waiting for a degree-day threshold to be crossed.

        Dormancy strips the plant's leaves and marks its non-dormant buds dormant, so a
        custom-built plant can be put into the same over-winter state that a library-built
        perennial reaches through phenology.

        Args:
            plant_id: Identifier of the plant to make dormant

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the plant does not exist or the call fails

        Example:
            >>> plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
            >>> plantarch.addBaseStemShoot(plant_id, 3, AxisRotation(0, 0, 0),
            ...                            0.01, 0.1, 1.0, 1.0, 0.9, "trifoliate")
            >>> plantarch.makePlantDormant(plant_id)
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.makePlantDormant(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to make plant {plant_id} dormant: {e}")

    def breakPlantDormancy(self, plant_id: int) -> None:
        """
        Break dormancy for all shoots on a plant, returning it to an active state.

        This is the counterpart to :meth:`makePlantDormant`. Note that it only revives buds that
        are not dead, so a plant that was repeatedly made dormant may not recover every bud.

        Args:
            plant_id: Identifier of the plant whose dormancy should be broken

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the plant does not exist or the call fails

        Example:
            >>> plantarch.makePlantDormant(plant_id)
            >>> plantarch.breakPlantDormancy(plant_id)  # resume growth in spring
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.breakPlantDormancy(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to break dormancy for plant {plant_id}: {e}")

    def isPlantDormant(self, plant_id: int) -> bool:
        """
        Check whether a plant is dormant.

        Args:
            plant_id: Identifier of the plant to check

        Returns:
            True if all shoots on the plant are dormant, False otherwise

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the plant does not exist or the query fails

        Example:
            >>> plantarch.makePlantDormant(plant_id)
            >>> plantarch.isPlantDormant(plant_id)
            True
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                return plantarch_wrapper.isPlantDormant(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to query dormancy state for plant {plant_id}: {e}")

    # Pruning and organ removal methods
    def pruneBranch(self, plant_id: int, shoot_id: int, node_index: int) -> None:
        """
        Prune a shoot at a node, removing that node and everything distal to it.

        The phytomer at ``node_index`` is deleted along with every phytomer above it
        on the same shoot, and the cut recurses into every child shoot attached at or
        above that node. The shoot's woody internode tube is trimmed back to the cut
        and its apical bud is terminated, so the pruned axis will not resume growing.
        Pruning at ``node_index=0`` therefore removes the entire shoot and its whole
        branch system.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant (see :meth:`getAllShootIDs`)
            node_index: Node on the shoot to cut at, in ``[0, node_count)``

        Raises:
            ValueError: If any identifier is negative
            PlantArchitectureError: If the plant or shoot does not exist, if
                ``node_index`` is beyond the shoot's current node count, or if the
                native call fails

        Note:
            A pruned shoot currently keeps its ID in :meth:`getAllShootIDs` with a
            ``node_count`` of 0 rather than disappearing. Do not rely on either
            behavior; traverse with :meth:`getShoot` and treat ``node_count == 0``
            as "nothing left here".

        Example:
            >>> # Remove a whole branch and everything growing off it
            >>> plantarch.pruneBranch(plant_id, shoot_id=3, node_index=0)
            >>> # Head back a leader, keeping its lowest 5 nodes
            >>> plantarch.pruneBranch(plant_id, shoot_id=0, node_index=5)
        """
        if plant_id < 0 or shoot_id < 0 or node_index < 0:
            raise ValueError("Plant ID, shoot ID and node index must be non-negative")

        self._check_context_alive()
        try:
            plantarch_wrapper.pruneBranch(self._plantarch_ptr, plant_id, shoot_id, node_index)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to prune shoot {shoot_id} of plant {plant_id} at node {node_index}: {e}")

    def harvestPlant(self, plant_id: int) -> None:
        """
        Harvest a plant by removing its flowers and fruit.

        Every non-dormant floral bud on the plant is killed, which deletes the
        associated flower, fruit and peduncle geometry from the Context. Vegetative
        structure is untouched and the plant continues to grow afterwards.

        Args:
            plant_id: ID of the plant instance to harvest

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the plant does not exist or the call fails

        Note:
            Leaves are **not** removed, despite what the upstream Helios
            documentation for ``harvestPlant`` states. Use :meth:`removePlantLeaves`
            to defoliate.

        Example:
            >>> before = len(plantarch.getPlantFruitObjectIDs(plant_id))
            >>> plantarch.harvestPlant(plant_id)
            >>> len(plantarch.getPlantFruitObjectIDs(plant_id)) < before
            True
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            plantarch_wrapper.harvestPlant(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to harvest plant {plant_id}: {e}")

    def removePlantLeaves(self, plant_id: int) -> None:
        """
        Remove all leaves from every shoot on a plant.

        Leaf and petiole geometry is deleted from the Context. Buds are left alive,
        so the plant can produce new leaves as it continues to grow.

        Args:
            plant_id: ID of the plant instance to defoliate

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the plant does not exist or the call fails

        Example:
            >>> plantarch.removePlantLeaves(plant_id)
            >>> plantarch.getPlantLeafObjectIDs(plant_id)
            []
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            plantarch_wrapper.removePlantLeaves(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to remove leaves from plant {plant_id}: {e}")

    def removeShootLeaves(self, plant_id: int, shoot_id: int) -> None:
        """
        Remove all leaves from a single shoot.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant (see :meth:`getAllShootIDs`)

        Raises:
            ValueError: If either identifier is negative
            PlantArchitectureError: If the plant or shoot does not exist

        Example:
            >>> # Strip the leaves off a grapevine trunk, as in a trained architecture
            >>> plantarch.removeShootLeaves(plant_id, shoot_id=0)
        """
        self._removeShootOrgans("removeShootLeaves", plant_id, shoot_id, "leaves")

    def removeShootVegetativeBuds(self, plant_id: int, shoot_id: int) -> None:
        """
        Kill all vegetative buds on a single shoot.

        The shoot keeps its existing structure but can no longer produce new lateral
        shoots from those buds -- the standard way to stop a trained axis from
        throwing new canes.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant (see :meth:`getAllShootIDs`)

        Raises:
            ValueError: If either identifier is negative
            PlantArchitectureError: If the plant or shoot does not exist

        Example:
            >>> plantarch.removeShootVegetativeBuds(plant_id, shoot_id=1)
        """
        self._removeShootOrgans("removeShootVegetativeBuds", plant_id, shoot_id,
                                "vegetative buds")

    def removeShootFloralBuds(self, plant_id: int, shoot_id: int) -> None:
        """
        Kill all floral buds on a single shoot.

        Existing flower, fruit and peduncle geometry on the shoot is deleted and no
        new flowers will form there.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Shoot index within the plant (see :meth:`getAllShootIDs`)

        Raises:
            ValueError: If either identifier is negative
            PlantArchitectureError: If the plant or shoot does not exist

        Example:
            >>> plantarch.removeShootFloralBuds(plant_id, shoot_id=1)
        """
        self._removeShootOrgans("removeShootFloralBuds", plant_id, shoot_id, "floral buds")

    def _removeShootOrgans(self, wrapper_fn_name: str, plant_id: int, shoot_id: int,
                           organ_description: str) -> None:
        """Shared body for the three shoot-level organ removal methods."""
        if plant_id < 0 or shoot_id < 0:
            raise ValueError("Plant ID and shoot ID must be non-negative")

        self._check_context_alive()
        try:
            getattr(plantarch_wrapper, wrapper_fn_name)(self._plantarch_ptr, plant_id, shoot_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to remove {organ_description} from shoot {shoot_id} "
                f"of plant {plant_id}: {e}")

    # Shoot hierarchy traversal
    def getShootIDsByRank(self, plant_id: int) -> Dict[int, List[int]]:
        """
        Group a plant's shoot IDs by branching rank.

        Rank 0 is the base stem, rank 1 its direct branches, and so on. Shoots that have
        been pruned away are not included.

        Args:
            plant_id: ID of the plant instance

        Returns:
            Dict mapping rank to the list of shoot IDs at that rank. Ranks with no live
            shoots are omitted from the dict.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the plant does not exist

        Example:
            >>> by_rank = plantarch.getShootIDsByRank(plant_id)
            >>> print(f"{len(by_rank.get(1, []))} primary branches")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        self._check_context_alive()
        try:
            groups = plantarch_wrapper.getShootIDsByRank(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get shoot IDs by rank for plant {plant_id}: {e}")

        # Native returns one group per rank, indexed by rank, with empty groups for ranks
        # that have no live shoots. The dict form drops those empties.
        return {rank: shoot_ids for rank, shoot_ids in enumerate(groups) if shoot_ids}

    def getTerminalShootIDs(self, plant_id: int) -> List[int]:
        """
        Get the plant's terminal shoots -- those carrying no child shoots.

        These are the tips of the shoot tree. Note that this is a topological test rather
        than a botanical one: a shoot whose axis is continued by :meth:`appendShoot` has
        that continuation as a child and so is not terminal. Pruned shoots are omitted.

        Args:
            plant_id: ID of the plant instance

        Returns:
            List of terminal shoot IDs.

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If the plant does not exist

        Example:
            >>> tips = plantarch.getTerminalShootIDs(plant_id)
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        self._check_context_alive()
        try:
            return plantarch_wrapper.getTerminalShootIDs(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(
                f"Failed to get terminal shoots for plant {plant_id}: {e}")

    # Bulk pruning built on the traversal helpers
    def pruneShootsByRank(self, plant_id: int, min_rank: int) -> List[int]:
        """
        Prune every shoot at or above a given branching rank.

        This is the "remove higher-order branches" thinning operation: passing
        ``min_rank=3`` leaves the base stem and its first two orders of branching
        intact and cuts everything finer. Because :meth:`pruneBranch` already
        recurses into child shoots, only the shallowest shoot on each pruned axis is
        cut and the rest follow.

        Args:
            plant_id: ID of the plant instance
            min_rank: Lowest rank to prune. Must be at least 1 -- rank 0 is the base
                stem, and pruning it would destroy the plant.

        Returns:
            Ascending list of the shoot IDs actually cut. Shoots removed as a side
            effect of a shallower cut are not listed.

        Raises:
            ValueError: If plant_id is negative or min_rank is less than 1
            PlantArchitectureError: If the plant does not exist

        Note:
            To remove a whole plant use :meth:`deletePlantInstance`; to cut the base
            stem itself call :meth:`pruneBranch` directly.

        Example:
            >>> pruned = plantarch.pruneShootsByRank(plant_id, min_rank=3)
            >>> print(f"Cut {len(pruned)} higher-order branches")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if min_rank < 1:
            raise ValueError(
                f"min_rank must be at least 1, got {min_rank}. Rank 0 is the base stem; "
                "use deletePlantInstance() to remove the whole plant, or pruneBranch() "
                "to cut the base stem explicitly.")

        by_rank = self.getShootIDsByRank(plant_id)
        targets = {shoot_id
                   for rank, shoot_ids in by_rank.items() if rank >= min_rank
                   for shoot_id in shoot_ids}
        return self._pruneShallowest(plant_id, targets)

    def pruneShootSubtree(self, plant_id: int, shoot_id: int,
                          include_self: bool = True) -> List[int]:
        """
        Prune a shoot and everything growing off it.

        Args:
            plant_id: ID of the plant instance
            shoot_id: Root of the branch system to remove
            include_self: If True (default) the shoot itself is cut at node 0. If
                False the shoot is kept and only its child shoots are cut.

        Returns:
            Ascending list of the shoot IDs actually cut. Shoots removed as a side
            effect of a shallower cut are not listed.

        Raises:
            ValueError: If either identifier is negative
            PlantArchitectureError: If the plant or shoot does not exist

        Example:
            >>> # Remove a whole branch system
            >>> plantarch.pruneShootSubtree(plant_id, shoot_id=2)
            >>> # Keep the cane but strip everything growing off it
            >>> plantarch.pruneShootSubtree(plant_id, shoot_id=2, include_self=False)
        """
        if plant_id < 0 or shoot_id < 0:
            raise ValueError("Plant ID and shoot ID must be non-negative")

        if include_self:
            return self._pruneShallowest(plant_id, {shoot_id})
        return self._pruneShallowest(plant_id, set(self._liveChildShootIDs(plant_id, shoot_id)))

    def pruneTerminalShoots(self, plant_id: int, stride: int = 2) -> List[int]:
        """
        Thin a plant by pruning every *stride*-th terminal shoot.

        Terminal shoots are taken in ascending ID order and every ``stride``-th one
        starting from the first is cut, so ``stride=2`` removes about half the tips
        and ``stride=3`` about a third. The base stem is never cut.

        Args:
            plant_id: ID of the plant instance
            stride: Spacing between pruned tips. Must be at least 1; ``stride=1``
                prunes every terminal shoot.

        Returns:
            Ascending list of the shoot IDs actually cut.

        Raises:
            ValueError: If plant_id is negative or stride is less than 1
            PlantArchitectureError: If the plant does not exist

        Example:
            >>> pruned = plantarch.pruneTerminalShoots(plant_id, stride=2)
            >>> print(f"Thinned {len(pruned)} tips")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if stride < 1:
            raise ValueError(f"stride must be at least 1, got {stride}")

        targets = set()
        for index, shoot_id in enumerate(self.getTerminalShootIDs(plant_id)):
            if index % stride != 0:
                continue
            if self.getShootRank(plant_id, shoot_id) == 0:
                continue  # never cut the base stem
            targets.add(shoot_id)
        return self._pruneShallowest(plant_id, targets)

    def _childShootIDsOrEmpty(self, plant_id: int, shoot_id: int) -> List[int]:
        """Return a shoot's child IDs, or an empty list if it no longer resolves."""
        try:
            return self.getShootChildIDs(plant_id, shoot_id)
        except PlantArchitectureError:
            return []

    def _liveChildShootIDs(self, plant_id: int, shoot_id: int) -> List[int]:
        """Child shoot IDs that have not been pruned away, ascending."""
        # getChildShootIDs already excludes pruned shoots, so no second filter is needed.
        return sorted(set(self._childShootIDsOrEmpty(plant_id, shoot_id)))

    def _pruneShallowest(self, plant_id: int, target_shoot_ids) -> List[int]:
        """Prune every target that something shallower has not already removed.

        pruneBranch() recurses into child shoots, so cutting a shoot also empties
        every shoot descended from it. Targets are therefore visited in ascending
        shoot ID order -- a child shoot is always created after its parent and so
        always has the higher ID -- which puts each shoot after its ancestors. By
        the time a descendant of an already-cut shoot comes up it has nothing left
        on it and is skipped, so no shoot is cut twice and the returned list holds
        only the cuts that actually did something.
        """
        pruned = []
        for shoot_id in sorted(set(target_shoot_ids)):
            if self._isPrunedOrGone(plant_id, shoot_id):
                continue  # gone already, either pruned above or pruned earlier
            self.pruneBranch(plant_id, shoot_id, 0)
            pruned.append(shoot_id)
        return pruned

    def _isPrunedOrGone(self, plant_id: int, shoot_id: int) -> bool:
        """Whether a shoot has been pruned away or no longer resolves at all."""
        try:
            return self.isShootPruned(plant_id, shoot_id)
        except PlantArchitectureError:
            return True

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
        self._check_context_alive()
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

    def enableGroundClipping(self, ground_height: float = 0.0) -> None:
        """
        Enable automatic removal of plant organs that fall below the ground plane.

        Organ vertices below `ground_height` are clipped as plant geometry is
        built, which prevents drooping leaves and low branches from poking
        through a ground tile.

        Args:
            ground_height: Height of the ground plane (default 0.0)

        Raises:
            ValueError: If ground_height is not a number
            PlantArchitectureError: If the call fails

        Example:
            >>> plantarch.enableGroundClipping(0.0)
            >>> plantarch.advanceTime(30.0)
        """
        self._check_context_alive()

        if isinstance(ground_height, bool) or not isinstance(ground_height, (int, float)):
            raise ValueError(f"Ground height must be a number, got {type(ground_height).__name__}")

        try:
            plantarch_wrapper.enableGroundClipping(self._plantarch_ptr, float(ground_height))
        except Exception as e:
            raise PlantArchitectureError(f"Failed to enable ground clipping: {e}")

    def disableMessages(self) -> None:
        """
        Suppress standard output from the plantarchitecture plugin.

        This silences progress bars and informational messages the C++ plugin
        writes to stdout, including the "BVH not cached" warning emitted during
        the first growth steps of a collision-enabled canopy (before any plant
        geometry exists for the BVH to contain).

        Raises:
            PlantArchitectureError: If the call fails

        Example:
            >>> plantarch.disableMessages()
            >>> plantarch.advanceTime(30.0)  # runs quietly
        """
        self._check_context_alive()
        try:
            plantarch_wrapper.disableMessages(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to disable messages: {e}")

    def enableMessages(self) -> None:
        """
        Re-enable standard output from the plantarchitecture plugin.

        Raises:
            PlantArchitectureError: If the call fails

        Example:
            >>> plantarch.enableMessages()
        """
        self._check_context_alive()
        try:
            plantarch_wrapper.enableMessages(self._plantarch_ptr)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to enable messages: {e}")

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
        self._check_context_alive()
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

        self._check_context_alive()
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
        self._check_context_alive()
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

        self._check_context_alive()
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
            Collision avoidance must be enabled BEFORE calling this method -- the
            native call raises "Collision detection must be enabled before setting
            static obstacles" otherwise.
            Static obstacles cannot be modified or moved after being marked static.

        Example:
            >>> # Enable collision avoidance first
            >>> plantarch.enableSoftCollisionAvoidance()
            >>> # Then mark ground and building geometry as static
            >>> static_uuids = ground_uuids + building_uuids
            >>> plantarch.setStaticObstacles(static_uuids)
        """
        if not target_UUIDs:
            raise ValueError("target_UUIDs list cannot be empty")

        self._check_context_alive()
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

        self._check_context_alive()
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

        self._check_context_alive()
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

        self._check_context_alive()
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

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.writeQSMCylinderFile(
                    self._plantarch_ptr, plant_id, absolute_path
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to write QSM cylinder file to {filename}: {e}")

    def writePlantStructureUSD(self, plant_id: int, filename: Union[str, Path],
                               elastic_modulus: float = 5e9,
                               wood_density: float = 800.0,
                               damping_ratio: float = 0.1,
                               static_friction: float = 0.5,
                               dynamic_friction: float = 0.3,
                               restitution: float = 0.1,
                               organ_spring_stiffness: float = 10.0,
                               organ_spring_damping: float = 1.0,
                               leaf_mass_per_area: float = 0.05,
                               fruit_mass: float = 0.01,
                               flower_mass: float = 0.002,
                               solver_position_iterations: int = 32,
                               min_segment_length: float = 0.001) -> None:
        """
        Export plant structure as a USD articulated rigid body for NVIDIA IsaacSim physics.

        Each tube segment becomes a capsule-shaped rigid link connected by spherical joints.
        Spring/damper drives are derived from beam bending stiffness (E*I/L). Leaves, fruits,
        and flowers are represented as mass bodies attached by spring links.

        Args:
            plant_id: ID of the plant instance to export
            filename: Output file path (should have .usda extension)
            elastic_modulus: Young's modulus (Pa) for joint stiffness, K = E*I/L
            wood_density: Wood density (kg/m^3) used to compute mass from capsule volume
            damping_ratio: Joint damping ratio (dimensionless)
            static_friction: Static friction coefficient for collision material
            dynamic_friction: Dynamic friction coefficient for collision material
            restitution: Restitution (bounciness) for collision material
            organ_spring_stiffness: Spring stiffness (N*m/rad) for organ attachment joints
            organ_spring_damping: Damping (N*m*s/rad) for organ attachment joints
            leaf_mass_per_area: Leaf mass per unit area (kg/m^2)
            fruit_mass: Mass per fruit (kg)
            flower_mass: Mass per flower (kg)
            solver_position_iterations: PhysX articulation solver position iteration count
            min_segment_length: Minimum segment length (m); shorter segments are skipped

        Raises:
            ValueError: If plant_id is negative or filename is empty
            PlantArchitectureError: If plant doesn't exist or file cannot be written

        Example:
            >>> plantarch.writePlantStructureUSD(plant_id, "plant.usda")
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if not filename:
            raise ValueError("Filename cannot be empty")

        absolute_path = _resolve_user_path(filename)

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.writePlantStructureUSD(
                    self._plantarch_ptr, plant_id, absolute_path,
                    elastic_modulus, wood_density, damping_ratio,
                    static_friction, dynamic_friction, restitution,
                    organ_spring_stiffness, organ_spring_damping,
                    leaf_mass_per_area, fruit_mass, flower_mass,
                    solver_position_iterations, min_segment_length
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to write plant structure USD to {filename}: {e}")

    def registerGrowthFrame(self, plant_id: int, min_segment_length: float = 0.001) -> None:
        """
        Capture a snapshot of the plant's geometry as a growth animation frame.

        Call this after each :meth:`advanceTime` step to record the plant state for later
        animation export via :meth:`writePlantGrowthUSD`.

        Args:
            plant_id: ID of the plant instance to capture
            min_segment_length: Minimum segment length (m); shorter segments are skipped

        Raises:
            ValueError: If plant_id is negative
            PlantArchitectureError: If plant doesn't exist
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            plantarch_wrapper.registerGrowthFrame(self._plantarch_ptr, plant_id, min_segment_length)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to register growth frame for plant {plant_id}: {e}")

    def writePlantGrowthUSD(self, plant_id: int, filename: Union[str, Path],
                            seconds_per_frame: float = 1.0) -> None:
        """
        Export all registered growth frames as a time-sampled USD animation file.

        The resulting file can be imported directly into Blender. This is a visual-only
        export — no physics prims, joints, or collision shapes are written.

        Args:
            plant_id: ID of the plant instance to export
            filename: Output file path (should have .usda extension)
            seconds_per_frame: Duration in seconds each growth frame occupies (default: 1.0)

        Raises:
            ValueError: If plant_id is negative or filename is empty
            PlantArchitectureError: If plant doesn't exist or file cannot be written
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")
        if not filename:
            raise ValueError("Filename cannot be empty")

        absolute_path = _resolve_user_path(filename)

        self._check_context_alive()
        try:
            with _plantarchitecture_working_directory():
                plantarch_wrapper.writePlantGrowthUSD(
                    self._plantarch_ptr, plant_id, absolute_path, seconds_per_frame
                )
        except Exception as e:
            raise PlantArchitectureError(f"Failed to write plant growth USD to {filename}: {e}")

    def clearGrowthFrames(self, plant_id: int) -> None:
        """
        Clear stored growth animation frames for a plant.

        Args:
            plant_id: ID of the plant instance whose frames should be cleared

        Raises:
            ValueError: If plant_id is negative
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            plantarch_wrapper.clearGrowthFrames(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to clear growth frames for plant {plant_id}: {e}")

    def getGrowthFrameCount(self, plant_id: int) -> int:
        """
        Get the number of registered growth frames for a plant.

        Args:
            plant_id: ID of the plant instance to query

        Returns:
            Number of frames registered via :meth:`registerGrowthFrame`

        Raises:
            ValueError: If plant_id is negative
        """
        if plant_id < 0:
            raise ValueError("Plant ID must be non-negative")

        self._check_context_alive()
        try:
            return plantarch_wrapper.getGrowthFrameCount(self._plantarch_ptr, plant_id)
        except Exception as e:
            raise PlantArchitectureError(f"Failed to get growth frame count for plant {plant_id}: {e}")

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

        self._check_context_alive()
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
        # Parameter type validation
        if not isinstance(base_position, vec3):
            raise ValueError(f"base_position must be a vec3, got {type(base_position).__name__}")

        # Convert position to list for C++ interface
        position_list = [base_position.x, base_position.y, base_position.z]

        # Validate age
        if current_age < 0:
            raise ValueError(f"Age must be non-negative, got {current_age}")

        self._check_context_alive()
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

        self._check_context_alive()
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
            >>> from pyhelios.types import vec3, AxisRotation
            >>>
            >>> # REQUIRED: Load a plant model to define shoot types
            >>> plantarch.loadPlantModelFromLibrary("bean")
            >>>
            >>> # Create empty plant for custom building
            >>> plant_id = plantarch.addPlantInstance(vec3(0, 0, 0), 0.0)
            >>>
            >>> # Add base stem using a shoot type from the loaded model. Labels are
            >>> # species-specific: bean defines "unifoliate"/"trifoliate", almond
            >>> # defines "trunk"/"scaffold"/"proleptic"/"sylleptic". There is no
            >>> # generic "stem" type.
            >>> shoot_id = plantarch.addBaseStemShoot(
            ...     plant_id=plant_id,
            ...     current_node_number=1,
            ...     base_rotation=AxisRotation(0, 0, 0),  # Upright
            ...     internode_radius=0.01,       # 1cm radius
            ...     internode_length_max=0.1,    # 10cm max length
            ...     internode_length_scale_factor_fraction=1.0,
            ...     leaf_scale_factor_fraction=1.0,
            ...     radius_taper=0.9,            # Gradual taper
            ...     shoot_type_label="trifoliate"  # Must match loaded model
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

        self._check_context_alive()
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
            ...     shoot_type_label="trifoliate"
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

        self._check_context_alive()
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
            ...     shoot_type_label="trifoliate"
            ... )
            >>>
            >>> # Add second branch from opposite petiole
            >>> branch_id2 = plantarch.addChildShoot(
            ...     plant_id, main_shoot_id, 3, 1, AxisRotation(45, 270, 0),
            ...     0.005, 0.06, 1.0, 0.9, 0.8, "trifoliate", petiole_index=1
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

        self._check_context_alive()
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