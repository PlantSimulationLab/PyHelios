# Phase 7 log — Foundation model diagnostics (D1-D6)

Working directory for this run: isolated worktree
`.claude/worktrees/phase7-diagnostics` (branch `worktree-phase7-diagnostics`,
reset onto `apple-tree-cameras` HEAD `4c655c8` so Phase 0-4's committed
`yogesh_dev/` deliverables are present). All work confined to
`yogesh_dev/phase7/`.

## Environment check (done first, not assumed)

`/home/yogesh/anaconda3/envs/helios/bin/python` package inventory:
- Present: `numpy` 2.5.1, `pillow` 12.3.0, `OpenEXR` 3.4.13, `ImageIO` 2.37.4,
  `PyYAML`, `PuLP` (from Phase 5), `pyhelios3d` (editable, this repo).
- **Absent**: `torch`, `scipy`, `opencv (cv2)`, `scikit-learn`, `open3d`,
  `trimesh`, `pycolmap`. No foundation-model packages installed or
  importable: `mapanything`, `vggt`, `pi3`/`pi-cubed`, `depth_anything`
  (DA3), `promptda`. None of these are on the Python path and none were
  pip-installed for this task.
- Disk: `df -h /` shows 2.7T free of 3.0T (6% used) — plenty of headroom.
  Network reachable (`pip index versions scipy` succeeded, scipy 1.18.0
  available, ~30MB wheel).
- **Decision**: did NOT install scipy/opencv/sklearn/torch or any
  foundation-model package. None of T7.2/T7.3/T7.6's classical/proxy
  math actually requires them (linear algebra via `numpy.linalg` covers
  triangulation, 8-point F/E-matrix estimation, SVD-based Umeyama
  alignment — all implemented by hand in `mv_geometry.py`, no external CV
  library). Multi-GB pretrained foundation-model checkpoints were never
  attempted: not practical/necessary given the task's explicit escape
  hatch to a documented proxy, and the "prefer lightweight over multi-GB
  checkpoints" guidance in the task brief. This mirrors Phase 5's `pulp`
  precedent for scoped, justified installs — here the conclusion is the
  opposite (no install needed at all).
- **Consequence for T7.2/T7.3**: "anchor" is a hand-rolled classical
  multi-view-geometry pipeline (linear DLT triangulation, 8-point
  fundamental/essential matrix, Umeyama similarity alignment, canonical
  projective reconstruction from F), NOT MapAnything/DA3/pi-cubed/VGGT.
  This is a proxy for the named foundation models, documented as such
  throughout — never blurred with "ran the real model."

## Worktree native-library setup (not code, but required to run anything)

The worktree's `pyhelios_build/build/` and `helios-core/` were empty
(submodule not checked out, native lib not built in this isolated
worktree). Symlinked (read-only, nothing written into the main checkout):
- `pyhelios_build/build/lib` -> `/home/yogesh/PyHelios/pyhelios_build/build/lib`
- `pyhelios_build/build/plugins` -> `/home/yogesh/PyHelios/pyhelios_build/build/plugins`
- `helios-core` -> `/home/yogesh/PyHelios/helios-core`

Verified: `Context`/`PlantArchitecture`/`RadiationModel` import and run;
single apple tree build ~0.08s (7837 primitives, `age_days=365`), single
camera render (640x480, AA=2) ~0.04-0.05s after warmup. This means large
view sweeps (dozens to hundreds of renders) are cheap here — not a
bottleneck for this phase's sweeps.

## Design decisions carried from Phase 0/1 (reused, not re-derived)

- Pose convention: `yogesh_dev/phase0/pose_convention.py`
  (`look_at_view_matrix`, `intrinsics_matrix`) — empirically validated
  sub-pixel accurate in T0.3. Reused directly for T7.1's WAI writer.
- Projection/unprojection for depth-based work: reused
  `yogesh_dev/phase4/sensor_model.py` (independently calibrated in Phase 4,
  <6cm mean error self-test, consistent convention with pose_convention.py
  — right/forward same, only up-vs-down-vector naming differs, both are
  the OpenCV X-right/Y-down/Z-forward convention under world_up=+Z).
