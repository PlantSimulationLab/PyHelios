"""
Validation decorators for PyHelios plugin methods.

This module provides validation decorators that ensure parameter validation
for all plugin methods, maintaining consistency across the PyHelios API.
"""

from functools import wraps
from typing import Any, Callable, List, Optional, Union
from .plugins import (
    validate_band_label, validate_source_id, validate_source_id_list,
    validate_flux_value, validate_ray_count, validate_direction_vector,
    validate_angle_degrees, validate_scaling_factor, validate_uuid_list,
    validate_tree_id, validate_segment_resolution, validate_filename,
    validate_recursion_level, validate_subdivision_count, validate_time_value,
    # Photosynthesis validation functions
    validate_species_name, validate_temperature, validate_co2_concentration,
    validate_photosynthetic_rate, validate_conductance, validate_par_flux,
    validate_empirical_coefficients, validate_farquhar_coefficients,
    validate_vcmax, validate_jmax, validate_quantum_efficiency, validate_dark_respiration,
    validate_oxygen_concentration, validate_temperature_response_params,
    # Camera validation functions
    validate_camera_label, validate_band_labels_list, validate_antialiasing_samples
)
from .datatypes import validate_vec3, validate_rgb_color
from .core import validate_positive_value, validate_non_negative_value


# RadiationModel decorators
def validate_radiation_band_params(func: Callable) -> Callable:
    """Validate parameters for radiation band operations."""
    @wraps(func)
    def wrapper(self, old_label: str, new_label: str, *args, **kwargs):
        validate_band_label(old_label, "old_label", func.__name__)
        validate_band_label(new_label, "new_label", func.__name__)
        return func(self, old_label, new_label, *args, **kwargs)
    return wrapper


def validate_collimated_source_params(func: Callable) -> Callable:
    """Validate parameters for collimated radiation source creation."""
    @wraps(func)
    def wrapper(self, direction=None, *args, **kwargs):
        if direction is not None:
            # RadiationModel handles multiple types (vec3, SphericalCoord, tuple)
            # Let the method handle type conversion, but validate if it's vec3-like
            if hasattr(direction, 'x') and hasattr(direction, 'y') and hasattr(direction, 'z'):
                validate_direction_vector(direction, "direction", func.__name__)
        return func(self, direction, *args, **kwargs)
    return wrapper


def validate_sphere_source_params(func: Callable) -> Callable:
    """Validate parameters for sphere radiation source creation."""
    @wraps(func)
    def wrapper(self, position, radius: float, *args, **kwargs):
        validate_vec3(position, "position", func.__name__)
        validate_positive_value(radius, "radius", func.__name__)
        return func(self, position, radius, *args, **kwargs)
    return wrapper


def validate_sun_sphere_params(func: Callable) -> Callable:
    """Validate parameters for sun sphere radiation source."""
    @wraps(func)
    def wrapper(self, radius: float, zenith: float, azimuth: float, 
                position_scaling: float = 1.0, angular_width: float = 0.53, 
                flux_scaling: float = 1.0, *args, **kwargs):
        validate_positive_value(radius, "radius", func.__name__)
        validate_angle_degrees(zenith, "zenith", func.__name__)
        validate_angle_degrees(azimuth, "azimuth", func.__name__)
        validate_scaling_factor(position_scaling, param_name="position_scaling", function_name=func.__name__)
        validate_positive_value(angular_width, "angular_width", func.__name__)
        validate_scaling_factor(flux_scaling, param_name="flux_scaling", function_name=func.__name__)
        return func(self, radius, zenith, azimuth, position_scaling, angular_width, flux_scaling, *args, **kwargs)
    return wrapper


def validate_source_flux_multiple_params(func: Callable) -> Callable:
    """Validate parameters for setting multiple source flux."""
    @wraps(func)
    def wrapper(self, source_ids: List[int], label: str, flux: float, *args, **kwargs):
        validate_source_id_list(source_ids, "source_ids", func.__name__)
        validate_band_label(label, "label", func.__name__)
        validate_flux_value(flux, "flux", func.__name__)
        return func(self, source_ids, label, flux, *args, **kwargs)
    return wrapper


