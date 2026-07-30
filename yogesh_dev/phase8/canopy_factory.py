"""
T8.1 -- seeded canopy generation with disjoint dev/test seed sets, and the real
factor knobs (LAI, fruit density, clustering, trellis type) T8.2/T8.3 sweep over.

## Determinism (verified empirically for this phase, not assumed)

`context.seedRandomGenerator(seed)` called BEFORE `PlantArchitecture(context)` makes
growth fully deterministic -- Phase 5 found this by accident (a fresh process
reproduced Phase 2's exact 83-fruit count); PHASE8_LOG.md re-verified it directly here
with a same-seed/different-seed A/B/C build (identical primitive/fruit/leaf counts for
two independent seed=1000 builds, different counts for seed=1001). Every canopy this
factory builds calls `seedRandomGenerator` first for exactly this reason -- it is what
makes "identical canopies across conditions" (the paired design the task requires) real
rather than aspirational.

## Disjoint dev/test seeds

DEV_SEEDS and TEST_SEEDS are disjoint `range()` objects by construction (1000-1999 vs
2000-2999); `verify_disjoint_seeds()` checks this for real (not just "obviously true by
construction") in case someone edits the ranges later.

## What a "factor level" actually changes, and why (no native build-parameter knobs)

Neither `apple` nor `apple_fruitingwall` exposes build_parameters for LAI, fruit
density, or fruit clustering (checked directly in helios-core's PlantLibrary.cpp --
`apple`'s buildAppleTree only reads trunk_height/num_scaffolds/scaffold_angle;
`apple_fruitingwall`'s buildAppleFruitingWall reads no build_parameters at all, every
knob including tree_spacing=1.2 and wire_heights is hard-coded). So, following the same
real pattern Phase 7's T7.4 LAI sweep already established (grow the full tree once,
then remove real leaf/fruit compound objects to hit a target keep-fraction -- never
fake a lower density by rendering fewer of them, actually `context.deleteObject` them so
every downstream measurement, occlusion included, is against real remaining geometry):

- LAI level -> fraction of real leaf objects kept (deleted down from 100%, seeded
  permutation order, same pattern as `phase7/lai_sweep.py`).
- fruit_density level -> fraction of real fruit objects kept, same mechanism.
- clustering level -> WHICH fruit are kept at a given density, not what fraction:
    - "dispersed": greedy farthest-point sampling over real fruit centroids (from the
      real per-fruit ground truth, not a synthetic layout) -- keeps fruit spread out.
    - "clustered": seed a small number of real fruit, keep whichever OTHER real fruit
      are geometrically nearest those seeds (real nearest-neighbor distance) -- keeps
      fruit bunched.
  Both operate on the SAME underlying real fruit population (from the same seed), so at
  matched density the two policies are a real, paired manipulation of which real fruit
  survive, not two different canopies.
- trellis level -> `apple` vs `apple_fruitingwall` (PlantArchitecture library name).
  This is inherently a different growth model/architecture per the C++ source above (not
  just a spacing knob), so "same seed" here means "same RNG draw sequence and same
  leaf/fruit thinning permutation seed", not "bit-identical base skeleton" -- a real,
  documented limit on how "paired" this one factor's comparison can be, parallel to how
  Phase 5 documented the Phase 2/Phase 3 pose-derivation gap rather than hiding it.
"""

import numpy as np

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3

from yogesh_dev.phase1.ground_truth import enable_fruit_object_data, export_fruit_ground_truth

# Disjoint by construction -- verified for real by verify_disjoint_seeds(), not just asserted.
DEV_SEEDS = range(1000, 2000)
TEST_SEEDS = range(2000, 3000)

TRELLIS_TYPES = ("apple", "apple_fruitingwall")

DEFAULT_AGE_DAYS = 720.0


def verify_disjoint_seeds():
    """Real check, not an assumption: DEV_SEEDS and TEST_SEEDS share no seed."""
    dev = set(DEV_SEEDS)
    test = set(TEST_SEEDS)
    overlap = dev & test
    return {
        "n_dev_seeds": len(dev),
        "n_test_seeds": len(test),
        "n_overlap": len(overlap),
        "disjoint": len(overlap) == 0,
    }


