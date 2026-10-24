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

`generate.py` builds one orchard per seed at 540 d and then walks the growth schedule with
`advanceTime`, rendering all three view families at every stage plus a fixed 16-pose "growth
probe" rig. The probe renders are stage-major; transposing them pose-major turns them into
growth episodes at **zero extra render cost**, which is why the growth channel exists at all
despite being 24× smaller than the view channel.

Measured cost, full config (8 stages × 3 families × 128 steps + 16 growth probes = 3,200 frames
per orchard): **254–323 s per orchard**, ~81 MB compressed. Breakdown per stage: ~32 s, of
which 3 × (4.5 s solve + 1.2 s readback + ~2.5 s npz compression) for the view families, ~4.9 s
for the probe solve, and ~2.5 s for `advanceTime` + `updateGeometry`.

Two ordering decisions made after seeing real timings:

- **Val and test orchards are generated first.** At ~5 min each, a run that has to be cut short
  would otherwise leave a dataset with no validation or test split at all, which is worthless. A
  smaller *train* split is merely smaller. This cost one restart of the generator.
- **On `--resume`, the stored calibration is reused rather than recomputed.** `calibrate_once`
  is deterministic, but recomputing it would make the dataset's single global exposure an
  implicit function of when the run was restarted — and one fixed exposure across the whole
  dataset is the entire point.

## 5. W4 — does the model actually work?

Ran `train.py --overfit-one` on a single real recorded trajectory
(`train/view_s10000_g0_row_traversal.npz`, 32 frames, 64×64, 12,000 steps, ~18 it/s).

**First attempt diverged.** Reconstruction reached rgb MSE 7.7e-4 and depth 2.3e-4 by step
11,500 — then at step 12,000 jumped to 1.35e-2 and 3.77e-2, a 17× regression in the final 500
steps, and the saved last-step checkpoint scored only 20.05 dB. The cause is Adam `eps=1e-8`:
once gradients are that small, eps stops regularising the denominator and the effective step
size explodes. Fixed by defaulting to `eps=1e-5` (the DreamerV2/V3 value) and by checkpointing
on best loss instead of trusting the last step.

**Second attempt passed** (`run_w4.py`):

| | value |
|---|---|
| teacher-forced reconstruction PSNR | **30.67 dB** |
| SSIM | 0.956 |
| depth MAE | 0.047 m |
| semantic mIoU | 1.000 |
| open-loop imagination, ctx=5, t+1 | 31.00 dB |
| … t+5 / t+10 / t+25 | 30.89 / 31.07 / **30.14 dB** |

Holding ~30 dB out to a 25-step *open-loop* rollout means the RSSM's dynamics are doing the
work, not just the encoder/decoder — an autoencoder with a broken transition model would
collapse within a few imagined steps. Acceptance criterion (recon PSNR > 25 dB and mIoU > 0.7)
passed.

A note on reading the loss: with KL free bits at 1.0 nat and weights 0.5/0.1, `loss` cannot go
below 0.6 however good the reconstruction is. "Near zero" has to be read on the reconstruction
terms.

## 6. W5 — training

Two models, identical except for `--zero-actions` (the no-action ablation), trained concurrently
at 64×64, batch 24, sequence 32 on one RTX 5090.

**First attempt ran at 2.75 it/s** — 40 k steps would have taken 4 hours. The bottleneck was
`np.savez_compressed` decompression: with the default 64-episode LRU cache and 288 train view
episodes, ~78% of every batch's 24 elements needed a fresh episode decompressed from disk.
Raising `--cache-size` to 512 (≈1.2 GB of RAM at 64×64) took it to **11.3 it/s**, a 4× speedup,
after which the cache is warm and there is no disk I/O in the steady state.

**Second bug: checkpoint selection was picking the wrong model.** `ckpt_best` was selected on
total validation loss, but the KL term rises monotonically (val kl_dyn 1.35 → 2.05) as the model
uses more latent capacity, while every reconstruction term falls. Total loss therefore went *up*
while the model got *better*, and "best" froze at step 5,000 when validation reconstruction
actually kept improving to step 14,000. Fixed to select on validation reconstruction, and both
models retrained under the corrected rule.

**Third finding, from continuing the run to 42 k steps:** validation reconstruction bottoms out
at step 14,000 and then *rises* while training loss keeps falling. The model is limited by the
number of distinct orchards (12), not by step count. `output/w5/curves.png` shows the divergence
clearly on the depth and semantic heads. This is why the reduced dataset scale matters and is
reported as the binding constraint.

Resumability was exercised for real: one run was resumed from step 30,000 and continued to
42,000 with optimiser state and step count intact.

