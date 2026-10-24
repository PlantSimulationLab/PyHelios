# Phase 3 Log — Kinematics and the reachability roadmap

Scope: `helios_setup_tasks.md`, "## Phase 3 — Kinematics and the reachability
roadmap" (T3.1–T3.5) only. Implemented in `yogesh_dev/phase3/`.

Prior-phase inputs read (not modified):
- `worktree-phase0-radiation:yogesh_dev/phase0/canopy.py` — 3-tree scene layout
  (trees at x=0, 1.5, 3 m).
- `worktree-phase0-radiation:yogesh_dev/phase0/pose_convention.py` — empirically
  validated RadiationCamera pose convention: world_up=(0,0,1), OpenCV-style
  camera frame, **no roll representable** (EXIF roll hardcoded to 0). This
  directly shaped the FK look-direction convention in T3.1 (pan/tilt only,
  never introduces roll).
- `worktree-phase1-groundtruth:yogesh_dev/phase1/output/fruit_ground_truth.json`
  — 73 real fruit objects (bbox_min/bbox_max/centroid) across 3 trees. Copied
  verbatim into `yogesh_dev/phase3/reference_data/fruit_ground_truth.json` so
  Phase 3 doesn't depend on another worktree's on-disk path surviving. Used
  for: (a) picking realistic joint-limit numbers, (b) the T3.4 placeholder
  collision boxes.

Aggregate fruit geometry actually measured from that file (used to size the
workspace):
- Per-plant x-extent: plant0 [-0.61, 0.64], plant1 [0.75, 1.92], plant2 [2.60, 3.46] m
- Per-plant y-extent: plant0 [-0.37, 0.30], plant1 [-0.42, 0.44], plant2 [-0.41, 0.54] m
- Global z-extent (fruit only, all 3 trees): [0.70, 1.82] m

## T3.1 — Forward kinematics (`kinematics.py`)

5-DOF chain: 3 prismatic (x=left-right, y=in-out, z=up-down) + pan + tilt.
Position and orientation are fully decoupled by construction (zero gimbal
offset: the camera's optical center sits exactly at (x,y,z); pan/tilt only
rotate the look direction about that point). This is a deliberate
simplification — real gimbal hardware has a nonzero offset between its
rotation center and the camera's nodal point, which would turn IK into a
small nonlinear solve instead of the closed form in T3.2. Flagged for
revisit once real hardware geometry exists.

Look-direction convention: `forward = (sin(pan)cos(tilt), cos(pan)cos(tilt),
sin(tilt))`, i.e. pan=0/tilt=0 points along +Y, world up = +Z. Matches the
T0.3-validated RadiationCamera convention. Never introduces roll (neither
pan nor tilt rotates about the view axis) — required, not just convenient,
since the RadiationCamera cannot represent roll at all.

**Placeholder joint limits/vertical bands** (no real hardware spec exists —
documented explicitly as such in `default_arm_configs()`'s docstring):
- x (rail): [-0.75, 3.75] m — spans all 3 trees + 0.75 m margin per side
- y (reach): [-1.10, -0.05] m — rail-side approach envelope up to the
  canopy's front face (never crosses y > -0.05, i.e. never drives through
  the trunk region)
- pan: [-55, 55] deg, tilt: [-35, 35] deg
- Per-arm DISJOINT z-bands (this is what makes T3.5's structural guarantee
  work): arm_low [0.50, 0.95], arm_mid [1.00, 1.45], arm_high [1.50, 1.95] m,
  with explicit 0.05 m gaps between bands. Covers the full measured fruit
  z-range [0.70, 1.82] m with margin at both ends.

All of the above are placeholders pending real hardware measurements — this
is called out both in the module docstring and in `PHASE3_STATUS.md`.

## T3.2 — Inverse kinematics (`kinematics.py`)

Closed-form, no iterative solver: x,y,z = camera position directly (decoupled
from orientation); `tilt = asin(dz)`, `pan = atan2(dx, dy)` from the unit
look-direction vector. Valid without a gimbal-lock branch because tilt is
bounded to (-35, 35) deg, well inside (-90, 90) where cos(tilt) > 0 always.

**Round-trip check actually run** (`verify_roundtrip()`, called for real from
`run_phase3_demo.py`, not just asserted in a docstring): grid + small random
jitter over each arm's full joint-limit box, FK → IK → FK, compare pose and
joints.

Real numbers from the last run, 3125 samples/arm (5^5 grid, n_per_axis=5):

| arm | max position error (m) | max lookat error (m) | max joint error | limit violations | passed |
|---|---|---|---|---|---|
| arm_low | 0.0 | 4.71e-16 | 2.84e-14 | 0 | True |
| arm_mid | 0.0 | 4.58e-16 | 2.49e-14 | 0 | True |
| arm_high | 0.0 | 8.95e-16 | 2.84e-14 | 0 | True |