def _tree_spacing_positions(n_trees, spacing):
    """n_trees positions along x, spacing meters apart, centered on x=0 (matches
    Phase 0's build_three_tree_scene layout convention for n_trees=3, spacing=1.5)."""
    return [vec3((i - (n_trees - 1) / 2.0) * spacing, 0, 0) for i in range(n_trees)]


def _leaf_objects(context, all_uuids):
    leaf_uuids = context.filterPrimitivesByData(all_uuids, "object_label", "leaf")
    return list(context.getUniquePrimitiveParentObjectIDs(leaf_uuids, include_zero=False))


def _thin_leaves(context, all_uuids, keep_frac, seed):
    """Delete real leaf objects down to `keep_frac` of the original count, seeded
    permutation order (same mechanism as phase7/lai_sweep.py).

    Returns (n_kept, n_total, deleted_primitive_uuids). `deleted_primitive_uuids` (a
    set) matters because of a real gotcha discovered in this phase (see
    PHASE8_LOG.md): calling `plantarch.getAllPlantUUIDs(plant_id)` again AFTER any
    `context.deleteObject(...)` on that plant's leaf/fruit objects raises
    `unordered_map::at` inside helios-core -- deleteObject removes the primitives from
    Context but does not keep PlantArchitecture's own internal bookkeeping consistent
    for a later re-enumeration. So callers must capture the plant's full UUID list
    ONCE before any deletion and subtract deleted UUIDs in Python, never re-query
    PlantArchitecture after thinning.
    """
    leaf_objs = _leaf_objects(context, all_uuids)
    n_total = len(leaf_objs)
    if n_total == 0 or keep_frac >= 1.0:
        return n_total, n_total, set()
    rng = np.random.default_rng(seed)
    order = [leaf_objs[i] for i in rng.permutation(n_total)]
    target_keep = int(round(keep_frac * n_total))
    to_delete = order[target_keep:]
    deleted_uuids = set()
    if to_delete:
        for oid in to_delete:
            deleted_uuids.update(context.getObjectPrimitiveUUIDs(oid))
        context.deleteObject(to_delete)
    return target_keep, n_total, deleted_uuids


def _farthest_point_order(centroids, seed):
    """Greedy farthest-point-sampling order over real fruit centroids: index 0 is a
    seeded-random start, each subsequent index is whichever remaining point maximizes
    its minimum distance to already-chosen points. Real O(n^2) computation on real
    centroid coordinates -- this canopy's fruit count is small (tens), so this is cheap."""
    n = len(centroids)
    pts = np.asarray(centroids, dtype=float)
    rng = np.random.default_rng(seed)
    remaining = list(range(n))
    start = int(rng.integers(0, n))
    order = [remaining.pop(start if start < len(remaining) else 0)]
    min_dist = np.linalg.norm(pts[remaining] - pts[order[-1]], axis=1) if remaining else np.array([])
    while remaining:
        best_local = int(np.argmax(min_dist))
        chosen = remaining.pop(best_local)
        min_dist = np.delete(min_dist, best_local)
        order.append(chosen)
        if remaining:
            d_new = np.linalg.norm(pts[remaining] - pts[chosen], axis=1)
            min_dist = np.minimum(min_dist, d_new)
    return order


def _cluster_order(centroids, seed, n_seed_clusters=2):
    """Order real fruit by distance to a small seeded set of "cluster seed" fruit, so
    keeping the first `k` gives a spatially bunched subset rather than a spread one.
    Real nearest-neighbor distance on real centroid coordinates."""
    n = len(centroids)
    pts = np.asarray(centroids, dtype=float)
    rng = np.random.default_rng(seed + 500)
    n_seed_clusters = max(1, min(n_seed_clusters, n))
    seed_idx = rng.choice(n, size=n_seed_clusters, replace=False)
    dist_to_nearest_seed = np.min(
        np.linalg.norm(pts[:, None, :] - pts[seed_idx][None, :, :], axis=2), axis=1)
    return list(np.argsort(dist_to_nearest_seed))


