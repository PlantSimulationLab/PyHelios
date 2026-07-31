# World Model — chronological log

Run date: **2026-07-30**. Executing agent: unattended Claude Code session, working in the
main checkout on branch `apple-tree-cameras`, writing only under `yogesh_dev/world_model/`.

This is the "what actually happened" file, dead ends included. For the task-by-task verdict see
`WORLD_MODEL_STATUS.md`; for what was learned see `FINDINGS.md`.

---

## 0. Setup and a first discrepancy with the plan

**Environment.** The plan says "PyHelios works in the `base` conda env; torch lives in
`gsplat`". Both are true, but `base` is **missing `OpenEXR`**, which
`phase1/depth_export.read_depth_exr` needs to read depth back. The `helios` env has PyHelios
*and* OpenEXR *and* imageio, and is what Phases 0–8 used. **All data generation in this work
runs in `helios`, not `base`.** Training and evaluation run in `gsplat` (torch 2.7.0+cu128,
CUDA available on the RTX 5090). Verified:

```
base    : pyhelios OK, numpy OK, imageio OK, OpenEXR MISSING
helios  : pyhelios OK, numpy OK, imageio OK, OpenEXR OK
gsplat  : torch 2.7.0+cu128, cuda True, NVIDIA GeForce RTX 5090
```

No git worktree was used, per the instructions (Phase 4's cross-worktree `PYTHONPATH` bug).

---

## 1. W0 — orchard factory

Wrote `orchard.py` around `buildPlantCanopyFromLibrary(plant_count=int2(10,2),
plant_spacing=vec2(1.5,3.5))`, reusing Phase 8's seeding discipline (`seedRandomGenerator`
*before* `PlantArchitecture` is constructed), Phase 1's `enable_fruit_object_data`
(`optionalOutputObjectData` before any build) and `assign_semantic_class_ids`, and Phase 8's
never-re-query-`getAllPlantUUIDs`-after-deletion rule.

`run_w0.py` measured the four things the plan asks for. Two small mistakes on the way:

- `context.getDomainBoundingBox` returns **three `vec2`s** (`xbounds, ybounds, zbounds`), not
  two `vec3`s. Cost one crash.
- The C++ progress bar writes to stdout on every `advanceTime` sub-step and cannot be
  suppressed with `setProgressCallback` (tested: setting a no-op Python callback does not stop
  the printing). Every runner therefore writes its own clean log file next to the noisy stdout
  capture.

### Results (seed 10000 unless stated)

| Measurement | Value |
|---|---|
| 2×10 orchard, age 540 d | 752,201 primitives, 13.5 s build |
| 2×10 orchard, age 650 d | 830,392 primitives, 40.1 s build, 519 fruit objects |
| 2×10 orchard, age 720 d | 830,392 primitives, 37.8 s build, 519 fruit objects |
| 2×10 orchard, age 800 d | 381,346 primitives, 45.2 s build, **0** fruit objects |
| Determinism | seed 10000 twice → 830,392 / 519 both times; seed 10001 → 846,331 / 549 |
| `advanceTime` at 20 trees (650→750 d) | 0.92 – 2.77 s per call for dt = 10–40 d |

The plan's numbers for the *orchard* reproduce closely (it reported 756,833 prims / 14.1 s at
540 d; we measured 752,201 / 13.5 s — a seed difference). The plan's **single-tree** numbers do
not reproduce: it reported 11,963 prims at 365 d and 45,315 at 720 d; we measured 4,886 at
400–500 d and 34,024 at 600–730 d. Reported as a discrepancy, not silently adapted.

### The finding that changed the plan: growth is piecewise constant

The plan's gotcha 7 says age 540 d produces no fruit and that the schedule must reach
650–720 d. The measured single-tree age→fruit curve (`run_w0b.py`, ages 520–800 d in 10-day
steps, every quantity from real `getPrimitiveArea` sums) says something quite different:

```
 age  prims  fruit  leafA(m2)  fruitA(m2)  meanD(mm)  h(m)
 520   4886      0     0.0000     0.00000       0.00   1.79
 530   4886      0     0.0000     0.00000       0.00   1.79
 540  34001      0     0.5472     0.00000       0.00   1.97
 550  22357     20     1.7677     0.12059      43.81   2.17
 560  27992     20     2.9435     0.29179      68.15   2.37
 570  33062     20     3.9874     0.53743      92.49   2.56
 580  34024     20     4.6524     0.59549      97.35   2.70
 590 …730  ——— every value bit-identical to 580 ———
 740  16058      0     0.0000     0.00000       0.00   2.55
 …800  ——— identical to 740 ———
```

So: fruit exists from 550 to 730 d, but **all geometry is frozen from 580 d to 730 d** and gone
by 740 d. The only window in which anything actually grows is **540 → 580 d**. The plan's
recommended 650–720 d schedule is inside the frozen region — it would have produced a growth
channel where `advanceTime(20)` is a literal no-op, and W0's own `advanceTime` measurement
(started at 650 d) confirms exactly that: primitive count and fruit primitive count were
identical across four consecutive advances.

`run_w0c.py` re-measured the growth channel inside the real window:

```
 age 540.0  build   6.68s  prims 752201  leafA  13.10  fruitA  0.000
 age 545.0  grow    1.92s  prims 485145  leafA  27.55  fruitA  1.632
 age 550.0  grow    1.67s  prims 561096  leafA  40.76  fruitA  3.129
 age 555.0  grow    3.37s  prims 619871  leafA  55.43  fruitA  5.109
 age 560.0  grow    4.35s  prims 689544  leafA  68.67  fruitA  7.572
 age 565.0  grow    2.04s  prims 743468  leafA  81.82  fruitA 10.518
 age 570.0  grow    5.07s  prims 807859  leafA  93.76  fruitA 13.946
 age 575.0  grow    2.36s  prims 830392  leafA 105.12  fruitA 15.453
 age 580.0  grow    1.25s  prims 830392  leafA 110.41  fruitA 15.453
 age 585.0  grow    1.30s  ——— frozen from here ———
```

8 of 10 consecutive stages differ. `advanceTime` costs 1.25–5.07 s (mean 2.46 s) against 6.68 s
for a build at 540 d and ~38 s at 720 d.

`run_w0c.py` also checked whether `build(540) + advanceTime(50)` equals `build(590)`. It does:
identical organ counts for every organ; leaf area differs by 1.4e-5 m² out of 110.41 m²
(1.3e-7 relative) and shoot area by 0.017 m² out of ~111 m² (1.5e-4 relative). My strict
`< 1e-6 absolute` test reported "not equivalent", which is a *test* that was too strict, not a
real disagreement — the two paths agree to accumulation noise. The generator therefore builds
once and advances, saving ~8× on the growth channel.

---

## 2. W1 — batched observation rig

### The batching result is even better than the plan measured

Solve time is **flat** from 1 to 256 cameras on the full 830 k-primitive orchard:

| N cameras | solve (3 bands) | per image |
|---|---|---|
| 1 | 4.85 s | 4.846 s |
| 4 | 4.88 s | 1.220 s |
| 16 | 4.83 s | 0.302 s |
| 32 | 4.86 s | 0.152 s |
| 64 | 4.83 s | 0.075 s |
| 128 | 4.84 s | 0.038 s |
| **256** | **4.88 s** | **0.019 s** |

That is a **254× throughput difference** between naive and batched rendering, and it still has
not saturated at 256. Readback of all four modalities (3 RGB bands + depth EXR + semantic label
map + instance label map) costs **0.0091 s/image** — not a bottleneck.

### Dead end 1: the obvious orientation test does not work

`getCameraPixelData` returns a flat buffer whose scan order is not documented. The first test
compared a "has radiance > 0" mask against the "hit geometry" mask (`~isnan(label_map)`) under
four candidate flips. It gave a best IoU of only **0.872** — and the giveaway was that
`lit_frac` (0.442) *exceeded* `hit_frac` (0.403). Cause: `setDiffuseRadiationFlux` lights
background pixels too, so "lit" ≠ "hit". The test cannot work in principle.

