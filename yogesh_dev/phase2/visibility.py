"""
T2.1 -- per-fruit visible-fraction vis_i(v) for a given camera pose, and
T2.2 -- accumulated (union) visibility over a pose sequence.

## Why this isn't `CollisionDetection`-based, and why it's still real ray-traced
   occlusion (not the coarser object-level fallback originally scoped)

`CollisionDetection` (`castRaysSoA`, `findCollisions`, ...) is not exposed in
PyHelios, so T0.6-style arbitrary-origin ray casting from fruit-surface
primitives out to a camera is not available. The task brief for this phase
anticipated falling back to `RadiationModel.getObjectDataLabelMap(cam,
"fruitID")` (object-level: "this pixel belongs to fruit object N") and
weighting by *aggregate* fruit surface area -- explicitly coarser than the
design doc's `vis_i(v)` formula (§7.1 of active_vision_design.md), which is
defined per surface *primitive* s_ij, not per whole fruit.

It turns out we don't have to settle for the coarser version. Every camera
pose PyHelios already renders resolves, for each pixel, which single
primitive is nearest along that ray -- that's how rendering works, and it is
exactly the `unoccluded(s_ij, p_v) AND frustum(s_ij, v)` test the formula
asks for, computed by Helios's own OptiX ray tracer during `runBand()`.
`RadiationModel.getPrimitiveDataLabelMap(camera, label)` exposes exactly this
per-pixel nearest-primitive result for ANY int/uint/float primitive-data
field (see its docstring: "writes the value of `primitive_data_label` on the
primitive SEEN at that pixel" -- singular, nearest-hit). `getObjectDataLabelMap`
(used for `fruitID` in Phase 1) is the same mechanism, just reading an
object-level field instead of a primitive-level one.

So: assign every fruit-surface primitive its own globally unique small
integer id in a new primitive-data field (`vis_primitive_id`, see
`assign_vis_primitive_ids`), then read that field back with
`getPrimitiveDataLabelMap` after each render. Any primitive whose id appears
in >=1 pixel was the ray-traced nearest hit somewhere in frame -- i.e.
genuinely unoccluded and in-frustum, at full per-primitive resolution, not
aggregated to the whole fruit. This is real data produced by Helios's actual
renderer (the same renderer Phase 1 already used for `fruitID`/`object_label`
label maps), not fabricated or approximated ray casting.

One more piece of the formula comes for free: `front-facing`
(n_ij . (p_v - s_ij) > 0). Apple fruit primitives in the plant-architecture
model tile a closed, outward-facing surface (a near-spherical shell). A
camera ray can only ever have its *nearest* hit on the near (outward-facing)
side of that shell -- a back-facing primitive on the far side of the fruit
is, by construction, never the nearest hit along any ray that also crosses
the near side first. So nearest-hit selection also enforces front-facing
for this geometry, with no separate normal-dot-product check needed.

What this approach still does NOT resolve, honestly: sub-pixel partial
occlusion at a single pixel's footprint (a primitive that is 90% covered by
a leaf but whose remaining 10% still lands the nearest hit on some ray still
counts as fully "visible", same limitation any single-sample rasterizer has),
and antialiasing_samples=1 in the dense sweep (see `run_phase2.py`) means each
pixel has one ray sample rather than several. Report this as the caveat it is.

w(theta, r) (the optional observation-quality weight in the formula) is left
at w=1 throughout (pure geometric visibility is the primary metric per the
design doc; the weighted variant is not computed here -- out of scope for
this phase).
"""

import numpy as np

VIS_PRIMITIVE_ID_FIELD = "vis_primitive_id"
NO_FRUIT_PRIMITIVE_ID = -1