def validate_get_source_flux_params(func: Callable) -> Callable:
    """Validate parameters for getting source flux."""
    @wraps(func)
    def wrapper(self, source_id: int, label: str, *args, **kwargs):
        validate_source_id(source_id, "source_id", func.__name__)
        validate_band_label(label, "label", func.__name__)
        return func(self, source_id, label, *args, **kwargs)
    return wrapper


def validate_update_geometry_params(func: Callable) -> Callable:
    """Validate parameters for geometry updates."""
    @wraps(func)
    def wrapper(self, uuids: Optional[List[int]] = None, *args, **kwargs):
        if uuids is not None:
            validate_uuid_list(uuids, "uuids", func.__name__, allow_empty=True)
        return func(self, uuids, *args, **kwargs)
    return wrapper


def validate_run_band_params(func: Callable) -> Callable:
    """Validate parameters for running radiation bands."""
    @wraps(func)
    def wrapper(self, band_label: Union[str, List[str]], *args, **kwargs):
        if isinstance(band_label, str):
            validate_band_label(band_label, "band_label", func.__name__)
        elif isinstance(band_label, list):
            if not band_label:
                from .exceptions import create_validation_error
                raise create_validation_error(
                    f"Parameter cannot be empty",
                    param_name="band_label",
                    function_name=func.__name__,
                    expected_type="non-empty list",
                    actual_value=band_label,
                    suggestion="Provide at least one band label."
                )
            for i, label in enumerate(band_label):
                validate_band_label(label, f"band_label[{i}]", func.__name__)
        else:
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Parameter must be a string or list of strings, got {type(band_label).__name__}",
                param_name="band_label",
                function_name=func.__name__,
                expected_type="string or list of strings",
                actual_value=band_label,
                suggestion="Provide a band label string or list of band labels."
            )
        return func(self, band_label, *args, **kwargs)
    return wrapper


def validate_scattering_depth_params(func: Callable) -> Callable:
    """Validate parameters for scattering depth."""
    @wraps(func)
    def wrapper(self, label: str, depth: int, *args, **kwargs):
        validate_band_label(label, "label", func.__name__)
        if not isinstance(depth, int):
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Parameter must be an integer, got {type(depth).__name__}",
                param_name="depth",
                function_name=func.__name__,
                expected_type="integer",
                actual_value=depth,
                suggestion="Scattering depth must be an integer."
            )
        validate_non_negative_value(depth, "depth", func.__name__)
        return func(self, label, depth, *args, **kwargs)
    return wrapper


def validate_min_scatter_energy_params(func: Callable) -> Callable:
    """Validate parameters for minimum scatter energy."""
    @wraps(func)
    def wrapper(self, label: str, energy: float, *args, **kwargs):
        validate_band_label(label, "label", func.__name__)
        validate_positive_value(energy, "energy", func.__name__)
        return func(self, label, energy, *args, **kwargs)
    return wrapper


# WeberPennTree decorators
def validate_tree_uuid_params(func: Callable) -> Callable:
    """Validate tree ID parameters for WeberPennTree methods."""
    @wraps(func)
    def wrapper(self, tree_id: int, *args, **kwargs):
        validate_tree_id(tree_id, "tree_id", func.__name__)
        return func(self, tree_id, *args, **kwargs)
    return wrapper


def validate_recursion_params(func: Callable) -> Callable:
    """Validate recursion level parameters."""
    @wraps(func)
    def wrapper(self, level: int, *args, **kwargs):
        validate_recursion_level(level, "level", func.__name__)
        return func(self, level, *args, **kwargs)
    return wrapper


def validate_trunk_segment_params(func: Callable) -> Callable:
    """Validate trunk segment resolution parameters."""
    @wraps(func)
    def wrapper(self, trunk_segs: int, *args, **kwargs):
        validate_segment_resolution(trunk_segs, min_val=3, max_val=100, param_name="trunk_segs", function_name=func.__name__)
        return func(self, trunk_segs, *args, **kwargs)
    return wrapper


def validate_branch_segment_params(func: Callable) -> Callable:
    """Validate branch segment resolution parameters.""" 
    @wraps(func)
    def wrapper(self, branch_segs: int, *args, **kwargs):
        validate_segment_resolution(branch_segs, min_val=3, max_val=100, param_name="branch_segs", function_name=func.__name__)
        return func(self, branch_segs, *args, **kwargs)
    return wrapper


