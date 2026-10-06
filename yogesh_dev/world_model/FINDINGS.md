# World Model — findings

What was actually learned building an action-conditioned latent dynamics model on a simulated
2×10 apple orchard. Real numbers only; every one comes from a script under
`yogesh_dev/world_model/` that can be re-run. Negative results are reported as negative results.

---

## 1. The single most consequential finding: the apple growth model is piecewise constant

The plan's growth channel assumes `advanceTime(dt)` moves the orchard forward in a way the world
model can learn to predict. Measured on a single tree, seed 10000, ages 520–800 d in 10-day
steps (`run_w0b.py`, every quantity from real `context.getPrimitiveArea` sums):

| age (d) | primitives | fruit objects | leaf area (m²) | fruit area (m²) | mean fruit Ø (mm) | height (m) |
|---|---|---|---|---|---|---|
| 520 | 4,886 | 0 | 0.000 | 0.000 | 0.0 | 1.79 |
| 530 | 4,886 | 0 | 0.000 | 0.000 | 0.0 | 1.79 |
| 540 | 34,001 | 0 | 0.547 | 0.000 | 0.0 | 1.97 |
| 550 | 22,357 | 20 | 1.768 | 0.121 | 43.8 | 2.17 |
| 560 | 27,992 | 20 | 2.944 | 0.292 | 68.2 | 2.37 |
| 570 | 33,062 | 20 | 3.987 | 0.537 | 92.5 | 2.56 |
| 580 | 34,024 | 20 | 4.652 | 0.595 | 97.4 | 2.70 |
| 590–730 | 34,024 | 20 | 4.652 | 0.595 | 97.4 | 2.70 |
| 740–800 | 16,058 | 0 | 0.000 | 0.000 | 0.0 | 2.55 |

Read that carefully: **every value from 580 d to 730 d is bit-identical.** 15 consecutive
10-day samples, no change at all. Then between 730 and 740 d the leaves and fruit vanish
(deciduous dormancy) and the plant sits frozen again.

Consequences, all of them real:

1. **The plan's recommended growth schedule (650–720 d) is entirely inside the frozen region.**
   Following it would have produced a growth channel in which `advanceTime(20)` is a literal
   no-op — the model would have "learned growth" by learning to copy its input. W0's own
   `advanceTime` measurement, which started at 650 d as the plan suggests, confirms it directly:
   four consecutive advances (10, 10, 20, 20 days) left the primitive count at exactly 830,392
   and the fruit primitive count at exactly 106,914.
2. **The usable growth window is 540 → 580 d — about 40 simulated days, 8 stages at 5-day
   resolution.** In that window the orchard really does change: 752,201 → 830,392 primitives,
   leaf area 13.1 → 110.4 m², fruit area 0 → 15.45 m² (`run_w0c.py`, full 2×10 orchard).
3. The plan's gotcha 7 ("age 540 d produces NO fruit… any growth-stage schedule must reach
   ≥ ~650–720 d") is **half right and half misleading**: 540 d indeed has no fruit, but the fix
   is 550–580 d, not 650–720 d. Going to 650 d gets fruit *and* a dead growth channel.

This is a property of helios-core's `apple` plant model, not of anything in this work. It is not
a bug fixable from Python. It is a hard limit on what the growth channel of this world model can
be asked to predict, and it is reported rather than papered over.

## 2. `advanceTime` at 20-tree scale is cheap — the plan listed this as UNMEASURED

| where | dt | cost |
|---|---|---|
| frozen window (650 → 750 d) | 10–40 d | 0.92 – 2.77 s |
| real growth window (540 → 590 d) | 5 d | 1.25 – 5.07 s, mean 2.46 s |
| full rebuild for comparison | — | 6.7 s @540 d, 37.8 s @720 d |

And `build(540) + advanceTime(50)` == `build(590)`: identical organ counts for every organ, leaf
area agreeing to 1.4e-5 m² out of 110.41 (1.3e-7 relative), shoot area to 0.017 m² out of ~111
(1.5e-4 relative). So the dataset generator builds **once** per orchard and advances through the
schedule, ~8× cheaper than one build per stage.

## 3. Camera batching is worth 254×, and has not saturated at 256

Measured on the full 830,392-primitive orchard at 128×128, 3 bands, 2 AA samples:

| N cameras | solve (s) | per image (s) |
|---|---|---|
| 1 | 4.846 | 4.846 |
| 4 | 4.882 | 1.220 |
| 16 | 4.829 | 0.302 |
| 32 | 4.864 | 0.152 |
| 64 | 4.828 | 0.075 |
| 128 | 4.835 | 0.038 |
| **256** | **4.883** | **0.019** |

The solve time is **flat** — registering 256 cameras costs the same as registering 1. The plan
measured 3.45 s → 6.09 s over 1 → 128 cameras (a 72× ratio); we measure no rise at all over
1 → 256 (a 254× ratio). Readback of all four modalities together (3 RGB bands, depth EXR,
semantic label map, instance label map) costs **0.0091 s/image** and is not a bottleneck.

This inverts the compute picture: rendering an entire 128-step trajectory costs about 6 s, and
the dataset is bounded by orchard construction and disk compression, not by ray tracing.

## 4. Three real bugs found in this work's own code, each of which looked fine

Documented because each is a trap the next person will hit.

1. **"Lit pixels vs hit pixels" cannot calibrate the pixel-array orientation.** The obvious test —
   does the mask of pixels with radiance > 0 match the mask of pixels that hit geometry? — tops
   out at IoU 0.872 and is structurally wrong: `setDiffuseRadiationFlux` lights the *background*
   too, so `lit_frac` (0.442) exceeds `hit_frac` (0.403). Replaced with a test that uses the
   per-organ reflectances we set ourselves: median green/red on leaf pixels ÷ the same on fruit
   pixels is 6.23 for the correct orientation and 1.000 for the wrong ones, and under the correct
   orientation leaf g/r measures 2.413 against a configured 2.27 and fruit 0.387 against 0.357.
2. **Aggregating that score by the mean picks the wrong answer.** One calibration view with
   almost no fruit pixels produced a ratio of ~1.2e7 and outvoted 13 correct views. Fixed with a
   majority vote plus a ≥200-pixel-per-class requirement.
3. **Applying the calibrated flip to all four modalities is invisible and wrong.** RGB, depth,
   semantic and instance stay mutually consistent, and a left-right mirrored orchard still looks
   exactly like an orchard, so nothing looks broken. But depth and the label maps come out of the
   pixel-labelling pass that Phase 0 T0.3 validated sub-pixel against `look_at_view_matrix` —
   they were already right, and flipping them mirrored every modality relative to the recorded
   camera pose. Only the raw RGB buffer needs the flip.

A fourth, caught before it could do damage: **the orientation calibration was originally run at
growth stage 0 (540 d), which has zero fruit.** No view passed the fruit-pixel threshold, the
routine fell back to its default, and printed `orientation=as_is` — silently mirroring the whole
dataset. It now calibrates at the last stage and **raises** instead of falling back.

Bug 3 is why `run_w1.py` now includes a reprojection test: project each fruit's known world
centroid through the recorded pose and compare against its instance-mask centroid. Result over
135 fruit observations at 128×128: **mean 0.80 px, median 0.71 px, p90 1.09 px, max 3.26 px** —
matching Phase 0 T0.3's independently-measured 0.71 px and Phase 1's 1.41 px. That is the check
that proves the pose, the intrinsics and the images all agree.

## 5. A `PlantArchitecture` canopy has no ground, and that cost 61% of every frame

