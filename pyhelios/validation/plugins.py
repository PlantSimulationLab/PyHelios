"""
Validation for PyHelios plugin parameters.

Provides comprehensive validation for plugin operations,
ensuring parameters are valid before reaching C++ plugin code.
"""

from typing import Any, List, Union
from .core import is_finite_numeric, validate_positive_value, validate_non_negative_value
from .datatypes import validate_vec3
from .exceptions import ValidationError, create_validation_error


def validate_wavelength_range(wavelength_min: float, wavelength_max: float, 
                            param_name_min: str = "wavelength_min", 
                            param_name_max: str = "wavelength_max",
                            function_name: str = None):
    """Validate wavelength range for radiation modeling."""
    if not is_finite_numeric(wavelength_min) or not is_finite_numeric(wavelength_max):
        raise create_validation_error(
            f"Wavelength bounds must be finite numbers, got min={wavelength_min}, max={wavelength_max}",
            param_name=f"{param_name_min}, {param_name_max}",
            function_name=function_name,
            expected_type="finite numbers",
            actual_value=f"min={wavelength_min}, max={wavelength_max}",
            suggestion="Use finite numeric values for wavelength bounds."
        )
    
    if wavelength_min <= 0 or wavelength_max <= 0:
        raise create_validation_error(
            f"Wavelength values must be positive, got min={wavelength_min}, max={wavelength_max}",
            param_name=f"{param_name_min}, {param_name_max}",
            function_name=function_name,
            expected_type="positive numbers",
            actual_value=f"min={wavelength_min}, max={wavelength_max}",
            suggestion="Wavelengths must be greater than 0."
        )
    
    if wavelength_min >= wavelength_max:
        raise create_validation_error(
            f"Wavelength minimum ({wavelength_min}) must be less than maximum ({wavelength_max})",
            param_name=f"{param_name_min}, {param_name_max}",
            function_name=function_name,
            expected_type="min < max",
            actual_value=(wavelength_min, wavelength_max),
            suggestion="Ensure wavelength_min < wavelength_max."
        )
    
    # Physical reasonableness check (UV to far-IR range in nanometers)
    if wavelength_min < 100 or wavelength_max > 100000:
        raise create_validation_error(
            f"Wavelength range [{wavelength_min}, {wavelength_max}] nm seems unrealistic",
            param_name=f"{param_name_min}, {param_name_max}",
            function_name=function_name,
            expected_type="wavelengths in range 100-100000 nm",
            actual_value=f"min={wavelength_min}, max={wavelength_max}",
            suggestion="Typical wavelength range is 100-100000 nm (UV to far-IR). "
                      "Provide wavelength values in nanometers (e.g., PAR: 400-700 nm)."
        )


def validate_flux_value(flux: float, param_name: str = "flux", function_name: str = None):
    """Validate radiation flux value."""
    if not is_finite_numeric(flux):
        raise create_validation_error(
            f"Parameter must be a finite number, got {flux} ({type(flux).__name__})",
            param_name=param_name,
            function_name=function_name,
            expected_type="finite number",
            actual_value=flux,
            suggestion="Flux values must be finite numbers (not NaN or infinity)."
        )
    
    if flux < 0:
        raise create_validation_error(
            f"Parameter must be non-negative, got {flux}",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-negative number",
            actual_value=flux,
            suggestion="Flux values cannot be negative."
        )


def validate_ray_count(count: int, param_name: str = "ray_count", function_name: str = None):
    """Validate ray count for radiation simulations."""
    if not isinstance(count, int):
        raise create_validation_error(
            f"Parameter must be an integer, got {type(count).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer",
            actual_value=count,
            suggestion="Ray count must be a positive integer."
        )
    
    if count <= 0:
        raise create_validation_error(
            f"Parameter must be positive, got {count}",
            param_name=param_name,
            function_name=function_name,
            expected_type="positive integer",
            actual_value=count,
            suggestion="Ray count must be greater than 0."
        )
    
    if count > 10_000_000:  # 10 million rays as reasonable upper limit
        raise create_validation_error(
            f"Parameter {count:,} is very large and may cause memory issues",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer <= 10,000,000",
            actual_value=count,
            suggestion="Consider using fewer rays (< 10,000,000) for practical simulations."
        )