## 7. W6 — evaluation

The headline numbers, the ablations, the 3DGS reference and the honest negative results are in
`FINDINGS.md` §10–§11 and summarised in `WORLD_MODEL_STATUS.md`. Two things belong in the log
rather than the findings:

- **The plan's no-action ablation nearly failed to detect action usage.** At t+1 the full model
  and the eval-time zero-action rollout scored 18.13 vs 18.11 dB, and the *shuffled*-action
  rollout scored 18.14 — i.e. marginally better than the truth. On that evidence alone one would
  write "the model ignores actions". Adding a direct probe (roll out from the same context with
  true / zeroed / negated actions and compare the predictions *to each other*) shows the action
  displaces the prediction by 20–38% of the magnitude of real inter-frame motion. Both are
  reported; the disagreement between them is itself the finding.
- **The gsplat baseline needed `ninja` on `PATH`.** `gsplat` 1.5.3 JIT-compiles its CUDA
  extension on first use and fails with "Ninja is required to load C++ extensions" unless the
  `gsplat` env's own `bin` is on `PATH`. Invoking the interpreter by absolute path is not
  enough. One line in `run_remaining.sh`.

---
---

# ROUND 2 — chronological log

Run date: **2026-07-31**. Same machine, same branch, same checkout (no worktree). Data generation
in `helios`, training and evaluation in `gsplat`.

Round 1's parting diagnosis was "the model is limited by orchard diversity, not compute", and the
Round 2 brief is to extend the dataset to 40+ train orchards, then revisit regularisation and the
growth channel. That is what was done — but the diagnostics run *while the data was generating*
changed what the retraining was for, so this log is ordered by what was learned rather than by
the task list.

## 8. Housekeeping

The leftover `tail -f` process from Round 1 (pid ~275343) was already gone; nothing to kill.

Round 1's status file flagged the missing Slack notification as an unexplained anomaly —
`notify_slack.py` present at the start of the session and absent at the end, with none of its
commits touching it. **That entry is retracted.** The file and
`~/.config/claude-notify/slack_webhook_url` were deleted deliberately by the user on 2026-07-30,
mid-run. Nothing malfunctioned. The guarded call sites raise `ImportError` inside a bare
`except Exception: pass` and no-op; they are left alone rather than stripped across eight files
for no behavioural change, and Round 2 adds none.

## 9. Dataset extension — the easy part, started first

`generate.py --resume --n-train 44` extends the existing manifest rather than regenerating it:
the plan's ordering (val and test seeds first) means the 20 Round 1 orchards are all already on
disk, and `--resume` skips them by `(seed, split)` and **reuses the stored calibration** so the
single global exposure scale and the pixel orientation are byte-identical to Round 1's. Train
seeds 10012–10043 are new; `TRAIN_SEEDS = range(10000, 10999)` so they stay inside the declared
range and disjoint from val (11000+) and test (12000+).

Measured cost on the new orchards: **241–323 s each**, ~80 MB compressed, matching Round 1's
254–323 s. 32 new orchards ≈ 2 h 15 m.

`run_r2_check_split.py` re-verifies disjointness **against the manifest as written** rather than
against the declared ranges, plus three checks Round 1 did not make: that every episode's `split`
field matches the directory its file is in, that every referenced file exists, and that no two
episodes share a path. Extending a dataset with `--resume` is exactly the operation that can put
a test orchard into training silently, and the failure would be invisible in the loss curves.

## 10. The diagnostics that changed the plan

The GPU was busy ray-tracing for two hours, which is enough time to ask whether retraining on
more orchards would help. Four measurements, in the order they were made:

**R2-A, the growth channel (`run_r2_growth_signal.py`).** Reads only the stored dataset. The first
thing it printed ended the growth line of investigation as originally framed:

```
distinct a_grow sequences over 320 growth episodes: 1
  [5,5,5,5,5,5,10,0] x320
```

Every growth episode in the entire dataset carries the same action. Round 1's growth channel had
no counterfactual variation in it at all, and W6's "zero the growth action" ablation was an
out-of-distribution query rather than a counterfactual. The second thing it printed closed the
RGB half of it: consecutive growth stages differ by 20.60 dB while §9's measured simulator
re-render floor is 20.82 dB — the RGB growth signal sits *at* the render noise. Details in
FINDINGS §15.

**R2-C, error attribution (`run_r2_recon_floor.py`).** The measurement Round 1 never made:
teacher-forced posterior reconstruction on held-out orchards — encode a real frame, decode it
straight back. 1.035 m depth MAE, against 1.067 m for the open-loop t+1 rollout and 0.657 m for
copy-last-frame. **97% of the t+1 depth error is the autoencoder; 3% is the dynamics.** On the
train split the same model reconstructs at 1.020 m — a 1.5% generalisation gap. Round 1's
"data-limited" story is right about the loss curve and wrong about the ceiling.