def validate_leaf_subdivisions_params(func: Callable) -> Callable:
    """Validate leaf subdivision parameters."""
    @wraps(func)
    def wrapper(self, leaf_segs_x: int, leaf_segs_y: int, *args, **kwargs):
        validate_subdivision_count(leaf_segs_x, "leaf_segs_x", func.__name__)
        validate_subdivision_count(leaf_segs_y, "leaf_segs_y", func.__name__)
        return func(self, leaf_segs_x, leaf_segs_y, *args, **kwargs)
    return wrapper


def validate_xml_file_params(func: Callable) -> Callable:
    """Validate XML file path parameters for WeberPennTree."""
    @wraps(func)
    def wrapper(self, filename: str, silent: bool = False, *args, **kwargs):
        from pathlib import Path
        from .exceptions import create_validation_error

        # Validate filename parameter
        validate_filename(filename, "filename", func.__name__, allowed_extensions=['.xml'])

        # Convert to Path for existence checking
        xml_path = Path(filename)

        # Check if file exists
        if not xml_path.exists():
            raise create_validation_error(
                f"XML file not found: {filename}",
                param_name="filename",
                function_name=func.__name__,
                expected_type="path to existing .xml file",
                actual_value=filename,
                suggestion=f"Ensure the file exists at: {xml_path.resolve()}"
            )

        # Validate silent parameter
        if not isinstance(silent, bool):
            raise create_validation_error(
                f"Parameter must be a boolean, got {type(silent).__name__}",
                param_name="silent",
                function_name=func.__name__,
                expected_type="bool",
                actual_value=silent,
                suggestion="Use True or False for silent parameter."
            )

        return func(self, filename, silent, *args, **kwargs)
    return wrapper


# EnergyBalance decorators
def validate_energy_run_params(func: Callable) -> Callable:
    """Validate parameters for energy balance run method."""
    @wraps(func)
    def wrapper(self, uuids: Optional[List[int]] = None, dt: Optional[float] = None, *args, **kwargs):
        if uuids is not None:
            validate_uuid_list(uuids, "uuids", func.__name__, allow_empty=False)
        if dt is not None:
            validate_positive_value(dt, "dt", func.__name__)
        return func(self, uuids, dt, *args, **kwargs)
    return wrapper


def validate_energy_band_params(func: Callable) -> Callable:
    """Validate parameters for energy balance band operations."""
    @wraps(func)
    def wrapper(self, band: Union[str, List[str]], *args, **kwargs):
        if isinstance(band, str):
            if not band.strip():
                from .exceptions import create_validation_error
                raise create_validation_error(
                    f"Parameter must be a non-empty string",
                    param_name="band",
                    function_name=func.__name__,
                    expected_type="non-empty string",
                    actual_value=repr(band),
                    suggestion="Provide a non-empty band name."
                )
        elif isinstance(band, list):
            if not band:
                from .exceptions import create_validation_error
                raise create_validation_error(
                    f"Parameter cannot be empty",
                    param_name="band",
                    function_name=func.__name__,
                    expected_type="non-empty list",
                    actual_value=band,
                    suggestion="Provide at least one band name."
                )
            for i, b in enumerate(band):
                if not isinstance(b, str) or not b.strip():
                    from .exceptions import create_validation_error
                    raise create_validation_error(
                        f"All band names must be non-empty strings, got {type(b).__name__} at index {i}",
                        param_name=f"band[{i}]",
                        function_name=func.__name__,
                        expected_type="non-empty string",
                        actual_value=b,
                        suggestion="All band names must be non-empty strings."
                    )
        else:
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Parameter must be a string or list of strings, got {type(band).__name__}",
                param_name="band",
                function_name=func.__name__,
                expected_type="string or list of strings",
                actual_value=band,
                suggestion="Provide a band name string or list of band names."
            )
        return func(self, band, *args, **kwargs)
    return wrapper


