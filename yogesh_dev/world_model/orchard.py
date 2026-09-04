"""
W0 -- Seeded 2-row x 10-tree apple orchard factory for the world-model dataset.

This is the *only* place an orchard is built. Everything downstream (W1's render
rig, W3's dataset generator) goes through `build_orchard()`.

## What this reuses rather than reimplements

- `yogesh_dev/phase8/canopy_factory.py` -- the seeding scheme (`seedRandomGenerator`
  BEFORE `PlantArchitecture(context)`), the cache-UUIDs-before-thinning discipline,
  and the leaf/fruit thinning primitives. This module deliberately mirrors its
  `Canopy` class shape (`.all_uuids()`, `.close()`) so Phase 8 code can consume an
  Orchard where it expects a Canopy.
- `yogesh_dev/phase1/ground_truth.py` -- `enable_fruit_object_data` (the
  `optionalOutputObjectData`-before-build ordering gotcha) and
  `export_fruit_ground_truth`.
- `yogesh_dev/phase1/label_maps.py` -- `assign_semantic_class_ids`, which is
  mandatory: `getPrimitiveDataLabelMap(cam, "object_label")` silently returns an
  all-background map because `object_label` is string-typed.

## What is new here

1. **Canopy layout via `buildPlantCanopyFromLibrary`** rather than a Python loop of
   `buildPlantInstanceFromLibrary`. `plant_count=int2(10,2)` and
   `plant_spacing=vec2(1.5,3.5)` -> 10 trees along x (in-row), 2 rows along y.
   Row axis = x, across-row = y. This returns plant IDs in a single call, and is
   the API the plan specifies.
2. **Per-organ optical properties** (`reflectivity_<band>` / `transmissivity_<band>`),
   which is what makes the RGB render show green leaves and brown branches instead
   of the blown-out white blobs Phase 0 documented. Requires `disableEmission(band)`
   on the RadiationModel side -- see `render.py`.
3. **Cached UUID lists** captured once at build time, per-tree and global, so nothing
   downstream ever re-queries `plantarch.getAllPlantUUIDs()` (Phase 8 gotcha: that
   segfaults / raises `unordered_map::at` after any `context.deleteObject`).

## Growth channel

`grow(dt)` wraps `plantarch.advanceTime(dt)`. **Calling it invalidates the cached
UUID lists** -- growth adds new primitives that were not in the cached list. After a
grow step the caches are refreshed by re-querying `getAllPlantUUIDs` (which is safe
*as long as nothing has been deleted*, i.e. as long as no thinning was applied).
`Orchard.grow()` raises if thinning was applied, rather than silently returning a
stale or crashing UUID list.
"""

import os
import time

import numpy as np

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3, vec2, int2

from yogesh_dev.phase1.ground_truth import enable_fruit_object_data, export_fruit_ground_truth
from yogesh_dev.phase1.label_maps import assign_semantic_class_ids, SEMANTIC_CLASSES

# ---------------------------------------------------------------------------
# Fixed orchard geometry (Section 4 of WORLD_MODEL_PLAN.md). Do not vary these
# across experiments -- the plan fixes them so every result stays comparable.
# ---------------------------------------------------------------------------
ROWS = 2                 # number of rows (along y)
TREES_PER_ROW = 10       # trees per row (along x)
IN_ROW_SPACING = 1.5     # m, between trees within a row (x)
ROW_SPACING = 3.5        # m, between the two rows (y)
TREE_TYPES = ("apple", "apple_fruitingwall")
DEFAULT_TREE_TYPE = "apple"

# Seed streams, disjoint by construction, verified by verify_seed_split().
# Deliberately offset from Phase 8's DEV_SEEDS/TEST_SEEDS (1000-2999) so a
# world-model orchard is never confused with a Phase 8 canopy.
TRAIN_SEEDS = range(10000, 10999)
VAL_SEEDS = range(11000, 11499)
TEST_SEEDS = range(12000, 12499)

