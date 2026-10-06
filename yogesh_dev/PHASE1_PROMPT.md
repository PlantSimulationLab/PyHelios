# Task: Implement Phase 1 of the Helios setup plan (ground truth export)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 1** (section
"## Phase 1 — Ground truth export", tasks T1.1-T1.6). Later phases are out of scope.

**Phase 0 already produced working code you must build on**, at git branch
`worktree-phase0-radiation` (worktree `/home/yogesh/PyHelios/.claude/worktrees/phase0-radiation`
if still present, otherwise `git show worktree-phase0-radiation:yogesh_dev/phase0/<file>` to
read it). Relevant modules: `yogesh_dev/phase0/canopy.py` (tree builder),
`yogesh_dev/phase0/radiation_setup.py` (T0.1), `yogesh_dev/phase0/radiation_cameras.py`
(T0.2/T0.4 — pose convention already validated sub-pixel accurate). Copy/adapt what you need
from that branch rather than re-deriving it. Note from Phase 0: `Visualizer.getDepthMap()` is
broken upstream (returns only `{0.0, 255.0}`) — do not rely on it; T1.4 explicitly uses the
EXR writer path instead for exactly this reason.

Use the `helios` conda env for all Python: `/home/yogesh/anaconda3/envs/helios/bin/python`.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. Do not
touch `apple_tree.py`, `apple_tree_cameras.py`, `helios-core/`, `pyhelios/`, or anything with
uncommitted changes already in git status. No `git commit`/`push`/`checkout`/`stash`, no
`sudo`, no installs outside the `helios` env.

## Deliverables (`yogesh_dev/phase1/`)

- **T1.1 [BLOCKER for T1.2/T1.3]** — call `plantarch.optionalOutputObjectData([...])` with
  `plantID`, `fruitID`, `leafID`, `rank`, `age`, `phenology_stage`. Verify with
  `context.listObjectData(objID)` on a real fruit object that labels actually appear — don't
  assume the call worked.
- **T1.2** — export `fruit_ground_truth.json`: per fruit object, object ID, `plantID`,
  centroid, bounding box, equivalent diameter, surface area, primitive UUID list.
- **T1.3** — per-pixel semantic (`getPrimitiveDataLabelMap`) and instance
  (`getObjectDataLabelMap` on `fruitID`) maps per camera view, replacing any flat-color/
  nearest-color hack. Note the perf caveat in the task doc (text-file round trip) — fine for
  this dataset-generation use case, just don't pretend it's fast.
- **T1.4** — depth via `writeDepthImageDataEXR`, real EXR files on disk (needs
  `imageio`/`OpenEXR` — check what's available in the `helios` env first, install into that
  env only if genuinely missing and only via pip inside that env, not system-wide).
- **T1.5** — camera intrinsics/extrinsics per view in a `transforms.json`, gsplat-compatible
  format, using T0.2's real HFOV and T0.3's validated world-to-camera convention (don't
  re-derive the convention, it's already proven correct).
- **T1.6** — an RGB-D noise model: at minimum depth-edge mixed pixels and range-dependent
  noise, toggleable, with a before/after comparison so its effect is quantifiable.

Run everything end-to-end against the real 3-tree scene, on real `pyhelios` — not simulated.
If something is broken upstream (like T0.7's depth bug), document it rather than silently
working around it without saying so.

## Logging and completion

Continuously append to `yogesh_dev/PHASE1_LOG.md` (what you did, real numbers/output,
problems hit). When finished (or genuinely blocked), write `yogesh_dev/PHASE1_STATUS.md`
whose **last line** is exactly `STATUS: DONE` or `STATUS: BLOCKED: <reason>` — written last,
after everything else.