**Bug found and fixed during this check**: exact-boundary joint samples
(e.g. tilt = -35.0 deg exactly) round-tripped through `asin`/`atan2` to
values like `-35.00000000000001`, tripping `joint_within_limits`'s strict
inequality and getting flagged as spurious "limit violations" (164–196 out
of 1024 samples in the first run). Fixed by adding a `1e-9` floating-point
tolerance to `joint_within_limits` (documented in its docstring as absorbing
round-off, not real joint slack). After the fix: 0 violations across all
three arms, confirmed above.

## T3.3 — Execution-time model (`motion_time.py`)

Trapezoidal velocity profile, standard closed form:
`d_accel = v_max²/(2·a_max)`; trapezoidal if `2·d_accel ≤ d`, else
triangular (`t = 2·sqrt(d/a_max)`). Move time between two joint states =
`max` over the 5 per-axis times (assumes synchronized start/stop, bounded by
the slowest axis — standard multi-axis move-time simplification).

**Placeholder hardware numbers** (no real datasheet available — flagged in
the module docstring):
| axis | v_max | a_max |
|---|---|---|
| x (rail) | 0.30 m/s | 0.50 m/s² |
| y (reach) | 0.20 m/s | 0.40 m/s² |
| z (lift) | 0.25 m/s | 0.40 m/s² |
| pan | 180 deg/s | 400 deg/s² |
| tilt | 180 deg/s | 400 deg/s² |

Real numbers produced by `demonstrate_asymmetry()` (full-range single-axis
moves matching the T3.1 joint-limit widths):
- full rail traverse (4.5 m): **15.60 s**
- full reach traverse (1.05 m): 5.75 s
- full lift traverse (0.45 m, one z-band width): 2.43 s
- full pan sweep (110 deg): 1.06 s
- full tilt sweep (70 deg): 0.84 s
- **cost asymmetry (rail / pan): 14.7x**

This asymmetry (gimbal moves ~15-19x cheaper than the linear stages) is the
structural basis for the nested-planner idea in the design doc §3.1 — it's
what the roadmap's execution-time-weighted edges (T3.4) actually encode.

## T3.4 — Roadmap building (`roadmap.py`)

Per arm: discretize the 5-DOF joint box on a regular grid (6 samples/linear
axis, 4/gimbal axis = 3456 grid points), reject nodes via the placeholder
collision check (below), connect survivors with a k=6-NN graph in
*normalized* joint space (Euclidean distance / per-axis range, used only to
pick which nodes are "nearby" candidates for an edge), with edge weight =
REAL T3.3 execution time between the two joint configs (not joint-space
distance). Dijkstra over that graph turns planning into graph search.

No scipy/networkx in the `helios` conda env (checked directly — scipy
`ModuleNotFoundError`, networkx `ModuleNotFoundError`) — implemented k-NN as
brute-force numpy (fine at this node count) and Dijkstra with stdlib
`heapq`, no external graph library.

**"Precompute once per cart position" (task doc wording)**: this
implementation already includes the rail axis (x) as one of the 5
discretized joint dimensions rather than as a separate outer loop, so one
full build_roadmap() call is equivalent to precomputing for every cart
position simultaneously. Documented in the module docstring; not
implemented as a separate per-x-slice cache since it would just be a
reslicing of the same grid, not new machinery.

**Real numbers from the last run** (n_linear=6, n_gimbal=4, k=6):

| arm | grid samples | rejected (placeholder collision) | reachable nodes | edges | build time |
|---|---|---|---|---|---|
| arm_low | 3456 | 224 | 3232 | 21676 | 0.235 s |
| arm_mid | 3456 | 576 | 2880 | 19250 | 0.193 s |
| arm_high | 3456 | 320 | 3136 | 21186 | 0.216 s |

Dijkstra demo (node 0 → last node, each arm): 17-hop path, 27.2–28.4 s total
execution time — a real graph-search result over real edge weights.

### COLLISION CAVEAT — read this before trusting any "reachable" number above

`CollisionDetection` (`castRaysSoA`/`findCollisions`/`findCollisionsWithinDistance`/
`buildBVH`) is **not exposed in PyHelios** —
`pyhelios/config/plugin_metadata.py`: *"CollisionDetection dependency handled
at C++ level, not exposed in Python API."* Confirmed by grepping that file
directly. This is blocked on T0.6, which has not been done in any prior
phase. Nothing in this phase fakes or claims otherwise.