def _thin_fruit(context, fruit_records, keep_frac, clustering, seed):
    """Delete real fruit objects down to `keep_frac` of the original count, selecting
    WHICH fruit survive according to `clustering` ("dispersed" or "clustered"). Returns
    (n_kept, n_total, kept_fruit_records, deleted_primitive_uuids) -- see
    `_thin_leaves`'s docstring for why `deleted_primitive_uuids` must be tracked here
    rather than re-derived later via a fresh PlantArchitecture query."""
    n_total = len(fruit_records)
    if n_total == 0 or keep_frac >= 1.0:
        return n_total, n_total, list(fruit_records), set()

    centroids = [r["centroid"] for r in fruit_records]
    target_keep = max(0, int(round(keep_frac * n_total)))

    if clustering == "dispersed":
        order = _farthest_point_order(centroids, seed)
    elif clustering == "clustered":
        order = _cluster_order(centroids, seed)
    else:
        raise ValueError(f"unknown clustering policy {clustering!r}")

    keep_idx = set(order[:target_keep])
    to_delete_objs = [fruit_records[i]["object_id"] for i in range(n_total) if i not in keep_idx]
    deleted_uuids = set()
    for i in range(n_total):
        if i not in keep_idx:
            deleted_uuids.update(fruit_records[i]["primitive_uuids"])
    if to_delete_objs:
        context.deleteObject(to_delete_objs)
    kept_records = [fruit_records[i] for i in sorted(keep_idx)]
    return len(kept_records), n_total, kept_records, deleted_uuids


class Canopy:
    """Live handles + metadata for one built canopy. Caller owns the context managers
    (`context`, `plantarch`) it entered -- close them in reverse order when done, same
    convention as phase5/common.py's build_scene()."""

    def __init__(self, context, plantarch, seed, tree_type, plant_ids, positions,
                 fruit_records, thinning_report, build_time_s, cached_uuids, cached_per_tree_uuids):
        self.context = context
        self.plantarch = plantarch
        self.seed = seed
        self.tree_type = tree_type
        self.plant_ids = plant_ids
        self.positions = positions
        self.fruit_records = fruit_records
        self.thinning_report = thinning_report
        self.build_time_s = build_time_s
        self._cached_uuids = cached_uuids
        self._cached_per_tree_uuids = cached_per_tree_uuids

    def all_uuids(self):
        """Returns the cached post-thinning UUID list captured at build time. Does
        NOT re-query `plantarch.getAllPlantUUIDs()` -- see `_thin_leaves`'s docstring:
        that call reliably raises `unordered_map::at` once any leaf/fruit object on
        this plant has been deleted via `context.deleteObject`, a real gotcha found
        while building this factory (PHASE8_LOG.md)."""
        return list(self._cached_uuids)

    def tree_uuids(self, tree_index):
        """Cached post-thinning UUID list for one tree (index into plant_ids/positions),
        for callers that need per-tree bounding boxes (e.g. camera placement) without
        re-querying PlantArchitecture -- same rationale as `all_uuids()`."""
        return list(self._cached_per_tree_uuids[tree_index])

    def close(self):
        self.plantarch.__exit__(None, None, None)
        self.context.__exit__(None, None, None)