# ---------------------------------------------------------------------------
# Per-organ optical properties.
#
# These are *plausible visible-RGB* values, not calibrated spectra -- same stance
# as phase0/radiation_setup.py's docstring takes for flux. They are chosen so the
# band ratios are physically sensible for foliage (green > red > blue reflectance)
# and so bark/fruit are distinguishable. `transmissivity` is nonzero only for thin
# organs (leaf, petiole) -- wood and fruit are treated as opaque.
#
# CONSTRAINT (helios-core): emissivity + transmissivity + reflectivity must sum to
# 1 per band, so `disableEmission(band)` must be called before setting these or
# `runBand()` aborts. reflectivity + transmissivity is kept <= 1 for every entry.
# ---------------------------------------------------------------------------
ORGAN_OPTICS = {
    #            reflectivity (r,g,b)      transmissivity (r,g,b)
    "leaf":     ((0.075, 0.170, 0.050), (0.050, 0.110, 0.030)),
    "petiole":  ((0.100, 0.180, 0.060), (0.020, 0.040, 0.015)),
    "peduncle": ((0.100, 0.180, 0.060), (0.020, 0.040, 0.015)),
    "shoot":    ((0.190, 0.140, 0.100), (0.000, 0.000, 0.000)),
    "fruit":    ((0.420, 0.150, 0.110), (0.000, 0.000, 0.000)),
    # Ground: dry soil / grass alley. Added because W1's first contact sheet
    # showed ~61% of every frame was "sky" -- there was no ground plane, so the
    # entire lower half of every view was empty space rendered as background.
    # A world model trained on that would spend most of its capacity on a
    # constant. See W1 findings.
    "ground":   ((0.110, 0.098, 0.068), (0.000, 0.000, 0.000)),
}
# Per-patch multiplicative jitter on the ground's reflectivity, seeded from the
# orchard seed. Without it the alley renders as one flat colour, which gives the
# world model NO optical-flow cue in ~46% of every frame -- an action-conditioned
# model that has to infer "how far did I move" from the image would be reading
# only the canopy. With jitter the ground carries real, static, per-orchard
# texture that moves correctly under camera motion.
GROUND_REFLECTANCE_JITTER = 0.35
BAND_ORDER = ("red", "green", "blue")

# Ground plane geometry. Large enough that the horizon is never visible from any
# in-lane camera pose, subdivided so the radiative solve gets some spatial
# variation rather than one flat patch.
GROUND_SIZE_M = (40.0, 24.0)
GROUND_SUBDIV = (80, 48)
GROUND_LABEL = "ground"


def verify_seed_split():
    """Real check that the three seed streams are disjoint (W3 acceptance)."""
    tr, va, te = set(TRAIN_SEEDS), set(VAL_SEEDS), set(TEST_SEEDS)
    return {
        "n_train": len(tr), "n_val": len(va), "n_test": len(te),
        "train_val_overlap": len(tr & va),
        "train_test_overlap": len(tr & te),
        "val_test_overlap": len(va & te),
        "disjoint": len(tr & va) == 0 and len(tr & te) == 0 and len(va & te) == 0,
    }


def apply_organ_optics(context, all_uuids, optics=None, bands=BAND_ORDER):
    """Set `reflectivity_<band>` / `transmissivity_<band>` per organ.

    Returns {organ: n_primitives_matched} for logging. Organs with no matching
    primitives are reported with 0 rather than skipped silently, so an empty
    'fruit' entry (which happens at age 540 d -- see the age->fruit curve) is
    visible in the log instead of being mistaken for a working setup.
    """
    if optics is None:
        optics = ORGAN_OPTICS
    counts = {}
    for organ, (refl, trans) in optics.items():
        matched = context.filterPrimitivesByData(all_uuids, "object_label", organ)
        counts[organ] = len(matched)
        if not matched:
            continue
        for band, r, t in zip(bands, refl, trans):
            context.setPrimitiveDataFloat(matched, f"reflectivity_{band}", float(r))
            if t > 0.0:
                context.setPrimitiveDataFloat(matched, f"transmissivity_{band}", float(t))
    return counts