def validate_direction_vector(direction: Any, param_name: str = "direction", function_name: str = None):
    """Validate direction vector for radiation sources."""
    validate_vec3(direction, param_name, function_name)
    
    # Check for zero vector
    if hasattr(direction, 'x') and hasattr(direction, 'y') and hasattr(direction, 'z'):
        magnitude_squared = direction.x**2 + direction.y**2 + direction.z**2
        if magnitude_squared == 0:
            raise create_validation_error(
                f"Direction vector cannot be zero vector (0,0,0)",
                param_name=param_name,
                function_name=function_name,
                expected_type="non-zero vec3",
                actual_value=direction,
                suggestion="Provide a direction vector with non-zero magnitude."
            )


def validate_band_label(label: str, param_name: str = "band_label", function_name: str = None):
    """Validate radiation band label."""
    if not isinstance(label, str):
        raise create_validation_error(
            f"Parameter must be a string, got {type(label).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="string",
            actual_value=label,
            suggestion="Band labels must be strings."
        )
    
    if not label.strip():
        raise create_validation_error(
            f"Parameter cannot be empty or whitespace-only",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty string",
            actual_value=repr(label),
            suggestion="Provide a non-empty band label."
        )


def validate_source_id(source_id: int, param_name: str = "source_id", function_name: str = None):
    """Validate radiation source ID."""
    if not isinstance(source_id, int):
        raise create_validation_error(
            f"Parameter must be an integer, got {type(source_id).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer",
            actual_value=source_id,
            suggestion="Source IDs are integers returned by add*RadiationSource methods."
        )
    
    if source_id < 0:
        raise create_validation_error(
            f"Parameter must be non-negative, got {source_id}",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-negative integer",
            actual_value=source_id,
            suggestion="Source IDs are non-negative integers."
        )


def validate_source_id_list(source_ids: List[int], param_name: str = "source_ids", function_name: str = None):
    """Validate list of radiation source IDs."""
    if not isinstance(source_ids, list):
        raise create_validation_error(
            f"Parameter must be a list, got {type(source_ids).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="list of integers",
            actual_value=source_ids,
            suggestion="Provide a list of source IDs."
        )
    
    if not source_ids:
        raise create_validation_error(
            f"Parameter cannot be empty",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty list",
            actual_value=source_ids,
            suggestion="Provide at least one source ID."
        )
    
    for i, source_id in enumerate(source_ids):
        validate_source_id(source_id, f"{param_name}[{i}]", function_name)


def validate_wpt_parameters(scale_factor: float = 1.0, recursion_level: int = 5, 
                           segment_resolution: int = 10, param_prefix: str = "WPT"):
    """Validate WeberPennTree generation parameters."""
    if not is_finite_numeric(scale_factor):
        raise create_validation_error(
            f"Scale factor must be a finite number, got {scale_factor} ({type(scale_factor).__name__})",
            param_name=f"{param_prefix}_scale_factor",
            expected_type="finite number",
            actual_value=scale_factor,
            suggestion="Scale factor must be a finite number."
        )
    
    if scale_factor <= 0:
        raise create_validation_error(
            f"Scale factor must be positive, got {scale_factor}",
            param_name=f"{param_prefix}_scale_factor",
            expected_type="positive number",
            actual_value=scale_factor,
            suggestion="Scale factor must be greater than 0."
        )
    
    if scale_factor > 100:
        raise create_validation_error(
            f"Scale factor {scale_factor} is very large and may cause issues",
            param_name=f"{param_prefix}_scale_factor",
            expected_type="reasonable scale factor (0.1-10)",
            actual_value=scale_factor,
            suggestion="Typical scale factors are 0.1-10. Large values may cause performance issues."
        )
    
    if not isinstance(recursion_level, int):
        raise create_validation_error(
            f"Recursion level must be an integer, got {type(recursion_level).__name__}",
            param_name=f"{param_prefix}_recursion_level",
            expected_type="integer",
            actual_value=recursion_level,
            suggestion="Recursion level must be an integer."
        )
    
    if recursion_level < 1 or recursion_level > 10:
        raise create_validation_error(
            f"Recursion level must be between 1-10, got {recursion_level}",
            param_name=f"{param_prefix}_recursion_level",
            expected_type="integer in range 1-10",
            actual_value=recursion_level,
            suggestion="Use recursion level between 1-10 for realistic tree generation."
        )
    
    if not isinstance(segment_resolution, int):
        raise create_validation_error(
            f"Segment resolution must be an integer, got {type(segment_resolution).__name__}",
            param_name=f"{param_prefix}_segment_resolution",
            expected_type="integer",
            actual_value=segment_resolution,
            suggestion="Segment resolution must be an integer."
        )
    
    if segment_resolution < 3 or segment_resolution > 50:
        raise create_validation_error(
            f"Segment resolution must be between 3-50, got {segment_resolution}",
            param_name=f"{param_prefix}_segment_resolution",
            expected_type="integer in range 3-50",
            actual_value=segment_resolution,
            suggestion="Use segment resolution between 3-50 for good performance and quality."
        )


