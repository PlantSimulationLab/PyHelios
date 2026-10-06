# Phase 2 log — Visibility ground truth (AVUB / NVE)

Implements T2.1-T2.6 from `helios_setup_tasks.md`, built on top of Phase 0's
validated radiation-camera rig/pose convention and Phase 1's ground-truth
export machinery (`yogesh_dev/phase1/ground_truth.py`,
`yogesh_dev/phase0/radiation_cameras.py`, imported directly, not
duplicated). Run end-to-end against the real pyhelios `RadiationModel` +
`PlantArchitecture` on the real 3-apple-tree scene (RTX 5090, OptiX 8.1
backend) — not simulated, not estimated.

## Worktree setup (operational note, not part of T2.1-T2.6)

This worktree, like `worktree-phase1-groundtruth` before it, branched from
`origin/master`, not `apple-tree-cameras` — so `yogesh_dev/` didn't exist
here until `git merge worktree-phase1-groundtruth` pulled in Phase 0+1's
code and `phase1/output/` artifacts. Two more gaps had to be closed before
`pyhelios` would import at all, both **local, gitignored build artifacts,
not source**, and fixed with symlinks into the main checkout rather than by
touching anything tracked:

- `pyhelios_build/build/lib` (the compiled `libhelios.so`/OptiX bindings)
  did not exist in this worktree (it's `.gitignore`d, built once in the
  main checkout at `/home/yogesh/PyHelios`). Symlinked
  `pyhelios_build/build/lib -> /home/yogesh/PyHelios/pyhelios_build/build/lib`.
- `helios-core/` (the git submodule) was not checked out in this worktree.
  Symlinked `helios-core -> /home/yogesh/PyHelios/helios-core`.