- Depth EXR convention: PLANE depth (not Euclidean range), sky sentinel
  exactly -1.0 (`depth_export.py`, `sensor_model.py` agree).
- Branch/thin-structure ground truth: reused
  `yogesh_dev/phase4/gen_dataset.py:extract_branch_segments` (real Tube
  node positions + radii off `shoot`/`peduncle` objects; `petiole` is
  Cone-typed, excluded) and `yogesh_dev/phase4/voxel_sweep.py`'s
  `DIAMETER_CLASSES`/`classify_diameter` for T7.5.
- Depth fusion: reused `yogesh_dev/phase4/occupancy_map.py`
  (`make_grid`/`integrate_view`, a real log-odds volumetric fusion using
  exact poses + real depth) as the "classical MVS/TSDF fusion" baseline
  for T7.6, rather than reimplementing TSDF from scratch — it already IS
  a real, validated, exact-pose depth-fusion system.

## T7.1 -- WAI dataset writer (`wai_writer.py`, `run_t71_wai_writer.py`)

Looked up the real WAI spec (facebookresearch/map-anything,
`data_processing/README.md`, via WebSearch/WebFetch) rather than guessing:
`<dataset>/<scene>/scene_meta.json` + `images/`/`depth/`/`masks/`, with
`scene_meta.json` root fields (`scene_name`, `dataset_name`, `version`,
`camera_model`, `camera_convention: "opencv"`, `fl_x/fl_y/cx/cy/w/h`) and a
`frames[]` list (`frame_name`, `file_path`, `transform_matrix` = 4x4
flattened camera-to-world in OpenCV convention). Implemented faithfully in
`write_wai_scene`, reusing Phase 0's validated `look_at_view_matrix`/
`intrinsics_matrix` directly (already OpenCV convention, no re-derivation).
One writer, reused by T7.6 too (not a one-off demo). Real run: 1 apple
tree (age 720d, real fruit present), 16-view real 360deg orbit, RGB+EXR
depth+semantic-mask written for real -- `output/wai_dataset/
helios_apple_tree/tree0_orbit16/` (16 frames, verified on disk).

## T7.2 (D1) -- pose-conditioning ablation (`pose_conditioning_ablation.py`)

PROXY, not MapAnything/DA3/pi-cubed/VGGT (see Environment check above).
Real classical multi-view geometry (`mv_geometry.py`: normalized 8-point
F/E, DLT triangulation, Umeyama/affine alignment -- unit-tested against
synthetic ground truth first: exact triangulation gave ~3e-15 RMSE,
essential-matrix recon after similarity align gave exact shape recovery
with a genuine unrecoverable scale factor, uncalibrated F recon after
affine align showed real nonzero residual -- confirms the math is
correct before trusting it on real data). Real 3D landmarks = branch
tube-segment midpoints + real fruit centroids from one real Helios apple
tree (age 720d). 8 real camera poses over a 180deg arc from Phase 0's
rig-sizing logic. Found and fixed a real bug: condition D's depth
back-projection initially had huge error (219mm) because it didn't check
for occlusion (a leaf in front of the intended branch point) -- added a
depth-consistency gate (compare rendered depth to the landmark's own
analytic depth) and it dropped to a physically sensible range.

Representative real run: A(images only)=74mm, B(+intrinsics)=48mm,
C(+intrinsics+extrinsics)=4.6mm, D(+depth, single-view, occlusion-gated)
=32mm. `hypothesis_A_B_C_pose_conditioning_monotonic=True` every run;
`hypothesis_D_depth_beats_unconditioned=True` (D beats A by >2x). D vs C
NOT compared head-to-head as pass/fail (D is single-view, C is N=8-view
triangulation -- documented explicitly as not apples-to-apples).

## T7.3 (D2) -- baseline-angle sweep (`baseline_angle_sweep.py`) -- core figure