def validate_time_value(time_val: Any, param_name: str = "time", function_name: str = None):
    """Validate time values for energy balance calculations."""
    if not is_finite_numeric(time_val):
        raise create_validation_error(
            f"Parameter must be a finite number, got {time_val} ({type(time_val).__name__})",
            param_name=param_name,
            function_name=function_name,
            expected_type="finite number",
            actual_value=time_val,
            suggestion="Time values must be finite numbers (not NaN or infinity)."
        )
    
    if time_val < 0:
        raise create_validation_error(
            f"Parameter cannot be negative, got {time_val}",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-negative number",
            actual_value=time_val,
            suggestion="Time values must be >= 0."
        )


def validate_physical_quantity(value: Any, quantity_name: str, 
                             expected_units: str = None, min_val: float = None, 
                             max_val: float = None, param_name: str = None,
                             function_name: str = None):
    """Validate physical quantity values with optional range checking."""
    param_name = param_name or quantity_name.lower().replace(' ', '_')
    
    if not is_finite_numeric(value):
        units_info = f" ({expected_units})" if expected_units else ""
        raise create_validation_error(
            f"{quantity_name}{units_info} must be a finite number, got {value} ({type(value).__name__})",
            param_name=param_name,
            function_name=function_name,
            expected_type="finite number",
            actual_value=value,
            suggestion=f"Provide a finite numeric value for {quantity_name}."
        )
    
    if min_val is not None and value < min_val:
        units_info = f" {expected_units}" if expected_units else ""
        raise create_validation_error(
            f"{quantity_name} must be >= {min_val}{units_info}, got {value}",
            param_name=param_name,
            function_name=function_name,
            expected_type=f"number >= {min_val}",
            actual_value=value,
            suggestion=f"Use a value >= {min_val} for {quantity_name}."
        )
    
    if max_val is not None and value > max_val:
        units_info = f" {expected_units}" if expected_units else ""
        raise create_validation_error(
            f"{quantity_name} must be <= {max_val}{units_info}, got {value}",
            param_name=param_name,
            function_name=function_name,
            expected_type=f"number <= {max_val}",
            actual_value=value,
            suggestion=f"Use a value <= {max_val} for {quantity_name}."
        )


def validate_tree_id(tree_id: Any, param_name: str = "tree_id", function_name: str = None):
    """Validate WeberPennTree tree ID."""
    if not isinstance(tree_id, int):
        raise create_validation_error(
            f"Parameter must be an integer, got {type(tree_id).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer",
            actual_value=tree_id,
            suggestion="Tree IDs are integers returned by buildTree()."
        )
    
    if tree_id < 0:
        raise create_validation_error(
            f"Parameter must be non-negative, got {tree_id}",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-negative integer",
            actual_value=tree_id,
            suggestion="Tree IDs are non-negative integers."
        )


