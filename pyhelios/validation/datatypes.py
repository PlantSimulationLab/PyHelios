"""
Validation for PyHelios DataTypes (vec2, vec3, vec4, colors, etc.)

Provides comprehensive validation for all geometric data types,
ensuring finite values and appropriate ranges before C++ operations.
"""

from typing import Any
from .core import is_finite_numeric
from .exceptions import ValidationError, create_validation_error


def validate_color_component(value: float, component_name: str, param_name: str, function_name: str = None):
    """Validate a color component is in valid range [0,1]."""
    if not is_finite_numeric(value):
        raise create_validation_error(
            f"Color component {component_name} must be a finite number, got {value} ({type(value).__name__})",
            param_name=f"{param_name}.{component_name}",
            function_name=function_name,
            expected_type="finite number in range [0,1]",
            actual_value=value,
            suggestion="Color components must be normalized values between 0 and 1."
        )
    
    if not (0.0 <= value <= 1.0):
        raise create_validation_error(
            f"Color component {component_name}={value} is outside valid range [0,1]",
            param_name=f"{param_name}.{component_name}",
            function_name=function_name,
            expected_type="number in range [0,1]",
            actual_value=value,
            suggestion="Color components must be normalized values between 0 and 1."
        )


def validate_rgb_color(color: Any, param_name: str = "color", function_name: str = None):
    """
    Validate RGBcolor has finite values in [0,1] range.
    
    Args:
        color: RGBcolor object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
        
    Raises:
        ValidationError: If color is invalid or components out of range
    """
    if color is None:
        return
    
    # Check if it has the expected attributes
    if not hasattr(color, 'r') or not hasattr(color, 'g') or not hasattr(color, 'b'):
        raise create_validation_error(
            f"Parameter must be an RGBcolor object with .r, .g, .b attributes",
            param_name=param_name,
            function_name=function_name,
            expected_type="RGBcolor",
            actual_value=color,
            suggestion="Use RGBcolor(r, g, b) where r, g, b are values between 0 and 1."
        )
    
    validate_color_component(color.r, 'r', param_name, function_name)
    validate_color_component(color.g, 'g', param_name, function_name)
    validate_color_component(color.b, 'b', param_name, function_name)


def validate_rgba_color(color: Any, param_name: str = "color", function_name: str = None):
    """
    Validate RGBAcolor has finite values in [0,1] range.
    
    Args:
        color: RGBAcolor object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
        
    Raises:
        ValidationError: If color is invalid or components out of range
    """
    if color is None:
        return
        
    # Check if it has the expected attributes
    if not hasattr(color, 'r') or not hasattr(color, 'g') or not hasattr(color, 'b') or not hasattr(color, 'a'):
        raise create_validation_error(
            f"Parameter must be an RGBAcolor object with .r, .g, .b, .a attributes",
            param_name=param_name,
            function_name=function_name,
            expected_type="RGBAcolor",
            actual_value=color,
            suggestion="Use RGBAcolor(r, g, b, a) where all values are between 0 and 1."
        )
    
    validate_color_component(color.r, 'r', param_name, function_name)
    validate_color_component(color.g, 'g', param_name, function_name)
    validate_color_component(color.b, 'b', param_name, function_name)
    validate_color_component(color.a, 'a', param_name, function_name)


def validate_vector_finite(vector: Any, param_name: str = "vector", expected_dims: int = 3, function_name: str = None):
    """
    Validate vector has finite components.
    
    Args:
        vector: Vector object to validate (vec2, vec3, vec4, etc.)
        param_name: Parameter name for error messages
        expected_dims: Expected number of dimensions
        function_name: Function name for error messages
        
    Raises:
        ValidationError: If vector is invalid or has non-finite components
    """
    if vector is None:
        return
    
    # Get the expected attribute names based on dimensions
    attrs = ['x', 'y', 'z', 'w'][:expected_dims]
    
    # Check if it has the expected attributes
    for attr in attrs:
        if not hasattr(vector, attr):
            raise create_validation_error(
                f"Parameter must be a vector with {'.'.join(attrs)} attributes",
                param_name=param_name,
                function_name=function_name,
                expected_type=f"vec{expected_dims}",
                actual_value=vector,
                suggestion=f"Use vec{expected_dims}() constructor or provide object with {'.'.join(attrs)} attributes."
            )
        
        value = getattr(vector, attr)
        if not is_finite_numeric(value):
            raise create_validation_error(
                f"Vector component {attr} must be a finite number, got {value} ({type(value).__name__})",
                param_name=f"{param_name}.{attr}",
                function_name=function_name,
                expected_type="finite number",
                actual_value=value,
                suggestion="Ensure all vector components are finite numbers (not NaN or infinity)."
            )


def validate_vec2(vector: Any, param_name: str = "vector", function_name: str = None):
    """
    Validate vec2 has finite x,y components.

    Args:
        vector: vec2 object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages

    Returns:
        The validated vec2 object
    """
    validate_vector_finite(vector, param_name, expected_dims=2, function_name=function_name)
    return vector