Adding a per-class IoU breakdown to the same script made the mIoU result exact rather than
opaque: the model never predicts fruit, petiole or peduncle at all, and the seven per-class IoUs
average to 0.268 — the reported number, to three decimals. See FINDINGS §13.

**R2-H, the blurred-ground-truth control (`run_r2_blur_baseline.py`).** No model at all: take the
correct frame, blur it, score it. At the model's measured sharpness a *perfect* depth map still
scores ~0.94 m, worse than copy-last's 0.657 m. So the depth criterion is unreachable at that
sharpness however accurate the prediction is. That reframed the whole round: **depth is a
sharpness problem, mIoU is a class-balance problem, and neither is a data problem.**

**The KL logs.** Round 1's own training log, re-read with the above in hand: `kl_dyn=1.371` at
step 17,500 and 1.372 at step 18,000 — flat — with validation rising only 1.58 → 1.64 over the
same window. The latent is 32 categorical
variables × 32 classes = 160 bits per frame, and the posterior diverges from the prior by 1.37
nats = 2.0 bits. The encoder is very nearly bypassed. That is the mechanism behind the blur, and
it is a hyperparameter, not a capacity limit.

## 11. What was actually run, and why each run exists

Seven training runs in five chained phases, all on the 44-orchard dataset, all seeded, all
otherwise identical to Round 1's `main2` except where stated:

| phase | tag | change from `r2_main` | what it tests |
|---|---|---|---|
| A | `r2_main` | none (40k steps) | data scaling 12 → 44 orchards, vs Round 1 |
| A | `r2_noaction` | `--zero-actions` | the trained no-action ablation |
| A | `r2_growth` | `--growth-subsample`, growth fraction 0.40 | can the growth action be made real? |
| B | `r2_big` | base 32→64, deter 512→1024, latent 32×32→48×48 | capacity |
| C | `r2_sem` | class-weighted semantic CE | the mIoU class-collapse fix |
| D | `r2_best` | class weights **+** L1 depth | both metric-directed fixes together |
| E | `r2_kl` | free-bits 1→6, KL weights 0.5/0.1 → 0.2/0.04 | the information bottleneck |

`r2_sem` vs `r2_main` isolates the class weights and `r2_best` vs `r2_sem` isolates the depth
loss. `r2_kl` moves two knobs in the same direction on one hypothesis and is labelled as one
intervention, not a controlled pair. Three jobs share the GPU at any time.

**A comparability caveat, stated rather than buried:** `r2_sem`, `r2_best` and `r2_kl` change the
*scale* of terms in the training objective (class weights, L1 instead of MSE, KL weights), so
their "best validation reconstruction" numbers are not comparable with `r2_main`'s and are not
used for cross-run comparison. Only the held-out evaluation metrics — which are unweighted and
identical for every model — are.

## 12. Dead ends and fixes inside Round 2 itself

- **The growth stage-subsampling augmentation started too diffuse.** Choosing the start stage
  uniformly over all 8 made most subsampled windows 2–3 frames long, which would have shrunk the
  growth channel's already-small share of the loss. Restricting the start to the first three
  stages brings the mean window length to 3.79 (max 7) while leaving every stage reachable, and
  `--growth-fraction` is raised 0.25 → 0.40 in `r2_growth` to compensate for the rest.
- **The counterfactual growth evaluation initially scored out-of-distribution actions.**
  Subsampling with stride ≤ 3 produces `a_grow` ∈ {5, 10, 15, 20} d, but the evaluation's
  candidate set runs to 25 d and 35 d. Scoring those together would blame a model for failing on
  an action it was never shown, so the script now keeps the full per-episode error matrix and
  reports identification accuracy twice, each against its own chance level.
- **Evaluation was not reproducible.** The RSSM samples its categorical latent, so two runs of
  `run_r2_recon_floor.py` on the *same* checkpoint differed by ~0.015 m of depth MAE — of the
  same order as some of the differences being compared. Seeding torch per checkpoint fixed it;
  verified by running one checkpoint twice and getting identical output.
- **`generate_log.txt` is opened in append mode**, so a naive "count the completed-orchard lines"
  progress check counts Round 1's 20 lines too. Cost one confused progress reading, nothing more.

## 13. How the runs actually went

