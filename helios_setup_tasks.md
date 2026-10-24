# Helios / PyHelios Setup — Task List

Ordered work plan to get from the current `apple-tree-cameras` branch to a rig that can run every experiment in `active_vision_design.md`.

**Current state (audited at `PyHelios @ apple-tree-cameras`, `4f4ccc0`):**
- 3 apple trees built via `PlantArchitecture` with fruit-aware collision avoidance ✓
- 3 camera *positions* exist, but as `Visualizer` (OpenGL rasterizer) cameras — **not** `RadiationModel` cameras
- Rendering path is `Visualizer.printWindow()` → PNG. No depth, no per-pixel semantics except a flat-color re-render + nearest-color match
- gsplat training pipeline works end to end
- No ground truth exported at all

**Where this is going:** the `Visualizer` path stays — it becomes your fast Tier-B renderer. The `RadiationModel` path gets added alongside it as Tier C (physically-based RGB + depth + exact per-pixel labels). Both are needed. Don't delete `apple_tree_cameras.py`.

Legend: **[PY]** pure Python, **[BIND]** needs a new PyHelios binding, **[C++]** needs a helios-core patch, **[BLOCKER]** blocks a whole phase.

---

## Phase 0 — Radiation camera migration and honest benchmarking

This is the phase you asked about. Note that a radiation camera is *not* a drop-in replacement for a Visualizer camera: the radiation model needs **bands and light sources** configured before `runBand()` will produce anything but black.

### T0.1 — Add the radiation band + source stack **[PY]**
Cameras alone render nothing. Minimum viable setup:
```python
radiation = RadiationModel(context)
for band, (lo, hi) in {"red": (600, 700), "green": (500, 600), "blue": (400, 500)}.items():
    radiation.addRadiationBand(band, lo, hi)
sun = radiation.addSunSphereRadiationSource(radius=..., zenith=..., azimuth=..., ...)
for band in ("red", "green", "blue"):
    radiation.setSourceFlux(sun, band, flux)
    radiation.setDiffuseRadiationFlux(band, diffuse_flux)
    radiation.setScatteringDepth(band, 1)     # start at 1; raise only if leaves look wrong
```
Decide early whether you want physically meaningful radiometry (set source spectra properly, `setSourceSpectrum`) or just plausible RGB. For perception experiments, plausible RGB is enough; for anything claiming radiometric realism you need real spectra. **Write down which you chose.**

### T0.2 — Define the 3 cameras as radiation cameras **[PY]**
Replace the `CAMERA_RIGS` dict in `apple_tree_cameras.py` with `addRadiationCamera` calls. Critical parameter notes:

| Parameter | Value | Why |
|---|---|---|
| `lens_diameter` | **`0.0`** | Default is `0.05`, which enables a thin-lens depth-of-field blur. Any non-zero value corrupts geometric experiments and makes depth ambiguous. You want a pinhole. |
| `HFOV` | derived from your calibration | `CameraProperties` takes **horizontal** FOV; your current `FOV_DEG` is **vertical** (derived from `fy`, `cy`). Convert: `HFOV = 2·atan(aspect · tan(VFOV/2))`. Getting this wrong silently rescales the whole scene. |
| `FOV_aspect_ratio` | `0.0` | Auto-computes vertical FOV from resolution. |
| `camera_resolution` | start at `(640, 480)` | Not your 1957×1286 calibration. See T0.5. |
| `antialiasing_samples` | **`1–4`** for loop renders | The Helios tutorials use 100. That is a 25–100× cost multiplier you do not need for a closed loop. Reserve high AA for final figures. |

Keep all three cameras registered simultaneously — `runBand()` iterates every registered camera in a single dispatch, so your 3-arm rig costs roughly one render, not three.

### T0.3 — Verify the radiation camera's pose convention empirically **[PY] [BLOCKER for gsplat + all geometry work]**
Do **not** assume the radiation camera uses the same convention as `Visualizer`. Your `look_at_view_matrix()` was reverse-engineered against the Visualizer's hardcoded world-up `+Z`. The radiation camera stores position + lookat only, with its own internal up convention, and **no matrix getter exists**.

Test: place 5–10 spheres at known world coordinates spanning the frame, render, and check that each sphere's image centroid matches your projected `K · [R|t] · X`. Reprojection error should be sub-pixel. If it is not, the convention differs and every downstream pose is wrong.

