# Phase 4 Log — Map and Planner

Branch: `worktree-phase4-map-planner`. Scope: `helios_setup_tasks.md` Phase 4
(T4.1-T4.10) only. Hard constraint: everything lives under `yogesh_dev/`.

## Starting state (session resume)

This worktree was resumed from an earlier session's partial work:
`yogesh_dev/phase4/gen_dataset.py`, `kinematics.py`, `motion_time.py`,
`roadmap.py` (the latter three vendored verbatim from
`worktree-phase3-kinematics`, documented in their own docstrings), plus a
partially-written `data/` dir (only `fruit_ground_truth.json` and
`vis_primitive_index.json` had been written; `depth/` and `labels/` were
empty — the generator had crashed before finishing). No `PHASE4_LOG.md` or
`PHASE4_STATUS.md` existed yet, so this is effectively a continuation with a
mostly-untested generator script.

## Bug #1: cross-worktree PYTHONPATH trick was silently resolving to the WRONG pyhelios

`gen_dataset.py`'s own docstring documents running it with
`PYTHONPATH=<phase2-avub worktree>` so it picks up phase2-avub's *built*
native library (this worktree has no `libhelios.so` of its own — no build
was ever run here). Testing confirmed phase2-avub's build is real and
working (`Context()` construction succeeds there). But invoking the script
with cwd = this worktree's root still resolved `import pyhelios` to *this*
worktree's own (unbuilt) `pyhelios/` package, because `sys.path[0]` is `''`
(cwd) for `-c`/interactive, or the *script's own directory* is not the repo
root but `''`/cwd still leaks in via other means in practice — empirically,
running from this worktree's root always resolved to the local unbuilt
package regardless of PYTHONPATH order, and only running from a neutral cwd
outside any `pyhelios/`-containing directory made `PYTHONPATH` win. Fixed by
invoking from `$CLAUDE_JOB_DIR/tmp` instead of the worktree root:

```
cd $CLAUDE_JOB_DIR/tmp && PYTHONPATH=<phase2-avub worktree> \
    /home/yogesh/anaconda3/envs/helios/bin/python <phase4 worktree>/yogesh_dev/phase4/gen_dataset.py
```

