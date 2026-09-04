# Phase 8 Pre-registration (T8.5)

Written before any T8.2/T8.3/T8.4/T8.6 experiment is executed (T8.1's `canopy_factory.py`
is infrastructure, smoke-tested but producing no reported result -- this document commits
to what counts as "the" evaluation before any of those results exist). If a later section
of this phase needs something not listed here, that is a deviation and must be logged as
one in `PHASE8_LOG.md`, not silently folded in.

## Headline metric

**`mean_coverage_frac`**: the area-weighted mean, over all fruit in a canopy, of the
fraction of each fruit's real surface area that is visible (unoccluded + in-frustum,
ray-traced nearest-hit) across the union of every view a policy actually used. This is
exactly Phase 2/5's `fruit_visible_fraction` / `coverage_summary` machinery
(`yogesh_dev/phase2/visibility.py`, `yogesh_dev/phase5/common.py`), reused unchanged.

**Secondary metric**: `fraction_fruit_observed` -- fraction of fruit with coverage > 0
(from the same `coverage_summary` call, always computed alongside the headline metric).

## Policies compared (T8.2 sweep, T8.4 statistics)

Two policies, applied identically to every canopy in every factorial cell:

- **`fixed_rig`**: 3 fixed camera positions per tree (above/level/below height fractions
  0.05/0.5/1.15 of tree height, Phase 0's `CAMERA_RIGS` convention), no motion. The
  realistic static-hardware alternative (mirrors Phase 5's T5.2).
- **`reachable_union`**: union visibility over a small reachable-pose grid (rail x
  height x depth in front of the tree, Phase 2's `placeholder_reachable_poses`
  mechanism at reduced density for this phase's budget -- see `PHASE8_LOG.md` for the
  exact grid size and why). The small-grid ceiling (mirrors Phase 5's T5.8).

These two are pre-registered as the paired comparison T8.4's Wilcoxon/Cliff's-delta
statistics run on (`reachable_union` vs `fixed_rig`, per canopy, matched by seed).

## Degenerate baseline (Tatarchenko check, T8.5)

**`look_away`**: one camera at the same standoff distance and height as `fixed_rig`'s
"level" position, but boresight rotated 180 degrees in azimuth (facing directly away
from the canopy, at the same height, same distance). Pre-registered expectation:
`mean_coverage_frac` for `look_away` must be statistically indistinguishable from 0 and
far below `fixed_rig`'s. If it is not, `mean_coverage_frac` is a degenerate metric (a
policy that looks at nothing already "wins") and must not be trusted as this phase's
headline number without further investigation.

## Seeds

- **Dev seeds** (used for the T8.2 factorial sweep and all T8.4 statistics in this run):
  `{1000, 1001, 1002}` -- 3 canopies/cell, drawn from `DEV_SEEDS = range(1000, 2000)`.
  This is a REDUCED count from the task spec's "&ge;20 canopies/cell" -- see
  `PHASE8_LOG.md` for the real per-canopy cost measurement this reduction is based on,
  and what the full spec would cost at that measured rate.
- **Test seed** (reserved, used ONLY by T8.6's digital-twin canopy, never touched by
  T8.2/T8.4): `{2000}`, drawn from `TEST_SEEDS = range(2000, 3000)`. Kept out of the dev
  sweep so the twin-vs-original rank-preservation check in T8.6 is not contaminated by
  having already been used to tune anything in T8.2/T8.4.
- Both ranges are verified disjoint by `canopy_factory.verify_disjoint_seeds()` (real
  set-intersection check, not just "obviously true from the range bounds").

## Statistics (T8.4)

- Bootstrap CIs resample CANOPIES (the per-canopy `mean_coverage_frac` values), never
  individual views/poses pooled across canopies -- see `statistics.py`'s docstring for
  why this distinction is real and easy to get backwards.
- Paired Wilcoxon signed-rank test on `(reachable_union, fixed_rig)` per canopy.
- Cliff's delta as the paired effect size.
- Holm-Bonferroni correction across every p-value produced in this phase (T8.2 cell
  comparisons + T8.3's apple-vs-fruitingwall interpenetration comparison + T8.5's
  degenerate-baseline check), applied once at the end over the full set, not per-family.

## Factorial design (T8.2)

4 factors, 2 levels each (LAI keep-fraction {0.3 sparse, 1.0 dense}; fruit-density
keep-fraction {0.3 low, 1.0 high}; clustering {clustered, dispersed} -- only affects
which fruit survive when fruit-density < 1.0; trellis {apple, apple_fruitingwall}) =
16-cell full factorial. This run executes a resolution-IV half-fraction (8 cells,
generator D = LAI x fruit_density x clustering, see `factorial_design.py`) as the
screening design the task doc calls for, NOT the full 16-cell grid -- logged as a scale
reduction, not hidden.
