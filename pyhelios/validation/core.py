"""
Core validation utilities for PyHelios.

Provides decorators, type coercion, and standardized error handling
following PyHelios's fail-fast philosophy.
"""

import functools
import math
from typing import Any, Callable, Dict, Union

from .exceptions import ValidationError, create_validation_error


def validate_input(param_validators: Dict[str, Callable] = None, 
                  type_coercions: Dict[str, Callable] = None):
    """
    Decorator for comprehensive parameter validation.
    
    Performs type coercion first, then validation, following the pattern:
    1. Coerce types where safe (e.g., list to vec3)
    2. Validate all parameters meet requirements
    3. Call original function if validation passes
    
    Args:
        param_validators: Dict mapping parameter names to validation functions
        type_coercions: Dict mapping parameter names to coercion functions
    
    Example:
        >>> # Using the validate_input decorator:
        >>> # validate_input(
        >>> #     param_validators={'center': validate_vec3, 'radius': validate_positive_value},
        >>> #     type_coercions={'center': coerce_to_vec3}
        >>> # )
        >>> # def addSphere(self, center, radius, **kwargs):
        >>> #     # center is guaranteed to be vec3, radius is positive
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Perform type coercion first
            if type_coercions:
                for param, coercion_func in type_coercions.items():
                    if param in kwargs:
                        try:
                            kwargs[param] = coercion_func(kwargs[param], param_name=param)
                        except ValidationError:
                            raise  # Re-raise validation errors from coercion
                        except Exception as e:
                            raise create_validation_error(
                                f"Failed to coerce parameter to expected type: {str(e)}",
                                param_name=param,
                                function_name=func.__name__
                            )
            
            # Then validate parameters
            if param_validators:
                for param, validator in param_validators.items():
                    if param in kwargs:
                        try:
                            validator(kwargs[param], param_name=param, function_name=func.__name__)
                        except ValidationError:
                            raise  # Re-raise validation errors
                        except Exception as e:
                            raise create_validation_error(
                                f"Parameter validation failed: {str(e)}",
                                param_name=param,
                                function_name=func.__name__
                            )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_finite_numeric(value: Any) -> bool:
    """Check if value is a finite number (not NaN or inf)."""
    try:
        float_value = float(value)
        return math.isfinite(float_value)
    except (ValueError, TypeError, OverflowError):
        return False


def validate_positive_value(value: Any, param_name: str = "value", function_name: str = None):
    """
    Validate value is positive and finite.
    
    Args:
        value: Value to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
        
    Raises:
        ValidationError: If value is not positive or not finite
    """
    if not is_finite_numeric(value):
        raise create_validation_error(
            f"Parameter must be a finite number, got {value} ({type(value).__name__})",
            param_name=param_name,
            function_name=function_name,
            expected_type="positive finite number",
            actual_value=value
        )
    
    if value <= 0:
        raise create_validation_error(
            f"Parameter must be positive, got {value}",
            param_name=param_name,
            function_name=function_name,
            expected_type="positive number",
            actual_value=value,
            suggestion="Use a value greater than 0."
        )


def validate_non_negative_value(value: Any, param_name: str = "value", function_name: str = None):
    """
    Validate value is non-negative and finite.
    
    Args:
        value: Value to validate
        param_name: Parameter name for error messages
        function_name: Function name for error messages
        
    Raises:
        ValidationError: If value is negative or not finite
    """
    if not is_finite_numeric(value):
        raise create_validation_error(
            f"Parameter must be a finite number, got {value} ({type(value).__name__})",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-negative finite number",
            actual_value=value
        )
    
    if value < 0:
        raise create_validation_error(
            f"Parameter must be non-negative, got {value}",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-negative number",
            actual_value=value,
            suggestion="Use a value >= 0."
        )


def coerce_to_vec3(value: Any, param_name: str = "parameter") -> 'vec3':
    """
    Safely coerce list/tuple to vec3 with validation.
    
    Args:
        value: Value to coerce (vec3, list, or tuple)
        param_name: Parameter name for error messages
        
    Returns:
        vec3 object
        
    Raises:
        ValidationError: If coercion fails or values are invalid
    """
    from ..wrappers.DataTypes import vec3
    
    # Check if it's already a vec3 (using duck typing to avoid import issues)
    if hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z') and hasattr(value, 'to_list'):
        return value
    
    if isinstance(value, (list, tuple)):
        if len(value) != 3:
            raise create_validation_error(
                f"Parameter must have exactly 3 elements for vec3 conversion, got {len(value)} elements: {value}",
                param_name=param_name,
                expected_type="3-element list or tuple",
                actual_value=value,
                suggestion="Provide exactly 3 numeric values like [x, y, z] or (x, y, z)."
            )
        
        # Validate each component is finite
        for i, component in enumerate(value):
            if not is_finite_numeric(component):
                raise create_validation_error(
                    f"Parameter element [{i}] must be a finite number, got {component} ({type(component).__name__})",
                    param_name=f"{param_name}[{i}]",
                    expected_type="finite number",
                    actual_value=component,
                    suggestion="Ensure all coordinate values are finite numbers (not NaN or infinity)."
                )
        
        return vec3(float(value[0]), float(value[1]), float(value[2]))
    
    raise create_validation_error(
        f"Parameter must be a vec3, list, or tuple, got {type(value).__name__}",
        param_name=param_name,
        expected_type="vec3, list, or tuple",
        actual_value=value,
        suggestion="Use vec3(x, y, z), [x, y, z], or (x, y, z) format."
    )


def coerce_to_vec2(value: Any, param_name: str = "parameter") -> 'vec2':
    """
    Safely coerce list/tuple to vec2 with validation.
    
    Args:
        value: Value to coerce (vec2, list, or tuple)
        param_name: Parameter name for error messages
        
    Returns:
        vec2 object
        
    Raises:
        ValidationError: If coercion fails or values are invalid
    """
    from ..wrappers.DataTypes import vec2
    
    # Check if it's already a vec2 (using duck typing to avoid import issues)  
    if hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'to_list') and not hasattr(value, 'z'):
        return value
    
    if isinstance(value, (list, tuple)):
        if len(value) != 2:
            raise create_validation_error(
                f"Parameter must have exactly 2 elements for vec2 conversion, got {len(value)} elements: {value}",
                param_name=param_name,
                expected_type="2-element list or tuple",
                actual_value=value,
                suggestion="Provide exactly 2 numeric values like [x, y] or (x, y)."
            )
        
        # Validate each component is finite
        for i, component in enumerate(value):
            if not is_finite_numeric(component):
                raise create_validation_error(
                    f"Parameter element [{i}] must be a finite number, got {component} ({type(component).__name__})",
                    param_name=f"{param_name}[{i}]",
                    expected_type="finite number",
                    actual_value=component,
                    suggestion="Ensure all coordinate values are finite numbers (not NaN or infinity)."
                )
        
        return vec2(float(value[0]), float(value[1]))
    
    raise create_validation_error(
        f"Parameter must be a vec2, list, or tuple, got {type(value).__name__}",
        param_name=param_name,
        expected_type="vec2, list, or tuple",
        actual_value=value,
        suggestion="Use vec2(x, y), [x, y], or (x, y) format."
    )