The first contact sheet from an in-lane camera was 61% background: there is no ground plane, so
everything below the canopy was empty space. Adding a 40 × 24 m subdivided tile with soil
reflectance brought sky down to 18.4% and gave ground 45.7%. More importantly, the ground was
given **seeded per-patch reflectance jitter** — a uniform alley provides an action-conditioned
model with no optical-flow cue at all across nearly half the image, which is exactly the signal
it needs to infer how far the camera moved.

## 6. The RGB photometry recipe from the plan works, verified end to end

Per-organ `reflectivity_<band>` / `transmissivity_<band>` + `disableEmission(band)` + raw float
readback + our own fixed-exposure tonemap produces recognisable orchard imagery: green foliage,
brown trunks, red-orange apples, blue sky. The band ratios come out where they were configured
(leaf green/red measured 2.41 against 2.27 configured; fruit 0.387 against 0.357). One fixed
global exposure scale is computed once, pooled over the first and last growth stage
(1,071,921 sample pixels), and used verbatim for every frame in the dataset.

## 7. The inter-row lane is only ~0.8 m wide

Measured orchard bounding box at 720 d: x ∈ [−7.78, 7.86], y ∈ [−3.09, 3.12], z ∈ [0, 2.79],
with tree bases at y = ±1.75. That implies a canopy half-width of ~1.34 m against a 3.5 m row
spacing, leaving a free lane of about 0.82 m. Camera trajectories are constrained to
|y| ≤ 0.35 m as a result. This is not a modelling choice — it is what a 2×10 `apple` canopy at
1.5 m in-row spacing actually measures, and it is consistent with Phase 8's finding that plain
`apple` canopies interpenetrate their neighbours by ~29% of canopy width at that spacing.

## 8. Other measured facts worth recording

- **Determinism holds end to end.** Same seed twice → 830,392 primitives / 519 fruit objects,
  identical organ counts. Different seed → 846,331 / 549.
- **Depth and semantic sky masks agree pixel-for-pixel** (agreement 1.000000 over 16 frames),
  confirming Phase 1's finding that depth's −1 sentinel and the label map's NaN come from the
  same ray-hit-topology pass.
- **The plan's single-tree primitive counts do not reproduce.** It reports 11,963 prims at
  365 d and 45,315 at 720 d; we measure 4,886 at 400–500 d and 34,024 at 600–730 d. The
  *orchard*-scale numbers do reproduce closely (752,201 prims / 13.5 s at 540 d vs the plan's
  756,833 / 14.1 s). Most likely a seed difference, but reported as a discrepancy rather than
  quietly adapted.
- **`setProgressCallback` does not suppress the C++ progress bar.** Setting a no-op Python
  callback still leaves `advanceTime` writing a progress bar to stdout on every sub-step. Every
  runner here writes its own clean log file alongside the noisy stdout capture.
- **`base` cannot generate this dataset**: `OpenEXR` is not installed there and depth readback
  needs it. Generation runs in the `helios` env (PyHelios + OpenEXR + imageio), training in
  `gsplat`.

---

## 9. The dataset is reproducible in everything except radiance — and that sets a hard ceiling on RGB prediction

W3's acceptance criterion is *"regenerating one shard with the same seed is byte-identical"*.
**It is not.** `run_w3_verify.py` regenerated a whole orchard (40 episodes, 3,200 frames) from
the same seed and found **0/40 byte-identical**. But the per-array breakdown makes the failure
precise rather than mysterious, and `run_w3_determinism_probe.py` quantifies it on one episode:

| array | reproducible? | detail |
|---|---|---|
| `depth` | **yes**, bit-exact | |
| `semantic` | **yes**, bit-exact | |
| `pose`, `state`, `a_view`, `fruit_vis` | **yes**, bit-exact | |
| `instance` | effectively yes | fruit mask IoU **1.0**, identical set of 796 fruit IDs, only **0.0042%** of pixels differ (ties on object boundaries) |
| `rgb` | **no** | 41.1% of pixels differ; mean |Δ| 6.2 levels, p99 134, max 255; **run-to-run PSNR 20.82 dB** |

So the *geometry* pipeline is fully deterministic — seeded plant growth, ray-hit topology,
depth, labels and poses all reproduce bit-for-bit. What does not reproduce is the Monte-Carlo
radiative solve: OptiX samples direct and diffuse rays with an RNG PyHelios does not expose, so
two renders of the identical scene from the identical pose give different radiance.

**The consequence is the important part.** Re-rendering the same frame twice agrees only to
**20.8 dB PSNR**. That is a *noise floor on the simulator itself*, and therefore an approximate
ceiling on what any model can score when predicting a held-out Helios RGB frame: the stored
target contains a specific noise realisation that is not a function of the scene or the camera
pose, so it is not predictable in principle. Every RGB PSNR in the W6 tables has to be read
against that 20.8 dB reference, not against ∞. (Depth and semantic have no such ceiling — they
are bit-exact — which is one reason the multi-modal decoder heads earn their keep.)

Two things follow for anyone continuing this work:

1. **Raising `setDirectRayCount` / `setDiffuseRayCount` would raise the ceiling.** The dataset
   here uses the plugin defaults with `antialiasing_samples=2`. Nothing was tuned, because the
   ceiling only became visible after the dataset was generated. Measuring PSNR-between-repeats
   as a function of ray count is a cheap, high-value follow-up.
2. **"Byte-identical regeneration" is the wrong acceptance criterion for a ray-traced dataset**
   unless the sampler is seeded. The right one is what this section reports: bit-exact geometry
   and labels, plus a stated and measured radiance reproducibility.

---

## 10. The trained world model: what it does and does not do

Trained at 64×64 (nearest 2× downsample of the stored 128×128; 64² is DreamerV3's own
resolution), batch 24, sequence 32, on 12 train orchards (38,400 frames). A second model was
trained **identically except with all actions zeroed** — the real no-action ablation. Both were
run concurrently on the RTX 5090 at ~11 it/s. The reported checkpoints are the ones selected by
best **validation reconstruction**, which for both models is step **14,000** (see §11 for why
step count is not the binding constraint and why total-loss selection was wrong). Evaluated on
4 held-out test orchard seeds (96 view episodes, 64 growth episodes), conditioning on 5 real
frames and then rolling the prior forward open-loop with the recorded actions.

An earlier 30,000-step snapshot of the same experiment is preserved under `output/w6_30k/`; its
numbers are within ~0.05 dB of these, so nothing below depends on the checkpoint choice.

### View channel — RGB PSNR (dB), test split

| horizon | full model | zeroed actions (eval) | shuffled actions | **no-action model (trained)** | copy-last-frame |
|---|---|---|---|---|---|
| t+1 | 18.13 | 18.11 | **18.14** | 18.09 | 16.71 |
| t+5 | **17.96** | 17.92 | 17.92 | 17.87 | 15.63 |
| t+10 | **17.78** | 17.69 | 17.66 | 17.58 | 15.38 |
| t+25 | **17.45** | 17.42 | 17.28 | 17.20 | 15.14 |

The full model beats copy-last-frame by 1.4–2.3 dB at every horizon. Against the ablations the
ordering is right and the margin **grows with horizon** — full vs the trained no-action model is
+0.04 dB at t+1 and +0.25 dB at t+25 — which is the correct qualitative behaviour (a one-step
prediction barely needs the action; a 25-step rollout does). **But at t+1 the shuffled-action
rollout actually scores 0.01 dB higher than the true-action one**, so at short horizons the PSNR
ablation is pure noise. PSNR alone cannot support the claim that the model uses its actions.

### Depth and semantics — where it clearly loses