def validate_segment_resolution(resolution: Any, min_val: int = 3, max_val: int = 100, 
                              param_name: str = "resolution", function_name: str = None):
    """Validate segment resolution parameters for tree generation."""
    if not isinstance(resolution, int):
        raise create_validation_error(
            f"Parameter must be an integer, got {type(resolution).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer",
            actual_value=resolution,
            suggestion="Segment resolution must be an integer."
        )
    
    if resolution < min_val or resolution > max_val:
        raise create_validation_error(
            f"Parameter must be between {min_val}-{max_val}, got {resolution}",
            param_name=param_name,
            function_name=function_name,
            expected_type=f"integer in range {min_val}-{max_val}",
            actual_value=resolution,
            suggestion=f"Use resolution between {min_val}-{max_val} for good performance and quality."
        )


def validate_angle_degrees(angle: Any, param_name: str = "angle", function_name: str = None):
    """Validate angle values in degrees."""
    if not is_finite_numeric(angle):
        raise create_validation_error(
            f"Parameter must be a finite number, got {angle} ({type(angle).__name__})",
            param_name=param_name,
            function_name=function_name,
            expected_type="finite number",
            actual_value=angle,
            suggestion="Angle values must be finite numbers (not NaN or infinity)."
        )
    
    # Note: We don't restrict angle range since angles can be outside [0, 360] for various reasons
    # The underlying C++ code will handle angle normalization


def validate_scaling_factor(scale: Any, min_val: float = 0.001, max_val: float = 1000.0,
                           param_name: str = "scaling_factor", function_name: str = None):
    """Validate scaling factor parameters."""
    if not is_finite_numeric(scale):
        raise create_validation_error(
            f"Parameter must be a finite number, got {scale} ({type(scale).__name__})",
            param_name=param_name,
            function_name=function_name,
            expected_type="finite number",
            actual_value=scale,
            suggestion="Scaling factors must be finite numbers."
        )
    
    if scale <= 0:
        raise create_validation_error(
            f"Parameter must be positive, got {scale}",
            param_name=param_name,
            function_name=function_name,
            expected_type="positive number",
            actual_value=scale,
            suggestion="Scaling factors must be greater than 0."
        )
    
    if scale < min_val or scale > max_val:
        raise create_validation_error(
            f"Parameter {scale} is outside reasonable range [{min_val}, {max_val}]",
            param_name=param_name,
            function_name=function_name,
            expected_type=f"number in range [{min_val}, {max_val}]",
            actual_value=scale,
            suggestion=f"Use scaling factors between {min_val} and {max_val} to avoid numerical issues."
        )


def validate_filename(filename: Any, param_name: str = "filename", function_name: str = None,
                     allowed_extensions: List[str] = None):
    """Validate filename parameters for file operations."""
    if not isinstance(filename, str):
        raise create_validation_error(
            f"Parameter must be a string, got {type(filename).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="string",
            actual_value=filename,
            suggestion="Filename must be a string."
        )
    
    if not filename.strip():
        raise create_validation_error(
            f"Parameter cannot be empty or whitespace-only",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty string",
            actual_value=repr(filename),
            suggestion="Provide a non-empty filename."
        )
    
    # Check for potentially problematic characters in the basename only
    # (full paths may contain valid characters like ':' in Windows drive letters C:\)
    import os
    import ntpath
    # Handle both Windows and Unix paths correctly regardless of current platform
    # Use ntpath for Windows-style paths (backslash or drive letter pattern)
    if '\\' in filename or (len(filename) >= 2 and filename[1] == ':'):
        basename = ntpath.basename(filename)
    else:
        basename = os.path.basename(filename)
    # On Windows, colons are only valid after drive letters, not in filenames
    # On all platforms, these characters are problematic in filenames
    invalid_chars = ['<', '>', '"', '|', '?', '*']
    # Add colon check for the basename (not allowed in filenames on any platform)
    if ':' in basename:
        invalid_chars.append(':')
    if any(char in basename for char in invalid_chars):
        raise create_validation_error(
            f"Filename contains invalid characters: {basename}",
            param_name=param_name,
            function_name=function_name,
            expected_type="valid filename",
            actual_value=filename,
            suggestion="Avoid characters: < > : \" | ? * in filename"
        )
    
    # Validate file extension if specified
    if allowed_extensions:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            raise create_validation_error(
                f"File extension '{ext}' not allowed. Must be one of: {', '.join(allowed_extensions)}",
                param_name=param_name,
                function_name=function_name,
                expected_type=f"filename with extension {allowed_extensions}",
                actual_value=filename,
                suggestion=f"Use a filename ending with one of: {', '.join(allowed_extensions)}"
            )