What's actually implemented instead (`canopy_boxes_from_ground_truth` +
`point_in_any_box` in `roadmap.py`): a candidate node is rejected if the
camera's optical-center POINT falls inside the coarse per-plant axis-aligned
bounding box of that tree's **fruit only** (unioned from the real Phase 1
`bbox_min`/`bbox_max` records). This is explicitly:
1. A point-vs-box test on one point (the camera's optical center) — not a
   ray-traced test against actual leaf/branch/fruit triangles.
2. A box built from fruit bounding boxes only — leaves and branches extend
   beyond it in both directions, so it's neither a superset nor a subset of
   the true canopy volume.
3. Evaluated once per discrete node — no continuous sweep of the path
   between two connected roadmap nodes.
4. Blind to the T3.5 arm-link geometry — it doesn't check whether the
   mast/column itself would clip the canopy, only the bare camera point.

**What swapping in real `findCollisions`/`castRaysSoA` (once T0.6 lands)
would change**, precisely:
1. Box → per-primitive resolution: fixes both false rejections (empty space
   inside the box, e.g. under a sparse canopy) and false acceptances (a
   branch poking outside the fruit box).
2. Endpoint → continuous path sweep between connected roadmap nodes.
3. Camera point → the actual T3.5 arm-link volume.
4. Static canopy box → arbitrary-origin ray casts, which this bounding-box
   test cannot approximate at all (also needed for Phase 2's fruit-outward
   visibility, same underlying gap).

## T3.5 — Arm/workcell collision geometry (`arm_geometry.py`)

Two independent, both real, both run:

1. **Structural non-collision guarantee** (`verify_non_overlapping_bands`) —
   direct interval-overlap arithmetic (`a0 < b1 and b0 < a1`) over every pair
   of arms' z-bands from `default_arm_configs()`. Result: **all 3 bands
   disjoint** (arm_low [0.50,0.95], arm_mid [1.00,1.45], arm_high
   [1.50,1.95] — 0.05 m gaps). This does NOT use `findCollisions` — pure
   Python, as the task doc asks for.

2. **Live Context geometry** (`add_arm_link_geometry` +
   `verify_geometry_bands_via_context`) — added one box per arm (15 cm
   square cross-section placeholder mast, spanning exactly its z-band) to a
   real `pyhelios.Context`, then independently re-derived the same
   disjointness conclusion via `Context.getDomainBoundingBox` on the added
   primitives. Real run output:
   ```
   arm_low: added 6 primitive(s)
   arm_mid: added 6 primitive(s)
   arm_high: added 6 primitive(s)
   Context z-ranges: arm_low (0.5, 0.9500000477), arm_mid (1.0, 1.4500000477), arm_high (1.5, 1.9500000477)
   Bands disjoint per live Context geometry: True
   ```
   Two independent code paths (pure Python interval math, and the Helios API
   round-trip) agree.

**Explicitly NOT done here** (documented in the module docstring): arm-vs-canopy
collision checking. That needs ray casts / BVH queries against the real
leaf/branch/fruit primitives — blocked on T0.6, same as T3.4's caveat.

## Problems hit / environment notes

- **No scipy or networkx in the `helios` conda env.** Checked directly
  (`ModuleNotFoundError` for both). Worked around with brute-force numpy
  k-NN and stdlib `heapq` Dijkstra — fine at this task's node counts (~3000
  nodes/arm), would need scipy's `cKDTree` if scaled up substantially.
- **Cross-worktree package collision (this session's environment only, not
  a code issue).** This background job's isolation runs `yogesh_dev/phase3`
  in its own git worktree, while the main PyHelios checkout has an unrelated
  untracked `yogesh_dev/` (other phases' in-progress work, no `phase3/`) that
  shares the same top-level package name — and only the MAIN checkout has
  the compiled native Helios library (`pyhelios_build/build/lib/libhelios.so`).
  No single sys.path ordering resolves both `yogesh_dev.phase3` (worktree)
  and a working `pyhelios` (main checkout) simultaneously via normal package
  resolution. Verified this is purely a parallel-worktree artifact, not a
  real deployment problem: once this branch is the only `yogesh_dev/` on
  disk (post-merge), plain `python -m yogesh_dev.phase3.run_phase3_demo`
  from the repo root works exactly like `yogesh_dev/phase0`'s existing
  scripts. To get the real numbers logged above in THIS sandboxed session, I
  ran the demo through a one-off shim (not part of the deliverable, lives
  under the job's tmp dir) that wires `sys.modules['yogesh_dev.phase3']`
  directly at the worktree path and appends the main checkout to `sys.path`
  for `pyhelios` — it just calls `run_phase3_demo.main()` unmodified, no
  logic duplicated.

## What remains blocked on T0.6 (exact list)

T0.6 = exposing `CollisionDetection` (`castRaysSoA`/`castRaysGPU`/
`findCollisions`/`findCollisionsWithinDistance`/`buildBVH`) in PyHelios.
Not done in any phase so far. Blocked because of it:

1. **T3.4's collision check is a coarse fruit-bbox point test**, not
   per-primitive ray-traced collision. See the COLLISION CAVEAT section
   above for the precise list of what changes once T0.6 lands.
2. **T3.5's arm-vs-canopy collision is not checked at all** — only
   arm-vs-arm (via the structural vertical-band guarantee, which doesn't
   need T0.6). Checking whether an arm's link geometry actually clips the
   tree needs `findCollisions`/`castRaysSoA` against the real leaf/branch
   primitives.
3. Continuous-path (as opposed to discrete-node) collision checking for
   roadmap edges is not implemented — needs the same binding to be
   worth doing accurately (a coarse box-based path sweep would be possible
   without T0.6, but wasn't requested and wouldn't be meaningfully better
   than the endpoint check already done).
4. Downstream: Phase 2 (T2.1, T2.3) and Phase 4 (T4.1, T4.5) are also
   blocked on T0.6, per the task doc's own dependency notes — not attempted
   here since only Phase 3 was in scope for this task.