def validate_air_energy_params(func: Callable) -> Callable:
    """Validate parameters for air energy balance."""
    @wraps(func)
    def wrapper(self, canopy_height_m: Optional[float] = None, reference_height_m: Optional[float] = None, *args, **kwargs):
        if canopy_height_m is not None:
            validate_positive_value(canopy_height_m, "canopy_height_m", func.__name__)
        if reference_height_m is not None:
            validate_positive_value(reference_height_m, "reference_height_m", func.__name__)
        
        # Check that both parameters are provided together or neither
        if (canopy_height_m is None) != (reference_height_m is None):
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Canopy height and reference height must be provided together or omitted together",
                param_name="canopy_height_m, reference_height_m", 
                function_name=func.__name__,
                expected_type="both parameters provided or both None",
                actual_value=f"canopy_height_m={canopy_height_m}, reference_height_m={reference_height_m}",
                suggestion="Provide both canopy_height_m and reference_height_m, or omit both for automatic detection."
            )
            
        return func(self, canopy_height_m, reference_height_m, *args, **kwargs)
    return wrapper


def validate_evaluate_air_energy_params(func: Callable) -> Callable:
    """Validate parameters for evaluating air energy balance.""" 
    @wraps(func)
    def wrapper(self, dt_sec: float, time_advance_sec: float, UUIDs: Optional[List[int]] = None, *args, **kwargs):
        validate_time_value(dt_sec, "dt_sec", func.__name__)
        validate_time_value(time_advance_sec, "time_advance_sec", func.__name__)
        
        if time_advance_sec < dt_sec:
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Time advance ({time_advance_sec}) must be greater than or equal to time step ({dt_sec})",
                param_name="time_advance_sec",
                function_name=func.__name__,
                expected_type=f"number >= {dt_sec}",
                actual_value=time_advance_sec,
                suggestion=f"Use time_advance_sec >= {dt_sec}."
            )
            
        if UUIDs is not None:
            validate_uuid_list(UUIDs, "UUIDs", func.__name__, allow_empty=False)
            
        return func(self, dt_sec, time_advance_sec, UUIDs, *args, **kwargs)
    return wrapper


def validate_output_data_params(func: Callable) -> Callable:
    """Validate parameters for optional output data."""
    @wraps(func) 
    def wrapper(self, label: str, *args, **kwargs):
        if not isinstance(label, str):
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Parameter must be a string, got {type(label).__name__}",
                param_name="label",
                function_name=func.__name__,
                expected_type="string", 
                actual_value=label,
                suggestion="Provide a string label for the output data."
            )
        if not label.strip():
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Parameter cannot be empty or whitespace-only",
                param_name="label",
                function_name=func.__name__,
                expected_type="non-empty string",
                actual_value=repr(label),
                suggestion="Provide a non-empty label for the output data."
            )
        return func(self, label, *args, **kwargs)
    return wrapper


def validate_print_report_params(func: Callable) -> Callable:
    """Validate parameters for print report methods.""" 
    @wraps(func)
    def wrapper(self, UUIDs: Optional[List[int]] = None, *args, **kwargs):
        if UUIDs is not None:
            validate_uuid_list(UUIDs, "UUIDs", func.__name__, allow_empty=False)
        return func(self, UUIDs, *args, **kwargs)
    return wrapper


# Visualizer decorators
def validate_build_geometry_params(func: Callable) -> Callable:
    """Validate parameters for building visualizer geometry."""
    @wraps(func)
    def wrapper(self, context, uuids: Optional[List[int]] = None, *args, **kwargs):
        # Context validation - check it's the right type
        # Use both isinstance and string-based checking to handle import ordering issues
        from ..Context import Context
        is_valid_context = (
            isinstance(context, Context) or 
            (hasattr(context, '__class__') and 
             context.__class__.__name__ == 'Context' and 
             'pyhelios.Context' in context.__class__.__module__)
        )
        
        if not is_valid_context:
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Parameter must be a Context instance, got {type(context).__name__}",
                param_name="context",
                function_name=func.__name__,
                expected_type="Context",
                actual_value=context,
                suggestion="Provide a valid PyHelios Context instance."
            )
        
        if uuids is not None:
            validate_uuid_list(uuids, "uuids", func.__name__, allow_empty=True)
        return func(self, context, uuids, *args, **kwargs)
    return wrapper


