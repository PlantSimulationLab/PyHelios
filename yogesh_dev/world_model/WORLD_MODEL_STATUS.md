# World Model — task-by-task status

Legend: **DONE** = deliverable exists and its acceptance criterion was checked against real
output · **PARTIAL** = deliverable exists, acceptance only partly met (reason stated) ·
**NOT DONE** = stated plainly with why.

Numbers here are summaries; `FINDINGS.md` has the detail and `WORLD_MODEL_LOG.md` the
chronology. Every number is produced by a script in this directory and every script writes its
own JSON + log under `output/`.

---

## W0 — orchard factory + measurement — **DONE**

Deliverable: `orchard.py`, `run_w0.py`, `run_w0b.py`, `run_w0c.py`.
Output: `output/w0/w0_measurements.json`, `w0b_age_curve.json`, `w0c_growth_window.json`.

Acceptance (*"two builds with the same seed produce identical primitive counts; two different
seeds differ; age→fruit curve written to JSON"*): **passed.**
Same seed 10000 twice → 830,392 primitives / 519 fruit objects / identical organ counts.
Seed 10001 → 846,331 / 549. Age→fruit curve written, on a 10-day grid from 520 to 800 d.

Beyond the acceptance criterion, W0 measured the thing the plan listed as UNKNOWN
(`advanceTime` cost at 20-tree scale: 0.9–5.1 s vs 6.7–37.8 s for a rebuild) and found that the
plan's recommended growth schedule sits in a region where the plant model does not change at
all. See FINDINGS §1.

## W1 — batched observation rig — **DONE**

Deliverable: `render.py`, `run_w1.py`. Output: `output/w1/`.

Acceptance (*"a contact sheet a human can look at and see a recognisable orchard row; depth EXR
with sane min/max; semantic class histogram matching the organ counts"*): **passed.**
- `output/w1/contact_rgb.png` and `hires_*_rgb.png` show green foliage, brown trunks,
  red-orange apples, textured ground and sky.
- Depth over 16 frames: 0.780–18.048 m against a 17.07 m orchard bounding-box diagonal; the
  depth sky mask agrees with the semantic sky mask on **100.0000%** of pixels.
- Semantic histogram over 128 views: ground 45.66%, leaf 24.39%, sky 18.43%, shoot 7.26%,
  fruit 3.98%, petiole 0.27%, peduncle 0.01% — ordering consistent with the organ primitive
  counts, with the expected shoot deficit (branches are thin and self-occluded).

Also re-verified the batching table and probed N=256 (solve time flat at ~4.85 s throughout),
and added a reprojection check the plan did not ask for but which caught a real bug: fruit
world-centroid vs instance-mask centroid, **mean 0.80 px / median 0.71 px** over 135
observations at 128×128.

## W2 — action spaces and trajectory samplers — **DONE**

Deliverable: `actions.py`, `run_w2.py`. Output: `output/w2/w2_measurements.json`.

Acceptance (*"trajectories stay inside the orchard bounds and inside the inter-row lane;
replaying recorded actions from the start pose reproduces the recorded poses to < 1e-6"*):
**passed.** 600 trajectories (3 families × 200 × 128 steps): every state in bounds; worst
replay error **4.71e-7** (the residual is float32 quantisation of the stored actions, which is
what the plan's own schema specifies).

Reported honestly: `orbit` trajectories pass through canopy volume 41.8% of the time on
average (max 76.6%). Helios cameras have no collision, so this is geometrically well-defined
but physically unrealisable; it is measured rather than prevented, and the lane families are
bounds-checked against the lane while orbits are checked against the orchard's outer bounds.

## W3 — dataset generation — **PARTIAL** (scale reduced; one acceptance criterion fails, with a measured explanation)

Deliverable: `generate.py`, `run_w3_verify.py`, `run_w3_determinism_probe.py`.
Output: `output/dataset/` (800 episodes, **64,000 frames**, 1.61 GB), `output/w3/`.

**Scale reduced, deliberately and reported.** The plan targets ~40 orchard seeds × 8 growth
stages × 128 views ≈ 40 k frames. What was generated: **12 train + 4 val + 4 test = 20 orchard
seeds** × 8 growth stages × (3 families × 128 views + 16 growth probes) = **64,000 frames** —
more frames than the plan's target, but from half as many orchards. Generation ran at 254–323 s
per orchard and was stopped after 20 to leave time for training and evaluation. §11 of
`FINDINGS.md` shows this reduction is the binding constraint on the model: it overfits 12 train
orchards after ~15 k steps.

Acceptance, part 1 (*"train/val/test seed sets are provably disjoint"*): **passed**, checked both
as declared ranges and as seeds actually present in the manifest — zero overlap in all three
pairs. Split is by orchard seed, never by frame.

Acceptance, part 2 (*"regenerating one shard with the same seed is byte-identical"*): **fails**,
0/40 episodes. The per-array diagnostic makes it precise rather than mysterious: `depth`,
`semantic`, `pose`, `state`, `a_view` and `fruit_vis` are **bit-exact**; `instance` differs on
0.0042% of pixels with an identical 796-ID set and a fruit-mask IoU of 1.0; only `rgb` genuinely
differs, because the OptiX Monte-Carlo radiative solve samples with an RNG PyHelios does not
expose. See FINDINGS §9 — including the consequence that re-rendering the same frame twice
agrees only to **20.8 dB PSNR**, which is a ceiling on any model's held-out RGB score.

## W5 — training — **DONE**

## W4 — world model implementation — **DONE**

Deliverable: `rssm.py`, `train.py`, `run_w4.py`. Output: `output/w4/w4_results.json`,
`overfit_recon.png`.

Acceptance (*"overfits a single trajectory to near-zero reconstruction loss"*): **passed.**
Teacher-forced reconstruction on one real recorded trajectory: PSNR **30.67 dB**, SSIM 0.956,
depth MAE **0.047 m**, semantic mIoU **1.000**. Open-loop imagination from a 5-frame context on
the same trajectory holds 31.0 / 30.9 / 31.1 / **30.1 dB** at t+1 / t+5 / t+10 / t+25, which is
the part that shows the *dynamics* work rather than just the autoencoder.

The first attempt at this run diverged in its last 500 steps (Adam eps=1e-8); see
`WORLD_MODEL_LOG.md` §5.

Deliverable: `train.py`, `plot_curves.py`. Output: `output/train/{main2,noaction2}/`,
`output/w5/curves.png`, `curve_summary.json`.

Acceptance (*"validation loss curve saved; checkpoints resumable"*): **passed.**
`output/w5/curves.png` plots train and validation for all four reconstruction heads plus KL and
total loss, for the main model and the no-action ablation. Resumability was not just implemented
but exercised: a run was resumed from step 30,000 and continued to 42,000 with optimiser state
and step count intact.

Two models were trained identically except for `--zero-actions`: 64×64, batch 24, sequence 32,
~11 it/s, concurrently on one RTX 5090. Best validation reconstruction for both is at step
**14,000** — main **0.7407**, no-action **0.7605**, a 2.7% gap in the action-conditioned model's
favour.

A real bug was found and fixed here: selecting the best checkpoint on *total* validation loss
picks the wrong model, because the KL term rises monotonically as the model uses more latent
capacity while every reconstruction term falls. The original rule froze "best" at step 5,000 and
discarded the genuinely best model at 14,000. Selection is now on validation reconstruction.

## W6 — evaluation — **DONE**, and the result is largely negative

Deliverable: `evaluate.py`, `gsplat_baseline.py`. Output: `output/w6/w6_results.json`,
`rollout_*.png`, `gsplat_baseline.json`; a 30 k-step snapshot in `output/w6_30k/`.

All four required elements were produced against real held-out data (4 test orchard seeds, 96
view + 64 growth episodes): horizon-resolved open-loop rollout quality, action fidelity,
counterfactual growth, and all three required baselines (copy-last-frame, a **separately trained
no-action model**, and a 3DGS view-synthesis reference in two information settings).

Acceptance (*"every number is produced by a re-runnable script; the no-action ablation is
strictly worse than the full model, or the model is ignoring actions and this must be reported
as a negative result"*): **passed, with the negative result reported.**

- The full model beats copy-last-frame on RGB PSNR at every horizon (18.13→17.45 dB vs
  16.71→15.14 dB) and beats the trained no-action model at every horizon, with the margin
  growing from +0.04 dB at t+1 to +0.25 dB at t+25.
- **But** it *loses* to copy-last-frame on depth MAE at every horizon (1.06 m vs 0.66 m at t+1),
  its mIoU is flat at ~0.26, and at t+1 the shuffled-action rollout scores 0.01 dB *higher* than
  the true-action one. The qualitative rollouts show the model has learned the orchard's global
  layout and essentially no canopy structure.
- **The growth channel does not work**: up to t+3 the full model is worse than itself with the
  growth action zeroed, worse than the trained no-action model, and worse than copy-last-frame.
- A methodological finding: the plan's PSNR-based no-action ablation is a weak instrument when
  predictions are blurry. A direct probe added here (`action_sensitivity`) shows zeroing the
  action displaces the prediction by 20.3% (t+1) to 35.3% (t+25) of the magnitude of real
  inter-frame motion — substantial action-conditioning that the PSNR ablation understated by an
  order of magnitude.

LPIPS is **not reported**: `lpips` is not installed in the `gsplat` env and there is no network
access. SSIM is reported instead and the substitution is stated rather than made silently.

## W7 — reporting — **DONE**

`WORLD_MODEL_LOG.md`, `WORLD_MODEL_STATUS.md` (this file), `FINDINGS.md`.
`COMPLETE_SETUP_PATCH.md` holds the pointer text the plan asks to add to
`yogesh_dev/COMPLETE_SETUP.md`; that file is outside this task's write scope, so the text is
proposed rather than applied — the same pattern Phase 6 used for the gsplat fixes.

### Slack notification — **NOT SENT, and the cause is known** (corrected in Round 2)

The plan (rule 5) and the Round 1 task both ask for a `notify_slack()` call on completion. Every
long-running entrypoint here is wrapped in the required try/except that calls it, and none of
them delivered anything.

Round 1 recorded this as an unexplained anomaly — that `notify_slack.py` had been present at the
start of the session and was gone by the end, with nothing in this work's commits touching it.
**That framing was wrong and is retracted here.** The explanation is mundane: `notify_slack.py`
and `~/.config/claude-notify/slack_webhook_url` were **deleted deliberately by the user on
2026-07-30**, mid-run, because Slack notification was no longer wanted. Nothing malfunctioned and
nothing was lost.

The consequence for this directory: the notification is **permanently removed, not pending**. The
guarded call sites are harmless — `from notify_slack import notify_slack` raises `ImportError`
inside a bare `except Exception: pass`, so they no-op — and they are left in place rather than
stripped, because editing them would touch eight files for no behavioural change. Do not
recreate `notify_slack.py`, and do not report its absence as an anomaly again. Round 2 adds no
new notification call sites.

---
---

# ROUND 2 — task-by-task status (2026-07-31)

Round 2's brief was: extend the dataset to 40+ train orchards, then revisit regularisation and the
growth channel, with success defined as beating copy-last-frame on **depth MAE** and lifting
**mIoU** meaningfully above 0.266 on held-out orchards.

## R2-W3 — dataset extension — **DONE**

`generate.py --resume --n-train 44`, `run_r2_check_split.py`.
Output: `output/dataset/` (**2,080 episodes, 166,400 frames, 4.14 GB**), `output/r2/r2_split_check.json`.

**44 train + 4 val + 4 test orchards** (Round 1: 12/4/4). Train seeds 10012–10043 are new; val and
test are the *same four seeds each* as Round 1, so every held-out number is directly comparable.
Generation: 241–330 s per orchard, 9,857 s total for the 32 new ones. `--resume` reuses the stored
calibration, so the global exposure scale and pixel orientation are byte-identical to Round 1's.

Acceptance (*splits provably disjoint*): **passed**, and checked harder than in Round 1 — against
the manifest **as written** rather than the declared ranges, plus that every episode's `split`
field matches its directory, that every referenced file exists, and that no two episodes share a
path. Zero violations on all four checks.

## R2-A — is the growth channel learnable? — **DONE**, and it found a dataset bug

`run_r2_growth_signal.py`, `run_r2_noise_floor.py`, `run_r2_growth_eval.py`.

The brief asked to establish with evidence whether the growth signal is degenerate. It is, for two
independent reasons, and one of them is a bug in Round 1's generator:

1. **The growth action is a constant.** All **832** growth episodes carry the identical `a_grow`
   sequence `[5,5,5,5,5,5,10,0]` — one distinct sequence in the whole dataset. Round 1's
   "counterfactual growth" ablation was therefore an out-of-distribution query, not a
   counterfactual.
2. **The RGB growth signal is below the render noise.** Measured at the same poses on the same
   orchard: re-rendering the identical scene gives 22.75 dB, advancing one stage gives 20.41 dB,
   so the growth signal is 15.70 RMS levels against 18.57 of Monte-Carlo noise — **SNR 0.85**.
   Depth and semantics are the opposite: **bit-exact across re-renders at all 8 stages**
   (0.000000 m, 1.000000 agreement) while moving 0.11–0.31 m and ~5% of pixels per stage.
3. Only **4.5%** of the stage-to-stage change is explained by a scene-independent mean delta.

**The action degeneracy is fixable at zero rendering cost** (`--growth-subsample`: build growth
windows from a random increasing subsequence of the stored stages). Measured with a real
counterfactual — from the 545 d frame, predict with `a_grow = d` and score against the stored
frame at 545 + d:

| model | dt identification (all 6, chance 16.7%) | in-distribution 4 (chance 25.0%) |
|---|---|---|
| Round 1 | 16.9% — chance | 25.4% — chance |
| 44 orchards, unchanged sampler | 16.4% — chance | 24.6% — chance |
| 44 orchards + `--growth-subsample` | **24.5%** | **33.2%** |
| `r2_final` (no subsampling; control) | 16.9% — chance | 25.4% — chance |

So the growth channel was **not intrinsically unlearnable — it was a degenerate action variable**,
and no amount of data or loss tuning touches it. It remains far from useful (it loses to
copy-last on depth and mIoU at every dt) and §15.2 gives the measured reason.

## R2-C — where the error comes from — **DONE**, and it overturned the Round 1 diagnosis

`run_r2_recon_floor.py`, `run_r2_blur_baseline.py`.

Teacher-forced posterior reconstruction on held-out orchards — the upper bound on any rollout —
is **1.035 m** depth MAE for the Round 1 model against **1.067 m** for its open-loop t+1 and
0.657 m for copy-last. **97% of the t+1 depth error is the autoencoder.** On *train* orchards the
same model reconstructs at 1.020 m: a **1.5%** generalisation gap. Per-class IoU shows mIoU 0.266
is class collapse — four of seven classes never predicted, and the seven per-class IoUs average
to the reported number exactly.

## R2-D…R2-J — six single-factor runs + their combination — **DONE**

`train.py` (new: `--sem-class-weights`, `--depth-loss`, `--kl-dyn/--kl-rep`, `--weight-decay`,
`--growth-subsample`), `run_r2.sh` … `run_r2f.sh`.
Output: `output/train/r2_*/`, `output/r2_w6*/`, `output/r2/`.

Held-out test split, t+1, open-loop from a 5-frame context:

| run | change from `r2_main` | depth MAE | mIoU | PSNR |
|---|---|---|---|---|
| Round 1 baseline | 12 orchards | 1.061 m | 0.265 | 18.13 dB |
| `r2_main` | 44 orchards | 1.038 | 0.268 | 18.23 |
| `r2_big` | 4× parameters, 268-bit latent | 1.033 | 0.269 | 18.22 |
| `r2_sem` | class-weighted semantic CE | 1.063 | 0.275 | 18.14 |
| `r2_best` | class weights + L1 depth | 0.904 | 0.279 | 18.23 |
| `r2_kl` | free-bits 1→6, KL 0.5/0.1→0.2/0.04 | 0.919 | 0.282 | **18.51** |
| **`r2_final`** | **all three** | **0.810** | **0.294** | 18.47 |
| *copy-last-frame* | | *0.657* | *0.333* | *16.71* |

## Acceptance against the Round 2 success criteria

**Depth MAE vs copy-last-frame — PARTIALLY MET.** Round 1 lost at every horizon. `r2_final` beats
copy-last at **t+5 (0.891 vs 0.968), t+10 (0.975 vs 1.096) and t+25 (1.068 vs 1.205)** and loses
at **t+1 (0.810 vs 0.657)**. Improvement over Round 1: 24% / 20% / 17% / 15%. The residual t+1
failure is bounded, not mysterious: at `r2_final`'s depth sharpness of 0.293 a *uniformly blurred
perfect predictor* scores ~0.70 m, and the sharpness needed to reach 0.657 m is ~0.31.

**mIoU meaningfully above 0.266 — MET, MODESTLY.** 0.265 → **0.294** on the rollout, 0.268 →
**0.304** on the reconstruction (+11% / +13%), and `r2_final` beats copy-last from t+5 onward.
Petiole (0.22% of pixels) and peduncle (0.03%) remain at IoU 0 at 64×64, which caps mIoU at
5/7 = 0.714 for any model at this resolution.

**RGB PSNR against the 20.8 dB simulator noise floor — not chased, as instructed.** 87.2% of the
ceiling in Round 1 → 89.0% (`r2_kl`) / 88.8% (`r2_final`).

**Action conditioning — now clean.** Round 1 had to report that the shuffled-action rollout beat
the true-action one at t+1. With 44 orchards the ordering is correct at every horizon, and the
direct displacement probe grows 23.2% → 37.5% of real inter-frame motion over t+1 → t+25.

## The correction this round owes Round 1 (and its own brief)

Round 1 concluded "the model is limited by orchard diversity, not compute", and the Round 2 brief
was built on it. **That diagnosis is wrong as an explanation of the held-out result.** It is
correct about the loss — 44 orchards give a 5.9% better validation optimum and push the
overfitting onset from step 14k to 26k — but the held-out failures it was invoked to explain are
not diversity effects:

| lever | Δ held-out depth MAE at t+1 | cost |
|---|---|---|
| 3.7× the orchards | −2% | 2 h 45 m of ray tracing |
| 4× the parameters | −0.5% | 4× parameters, ~2× wall clock |
| KL relaxation + class weights + L1 depth | **−22%** | nothing |

`r2_big` is the cleanest single piece of evidence: quadrupling the latent from 160 to 268 bits
left the KL at **1.373 nats**, unchanged to three decimals, and the metrics unchanged with it.
The model was never short of capacity or of orchards — it was declining to use the channel it had,
because the KL penalty made information expensive. That is a hyperparameter, and it was free to
fix.

## R2 reporting — **DONE**

`FINDINGS.md` §12–§18, `WORLD_MODEL_LOG.md` Round 2 sections, this file. Round 1's Slack anomaly
note is retracted above (§W7): `notify_slack.py` and the webhook file were deleted deliberately by
the user on 2026-07-30, mid-run. Round 2 adds no notification call sites.

One self-correction is recorded in `FINDINGS.md` §14 rather than quietly fixed: the
blurred-ground-truth bound was first indexed by RGB sharpness, which put ~90% of the depth deficit
down to blur. `r2_best` disproved it by producing a sharp depth map behind a blurred RGB decode.
Re-indexed by depth sharpness the blur share is ~35% (Round 1) and ~28% (`r2_best`), and the
earlier claim is retracted.