| horizon | model depth MAE | copy-last depth MAE | model mIoU | copy-last mIoU |
|---|---|---|---|---|
| t+1 | 1.061 m | **0.657 m** | 0.265 | **0.333** |
| t+5 | 1.117 m | **0.968 m** | **0.266** | 0.264 |
| t+10 | 1.171 m | **1.096 m** | **0.263** | 0.250 |
| t+25 | 1.256 m | **1.205 m** | **0.253** | 0.237 |

**Copy-last-frame beats the model on depth at every horizon**, by 1.6× at t+1 and still by 4% at
t+25. On semantics the model only edges ahead from t+5 onward, and only because copy-last
degrades — the model's own mIoU is flat at ~0.26 throughout. So the RGB PSNR win does not
generalise to the geometric and semantic heads.

### What the qualitative rollouts show, and why the PSNR table is misleading on its own

`output/w6/rollout_*.png` (top row = Helios ground truth, bottom = model imagination) shows
the honest picture: **the model has learned the global layout — sky band above, textured ground
below, roughly the right colours — and essentially none of the canopy structure.** Its
predictions are low-frequency smears. That is exactly why it beats copy-last on PSNR (a blurry
image of the right average is a better L2 predictor of a moved scene than a sharp image of the
wrong scene) while losing on depth and mIoU (which are not forgiving of blur).

Note also that the model's PSNR *barely degrades with horizon* (18.13 → 17.45 over 25 steps)
while copy-last drops 1.6 dB. A predictor that is equally accurate at t+1 and t+25 is not
tracking the scene; it has converged to a horizon-independent average.

### PSNR ablations badly understate action usage — a methodological finding

Because the predictions are blurry, moving them in the correct direction buys almost no PSNR, so
the no-action ablation the plan specifies is nearly uninformative here. Measuring the thing
directly (`action_sensitivity` in `evaluate.py`: roll out from the same context with true, zeroed
and negated actions, and compare the *predictions to each other*, scaled by how much the real
image actually changes over the same interval):

| horizon | zeroing the action moves the prediction by | negating it moves it by | (real inter-frame motion) |
|---|---|---|---|
| t+1 | 0.0314 RMS = **20.3%** of real motion | 0.0348 = 22.6% | 0.1544 |
| t+5 | 0.0444 = **25.4%** | 0.0503 = 28.8% | 0.1750 |
| t+10 | 0.0518 = **28.3%** | 0.0574 = 31.4% | 0.1836 |
| t+25 | 0.0658 = **35.3%** | 0.0701 = 37.5% | 0.1871 |

So the model is **not** ignoring its actions: changing the action displaces the prediction by
20–38% of the magnitude by which the real image changes over the same interval, and the
displacement grows with horizon exactly as it should. The plan's risk table lists "model ignores
actions" as the thing the no-action ablation exists to catch — here the ablation would have
suggested near-indifference (0.03 dB at t+1) while a direct probe shows substantial
action-conditioning. **A PSNR-based no-action ablation is a weak test when the model's outputs
are blurry; report a direct sensitivity measure alongside it.**

### Growth channel — a negative result

Conditioning on 2 growth stages and imagining forward (each step = 5 simulated days):

| horizon | full | zeroed action | trained no-action model | copy-last |
|---|---|---|---|---|
| t+1 (5 d) | 19.39 dB / mIoU 0.272 / depth 1.50 m | 19.57 | **19.82** | **20.97** / **0.731** / **0.26 m** |
| t+2 (10 d) | 18.72 | 18.93 | **19.06** | **19.52** / **0.616** / **0.45** |
| t+3 (15 d) | 18.19 | 18.33 | 18.31 | **18.43** / **0.557** / **0.59** |
| t+5 (25 d) | **17.44** | 17.25 | 17.09 | 16.83 / **0.471** / **0.78** |

**The growth channel does not work at this training scale.** Up to t+3 the full model is *worse*
than the same model with the growth action zeroed, worse than the trained no-action model, and
worse than copy-last-frame; and it is far worse than copy-last on depth (1.50 m vs 0.26 m) and
semantics (0.272 vs 0.731) at *every* horizon. It only overtakes the alternatives on PSNR at
t+5 — 25 simulated days, by which point the canopy has changed enough that copying the last
frame finally fails. That single crossover is the only evidence in the whole evaluation that the
growth action is being used constructively, and it is thin.

The likely reason is the channel imbalance the plan's own risk table anticipated: growth frames
are **4.0%** of the dataset (2,560 of 64,000), and although the sampler oversamples them to a
measured 25.0% of batch *elements*, each growth episode is only 8 frames against 32 for a view
window, so after pad-masking they contribute roughly 6% of the actual loss. Reported as a
negative result rather than dressed up.

### Comparison with the 3DGS view-synthesis reference

| horizon | world model (RGB PSNR) | 3DGS matched (5 views) | 3DGS generous (28 views) | simulator noise floor |
|---|---|---|---|---|
| t+1 | 18.13 | 20.98 | 21.67 | ~20.8 |
| t+5 | 17.96 | 20.12 | 21.15 | ~20.8 |
| t+10 | 17.78 | 18.17 | 20.50 | ~20.8 |
| t+25 | 17.45 | **16.67** | 20.36 | ~20.8 |

3DGS wins at short horizons and the world model overtakes the *matched-information* splat at
t+25 — but this comparison is heavily in 3DGS's favour and should be read that way: **the splat
is given the true camera pose of every target frame**, while the world model gets only the
action sequence and must infer where the camera ended up. The "generous" splat additionally gets
27 posed views of the exact scene it must render, and it lands at ~20.4–21.7 dB, essentially at
the simulator's own re-render noise floor (§9) — which is what you would expect from a method
that is effectively interpolating between views it has already seen.

### Honest bottom line on the model

At this scale (12 orchards, 64×64, best checkpoint at 14k steps) the RSSM has learned the orchard's
*global photometric layout* and a real but weak action-conditioned displacement of it. It has
not learned canopy structure on unseen orchards, its depth predictions are worse than a
copy-last baseline at short horizons, and its growth channel is not working. The infrastructure
— dataset, action space, training loop, evaluation harness, ablations, baselines — is real and
re-runnable; the model is under-trained relative to what the architecture would need, and the
plan's own priority note ("cut training scale, not correctness or honesty") is exactly the
trade-off that was made.

---

## 11. The model overfits 12 orchards after ~15k steps — this is a data-diversity limit, not a step-count limit

Continuing training from 30k to 42k steps made validation *worse*, not better
(`output/w5/curves.png`, `curve_summary.json`):

| | validation reconstruction (rgb + depth + semantic + fruit) |
|---|---|
| best, at step **14,000** | main **0.7398**, no-action **0.7605** |
| final, at step 42,000 | main 0.8341, no-action 0.8406 |

Training loss kept falling throughout (train semantic 0.53 → 0.48, depth 0.150 → 0.134 between
14k and 42k) while validation rose. The model runs out of *orchards*, not of steps. The plan's
40-seed target was the right call; the 12 seeds generated here (a deliberate, time-driven
reduction — see §12) are demonstrably not enough.

**A cleaner action signal falls out of this.** Comparing the two models' *best validation
reconstruction* — the actual training objective, on held-out orchards, at the same step for both
— the full model is **2.7% better than the no-action model** (0.7398 vs 0.7605), and the gap is
visible in the per-term curves for depth and semantics throughout training. That, plus §10's
action-sensitivity probe, is much stronger evidence that actions are used than the 0.03–0.31 dB
PSNR margins.

### A real methodological bug in checkpoint selection