⚠️ **Roll is not representable.** The radiation camera has no up-vector; roll is implicit and EXIF roll is hardcoded to 0. Your 5-DOF chain (3 linear + pan/tilt) does not produce roll, so this is fine — but confirm your kinematics never introduces it, and record the assumption.

### T0.4 — Structure the render loop correctly **[PY]**
```python
radiation.updateGeometry()                # ONCE, outside the loop — ~0.5–1.3 s, only needed when geometry changes
for pose in poses:
    for cam, p in zip(cams, pose):
        radiation.setCameraPosition(cam, p.eye)
        radiation.setCameraLookat(cam, p.lookat)
    radiation.runBand(["red", "green", "blue"])   # ONE call, all bands — docs report 2–5× over sequential
    rgb = radiation.getCameraPixelData(cam, "red")   # in-memory, no file I/O
```
Two mistakes to avoid: calling `updateGeometry()` per view, and calling `runBand()` once per band.

### T0.5 — Benchmark honestly (this is E0, and it decides your architecture) **[PY] [BLOCKER]**
Published Helios timings disagree by an order of magnitude (11 s/image in Lei & Bailey vs ~1 s in `Benchmarks.dox`) because they measure different things. Measure yours:

| Path | What to time | Expect |
|---|---|---|
| Tier A — geometric ray casts | *(blocked, see T0.6)* | ms |
| Tier B — `Visualizer.plotUpdate()` + `getDepthMap()` | per view | ~30 Hz |
| Tier C — `runBand(["r","g","b"])`, 640×480, AA=1, 3 cameras, scattering depth 1 | per pose | **???** |

Also record primitive count per tree (`len(getAllPlantUUIDs)`) and total. Then sweep resolution and AA to get a cost curve. **Everything downstream — how many candidate viewpoints you can afford, whether the loop is 1 Hz or 10 Hz — falls out of this number. Do it before writing any planner code.**

### T0.6 — Decide the Tier-A ray-casting story **[BIND] [BLOCKER for Phase 4]**
`CollisionDetection` — the BVH ray tracer with `castRaysSoA()` / `castRaysGPU()` — **is not exposed in PyHelios.** It is explicitly excluded (`pyhelios/config/plugin_metadata.py`: *"CollisionDetection dependency handled at C++ level, not exposed in Python API"*).

This is your single biggest infrastructure gap. Information-gain evaluation is 93% of the planning cycle in comparable systems, and it is exactly what `castRaysSoA` is for. Three options:

1. **Write the binding** (recommended). Expose `castRaysSoA`, `castRaysGPU`, `findCollisions`, `findCollisionsWithinDistance`, `buildBVH`/`setStaticGeometry`. Highest effort, unblocks everything, and is a genuinely good upstream PR.
2. **Write the sim loop in C++** and drive it from Python only at the experiment level.
3. **Interim hack:** use `Visualizer.getDepthMap()` as a poor-man's depth-only ray cast at ~30 Hz. Gets you moving but gives no per-primitive UUID and no arbitrary-origin rays, so it cannot do fruit-outward visibility (Phase 2).

Pick one now — it determines Phase 4's shape.

### T0.7 — Keep the Visualizer path as Tier B **[PY]**
Add `Visualizer.getDepthMap() -> (List[float], w, h)` to the existing rig. It already exists and is currently unused. Free depth at frame rate for debugging and fast rollouts.

---

## Phase 1 — Ground truth export

**Highest value-per-line work in the whole plan.** Fifteen lines turns the repo from a rendering demo into an evaluation harness, and it unlocks most of Tiers 1–4 in the design doc.

### T1.1 — Enable optional object data **[PY] [BLOCKER for T1.2, T1.3]**
`fruitID`, `leafID`, `plantID`, `phenology_stage` are **not written by default**. After building the plants:
```python
plantarch.optionalOutputObjectData(["plantID", "fruitID", "leafID", "rank", "age", "phenology_stage"])
```
Verify with `context.listObjectData(objID)` on one fruit object that the labels actually appear — do not assume.

### T1.2 — Export per-fruit ground truth **[PY]**
```python
fruit_uuids = context.filterPrimitivesByData(all_uuids, "object_label", "fruit")
fruit_objs  = context.getUniquePrimitiveParentObjectIDs(fruit_uuids)
for oid in fruit_objs:
    center = context.getObjectCenter(oid)
    bbox   = context.getObjectBoundingBox([oid])
    area   = sum(context.getPrimitiveArea(u) for u in context.getObjectPrimitiveUUIDs([oid]))
```
Write `fruit_ground_truth.json`: object ID, `plantID`, centroid, bounding box, equivalent diameter, surface area, primitive UUID list. This is `𝓕` in §7 of the design doc.

