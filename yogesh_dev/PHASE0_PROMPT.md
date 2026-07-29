# Task: Implement Phase 0 of the Helios setup plan

You are running unattended (headless, `--dangerously-skip-permissions`) inside a detached
tmux session on a devbox. Nobody is watching this run interactively — there is no human to
approve anything mid-run, so follow the constraints below exactly rather than asking.

## Context

Repo: `/home/yogesh/PyHelios` (git branch `apple-tree-cameras`). This is PyHelios — Python
bindings for the Helios plant-simulation/radiation-modeling C++ library (submodule at
`helios-core/`). The repo has an apple-tree canopy generator (`apple_tree.py`), a
Visualizer-based 3-camera capture rig (`apple_tree_cameras.py`), and a working Gaussian-splatting
training pipeline.

The full multi-week task list lives at `/home/yogesh/PyHelios/helios_setup_tasks.md`.
**Only implement Phase 0** (the section "## Phase 0 — Radiation camera migration and honest
benchmarking", tasks T0.1 through T0.7). Every later phase (1-8) is out of scope for this run —
do not start them.

Read these existing files for reference before writing anything:
- `helios_setup_tasks.md` — Phase 0 section is your spec, read it in full
- `apple_tree.py` — canopy builder
- `apple_tree_cameras.py` — existing Visualizer camera rig; the `CAMERA_RIGS` pattern here is
  what you're porting to `RadiationModel` cameras
- Anything under `docs/` that demonstrates `RadiationModel` / `addRadiationCamera` usage
- `docs/examples/primitive_data_sample.py` if relevant

## Environment

Use the `helios` conda environment for all Python execution:
`/home/yogesh/anaconda3/envs/helios/bin/python`. It already has `pyhelios` installed and
importable — verify with `import pyhelios` before relying on it. Do not create a new
environment, do not `pip install` into other environments, do not modify the conda env itself.

## HARD CONSTRAINT — read this twice

**Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`.**
This directory is yours. Do not edit, move, or delete any file outside it — not
`apple_tree.py`, not `apple_tree_cameras.py`, nothing in `helios-core/`, nothing in
`pyhelios/`. If you need code from an existing file, copy it into `yogesh_dev/` and adapt
the copy there. This applies even to files that already show uncommitted changes in
`git status` — leave them exactly as they are; do not `git checkout` or `git stash` them
either.

Additional hard rules:
- No `git commit`, `git push`, `git checkout`, `git stash`, or anything else that changes
  repo/branch state.
- No `sudo`, no installing system packages, no writing outside the repo.
- Do not touch the `helios-core/` submodule.
- If a task requires something outside these bounds (T0.6's C++ binding option), do **not**
  implement it — see the T0.6 handling below.

## Deliverables (all inside `yogesh_dev/`)

Build a `yogesh_dev/phase0/` package with working, actually-runnable code for:

- **T0.1** — radiation band + light source setup. Explicitly decide and write down whether
  you're doing "plausible RGB" or real-spectra radiometry, per the task doc.
- **T0.2** — the 3 cameras defined as `RadiationCamera`s: pinhole (`lens_diameter=0.0`),
  `HFOV` correctly converted from the existing *vertical* FOV convention in
  `apple_tree_cameras.py` (`HFOV = 2*atan(aspect * tan(VFOV/2))`), `camera_resolution`
  starting at `(640, 480)`, `antialiasing_samples` in the 1-4 range.
- **T0.3 [BLOCKER]** — empirically verify the radiation camera's pose convention: place
  5-10 spheres at known world coordinates spanning the frame, render, and check each
  sphere's image centroid against the projected `K·[R|t]·X`. This must actually execute
  against `pyhelios` and report a real measured result (sub-pixel or not) — not a
  theoretical writeup. If the convention differs from Visualizer's, document the actual
  discovered convention.
- **T0.4** — correct render loop structure: `updateGeometry()` called once outside the pose
  loop, one `runBand()` call per pose covering all bands together (never once per band).
- **T0.5 [BLOCKER]** — an honest benchmark with real measured numbers (not estimates):
  Tier B (`Visualizer.plotUpdate()` + `getDepthMap()`) vs Tier C (`runBand` at 640x480,
  AA=1, 3 cameras, scattering depth 1), plus a resolution/AA sweep. Record primitive count
  per tree too.
- **T0.7** — wire `Visualizer.getDepthMap()` into a Tier-B rig, as a fresh copy/adaptation
  inside `yogesh_dev` (do not edit the original `apple_tree_cameras.py`).

**T0.6 is a decision task, not an implementation task.** Do not attempt to write the
C++/pybind11 `CollisionDetection` binding — that touches `helios-core` and is out of scope
for an unattended run. Instead write `yogesh_dev/PHASE0_DECISIONS.md` recommending one of
the three T0.6 options with concrete reasoning drawn from what you actually learn in
T0.1-T0.5, so a human can decide whether to greenlight the C++ work later.

## Logging (required — this is how your work gets reviewed later)

Continuously append to `yogesh_dev/PHASE0_LOG.md`: what you did, key code decisions, the
actual numbers you measured (report real data, don't round it away), and any problems you
hit and how you resolved or worked around them.

## Completion

When you finish — or if you get genuinely stuck and cannot make further progress within
these constraints — write a final file `yogesh_dev/PHASE0_STATUS.md` whose **last line** is
exactly one of:

```
STATUS: DONE
STATUS: BLOCKED: <one-line reason>
```

This is the literal signal the orchestrating process is watching for. Write it last, after
everything else is finished, and make sure it is the final line of that file.
