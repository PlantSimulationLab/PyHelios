# World Model for a 2×10 Apple Orchard — End-to-End Plan

**Status:** plan, not yet executed. Written 2026-07-30.
**Scope owner:** the unattended agent executing this file.
**Write scope:** `yogesh_dev/world_model/` only. Do not modify anything else in the repo.

---

## 0. What a world model is here, and what we are actually building

A world model is a *learned simulator*: given the current latent state of the orchard and an
action, it predicts the next observation. Once trained, it lets an agent "imagine" futures
(move the camera here → what do I see? advance three weeks → what does the canopy look like?)
without touching the real orchard, and lets a policy be trained entirely inside the imagined
rollouts.

We are building it in two coupled action channels, because agriculture genuinely has two
timescales and they need different data:

| Channel | Action | Timescale | What it predicts |
|---|---|---|---|
| **View / embodied** | camera pose delta along the row | seconds | next RGB-D view, occlusion changes |
| **Growth / agronomic** | `advanceTime(dt)` (+ management) | days–weeks | canopy structure, fruit development |

Helios is the data generator. The world model is the learned thing. **Helios is not the world
model** — this distinction must stay clear in all reporting.

---

## 1. Method decision (decided — do not re-litigate)

**Build an action-conditioned latent dynamics model in the DreamerV3 / RSSM family.**

Concretely: a recurrent state-space model with a deterministic GRU carry `h_t` plus a
stochastic discrete latent `z_t` (32 categoricals × 32 classes), a convolutional encoder over
RGB-D, and multiple decoder heads (RGB, depth, semantic mask, fruit-visibility scalar).

### Why this and not the alternatives

| Candidate | Verdict | Reason |
|---|---|---|
| **RSSM latent dynamics (DreamerV3)** | **Chosen** | Trains on 10⁴–10⁵ frames, which is exactly the scale we can generate. Natively action-conditioned. Supports multi-step imagination, which is the entire point. |
| Video diffusion (Genie / Sora-style) | Rejected for now | Needs 10⁵–10⁶ clips and multi-GPU-weeks. We have one RTX 5090. Revisit only if the RSSM saturates. |
| NeRF / 3D Gaussian Splatting | Rejected *as the world model* | These reconstruct one static scene. No action conditioning, no growth, no dynamics. **But** the repo already has a working gsplat pipeline — keep it as a *view-synthesis baseline* to beat (see W6). |
| Pure video prediction, no actions | Rejected | Cannot answer counterfactuals ("if I move here"), which is the only reason to build this. |
| Physics/PDE surrogate of Helios | Rejected | Helios is already the physics. Surrogating it adds no capability. |

### Honest limitation to state up front
An RSSM trained purely on Helios renders learns *Helios's* dynamics, not an orchard's. Every
claim in the final report must say "in simulation". Sim-to-real is out of scope; Phase 8's
digital-twin result (LiDAR twin preserved planner ranking, ρ = 1.0) is the closest existing
evidence that relative conclusions may transfer, and should be cited as such — not as proof.

---

## 2. What already exists in `yogesh_dev/` — reuse, do not rewrite

Phases 0–8 are complete. Read `FINDINGS_SUMMARY.md` and `COMPLETE_SETUP.md` before starting.
The following are directly reusable and **must** be reused rather than reimplemented:

| Module | What it gives you |
|---|---|
| `phase0/radiation_setup.py` | RGB bands + sun source, hand-tuned flux, scattering depth. Read its docstring — it documents the photometric saturation artifact honestly. |
| `phase0/radiation_cameras.py`, `phase0/pose_convention.py` | Camera rig and the pose convention validated to 0.71 px (independently re-confirmed at 1.41 px mean in Phase 1). **Do not invent a new pose convention.** |
| `phase1/label_maps.py` | `assign_semantic_class_ids()` — derives an int `semantic_class_id` from the string `object_label`. Required, because string fields silently produce an all-background label map. |
| `phase1/depth_export.py` | EXR depth write/read + stats. |
| `phase1/transforms_export.py` | gsplat-compatible `transforms.json`. |
| `phase1/noise_model.py` | Seeded RGB-D noise (for the sim-to-real robustness ablation only). |
| `phase1/ground_truth.py` | Fruit ground truth export, `fruitID` object data. |
| `phase8/canopy_factory.py` | Seeded canopy construction with disjoint seed streams, leaf/fruit thinning. **This is the starting point for the orchard factory.** |

