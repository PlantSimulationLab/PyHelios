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