### T1.3 — Export per-pixel semantic and instance maps **[PY]**
Replace the flat-color-render + nearest-color-match hack entirely:
```python
sem  = radiation.getPrimitiveDataLabelMap(cam, "object_label")   # → (H,W) float, NaN = background
inst = radiation.getObjectDataLabelMap(cam, "fruitID")           # → (H,W), per-apple instance IDs
```
No threshold, no antialiasing erosion, no color ambiguity. This directly fixes issue #4 from the code review and gives you free instance segmentation.

⚠️ **Performance caveat:** both go through a temp file + `np.loadtxt` — **text parsing**. At 640×480 that is ~300k floats parsed per call. Fine for dataset generation, too slow for a closed loop. If you need these inside the planner, add a binary/in-memory binding **[BIND]**.

### T1.4 — Export depth **[PY]**
`writeDepthImageDataEXR(camera_label, base)` gives lossless float depth. There is **no in-memory depth getter** in PyHelios for the radiation camera (only the three file writers), and `getGlobalData` cannot return float arrays, so the `camera_<label>_pixel_depth` global-data path is **not reachable from Python today**. Either accept the EXR round-trip (needs `imageio`/`OpenEXR`) or add the binding **[BIND]**.

### T1.5 — Export camera intrinsics/extrinsics per view **[PY]**
Extend `transforms.json` with the radiation camera's actual `HFOV`, resolution, and derived `K`, plus the world-to-camera matrix validated in T0.3. Keep the gsplat-compatible format so the existing pipeline still runs.

### T1.6 — Add an RGB-D noise model **[PY]**
Helios depth is perfect. Real RealSense/ZED depth over foliage has flying pixels, mixed pixels at depth discontinuities, holes on specular leaves, and stereo shadowing. **Perfect depth will flatter any fusion pipeline you build** — specifically it removes the artifact that triggers carving-through-leaves. Write a noise model that at minimum injects depth-edge mixed pixels and range-dependent noise, and make it a toggle so you can quantify its effect. This is itself a small paper contribution.

---

## Phase 2 — Visibility ground truth (AVUB / NVE)

Blocked on T0.6 (needs arbitrary-origin ray casting from fruit surfaces).

### T2.1 — Per-fruit visible-fraction from a given pose **[PY, needs T0.6]**
Implement `vis_i(v)` from §7.1: for each fruit surface primitive, area-weighted indicator of (unoccluded ∧ front-facing ∧ in-frustum), optionally weighted by incidence angle and range. **Weight by primitive area, not pixel count** — pixel fraction conflates visibility with distance.

Cheap validation: cross-check against `getObjectDataLabelMap(cam,"fruitID")` pixel counts. They should correlate strongly; systematic disagreement means a bug in one of them.

### T2.2 — Accumulated visibility over a trial **[PY]**
`v_i_max(t)` = **union** over primitives seen by at least one camera at any time — not a max over views. A fruit seen 40% left + 40% right is 80% covered.

### T2.3 — Reachable view set 𝒱_reach **[PY, needs Phase 3]**
Densely sample the 5-DOF joint space → FK → camera pose → reject self-collision and canopy collision. Cache per canopy. **Every oracle and upper bound in the evaluation depends on this set.**

### T2.4 — Compute AVUB and AVUB^∞ **[PY, needs T2.1 + T2.3]**
`AVUB_i` = fraction of fruit *i*'s surface visible from **any** pose in 𝒱_reach. Also compute `AVUB^∞` with an unconstrained free-flying camera. The ratio `AVUB / AVUB^∞` is your hardware-design metric — how much visibility the 5-DOF arm design is leaving on the table.

### T2.5 — Fruit achievability classes **[PY]**
Tag each fruit *observable* (`AVUB_i > 0`), *sizeable* (`AVUB_i > γ_size`), *graspable* (approach cone clear). Recall must be reported against the **observable** denominator.

### T2.6 — Validate the proposal's occlusion-regulation module against AVUB **[PY]**
The WTFRC proposal's occlusion control adds/removes leaves to hit a target per-fruit occlusion. Check that the target occlusion level and the resulting AVUB distribution actually move together — that is the calibration that makes your factorial sweep meaningful.