Standing repo-wide blocker, still true: **`CollisionDetection` is not exposed in PyHelios**
(`castRaysSoA`, `findCollisions`, `buildBVH`). Do not plan around having it. Occlusion must be
derived from renders / label maps, as Phase 2 did.

---

## 3. Verified facts and API recipes (measured on this machine, 2026-07-30)

These were measured directly before writing this plan. Trust them, but re-verify in W0 and
report any discrepancy rather than silently adapting.

**Hardware / env**
- GPU: NVIDIA RTX 5090, 32 GB. Radiation backend: **OptiX 8.1**, confirmed working.
- Disk: 2.6 TB free.
- **Two-env split (unavoidable):** PyHelios works in the `base` conda env. `torch` is **not**
  installed there. `torch 2.7.0+cu128` with CUDA available lives in the **`gsplat`** env.
  → **Generate data in `base`, train in `gsplat`, bridge via files on disk.** Do not attempt to
  install torch into `base`.

**Scene scale (measured)**
- Single apple tree, age 365 d: 11,963 primitives, 0.2 s build, 1.98 m tall.
- Single apple tree, age 720 d: 45,315 primitives, 1.4 s build, 2.72 m tall, 6.02 m² leaf area.
- **Full 2×10 orchard at age 540 d: 756,833 primitives, 14.1 s build.** (Expect ~900 k at 720 d.)

**Render throughput — the single most important number (measured on the full 2×10 orchard)**

Cameras amortize across one radiative solve. Registering many cameras and solving once is
dramatically cheaper than solving per camera:

| Cameras registered | Solve time (3 bands) | Per image |
|---|---|---|
| 1 | 3.45 s | 3.450 s |
| 4 | 3.52 s | 0.880 s |
| 16 | 3.95 s | 0.247 s |
| 32 | 4.13 s | 0.129 s |
| 64 | 4.76 s | 0.074 s |
| **128** | **6.09 s** | **0.048 s** |

**This is a 72× throughput difference between naive and batched rendering. The dataset
generator must batch cameras.** It has not saturated at 128 — W1 should probe 256 and pick the
best point that fits in GPU memory.

Readback is not a bottleneck: `getCameraPixelData` 0.021 s/image, `writeCameraImage`
0.008 s/image, `writeDepthImageDataEXR` 0.002 s/image.

**Verified gotchas (each one cost real debugging time — do not rediscover them)**

1. **Camera bands need non-zero scattering depth.** With the default `scatteringDepth = 0`,
   `runBand()` skips the camera pass entirely: RGB pixel data stays empty *and*
   `writeDepthImageDataEXR` fails with `"Depth data for camera 'X' does not exist"`.
   → Call `setScatteringDepth(band, >=1)` for every camera band.
2. **Depth is a side effect of the pixel-labeling pass**, stored in global data
   `camera_<label>_pixel_depth`. It only exists after a successful camera solve (see 1).
   `Visualizer.getDepthMap()` is **broken upstream** (returns only {0.0, 255.0}) — Phase 0
   confirmed this against helios-core's own `\todo`. Use the RadiationModel EXR path only.
3. **Setting `reflectivity_<band>` / `transmissivity_<band>` requires `disableEmission(band)`**,
   otherwise `runBand()` aborts: *"emissivity, transmissivity, and reflectivity must sum to 1"*.