Same proxy machinery, real 8-view rig at 23 real arc widths (5deg-360deg).
POSED = DLT over all 8 real-posed views; UNPOSED = essential-matrix 2-view
(widest pair) + similarity align. Real, honest finding, NOT the clean
textbook story: UNPOSED is worse than POSED at every single arc width
(unposed_over_posed_ratio_by_arc > 1 throughout), but the naive "collapse
only when uncalibrated, none when posed" claim does NOT hold cleanly --
POSED also degrades substantially at small arc width here (~8-9x from
large to small arc, vs ~4-5x for UNPOSED), because plain DLT triangulation
has zero learned shape prior to fall back on at near-parallel rays: it's
pure epipolar geometry, so it inherits the textbook triangulation-
uncertainty-vs-baseline relationship regardless of pose being exact. This
is flagged explicitly in the report as a structural limitation of using
classical geometry (vs a real trained foundation model) as the "posed"
anchor -- the naive prediction may well hold for an actual foundation
model with learned priors; this proxy cannot test that part of the claim.
`unposed_beats_posed_hypothesis_supported` / `naive_no_collapse_when_
posed_supported` both reported per-run rather than one blurred verdict.

## T7.4 (D3) -- LAI sweep (`lai_sweep.py`)

Confirmed empirically (3 consecutive identical-parameter builds gave
57/94/66 shoot objects) that PlantArchitecture growth has NO exposed seed
-- it's genuinely stochastic. So "fixed branch skeleton" is only real if
leaves are thinned within ONE already-built tree (never rebuilt) --
implemented that way: one tree built once, `context.deleteObject` removes
real leaf compound objects only (never shoot/petiole/peduncle) across 10
nested keep-fractions from 1.0 (full canopy) to 0.0 (bare skeleton),
`radiation.updateGeometry()` re-called after each deletion (a REAL
geometry change, unlike T0.4's camera-move case). Occlusion checked via
real semantic-label + real depth-consistency at each of 8 fixed views per
LAI level. "Attention effective rank" explicitly SKIPPED (`null` in every
result), not approximated -- no foundation-model attention runs here to
take a rank of.

Real result, monotonic and clean: recall(>=1 unoccluded view) rises from
~0.81-0.85 at full canopy to ~0.94-0.96 at bare skeleton;
recall(>=2 views, reconstructable) similarly rises (~0.55-0.65 ->
~0.82-0.88). `hypothesis_more_leaves_occlude_branches_supported=True`
every run. branch_geometry_rmse among successfully-reconstructed points
stayed roughly flat (~8-13mm) across LAI -- occlusion mainly gates WHICH
points are reconstructable, not the triangulation quality of the ones
that survive.

## T7.6 (D5) -- classical baseline (`classical_baseline.py`)

Reused Phase 4's real log-odds volumetric depth-fusion
(`occupancy_map.py`/`sensor_model.py`, path-injected onto sys.path since
those modules use bare `import sensor_model`) against Phase 7's OWN real
data: 1 tree, 42 real views (3 elevation rings x 14 azimuths), real RGB+
EXR depth persisted as a real WAI scene (`output/wai_dataset/
helios_apple_tree/tree_t76_mvs_rig/`, reusing T7.1's writer). Fused at
2cm (matches the literature's common 5cm-ish benchmark resolution,
rounded finer) and 5mm. No opencv/pycolmap -- true patch-match dense
stereo was out of scope per the task's own "simple depth fusion is fine"
guidance; exact poses were used throughout (no pose estimation in this
step at all). Real result: ~54% of real branch-segment landmarks and
100% of real fruit landmarks land on an occupied fine-grid voxel.
Initially saved dense boolean grids via `np.savez` (73MB for the fine
grid, >99.96% zeros) -- switched to `np.savez_compressed` (136KB) once
noticed, since that's real repo bloat for no reason.

## T7.5 (D4) -- thin-structure recall by diameter class (`thin_structure_recall.py`)

Reused Phase 4's `DIAMETER_CLASSES`/`classify_diameter` AND its exact
one-voxel/two-voxel geometric-detectability criterion verbatim (path-
injected import from `phase4/voxel_sweep.py`), applied at T7.6's own 2cm/
5mm resolutions -- this is the THEORETICAL upper bound (ignores occlusion/
coverage entirely). Added a second, NEW empirical number: real recall
against T7.6's actual fused voxel grid (segment-length sampling +
index-space neighborhood lookup, not a brute-force O(segments x voxels)
distance matrix, which would have been multi-GB at this resolution).
Found and fixed a real bug twice: first pass used a physically-scaled
tolerance (radius + voxel_size) that ballooned at 2cm resolution into a
~10cm search cube, so it just detected "reconstructed matter somewhere
nearby" (100% recall for every class, including physically-undetectable
<5mm) rather than "was this specific structure resolved" -- fixed to a
fixed 1-voxel neighborhood window, which then showed real class-dependent
differentiation (0.4-0.88 range at 5mm resolution). Real empirical
recall below 10mm across runs: 65-76%, consistently BEATS the "<55%
recall below 10mm" benchmark the task doc calls out to beat.