def validate_print_window_params(func: Callable) -> Callable:
    """Validate parameters for printing window to file."""
    @wraps(func)
    def wrapper(self, filename: str, *args, **kwargs):
        validate_filename(filename, "filename", func.__name__, 
                         allowed_extensions=['.png', '.jpg', '.jpeg', '.bmp', '.tga'])
        return func(self, filename, *args, **kwargs)
    return wrapper


# Photosynthesis decorators
def validate_photosynthesis_species_params(func: Callable) -> Callable:
    """Validate photosynthesis species parameters."""
    @wraps(func)
    def wrapper(self, species: str, *args, **kwargs):
        validate_species_name(species, "species", func.__name__)
        return func(self, species, *args, **kwargs)
    return wrapper


def validate_photosynthesis_temperature_params(func: Callable) -> Callable:
    """Validate temperature parameters for photosynthesis."""
    @wraps(func)
    def wrapper(self, temperature: float, *args, **kwargs):
        validate_temperature(temperature, "temperature", func.__name__)
        return func(self, temperature, *args, **kwargs)
    return wrapper


def validate_photosynthesis_co2_params(func: Callable) -> Callable:
    """Validate CO2 concentration parameters."""
    @wraps(func)
    def wrapper(self, co2_concentration: float, *args, **kwargs):
        validate_co2_concentration(co2_concentration, "co2_concentration", func.__name__)
        return func(self, co2_concentration, *args, **kwargs)
    return wrapper


def validate_photosynthesis_par_params(func: Callable) -> Callable:
    """Validate PAR flux parameters."""
    @wraps(func)
    def wrapper(self, par_flux: float, *args, **kwargs):
        validate_par_flux(par_flux, "par_flux", func.__name__)
        return func(self, par_flux, *args, **kwargs)
    return wrapper


def validate_photosynthesis_conductance_params(func: Callable) -> Callable:
    """Validate conductance parameters."""
    @wraps(func)
    def wrapper(self, conductance: float, *args, **kwargs):
        validate_conductance(conductance, "conductance", func.__name__)
        return func(self, conductance, *args, **kwargs)
    return wrapper


def validate_empirical_model_params(func: Callable) -> Callable:
    """Validate empirical model coefficient parameters."""
    @wraps(func)
    def wrapper(self, coefficients, *args, **kwargs):
        validate_empirical_coefficients(coefficients, "coefficients", func.__name__)
        return func(self, coefficients, *args, **kwargs)
    return wrapper


def validate_farquhar_model_params(func: Callable) -> Callable:
    """Validate Farquhar model coefficient parameters."""
    @wraps(func)
    def wrapper(self, coefficients, *args, **kwargs):
        validate_farquhar_coefficients(coefficients, "coefficients", func.__name__)
        return func(self, coefficients, *args, **kwargs)
    return wrapper


def validate_vcmax_params(func: Callable) -> Callable:
    """Validate Vcmax parameters for Farquhar model."""
    @wraps(func)
    def wrapper(self, vcmax: float, *args, **kwargs):
        validate_vcmax(vcmax, "vcmax", func.__name__)
        return func(self, vcmax, *args, **kwargs)
    return wrapper


def validate_jmax_params(func: Callable) -> Callable:
    """Validate Jmax parameters for Farquhar model."""
    @wraps(func)
    def wrapper(self, jmax: float, *args, **kwargs):
        validate_jmax(jmax, "jmax", func.__name__)
        return func(self, jmax, *args, **kwargs)
    return wrapper


def validate_quantum_efficiency_params(func: Callable) -> Callable:
    """Validate quantum efficiency parameters."""
    @wraps(func)
    def wrapper(self, efficiency: float, *args, **kwargs):
        validate_quantum_efficiency(efficiency, "efficiency", func.__name__)
        return func(self, efficiency, *args, **kwargs)
    return wrapper


def validate_dark_respiration_params(func: Callable) -> Callable:
    """Validate dark respiration parameters."""
    @wraps(func)
    def wrapper(self, respiration: float, *args, **kwargs):
        validate_dark_respiration(respiration, "respiration", func.__name__)
        return func(self, respiration, *args, **kwargs)
    return wrapper


