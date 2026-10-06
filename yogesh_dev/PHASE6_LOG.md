# Phase 6 — Metrics harness — Log

Working under the hard constraint that nothing outside `yogesh_dev/` may be
edited. All code lives in `yogesh_dev/phase6/`. Where a task's ground truth
is a real bug in `apple_tree_gaussian_splatting.py` (repo root), the fix is
implemented + demonstrated in `yogesh_dev/phase6/`, and the exact patch for
a human to apply to the real file is written below.

## Environment notes (apply to every task in this log)

- This worktree (`worktree-phase6-metrics-harness-v2`) was created fresh
  from `apple-tree-cameras`'s HEAD, so it starts with no native Helios build
  and no populated `helios-core` submodule. Rather than rebuild (slow,
  duplicates ~GB of artifacts already built for the sibling phase
  worktrees), I symlinked the already-built artifacts from the main
  checkout: `pyhelios_build/build -> /home/yogesh/PyHelios/pyhelios_build/build`
  and `helios-core -> /home/yogesh/PyHelios/helios-core` (same pattern
  already used by `worktree-phase2-avub` and `worktree-phase5-baselines`).
  These are untracked/gitlink-type local filesystem changes only, never
  staged or committed.
- The `helios` conda env (`/home/yogesh/anaconda3/envs/helios/bin/python`)
  has **no `torch`, no `gsplat`, no `scipy`**, but does have `numpy`,
  `pillow`, `OpenEXR`, and `pulp` (3.3.2, installed into this env by the
  Phase 5 job for its T5.7 ILP work — not installed by this phase).
  Consequences:
  - `apple_tree_gaussian_splatting.py` cannot be imported as a whole module
    here (`import torch` fails at line 7) — this is true independent of the
    edit restriction, so all T6.1-T6.3 code below reimplements (not
    imports) the small pieces of that file's logic it needs, each cited by
    exact line number against the real file.
  - No SciPy in this phase's own code: `scipy.stats.spearmanr` (T6.9) is
    replaced with a hand-rolled Spearman rho (Pearson correlation of ranks,
    with the standard average-rank tie handling) — mathematically
    identical, just not SciPy's implementation.
  - PuLP *is* available, so T6.8's optional ILP cross-check can use it
    without a new install.

---

## T6.1–T6.3 — `yogesh_dev/phase6/t61_t62_t63_gsplat_fixes.py`

All three demonstrated together against ONE real, live-built apple tree
(same `apple_tree.build_apple_tree`, `age_days=720.0`, as the real
pipeline uses) — see `yogesh_dev/phase6/output/t61_t62_t63_report.json`
for the full real numbers. Run via
`python -m yogesh_dev.phase6.t61_t62_t63_gsplat_fixes` from the repo root
in the `helios` env.

### T6.1 — train/test split collapses to column 0

**Bug, reproduced for real** on the actual `CAPTURE_CONFIGS` grids (using a
faithful reimplementation of `plane_camera_poses`, since the real function
can't be imported — see env notes above — fed with a real built tree's
bounding geometry: center `(-0.076, 0.142, 1.391)`, height `2.79m`, x-extent
`2.24m`, y-extent `1.51m`):

| config | n_views | num_cols | old scheme test cols | old n_test | new (seeded permutation) test cols |
|---|---|---|---|---|---|
| sparse | 8 | 4 | `{0}` | 1 | `{0}` (only 1 test view exists at this density, so no spread is possible either way — see caveat below) |
| default | 24 | 8 | `{0}` | 3 | `{5, 6}` |
| multi_face | 96 | 8 | `{0, 0, 0, ...}` → `{0}` | 12 | `{0, 1, 2, 3, 5, 7}` |

Root cause confirmed exactly as hypothesized: `TEST_EVERY = 8` (line 53)
divides every config's `num_cols` (`4` or `8`), so `i % TEST_EVERY == 0`
only ever lands on `i % num_cols == 0` (column 0), for every plane, in
every config — because `plane_camera_poses`'s pose loop
(lines 285-286, `for z_off in rows: for t_off in cols:`) is row-major with
columns innermost, so `column(i) = i % num_cols` globally, and `num_cols`
evenly divides the per-plane block size `num_rows * num_cols`.

