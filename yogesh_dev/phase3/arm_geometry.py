"""
T3.5 -- Arm/workcell collision geometry.

Two independent things happen here:

1. STRUCTURAL non-collision guarantee (does NOT need T0.6). Each arm's
   vertical (z) travel band from `kinematics.default_arm_configs()` is
   disjoint from every other arm's band, so no matter what x/y/pan/tilt each
   arm executes, their z-coordinates can never coincide -- arm-arm collision
   is impossible by construction. `verify_non_overlapping_bands()` checks
   this directly via interval-overlap arithmetic (NOT `findCollisions` --
   that binding doesn't exist yet, see T0.6). This is the check the task
   doc asks for explicitly.

2. Arm link geometry as actual Helios Context primitives
   (`add_arm_link_geometry`), so the arms are visualizable/queryable objects
   in the same Context the canopy lives in, plus an independent cross-check
   (`verify_geometry_bands_via_context`) that re-derives the same
   non-overlap conclusion from `Context.getDomainBoundingBox` on the added
   geometry -- i.e. two different code paths (pure Python interval math, and
   the Helios API) agree.

WHAT THIS DOES NOT DO: arm-vs-canopy collision checking. That needs ray
casts or BVH queries against the real leaf/branch/fruit primitives
(`CollisionDetection.findCollisions` / `castRaysSoA`), which is not exposed
in PyHelios (`pyhelios/config/plugin_metadata.py`: "CollisionDetection
dependency handled at C++ level, not exposed in Python API") -- blocked on
T0.6. The boxes added here are geometric placeholders for the arm's physical
envelope; they are not (yet) tested against the tree at all.
"""

from typing import Dict, List, Tuple

from .kinematics import ArmConfig


def z_bands_overlap(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    """Standard half-open interval overlap test: two closed intervals
    [a0,a1], [b0,b1] overlap iff a0 < b1 and b0 < a1."""
    return a[0] < b[1] and b[0] < a[1]


def verify_non_overlapping_bands(arm_configs: List[ArmConfig]) -> Tuple[bool, List[Tuple[str, str]]]:
    """Direct interval-overlap check (pure Python, no Helios/findCollisions)
    across every pair of arms' z-bands. Returns (all_disjoint, conflicts)."""
    conflicts = []
    for i in range(len(arm_configs)):
        for j in range(i + 1, len(arm_configs)):
            a, b = arm_configs[i], arm_configs[j]
            if z_bands_overlap(a.limits.z, b.limits.z):
                conflicts.append((a.name, b.name))
    return (len(conflicts) == 0, conflicts)


def add_arm_link_geometry(context, arm_configs: List[ArmConfig],
                           mast_x_positions: List[float],
                           mast_size_xy: float = 0.15) -> Dict[str, List[int]]:
    """Add one vertical box ("mast") per arm to the Context, spanning exactly
    its z-band, at a representative home (x, y) position just behind the
    arm's own y-travel envelope. Returns {arm_name: [primitive_uuids]}.

    This is a coarse placeholder for the arm's real link shape (column +
    carriage + camera housing) -- good enough to reason about vertical
    clearance and to exercise `getDomainBoundingBox`, not a CAD-accurate
    model. `mast_size_xy` is an assumed 15 cm square cross-section
    (placeholder, no hardware spec).
    """
    from pyhelios.types import vec3, int3

    uuids_by_arm: Dict[str, List[int]] = {}
    for arm, x_home in zip(arm_configs, mast_x_positions):
        z_lo, z_hi = arm.limits.z
        height = z_hi - z_lo
        y_home = arm.limits.y[0] - 0.15  # sits just behind the arm's own reach envelope
        center = vec3(x_home, y_home, z_lo + height / 2.0)
        size = vec3(mast_size_xy, mast_size_xy, height)
        uuids = context.addBox(center=center, size=size, subdiv=int3(1, 1, 1))
        uuids_by_arm[arm.name] = uuids
    return uuids_by_arm


def verify_geometry_bands_via_context(context, uuids_by_arm: Dict[str, List[int]]) -> Tuple[bool, Dict[str, Tuple[float, float]]]:
    """Independent cross-check of the same non-overlap property, this time
    read back through `Context.getDomainBoundingBox` on the geometry actually
    added to the Context (rather than the JointLimits dataclass values).
    Two different code paths agreeing is stronger evidence than either one
    alone."""
    zranges: Dict[str, Tuple[float, float]] = {}
    for name, uuids in uuids_by_arm.items():
        _xb, _yb, zb = context.getDomainBoundingBox(uuids)
        zranges[name] = (zb.x, zb.y)

    names = list(zranges)
    ok = True
    conflicts = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if z_bands_overlap(zranges[names[i]], zranges[names[j]]):
                ok = False
                conflicts.append((names[i], names[j]))
    return ok, zranges