`train.py` originally selected its best checkpoint on **total validation loss**. But the KL term
rises monotonically as the model uses more latent capacity (kl_dyn 1.35 → 2.05 on validation),
so total loss went *up* while every reconstruction term went *down*. The rule therefore froze
"best" at step 5,000, discarding the genuinely best model at step 14,000. Fixed: selection is now
on validation reconstruction only, which is what the model is actually evaluated on. Reported
because it is exactly the kind of silent mis-selection that would make a model look worse than
it is for reasons unrelated to the model.

---
---

# ROUND 2 — 2026-07-31

Round 1 ended with a largely negative result and a diagnosis: *the model is limited by orchard
diversity*. Round 2 took that diagnosis seriously enough to test it rather than act on it. The
dataset was extended from 12 to 44 train orchards as planned, but before retraining, four
model-free or model-only diagnostics were run to find out **which** constraint is actually
binding. They changed the picture substantially, and they are reported first because everything
after depends on them.

Everything below is produced by a script in this directory and written to `output/r2/`. Splits,
seeds and the exposure calibration are unchanged from Round 1, so every Round 2 number is
directly comparable with the Round 1 tables above.

---

## 12. Round 1's diagnosis is half right: the loss overfits 12 orchards, but the *ceiling* is the representation

Round 1 §11 showed validation reconstruction bottoming at step 14,000 and rising afterwards while
training loss kept falling, and concluded the model had run out of orchards. That overfitting is
real. But it says nothing about *how good the model could be if it stopped overfitting*, and the
measurement that answers that was never made.

`run_r2_recon_floor.py` makes it. Give the model the real frame at time *t*, encode it, decode it
straight back — teacher-forced **posterior reconstruction**, no dynamics involved at all. That is
an upper bound on every rollout number the architecture can produce. On the 4 held-out test
orchards, Round 1's `main2` checkpoint (step 14,000, 64×64, seeded, 24 batches of 8):

| | RGB PSNR | SSIM | depth MAE | mIoU | fruit MAE |
|---|---|---|---|---|---|
| posterior reconstruction | 18.25 dB | 0.523 | **1.035 m** | 0.268 | 0.0049 |
| open-loop t+1 | 18.14 dB | 0.521 | 1.067 m | 0.263 | 0.0054 |
| copy-last-frame t+1 | 16.71 dB | 0.559 | **0.657 m** | 0.333 | 0.0016 |

**97% of the depth error at t+1 is already present in the reconstruction.** One step of dynamics
adds 0.032 m to a 1.035 m error. The RSSM's transition model is not what loses to copy-last-frame
— the encoder/decoder is. Round 1's headline negative ("copy-last beats the model on depth at
every horizon") is, at t+1, almost entirely a statement about the autoencoder.

The same measurement on **training** orchards settles whether that ceiling is itself a
data-diversity effect:

| split | posterior recon PSNR | depth MAE | mIoU | sharpness |
|---|---|---|---|---|
| train (12 orchards it was fit on) | 18.49 dB | 1.020 m | 0.290 | 0.122 |
| test (never seen) | 18.25 dB | 1.035 m | 0.268 | 0.115 |

The generalisation gap is **1.5% on depth** and 0.022 mIoU. The model reconstructs frames it was
trained on barely better than frames it has never seen: it cannot render a sharp orchard *at
all*. More orchards can close a 1.5% gap; they cannot move a 1.035 m ceiling.

Two more things this run measures, both of which Round 1 asserted qualitatively:

**The blur, as a number.** Mean absolute spatial gradient of the prediction divided by the same
for the ground-truth frame: **0.115**. Round 1 called the outputs "low-frequency smears" from
looking at the rollout strips; measured, they carry 11.5% of the real frame's gradient energy
(copy-last-frame, being a real frame, scores 0.992). This is the architecture working as
specified rather than a bug: the decoder is trained on MSE, whose optimum *is* the conditional
mean, and with a 32×32 categorical latent — **160 bits per frame** — the conditional entropy of
an orchard frame given the latent is enormous. The mean of that distribution is a blur.

**Where the depth error lives.**

| ground-truth distance | share of pixels | model | copy-last |
|---|---|---|---|
| 0–2 m | 35.0% | 0.813 m | 0.681 m |
| 2–4 m | 39.8% | 0.610 m | 0.449 m |
| 4–8 m | 18.7% | 1.152 m | 0.668 m |
| 8 m+ | 6.5% | **4.476 m** | 1.841 m |

Roughly half the total error comes from the 25% of pixels beyond 4 m. There is a loss/metric
mismatch behind that: the model trains on MSE in **symlog** depth but is scored on MAE in
**metres**, and symlog charges about a fifth as much for a metre of error at 16 m as at 1 m. So
the far field is systematically under-penalised in training and fully priced in the metric. That
is part of the copy-last gap — but not all of it, because the model is worse than copy-last even
in the nearest band.

## 13. mIoU 0.266 is not a plateau, it is class collapse — and the arithmetic is exact

Round 1 reported mIoU "flat at ~0.26" across every horizon and left it as an opaque number. The
per-class breakdown (pooled over the whole test split, so a frame with three fruit pixels cannot
dominate) says exactly what it is:

| class | IoU | share of GT pixels | share of **predicted** pixels |
|---|---|---|---|
| ground | 0.858 | 42.23% | 46.68% |
| fruit | **0.001** | 2.01% | **0.01%** |
| leaf | 0.379 | 19.64% | 19.14% |
| shoot | **0.016** | 6.22% | **0.25%** |
| petiole | **0.000** | 0.22% | **0.00%** |
| peduncle | **0.000** | 0.03% | **0.00%** |
| sky | 0.625 | 29.65% | 33.91% |

(0.858 + 0.001 + 0.379 + 0.016 + 0.000 + 0.000 + 0.625) / 7 = **0.268**. That is the number.

The model emits ground, leaf and sky and essentially nothing else. Four of the seven classes are
never predicted, score IoU 0, and are averaged in. Copy-last-frame reaches 0.333 for the trivial
reason that copying a real label map reproduces every class for free. So "the model's mIoU is
flat at 0.26" means "the model has dropped every thin and every rare class", which is the
expected behaviour of an unweighted cross-entropy on a distribution whose rarest class is 0.03%
of pixels — not evidence about dynamics, actions, or orchard diversity.

## 14. What sharpness allows: a blurred-ground-truth control

If the model's outputs carry 11.5% of the ground truth's gradient energy, how well could
*anything* score at that sharpness? `run_r2_blur_baseline.py` answers it with no model at all:
take the **correct** frame — the perfect prediction — blur it, and score it with exactly
`evaluate.py`'s metrics.

| Gaussian σ (px, at 64×64) | RGB sharpness | depth sharpness | depth MAE | RGB PSNR | mIoU |
|---|---|---|---|---|---|
| 0 (perfect) | 1.000 | 1.000 | 0.000 m | ∞ | 1.000 |
| 0.5 | 0.651 | 0.669 | 0.283 m | 28.03 dB | 1.000 |
| 1.0 | 0.271 | 0.336 | 0.622 m | 21.27 dB | 0.476 |
| 1.5 | 0.181 | 0.247 | 0.752 m | 20.29 dB | 0.392 |
| 2.0 | 0.139 | 0.199 | 0.841 m | 19.84 dB | 0.357 |
| 3.0 | 0.100 | 0.149 | 0.972 m | 19.35 dB | 0.324 |
| 4.0 | 0.080 | 0.121 | 1.071 m | 19.04 dB | 0.307 |
| 6.0 | 0.060 | 0.089 | 1.225 m | 18.62 dB | 0.288 |
| **copy-last-frame** | 0.992 | 0.985 | **0.657 m** | 16.71 dB | 0.333 |