4. **`optionalOutputObjectData` must be called BEFORE building plants**, and only accepts these
   labels: `age, rank, plantID, plant_name, plant_height, plant_type, phenology_stage, leafID,
   peduncleID, closedflowerID, openflowerID, fruitID, carbohydrate_concentration` (or `"all"`).
   `object_label` is **not** valid here — it's primitive data, set automatically.
5. **Growth is stochastic and unseeded upstream.** Always call
   `context.seedRandomGenerator(seed)` before building, or two "identical" builds differ
   (Phase 2 measured 97 vs 72 fruit).
6. **`getAllPlantUUIDs()` segfaults if called after `context.deleteObject()`** removed any of
   that plant's primitives. Cache UUID lists *before* any thinning/pruning and never re-query.
7. **At age 540 d the apple model produces NO fruit** (verified: organ counts were leaf 28,490 /
   shoot 80,290 / petiole 12,432 / peduncle 10,206 / **fruit 0**). Phases 1 and 8 used **720 d**,
   which does fruit. → **Any growth-stage schedule must reach ≥ ~650–720 d to contain fruit**,
   and W0 must empirically map age → fruit count before fixing the schedule.

**RGB photometry — a real problem, and a verified fix**

Phase 0 documented a saturation artifact where canopy pixels clamp to a fixed value regardless
of flux, making raw `writeCameraImage` output blown-out white. This was reproduced (image was
unusable) **and then solved**. The working recipe, verified end-to-end:

1. Assign per-organ optical properties via `filterPrimitivesByData(uuids, "object_label", organ)`
   then `setPrimitiveDataFloat(matched, "reflectivity_<band>", rho)` / `"transmissivity_<band>"`.
2. Call `disableEmission(band)` for every band (see gotcha 3).
3. Read **raw float** pixels with `getCameraPixelData` — do **not** rely on Helios's internal
   sRGB clamp.
4. Apply your own exposure normalisation (a fixed percentile scale) + sRGB transfer, then quantise
   to uint8.

With this, band ratios came out physically sensible for foliage (green ≈ 2.2× red ≈ 3.7× blue)
and the render showed green leaves and brown branches instead of white blobs. **Use a single
fixed exposure scale across the whole dataset, computed once — never per frame**, or the world
model will learn the exposure controller instead of the orchard.

Open sub-issue to handle in W1: sky/background renders as 0 (black) because no sky radiance is
present in these bands. Decide and document one of: composite a fixed sky colour using the
`NaN`/no-hit mask from the label map, or add sky radiance. Do not leave it black by accident.

---

## 4. The simulator: 2 rows × 10 trees

Fixed geometry for all experiments:

- **Layout:** 2 rows, 10 trees per row (20 trees), via
  `buildPlantCanopyFromLibrary(canopy_center=vec3(0,0,0), plant_spacing=vec2(1.5, 3.5),
  plant_count=int2(10, 2), age=...)`.
- **In-row spacing 1.5 m, row spacing 3.5 m.** Row axis = **x**, across-row = **y**.
  Orchard extent ≈ 13.5 m × 3.5 m.
- **Model:** `apple`. Also build the `apple_fruitingwall` variant as a documented alternative —
  Phase 8 measured 29% → 4% canopy interpenetration at 1.5 m spacing, so it is the more
  realistic trellised orchard. **Report both; default to `apple` for the main dataset** so
  results stay comparable to Phases 0–8, and treat `apple_fruitingwall` as an ablation.
- **Seeding:** one disjoint seed stream per orchard instance, following
  `phase8/canopy_factory.py`'s existing scheme.

---

## 5. Action spaces

**View actions `a_view` (continuous, 4-D):** `(Δx along row, Δy across row, Δz height, Δyaw)`.
Trajectories are generated as camera paths, then the *action* recorded for step *t* is the pose
delta from *t* to *t+1*. Sample three trajectory families:
- **row traversal** — drive down the inter-row lane (the realistic robot path),
- **orbit** — circle an individual tree,
- **random walk** — bounded jitter, for coverage of the action space.