class Orchard:
    """Live handles + metadata for one built orchard. Caller owns the context
    managers -- call `.close()` when done (or use as a context manager)."""

    def __init__(self, context, plantarch, seed, tree_type, age_days, plant_ids,
                 build_time_s, cached_uuids, cached_per_tree_uuids, fruit_records,
                 organ_counts, optics_counts, thinned=False, ground_uuids=()):
        self.ground_uuids = list(ground_uuids)
        self.context = context
        self.plantarch = plantarch
        self.seed = seed
        self.tree_type = tree_type
        self.age_days = age_days
        self.plant_ids = plant_ids
        self.build_time_s = build_time_s
        self._cached_uuids = cached_uuids
        self._cached_per_tree_uuids = cached_per_tree_uuids
        self.fruit_records = fruit_records
        self.organ_counts = organ_counts
        self.optics_counts = optics_counts
        self._thinned = thinned
        self.grow_history = []  # list of {"dt": float, "seconds": float, "n_primitives": int}

    # -- accessors -----------------------------------------------------------
    def all_uuids(self):
        """Cached UUID list (plants + ground). Never re-queries PlantArchitecture
        (Phase 8 gotcha)."""
        return list(self._cached_uuids) + list(self.ground_uuids)

    def plant_uuids(self):
        """Plant primitives only, excluding the ground plane."""
        return list(self._cached_uuids)

    def tree_uuids(self, tree_index):
        return list(self._cached_per_tree_uuids[tree_index])

    def n_primitives(self):
        """Plant primitives only -- the ground plane is a fixed-size backdrop and
        including it would make orchard-size comparisons across ages misleading."""
        return len(self._cached_uuids)

    def bounds(self):
        """Axis-aligned world bounds of the PLANTS (ground excluded), from real
        primitive vertices. Returns (min_xyz, max_xyz) as numpy arrays."""
        xb, yb, zb = self.context.getDomainBoundingBox(self._cached_uuids)
        return (np.array([xb.x, yb.x, zb.x], dtype=float),
                np.array([xb.y, yb.y, zb.y], dtype=float))

    # -- growth channel ------------------------------------------------------
    def grow(self, dt):
        """Advance plant growth by `dt` days and refresh the UUID caches.

        Raises if this orchard was thinned: after `context.deleteObject`,
        `plantarch.getAllPlantUUIDs` raises `unordered_map::at` (Phase 8 finding),
        so the caches cannot be refreshed and would go stale.
        """
        if self._thinned:
            raise RuntimeError(
                "grow() on a thinned orchard is unsupported: refreshing the UUID cache "
                "requires getAllPlantUUIDs, which crashes after context.deleteObject "
                "(Phase 8 gotcha). Build a fresh orchard at the target age instead.")
        t0 = time.time()
        self.plantarch.advanceTime(float(dt))
        elapsed = time.time() - t0
        self.age_days += float(dt)
        self._refresh_caches()
        self.grow_history.append({"dt": float(dt), "seconds": elapsed,
                                  "n_primitives": self.n_primitives()})
        return elapsed

    def _refresh_caches(self):
        per_tree = [self.plantarch.getAllPlantUUIDs(pid) for pid in self.plant_ids]
        self._cached_per_tree_uuids = per_tree
        self._cached_uuids = [u for uu in per_tree for u in uu]
        # New primitives from growth carry object_label but not our derived fields.
        uu = self.all_uuids()
        self.organ_counts = assign_semantic_class_ids(self.context, uu)
        self.optics_counts = apply_organ_optics(self.context, uu)

    # -- lifecycle -----------------------------------------------------------
    def close(self):
        self.plantarch.__exit__(None, None, None)
        self.context.__exit__(None, None, None)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def summary(self):
        return {
            "seed": self.seed,
            "tree_type": self.tree_type,
            "age_days": self.age_days,
            "n_trees": len(self.plant_ids),
            "n_primitives": self.n_primitives(),
            "build_time_s": self.build_time_s,
            "organ_primitive_counts": dict(self.organ_counts),
            "optics_primitive_counts": dict(self.optics_counts),
            "n_fruit_objects": len(self.fruit_records),
            "grow_history": list(self.grow_history),
        }