def validate_uuid_list(uuids: Any, param_name: str = "uuids", function_name: str = None,
                      allow_empty: bool = False):
    """Validate UUID list parameters."""
    if not isinstance(uuids, list):
        raise create_validation_error(
            f"Parameter must be a list, got {type(uuids).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="list of integers",
            actual_value=uuids,
            suggestion="Provide a list of UUID integers."
        )
    
    if not allow_empty and not uuids:
        raise create_validation_error(
            f"Parameter cannot be empty",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty list",
            actual_value=uuids,
            suggestion="Provide at least one UUID."
        )
    
    for i, uuid in enumerate(uuids):
        if not isinstance(uuid, int):
            raise create_validation_error(
                f"UUID at index {i} must be an integer, got {type(uuid).__name__}",
                param_name=f"{param_name}[{i}]",
                function_name=function_name,
                expected_type="integer",
                actual_value=uuid,
                suggestion="UUIDs are integers returned by geometry creation methods."
            )
        
        if uuid < 0:
            raise create_validation_error(
                f"UUID at index {i} must be non-negative, got {uuid}",
                param_name=f"{param_name}[{i}]",
                function_name=function_name,
                expected_type="non-negative integer",
                actual_value=uuid,
                suggestion="UUIDs are non-negative integers."
            )


def validate_positive_integer_range(value: Any, min_val: int = 1, max_val: int = 50,
                                   param_name: str = "value", function_name: str = None):
    """Validate positive integer within a specified range."""
    if not isinstance(value, int):
        raise create_validation_error(
            f"Parameter must be an integer, got {type(value).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="integer",
            actual_value=value,
            suggestion="Provide an integer value."
        )
    
    if value < min_val or value > max_val:
        raise create_validation_error(
            f"Parameter must be between {min_val}-{max_val}, got {value}",
            param_name=param_name,
            function_name=function_name,
            expected_type=f"integer in range {min_val}-{max_val}",
            actual_value=value,
            suggestion=f"Use a value between {min_val} and {max_val}."
        )


def validate_recursion_level(level: Any, param_name: str = "recursion_level", function_name: str = None):
    """Validate recursion level for tree generation."""
    validate_positive_integer_range(level, min_val=1, max_val=10, param_name=param_name, function_name=function_name)


def validate_subdivision_count(count: Any, param_name: str = "subdivision_count", function_name: str = None):
    """Validate subdivision count parameters."""
    validate_positive_integer_range(count, min_val=1, max_val=20, param_name=param_name, function_name=function_name)


# ============================================================================
# Photosynthesis Plugin Validation Functions
# ============================================================================

def validate_species_name(species: Any, param_name: str = "species", function_name: str = None):
    """Validate species name for photosynthesis library."""
    from ..types.photosynthesis import validate_species_name as _validate_species
    
    if not isinstance(species, str):
        raise create_validation_error(
            f"Parameter must be a string, got {type(species).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="string",
            actual_value=species,
            suggestion="Species names must be strings."
        )
    
    try:
        return _validate_species(species)
    except ValueError as e:
        raise create_validation_error(
            str(e),
            param_name=param_name,
            function_name=function_name,
            expected_type="valid species name",
            actual_value=species,
            suggestion="Use one of the available species or aliases. See get_available_species()."
        )


def validate_temperature(temperature: Any, param_name: str = "temperature", function_name: str = None):
    """Validate temperature values for photosynthesis calculations."""
    validate_physical_quantity(
        value=temperature,
        quantity_name="Temperature",
        expected_units="K",
        min_val=200.0,  # Absolute minimum for biological processes
        max_val=400.0,  # Absolute maximum for biological processes
        param_name=param_name,
        function_name=function_name
    )