---

## Phase 3 — Kinematics and the reachability roadmap

Helios has **zero** kinematics support (no FK/IK, no joint limits, no Jacobians, no collision-checked motion). All of this is yours to write; Helios only ever needs the resulting camera pose.

### T3.1 — 5-DOF forward kinematics **[PY]**
3 prismatic (left-right, up-down, in-out) + pan + tilt → camera pose. Trivial to hand-roll for this chain; no need for Pinocchio/KDL. Include joint limits and the workcell's per-arm vertical band.

### T3.2 — Inverse kinematics **[PY]**
For a 3-prismatic + pan/tilt chain, position is decoupled from orientation, so IK is closed-form: solve the linear axes for camera *position*, then pan/tilt for *look direction*. No solver needed.

### T3.3 — Execution-time model **[PY]**
Trapezoidal velocity profiles per axis. Record real max velocity/acceleration for the linear stages and the gimbal separately — **the cost asymmetry between them is the basis of the whole nested-planner idea** (§3.1 of the design doc). Get real numbers from the hardware if you can.

### T3.4 — Build the roadmap **[PY, needs T0.6 for collision]**
Nodes = discretized reachable 5-DOF poses per arm with IK cached. Edges = k-NN in joint space, **weight = actual execution time** from T3.3. Precompute once per cart position. This turns planning into graph search and keeps IK out of the loop.

### T3.5 — Arm and workcell collision geometry **[PY]**
Add arm links as Helios geometry (boxes/tubes) so `findCollisions` / `findCollisionsWithinDistance` can check arm-vs-canopy. Enforce non-overlapping vertical bands per arm so arm-arm collision is structurally impossible.

---

## Phase 4 — Map and planner