Timeline, all on 2026-07-31: dataset extension 00:12 → 03:02 (32 orchards, 9,857 s). Phase A
(`r2_main`, `r2_noaction`, `r2_growth`, 40k steps, three concurrent) 03:04 → 04:32 at **7.6 it/s
each** — noticeably faster than Round 1's 11.4 it/s solo would predict for three concurrent jobs,
because `--cache-size 1200` holds all 1,056 train view episodes at 64×64 in RAM (~4.4 GB per
process, 48 GB used of 62 total) and there is no disk I/O in the steady state. Phases B/C/D
(`r2_big`, `r2_sem`, `r2_best`, 30k, three concurrent) 04:32 → 05:59 at ~5.5 it/s. Phase E
(`r2_kl`, alone) 05:56 → 06:25 at ~17 it/s. Phase F (`r2_final`, alone) 06:26 → 06:54.

Nothing failed. No run crashed, no OOM, and the two evaluation steps that finished in 12 and 3
seconds were checked rather than assumed — they were genuinely that fast because the episode
caches were already warm.

## 14. The moment the round turned

`r2_big` finished and its validation log read `kl_dyn=1.373`. Round 1's model, with a 160-bit
latent, ran at 1.371. `r2_big` has a 268-bit latent and four times the parameters, and it was
transmitting the *same 2.0 bits per frame*, with held-out depth MAE 1.033 m against `r2_main`'s
1.038 m and mIoU identical to three decimals. Capacity was not the constraint; the KL penalty was.
`r2_kl` — free-bits 1 → 6, weights 0.5/0.1 → 0.2/0.04, nothing else changed — ran at 6.2–6.3 nats
and took reconstruction depth from 1.022 m to 0.887 m and RGB sharpness from 0.108 to 0.127, the
only intervention in the whole round that moved sharpness.

That is also why `r2_final` exists. It was not in the original plan: phases B–E were designed as
single-factor runs, and once three of them had each moved the needle through independent
mechanisms — information through the bottleneck, sharpness in the depth head, class balance in the
semantic head — the obvious question was whether they compose. They do, almost additively.

## 15. Round 2's own mistakes

- **The blurred-ground-truth bound was indexed by the wrong quantity.** It blurs every modality by
  one σ and was reported against RGB sharpness, which gave "~90% of the depth deficit is blur".
  `r2_best` broke the assumption by producing a sharp depth map (0.281) behind a blurred RGB
  decode (0.105). Both scripts now report depth sharpness separately, the bound is read off the
  depth column, and the corrected blur share is ~35% for Round 1 and ~28% for `r2_best`. The
  original claim is retracted in `FINDINGS.md` §14 rather than edited away.
- **The growth-signal SNR was first computed against a noise floor measured somewhere else.**
  Comparing the 20.60 dB stage step against §9's 20.82 dB view-episode floor gave "the growth
  signal is at the noise floor". Measuring both at the same poses on the same orchard gives a
  floor of 22.75 dB and an SNR of 0.85 — a real signal, smaller than its noise. Corrected.
- **"Every run's best checkpoint is at step 26,000" looked like a bug and is not.** All runs share
  `--seed 0`, so the validation sampler draws the same windows at the same steps in every run, and
  the val curve oscillates ~7% step to step with only 8 val batches. Fixed-step cross-run
  comparison is therefore fair; "best step" is partly a draw of the validation dice. Recorded, and
  it is why every headline number in this round comes from the held-out test evaluation instead.
- **Class weights alone made held-out depth slightly worse** (1.063 m vs `r2_main`'s 1.038 m).
  Reported as-is; they only pay off in combination.

## 16. What Round 2 concludes

The dataset extension was carried out exactly as briefed and produced a clean negative: 3.7× the
orchards moved held-out depth MAE by 2% and mIoU by 1%, while three changes that cost no compute
at all moved depth MAE by 22% and mIoU by 11%. Round 1's diagnosis — and the brief that was built
on it — pointed at the wrong constraint. The constraint was an information bottleneck the model
was choosing not to use, a loss shape that mispriced the far field, and a cross-entropy that
dropped five of seven classes; plus, for the growth channel, an action variable that was a
constant in every episode of the dataset.

What is still unsolved is honest and specific: at t+1 copy-last-frame still wins on depth
(0.657 m vs 0.810 m) and on mIoU (0.333 vs 0.294), and the measured reason is output sharpness —
0.293 against the ~0.31 a uniformly blurred perfect predictor needs. Petiole and peduncle are
0.22% and 0.03% of pixels and cannot be segmented at 64×64 at all, capping mIoU at 0.714. And the
growth channel's RGB signal genuinely sits below the render noise (SNR 0.85), so any further work
there should be scored on depth and semantics, which are bit-exact, and not on RGB.