def build_orchard(seed, age_days=720.0, tree_type=DEFAULT_TREE_TYPE,
                  trees_per_row=TREES_PER_ROW, rows=ROWS,
                  in_row_spacing=IN_ROW_SPACING, row_spacing=ROW_SPACING,
                  fruit_ground_truth_path=None, apply_optics=True,
                  build_parameters=None, add_ground=True):
    """Build one seeded 2x10 orchard. Returns an `Orchard` (caller must `.close()`).

    Ordering matters and is load-bearing, in this exact order:
      1. `context.seedRandomGenerator(seed)`  -- before PlantArchitecture exists.
      2. `PlantArchitecture(context)`
      3. `optionalOutputObjectData(...)`      -- BEFORE any build call.
      4. `loadPlantModelFromLibrary` / `buildPlantCanopyFromLibrary`
      5. cache UUIDs, derive semantic_class_id, set optical properties.
    """
    if tree_type not in TREE_TYPES:
        raise ValueError(f"tree_type must be one of {TREE_TYPES}, got {tree_type!r}")

    context = Context()
    context.__enter__()
    context.seedRandomGenerator(int(seed))

    plantarch = PlantArchitecture(context)
    plantarch.__enter__()
    enable_fruit_object_data(plantarch)          # optionalOutputObjectData, BEFORE build

    t0 = time.time()
    plantarch.loadPlantModelFromLibrary(tree_type)
    plant_ids = plantarch.buildPlantCanopyFromLibrary(
        canopy_center=vec3(0.0, 0.0, 0.0),
        plant_spacing=vec2(float(in_row_spacing), float(row_spacing)),
        plant_count=int2(int(trees_per_row), int(rows)),
        age=float(age_days),
        germination_rate=1.0,
        build_parameters=build_parameters,
    )
    build_time_s = time.time() - t0

    per_tree_uuids = [plantarch.getAllPlantUUIDs(pid) for pid in plant_ids]
    all_uuids = [u for uu in per_tree_uuids for u in uu]

    if fruit_ground_truth_path is not None:
        os.makedirs(os.path.dirname(os.path.abspath(fruit_ground_truth_path)), exist_ok=True)
        fruit_records, _ = export_fruit_ground_truth(
            context, plantarch, plant_ids, fruit_ground_truth_path)
    else:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            fruit_records, _ = export_fruit_ground_truth(
                context, plantarch, plant_ids, os.path.join(td, "fruit_gt.json"))

    ground_uuids = []
    if add_ground:
        from pyhelios.types import vec2 as _vec2, int2 as _int2, RGBcolor
        ground_uuids = list(context.addTile(
            center=vec3(0.0, 0.0, 0.0),
            size=_vec2(*GROUND_SIZE_M),
            subdiv=_int2(*GROUND_SUBDIV),
            color=RGBcolor(0.45, 0.40, 0.30)))
        # object_label makes the ground selectable by the same
        # filterPrimitivesByData path the plant organs use; it maps to semantic
        # class 0 ("other") because it is not one of SEMANTIC_CLASSES' keys.
        context.setPrimitiveDataString(ground_uuids, "object_label", GROUND_LABEL)

    combined = list(all_uuids) + ground_uuids
    organ_counts = assign_semantic_class_ids(context, combined)
    optics_counts = apply_organ_optics(context, combined) if apply_optics else {}

    if add_ground and apply_optics and ground_uuids:
        # Seeded per-patch reflectance texture (see GROUND_REFLECTANCE_JITTER).
        rng = np.random.default_rng(int(seed) * 6151 + 7)
        base_refl = ORGAN_OPTICS[GROUND_LABEL][0]
        j = rng.uniform(1.0 - GROUND_REFLECTANCE_JITTER, 1.0 + GROUND_REFLECTANCE_JITTER,
                        size=len(ground_uuids))
        for band, r in zip(BAND_ORDER, base_refl):
            vals = np.clip(j * r, 0.01, 0.95)
            for u, v in zip(ground_uuids, vals):
                context.setPrimitiveDataFloat(u, f"reflectivity_{band}", float(v))

    return Orchard(context, plantarch, int(seed), tree_type, float(age_days), plant_ids,
                   build_time_s, all_uuids, per_tree_uuids, fruit_records,
                   organ_counts, optics_counts, ground_uuids=ground_uuids)


def orchard_extent(trees_per_row=TREES_PER_ROW, rows=ROWS,
                   in_row_spacing=IN_ROW_SPACING, row_spacing=ROW_SPACING):
    """Nominal planting-grid extent (tree base positions only, not canopy).

    `buildPlantCanopyFromLibrary` centres the grid on `canopy_center`, so with
    plant_count=(10,2) and spacing=(1.5,3.5) the tree bases span
    x in [-6.75, +6.75] and y in [-1.75, +1.75]. Returned as
    (x_min, x_max, y_min, y_max, lane_y) where lane_y is the inter-row lane
    centre (y=0 by construction: exactly between the two rows).
    """
    half_x = (trees_per_row - 1) * in_row_spacing / 2.0
    half_y = (rows - 1) * row_spacing / 2.0
    return {
        "x_min": -half_x, "x_max": half_x,
        "y_min": -half_y, "y_max": half_y,
        "lane_y": 0.0,
        "row_y": [-half_y + i * row_spacing for i in range(rows)],
        "tree_x": [-half_x + i * in_row_spacing for i in range(trees_per_row)],
    }


SEMANTIC_CLASS_NAMES = {v: k for k, v in SEMANTIC_CLASSES.items()}