def validate_vec3(vector: Any, param_name: str = "vector", function_name: str = None):
    """
    Validate vec3 has finite x,y,z components.

    Args:
        vector: vec3 object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages

    Returns:
        The validated vec3 object
    """
    validate_vector_finite(vector, param_name, expected_dims=3, function_name=function_name)
    return vector


def validate_vec4(vector: Any, param_name: str = "vector", function_name: str = None):
    """
    Validate vec4 has finite x,y,z,w components.
    
    Args:
        vector: vec4 object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
    """
    validate_vector_finite(vector, param_name, expected_dims=4, function_name=function_name)


def validate_spherical_coord(coord: Any, param_name: str = "coordinate", function_name: str = None):
    """
    Validate SphericalCoord has valid values.
    
    Args:
        coord: SphericalCoord object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
        
    Raises:
        ValidationError: If coordinate has invalid values
    """
    if coord is None:
        return
    
    if not hasattr(coord, 'radius') or not hasattr(coord, 'elevation') or not hasattr(coord, 'azimuth'):
        raise create_validation_error(
            f"Parameter must be a SphericalCoord with .radius, .elevation, .azimuth attributes",
            param_name=param_name,
            function_name=function_name,
            expected_type="SphericalCoord",
            actual_value=coord,
            suggestion="Use SphericalCoord(radius, elevation, azimuth) constructor."
        )
    
    # Validate radius is positive
    if not is_finite_numeric(coord.radius) or coord.radius <= 0:
        raise create_validation_error(
            f"SphericalCoord radius must be a positive finite number, got {coord.radius}",
            param_name=f"{param_name}.radius",
            function_name=function_name,
            expected_type="positive finite number",
            actual_value=coord.radius,
            suggestion="Radius must be greater than 0."
        )
    
    # Elevation and azimuth can be any finite values (angles wrap around)
    if not is_finite_numeric(coord.elevation):
        raise create_validation_error(
            f"SphericalCoord elevation must be a finite number, got {coord.elevation} ({type(coord.elevation).__name__})",
            param_name=f"{param_name}.elevation",
            function_name=function_name,
            expected_type="finite number",
            actual_value=coord.elevation,
            suggestion="Elevation angle must be a finite number (not NaN or infinity)."
        )
    
    if not is_finite_numeric(coord.azimuth):
        raise create_validation_error(
            f"SphericalCoord azimuth must be a finite number, got {coord.azimuth} ({type(coord.azimuth).__name__})",
            param_name=f"{param_name}.azimuth",
            function_name=function_name,
            expected_type="finite number",
            actual_value=coord.azimuth,
            suggestion="Azimuth angle must be a finite number (not NaN or infinity)."
        )


def validate_integer_vector(vector: Any, param_name: str = "vector", expected_dims: int = 3, function_name: str = None):
    """
    Validate integer vector (int2, int3, int4) has valid integer components.
    
    Args:
        vector: Integer vector object to validate
        param_name: Parameter name for error messages
        expected_dims: Expected number of dimensions
        function_name: Function name for error messages
        
    Raises:
        ValidationError: If vector has invalid or non-integer components
    """
    if vector is None:
        return
    
    # Get the expected attribute names based on dimensions
    attrs = ['x', 'y', 'z', 'w'][:expected_dims]
    
    # Check if it has the expected attributes
    for attr in attrs:
        if not hasattr(vector, attr):
            raise create_validation_error(
                f"Parameter must be an integer vector with {'.'.join(attrs)} attributes",
                param_name=param_name,
                function_name=function_name,
                expected_type=f"int{expected_dims}",
                actual_value=vector,
                suggestion=f"Use int{expected_dims}() constructor or provide object with {'.'.join(attrs)} attributes."
            )
        
        value = getattr(vector, attr)
        if not isinstance(value, int):
            raise create_validation_error(
                f"Integer vector component {attr} must be an integer, got {value} ({type(value).__name__})",
                param_name=f"{param_name}.{attr}",
                function_name=function_name,
                expected_type="integer",
                actual_value=value,
                suggestion="Ensure all vector components are integers."
            )


def validate_int2(vector: Any, param_name: str = "vector", function_name: str = None):
    """
    Validate int2 has valid integer x,y components.

    Args:
        vector: int2 object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages

    Returns:
        The validated vector
    """
    validate_integer_vector(vector, param_name, expected_dims=2, function_name=function_name)
    return vector


def validate_int3(vector: Any, param_name: str = "vector", function_name: str = None):
    """
    Validate int3 has valid integer x,y,z components.

    Args:
        vector: int3 object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
    """
    validate_integer_vector(vector, param_name, expected_dims=3, function_name=function_name)


def validate_int4(vector: Any, param_name: str = "vector", function_name: str = None):
    """
    Validate int4 has valid integer x,y,z,w components.

    Args:
        vector: int4 object to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
    """
    validate_integer_vector(vector, param_name, expected_dims=4, function_name=function_name)