def build_canopy(seed, tree_type="apple", n_trees=1, spacing=1.5, age_days=DEFAULT_AGE_DAYS,
                  lai_keep_frac=1.0, fruit_keep_frac=1.0, clustering="dispersed",
                  build_parameters=None, ground_truth_path=None):
    """T8.1's real, reusable canopy factory. Same seed + same factor levels ALWAYS
    reproduces the same canopy (see module docstring) -- this is what makes every later
    T8.2/T8.4 comparison a real paired design instead of an assumed one.

    Args:
        seed: RNG seed, applied via context.seedRandomGenerator BEFORE PlantArchitecture
            construction (see module docstring) and reused (offset) for leaf/fruit
            thinning order, so the same seed always gives the same base tree AND the
            same thinning permutation.
        tree_type: "apple" or "apple_fruitingwall" (T8.3's trellis factor).
        n_trees, spacing: canopy layout (Phase 0's convention: n_trees positions along
            x, `spacing` meters apart).
        lai_keep_frac: fraction of real leaf objects kept (1.0 = no thinning).
        fruit_keep_frac: fraction of real fruit objects kept (1.0 = no thinning).
        clustering: "dispersed" or "clustered" -- which fruit survive thinning (only
            matters when fruit_keep_frac < 1.0).
        ground_truth_path: if given, write fruit_ground_truth.json (pre-thinning) here.

    Returns: a Canopy (caller must call .close()).
    """
    if tree_type not in TRELLIS_TYPES:
        raise ValueError(f"tree_type must be one of {TRELLIS_TYPES}, got {tree_type!r}")

    context = Context()
    context.__enter__()
    context.seedRandomGenerator(seed)

    plantarch = PlantArchitecture(context)
    plantarch.__enter__()
    enable_fruit_object_data(plantarch)

    import time
    t0 = time.time()
    plantarch.loadPlantModelFromLibrary(tree_type)
    positions = _tree_spacing_positions(n_trees, spacing)
    plant_ids = [
        plantarch.buildPlantInstanceFromLibrary(base_position=p, age=age_days,
                                                 build_parameters=build_parameters)
        for p in positions
    ]
    build_time_s = time.time() - t0

    # Captured ONCE, before any thinning -- see _thin_leaves's docstring for why
    # plantarch.getAllPlantUUIDs must never be called again after deleteObject.
    per_tree_uuids_pre_thin = [plantarch.getAllPlantUUIDs(pid) for pid in plant_ids]
    all_uuids = [u for uuids in per_tree_uuids_pre_thin for u in uuids]

    if ground_truth_path is not None:
        fruit_records, gt_report = export_fruit_ground_truth(context, plantarch, plant_ids, ground_truth_path)
    else:
        # Still need the records (centroids, object ids) even without writing to disk --
        # reuse the same real export logic, just point it at a throwaway path is wasteful;
        # instead call the same underlying logic without requiring a file write.
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as td:
            fruit_records, gt_report = export_fruit_ground_truth(
                context, plantarch, plant_ids, os.path.join(td, "_tmp_fruit_gt.json"))

    n_leaf_total_pre = len(_leaf_objects(context, all_uuids))
    n_fruit_total_pre = len(fruit_records)

    n_leaf_kept, n_leaf_total, deleted_leaf_uuids = _thin_leaves(context, all_uuids, lai_keep_frac, seed)
    n_fruit_kept, n_fruit_total, kept_fruit_records, deleted_fruit_uuids = _thin_fruit(
        context, fruit_records, fruit_keep_frac, clustering, seed)

    # Cache post-thinning UUID lists NOW, in Python, from the pre-thin lists minus
    # exactly what was deleted -- never re-query plantarch.getAllPlantUUIDs after this
    # point (see _thin_leaves's docstring for the real crash that motivates this).
    deleted_all = deleted_leaf_uuids | deleted_fruit_uuids
    cached_uuids = [u for u in all_uuids if u not in deleted_all]
    cached_per_tree_uuids = [[u for u in uuids if u not in deleted_all] for uuids in per_tree_uuids_pre_thin]

    thinning_report = {
        "lai_keep_frac_requested": lai_keep_frac,
        "n_leaf_total": n_leaf_total,
        "n_leaf_kept": n_leaf_kept,
        "fruit_keep_frac_requested": fruit_keep_frac,
        "clustering": clustering,
        "n_fruit_total": n_fruit_total,
        "n_fruit_kept": n_fruit_kept,
        "n_leaf_total_pre_thin": n_leaf_total_pre,
        "n_fruit_total_pre_thin": n_fruit_total_pre,
        "gt_report": gt_report,
    }

    return Canopy(context, plantarch, seed, tree_type, plant_ids, positions,
                  kept_fruit_records, thinning_report, build_time_s, cached_uuids, cached_per_tree_uuids)