Nothing in phase2-avub is read for Python source (its `pyhelios/` is
git-identical to this worktree's own, both are `apple-tree-cameras` plus
each phase's untouched `yogesh_dev/`) — only its compiled `.so` is linked at
import time. Nothing there is written to.

## Bug #2: real native-library SEGFAULT on `getTubeObjectNodes`/`getTubeObjectNodeRadii` for petiole objects

`extract_branch_segments` (T4.2's real branch/twig ground truth) originally
wrapped the tube-node accessor calls in `try/except Exception` on the
assumption that a non-Tube compound object would raise a catchable
exception. It does not — it crashes the whole process (confirmed via
isolated probe script: build tree, iterate `shoot` objects first — 5/5
succeed — then start on `petiole` objects, and the process dumps core on the
very first one, no Python traceback at all).

Root-caused by isolating further with `context.getObjectType(oid)`
(`helios::ObjectType` enum: 0=tile, 1=sphere, 2=tube, 3=box, 4=disk,
5=polymesh, 6=cone — documented in `Context.py`'s docstring). Empirically,
for this seeded apple tree (seed 20260729, age 720 days):

| label | n_objects | ObjectType | tube-accessor safe? |
|---|---|---|---|
| shoot | 61 | 2 (tube) | yes |
| petiole | 963 | 6 (cone) | **NO — segfaults** |
| peduncle | 27 | 2 (tube) | yes |

Fix: guard every tube-accessor call with `context.getObjectType(oid) == 2`
*before* calling, never rely on try/except for this. This is a real,
reproducible native-library bug/limitation (calling a Tube-object accessor
on a Cone object corrupts memory rather than raising), not a modeling
choice — documented here so nobody re-introduces the try/except version.
Petioles are therefore excluded from `branch_segments_gt.json`'s tube
geometry (they're geometrically cones in this plant model, not the
tube/twig geometry T4.2's diameter-class recall sweep is measuring) — this
is a real, verified finding, not a gap-filling assumption.

## Real dataset actually generated (`gen_dataset.py`, seed=20260729, tree age=720 days)

- 1 seeded apple tree at origin, 41351 primitives.
- Semantic class counts: fruit=5562, leaf=10593, shoot=19040, petiole=5778,
  peduncle=378.
- 27 fruit objects (real `fruitID`/centroid/bbox/diameter/surface-area each).
- 1336 real tube segments (61 shoot objects + 27 peduncle objects, all
  Tube-typed; petiole objects excluded, see Bug #2) — this is T4.2's real
  branch/twig ground-truth geometry (node positions + radii, i.e. real
  per-segment diameter).
- 3 arms (`arm_low`/`arm_mid`/`arm_high`, single-tree-scaled from Phase 3's
  kinematics, non-overlapping z-bands), each with its own T3.4-style
  placeholder-collision roadmap: arm_low 549/576 reachable nodes (3718
  edges), arm_mid 468/576 (3228 edges), arm_high 468/576 (3230 edges). Build
  time <15ms per arm. **Placeholder-collision caveat propagates unchanged
  from Phase 3**: a node is only rejected if the camera's optical center
  falls inside the fruit-bearing AABB — no real ray-traced/swept collision
  check (T0.6 `CollisionDetection` still not exposed in PyHelios).
- 42 real rendered views (14 stride-sampled reachable nodes per arm x 3
  arms), real RGB radiation + depth EXR + semantic/instance/vis-primitive-id
  label maps via the real T0.1-T0.4 recipe (RadiationModel, OptiX backend).
  Render time 3.95s total (0.094s/view). 23/42 views have non-empty
  semantic label content (the rest point the camera at empty space/sky —
  expected for a rig covering the full reachable envelope, not curated to
  always frame the canopy).

## Camera projection convention — calibrated empirically, not assumed

Phase 4's planners/mapping code all need to turn a rendered view's pixel
grid + depth into world-frame rays/points, but PyHelios's `RadiationCamera`
pixel convention (row-major direction, right-handedness, HFOV/VFOV
resolution) is not documented anywhere Python-visible, and `helios-core` C++
source isn't checked out in this worktree (submodule never initialized
here) to read directly. Calibrated it the same way Phase 2 verified its own
assumptions: against real rendered data.

Method: took 8 real (view, fruit-instance) pairs with >=300 visible pixels
each (from the real `vis_primitive_id`/instance label maps), and for each of
the 8 sign/mode combinations `(sx, sy, depth_mode)` — column direction sign,
row direction sign, and whether the depth channel is Euclidean range or
forward-axis ("plane") depth — reconstructed each pixel's 3D world point via
unprojection and compared the reconstructed point cloud's centroid to the
fruit's independently-known true 3D centroid (`fruit_ground_truth.json`).

Result: `(sx=+1, sy=+1, mode=plane)` wins decisively — mean centroid error
3.69 cm (max 4.43 cm) across all 8 pairs, next-best combination 7.29 cm
mean. The residual ~3-4 cm is consistent with what's expected anyway (a
sphere's near-surface points reconstruct closer to the camera than the
sphere's *center*, by roughly the fruit radius), not calibration error.

Confirmed convention, used throughout Phase 4's code (`sensor_model.py`):
- world up = `(0,0,1)`; camera right `r = normalize(forward x world_up)`;
  camera up `u = r x forward`.
- pixel `(row, col)`, resolution `(W,H)`: `x_ndc = (col - W/2)/fl_x`,
  `y_ndc = (H/2 - row)/fl_y` (row 0 = top of array = "up" in world, matching
  standard image-row-major-top-down convention).
- `fl_x = 0.5*W/tan(HFOV/2)`, `fl_y = 0.5*H/tan(VFOV/2)` with `VFOV=45 deg`
  fixed (`gen_dataset.py`'s `build_camera_properties`); confirmed
  numerically `fl_x == fl_y` for this square-ish aspect (320x240 with 45deg
  VFOV auto-computing a matching HFOV).
- depth EXR value `d` at a pixel is **plane depth** (distance along the
  forward axis to the ray-primitive hit), NOT Euclidean range: world point
  `= eye + d*(x_ndc*r + y_ndc*u + forward)`.
- depth EXR sky/no-hit sentinel = exactly `-1.0` (same convention Phase 1
  found and documented).

This calibration underpins T4.1's beam sensor model, T4.3's semantic
fusion, T4.4's tracker projection, and T4.10's gimbal refinement — all
share `sensor_model.py` rather than re-deriving this per module.

## T4.1 — occupancy map (done)

`occupancy_map.py`. Scoping decision (build vs. nvblox/UFOMap/wavemap):
hand-rolled numpy log-odds grid — documented in the module docstring, same
build-vs-fake-integration reasoning Phase 2 used for `CollisionDetection`.
Real beam sensor model: per-pixel angular footprint (`1/fl_x`, `1/fl_y`
radians/pixel from real camera intrinsics) combined with range uncertainty
`sigma(d) = 0.0015*d^2` (same quadratic law Phase 1's RGB-D noise model
used) via a Gaussian-weighted occupied band +/- 2*sigma around the real
per-pixel plane-depth hit, widened laterally by the angular footprint;
free-space carved by along-ray samples short of the uncertain band.

Real run over the full 42-view dataset (`pixel_stride=2`, ~302k valid
depth pixels): coarse global grid at 2cm covers a (63,62,66)=257796-voxel
box around the fruit-bearing volume — 241689 unknown / 10597 free / 5510
occupied after integration. 23 fine (3mm) attention-region grids built from
real single-link clustering of the 27 fruit centroids (12cm merge radius);
most are small per-fruit boxes (~8800 voxels), one region absorbed a chain
of nearby fruit into a much larger box (271049 voxels) — a known artifact
of single-link/chaining clustering, not a bug (documented, not "fixed" by
switching clustering algorithms, since 1-2 chained clusters don't change
this phase's conclusions). Total integration time for all 42 views: 0.13s.

Real, honest limitation found: fine attention-region grids show `free: 0`
for every region. Root cause (verified, not a bug): free-space samples are
drawn along the whole camera-to-hit ray, and the camera is typically
15-100cm from a fruit while a fine region's box is only ~10-25cm across —
so almost none of the free-space sample points (concentrated at fractional
depths 0.05-0.95 of the way to the hit) land inside the small box near the
surface. A fine grid built this way mostly accumulates `occupied` or stays
`unknown`, essentially never `free`, unless the beam happens to graze
through the box before reaching its actual hit elsewhere. This is reported
as-is rather than papered over with a synthetic near-surface free-space
heuristic.

## T4.2 (E1) — voxel size sweep (done)

`voxel_sweep.py`. Ground truth: the real 1336 tube segments from
`branch_segments_gt.json` (real per-node diameters). Recall criterion
documented as an explicit modeling choice (not re-run through the render
pipeline, since the dataset has no per-segment pixel labels): a structure
of diameter D counts as "hit" at voxel size v if D>=v (one-voxel), and
"robustly resolved" if D>=2v.

Real numbers (diameter classes exactly per task doc: <5, 5-10, 10-20,
>20mm; real class populations: n=1336 total, 5-10mm=862 segments,
10-20mm=290, >20mm=157, <5mm=27 — all peduncle/shoot, no petiole per Bug
#2):

| voxel (m) | <5mm recall | 5-10mm recall | 10-20mm recall | >20mm recall |
|---|---|---|---|---|
| 0.05 (published-benchmark size) | 0.0 | 0.0 | 0.0 | 1.0 |
| 0.02 | 0.0 | 0.0 | 1.0 | 1.0 |
| 0.01 | 0.0 | 1.0 | 1.0 | 1.0 |
| 0.005 | 0.0 | 1.0 | 1.0 | 1.0 |
| 0.003 | 0.0 | 1.0 | 1.0 | 1.0 |
| 0.002 | 1.0 | 1.0 | 1.0 | 1.0 |

This is the task doc's central point made concrete with this tree's real
geometry: a 5cm voxel (the field's de facto benchmark resolution) recalls
*zero* twig/peduncle structure under 20mm — everything in this tree's real
branch network except the thickest scaffold wood is invisible at that
resolution.

Update-time sweep (single GLOBAL grid, all 42 real views, `pixel_stride=4`,
same scene AABB as T4.1's coarse grid):

| voxel (m) | n_voxels | update time (42 views) | ms/view |
|---|---|---|---|
| 0.05 | 17,550 | 0.022s | 0.53 |
| 0.02 | 257,796 | 0.022s | 0.53 |
| 0.01 | 2,062,368 | 0.065s | 1.55 |
| 0.005 | 16,305,211 | 0.691s | 16.44 |
| 0.003 | 75,255,333 | 3.497s | 83.25 |
| 0.002 | 253,772,288 | 11.766s | 280.15 |

~500x update-time blowup from 5cm to 2mm globally, tracking voxel count
(~1/v^3) almost exactly — this is the concrete justification for T4.1's
dual-resolution design (small local fine regions instead of one global
fine grid): recall needs <=3mm to see twigs, but a *global* 3mm grid costs
~27x the 1cm grid's update time for a scene this size, and would keep
growing catastrophically for a full multi-tree row.

## T4.3 — semantic layer (done)

`semantic_map.py`. Verified empirically (not assumed) that the semantic
label map's no-hit sentinel is NaN and is pixel-for-pixel identical to the
depth map's -1.0 sentinel mask on a real view (`arm_mid_33`,
`np.array_equal` true over 76800 pixels) — the two masks come from the same
ray-hit-topology pass, so no separate validity logic was needed once the
depth mask is known. Per-voxel class posterior (Dirichlet, alpha=1 flat
prior) on the SAME grid geometry as T4.1's coarse (2cm) occupancy grid, so
the two layers are spatially aligned.

Real run, all 42 views, pixel_stride=2, 0.042s total: 75557 real pixel
observations -> 5771 observed voxels (out of 257796 total). Majority-class
voxel counts: leaf 3569, shoot 1233, fruit 917, petiole 45, peduncle 7,
other 0. Mean posterior entropy: 1.358 nats for observed voxels vs exactly
ln(6)=1.792 nats for unobserved voxels (the theoretical max, confirming the
flat-prior-with-zero-counts case is being computed correctly) — observed
voxels are meaningfully more certain but still fairly mixed, consistent
with a 2cm voxel often straddling more than one class's real geometry
(leaf/fruit/shoot boundaries).

## T4.4 — apple instance track database (done)

`tracker.py` + `hungarian.py`. Detections: real per-frame instance label
map (`fruitID`) pixels unprojected to real 3D centroids via
`sensor_model`. Tracker: greedy nearest-3D-centroid association (6cm gate),
reads ONLY position, never the real fruitID (kept in a separate scoring
path so the tracker can't cheat). Oracle: the real fruitID itself. IDF1
computed via a real from-scratch Hungarian algorithm (`hungarian.py`, no
scipy in the `helios` env — deliberately not installed, to avoid touching
a conda env shared by every phase's worktree for one small dependency;
self-tested against brute-force optimal matching on 200 random small
matrices, all exact) rather than greedy matching, since IDF1 is specifically
defined over the OPTIMAL identity assignment.

Real per-arm sequences (ordered by roadmap `node_id`, the closest proxy
this dataset has to a camera trajectory — documented as such, not
mislabeled as video):

| sequence | frames | detections | true fruit ids | IDF1 | ID switches |
|---|---|---|---|---|---|
| arm_low | 14 | 0 (never sees fruit from this z-band) | - | - | - |
| arm_mid | 14 | 16 | 8 | 0.938 | 1 |
| arm_high | 14 | 75 | 21 | 0.907 | 5 |
| naive combined (both arms, independent track-id streams) | 28 | 91 | 21 | 0.747 | 14 |

The combined-arms number is a real, honest finding, not a bug: concatenating
two arms' track-id streams without cross-camera re-identification is not
apples-to-apples (arm_mid and arm_high both see overlapping fruit but
number their tracks independently from 0), so every fruit seen by both arms
necessarily counts as an "ID switch" in the naive combined view. This
demonstrates, with real numbers, exactly why cross-camera re-identification
(not implemented here — out of scope for this phase, tracker is single-camera
per arm) is a real requirement for a true multi-arm track database, rather
than something a bigger tracker would trivially subsume.

## T4.5 — GPU-batched information gain (CPU reference implemented; GPU explicitly out of scope)

`information_gain.py`. Real vectorized (batched over pose x ray, numpy)
volumetric information gain over T4.1's real occupancy log-odds grid:
binary entropy of `p_occ=sigmoid(L)` per voxel, transmittance-discounted
along each ray (`T(s)=prod_{s'<s}(1-p_occ(s'))`), optionally boosted by
T4.3's real per-voxel fruit-class posterior. GPU/CUDA implementation is
explicitly OUT OF SCOPE for this Python-only phase (needs T0.6); the design
note for what a real GPU-batched port would change is in the module
docstring (batch dim = candidate poses -> CUDA grid/block; SoA memory
layout; occupancy grid as a CUDA 3D texture for free trilinear
interpolation + border clamping; one thread per (pose,ray) with the step
loop INSIDE the kernel accumulating in registers, block/warp reduction for
per-pose gain — all mirrored from this file's actual vectorized structure,
not invented independently).

Real run: 468 real reachable roadmap nodes (arm_high), 48 rays/pose (8x6
grid spanning the real camera FOV), 20 march steps, `max_range=0.4m`.
Batched eval time: **35ms for all 468 candidates** (0.075ms/candidate) —
demonstrates the CPU reference is already fast enough to rank hundreds of
candidates well within a planning cycle; a GPU port would matter at
thousands-to-millions of candidates, not hundreds. Gain distribution: mean
72.4, std 11.6, range [47.2, 121.3] — real discrimination between
information-rich (near canopy, node 196: gain 121.3) and starved (facing
away/into open space, node 294: gain 47.2) viewpoints.

## T4.6 — explore planner (done)

`explore_planner.py`. Ground set: real `vis_primitive_id` values seen
across the 42 actually-rendered poses (only those have known coverage;
documented restriction, not silently smaller than advertised). Real
per-arm CELF max-coverage, time-normalized by real T3.3 move-time cost
(Dijkstra over the real T3.4 roadmap graph) from the arm's current
position, updated every round (receding horizon).

Correctness check (more important here than raw savings, given only
5-13 real rendered candidates per arm): CELF's selected sequence was
verified IDENTICAL to a brute-force reference greedy (`naive_greedy_explore`,
recomputes every candidate's gain every round, no caching) on both arms
with nonzero coverage — `celf_matches_naive_greedy: True` for arm_mid and
arm_high.

Real per-arm results (both reach 100% of their own known ground set):

| arm | candidates w/ coverage | ground set size | steps to full coverage | total time (s) | CELF gain-recompute savings |
|---|---|---|---|---|---|
| arm_low | 0 (real finding: this z-band never sees fruit in this dataset) | - | - | - | - |
| arm_mid | 5/13 | 498 | 5 | 56.9 | 0% |
| arm_high | 8/13 | 1785 | 8 | 58.3 | 0% |

CELF's measured savings are honestly 0% here — NOT a bug in the lazy
mechanism (proven correct by the naive-greedy match above), but an expected
consequence of this dataset's small candidate pool (5-13 real rendered
poses per arm): with so few candidates and highly informative early picks,
every round's top candidate's coverage gain changes enough round-to-round
that caching rarely pays off at this scale. CELF's savings are known to
scale with candidate-pool size (hundreds-to-thousands, not tens) — this
phase's real render budget (42 poses total, `N_RENDER_PER_ARM=14`) doesn't
reach that regime, and this is reported as-is rather than manufactured with
a larger synthetic candidate pool that wouldn't be real coverage data.

## T4.7 — switching criteria (done)

`switching.py`. All three disjunction criteria plus the hard cap, evaluated
over T4.6's real CELF explore traces:

- eta (predicted exploit-phase rate) estimated as the best real single-hop
  exploit-style rate (new distinct real fruit instances / real travel time)
  from the start position — arm_mid: 0.436 fruit/s, arm_high: 1.189 fruit/s.
- Good-Turing `C_hat=1-f1/n` over real cumulative fruit-instance detections
  along the real CELF-selected sequence: arm_high crosses 0.95 at **step 6
  of 8** (C_hat: 0 -> 0.571 -> 0.833 -> 0.9 -> 0.917 -> **0.962** -> 0.986
  -> 0.986) — a real case of the Good-Turing criterion firing BEFORE
  frontier exhaustion (step 8), exactly the disjunction's intended
  behavior (earliest-firing criterion wins). arm_mid never crosses 0.95
  (tops out at 0.875 over its shorter 5-step run) — reported honestly
  rather than forced to fire.
- Hard cap sweep (rho in [0.2, 0.3, 0.4, 0.5, 0.6, 0.8], `T_total=120s`):
  real different cut points per rho on both arms (e.g. arm_high: rho=0.2
  cuts at step 4/8, rho=0.4 cuts at step 8/8 — right at natural completion,
  rho>=0.5 never cuts).
- Combined disjunction switch step (min of criteria 1-3): arm_mid step 5
  (frontier exhaustion — no other criterion fired first), arm_high step 6
  (Good-Turing fired first, 2 steps before natural exhaustion).

## T4.8 — exploit planner (done)

`exploit_planner.py`. `q_i(v)` = real fraction of fruit i's surface
primitives visible from pose v (same real `vis_primitive_id` mechanism as
T4.6, continuous not binary). `F(A)=sum w_i*phi(sum q_i(v))`,
`phi(z)=1-e^{-z}`, `w_i=1` uniform (documented: no independent per-fruit
value signal in this dataset). Submodularity argument (concave
non-decreasing function of a modular per-item sum) stated in the module
docstring; empirical verification deferred to T4.9 per the task doc's own
split between the two tasks.

Real budget-constrained run (`budget_s=45`): arm_high reaches 20/27 real
fruit touched (final value 8.24) in 32.0s of its 45s budget before running
out of positive-gain candidates; arm_mid reaches 8/27 fruit (final value
2.55), stopped by the budget at step 4 (would-be step 5 costs 12.7s,
pushing total past the 45s cap). Same CELF gain-recompute instrumentation
as T4.6; again 0% measured savings at this candidate-pool scale (55 and 70
recomputes respectively, matching naive-would-be counts exactly) — same
honest small-N explanation as T4.6.

## T4.9 — three-arm coordination (done)

`coordination.py`. Real bearing-only Fisher-information model
(`M_i(v)=(I-dd^T)/r^2`, standard D-optimal/triangulation-observability
construction) over 5 real fruit targets and each arm's FULL real reachable
roadmap (549/468/468 nodes — geometry-only objective, no render needed, so
the full set is usable here unlike T4.6/T4.8). `trace`'s modularity was
verified as an executable assertion (`_assert_trace_is_modular`: marginal
trace-gain of adding any node, computed two independent ways, matches to
1e-8 regardless of what's already selected — for real data, not just
argued) before running the demo.

Real result over 6 random arm orderings each, sequential greedy:

| objective | unique final assignments (of 6 orderings) | mean pairwise bearing-vector dot product |
|---|---|---|
| trace | **1** | 0.817 |
| log-det | **3** | 0.629 |

This is the task doc's warned failure mode, reproduced with real numbers:
under `trace`, every single one of the 6 random arm orderings converges to
the IDENTICAL final assignment — mathematically guaranteed once
modularity is verified (each arm's optimal pick literally cannot depend on
what other arms chose), matching "a modular objective will make all three
arms converge on the same view" exactly. Under `log-det`, arm order
genuinely changes the outcome (3 distinct assignments) and produces
measurably more diverse viewing angles (lower mean bearing-vector dot
product: 0.629 vs 0.817, i.e. the 3 arms' chosen viewing directions are
further apart on average) — log-det is doing real coordination, trace is
not.

## T4.10 — gimbal-only local refinement (done)

`run_t410_gimbal.py`. Choice made (of the task doc's two options): gradient
ascent over pan/tilt. Since PyHelios's renderer isn't differentiable, this
is implemented the only real way available — central finite-difference
gradient estimates from ACTUAL re-renders at perturbed pan/tilt (5 real
renders/iteration: center + pan+-h + tilt+-h), then a real ascent step,
against the real seeded tree + real `arm_high` joint limits (x/y/z frozen
at a real reachable position, only pan/tilt move — "gimbal-only" enforced
literally). Utility = real count of `semantic_class_id==1` (fruit) pixels
in the actual render. Needed the same cross-worktree PYTHONPATH/neutral-cwd
recipe as `gen_dataset.py` (real renders, not pre-exported data) — same
Bug #1 workaround, documented again in this script's own docstring.

Real run: started deliberately off-aim (pan=20 deg, tilt=0 deg, NOT the
roadmap's own optimized -0/-35 pick) at a real reachable `arm_high`
position. 61 real renders total (0.149s/render), 12 ascent iterations,
9.08s wall time. Initial utility 9220 fruit-pixels -> peak 15339 at
iteration 7 (**1.66x improvement**) -> final-iterate 14722 (1.60x) after
mild oscillation past the peak. The oscillation is reported honestly, not
hidden: it's the expected consequence of a FIXED ascent step size
(`LR_DEG=8`) with no backtracking/decay near a local maximum, not a bug —
a keep-best-seen policy (reported separately) recovers the peak. This
demonstrates the task doc's framing directly: gimbal motion is cheap (no
roadmap travel-time cost at all, just 61 in-place re-renders) for a real,
substantial (60%+) gain in a real semantic utility.

---

# Phase 4 complete — summary

All ten subtasks (T4.1-T4.10) implemented against real data: a fresh
seeded (reproducible) apple tree built by this phase's own `gen_dataset.py`
(41351 primitives, 27 fruit, 1336 real tube segments, 3 arms' real
placeholder-collision roadmaps, 42 real rendered views). No task was
skipped; every upstream placeholder (T3.4's collision, T0.6's missing
ray-caster/GPU infra) is traced through explicitly into this phase's own
docs rather than silently absorbed. See `PHASE4_STATUS.md` for the final
per-subtask scope declaration (real / placeholder-propagated / explicitly
out-of-scope).

