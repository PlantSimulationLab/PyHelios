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

## W3 — dataset generation — see below

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

## W5 — training — see below

## W6 — evaluation — see below

## W7 — reporting — **DONE**

`WORLD_MODEL_LOG.md`, `WORLD_MODEL_STATUS.md` (this file), `FINDINGS.md`.
`COMPLETE_SETUP_PATCH.md` holds the pointer text the plan asks to add to
`yogesh_dev/COMPLETE_SETUP.md`; that file is outside this task's write scope, so the text is
proposed rather than applied — the same pattern Phase 6 used for the gsplat fixes.