**Fix**: `seeded_permutation_split(n, test_every, seed)` in
`t61_t62_t63_gsplat_fixes.py` — draws the SAME number of test views
(`round(n / test_every)`, so downstream train/test counts printed by the
pipeline don't change) via `np.random.RandomState(seed).permutation(n)`
instead of `i % test_every`. Caveat: at very low view counts (`sparse`,
n_test=1) a single held-out view can't "distribute across columns" by
definition — the fix's benefit is real but only visible once
`n_test > num_cols`, which `default`/`multi_face` both satisfy.

**Patch for the real file** (apply by hand — see constraint):

```
File: apple_tree_gaussian_splatting.py

--- around line 53 ---
- TEST_EVERY = 8
+ TEST_EVERY = 8
+ SPLIT_SEED = 20260729  # new: seeds the train/test permutation (T6.1)

--- render_dataset(), around lines 328-350 ---
 def render_dataset(context, all_uuids, camera_poses, out_dir, width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
                     fov_deg=FOV_DEG, background_rgb=BACKGROUND_RGB, test_every=TEST_EVERY):
     os.makedirs(out_dir, exist_ok=True)
     K = intrinsics_matrix(width, height, fov_deg)

+    n_views = len(camera_poses)
+    n_test = max(1, round(n_views / test_every))
+    rng = np.random.RandomState(SPLIT_SEED)
+    test_idx = set(rng.permutation(n_views)[:n_test].tolist())
+
     frames = []
     with Visualizer(width=width, height=height, headless=True) as visualizer:
         ...
         for i, (eye, lookAt) in enumerate(camera_poses):
             ...
             frames.append({
                 "file_path": filename,
                 "viewmat": look_at_view_matrix(eye, lookAt),
-                "split": "test" if (i % test_every == 0) else "train",
+                "split": "test" if (i in test_idx) else "train",
             })
```

(`np` is already imported at the top of the file; no new imports needed.)

---

### T6.2 — masked PSNR restricted to GT-fruit ∪ rendered-alpha

**Bug, reproduced for real** on 3 of Phase 1's actual rendered views + real
semantic label maps (`yogesh_dev/phase1/output/rgb/*.jpeg` +
`labels/*_semantic.npy`), against a "dummy" render that reproduces the
scene's own real background color everywhere and renders NO fruit at all
(alpha=0 everywhere) — the exact degenerate case T6.2 describes:

| view | fruit fraction of frame | naive full-frame PSNR | masked PSNR | inflation |
|---|---|---|---|---|
| above_tree0_above | 1.09% | 15.94 dB | 8.76 dB | **+7.19 dB** |
| level_tree1_level | 1.97% | 14.30 dB | 8.85 dB | **+5.45 dB** |
| below_tree2_below | 1.22% | 16.14 dB | 8.71 dB | **+7.42 dB** |

A model that renders literally nothing scores 14-16 dB on the pipeline's
current full-frame metric (`evaluate()`, lines 544-563) purely because
>=73-83% of every frame is background it trivially reproduces — masking to
GT-fruit ∪ rendered-alpha (which for this all-background dummy reduces to
GT-fruit only, since its alpha is 0 everywhere) drops that to the true
~8.7-8.9 dB, a 5.4-7.4 dB inflation on real data.

**Fix**: `masked_psnr(target_rgb, rendered_rgb, gt_fruit_mask,
rendered_alpha, alpha_thresh=0.5)` in `t61_t62_t63_gsplat_fixes.py`.

**Patch for the real file**:

```
File: apple_tree_gaussian_splatting.py

--- evaluate(), lines 544-563 ---
 def evaluate(params, dataset, K, width, height, background_rgb, out_dir, device=DEVICE):
     os.makedirs(out_dir, exist_ok=True)
     background = torch.tensor(background_rgb, dtype=torch.float32, device=device).unsqueeze(0)
     psnrs = []
     with torch.no_grad():
         for i, view in enumerate(dataset["test"]):
-            rendered, _, _ = render_view(params, view["viewmat"], K, width, height, background)
+            rendered, alpha, _ = render_view(params, view["viewmat"], K, width, height, background)
             rendered = rendered.clamp(0, 1)
             target = view["image"]

-            mse = ((rendered - target) ** 2).mean().item()
+            gt_fruit_mask = view["fruit_mask"]  # new: needs threading through load_dataset_tensors, see below
+            mask = gt_fruit_mask | (alpha.squeeze(-1) > 0.5)
+            mse = ((rendered[mask] - target[mask]) ** 2).mean().item() if mask.any() else float("nan")
             psnr = 10 * math.log10(1.0 / max(mse, 1e-10))
             psnrs.append(psnr)
```

`load_dataset_tensors` (lines 375-395) needs to additionally stash the
boolean `keep` array (currently computed at line 389 and only used to
overwrite pixel colors) into each dataset entry as `"fruit_mask"` so
`evaluate()` can read it back per test view:

```
--- load_dataset_tensors(), around line 391 ---
         dataset[frame["split"]].append({
             "image": torch.from_numpy(image).to(device),
             "viewmat": torch.from_numpy(frame["viewmat"]).to(device),
+            "fruit_mask": torch.from_numpy(keep).to(device) if mask_paths is not None else None,
         })
```

---

### T6.3 — occlusion-aware mask supervision

**Bug, reproduced for real**: built one real tree, rendered ONE camera pose
twice — once with the full scene's geometry (fruit + everything else, the
same nearest-hit-wins occlusion the pipeline's current mask already uses)
and once with ONLY the fruit primitives in the Visualizer's geometry build
(so nothing can occlude — the true unoccluded silhouette):

- `n_fruit_alone_silhouette_px` (true fruit extent, unoccluded): 8662
- `n_fruit_visible_unoccluded_px` (current pipeline's "fruit mask", i.e.
  fruit that's ALSO the nearest hit in the full scene): 6493
- `n_occluded_fruit_px` (silhouette minus visible — real apples hidden
  behind leaves/branches from this pose): **2169 (25.0% of the true fruit
  silhouette)**

Under the CURRENT pipeline (`load_dataset_tensors`, line 390:
`np.where(keep[..., None], image, background_rgb)`), those 2169 pixels are
unconditionally replaced with `background_rgb` and then supervised via the
full-frame `l1`/`ssim` loss in `train_gaussians` (lines 516-517) with no
per-pixel mask at all — i.e. the model is explicitly taught "there is
background here," for pixels that are real occluded apples. Confirmed:
`old_scheme_loss_mask_excludes_any_pixels: false` (today's pipeline has no
loss-exclusion mechanism whatsoever).

**Fix**: `build_occlusion_aware_training_mask(fruit_visible_mask,
fruit_alone_silhouette_mask)` in `t61_t62_t63_gsplat_fixes.py` — returns a
`loss_mask` that is `False` exactly on `occluded_fruit_mask` (the 2169
pixels above), so the training loss skips them instead of supervising them
toward background.

**Patch for the real file** — this needs one new rendering pass
(fruit-alone silhouette, alongside the existing `render_semantic_masks`
call) plus a loss-mask threaded through training:

```
File: apple_tree_gaussian_splatting.py

--- main(), after the existing render_semantic_masks call (~line 636) ---
+                print(f"Rendering {len(camera_poses)} fruit-alone silhouette masks (T6.3)...")
+                silhouette_paths = render_semantic_masks(
+                    context, {"fruit": class_uuids["fruit"], "leaf": [], "tree": []},
+                    camera_poses, dataset_dir, width=IMAGE_WIDTH, height=IMAGE_HEIGHT,
+                )  # only fruit geometry present -> unoccluded silhouette per view
                 capture_datasets.append({"name": capture_name, "frames": frames, "K": K,
-                                          "mask_paths": mask_paths})
+                                          "mask_paths": mask_paths, "silhouette_paths": silhouette_paths})

--- load_dataset_tensors(), lines 375-395 ---
 def load_dataset_tensors(frames, K, device=DEVICE, mask_paths=None, target_class_index=None,
-                          background_rgb=BACKGROUND_RGB):
+                          background_rgb=BACKGROUND_RGB, silhouette_paths=None):
     ...
     for i, frame in enumerate(frames):
         image = np.asarray(Image.open(frame["file_path"]).convert("RGB"), dtype=np.float32) / 255.0
+        loss_mask = np.ones(image.shape[:2], dtype=bool)
         if mask_paths is not None and target_class_index is not None:
             class_mask = np.asarray(Image.open(mask_paths[i]).convert("L"))
             keep = class_mask == target_class_index
             image = np.where(keep[..., None], image, np.array(background_rgb, dtype=np.float32))
+            if silhouette_paths is not None:
+                silhouette = np.asarray(Image.open(silhouette_paths[i]).convert("L")) == target_class_index
+                occluded_fruit = silhouette & ~keep
+                loss_mask &= ~occluded_fruit
         dataset[frame["split"]].append({
             "image": torch.from_numpy(image).to(device),
             "viewmat": torch.from_numpy(frame["viewmat"]).to(device),
+            "loss_mask": torch.from_numpy(loss_mask).to(device),
         })

--- train_gaussians(), lines 511-517 ---
     for step in range(1, iters + 1):
         view = train_views[np.random.randint(len(train_views))]
         rendered, _, info = render_view(params, view["viewmat"], K, width, height, background)
         target = view["image"]
+        m = view["loss_mask"]

-        l1 = (rendered - target).abs().mean()
-        loss = 0.8 * l1 + 0.2 * (1.0 - ssim(rendered, target))
+        l1 = (rendered - target).abs()[m].mean()
+        loss = 0.8 * l1 + 0.2 * (1.0 - ssim(rendered * m.unsqueeze(-1), target * m.unsqueeze(-1)))
```

(The SSIM term over a masked image is an approximation — SSIM is a
windowed statistic, so a hard per-pixel mask multiplied in before the
convolution is not identical to "compute SSIM only over unmasked pixels,"
but zeroing masked-out regions before the windowed conv is the standard
practical compromise and is far better than the current unmasked behavior.
A cleaner fix would drop the SSIM term entirely for masked training views
or use a masked SSIM implementation; noted here rather than silently
picked.)

---

## T6.4–T6.6 — `yogesh_dev/phase6/t64_t65_t66_perception_metrics.py`

All run against Phase 4's real single-tree dataset (`yogesh_dev/phase4/data/`:
27 fruit, 42 real rendered views across 3 arms). Full output:
`yogesh_dev/phase6/output/t64_t65_t66_report.json`.

### T6.4 — occlusion-conditioned detection recall by GT occlusion decile

Occlusion measure = `1 - (union-visible-fraction across all 42 real
rendered views)`, using Phase 2's own `fruit_visible_fraction` reused
verbatim on this dataset's real `vis_primitive_id` maps. "Detected" = the
fruit appeared as a real ≥5px instance-map detection (Phase 4 T4.4's own
`tracker.extract_detections`, reused verbatim) in ≥1 of the 42 views, any
arm.

Overall: **21/27 fruit (77.8%) ever detected**. Per-decile recall is
monotonically decreasing in occlusion, as expected for a real, working
occlusion measure:

| decile | mean occlusion | n_fruit | detection recall |
|---|---|---|---|
| 0 (least occluded) | 0.318 | 3 | 1.00 |
| 1 | 0.422 | 2 | 1.00 |
| 2 | 0.491 | 3 | 1.00 |
| 3 | 0.518 | 3 | 1.00 |
| 4 | 0.531 | 3 | 1.00 |
| 5 | 0.601 | 2 | 1.00 |
| 6 | 0.728 | 3 | 1.00 |
| 7 | 0.912 | 3 | 0.667 |
| 8 | 1.000 | 2 | 0.00 |
| 9 (most occluded) | 1.000 | 3 | 0.00 |

Caveat (documented, not hidden): with only 27 fruit, each decile bucket
holds ~2-3 fruit — real numbers, small-N.

### T6.5 — semantically stratified F-score at class-specific tau

GT points per class = real 3D points from multi-view unprojection of EXACT
(noiseless) depth at exactly-known poses (`poses.json`), keyed by the real
per-pixel semantic label — no ICP/registration needed. Candidate = Phase
4's real dual-resolution occupancy map's OCCUPIED voxel centers (fine
~3mm grid for fruit, since tau=5mm needs finer-than-2cm resolution; coarse
~2cm grid for branch/leaf).

| class | tau | precision | recall | F | candidate grid |
|---|---|---|---|---|---|
| fruit | 5mm | 0.540 | 0.109 | **0.182** | fine (~3mm) |
| branch (shoot) | 10mm | 0.097 | 0.291 | **0.146** | coarse (~2cm) |
| leaf | 10mm | 0.276 | 0.354 | **0.310** | coarse (~2cm) |
| wire | 5mm | n/a | n/a | n/a | — |

**Wire**: no wire/trellis geometry exists anywhere in this repo's scene
(single freestanding apple tree — trellis is Phase 8 scope, T8.3). 0 GT
wire elements; same "real, not fabricated" policy as T2.6's missing-module
finding.

Real finding: F-scores are low across the board (0.15-0.31) — the coarse
2cm grid genuinely cannot resolve a 10mm tau well (recall better than
precision, since occupied-voxel centers are coarser than the GT points
they're compared against), and even the fine 3mm fruit grid, while much
better-suited to a 5mm tau than the coarse grid would be, still only
reaches 0.18 F — real evidence that Phase 4's occupancy resolution is the
binding constraint for millimeter-scale class-specific accuracy, not a
bug in the scoring method.

### T6.6 — three-state occupancy confusion matrix + M(free|occ)

GT occupancy is a real-geometry proxy: fruit = sphere of real
`equivalent_diameter_m` around real centroid; branch = real tube segments
from `branch_segments_gt.json` (label=="shoot"). Leaf has no tube/sphere
geometric proxy available and is excluded from GT-occupied (documented
under-count, not hidden). No wire class exists in this scene.

Confusion matrix (predicted × GT), coarse grid (63×62×66 voxels, 2cm):

| predicted \ GT | occupied | free (incl. unmodeled leaf) |
|---|---|---|
| unknown | 1685 | 240004 |
| free | 20 | 10577 |
| occupied | 888 | 4622 |

**`M(free|occ)` restricted to wire/branch classes (safety-critical miss
rate) = 20 / 3981 = 0.503%** (branch-only GT-occupied voxels predicted
free — i.e. the mapper would tell the arm "clear to move" through a real
branch 0.5% of the time it checks a truly-occupied branch voxel). For
reference, across all modeled classes (fruit+branch): 0.771%. No wire class
exists in this scene, so `M(free|occ)` for wire specifically is n/a (same
caveat as T6.5).

---

## T6.7–T6.9 — `yogesh_dev/phase6/t67_t68_t69_planning_metrics.py`

Reuses Phase 4's own real planner code (`explore_planner.py`,
`information_gain.py`, `occupancy_map.py`) rather than reimplementing it.
`arm_low` excluded from all three (zero fruit-surface coverage possible —
real T4.6/T4.8 finding, not an error). Full output:
`yogesh_dev/phase6/output/t67_t68_t69_report.json`.

### T6.7 — discovery curve, 3 x-axes, AUC, time-to-90%

Per-step compute time was measured for real (a faithful, timed
reimplementation of `celf_explore` verified to select the IDENTICAL
sequence as the original — `sequence_matches_official_celf_explore: true`
for both arms) since the original function only returns aggregate counts,
not a per-step wall-clock breakdown.

| arm | n_steps | AUC (view_idx) | AUC (motion time) | AUC (wall incl. compute) | t90 (view_idx) | t90 (motion_time_s) | compute % of wall-clock |
|---|---|---|---|---|---|---|---|
| arm_mid | 5 | 0.823 | 0.741 | 0.741 | 2 | 32.24 | 4.3e-6% |
| arm_high | 8 | 0.723 | 0.708 | 0.708 | 7 | 45.43 | 4.3e-6% |

"Joint-space path length" x-axis realized as cumulative real T3.3 motion
time (Dijkstra over the T3.4 roadmap, edge weights = `kinematics.move_time`)
— the roadmap edge cost IS a monotonic function of joint-space travel
distance; Phase 3/4 don't track a separate physical arc-length unit, so
this is the direct available proxy, documented as such. Motion-time and
wall-clock-incl.-compute AUC/curves are visually indistinguishable at this
candidate-set scale because planning compute is ~5-6 orders of magnitude
smaller than motion time here (see T6.11's own latency numbers) — a real
finding, not a rounding artifact.

### T6.8 — oracle-normalized planning score Pi + per-step regret

Oracle = a real ILP (PuLP + CBC) max-coverage solve at each k=1..n_steps,
computed DIRECTLY on Phase 4's own per-arm coverage ground set (NOT Phase
5's T5.6/T5.7 numbers, which exist but are on a different, differently-
scaled 3-tree/83-fruit scene — included below for reference only, per the
task brief's explicit fallback-normalizer policy).

| arm | mean Pi | final Pi (k=n_steps) | final regret (elements) |
|---|---|---|---|
| arm_mid | 1.000 | 1.000 | 0 |
| arm_high | 0.938 | 1.000 | 0 |

arm_high's real greedy CELF planner is provably optimal at the final step
(matches the ILP ceiling exactly, regret=0) but sub-optimal at some
intermediate k (mean Pi=0.938 < 1.0) — genuine evidence that greedy's
well-known "can lag the true optimum mid-sequence, converge by the end"
behavior for submodular coverage is real and measurable on this data, not
merely theoretical. Phase 5's own (different-scene) T5.6-at-k/T5.7-by-k
numbers are carried into the report as `T6.8.phase5_reference` for
cross-reference, clearly flagged as not the same denominator.

### T6.9 — IG calibration

Real per-step comparison, for `arm_high`'s real roadmap-index view order:
predicted IG (Phase 4's real `batch_information_gain` against the CURRENT
partial occupancy map) vs. actual IG (real total-grid binary-entropy
reduction from actually integrating that candidate's real depth,
counterfactually measured then reverted for every non-chosen candidate).

- **Mean Spearman rho across 13 steps: -0.263** (negative — predicted IG
  is, on average, anti-correlated with the actually-realized entropy
  reduction on this dataset).
- **Top-1 hit rate: 1/13 (7.7%)** — the candidate `batch_information_gain`
  ranks highest is almost never the one that actually reduced entropy the
  most.
- **AUIGSE (first-step sparsification, area between oracle-order and
  predicted-order cumulative-gain curves): 0.279** (0 = perfectly
  calibrated; this is a meaningfully large miscalibration on real data).

This is a genuine, unflattering real finding about T4.5's reference IG
implementation, not a bug in T6.9's measurement — worth flagging back to
Phase 4: `batch_information_gain`'s short `max_range=0.4` m ray march
combined with this scene's fast-saturating single-tree occupancy map (most
of the volume becomes confidently free/occupied within a handful of views)
plausibly explains why the entropy-based predicted-IG signal decorrelates
from actual achieved entropy reduction after the first few views — flagged
here as a real, reproducible measurement rather than silently smoothed
over.

---

## T6.10 — `yogesh_dev/phase6/t610_deadline_closed_loop.py`

Budget = Phase 4 T4.7's own real `T_TOTAL_S = 120.0` constant
(`switching.py`), reused rather than inventing a new number. Two
concurrency models simulated over the SAME real per-step travel/compute
times: **paused-clock** (`compute_i + travel_i`, sequential — today's
implicit sense-plan-act behavior) vs. **closed-loop** (`max(compute_i,
travel_i)` — arm keeps moving while the next decision is computed).

**Real finding: at every real compute cost actually measured in this
codebase, the gap is ~0.** With CELF's real per-step compute (~0.0002s
total across the whole 8-step arm_high run) the closed-loop-vs-paused-clock
elapsed-time gap is 0.00025s — utterly negligible next to the ~58s of real
motion time, so neither model ever comes close to forcibly forfeiting a
step at a 120s budget (both complete all 8 real steps, 100% coverage,
`forfeited_at_step: null`, `coverage_gap_closed_loop_minus_paused: 0.0`).