## T7.7 (D6) -- metric-scale integrity (`metric_scale_integrity.py`)

Ground truth computed directly from T7.6's SAME tree/Context (persisted
by T7.6 to `t76_ground_truth_scale.json`/`t76_branch_segments.json` --
reused, never rebuilt, for the same stochastic-growth reason as T7.4):
real leaf area (`getPrimitiveArea` sum), real domain bounding-box volume,
real mean internode length (real shoot-segment node spacing), real fruit
diameters. Reconstructed side computed from T7.6's actual fine occupied-
voxel grid: canopy volume = occupied-voxel-count x voxel^3, fruit diameter
= 2x max distance of nearby occupied voxels from the KNOWN fruit center
(radius-relative search window, not diameter-relative -- first attempt
used too generous a window and 3x too generous distance metric,
pairwise-among-neighbors instead of from-known-center, giving 490% mean
error from neighboring branch/leaf voxels being swept in; fixed to a
tight 1.3x-radius window + from-center distance, giving ~22-24% mean
error, a believable number for a sparse multi-view depth-fusion
reconstruction of a curved surface). Internode length reconstructed by
snapping each real segment endpoint to its nearest actually-occupied
voxel (excluding segments where snapping fails at either end) --
real error 4-11% across runs. Leaf area explicitly NOT cross-checked
(no per-primitive surface classification recoverable from a sparse
occupancy grid -- reported ground-truth-only). Canopy volume relative
error is large (~-99.96%) but flagged explicitly as a DEFINITIONAL
mismatch (filled-surface-voxel volume vs. whole-tree bounding-box
volume), not reconstruction error -- these are genuinely different
quantities, stated as such rather than left to look like a failure.
Explicitly cross-references T7.2's finding (scale is only correct under
known-extrinsics conditions C/D; T7.6 used exact poses throughout, so
this is squarely in the regime where scale integrity is expected to hold,
and mostly does for internode length and fruit diameter).

## Full pipeline

`run_phase7.py` runs T7.1 -> T7.2 -> T7.3 -> T7.4 -> T7.6 -> T7.5 -> T7.7
in dependency order (T7.5/T7.7 consume T7.6's persisted same-tree
outputs). Full run: ~20-26s wall clock, real Helios renders throughout.
Total `yogesh_dev/phase7/output/` size: ~29MB (mostly two real WAI scenes,
58 real rendered views total with RGB+depth).

## Overall proxy-vs-real accounting (explicit, per the task's
"be explicit per-subtask" instruction)

| Task | Real Helios data/geometry | Anchor / method | Real vs proxy |
|------|---------------------------|------------------|----------------|
| T7.1 | real render (1 tree, 16 views) | WAI format writer | 100% real, no anchor needed |
| T7.2 (D1) | real tree, real landmarks, real poses | classical multi-view geometry (`mv_geometry.py`) | PROXY for MapAnything/DA3/pi3/VGGT -- none installed |
| T7.3 (D2) | real rig-derived poses, real landmarks | same classical geometry | PROXY, same caveat |
| T7.4 (D3) | real tree, real leaf deletion, real render+depth+labels | classical DLT triangulation for the reconstruction sub-metric; occlusion/recall fully real | attention-effective-rank SKIPPED (not approximated) |
| T7.5 (D4) | real branch segments, real reconstruction (from T7.6) | Phase 4's real criterion (theoretical) + new empirical check (real) | 100% real, no foundation model involved by design |
| T7.6 (D5) | real 42-view render, real depth, real exact poses | Phase 4's real log-odds volumetric fusion | 100% real classical baseline, explicitly the "honest classical" arm |
| T7.7 (D6) | real Context geometry + real T7.6 reconstruction | direct measurement + voxel-grid cross-check | 100% real, no anchor needed |