def assign_vis_primitive_ids(context, all_uuids, fruit_records):
    """Set VIS_PRIMITIVE_ID_FIELD (int) on every primitive in the scene:
    -1 for anything that isn't a fruit-surface primitive, and a globally
    unique id 0..N-1 (across ALL fruit objects/trees) for every primitive
    listed in a fruit_ground_truth record's `primitive_uuids`.

    Must be called once, after the scene is built, before any pose is
    rendered (matches the T1.3 `semantic_class_id` pattern in
    yogesh_dev/phase1/label_maps.py -- plain Context primitive data, no
    updateGeometry/runBand dependency).

    Returns:
        prim_id_to_info: {vis_primitive_id: {"uuid": int, "object_id": int, "area": float}}
        fruit_prim_ids: {object_id: [vis_primitive_id, ...]}
    """
    context.setPrimitiveDataInt(list(all_uuids), VIS_PRIMITIVE_ID_FIELD, NO_FRUIT_PRIMITIVE_ID)

    prim_id_to_info = {}
    fruit_prim_ids = {}
    next_id = 0
    for rec in fruit_records:
        oid = rec["object_id"]
        ids_here = []
        for u in rec["primitive_uuids"]:
            area = context.getPrimitiveArea(u)
            context.setPrimitiveDataInt(u, VIS_PRIMITIVE_ID_FIELD, next_id)
            prim_id_to_info[next_id] = {"uuid": int(u), "object_id": oid, "area": float(area)}
            ids_here.append(next_id)
            next_id += 1
        fruit_prim_ids[oid] = ids_here
    return prim_id_to_info, fruit_prim_ids


def visible_primitive_ids_for_pose(radiation, camera_label):
    """Read back which fruit primitives were the nearest ray-traced hit at
    >=1 pixel for the CURRENT render state of `camera_label` (caller must
    have already called setCameraPosition/setCameraLookat + runBand for the
    pose being queried).

    Returns (visible_ids: set[int], pixel_counts: {vis_primitive_id: int}).
    """
    label_map = radiation.getPrimitiveDataLabelMap(camera_label, VIS_PRIMITIVE_ID_FIELD)
    valid = ~np.isnan(label_map)
    if not np.any(valid):
        return set(), {}
    ids, counts = np.unique(np.round(label_map[valid]).astype(np.int64), return_counts=True)
    pixel_counts = {int(i): int(c) for i, c in zip(ids, counts) if int(i) != NO_FRUIT_PRIMITIVE_ID}
    return set(pixel_counts.keys()), pixel_counts


def fruit_visible_fraction(visible_ids, fruit_prim_ids, prim_id_to_info, object_id, surface_area_m2):
    """vis_i(v) (or the union-accumulated version, if `visible_ids` is
    already a union over several poses) -- area-weighted fraction of fruit
    `object_id`'s surface area covered by primitives present in `visible_ids`.
    """
    ids_here = fruit_prim_ids.get(object_id, [])
    if not ids_here or surface_area_m2 <= 0:
        return 0.0, 0.0
    area_visible = sum(prim_id_to_info[pid]["area"] for pid in ids_here if pid in visible_ids)
    return area_visible / surface_area_m2, area_visible


def render_poses_batched(radiation, camera_labels, poses, bands):
    """Render a list of (eye, lookat) poses in batches of len(camera_labels),
    reusing the already-registered camera slots (never re-adding cameras --
    matches the T0.4 pattern in yogesh_dev/phase0/radiation_cameras.py).
    `radiation.updateGeometry()` must already have been called once by the
    caller; geometry never changes here, only camera pose. The final
    (possibly short) batch reuses only as many camera slots as it has poses.

    Returns a list (same order as `poses`) of (visible_ids, pixel_counts).
    """
    results = []
    batch_size = len(camera_labels)
    for start in range(0, len(poses), batch_size):
        batch = poses[start:start + batch_size]
        cams_used = camera_labels[:len(batch)]
        for cam, (eye, lookat) in zip(cams_used, batch):
            radiation.setCameraPosition(cam, eye)
            radiation.setCameraLookat(cam, lookat)
        radiation.runBand(list(bands))
        for cam in cams_used:
            results.append(visible_primitive_ids_for_pose(radiation, cam))
    return results


def union_visible_ids(sequence_of_visible_id_sets):
    """T2.2: v_i_max(t) as a UNION over primitives seen by ANY pose up to
    and including step t -- explicitly not a max over individual per-view
    fractions (a fruit seen 40% left + 40% right is ~80% covered, not 40%).

    Returns a list `cumulative` where `cumulative[t]` is the union set of
    visible primitive ids after poses[0..t] (inclusive).
    """
    union = set()
    cumulative = []
    for s in sequence_of_visible_id_sets:
        union = union | s
        cumulative.append(set(union))
    return cumulative
