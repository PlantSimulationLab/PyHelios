"""
T2.5 -- fruit achievability classes (design doc §7.1):

    observable: AVUB_i > 0
    sizeable:   AVUB_i > gamma_size
    graspable:  approach cone clear

## gamma_size -- PLACEHOLDER threshold

The design doc defines gamma_size as "the visible fraction empirically
needed for sizing within tolerance, calibrated from Tier 1" -- Tier 1
(the actual sizing-accuracy-vs-visible-fraction calibration sweep) does not
exist yet in this repo. GAMMA_SIZE below is a documented placeholder, not a
calibrated value: 0.30 (30% of surface area visible) is a common rule of
thumb for fitting a stable circle/ellipse diameter estimate to a partially
occluded round object without the fit being dominated by the occluding
boundary rather than the object's own silhouette. Replace with a real
calibrated value once a Tier-1-equivalent sweep exists.

## graspable -- approach-cone approximation

The design doc allows approximating this "with a simple geometric
cone-vs-neighboring-primitive check if a real approach-planner doesn't exist
yet" (task brief) -- it doesn't, so that's what this module does, using only
real fruit centroids from fruit_ground_truth.json-equivalent records (no
synthetic geometry):

  1. A fruit's "approach direction" is approximated as the direction from
     the fruit's own centroid toward the eye position of whichever pose in
     V_reach gave it the single highest per-pose vis_i(v) (i.e. its
     clearest, most head-on real view) -- this is itself real data produced
     by the T2.1/T2.3 sweep, not invented.
  2. A cone is built at the fruit's centroid, axis = that approach
     direction, half-angle APPROACH_CONE_HALFANGLE_DEG, length
     APPROACH_CONE_LENGTH_M (a plausible gripper reach depth).
  3. The approach is "clear" if no OTHER fruit's centroid falls inside that
     cone.

This is explicitly an approximation, not a real approach planner: it checks
fruit-vs-fruit interference only (not leaves, branches, trellis wire, or the
arm/gripper's own geometry), and it collapses the whole fruit to its
centroid rather than using its true surface. Leaves are assumed graspable-
through (a real gripper can push foliage aside; it cannot push another
apple aside), which is why only fruit-fruit interference is checked.
"""

import math

GAMMA_SIZE = 0.30  # PLACEHOLDER -- see module docstring
APPROACH_CONE_HALFANGLE_DEG = 15.0
APPROACH_CONE_LENGTH_M = 0.15


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _norm(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def approach_cone_clear(fruit_centroid, approach_axis, other_centroids,
                         half_angle_deg=APPROACH_CONE_HALFANGLE_DEG,
                         length_m=APPROACH_CONE_LENGTH_M):
    """True if no centroid in `other_centroids` falls inside the cone at
    `fruit_centroid`, axis `approach_axis` (need not be normalized, but must
    be nonzero), half-angle `half_angle_deg`, length `length_m`.
    """
    axis_len = _norm(approach_axis)
    if axis_len == 0:
        return True  # no defined approach direction -- nothing to check against
    axis = tuple(c / axis_len for c in approach_axis)
    cos_half_angle = math.cos(math.radians(half_angle_deg))

    for other in other_centroids:
        v = _sub(other, fruit_centroid)
        dist = _norm(v)
        if dist == 0 or dist > length_m:
            continue
        cos_angle = _dot(v, axis) / dist
        if cos_angle >= cos_half_angle:
            return False
    return True


def classify_fruit(fruit_records, avub, best_pose_eye_by_fruit, gamma_size=GAMMA_SIZE):
    """Returns {object_id: {"AVUB_i", "observable", "sizeable", "graspable"}}.

    `best_pose_eye_by_fruit`: {object_id: (ex, ey, ez) or None} -- the eye
    position of the reachable-set pose that gave this fruit its highest
    single-pose vis_i(v) (None if never visible from any reachable pose).
    """
    centroids = {rec["object_id"]: tuple(rec["centroid"]) for rec in fruit_records}
    classes = {}
    for rec in fruit_records:
        oid = rec["object_id"]
        a = avub.get(oid, 0.0)
        observable = a > 0.0
        sizeable = a > gamma_size
        graspable = False
        if observable:
            eye = best_pose_eye_by_fruit.get(oid)
            if eye is not None:
                centroid = centroids[oid]
                axis = _sub(eye, centroid)
                others = [c for other_oid, c in centroids.items() if other_oid != oid]
                graspable = approach_cone_clear(centroid, axis, others)
        classes[oid] = {
            "AVUB_i": a,
            "observable": observable,
            "sizeable": sizeable,
            "graspable": graspable,
        }
    return classes


def summarize_classes(classes):
    n = len(classes)
    n_observable = sum(1 for c in classes.values() if c["observable"])
    n_sizeable = sum(1 for c in classes.values() if c["sizeable"])
    n_graspable = sum(1 for c in classes.values() if c["graspable"])
    return {
        "n_fruit_total": n,
        "n_observable": n_observable,
        "n_sizeable": n_sizeable,
        "n_graspable": n_graspable,
        "fraction_observable_of_total": n_observable / n if n else 0.0,
        # Per design doc: recall must be reported against the OBSERVABLE
        # denominator, not the total -- so also report sizeable/graspable
        # as a fraction of observable fruit, not of all fruit.
        "fraction_sizeable_of_observable": n_sizeable / n_observable if n_observable else 0.0,
        "fraction_graspable_of_observable": n_graspable / n_observable if n_observable else 0.0,
    }