def validate_co2_concentration(co2: Any, param_name: str = "co2_concentration", function_name: str = None):
    """Validate CO2 concentration values for photosynthesis calculations."""
    validate_physical_quantity(
        value=co2,
        quantity_name="CO2 concentration",
        expected_units="ppm",
        min_val=50.0,   # Well below atmospheric levels
        max_val=2000.0, # Well above atmospheric levels for controlled environments
        param_name=param_name,
        function_name=function_name
    )


def validate_photosynthetic_rate(rate: Any, param_name: str = "photosynthetic_rate", function_name: str = None):
    """Validate photosynthetic rate values."""
    validate_physical_quantity(
        value=rate,
        quantity_name="Photosynthetic rate",
        expected_units="μmol/m²/s",
        min_val=0.0,    # Cannot be negative
        max_val=100.0,  # Reasonable upper limit for most plants
        param_name=param_name,
        function_name=function_name
    )


def validate_conductance(conductance: Any, param_name: str = "conductance", function_name: str = None):
    """Validate conductance values for photosynthesis calculations."""
    validate_physical_quantity(
        value=conductance,
        quantity_name="Conductance",
        expected_units="mol/m²/s",
        min_val=0.0,   # Cannot be negative
        max_val=10.0,  # Reasonable upper limit
        param_name=param_name,
        function_name=function_name
    )


def validate_par_flux(par_flux: Any, param_name: str = "PAR_flux", function_name: str = None):
    """Validate PAR flux values for photosynthesis calculations."""
    validate_physical_quantity(
        value=par_flux,
        quantity_name="PAR flux",
        expected_units="μmol/m²/s",
        min_val=0.0,     # Cannot be negative
        max_val=3000.0,  # Very high light conditions
        param_name=param_name,
        function_name=function_name
    )


def validate_empirical_coefficients(coefficients: Any, param_name: str = "coefficients", function_name: str = None):
    """Validate empirical model coefficients array or dataclass."""
    # Accept dataclass instances with to_array() method
    if hasattr(coefficients, 'to_array') and callable(getattr(coefficients, 'to_array')):
        return  # Dataclass instances are valid
    
    if not isinstance(coefficients, (list, tuple)):
        raise create_validation_error(
            f"Parameter must be a list or tuple, got {type(coefficients).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="list or tuple of numbers",
            actual_value=coefficients,
            suggestion="Provide coefficients as a list or tuple of numbers."
        )
    
    if len(coefficients) < 10:
        raise create_validation_error(
            f"Empirical model coefficients need at least 10 elements, got {len(coefficients)}",
            param_name=param_name,
            function_name=function_name,
            expected_type="list with >= 10 elements",
            actual_value=f"length {len(coefficients)}",
            suggestion="Provide all 10 empirical model coefficients: [Tref, Ci_ref, Asat, theta, Tmin, Topt, q, R, ER, kC]."
        )
    
    for i, coeff in enumerate(coefficients[:10]):
        if not is_finite_numeric(coeff):
            raise create_validation_error(
                f"Coefficient at index {i} must be a finite number, got {coeff} ({type(coeff).__name__})",
                param_name=f"{param_name}[{i}]",
                function_name=function_name,
                expected_type="finite number",
                actual_value=coeff,
                suggestion="All coefficients must be finite numbers (not NaN or infinity)."
            )


def validate_farquhar_coefficients(coefficients: Any, param_name: str = "coefficients", function_name: str = None):
    """Validate Farquhar model coefficients array or dataclass."""
    # Accept dataclass instances with to_array() method
    if hasattr(coefficients, 'to_array') and callable(getattr(coefficients, 'to_array')):
        return  # Dataclass instances are valid
        
    if not isinstance(coefficients, (list, tuple)):
        raise create_validation_error(
            f"Parameter must be a list or tuple, got {type(coefficients).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="list or tuple of numbers",
            actual_value=coefficients,
            suggestion="Provide coefficients as a list or tuple of numbers."
        )
    
    if len(coefficients) < 18:
        raise create_validation_error(
            f"Farquhar model coefficients need at least 18 elements, got {len(coefficients)}",
            param_name=param_name,
            function_name=function_name,
            expected_type="list with >= 18 elements",
            actual_value=f"length {len(coefficients)}",
            suggestion="Provide all 18 Farquhar model coefficients including temperature response parameters."
        )
    
    for i, coeff in enumerate(coefficients[:18]):
        if not is_finite_numeric(coeff):
            raise create_validation_error(
                f"Coefficient at index {i} must be a finite number, got {coeff} ({type(coeff).__name__})",
                param_name=f"{param_name}[{i}]",
                function_name=function_name,
                expected_type="finite number",
                actual_value=coeff,
                suggestion="All coefficients must be finite numbers (not NaN or infinity)."
            )


