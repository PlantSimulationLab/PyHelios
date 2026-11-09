"""
ctypes bindings for the helios::collision closest-point queries (collisiondetection
CollisionGeometry.h, helios-core v1.3.96+).

The C functions are compiled into the PlantArchitecture wrapper, because the plantarchitecture
plug-in always links collisiondetection, so they are present whenever PlantArchitecture is built.
"""

import ctypes
from typing import Tuple

from ..plugins import helios_lib
from ..exceptions import check_helios_error


def _check_error(result, func, args):
    check_helios_error(helios_lib.getLastErrorCode, helios_lib.getLastErrorMessage, helios_lib.clearError)
    return result


_Vec3 = ctypes.c_float * 3
_P = ctypes.POINTER(ctypes.c_float)

_COLLISION_GEOMETRY_AVAILABLE = False
try:
    helios_lib.collisionClosestPointsOnSegments.argtypes = [_P, _P, _P, _P, _P, _P]
    helios_lib.collisionClosestPointsOnSegments.restype = ctypes.c_float
    helios_lib.collisionClosestPointsOnSegments.errcheck = _check_error

    helios_lib.collisionClosestPointOnTriangle.argtypes = [_P, _P, _P, _P, _P]
    helios_lib.collisionClosestPointOnTriangle.restype = None
    helios_lib.collisionClosestPointOnTriangle.errcheck = _check_error

    helios_lib.collisionClosestPointsSegmentTriangle.argtypes = [_P, _P, _P, _P, _P, _P, _P]
    helios_lib.collisionClosestPointsSegmentTriangle.restype = ctypes.c_float
    helios_lib.collisionClosestPointsSegmentTriangle.errcheck = _check_error

    _COLLISION_GEOMETRY_AVAILABLE = True
except AttributeError:
    _COLLISION_GEOMETRY_AVAILABLE = False


def _require(name: str) -> None:
    if not _COLLISION_GEOMETRY_AVAILABLE:
        raise NotImplementedError(
            f"collision.{name} is not available in the loaded native library. It requires helios-core "
            "v1.3.96 or newer built with the plantarchitecture plug-in; rebuild with: "
            "build_scripts/build_helios --clean"
        )


def _v(t) -> ctypes.Array:
    return _Vec3(float(t[0]), float(t[1]), float(t[2]))


def closestPointsOnSegments(p1, q1, p2, q2) -> Tuple[float, tuple, tuple]:
    """Return (squared_distance, closest1_xyz, closest2_xyz). Points are (x, y, z) tuples."""
    _require("closestPointsOnSegments")
    c1, c2 = _Vec3(), _Vec3()
    d2 = helios_lib.collisionClosestPointsOnSegments(_v(p1), _v(q1), _v(p2), _v(q2), c1, c2)
    return float(d2), tuple(c1), tuple(c2)


def closestPointOnTriangle(p, a, b, c) -> tuple:
    """Return the (x, y, z) point of triangle a-b-c nearest p."""
    _require("closestPointOnTriangle")
    out = _Vec3()
    helios_lib.collisionClosestPointOnTriangle(_v(p), _v(a), _v(b), _v(c), out)
    return tuple(out)


def closestPointsSegmentTriangle(p, q, a, b, c) -> Tuple[float, tuple, tuple]:
    """Return (squared_distance, on_segment_xyz, on_triangle_xyz)."""
    _require("closestPointsSegmentTriangle")
    s_pt, t_pt = _Vec3(), _Vec3()
    d2 = helios_lib.collisionClosestPointsSegmentTriangle(_v(p), _v(q), _v(a), _v(b), _v(c), s_pt, t_pt)
    return float(d2), tuple(s_pt), tuple(t_pt)
