# Phase 1 log

Unattended run implementing `helios_setup_tasks.md`'s Phase 1 (T1.1-T1.6:
ground truth export), built on top of Phase 0's validated radiation-camera
rig and pose convention. Everything below is chronological; numbers are
real measurements from this run, not estimates.

Machine: same devbox as Phase 0 (RTX 5090, OptiX 8.1 backend, no physical
display). `helios` conda env, `/home/yogesh/anaconda3/envs/helios/bin/python`.

## Environment / worktree setup

1. **This worktree also branched from `origin/master`, not `apple-tree-cameras`.**
   Same situation Phase 0 hit (its own worktree did too, per
   `worktree-phase0-radiation`'s own log): the harness's `EnterWorktree`
   defaults to branching fresh off the repo's default branch, not the
   branch the session started on. Consequence: `yogesh_dev/` (including all
   of Phase 0's own deliverables) did not exist in this worktree at all, nor
   did `apple_tree.py` / `apple_tree_cameras.py`. Fix: same as Phase 0 --
   copied the 4 Phase 0 dependency modules
   (`canopy.py`, `radiation_setup.py`, `radiation_cameras.py`,
   `pose_convention.py`) verbatim from the still-present
   `.claude/worktrees/phase0-radiation` worktree into a new
   `yogesh_dev/phase0/` package in *this* worktree, unmodified, then built
   `yogesh_dev/phase1/` on top of them. Everything produced is still under
   `yogesh_dev/`; nothing outside it was touched.
2. **Build artifacts / submodule**, same fix as Phase 0: symlinked
   `helios-core -> /home/yogesh/PyHelios/helios-core` and
   `pyhelios_build/build -> /home/yogesh/PyHelios/pyhelios_build/build`
   from the main checkout (both are gitignored/submodule content, not
   tracked repo state). Verified with a plain `from pyhelios import Context,
   PlantArchitecture, RadiationModel` smoke import after linking.
3. **`imageio` and `OpenEXR` were not installed in the `helios` env.**
   Installed both via `pip install imageio OpenEXR` inside
   `/home/yogesh/anaconda3/envs/helios/bin/pip` (task doc explicitly allows
   this). `OpenEXR` (the PyPI package, v3.4.13) installed a prebuilt
   `manylinux2014_x86_64` wheel -- no system OpenEXR/Imath headers needed.
   Verified with a round-trip write/read test (`OpenEXR.File(header,
   channels)` -> `.write()` -> re-read -> exact match) before trusting it
   for T1.4.

## T1.1 -- enable optional object data, verified

`phase1/ground_truth.py`. Ran an explicit A/B test (not in the final
pipeline, a one-off throwaway script) building one real apple tree
(age=720 days) two ways:

| when `optionalOutputObjectData(...)` is called | result |
|---|---|
| **before** `buildPlantInstanceFromLibrary` | `listObjectData()` on a real fruit object = `['age', 'fruitID', 'phenology_stage', 'rank']` -- all 4 checkable fields present |
| **after** `buildPlantInstanceFromLibrary` (as the task doc's own snippet literally orders it: "After building the plants: `plantarch.optionalOutputObjectData(...)`") | `listObjectData()` = `[]` -- **nothing** present |

This matches `helios-core/plugins/plantarchitecture/src/PlantArchitecture.cpp`:
the `output_object_data["fruitID"|"rank"|"age"|...]` flags are read once, at
the moment each phytomer/fruit-bud compound object is constructed during
growth advancement inside `buildPlantInstanceFromLibrary`/
`loadPlantModelFromLibrary`, not retroactively. **The task doc's own ordering
is wrong** -- confirmed empirically, not assumed. `enable_fruit_object_data()`
in `ground_truth.py` calls it first, immediately after constructing
`PlantArchitecture(context)`.

Second gotcha, also empirical: **`plantID` is never set on fruit objects.**
Reading the same C++ source, `plantID` object data is only written onto
internode-tube / petiole / leaf compound objects, never onto the fruit
object created in the flower-bud state-machine transition. So
`fruit_ground_truth.json`'s `plant_id` field cannot come from
`getObjectDataInt(oid, "plantID")` on the fruit object itself (that call
would raise `HeliosRuntimeError` -- data doesn't exist) -- it's derived
instead by cross-referencing each fruit's primitive UUIDs against each
tree's own `plantarch.getAllPlantUUIDs(plant_id)` set, built once as a
uuid->plant_id lookup.

Real verification from the full pipeline run (`plant1_id=1487` object, i.e. a
real fruit object from the actual 3-tree scene, not the throwaway A/B test):
```
labels_present = ['age', 'fruitID', 'phenology_stage', 'rank']
all_expected_present = True
```
The driver (`run_phase1.py`) raises immediately if this check ever fails,
rather than silently exporting a ground-truth file with missing labels.

## T1.2 -- fruit ground truth export

`phase1/ground_truth.py:export_fruit_ground_truth`. Equivalent diameter uses
the sphere-equivalent-surface-area formula `D = sqrt(SA/pi)` (for a sphere,
`SA = pi*D^2`).

Real numbers, one full run of the 3-tree scene (age 720 days each,
positions x=0/1.5/3, matching `apple_tree_cameras.py` and Phase 0):

```
n_fruit_primitives: 15038
n_fruit_objects:    73
n_fruit_records_written: 73
n_trees: 3
plant_id_lookup_misses: 0
```
(Primitive/fruit counts are **not** deterministic run-to-run -- same
unseeded-growth-model caveat Phase 0 already documented; a different run in
this same session gave `n_fruit_objects=83`. `fruit_ground_truth.json` is
regenerated fresh each run, this is expected, not a bug.)

Sample record (one real fruit, from the actual output file):
```json
{
  "object_id": 1299, "plant_id": 0,
  "centroid": [-0.276, 0.177, 1.147],
  "bbox_min": [-0.325, 0.128, 1.098], "bbox_max": [-0.226, 0.227, 1.196],
  "equivalent_diameter_m": 0.0974, "surface_area_m2": 0.0298,
  "primitive_uuids": [190 uuids],
  "fruitID": 1299, "rank": 1, "age": 186.0, "phenology_stage": "reproductive"
}
```
9.7 cm equivalent diameter is a plausible apple size; the sphere-SA-implied
diameter for that surface area (`sqrt(0.0298*pi)`... i.e. `SA=pi*D^2` gives
`D=sqrt(0.0298/pi)=0.0974`) matches by construction. `fruitID`/`rank`/`age`/
`phenology_stage` are included as bonus fields (already free once T1.1 is
enabled) beyond what the task doc's minimum list asked for.

## T1.3 -- semantic + instance label maps

`phase1/label_maps.py`. **The task doc's own snippet does not work as
written**, verified against source rather than assumed:
`radiation.getPrimitiveDataLabelMap(cam, "object_label")` -- `object_label`
is a **string** primitive-data field (set unconditionally by the
plant-architecture model: `"fruit"`, `"leaf"`, `"shoot"`, `"petiole"`,
`"peduncle"`). `RadiationModel::writePrimitiveDataLabelMap`
(`RadiationCamera.cpp`) only branches on `HELIOS_TYPE_{FLOAT,UINT,INT,DOUBLE}`;
anything else (including string) falls into the `else` branch, which writes
`padvalue` for **every** pixel and prints a C++-side `stderr` warning ("No
primitive data ... found") -- it does **not** raise a Python exception. Passed
through as the task doc suggests, this would have silently produced an
all-NaN "semantic map" that looks superficially fine (right shape, no
Python error) and is completely empty. Fix: derive a new int-typed
`semantic_class_id` primitive-data field from `object_label` via
`filterPrimitivesByData` + `setPrimitiveDataInt` (once, right after the
trees are built), then label-map *that* field instead. Class table:
`fruit=1, leaf=2, shoot=3, petiole=4, peduncle=5`, `0`="other" (NaN stays
reserved for true background/no-hit, which is a materially different thing
from "hit geometry with an unrecognized label").

The instance map (`getObjectDataLabelMap(cam, "fruitID")`) works directly as
the task doc describes -- `fruitID` is already `int`-typed on fruit objects
(see T1.1), which is one of the natively-supported types.

Also confirmed empirically: `getPrimitiveDataLabelMap` /
`getObjectDataLabelMap` in the current PyHelios (`pyhelios/RadiationModel.py`)
are **already** NumPy-returning convenience wrappers around the
file+`np.loadtxt` round trip described in the task doc -- there is no manual
text-parsing step to write in Python. The perf caveat (text round-trip, ~300k
floats/call) is still real and still lives entirely inside those wrapper
methods; not reproduced or worked around here since it's fine for
dataset-generation.

Real numbers, one view (`tree1_above`, real render): 5/5 semantic classes
present, 73 distinct fruit instances visible in that single view,
background fraction 0.756. Across all 9 views: background fraction ranged
0.73-0.83 (more of the frame is sky than tree, as expected for these
camera distances), all 5 semantic classes present in every view. `.npy`
(canonical) + a colorized `.png` preview written per view per map type
(4 files/view x 9 views = 36 files in `output/labels/`). Eyeballed
`tree1_above_semantic.png` and `tree1_above_instance.png`: silhouettes
match the tree shapes exactly, instance blobs align with visible fruit
clusters, no antialiasing erosion or color-ambiguity artifacts (unlike the
old flat-color-render hack this replaces).

## T1.4 -- depth via EXR

`phase1/depth_export.py`. `writeDepthImageDataEXR` + `OpenEXR` read-back,
per the task doc (no in-memory depth getter exists for the radiation
camera in PyHelios; `Visualizer.getDepthMap()` is the separate,
upstream-broken path documented in Phase 0's T0.7 -- not used here, and not
silently worked around).

**Empirical finding, not documented anywhere in the task doc or PyHelios
docstrings: background/sky pixels (primary camera ray hits no geometry) get
depth EXACTLY `-1.0`**, not some large far-plane sentinel. Verified
pixel-for-pixel against the semantic label map's NaN (background) mask on a
real render (`tree0_above`): 254,257 pixels are exactly `depth == -1.0`,
254,257 pixels are exactly `isnan(semantic)` -- 100% overlap, zero pixels in
either exclusive set. Real (non-sky) depth on that same view ranged
3.11-5.55 m (mean 4.34 m), consistent with the rig's camera-to-canopy
framing distances. This -1.0 sentinel matters a lot for anyone consuming
these EXR files directly (a naive `depth.mean()` without masking would be
dominated by -1 values and come out negative, exactly the bug this log
entry exists to prevent someone from re-discovering the hard way -- see
`depth_export.depth_stats()`'s `valid_mask` parameter). This alignment also
means the semantic map's NaN mask can be used directly as the depth "valid"
mask without any depth-specific heuristics.

## T1.5 -- transforms.json

`phase1/transforms_export.py`. Reused (not re-derived) Phase 0's T0.3
pose convention (`look_at_view_matrix`/`intrinsics_matrix` from
`yogesh_dev/phase0/pose_convention.py`) and matched the exact top-level
field set (`camera_model`, `width`, `height`, `fl_x`, `fl_y`, `cx`, `cy`,
`frames[].transform_matrix`) that `apple_tree_gaussian_splatting.py`
(`git show apple-tree-cameras:apple_tree_gaussian_splatting.py`) already
consumes, so that pipeline should still run unmodified against this output.
`transform_matrix` = camera-to-world = `inv(world_to_camera_matrix)`, same
as that script. Extended (not replaced) with `hfov_deg`, a `pose_convention`
provenance note, and per-frame `camera_label`/`plant_id`/
`world_to_camera_matrix`/`depth_path`/`semantic_path`/`instance_path` so one
JSON ties every T1.2-T1.4 artifact for a view together.

Real numbers: HFOV 57.822 deg (matches Phase 0's measurement exactly, same
45 deg VFOV / 640x480 rig), `fl_x=fl_y=579.41`, `cx=320.0`, `cy=240.0`,
9 frames (3 trees x 3 rig cams), splits assigned `i%8==0 -> test` (same
`TEST_EVERY` semantics as the existing gsplat script -- note this is the
**same known-flawed** train/test split the task doc flags for a later fix
under T6.1; not fixed here since T6.1 is out of Phase 1's scope, but worth
noting it was carried forward rather than silently perpetuated without
comment).

**Cross-artifact integration check** (not requested by the task doc, done
as an extra correctness check since T1.2/T1.3/T1.5 all needed to agree with
each other): for every (fruit, view) pair where that fruit was visible in
that view's instance map (>=5 pixels), projected the fruit's T1.2 centroid
through `K @ [R|t]` using T1.5's exact `world_to_camera_matrix`, and compared
against the *measured* pixel centroid of that fruit's mask in the T1.3
instance map. 219 (fruit, view) pairs checked on one real run:
```
mean px err:   1.41 px
median px err: 0.98 px
90th pct:      2.75 px
max px err:    5.54 px
```
Slightly higher than T0.3's pure-point-target test (0.71 px mean) -- expected,
since real fruit are volumetric and partially self-/mutually-occluded (the
*visible*-pixel centroid of a partly-occluded apple isn't exactly its full
3D centroid), not a sign of a convention error. This confirms T1.2's
centroids, T1.3's instance maps, and T1.5's intrinsics/extrinsics are all
mutually consistent on a real render, not just individually plausible.

## T1.6 -- RGB-D noise model

`phase1/noise_model.py`. Two effects, both toggleable via `enable=False`
(true no-op, returns an unmodified copy):

1. **Range-dependent noise**: additive Gaussian, `sigma(z) = 0.0015 * z^2`
   (loosely modeled on stereo-depth-sensor behavior where noise grows with
   the square of range, e.g. the RealSense D435 whitepaper's error-vs-range
   curve). At the rig's typical 4-5 m range this is ~3-4 cm std.
2. **Depth-edge mixed pixels**: at real depth discontinuities, each edge
   pixel is pulled partway (random fraction, capped at 35%) toward whichever
   of its 8 neighbors is the actual discontinuity partner (largest depth
   difference) -- approximating a stereo match that partially interpolated
   between two surfaces straddling an edge, without ever landing past the
   far surface. Sky/no-hit neighbors are excluded from consideration so
   real geometry never gets mixed toward the -1.0 sentinel.

**Threshold tuning was data-driven, not guessed**, and is worth recording
because the first attempt was wrong: measured the actual pixel-to-pixel
depth-gradient distribution on a real rendered view of this scene before
picking `edge_threshold_m`. A naive RealSense-like threshold (~0.03 m)
flags **37%** of all foreground pixels as "edges" here (median gradient
already 0.011 m, 90th-percentile gradient 0.74 m) -- this is a dense,
cluttered canopy where thin leaves at very different depths sit
immediately next to each other in almost every frame region, so a small
absolute threshold stops being a sparse "edge artifact" and starts
corrupting most of the image (first attempt: mean abs diff 22.9 cm, RMSE
70 cm, max diff 4.4 m -- an obviously-too-destructive result, caught by
actually running the numbers rather than assuming the model was reasonable).
Raised to 0.15 m and capped the mix fraction at 35%; re-measured:

```
view=tree0_above:  mean_abs_diff=4.3 cm, rmse=7.0 cm, max_abs_diff=58 cm, n_valid=55200
view=tree0_level:  mean_abs_diff=4.2 cm, rmse=7.0 cm, max_abs_diff=64 cm, n_valid=58603
view=tree0_below:  mean_abs_diff=4.1 cm, rmse=6.6 cm, max_abs_diff=59 cm, n_valid=53460
```
~78% of valid pixels change by >1cm, ~97-98% change by >1mm (the range
noise alone touches nearly every valid pixel by definition; the edge effect
is the source of the larger, spatially-concentrated jumps). This is now a
plausible, quantified, and reproducible (seeded) before/after -- not a
guess -- though it remains a documented model, not a calibrated match to
any specific real sensor.

## Files produced (all under `yogesh_dev/`)

- `phase0/canopy.py`, `radiation_setup.py`, `radiation_cameras.py`,
  `pose_convention.py` -- verbatim copies of Phase 0's dependency modules
  (see "Environment / worktree setup" above for why they had to be copied
  rather than imported from the other worktree/branch)
- `phase1/ground_truth.py` -- T1.1, T1.2
- `phase1/label_maps.py` -- T1.3
- `phase1/depth_export.py` -- T1.4
- `phase1/transforms_export.py` -- T1.5
- `phase1/noise_model.py` -- T1.6
- `phase1/run_phase1.py` -- end-to-end driver, writes everything under `phase1/output/`
- `phase1/output/fruit_ground_truth.json` -- T1.2
- `phase1/output/rgb/*.jpeg` -- RGB renders (Phase 0's `writeCameraImage`, unchanged)
- `phase1/output/labels/*_{semantic,instance}.{npy,png}` -- T1.3
- `phase1/output/depth/*.exr` -- T1.4
- `phase1/output/transforms.json` -- T1.5
- `phase1/output/noise_model_demo/*_depth_{clean,noisy}.npy` -- T1.6 before/after arrays
- `phase1/output/phase1_run_report.json` -- every number quoted above, machine-readable
- `PHASE1_LOG.md` -- this file
- `PHASE1_STATUS.md` -- final status

## Known, pre-existing, NOT fixed in Phase 1 (out of scope, documented instead)

- **Photometric saturation artifact** (Phase 0 T0.1 finding): ~15-20% of
  foliage/fruit RGB pixels still render solid white in `output/rgb/*.jpeg`
  regardless of flux. Visibly present in this run's renders too (e.g.
  `output/rgb/above_tree1_above.jpeg`). Does not affect any of T1.2-T1.5's
  ground truth (confirmed again here: the semantic/instance maps are
  pixel-clean silhouettes even where the RGB is blown out, since they come
  from the separate ray-hit-topology pass).
- **`Visualizer.getDepthMap()`** is still broken upstream (Phase 0 T0.7);
  not touched here, not relevant since T1.4 uses the EXR writer path
  specifically to avoid it.
- **Train/test split** (`i % 8 == 0`) is the same scheme
  `apple_tree_gaussian_splatting.py` already used, flagged by the task doc
  itself for a proper fix under T6.1 -- carried forward unchanged in
  `transforms.json`, not silently perpetuated without a note (this note).

## How to re-run everything

```
cd /home/yogesh/PyHelios   # or wherever this yogesh_dev/ lands
PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase1.run_phase1
```
No `xvfb-run` needed -- Phase 1 only uses `RadiationModel`, not `Visualizer`.
Requires `imageio` and `OpenEXR` in the `helios` env (see "Environment /
worktree setup" above for the exact install commands if missing).