### T4.1 — Occupancy map with explicit unknown **[PY/C++, needs T0.6]**
Three-state (occupied / free / **unknown**), log-odds, with a beam sensor model covering range *and* angular uncertainty. Dual resolution: ~2 cm global + ~3 mm attention regions around fruit clusters. Decide build-vs-fork now (UFOMap semantics + wavemap beam model on GPU is a real project; `nvblox`'s occupancy/freespace layers are the pragmatic fallback — but use its occupancy layer, **not** its TSDF).

### T4.2 — Resolution vs thin-structure calibration **[PY]** *(this is E1)*
Sweep voxel size against branch recall by diameter class (<5, 5–10, 10–20, >20 mm) and against map update time. Apple leaf lamina is 0.15–0.3 mm, twigs 2–10 mm, trellis wire 2–3 mm. **Every published mapping benchmark you will read was measured at 5 cm.** This sweep produces the operating point everything else is built on.

### T4.3 — Semantic layer **[PY]**
Per-voxel class posterior fused from `getPrimitiveDataLabelMap` through known poses.

### T4.4 — Apple instance track database **[PY]**
"Seen at least once" must be defined over **tracked fruit instances**, not voxels — otherwise you double-count under registration error. With `fruitID` you have ground-truth association for free in sim, so build the tracker *and* the oracle association simultaneously and measure the tracker against it (IDF1, ID switches — novel in this domain).

### T4.5 — GPU-batched information gain **[C++/CUDA, needs T0.6]**
The single highest-leverage engineering decision. Comparable systems spend 93% of the planning cycle here, it is embarrassingly parallel, and no agricultural NBV paper has done it because they are all on CPU OctoMap.

### T4.6 — Explore planner **[PY]**
Quality-constrained: minimize time subject to coverage ⊇ reachable surface. Submodular max-coverage + CELF lazy evaluation + receding-horizon path search over the T3.4 roadmap. Time-normalized utility.

### T4.7 — Switching criteria **[PY]**
All three, in disjunction: frontier exhaustion; marginal-value-rate threshold η set to the predicted exploit-phase rate; Good–Turing coverage `Ĉ = 1 − f₁/n > 0.95` over discovered fruit instances. Plus a hard cap `ρ·T_total` with ρ swept.

### T4.8 — Exploit planner **[PY]**
Budget-constrained submodular team orienteering. Value `F(A) = Σ w_i φ(Σ q_i(ξ))` with `φ(z) = 1 − e^{−z}`. Cost-benefit greedy + CELF.

### T4.9 — Three-arm coordination **[PY]**
Sequential greedy with randomized arm ordering. Verify the objective is genuinely submodular — log-det is, plain trace is not, and a modular objective will make all three arms converge on the same view.

### T4.10 — Gimbal-only local refinement **[PY]**
The nested inner loop. Either gradient ascent on a differentiable semantic utility over pan/tilt, or a 3D-Move-to-See finite-difference gradient across your three physical cameras. Gimbal motion is nearly free — this should be a large, cheap win.

---

## Phase 5 — Baselines and oracles

Build these **before** tuning your planner, so you cannot fool yourself.

- **T5.1** Single fixed camera, one view (absolute floor) **[PY]**
- **T5.2** Static 3-camera rig, no arm motion — *the realistic commercial alternative* **[PY]**
- **T5.3** Boustrophedon raster over the 3 linear axes — *the engineering-practical competitor, absent from the entire NBV literature* **[PY]**
- **T5.4** Random reachable views (denominator of Π) **[PY]**
- **T5.5** Nearest-frontier + Ericson "distance advantage" — five lines, **may beat your planner in the explore phase** **[PY]**
- **T5.6** Greedy oracle: at each step evaluate every candidate in 𝒱_reach against ground truth, pick the truly best (numerator of Π) **[PY]**
- **T5.7** Offline ILP set-cover optimum for k ≲ 8 — the true ceiling **[PY]**
- **T5.8** All-reachable-views fusion (sensor + workspace ceiling) **[PY]**
- **T5.9** Perfect-perception ablation: feed GT detections to the planner, separating planning error from perception error **[PY]**

---

## Phase 6 — Metrics harness

- **T6.1** Fix the train/test split. Currently `i % 8 == 0` with `num_cols = 8` selects **column 0 only** in every config (3/24, 9/72, 36/288 views, all at one grid edge). Use a seeded random permutation. **[PY]**
- **T6.2** Fix masked PSNR. After masking, most pixels are constant background and a model rendering nothing scores well. Report PSNR restricted to GT-fruit ∪ rendered-alpha. **[PY]**
- **T6.3** Occlusion-aware mask supervision. Render the fruit class alone → unoccluded silhouette; subtract the fruit-visible mask from the full scene → occluded-fruit pixels. **Exclude those from the loss** instead of supervising them as background. Currently the pipeline teaches the splat that occluded apples are absent. **[PY]**
- **T6.4** Occlusion-conditioned detection recall, stratified by GT occlusion decile **[PY]**
- **T6.5** Semantically stratified F-score at class-specific τ (fruit 5 mm, branch 10 mm, wire 5 mm, leaf 10 mm). No ICP alignment — you know the exact frame. **[PY]**
- **T6.6** Three-state occupancy confusion matrix; report `M(free|occ)` restricted to wires and branches as the safety-critical miss rate **[PY]**
- **T6.7** Discovery curve against three x-axes (view index, joint-space path length, wall-clock incl. compute) + AUC + time-to-90% **[PY]**
- **T6.8** Oracle-normalized planning score Π and per-step regret **[PY]**
- **T6.9** IG calibration: Spearman ρ per step, top-1 hit rate, sparsification curve, AUIGSE **[PY]**
- **T6.10** Deadline-enforced closed-loop mode — arm keeps moving during planning, planner forfeits if over budget. Report the gap vs paused-clock. **[PY]**
- **T6.11** Per-module latency table with mean/p95/p99/max at a stated resolution, plus a hardware-independent work unit (ray casts, candidate evaluations) **[PY]**

---

## Phase 7 — Foundation model diagnostics (D1–D6)

Needs Phase 0 + Phase 1 only. **Can run in parallel with Phases 2–4** — this is the cheapest self-contained paper in the plan.

- **T7.1** Helios → WAI dataset writer (MapAnything's format). One loader serves every later experiment and can fine-tune VGGT/π³/MoGe-2 as guests. **[PY]**
- **T7.2** **D1 — pose-conditioning ablation.** Four conditions: images only / +intrinsics / +intrinsics+extrinsics / +depth. On MapAnything, DA3, π³, VGGT as anchor. *This measurement does not exist in the literature.* **[PY]**
- **T7.3** **D2 — baseline-angle sweep.** Arc width 5°→360°, with and without pose conditioning. Theory predicts sharp collapse at small disparity when uncalibrated, none when posed. **Likely your core figure.** **[PY]**
- **T7.4** **D3 — LAI sweep on a fixed branch skeleton**, measuring branch-geometry error and attention effective rank. Uses the proposal's occlusion-regulation module. **[PY]**
- **T7.5** **D4 — thin-structure recall by diameter class.** Benchmark to beat: <55% below 10 mm. **[PY]**
- **T7.6** **D5 — honest classical baseline.** Classical MVS / TSDF fusion / PromptDA depth completion with exact poses. If classical wins, that *is* the finding. **[PY]**
- **T7.7** **D6 — metric-scale integrity.** Canopy volume, leaf area, fruit diameter, internode length — metrically correct, not just plausible. **[PY]**

---

## Phase 8 — Scale-up

- **T8.1** Parameterize canopy generation by seed; build dev and test canopy sets with **disjoint** seeds. Every planner runs on identical canopies (paired comparisons). **[PY]**
- **T8.2** Factorial sweep: LAI × fruit density × clustering × trellis type. Fractional factorial to screen, full factorial on survivors. **[PY]**
- **T8.3** Switch to `apple_fruitingwall` alongside `apple`. Your current 1.5 m spacing already interpenetrates canopies, which is realistic for high-density — but the fruiting-wall model is the architecture your rig is actually designed for. **[PY]**
- **T8.4** Statistics: ≥20 canopies/cell, bootstrap CIs **resampling canopies not views**, paired Wilcoxon, Cliff's δ, Holm–Bonferroni. **[PY]**
- **T8.5** Pre-register metrics and test seeds; run the Tatarchenko degenerate-baseline check (verify a *stupid* baseline doesn't already score well on your headline metric). **[PY]**
- **T8.6** Digital-twin path for sim-to-real: reconstruct a real tree via the LiDAR plugin's leaf-by-leaf reconstruction, report the same metric vector on sim and twin, and validate **rank preservation** across planners. **[PY]**

---

## Upstream patches worth contributing

These are helios-core changes, not PyHelios. Each is a good PR and each removes a real constraint.

1. **`runCamerasOnly()` — highest value.** `runBand()` re-solves the entire scene radiative transfer on every render, even when only the camera moved. The fast path (`launchCameraRays()`, `RayTracingBackend.h:153`) exists internally but is not public. This is plausibly the difference between a 1 Hz and a 10 Hz loop. **[C++]**
2. **In-memory depth + pixel-UUID getters.** The C++ already pushes `camera_<label>_pixel_depth` and `camera_<label>_pixel_UUID` into Context global data, but PyHelios's `getGlobalData` handles only scalars and small vec types — no float arrays — so this data is unreachable from Python. **[BIND]**
3. **Binary label maps.** `getPrimitiveDataLabelMap` / `getObjectDataLabelMap` currently round-trip through a text file and `np.loadtxt`. Fine for datasets, too slow for a loop. **[BIND]**
4. **`CollisionDetection` bindings.** See T0.6. **[BIND]**
5. **Camera up-vector / roll.** `RadiationCamera` stores position + lookat only; EXIF roll hardcoded to 0. Not blocking for 5-DOF, but it is a real limitation to document. **[C++]**

---

## Immediate blockers, in order

1. **T0.5** — benchmark Tier C. Nothing about the architecture is decidable until you know the per-render cost.
2. **T0.6** — decide the ray-casting story. Phase 2 and Phase 4 both stall without it.
3. **T0.3** — validate the pose convention. Everything geometric is silently wrong if this is off, and it will not announce itself.
4. **T1.1** — enable `optionalOutputObjectData`. Two lines, and without it there is no instance ground truth at all.

---

## Suggested order of attack

**Week 1:** T0.1 → T0.2 → T0.3 → T0.4 → T0.5, then T1.1 → T1.2. At the end of week 1 you should have physically-based renders from three radiation cameras with exact per-fruit ground truth on disk, and a real number for render cost.

**Week 2:** T1.3 → T1.5 → T6.1 → T6.2 → T6.3. Fix the evaluation flaws in the existing gsplat pipeline so the capture sweep becomes readable, and re-run it as your Stage-0 baseline. Simultaneously start T0.6 since it has the longest lead time.

**Week 3–4:** T3.1–T3.4 (kinematics + roadmap) and T5.3 (raster baseline), then the E3 planarity check — greedy coverage vs raster on one fruiting-wall tree. **If that gap is small, you learn early that the explore phase is not where your novelty lives, and you shift weight to the exploit phase.**

**In parallel throughout:** Phase 7. It only needs Phases 0 and 1, and it de-risks the largest open question in the plan.