Because the scene is static within a growth stage, **one 128-camera batch = one full 128-step
trajectory for the cost of a single solve.** This is the core efficiency trick of the whole plan.

**Growth actions `a_grow` (scalar):** `dt` days passed to `plantarch.advanceTime(dt)`.
⚠️ **`advanceTime` cost on a 20-tree canopy is UNMEASURED.** W0 must measure it before the
dataset schedule is fixed; if it is prohibitive, reduce the number of growth stages or the tree
count for the growth channel *and say so explicitly* rather than quietly dropping the channel.

**Management actions `a_manage` (optional, only if time allows):** leaf/fruit thinning via the
existing `phase8/canopy_factory.py` thinning functions. Respect gotcha 6.

---

## 6. Task breakdown

Each task lists its deliverable and its acceptance criterion. **A task is not done until its
acceptance criterion has been checked with real output.**

### W0 — Orchard factory + measurement (foundation)
- `orchard.py`: seeded 2×10 orchard builder wrapping `phase8/canopy_factory.py`; per-organ
  optical properties; `assign_semantic_class_ids()` applied; cached UUID lists.
- **Measure and record:** per-orchard build time, primitive count, `advanceTime(dt)` cost at
  20-tree scale, and an **age → fruit-count curve** (sample ages ~400–900 d) to fix the growth
  schedule (gotcha 7).
- *Acceptance:* two builds with the same seed produce identical primitive counts; two different
  seeds differ. Age→fruit curve written to JSON.

### W1 — Batched observation rig
- `render.py`: register N cameras → one solve → N × (RGB uint8, depth float32, semantic mask,
  instance mask, 4×4 pose). Fixed global exposure. Sky/background handled explicitly.
- Re-verify the camera-batching table above and probe N = 256.
- *Acceptance:* a rendered contact sheet that a human can look at and see a recognisable
  orchard row; depth EXR with sane min/max; semantic mask whose class histogram matches the
  organ primitive counts from W0.

### W2 — Action spaces and trajectory samplers
- `actions.py`: the three view-trajectory families, growth schedule, action encoding/decoding.
- *Acceptance:* trajectories stay inside the orchard bounds and inside the inter-row lane;
  replaying recorded actions from the start pose reproduces the recorded poses to < 1e-6.

### W3 — Dataset generation
- `generate.py`: episodes → compressed shards + `manifest.json`. Store at **128×128** for
  training; keep a small full-resolution subset for qualitative evaluation.
- **Target scale:** ~40 orchard seeds × ~8 growth stages × 128 views ≈ **40 k frames**
  (≈ 4 GB). Scale up if W0/W1 timings allow; scale down and *report the reduction* if not.
- **Split by orchard seed, never by frame** — frames within a trajectory are near-duplicates and
  a random split would leak. (Phase 6 caught exactly this class of bug in the gsplat train/test
  split.)
- *Acceptance:* regenerating one shard with the same seed is byte-identical; train/val/test seed
  sets are provably disjoint.

### W4 — World model implementation (`gsplat` env)
- `rssm.py`: encoder, RSSM core (deterministic GRU + discrete stochastic latent), decoder heads
  (RGB, depth, semantic, fruit-visibility), KL balancing with free bits.
- `train.py`: sequence batching, symlog targets, checkpointing, resumability.
- *Acceptance:* overfits a single trajectory to near-zero reconstruction loss. If it cannot, the
  model is wrong — fix it before running the full training.

### W5 — Training
- Smoke run first (small, few hundred steps), then the full run. Log curves to disk.
- *Acceptance:* validation loss curve saved; checkpoints resumable.

### W6 — Evaluation
Evaluate what the model is *for* — multi-step imagination, not single-step reconstruction:
- **Open-loop rollout quality vs horizon:** RGB PSNR/LPIPS, depth MAE, semantic mIoU at
  t+1, t+5, t+10, t+25.
