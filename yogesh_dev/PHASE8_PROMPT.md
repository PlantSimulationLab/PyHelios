# Task: Implement Phase 8 of the Helios setup plan (scale-up)

Unattended headless run (`--dangerously-skip-permissions`), nobody watching interactively.
Follow the constraints below exactly rather than asking. This is the final phase in the plan.

## Context

Repo: `/home/yogesh/PyHelios`, branch `apple-tree-cameras`. Full plan:
`/home/yogesh/PyHelios/helios_setup_tasks.md` — **only implement Phase 8** (section
"## Phase 8 — Scale-up", tasks T8.1-T8.6).

**All of Phases 0-7 are already done and merged into this branch under `yogesh_dev/`** (camera
rig, ground truth, visibility/AVUB, kinematics, occupancy/planners, baselines/oracles, metrics
harness, foundation-model diagnostics) — reuse their real code rather than rebuilding.

**Already verified available in this environment (don't re-check, just use):**
- `apple_fruitingwall` exists in the plant library (`helios-core/plugins/plantarchitecture`),
  alongside the `apple` type used everywhere so far.
- `pyhelios.LiDARCloud` exposes real leaf-reconstruction methods:
  `triangulateHitPoints`, `calculateLeafArea`, `calculateSyntheticLeafArea`,
  `exportLeafAreaDensities`, `getCellLeafArea(Density)`, `setExternalTriangulation`,
  `getTriangulationStats`. Use these for real in T8.6, don't assume they don't exist.

**Real scale-honesty constraint**: this phase's full spec (T8.2's factorial sweep x T8.4's
"≥20 canopies/cell") could mean hundreds of full canopy builds + multi-view renders — likely
hours to days of wall-clock/GPU time, far beyond what's reasonable for one unattended budgeted
run. Do NOT silently truncate this and report it as if it were the full spec. Instead: **build
the real infrastructure for the full spec (real seeded generation, real factorial design, real
statistics functions), then run it at a clearly-labeled REDUCED scale** (e.g. 3-5 canopies/cell
instead of 20+, a screening subset of the factorial grid instead of the full grid) sufficient
to prove the pipeline is correct end-to-end, and report in the log exactly what scale was run,
what the full spec would require, and a real measured per-canopy cost so a human can estimate
the full run's wall-clock cost from your actual numbers.

Use the `helios` conda env: `/home/yogesh/anaconda3/envs/helios/bin/python`.

## HARD CONSTRAINT

Every file you create or modify must live under `/home/yogesh/PyHelios/yogesh_dev/`. Do not
touch `apple_tree.py`, `apple_tree_cameras.py`, `apple_tree_gaussian_splatting.py`,
`helios-core/`, `pyhelios/`, or anything with uncommitted changes already in git status. No
`git commit`/`push`/`checkout`/`stash`, no `sudo`, no installs outside the `helios` env unless
scoped and documented like Phase 5's `pulp`.

## Deliverables (`yogesh_dev/phase8/`)

- **T8.1** — seeded canopy generation, with disjoint dev/test seed sets (e.g. dev seeds
  1000-1999, test seeds 2000-2999, non-overlapping by construction, verify no overlap for
  real). Every later comparison in this phase must run on identical canopies across
  conditions (paired design) — implement this as a real, reusable canopy-factory function.
- **T8.2** — factorial sweep infrastructure: LAI x fruit density x clustering x trellis type.
  Implement the real factorial design (fractional-factorial screening design generation is
  fine — a full run isn't required, see scale-honesty constraint above), and actually execute
  it at the reduced scale, producing real per-cell results.
- **T8.3** — build canopies with `apple_fruitingwall` alongside the existing `apple` type,
  real comparison of the two (e.g. spacing/interpenetration behavior at the same density,
  matching the task doc's note that current 1.5m spacing already interpenetrates canopies
  under the plain `apple` type).
- **T8.4** — statistics: bootstrap CIs **resampling canopies, not views** (this is a real,
  easy-to-get-wrong distinction — make sure resampling actually happens at the canopy level),
  paired Wilcoxon signed-rank test, Cliff's delta effect size, Holm-Bonferroni correction for
  multiple comparisons. Implement all four for real (numpy/hand-rolled is fine, no scipy in
  this env per Phase 6/7's findings — verify that's still true rather than assuming) and
  demonstrate on the T8.2 reduced-scale results.
- **T8.5** — pre-registered metrics/seeds (write down, before running anything else new, which
  metrics and seeds are "the" evaluation — a real commitment artifact, not just a mention), and
  the Tatarchenko degenerate-baseline check: verify a deliberately stupid baseline (e.g. a
  constant/no-op policy) does NOT already score well on whatever headline metric you're using
  from Phase 5/6 — this must be a real empirical check with a real result, not an assertion.
- **T8.6** — digital-twin path: use `pyhelios.LiDARCloud`'s real leaf-by-leaf reconstruction
  (`triangulateHitPoints` etc.) on a simulated point cloud scan of one real Helios canopy
  (there's no actual real-world tree available in this environment — synthesize a realistic
  LiDAR scan of a real Helios canopy as the "digital twin" input, document this substitution
  clearly), report the same real metric vector (from Phase 6) on both the original sim canopy
  and its LiDAR-reconstructed "twin," and check **rank preservation**: do different planners
  (Phase 4/5's real policies) rank the same way on both.

## Logging and completion

Continuously append to `yogesh_dev/PHASE8_LOG.md` (what scale you actually ran vs. the full
spec and why, real numbers, real per-canopy timing so a human can extrapolate full-scale cost,
problems hit). When finished (or genuinely blocked), write `yogesh_dev/PHASE8_STATUS.md` whose
**last line** is exactly `STATUS: DONE` or `STATUS: BLOCKED: <reason>` — written last, after
everything else. Since this is the final phase in the plan, also write a one-paragraph closing
summary in the status file of what the whole `yogesh_dev/` body of work now covers end-to-end.
