"""
Convenient imports for all PyHelios vector types and factory functions.

This module provides all vector types, color types, and factory functions
for easy star import usage as documented in CLAUDE.md:

    from pyhelios.types import *  # All vector types: vec3, RGBcolor, etc.
"""

from .wrappers.DataTypes import (
    # Vector types
    vec2, vec3, vec4,
    int2, int3, int4,

    # Color types
    RGBcolor, RGBAcolor,

    # Coordinate types
    SphericalCoord,
    AxisRotation,

    # Time and Date types
    Time, Date,

    # Primitive type enumeration
    PrimitiveType,

    # Factory functions
    make_int2, make_int3, make_int4,
    make_vec2, make_vec3, make_vec4,
    make_RGBcolor, make_RGBAcolor,
    make_SphericalCoord,
    make_AxisRotation,
    make_Time, make_Date
)

# Export all for star imports
__all__ = [
    # Vector types
    'vec2', 'vec3', 'vec4',
    'int2', 'int3', 'int4',

    # Color types
    'RGBcolor', 'RGBAcolor',

    # Coordinate types
    'SphericalCoord',
    'AxisRotation',

    # Time and Date types
    'Time', 'Date',

    # Primitive type enumeration
    'PrimitiveType',

    # Factory functions
    'make_int2', 'make_int3', 'make_int4',
    'make_vec2', 'make_vec3', 'make_vec4',
    'make_RGBcolor', 'make_RGBAcolor',
    'make_SphericalCoord',
    'make_AxisRotation',
    'make_Time', 'make_Date'
]