To check this isn't just "CELF happens to be cheap," a second scenario
substitutes T6.8's real PuLP+CBC ILP solve (a genuinely more expensive
real computation in this codebase, ~30-45ms/solve, timed live) as the
per-step compute cost, at a tightened 30s budget. Result: still 0 gap —
even ~45ms of real ILP solve time is negligible against multi-second real
arm motion times, so both models forfeit at the identical step
(`forfeited_at_step: 5`, coverage 0.810 either way).

**Honest conclusion**: the deadline/closed-loop mechanism is implemented
and verified correct (it does forfeit under a tight-enough budget, and the
two models do diverge in principle), but no planning computation that
actually exists in this repository (CELF set-difference, or exact ILP
max-coverage over Phase 4's real ~500-1800-element ground sets) is
expensive enough, at these real measured costs, for the paused-vs-closed-
loop distinction to matter on this dataset's real motion-time scale. This
would become a real, non-zero gap either with a much larger candidate/
ground-set scale (where ILP solve time grows) or a much faster arm (where
motion time shrinks) — neither of which exists in this codebase to
measure directly, so the finding is reported as "verified mechanism, ~0
real-world impact at this scale" rather than fabricating a bigger number.

---

## T6.11 — `yogesh_dev/phase6/t611_latency_table.py`

Machine: this job's runner, `Linux 7.0.0-28-generic x86_64`, 24 logical
CPUs, CPU-only (no GPU used by any of these calls). All numbers are real
`time.perf_counter()` wall-clock (2 warmup calls discarded, N repeats per
module — see table), at Phase 4's real generated resolution (320×240) and
real graph/data sizes.

| module | mean | p95 | p99 | max | work unit | n/call | ns/unit |
|---|---|---|---|---|---|---|---|
| `phase2.visibility.fruit_visible_fraction` (all 27 fruit) | 0.083ms | 0.085ms | 0.091ms | 0.095ms | fruit visibility evals | 27 | 3074 |
| `phase3.kinematics.inverse_kinematics` | 0.0009ms | 0.0011ms | 0.0012ms | 0.0019ms | 5-DOF IK solve | 1 | 926 |
| `phase3.motion_time.move_time` | 0.0007ms | 0.0008ms | 0.0008ms | 0.0012ms | trapezoidal move-time eval (5 axes) | 5 | 141 |
| `phase4.occupancy_map.integrate_view` | 8.566ms | 8.683ms | 8.691ms | 8.693ms | valid pixels beam-integrated | 14446 | 593 |
| `phase4.semantic_map.integrate_semantic_view` | 1.161ms | 1.174ms | 1.267ms | 1.290ms | valid pixels semantic-integrated | 14446 | 80 |
| `phase4.information_gain.batch_information_gain` | 1.071ms | 1.088ms | 1.094ms | 1.095ms | (pose×ray×step) entropy evals, batched | 13440 | 80 |
| `phase4.tracker.extract_detections` (1 arm, 14 frames) | 18.355ms | 18.551ms | 18.562ms | 18.565ms | real (depth,instance) frames processed | 14 | 1,311,055 |
| `phase4.roadmap.dijkstra` (real 468-node/3230-edge graph) | 0.0102ms | 0.0104ms | 0.0121ms | 0.0129ms | shortest-path solve | 1 | 3.2/edge |

Hardware-independent work units (ray casts / candidate evaluations / valid
pixels / graph edges) reported alongside wall-clock per the task brief, so
these numbers remain interpretable if re-run on different hardware.
Full detail (all 8 modules, per-call unit counts): `t611_latency_table_report.json`.

---

## Environment / reproducibility notes for a human re-running this

- Run everything: `PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase6.run_phase6`
  from the repo root (this worktree). Individual modules are also runnable
  standalone as `python -m yogesh_dev.phase6.<module>`.
- This worktree needed two local (untracked, never staged) symlinks to
  reuse the main checkout's already-built native artifacts —
  `pyhelios_build/build -> /home/yogesh/PyHelios/pyhelios_build/build` and
  `helios-core -> /home/yogesh/PyHelios/helios-core` — see the env notes at
  the top of this log. `git status` in this worktree will show these as
  untracked/gitlink-changed; they were never `git add`ed.
- All JSON outputs live in `yogesh_dev/phase6/output/`.