Replacement, which does work: use the per-organ optical properties we set ourselves. Leaves get
green/red reflectance 0.170/0.075 = 2.27; fruit gets 0.150/0.420 = 0.357. Under the correct
orientation the median green/red ratio on leaf pixels divided by the same on fruit pixels should
be ≈ 6.4; under a scrambled orientation it collapses to ≈ 1. Measured:

```
as_is  2.186    flipud 1.000    fliplr 6.226    rot180 1.000
diagnostics under fliplr: leaf g/r = 2.413 (predicted 2.27), fruit g/r = 0.387 (predicted 0.357)
per-camera votes: fliplr 8/8
```

### Dead end 2: aggregating that score by the *mean* picked the wrong answer

During a generator smoke test the same routine reported `orientation=flipud, score=1.2e7`, with
votes `{as_is: 1, flipud: 2, fliplr: 13}`. One calibration view had almost no fruit pixels, its
green/red ratio blew up to ~1e7, and the mean followed it. Fixed by aggregating with a
**majority vote** (median score kept only as a diagnostic) and by requiring ≥ 200 leaf and
≥ 200 fruit pixels per view.

### Dead end 3: calibrating orientation at growth stage 0 silently disabled it

The generator originally calibrated at `stages[0]` = 540 d. W0b had already measured that there
is **zero fruit at 540 d**, so no view passed the fruit-pixel threshold, the routine fell back to
its default `as_is`, and printed `calibration: orientation=as_is`. That would have written the
whole dataset mirrored. Fixed three ways: calibrate at the *last* stage (which has fruit), pool
exposure samples over the first *and* last stage, and **raise** rather than fall back if fewer
than 3 views are usable or the vote share is under 60%.

### Dead end 4: flipping all four modalities is a bug that looks fine

The first implementation applied the calibrated flip to RGB **and** depth **and** the semantic
and instance label maps. Every modality then agrees with every other, and a mirrored orchard
still looks exactly like an orchard, so nothing looks wrong. But depth and the label maps come
out of the pixel-labelling pass whose geometry Phase 0 T0.3 validated sub-pixel against
`look_at_view_matrix` — they were already correct, and flipping them put every modality in a
mirror of the recorded pose. Only the raw RGB buffer needs the flip. Fixed, and a reprojection
test (V7) was added specifically to catch this class of bug: project each fruit's known world
centroid through the recorded pose and compare against its instance-mask centroid.

### The orchard had no ground

The first contact sheet showed **61% of every frame was background**: there is no ground plane
in a `PlantArchitecture` canopy, so the entire lower half of every in-lane view was empty space.
Added a 40 × 24 m subdivided tile at z = 0 with soil reflectance and, importantly, **seeded
per-patch reflectance jitter** — a flat alley gives an action-conditioned model no optical-flow
cue in ~46% of the frame. After: sky 18.4%, ground 45.7%, canopy ~36%.

---

## 3. W2 — actions

Pure NumPy, no rendering, so this was quick. 4-D view action `(dx, dy, dz, dyaw)` plus a scalar
growth action. Pitch is fixed per episode and roll is always zero **because
`addRadiationCamera` exposes no up-vector or roll control** — recording a pitch action the rig
cannot execute would be dishonest.

The measured orchard bounding box at 720 d (x ∈ [−7.78, 7.86], y ∈ [−3.09, 3.12]) with tree
bases at y = ±1.75 implies a canopy half-width of ~1.34 m and a free inter-row lane only
~0.82 m wide. `LANE_HALF_WIDTH = 0.35` is derived from that measurement.

Acceptance passed: 600 trajectories (200 per family × 128 steps) all in bounds; action replay
reproduces the recorded states to a maximum error of **4.7e-7** (the residual is float32
quantisation of the stored actions, which is what the schema specifies). Orbits pass through
canopy volume 41.8% of the time on average, up to 76.6% — reported rather than prevented,
because Helios cameras have no collision.

---

## 4. W3 — dataset generation

*(continued in FINDINGS.md and WORLD_MODEL_STATUS.md)*