def validate_vcmax(vcmax: Any, param_name: str = "Vcmax", function_name: str = None):
    """Validate maximum carboxylation rate (Vcmax) parameter.""" 
    if vcmax == -1.0:
        # Special case: -1 indicates uninitialized parameter (valid in Farquhar model)
        return
    
    validate_physical_quantity(
        value=vcmax,
        quantity_name="Maximum carboxylation rate (Vcmax)",
        expected_units="μmol/m²/s",
        min_val=1.0,    # Reasonable minimum
        max_val=300.0,  # Reasonable maximum for most plants
        param_name=param_name,
        function_name=function_name
    )


def validate_jmax(jmax: Any, param_name: str = "Jmax", function_name: str = None):
    """Validate maximum electron transport rate (Jmax) parameter."""
    if jmax == -1.0:
        # Special case: -1 indicates uninitialized parameter (valid in Farquhar model)
        return
    
    validate_physical_quantity(
        value=jmax,
        quantity_name="Maximum electron transport rate (Jmax)",
        expected_units="μmol/m²/s",
        min_val=5.0,    # Reasonable minimum
        max_val=500.0,  # Reasonable maximum for most plants
        param_name=param_name,
        function_name=function_name
    )


def validate_quantum_efficiency(alpha: Any, param_name: str = "alpha", function_name: str = None):
    """Validate quantum efficiency (alpha) parameter."""
    if alpha == -1.0:
        # Special case: -1 indicates uninitialized parameter (valid in Farquhar model)
        return
    
    validate_physical_quantity(
        value=alpha,
        quantity_name="Quantum efficiency (alpha)",
        expected_units="unitless",
        min_val=0.01,   # Very low efficiency
        max_val=1.0,    # Theoretical maximum
        param_name=param_name,
        function_name=function_name
    )


def validate_dark_respiration(rd: Any, param_name: str = "Rd", function_name: str = None):
    """Validate dark respiration rate (Rd) parameter."""
    if rd == -1.0:
        # Special case: -1 indicates uninitialized parameter (valid in Farquhar model)
        return
    
    validate_physical_quantity(
        value=rd,
        quantity_name="Dark respiration rate (Rd)",
        expected_units="μmol/m²/s",
        min_val=0.1,   # Reasonable minimum
        max_val=20.0,  # Reasonable maximum
        param_name=param_name,
        function_name=function_name
    )


def validate_oxygen_concentration(o2: Any, param_name: str = "oxygen", function_name: str = None):
    """Validate oxygen concentration for photosynthesis calculations."""
    validate_physical_quantity(
        value=o2,
        quantity_name="Oxygen concentration",
        expected_units="mmol/mol",
        min_val=50.0,   # Very low O2 environment
        max_val=500.0,  # Very high O2 environment  
        param_name=param_name,
        function_name=function_name
    )