def validate_oxygen_concentration_params(func: Callable) -> Callable:
    """Validate oxygen concentration parameters."""
    @wraps(func)
    def wrapper(self, o2_concentration: float, *args, **kwargs):
        validate_oxygen_concentration(o2_concentration, "o2_concentration", func.__name__)
        return func(self, o2_concentration, *args, **kwargs)
    return wrapper


def validate_temperature_response_params(func: Callable) -> Callable:
    """Validate temperature response parameters."""
    @wraps(func)
    def wrapper(self, params, *args, **kwargs):
        validate_temperature_response_params(params, "params", func.__name__)
        return func(self, params, *args, **kwargs)
    return wrapper


def validate_photosynthesis_rate_params(func: Callable) -> Callable:
    """Validate photosynthetic rate parameters."""
    @wraps(func)
    def wrapper(self, rate: float, *args, **kwargs):
        validate_photosynthetic_rate(rate, "rate", func.__name__)
        return func(self, rate, *args, **kwargs)
    return wrapper


def validate_photosynthesis_uuid_params(func: Callable) -> Callable:
    """Validate UUID parameters for photosynthesis methods."""
    @wraps(func)
    def wrapper(self, uuids: Union[List[int], int], *args, **kwargs):
        if isinstance(uuids, int):
            # Single UUID - validate as non-negative integer (UUIDs start from 0)
            validate_non_negative_value(uuids, "uuids", func.__name__)
        elif isinstance(uuids, list):
            validate_uuid_list(uuids, "uuids", func.__name__, allow_empty=False)
        else:
            from .exceptions import create_validation_error
            raise create_validation_error(
                f"Parameter must be an integer or list of integers, got {type(uuids).__name__}",
                param_name="uuids",
                function_name=func.__name__,
                expected_type="integer or list of integers",
                actual_value=uuids,
                suggestion="Provide a UUID (integer) or list of UUIDs."
            )
        return func(self, uuids, *args, **kwargs)
    return wrapper


def validate_radiation_camera_params(func: Callable) -> Callable:
    """
    Validate parameters for addRadiationCamera method.

    Handles validation and type conversion for camera creation parameters:
    - camera_label: string validation
    - band_labels: list of strings validation
    - position: converts lists/tuples to vec3 if needed
    - lookat_or_direction: handles vec3 or SphericalCoord
    - antialiasing_samples: positive integer validation
    """
    @wraps(func)
    def wrapper(self, camera_label, band_labels, position, lookat_or_direction,
                camera_properties=None, antialiasing_samples: int = 100, *args, **kwargs):
        from ..wrappers.DataTypes import vec3, SphericalCoord, make_vec3

        # Validate basic parameters
        validated_label = validate_camera_label(camera_label, "camera_label", func.__name__)
        validated_bands = validate_band_labels_list(band_labels, "band_labels", func.__name__)
        validated_samples = validate_antialiasing_samples(antialiasing_samples, "antialiasing_samples", func.__name__)

        # Validate and convert position to vec3
        validated_position = validate_vec3(position, "position", func.__name__)

        # Validate lookat_or_direction (can be vec3, list/tuple, or SphericalCoord)
        validated_direction = None
        if hasattr(lookat_or_direction, 'radius') and hasattr(lookat_or_direction, 'elevation'):
            # SphericalCoord - validate directly (already proper type)
            validated_direction = lookat_or_direction
        else:
            # Assume vec3 or convertible to vec3
            validated_direction = validate_vec3(lookat_or_direction, "lookat_or_direction", func.__name__)

        # Validate camera properties if provided
        if camera_properties is not None:
            if not hasattr(camera_properties, 'to_array'):
                from ..validation.exceptions import create_validation_error
                raise create_validation_error(
                    f"camera_properties must be a CameraProperties instance or None, got {type(camera_properties).__name__}",
                    param_name="camera_properties",
                    function_name=func.__name__,
                    expected_type="CameraProperties or None",
                    actual_value=camera_properties,
                    suggestion="Use a CameraProperties instance or None for default properties."
                )

        return func(self, validated_label, validated_bands, validated_position, validated_direction,
                   camera_properties, validated_samples, *args, **kwargs)
    return wrapper