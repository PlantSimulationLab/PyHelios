"""
Exact closest-point queries between segments, points and triangles (``helios::collision``).

These are the geometric primitives the collision detection plug-in's capsule queries are built
on, exposed so that segment-triangle distances can be measured without building a BVH. They
work on plain coordinates and need no Context.

The functions are compiled into the PlantArchitecture part of the native library (the
plantarchitecture plug-in always links collision detection), so they require a build that
includes the ``plantarchitecture`` plug-in, as the default build does.

Example:
    >>> from pyhelios import collision
    >>> from pyhelios.types import vec3
    >>> d2, on_a, on_b = collision.closestPointsOnSegments(
    ...     vec3(0, 0, 0), vec3(1, 0, 0), vec3(0.5, 1, 0), vec3(0.5, 2, 0))
    >>> d2
    1.0
"""

from typing import Tuple

from .wrappers import UCollisionWrapper as _collision_wrapper
from .wrappers.DataTypes import vec3

__all__ = [
    "closestPointsOnSegments",
    "closestPointOnTriangle",
    "closestPointsSegmentTriangle",
]


def _check_vec3(name: str, value) -> None:
    if not isinstance(value, vec3):
        raise ValueError(f"{name} must be a vec3, got {type(value).__name__}")


def _xyz(v: vec3) -> tuple:
    return (v.x, v.y, v.z)


def closestPointsOnSegments(p1: vec3, q1: vec3, p2: vec3, q2: vec3) -> Tuple[float, vec3, vec3]:
    """Closest points between two segments, and the squared distance between them.

    Minimizes the distance between a point of segment ``p1``-``q1`` and a point of segment
    ``p2``-``q2``. A zero-length segment is treated as a point, so this also gives point-to-segment
    and point-to-point distances. For (nearly) parallel segments one of the equally close pairs
    is returned.

    Args:
        p1: Start of the first segment
        q1: End of the first segment
        p2: Start of the second segment
        q2: End of the second segment

    Returns:
        ``(squared_distance, closest1, closest2)``: the squared distance between the two points,
        the point of the first segment nearest the second, and the point of the second segment
        nearest the first.

    Raises:
        ValueError: If an argument is not a vec3
        NotImplementedError: If the native library predates helios-core v1.3.96 or was built
            without the plantarchitecture plug-in
    """
    for name, v in (("p1", p1), ("q1", q1), ("p2", p2), ("q2", q2)):
        _check_vec3(name, v)
    d2, c1, c2 = _collision_wrapper.closestPointsOnSegments(_xyz(p1), _xyz(q1), _xyz(p2), _xyz(q2))
    return d2, vec3(*c1), vec3(*c2)


def closestPointOnTriangle(p: vec3, a: vec3, b: vec3, c: vec3) -> vec3:
    """Closest point of a triangle to a point.

    Found from the Voronoi region of the triangle (vertex, edge or face) that the point projects
    into. A degenerate (zero-area) triangle is handled through its edges.

    Args:
        p: Query point
        a: First vertex of the triangle
        b: Second vertex of the triangle
        c: Third vertex of the triangle

    Returns:
        Point of the triangle nearest ``p``

    Raises:
        ValueError: If an argument is not a vec3
        NotImplementedError: If the native library predates helios-core v1.3.96 or was built
            without the plantarchitecture plug-in
    """
    for name, v in (("p", p), ("a", a), ("b", b), ("c", c)):
        _check_vec3(name, v)
    return vec3(*_collision_wrapper.closestPointOnTriangle(_xyz(p), _xyz(a), _xyz(b), _xyz(c)))


def closestPointsSegmentTriangle(p: vec3, q: vec3, a: vec3, b: vec3, c: vec3) -> Tuple[float, vec3, vec3]:
    """Closest points between a segment and a triangle, and the squared distance between them.

    If the segment crosses the triangle the distance is zero and both points are the crossing.
    Otherwise the closest pair joins a segment endpoint to the triangle, or the segment to one of
    the triangle's edges. The gap between a capsule of radius ``r`` about the segment and the
    triangle is ``sqrt(squared_distance) - r``.

    Args:
        p: Start of the segment
        q: End of the segment
        a: First vertex of the triangle
        b: Second vertex of the triangle
        c: Third vertex of the triangle

    Returns:
        ``(squared_distance, on_segment, on_triangle)``: the squared distance between the two
        points, the point of the segment nearest the triangle, and the point of the triangle
        nearest the segment.

    Raises:
        ValueError: If an argument is not a vec3
        NotImplementedError: If the native library predates helios-core v1.3.96 or was built
            without the plantarchitecture plug-in
    """
    for name, v in (("p", p), ("q", q), ("a", a), ("b", b), ("c", c)):
        _check_vec3(name, v)
    d2, s_pt, t_pt = _collision_wrapper.closestPointsSegmentTriangle(_xyz(p), _xyz(q), _xyz(a), _xyz(b), _xyz(c))
    return d2, vec3(*s_pt), vec3(*t_pt)