def validate_temperature_response_params(value_at_25c: Any, dha: Any = None, topt: Any = None, dhd: Any = None,
                                       param_prefix: str = "", function_name: str = None):
    """Validate temperature response parameters for photosynthetic processes."""
    # Validate base value at 25°C
    validate_physical_quantity(
        value=value_at_25c,
        quantity_name=f"{param_prefix} value at 25°C",
        min_val=0.1,
        param_name=f"{param_prefix}_at_25C",
        function_name=function_name
    )
    
    # Validate optional temperature response parameters
    if dha is not None and dha >= 0:  # -1 means not provided
        validate_physical_quantity(
            value=dha,
            quantity_name=f"{param_prefix} activation energy (dHa)",
            expected_units="kJ/mol",
            min_val=10.0,   # Reasonable minimum activation energy
            max_val=150.0,  # Reasonable maximum activation energy
            param_name=f"{param_prefix}_dHa",
            function_name=function_name
        )
    
    if topt is not None and topt >= 0:  # -1 means not provided
        validate_physical_quantity(
            value=topt,
            quantity_name=f"{param_prefix} optimum temperature",
            expected_units="°C",
            min_val=15.0,   # Reasonable minimum
            max_val=55.0,   # Reasonable maximum
            param_name=f"{param_prefix}_Topt",
            function_name=function_name
        )
    
    if dhd is not None and dhd >= 0:  # -1 means not provided
        validate_physical_quantity(
            value=dhd,
            quantity_name=f"{param_prefix} deactivation energy (dHd)",
            expected_units="kJ/mol",
            min_val=100.0,  # Reasonable minimum deactivation energy
            max_val=1000.0, # Reasonable maximum deactivation energy
            param_name=f"{param_prefix}_dHd",
            function_name=function_name
        )


def validate_camera_label(label: str, param_name: str = "camera_label", function_name: str = None) -> str:
    """Validate camera label for radiation camera operations."""
    if not isinstance(label, str):
        raise create_validation_error(
            f"Camera label must be a string, got {type(label).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="str",
            actual_value=label,
            suggestion="Use a string label for the camera."
        )

    if not label or label.strip() == "":
        raise create_validation_error(
            "Camera label cannot be empty",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty string",
            actual_value=label,
            suggestion="Provide a non-empty string label for the camera."
        )

    return label.strip()


def validate_band_labels_list(band_labels: List[str], param_name: str = "band_labels", function_name: str = None) -> List[str]:
    """Validate list of band labels for camera operations."""
    if not isinstance(band_labels, (list, tuple)):
        raise create_validation_error(
            f"Band labels must be a list or tuple, got {type(band_labels).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="List[str]",
            actual_value=band_labels,
            suggestion="Provide a list of string band labels."
        )

    if len(band_labels) == 0:
        raise create_validation_error(
            "Band labels list cannot be empty",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty list",
            actual_value=band_labels,
            suggestion="Provide at least one band label."
        )

    validated_labels = []
    for i, label in enumerate(band_labels):
        if not isinstance(label, str):
            raise create_validation_error(
                f"Band label at index {i} must be a string, got {type(label).__name__}",
                param_name=f"{param_name}[{i}]",
                function_name=function_name,
                expected_type="str",
                actual_value=label,
                suggestion="All band labels must be strings."
            )

        if not label or label.strip() == "":
            raise create_validation_error(
                f"Band label at index {i} cannot be empty",
                param_name=f"{param_name}[{i}]",
                function_name=function_name,
                expected_type="non-empty string",
                actual_value=label,
                suggestion="All band labels must be non-empty strings."
            )

        validated_labels.append(label.strip())

    return validated_labels


def validate_antialiasing_samples(samples: int, param_name: str = "antialiasing_samples", function_name: str = None) -> int:
    """Validate antialiasing samples count."""
    if not isinstance(samples, int):
        raise create_validation_error(
            f"Antialiasing samples must be an integer, got {type(samples).__name__}",
            param_name=param_name,
            function_name=function_name,
            expected_type="int",
            actual_value=samples,
            suggestion="Provide an integer number of antialiasing samples."
        )

    if samples <= 0:
        raise create_validation_error(
            f"Antialiasing samples must be positive, got {samples}",
            param_name=param_name,
            function_name=function_name,
            expected_type="positive integer",
            actual_value=samples,
            suggestion="Use a positive number of antialiasing samples (typically 1-1000)."
        )

    # Practical upper limit check
    if samples > 10000:
        raise create_validation_error(
            f"Antialiasing samples ({samples}) is very high and may cause performance issues",
            param_name=param_name,
            function_name=function_name,
            expected_type="reasonable integer (1-10000)",
            actual_value=samples,
            suggestion="Consider using fewer antialiasing samples for better performance."
        )

    return samples