- **Action fidelity:** does a commanded pose delta produce the correct viewpoint change?
- **Counterfactual growth:** predicted canopy at +N days vs Helios ground truth.
- **Required baselines** (a world model that doesn't beat these is not working):
  1. copy-last-frame, 2. no-action ablation (actions zeroed — proves actions are actually used),
  3. the existing gsplat pipeline as a view-synthesis reference.
- *Acceptance:* every number is produced by a script that can be re-run; the no-action ablation
  is **strictly worse** than the full model, or the model is ignoring actions and this must be
  reported as a negative result.

### W7 — Reporting
- `WORLD_MODEL_LOG.md` (what was done, chronologically, including dead ends),
  `WORLD_MODEL_STATUS.md` (task-by-task status), `FINDINGS.md` (what was actually learned:
  real numbers, real failures).
- Update `yogesh_dev/COMPLETE_SETUP.md` with a short pointer to this work.

---

## 7. Data schema

Per frame:
```
rgb        uint8   [128,128,3]    tonemapped, fixed global exposure
depth      float16 [128,128]      metres; -1 = no hit
semantic   uint8   [128,128]      0 other,1 fruit,2 leaf,3 shoot,4 petiole,5 peduncle,255 sky
instance   int32   [128,128]      fruitID, -1 = not fruit
pose       float32 [4,4]          camera-to-world, Phase 0 convention
a_view     float32 [4]            (dx,dy,dz,dyaw) to the NEXT frame
a_grow     float32 [1]            days advanced to the NEXT frame (0 within a trajectory)
```
Per episode: orchard seed, tree model, age, sun zenith/azimuth, trajectory family, exposure scale.

---

## 8. Compute budget (extrapolated from measured numbers)

| Stage | Estimate | Basis |
|---|---|---|
| Orchard builds (40 seeds) | ~10 min | 14.1 s measured × 40 |
| Growth advances | **unknown** | must be measured in W0 |
| Rendering 40 k frames | ~35 min | 0.048 s/img at 128 cameras, measured |
| Image writes | ~7 min | 0.010 s/img measured |
| Training | hours (GPU-bound) | RTX 5090 |

Rendering is **not** the bottleneck once batched — training is. This inverts the assumption
from earlier phases (where Phase 8 estimated ~6.8 h of render time) and is a direct consequence
of the camera-batching finding.

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| `advanceTime` too slow at 20 trees | Measure in W0 *first*; cut growth stages, not honesty. |
| Growth channel has far fewer samples than view channel | Weight the losses; report the imbalance. |
| RGB exposure drift across the dataset | One fixed global scale, computed once in W1. |
| Model ignores actions | The no-action ablation in W6 exists precisely to catch this. Report it either way. |
| Two-env split causes drift | Data on disk is the only interface; no pyhelios import in training code. |
| Fruit absent from the dataset | W0's age→fruit curve gates the growth schedule. |

---

## 10. Rules for the executing agent

1. **Write only under `yogesh_dev/world_model/`.** Do not modify `apple_tree.py`,
   `apple_tree_gaussian_splatting.py`, `pyhelios/`, or `helios-core/`. If an upstream fix is
   needed, write the patch as a documented `.md`/`.patch` under your own folder.
2. **Seed everything.** Every stochastic step gets an explicit, recorded seed.
3. **Report honestly.** If something is blocked, broken, or reduced in scale, say so plainly
   with the evidence — that is the established standard for every phase in `yogesh_dev/`, and
   `FINDINGS_SUMMARY.md` is full of negative results reported as such. A negative result that
   is real beats a positive result that is dressed up.
4. **Measure, don't assume.** Every number in a report must come from a script that can be
   re-run.
5. **Notify on completion or failure:** use `notify_slack()` from `notify_slack.py` at the repo
   root, wrapping the long-running entrypoints in try/except.
6. Commit work to the current branch as you go, in coherent commits.