- `pyhelios_build/build/plugins` (per-plugin asset directories, e.g.
  `plantarchitecture`'s model library) is also a build artifact. Symlinked
  the same way.

Verified this doesn't silently pull in someone else's in-progress edits: all
three targets are build outputs / a submodule checkout, not tracked
sources, and are read-only inputs to this worktree, never written to here.

## Fresh scene, not Phase 1's — and why the fruit count differs from 73

Phase 1's `fruit_ground_truth.json` (73 fruit) lives in a `Context` that no
longer exists — primitive UUIDs are only valid within the process that
created them, so they cannot be reloaded from JSON into a new process. Phase
2 therefore builds its own fresh 3-tree scene via
`yogesh_dev.phase0.canopy.build_three_tree_scene` and its own
`fruit_ground_truth.json`-equivalent via
`yogesh_dev.phase1.ground_truth.export_fruit_ground_truth` (reused directly,
not reimplemented) inside its own process, in `run_phase2.py`.

This surfaced something worth flagging: **apple tree growth in this model is
stochastic and neither Phase 0 nor Phase 1 seeded it.** Verified empirically
before writing any Phase 2 code — building the same 3-tree scene twice in
one process (no seed) gave 97 fruit in one build and 72 in another, with
different centroids. So Phase 1's "73" and Phase 2's fruit count are
different random realizations of the same generative process, not the same
data. Phase 2 calls `context.seedRandomGenerator(20260729)` once at the top
of `run_phase2.py` so its OWN results are at least reproducible run-to-run;
this run produced **83 real fruit** across 3 trees (17,098 fruit-surface
primitives). This is real data from the real apple-architecture model, just
a different (seeded, reproducible) draw than Phase 1's — not synthetic
fruit, and the difference from "73" is called out explicitly rather than
silently treated as the same dataset.

## T2.1 — per-fruit visible-fraction vis_i(v)

**Better than what the task brief anticipated, and here's why it's still
real (not fabricated) occlusion resolution.** `CollisionDetection` isn't
exposed in PyHelios, so the brief expected falling back to
`getObjectDataLabelMap(cam, "fruitID")` (object-level) and accepting that
sub-primitive occlusion can't be resolved. Turns out it can, without
`CollisionDetection`: every render already computes, per pixel, which single
primitive is the nearest ray-traced hit (`RadiationModel.writePrimitiveDataLabelMap`'s
own docstring: "writes the value of `primitive_data_label` on the primitive
SEEN at that pixel"). So instead of reading a per-fruit-*object* field, I
assigned every one of the 17,098 fruit-surface primitives its own globally
unique int id (`vis_primitive_id`, `yogesh_dev/phase2/visibility.py
assign_vis_primitive_ids`) and read *that* back per pose with
`getPrimitiveDataLabelMap`. Any primitive whose id shows up in >=1 pixel was
the genuine nearest-hit ray-traced result somewhere in frame — full
per-primitive resolution of `unoccluded ∧ in-frustum`, computed by Helios's
own OptiX ray tracer, exactly like the `fruitID` maps Phase 1 already
validated, just at finer granularity. `front-facing` comes for free too:
apple fruit primitives tile a closed outward-facing shell, so a ray's
nearest hit can only ever land on the near (outward) side — see
`visibility.py`'s module docstring for the full argument and the honestly-
stated limitations (sub-pixel partial occlusion, AA=1 in the dense sweep).

`vis_i(v) = sum(area of visible primitives) / fruit's total surface_area_m2`.
`w(theta, r) = 1` throughout (pure geometric visibility is the design doc's
primary metric; the observation-quality-weighted variant is out of scope
here).

**Cross-validation against the task doc's own suggested check** (raw
`getObjectDataLabelMap(cam, "fruitID")` pixel-count fractions), computed on
the real Phase-0/1-style 3-view rig (9 poses across 3 trees), over 241
(fruit, view) pairs with signal in either metric:

    Pearson r(vis_i(v) area-fraction, fruitID pixel-count fraction) = 0.9242

Strongly correlated, as the task doc predicted — no systematic disagreement
that would indicate a bug in either metric.

## T2.2 — accumulated visibility over a trial (union, not max)

`visibility.union_visible_ids` unions the per-pose visible-primitive-id sets
across a sequence — implemented once, reused for both the small 3-view demo
here and the large placeholder-reachable-set union in T2.4's AVUB
computation. Demonstrated on the real 3-camera-rig sequence (Phase 0/1's
above/level/below views) per tree:

    82 / 83 fruit had union coverage > max single-view coverage
    mean (union - max single view) = 0.0871 (8.7 percentage points)
    best example: fruit object 7006 (tree 2) -- per-view fractions
        [0.187, 0.220, 0.190], union = 0.411 (nearly double the best
        single view's 0.220)

(The 1 fruit without improvement was only ever visible from exactly one of
the 3 views, so union == that single view trivially — expected, not a bug.)

## T2.3 — PLACEHOLDER reachable view set V_reach

Phase 3 (`worktree-phase3-kinematics`) doesn't have a real roadmap yet, so
`yogesh_dev/phase2/reachable_poses.py` builds a documented
`placeholder_reachable_poses` / `placeholder_free_flying_poses` pair
instead — full detail, including the exact interface a real T3.4 roadmap
must satisfy to be substitutable here, is in that module's docstring. Short
version:

- **Reachable set**: dense grid over the 3 prismatic axes a rail-mounted arm
  would actually have (rail x, height z, in/out depth y), 6x6x3 = 108 poses
  per tree, always looking level into the canopy from the **front
  hemisphere only** (mirrors "arm can't fly around behind the row").
- **Free-flying set** (for AVUB^inf): full-sphere sampling (12 azimuths x 8
  elevations x 3 radii = 288 poses/tree), including the back/below/above of
  the tree a rail-mounted arm can never reach.

No collision checking, no joint limits, no execution-time weighting — all
explicitly need Phase 3 and are out of scope here. **These numbers will
move once Phase 3's real roadmap replaces this grid** — repeated as a
caveat directly in `avub.py` and in every summary dict T2.4 produces.

Render settings for the sweep (396 poses/tree x 3 trees = 1,188 poses,
batched 3-at-a-time onto reusable camera slots per the T0.4 pattern):
320x240 resolution, antialiasing_samples=1 (reduced from Phase 0/1's
640x480/AA=2 — sized via a timing test before committing to the full run:
~0.25 s/pose at these settings, ~0.38 s/pose at Phase 0/1's full settings;
at 1,188 poses the difference is the run taking ~5 min instead of ~7-8 min,
not the difference between feasible and infeasible, but chosen anyway to
keep the dense sweep clearly tractable per the T1.3 performance caveat about
`getPrimitiveDataLabelMap`'s text-parsing cost). Actual measured cost: 108
reachable poses in ~24 s/tree, 288 free-flying poses in ~63-65 s/tree,
total pipeline (build + T2.1/T2.2 demo + all 3 trees' sweeps + T2.4/T2.5) =
**271 s**.

## T2.4 — AVUB and AVUB^inf

Reuses T2.1/T2.2 machinery directly: `AVUB_i` = `fruit_visible_fraction` of
the UNION of visible-primitive-ids across all 108 reachable poses for that
fruit's tree; `AVUB_i^inf` = same, over the 288 free-flying poses.

    n_fruit = 83
    mean AVUB_i        = 0.4993
    mean AVUB_i^inf     = 0.9766
    ratio of means      = 0.5113
    mean per-fruit ratio = 0.5098
    n_fruit with AVUB_i^inf == 0: 0  (every fruit is visible from SOME
                                       free-flying pose in this scene)
    range of AVUB_i: [0.150, 0.622], median 0.523
    range of AVUB_i^inf: [0.691, 1.000]

**CAVEAT (placeholder, not a real hardware-capability number):** this
`AVUB / AVUB^inf ~ 0.51` says the placeholder front-hemisphere-only rail grid
captures roughly half the surface a free-flying camera could see — which is
the *structurally correct direction* (front-hemisphere-only should lose real
visibility versus full-sphere), but the actual magnitude is a property of
this placeholder's grid density/envelope, not of any real 5-DOF arm design.
Do not cite "0.51" as a real workspace-design metric until Phase 3's roadmap
replaces `reachable_poses.py`.

## T2.5 — fruit achievability classes

`gamma_size = 0.30` (PLACEHOLDER — no Tier-1 sizing-accuracy calibration
exists yet to derive a real value from; documented as a placeholder in
`achievability.py`, not presented as calibrated). Graspability approximated
via a fruit-vs-fruit approach-cone check (15 deg half-angle, 0.15 m depth,
axis = direction from fruit centroid toward its single best-visibility
reachable pose) — explicitly NOT a real approach planner (ignores leaves,
branches, trellis wire, gripper geometry); documented as an approximation in
`achievability.py`.

    observable (AVUB_i > 0):        83 / 83  (100%)
    sizeable  (AVUB_i > 0.30):      79 / 83 observable (95.2%)
    graspable (cone clear):          82 / 83 observable (98.8%)

All 83 fruit in this scene are "observable" from the placeholder reachable
set — plausible given the trees are relatively young/small (720-day-old
single apple instances, not a dense mature orchard row) and the reachable
grid already covers a wide rail/height/depth envelope per tree; a denser
canopy or a tighter real Phase-3 workspace envelope could well produce
non-observable fruit. Per the design doc, sizeable/graspable fractions are
reported against the **observable** denominator, not the raw total (see
`achievability.summarize_classes`).

## T2.6 — occlusion-regulation module validation: blocked, skipped honestly

Before attempting anything: does an occlusion-regulation module (the WTFRC
proposal's leaf add/remove control targeting per-fruit occlusion) exist
anywhere in this repo? Searched every commit on every branch
(`git grep -niE "occlusion.regulat|occlusion.control" $(git rev-list --all) --`,
implemented reproducibly in `yogesh_dev/phase2/t26_check.py`). Result: **12
hits total, 0 in code** — every hit is prose in `active_vision_design.md` or
`helios_setup_tasks.md` *describing* the external WTFRC proposal's module,
never an implementation. No leaf add/remove control, no per-fruit occlusion
target, no calibration sweep exists as code anywhere in this repository's
history.

**T2.6 is genuinely blocked on a module that has never been built here.**
Per the task brief, no fake module was written to force a "done" — this is
reported as a legitimate partial outcome, not blended into the overall
Phase 2 status (see `PHASE2_STATUS.md`).

## Files

- `yogesh_dev/phase2/visibility.py` — T2.1 + T2.2 core (per-primitive
  visible-id assignment/lookup, area-weighted fraction, union accumulation,
  batched pose rendering).
- `yogesh_dev/phase2/reachable_poses.py` — T2.3 placeholder reachable +
  free-flying pose generation.
- `yogesh_dev/phase2/avub.py` — T2.4 AVUB / AVUB^inf / ratio computation.
- `yogesh_dev/phase2/achievability.py` — T2.5 observable/sizeable/graspable
  classification.
- `yogesh_dev/phase2/t26_check.py` — T2.6 repo-wide search + honest
  blocked/skip determination.
- `yogesh_dev/phase2/run_phase2.py` — end-to-end driver.
- `yogesh_dev/phase2/output/` — `phase2_fruit_ground_truth.json` (this run's
  83 fruit records), `phase2_run_report.json` (full report, all numbers
  above), `per_fruit_avub.json` (per-fruit AVUB_i/AVUB_i^inf/ratio +
  achievability classes), `per_fruit_union_demo.json` (T2.2 per-fruit
  detail).

Nothing outside `yogesh_dev/` was modified. No upstream bugs were silently
worked around without comment — the primitive-level occlusion-resolution
approach (an improvement over the task brief's anticipated fallback), the
unseeded-stochastic-growth finding, and T2.6's genuine blocker are all
documented here with the evidence, not asserted.
