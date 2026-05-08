"""
PyHelios data types and structures.

This module provides access to all data structures and parameter
classes used by PyHelios, including geometric types and plugin-specific
parameter structures.
"""

# Import all standard data types from wrappers.DataTypes
from ..wrappers.DataTypes import *

# Import photosynthesis-specific types
from .photosynthesis import (
    PhotosyntheticTemperatureResponseParameters,
    EmpiricalModelCoefficients, 
    FarquharModelCoefficients,
    PHOTOSYNTHESIS_SPECIES,
    SPECIES_ALIASES,
    validate_species_name,
    get_available_species,
    get_species_aliases
)

__all__ = [
    # Standard geometric types (imported from DataTypes)
    'vec2', 'vec3', 'vec4', 'int2', 'int3', 'int4',
    'RGBcolor', 'RGBAcolor', 'SphericalCoord', 'Time', 'Date', 'PrimitiveType',
    'Location',
    'make_vec2', 'make_vec3', 'make_vec4', 'make_int2', 'make_int3', 'make_int4',
    'make_RGBcolor', 'make_RGBAcolor', 'make_SphericalCoord',
    'make_Location',

    # Photosynthesis-specific types
    'PhotosyntheticTemperatureResponseParameters',
    'EmpiricalModelCoefficients',
    'FarquharModelCoefficients',
    'PHOTOSYNTHESIS_SPECIES',
    'SPECIES_ALIASES',
    'validate_species_name',
    'get_available_species',
    'get_species_aliases'
]