### A correction to this section, made after the Round 2 runs

An earlier version of this section indexed the bound by **RGB** sharpness only. The Round 1
model's RGB sharpness is 0.115, which sits near σ ≈ 2.6, giving a bound of ~0.94 m and the
conclusion that ~90% of the model's depth deficit was blur. **That was wrong, and the run that
disproved it is `r2_best` (§18):** an L1 depth head produces a sharp depth map behind a *blurred*
RGB decode, so the two sharpnesses are not locked together and the RGB-indexed bound understates
what a model can reach on depth. Measured separately, depth sharpness is roughly twice RGB
sharpness for every model here (r1_main 0.228 vs 0.115; r2_main 0.220 vs 0.108; r2_best **0.281**
vs 0.105). The table now reports both, and the bound must be read off the **depth** column.

Re-read correctly:

1. **A uniformly blurred perfect predictor needs depth sharpness ≥ ≈0.31 to match copy-last-frame
   on depth MAE** (interpolating the 0.622 m / 0.752 m rows against copy-last's 0.657 m). Every
   model in this work is below that: 0.228 (Round 1), 0.220 (44 orchards), **0.281** (`r2_best`).
   So the conclusion that *the depth criterion is unreachable at the sharpness these models
   achieve* survives — but `r2_best` is close to the threshold rather than far from it.
2. **The blur share of the gap is much smaller than first claimed.** At Round 1's depth sharpness
   of 0.228 the bound is ~0.79 m, so of its 1.035 − 0.657 = 0.378 m deficit against copy-last,
   ~0.13 m (**35%**) is blur-irreducible and ~0.25 m (**65%**) is the model being worse than a
   perfectly-blurred oracle. For `r2_best`: bound ~0.72 m, deficit 0.224 m, of which ~0.06 m
   (28%) is blur. Blur is a real and binding constraint, but it is not 90% of the problem, and
   the earlier statement to that effect is retracted.
3. mIoU behaves differently again. The blurred oracle keeps ~0.32–0.36 at these sharpnesses while
   the models score 0.268–0.284 — so unlike depth, mIoU headroom is not mainly blur. That is
   consistent with §13: the mIoU gap is class collapse, and class collapse is fixable without
   touching sharpness (§18 shows it partly is).

This is still the most useful frame for reading Round 2. **Depth is limited by sharpness *and* by
accuracy in roughly a 1:2 ratio; mIoU is limited by class balance.** Neither is limited by the
number of orchards.

## 15. The growth channel: the action is a constant, and the RGB signal is at the noise floor

Round 1 reported that the growth channel does not work and attributed it to channel imbalance
(growth frames are 4% of the dataset, ~6% of the loss). `run_r2_growth_signal.py` measures the
channel itself, from the stored dataset only — no model, no rendering — and finds two problems
that sit upstream of any training decision.

### 15.1 The growth action is a constant

Collect the `a_grow` sequence of every growth episode in the dataset:

```
distinct a_grow sequences over 832 growth episodes: 1
  [5,5,5,5,5,5,10,0] x832
```

**One.** Every growth episode in train, val and test carries the identical action sequence — 320
of them in the Round 1 dataset, all 832 of them after the Round 2 extension. A
constant action carries no information beyond the frame index, so:

- nothing in the data can teach the model to respond to a *different* number of days;
- W6's "counterfactual growth" ablation — roll out with the growth action zeroed — was querying a
  value that appears nowhere in training. It is an out-of-distribution probe, not a
  counterfactual, and its result ("the model is *worse* with the true action than with it
  zeroed") is not evidence about action usage.

For contrast, the view action is not degenerate at all: per-dimension standard deviation
(0.0892, 0.0338, 0.0202, 0.0546) over 3,072 steps.

This is a **dataset design bug in Round 1's generator**, and it is the real reason the growth
channel had nothing to learn. It is also fixable without re-rendering anything — see §17.

### 15.2 In RGB, the growth signal is at the simulator's noise floor

Per-step ground-truth change between consecutive growth stages, on the held-out test orchards:

| stage step | age | a_grow | RGB PSNR | depth MAE | semantic mIoU | Δ fruit_vis |
|---|---|---|---|---|---|---|
| 0→1 | 540→545 | 5 d | 17.97 dB | 0.199 m | 0.484 | +0.0033 |
| 1→2 | 545→550 | 5 d | 21.04 dB | 0.123 m | 0.745 | +0.0024 |
| 2→3 | 550→555 | 5 d | 20.95 dB | 0.110 m | 0.777 | +0.0029 |
| 3→4 | 555→560 | 5 d | 20.91 dB | 0.092 m | 0.799 | +0.0032 |
| 4→5 | 560→565 | 5 d | 21.16 dB | 0.068 m | 0.836 | +0.0033 |
| 5→6 | 565→570 | 5 d | 21.14 dB | 0.061 m | 0.840 | +0.0038 |
| 6→7 | 570→580 | 10 d | 21.05 dB | 0.055 m | 0.868 | +0.0010 |
| **mean** | | | **20.60 dB** | 0.101 m | 0.764 | |

Compare that 20.60 dB with §9's measured **20.82 dB** simulator re-render reproducibility and the
growth step looks like pure noise. **That comparison is not quite fair**, because §9's floor was
measured on *view* episodes — different orchard, different poses, different scene content — and
the noise level depends on what is in frame. `run_r2_noise_floor.py` therefore measures both
quantities in the same run, at the same growth-probe poses, on the same held-out orchard (seed
12000), by rendering each stage **twice** without touching the scene:

| | RGB PSNR | RMS levels | depth MAE | semantic agreement |
|---|---|---|---|---|
| re-render the identical scene | **22.75 dB** | 18.57 | **0.000000 m** | **1.000000** |
| advance one growth stage | **20.41 dB** | 24.32 | 0.172 m | 0.949 |

At these poses the noise floor is 22.75 dB, not 20.82 dB. Subtracting the noise in quadrature
leaves a true growth signal of √(24.32² − 18.57²) = **15.70 RMS levels**, i.e. an **SNR of
0.85**. So the corrected statement is not "there is no RGB growth signal" — there is one, and it
is *smaller than the render noise it is embedded in*. Recovering it would require the model to
average over the noise, which it cannot do from a single stored realisation of each frame.

Depth and semantics are a completely different regime, and the same run proves it in the
strongest possible way: **re-rendering the identical scene reproduces depth to 0.000000 m and the
semantic map to 1.000000 agreement, at every one of the 8 stages**, while advancing a stage moves
depth by 0.11–0.31 m and the label map by ~5% of pixels. Their growth SNR is not 0.85 — it is
unbounded. If the growth channel is learnable at all, it is learnable in depth and semantics and
not in RGB. (The 540→545 step, at 17.97 dB and 0.199 m, is also the one step that rises clearly
above the noise in RGB too — that is where the canopy leafs out.)

For scale, one *view* step (a camera move) changes the image by 17.77 dB / 0.467 m / 0.339 mIoU.
A growth step is about 4.6× smaller in depth and 4.4× smaller in RGB RMS than a camera step.

### 15.3 95% of the growth change is scene-specific

Split each episode's stage-to-stage RGB delta into the part explained by the **mean** delta over
all episodes at that transition (a scene-independent "everything gets denser and greener" effect,
learnable from the action alone) and the residual:

| transition | delta RMS | mean-delta RMS | explained by the action alone |
|---|---|---|---|
| 540→545 | 32.46 | 6.36 | 3.8% |
| 545→550 | 22.79 | 5.26 | 5.3% |
| 550→555 | 23.12 | 5.29 | 5.2% |
| 555→560 | 23.35 | 4.90 | 4.4% |
| 560→565 | 22.74 | 4.64 | 4.2% |
| 565→570 | 22.80 | 4.41 | 3.7% |
| 570→580 | 23.08 | 4.90 | 4.5% |
| **mean** | | | **4.5%** |

So the growth channel asks the model to do the hardest available thing — predict where new leaves
and fruit appear on *this particular* canopy — with the least informative conditioning signal
available (a constant), in the modality where the signal is buried in render noise. Round 1's
negative result on growth was over-determined.

### 15.4 A growth evaluation that is actually a counterfactual

The stored growth episodes render the *same camera pose* at 8 known ages, so from the 545 d frame
a one-step prediction with `a_grow = d` has a real stored target for d ∈ {5, 10, 15, 20, 25, 35}
days. `run_r2_growth_eval.py` uses that to ask a question the data can answer. On the Round 1
model:

- **dt response**: predictions for d = 5 and d = 35 differ by RMS 0.053 against 0.144 for the
  corresponding ground-truth frames — 36.6% of real growth change. The action *does* move the
  prediction.
- **dt identification**: 16.7% over 6 candidates against a chance level of 16.7%; 25.0%
  restricted to the four in-distribution values against a chance level of 25.0%. **Exactly
  chance.** The confusion matrix shows why — whatever dt is asked for, the prediction lands
  nearest the 550 d frame:

```
        550    555    560    565    570    580
 5d      63      1      0      0      0      0
10d      63      1      0      0      0      0
15d      62      2      0      0      0      0
20d      64      0      0      0      0      0
25d      63      1      0      0      0      0
35d      64      0      0      0      0      0
```

The model always predicts "one stage on", regardless of how many days it was told to advance.
That combination — the prediction moves, but never toward the requested target — is what a model
conditioned on a constant looks like when you feed it a value it has never seen. It is a much
sharper result than Round 1's PSNR-based growth table, and it is a *negative* result stated
precisely.

## 16. Scaling the dataset from 12 to 44 train orchards: the Round 1 diagnosis was wrong

The dataset was extended exactly as the Round 2 brief specified. Final dataset: **44 train + 4 val
+ 4 test orchards**, 2,080 episodes, **166,400 frames**, 4.14 GB, generated at 241–330 s per
orchard (9,857 s total for the 32 new ones). Val and test are the *same four seeds each* as Round
1, and `run_r2_check_split.py` verifies against the manifest as written — not against the declared
ranges — that the three seed sets are pairwise disjoint, that every episode's `split` field matches
the directory it lives in, that every referenced file exists and that no two episodes share a path.
All pass. `r2_main` is trained with **identical hyperparameters to Round 1's `main2`**, so the only
difference is 3.7× the orchards.

### It does help the training objective, and it does delay overfitting

| | best validation reconstruction | at step | final (40k) |
|---|---|---|---|
| Round 1, 12 orchards (`main2`) | 0.7398 | 14,000 | 0.8341 (at 42k) |
| **Round 2, 44 orchards (`r2_main`)** | **0.6959** | **26,000** | 0.7167 |
| Round 2, no-action ablation | 0.7133 | 26,000 | 0.7344 |
| Round 2, growth-subsampled | 0.6841 | 32,000 | 0.7441 |

So the Round 1 story about the *loss* is confirmed and sharpened: more orchards give a **5.9%
better** validation optimum and push the overfitting onset from step 14k to 26k. The model really
was running out of orchards in the sense Round 1 meant.

### It does almost nothing for the metrics that matter

Held-out test orchards, 4 seeds, 96 view episodes, open-loop rollout from a 5-frame context —
the same protocol and the same test seeds as Round 1's table in §10:

| horizon | metric | Round 1 (12) | **Round 2 (44)** | change | copy-last |
|---|---|---|---|---|---|
| t+1 | RGB PSNR | 18.13 dB | **18.23 dB** | +0.10 | 16.71 dB |
| | depth MAE | 1.061 m | **1.038 m** | −2.2% | **0.657 m** |
| | mIoU | 0.265 | **0.268** | +1.1% | **0.333** |
| t+5 | RGB PSNR | 17.96 | **18.11** | +0.15 | 15.63 |
| | depth MAE | 1.117 | **1.077** | −3.6% | **0.968** |
| | mIoU | 0.266 | **0.271** | +1.9% | 0.264 |
| t+10 | RGB PSNR | 17.78 | **17.86** | +0.08 | 15.38 |
| | depth MAE | 1.171 | **1.120** | −4.4% | **1.096** |
| | mIoU | 0.263 | **0.268** | +1.9% | 0.250 |
| t+25 | RGB PSNR | 17.45 | **17.57** | +0.12 | 15.14 |
| | depth MAE | 1.256 | **1.197** | −4.7% | 1.205 |
| | mIoU | 0.253 | **0.256** | +1.2% | 0.237 |

**3.7× the orchards buys 2–5% on depth MAE and 1–2% on mIoU.** Neither success criterion moves:
depth still loses to copy-last-frame at every horizon except t+25 (where it wins by 0.7%), and
mIoU is still 0.27. Read against the **20.8 dB simulator noise floor** (§9), RGB PSNR went from
87.2% to 87.6% of the ceiling — the RGB channel was never the problem and is not where the gain
went either.

And the representation ceiling — the thing §12 identified as binding — barely moved:

| | posterior recon PSNR | depth MAE | mIoU | sharpness |
|---|---|---|---|---|
| Round 1, 12 orchards | 18.25 dB | 1.035 m | 0.268 | 0.115 |
| Round 2, 44 orchards | 18.30 dB | **1.022 m** | 0.270 | **0.108** |

**1.3% better depth, and sharpness got slightly *worse*.** The attribution is even more extreme
than in Round 1: 99% of `r2_main`'s t+1 depth error is already in the teacher-forced
reconstruction, and one step of dynamics adds 0.007 m to a 1.022 m error. Four of seven semantic
classes are still never predicted.

### Stated plainly

**Round 1's diagnosis — "the model is limited by orchard diversity, not compute" — is wrong as an
explanation of the held-out result, and the Round 2 brief built on it was aimed at the wrong
target.** It is right that the model overfits 12 orchards, and 44 orchards demonstrably overfit
later and reach a better validation optimum. But the held-out failure modes Round 1 actually
reported — losing to copy-last on depth, mIoU pinned at 0.26, no canopy structure — are not
diversity effects. They are, in order of size: an output-sharpness limit (§12, §14), a
class-collapse artefact of the unweighted cross-entropy (§13), and for the growth channel a
dataset design bug (§15). Tripling the orchards moved none of them by more than a few percent,
which is exactly what §12's train-vs-test measurement predicted before any of this was retrained.

### One thing that did get cleanly better: the action ablations

Round 1 had to report that at t+1 the *shuffled*-action rollout scored 0.01 dB **higher** than the
true-action one, which on its own reads as "the model ignores actions". With 44 orchards the
ordering is correct at every horizon:

| horizon | true actions | zeroed | shuffled | trained no-action model |
|---|---|---|---|---|
| t+1 | **18.23** | 18.22 | 18.20 | 18.15 |
| t+5 | **18.11** | 18.00 | 17.91 | 17.95 |
| t+10 | **17.86** | 17.74 | 17.65 | 17.65 |
| t+25 | **17.57** | 17.31 | 17.22 | 17.40 |

and the direct action-displacement probe agrees, growing from 23.2% of real inter-frame motion at
t+1 to 37.5% at t+25 (Round 1: 20.3% → 35.3%). The margin over the *trained* no-action model is
+0.08 to +0.21 dB, and best validation reconstruction differs by 2.5% (0.6959 vs 0.7133) in the
action-conditioned model's favour. Action conditioning is real and is now visible in PSNR as well
as in the probe — but it is worth remembering this is the one place where more data was the fix,
and it is the smallest of the three problems.

## 17. The growth channel: fixing the constant action works, and it is not enough

§15 found the growth action is a single constant across all 832 growth episodes. The fix costs no
rendering at all: build growth windows from a random increasing **subsequence** of the stored
stages, so `a_grow` takes 5/10/15/20-day values instead of one fixed sequence, and recompute it
from the stored ages. The frames are the same real renders; only the step between them changes.
Realised distribution over a training run: dt = 5 d ×427, 10 d ×456, 15 d ×383, 20 d ×74, mean
window length 3.79 stages (`--growth-fraction` is raised 0.25 → 0.40 to compensate for the shorter
windows).

Evaluated with the counterfactual of §15.4 — from the 545 d frame, predict with `a_grow = d` and
score against the stored frame at 545 + d:

| model | dt response | dt identification, all 6 (chance 16.7%) | dt identification, in-distribution 4 (chance 25.0%) |
|---|---|---|---|
| Round 1, 12 orchards | 38.4% | 16.7% — **exactly chance** | 25.0% — **exactly chance** |
| Round 2, 44 orchards, unchanged sampler | 41.1% | 16.1% — **chance** | 24.2% — **chance** |
| **Round 2 + stage subsampling** | **55.3%** | **25.0% — 1.50× chance** | **34.0% — 1.36× chance** |

The confusion matrix goes from degenerate to structured. Round 1 put every prediction, for every
requested dt, nearest the 550 d frame. With subsampling the mass spreads along the diagonal:

```
        550    555    560    565    570    580
 5d      55      7      2      0      0      0
10d      45     10      6      3      0      0
15d      33     18      7      6      0      0
20d      31     12      5     12      3      1
25d      24     11      8     11      7      3
35d      17      9     10     15      8      5
```

Two conclusions, and they point in opposite directions:

1. **The growth channel was not intrinsically unlearnable — it was a dataset bug.** Scaling the
   data from 12 to 44 orchards left dt identification at chance (16.1% vs 16.7%). Making the
   action non-constant, at zero rendering cost, lifted it to 1.5× chance. Round 1's "the growth
   channel does not work at this training scale" attributed to compute what was actually a
   degenerate action variable.
2. **It is still a long way from useful, and §15.2 says why.** Against copy-last-frame the
   subsampled model still loses at every dt on depth (1.36–1.41 m vs 0.26–0.88 m) and on mIoU
   (0.29–0.30 vs 0.44–0.73). It wins on RGB PSNR only from dt ≥ 15 d (18.91 vs 18.48 at 15 d,
   17.84 vs 16.11 at 35 d), i.e. only once the canopy has changed enough that copying fails. And
   dt identification at 34% against 25% chance is a real effect but a weak one.

The ceiling is measured, not guessed. At the growth probe poses the RGB growth signal has an
**SNR of 0.85** against the Monte-Carlo render noise (§15.2), and only **4.5%** of the stage-to-
stage change is explained by the action alone — the other 95% requires knowing where new leaves
and fruit will appear on *this* canopy, which is the same canopy-structure problem the view
channel fails at. Depth and semantics do carry unbounded-SNR growth signal, so that is where any
further work on this channel should be scored; RGB should not be.

**Recommendation, stated as a finding rather than a to-do:** the growth channel's action
degeneracy is fixed and should stay fixed (`--growth-subsample` costs nothing). Its remaining
failure is the same representation failure as the view channel, and it will not move until §12's
sharpness ceiling does.

## 18. What actually moved the held-out numbers: five single-factor runs and their combination

Six runs on the same 44-orchard dataset, same seeds, same 40k/30k budget, each differing from
`r2_main` in exactly one respect (except `r2_final`, which is the combination). Every number below
is the **held-out test split**, 4 orchards, 96 view episodes, open-loop rollout from a 5-frame
context — the same protocol as Round 1's §10.

### Teacher-forced reconstruction — the representation ceiling

| run | what changed | PSNR | depth MAE | mIoU | RGB sharpness | **depth sharpness** |
|---|---|---|---|---|---|---|
| `r1_main` | Round 1, 12 orchards | 18.25 dB | 1.035 m | 0.268 | 0.115 | 0.228 |
| `r2_main` | 44 orchards | 18.30 | 1.022 | 0.270 | 0.108 | 0.220 |
| `r2_big` | 4× parameters, 268-bit latent | 18.35 | 1.009 | 0.271 | 0.112 | 0.224 |
| `r2_sem` | class-weighted semantic CE | 18.26 | 1.026 | 0.281 | 0.104 | 0.214 |
| `r2_best` | class weights + L1 depth | 18.30 | 0.881 | 0.284 | 0.105 | **0.281** |
| `r2_kl` | free-bits 1→6, KL 0.5/0.1→0.2/0.04 | **18.67** | 0.887 | 0.287 | **0.127** | 0.260 |
| **`r2_final`** | **KL + class weights + L1** | 18.63 | **0.775** | **0.304** | 0.123 | **0.293** |
| *copy-last-frame* | — | *16.71* | *0.657* | *0.333* | *0.992* | *0.985* |

### Open-loop rollout — the numbers the success criteria are about

| horizon | | Round 1 | `r2_main` | `r2_big` | `r2_sem` | `r2_best` | `r2_kl` | **`r2_final`** | copy-last |
|---|---|---|---|---|---|---|---|---|---|
| **t+1** | PSNR | 18.13 | 18.23 | 18.22 | 18.14 | 18.23 | **18.51** | 18.47 | 16.71 |
| | depth | 1.061 | 1.038 | 1.033 | 1.063 | 0.904 | 0.919 | **0.810** | **0.657** |
| | mIoU | 0.265 | 0.268 | 0.269 | 0.275 | 0.279 | 0.282 | **0.294** | **0.333** |
| **t+5** | PSNR | 17.96 | 18.11 | — | 18.06 | — | 18.24 | 18.19 | 15.63 |
| | depth | 1.117 | 1.077 | — | 1.092 | — | 1.002 | **0.891** | 0.968 |
| | mIoU | 0.266 | 0.271 | — | 0.276 | — | 0.277 | **0.283** | 0.264 |
| **t+10** | PSNR | 17.78 | 17.86 | — | 17.78 | — | 18.00 | 17.82 | 15.38 |
| | depth | 1.171 | 1.120 | — | 1.145 | — | 1.061 | **0.975** | 1.096 |
| | mIoU | 0.263 | 0.268 | — | 0.265 | — | 0.268 | **0.269** | 0.250 |
| **t+25** | PSNR | 17.45 | 17.57 | 17.57 | 17.52 | 17.58 | 17.58 | 17.57 | 15.14 |
| | depth | 1.256 | 1.197 | 1.211 | 1.211 | 1.088 | 1.162 | **1.068** | 1.205 |
| | mIoU | 0.253 | 0.256 | 0.259 | 0.253 | 0.252 | 0.258 | **0.258** | 0.237 |

### Against the success criteria

**Depth MAE vs copy-last-frame (0.657 m at t+1): partially met, and the pattern is clean.** Round
1 lost at *every* horizon. `r2_final` **beats copy-last at t+5, t+10 and t+25** (0.891 vs 0.968;
0.975 vs 1.096; 1.068 vs 1.205 — margins of 8%, 11%, 11%) and still **loses at t+1** (0.810 vs
0.657). Against Round 1 the improvement is 24% / 20% / 17% / 15% across the four horizons. The
t+1 failure is exactly what §14 predicts: at `r2_final`'s depth sharpness of 0.293, a *uniformly
blurred perfect predictor* scores ~0.70 m, so 0.657 m is not reachable — but the threshold is
0.31 and the model is at 0.293, i.e. the criterion is now just out of reach rather than far out
of reach.

**mIoU above 0.266: met, modestly.** 0.265 → **0.294** on the rollout at t+1 and 0.268 → **0.304**
on the reconstruction, an 11–13% lift, and `r2_final` beats copy-last from t+5 onward. It is a
real gain from a diagnosed cause, not noise, but it is not a transformation, and at t+1
copy-last-frame is still ahead.

**RGB PSNR, reported against the 20.8 dB noise floor (§9) rather than as an absolute:** Round 1
reached 18.13 dB = **87.2%** of the ceiling; `r2_kl` and `r2_final` reach 18.51 / 18.47 dB =
**89.0% / 88.8%**. There is at most 2.3 dB of headroom in this channel and 0.34 dB of it was
taken. RGB was never where the problem was.

### Which interventions worked, ranked by effect on held-out depth MAE at t+1

| intervention | Δ depth MAE vs `r2_main` | Δ mIoU | cost |
|---|---|---|---|
| KL relaxation + class weights + L1 (`r2_final`) | **−0.228 m (−22%)** | +0.026 | none |
| class weights + L1 depth (`r2_best`) | −0.134 m (−13%) | +0.010 | none |
| KL relaxation alone (`r2_kl`) | −0.119 m (−11%) | +0.013 | none |
| class weights alone (`r2_sem`) | +0.025 m (**worse**) | +0.007 | none |
| 4× capacity (`r2_big`) | −0.005 m (−0.5%) | +0.001 | 4× parameters, ~2× wall clock |
| 3.7× the orchards (`r2_main` vs Round 1) | −0.023 m (−2%) | +0.003 | **2 h 45 m of ray tracing** |

The two things Round 1 and the Round 2 brief pointed at — **more data and more capacity — are the
bottom two rows.** Between them they bought 2.5% of depth MAE. Three hyperparameter and loss
changes that cost nothing bought 22%. That is the headline of this round.

### Why each fix worked, mechanistically

**The KL relaxation is the one that unblocks the representation.** Round 1's KL sat at 1.371 nats
— 2.0 bits per frame through a 160-bit latent — and `r2_big` is the proof that this is a penalty
problem and not a capacity problem: quadrupling the latent to 268 bits left the KL at **1.373**
and the metrics unchanged to three decimals. The model was not short of channel; it was declining
to use the channel it had. With free-bits 6 and weights 0.2/0.04 the KL runs at **6.2–6.3 nats**,
RGB sharpness rises 0.108 → 0.127 (the only intervention that moves it) and reconstruction depth
falls 1.022 → 0.887 m.

**L1 depth sharpens the depth head specifically, and it shows up exactly where predicted.** §12
found the error concentrated in the far field because MSE-in-symlog under-prices a metre of error
at 16 m by ~5×. Depth sharpness goes 0.220 → 0.281 while RGB sharpness does not move (0.108 →
0.105), and the far bins collapse:

| GT distance | `r2_main` | `r2_final` | copy-last |
|---|---|---|---|
| 0–2 m (35.0%) | 0.784 m | **0.673 m** | 0.681 m |
| 2–4 m (39.8%) | 0.620 m | **0.514 m** | 0.449 m |
| 4–8 m (18.7%) | 1.194 m | **0.815 m** | 0.668 m |
| 8 m+ (6.5%) | 4.296 m | **2.843 m** | 1.841 m |

`r2_final` **beats copy-last in the 0–2 m band** (0.673 vs 0.681) and the remaining deficit is
entirely the far field.

**Class weights do what §13 said they would, and no more.** The classes come back:

| class | `r1_main` IoU | `r2_final` IoU | copy-last IoU | GT pixels | `r2_final` predicted |
|---|---|---|---|---|---|
| ground | 0.858 | 0.868 | 0.870 | 42.23% | 40.64% |
| fruit | **0.001** | **0.119** | 0.192 | 2.01% | 2.69% |
| leaf | 0.379 | **0.444** | 0.433 | 19.64% | 24.27% |
| shoot | **0.016** | **0.135** | 0.137 | 6.22% | 5.01% |
| petiole | 0.000 | 0.000 | 0.007 | 0.22% | 0.00% |
| peduncle | 0.000 | 0.000 | 0.014 | 0.03% | 0.00% |
| sky | 0.625 | 0.643 | 0.653 | 29.65% | 27.39% |

Fruit goes from never predicted to 2.69% of pixels against 2.01% in the ground truth, shoot from
0.25% to 5.01% against 6.22%, and **shoot IoU (0.135) now essentially matches copy-last-frame's
(0.137)** while leaf IoU (0.444) *beats* it. Petiole (0.22% of pixels) and peduncle (0.03%) stay
at zero even with a 4× weight — at 64×64 they are one or two pixels wide, and they cap mIoU at
5/7 = 0.714 for any model at this resolution. Note also that class weights **alone** made held-out
depth slightly *worse* (`r2_sem`, 1.063 m vs 1.038 m): they buy semantics at a small cost in
depth, and only pay off cleanly in combination.

**The three compose almost additively** — depth 1.022 → 0.887 (KL) → 0.881 (weights+L1) →
**0.775** (all three); mIoU 0.270 → 0.287 → 0.284 → **0.304**; depth sharpness 0.220 → 0.260 →
0.281 → **0.293**.

### The growth channel, with the final model

`r2_final` was deliberately **not** trained with `--growth-subsample`, which makes it a clean
control: its dt identification is 16.9% against a 16.7% chance level — exactly chance, like
`r1_main` (16.9%) and `r2_main` (16.4%). Only `r2_growth`, the run with the augmentation, is above
chance (24.5%, and 33.2% vs 25.0% on in-distribution dt). **None of the loss, capacity or
bottleneck fixes touch the growth channel at all.** Its problem was, and is, that the stored
action is a constant (§15.1); fixing the sampler fixes it, and nothing else does.

### Two methodological notes

**Validation reconstruction is noisier than it looks.** With `--val-batches 8` (192 windows) the
val curve oscillates by ~7% step to step — `r2_final` runs 0.634, 0.644, 0.604, 0.605, 0.640,
0.599, 0.587, 0.604, 0.592, **0.569**, 0.595 over steps 17k–27k. Every run reports its best at
step 26,000, and that is not a coincidence about the models: all runs share `--seed 0`, so the
validation sampler draws the *same* windows at the same steps in every run. That makes fixed-step
cross-run comparison fair, but it means "best step" is partly a draw of the validation dice.
The held-out test evaluation (24 batches, separate seed) is the number to trust, and it is what
every table above reports.

**Validation reconstruction is not comparable across runs that change the loss.** `r2_sem`,
`r2_best`, `r2_kl` and `r2_final` change the scale of the semantic, depth or KL terms, so their
val-recon numbers (0.577, 0.635, 0.627, 0.569) cannot be compared with `r2_main`'s 0.696. Only
`r2_main`, `r2_noaction`, `r2_growth` and `r2_big` are on a common scale. This is why checkpoint
selection is done within-run and every comparison in this section is on the unweighted held-out
metrics.
