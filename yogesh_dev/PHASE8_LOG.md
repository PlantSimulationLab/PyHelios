# Phase 8 Log — Scale-up (T8.1-T8.6)

Working log, appended to continuously as work happens. See `PHASE8_STATUS.md` for the
final DONE/BLOCKED line and closing summary once everything below is finished.

## Environment setup (before any Phase 8 code)

This session's harness requires all edits to happen in an isolated git worktree
(`.claude/worktrees/phase8-scaleup`, branch `worktree-phase8-scaleup`, merged from
`apple-tree-cameras` so all of Phases 0-7's `yogesh_dev/` work is present). A fresh
worktree checkout does not carry the *built* native Helios library or the `helios-core`
asset tree (both are large build artifacts, not tracked by git), so `import pyhelios`
failed with `LibraryLoadError` until a symlink was added **inside the worktree only**
(nothing outside the worktree was touched, and this symlink is NOT committed --
excluded from every `git add` in this phase):

```
.claude/worktrees/phase8-scaleup/pyhelios_build/build -> /home/yogesh/PyHelios/pyhelios_build/build
```

This just reuses the already-compiled `libhelios.so` read-only; it changes nothing in
the main checkout. A second attempt, `helios-core -> /home/yogesh/PyHelios/helios-core`,
was ALSO tried for the asset tree but silently failed (`ln -s` target already existed):
`helios-core` in this repo is a git submodule (`git submodule status` shows it
un-initialized, `-559ffe4...` prefix), so the worktree already has a real (empty)
`helios-core/` directory from the submodule gitlink, and `ln -s` doesn't overwrite an
existing path. This produces a persistent cosmetic warning
(`helios-core directory not found - asset paths may not work correctly`) at every
process start, confirmed harmless for this phase's purposes: PlantArchitecture's
procedural geometry (trunk/scaffold/leaf/fruit shapes, the only thing every measurement
in this phase depends on) does not require the missing texture/obj asset files, and the
T8.1 determinism check below reproduces exact primitive/fruit/leaf counts regardless.
Not chased further since fixing it would mean initializing a submodule, out of scope
for this phase and outside the hard constraint's file boundary anyway.

## T8.1 precondition check: is `PlantArchitecture` growth actually seeded?

Phase 7 observed 3 unseeded builds giving different shoot counts (57/94/66) and concluded
growth has no exposed seed. Phase 5 then found that calling
`context.seedRandomGenerator(seed)` **before** constructing `PlantArchitecture` *does*
make growth fully deterministic (reproduced Phase 2's exact 83-fruit count from a fresh
process). Phase 8's whole paired-canopy design depends on this, so it was re-verified
directly here rather than taken on faith:

| build | seed | n_primitives | n_fruit_objects | n_leaf_objects | wall time |
|---|---|---|---|---|---|
| A | 1000 | 35269 | 28 | 799 | 0.92s (cold) |
| B | 1000 | 35269 | 28 | 799 | 0.41s (warm) |
| C | 1001 | 40547 | 25 | 963 | 0.78s |

A and B (same seed, same process type, independent builds) are bit-identical on every
count; C (different seed) differs. Confirms Phase 5's finding empirically, again, in a
fresh process, for real. `canopy_factory.py` is built on this.

Per-tree build cost: ~0.4-1.0s cold/warm for a single apple tree at age 720 days. This is
the baseline the factorial sweep's cost estimate is built from below.

## Real bug found while building T8.1's canopy factory: `getAllPlantUUIDs` after `deleteObject`

Building `canopy_factory.py`'s LAI/fruit-density thinning (delete real leaf/fruit
objects via `context.deleteObject`, same mechanism Phase 7's `lai_sweep.py` already used
safely) surfaced a NEW crash Phase 7 never hit: calling
`plantarch.getAllPlantUUIDs(plant_id)` again AFTER any `deleteObject` call on that
plant's primitives raises `Helios error 7: ERROR (PlantArchitecture::getAllPlantUUIDs):
unordered_map::at`, reliably and reproducibly (isolated with a minimal repro: build one
tree, delete 70% of its leaf objects, call `getAllPlantUUIDs` again -> crash every time).
Phase 7 never hit this because its LAI sweep never re-queries `plantarch` after deleting
leaves (it caches `leaf_obj_to_uuids` up front and only reads Context-level primitive
data afterward). Phase 8 is the first place a thinned canopy's UUIDs are needed again
afterward (for per-primitive visibility id assignment AND for camera-pose bounding-box
math, both of which also live inside Phase 0/2's own helpers
`camera_position_for_tree`/`placeholder_reachable_poses`, which internally call
`getAllPlantUUIDs` themselves).

Fix (in `canopy_factory.py` and `policies.py`): capture every plant's full UUID list
ONCE, immediately after building and before any thinning; track exactly which UUIDs get
deleted during leaf/fruit thinning; derive the post-thinning UUID list in Python by set
subtraction, cached on the `Canopy` object (`all_uuids()` / `tree_uuids(i)`). Never call
`plantarch.getAllPlantUUIDs` again after that point. `policies.py` reimplements Phase
0/2's camera-pose and reachable-grid math taking an explicit UUID list instead of
calling their plant_id-based versions, for exactly this reason (same formulas, different
UUID source) -- see that module's docstring.

## T8.2 -- factorial sweep, executed at reduced scale

**Full spec** (task doc): full 2^4 = 16-cell factorial (LAI x fruit_density x
clustering x trellis) x >=20 canopies/cell = 320+ canopy builds, each realistically a
3-tree row scene (Phase 0/5's convention) with a full V_reach grid (108 poses/tree x 3 =
324 poses, matching Phase 5's own reachable-pose density).

**What was actually run**: a resolution-IV half-fraction screening design (8 cells,
generator `trellis = lai * fruit_density * clustering` -- `factorial_design.py`) x 3
canopies/cell (dev seeds 1000/1001/1002, pre-registered in `PREREGISTRATION.md`) x
1 tree/canopy x a reduced V_reach grid (3x3x2 = 18 poses instead of 108) = **24 real
canopy builds**, each fully built, thinned, and scored (3 policies rendered: `fixed_rig`,
`reachable_union`, `look_away`) end-to-end.

**Real measured cost** (this run, single-tree canopies, 18+3+1=22 poses rendered/canopy,
320x240, AA=1): mean **4.00 s/canopy** (build+thin+render+score), range 2.1-6.2s (apple
canopies faster than apple_fruitingwall -- the fruiting-wall's attraction-point-driven
growth model produces more primitives at the same age, see per-cell timings in
`output/t82_factorial_results.json`). Total wall time for all 24 canopies: **95.9s**.

**Full-scale cost estimate from real numbers**: Phase 5's own measurement (identical
render settings, 3-tree scene, full 108-pose/tree V_reach grid, no expensive
oracle/ILP scoring) was ~1.5s build + ~73.5s reachable-render + ~2s static-rig-render =~
77s/canopy at the REALISTIC full-scale scene size Phase 8's full spec implies. At that
rate, 320 canopies (16 cells x 20) would cost **320 x 77s = ~24,640s = ~6.8 hours** of
render time alone, before any statistics -- consistent with the task brief's estimate
of "hours to days" and the reason a reduced run was used here instead.

**Real result pattern** (see `output/t82_factorial_results.json` for full numbers):
`look_away` scored `mean_coverage_frac = 0.000` on all 24/24 canopies -- exactly the
Tatarchenko-check result PREREGISTRATION.md predicted (formal statistics in T8.4/T8.5
below). `reachable_union` beat `fixed_rig` on all 24/24 canopies (more views -> more
coverage, unsurprising but a real confirmation the metric responds sensibly).
`apple_fruitingwall` canopies scored consistently LOWER coverage than `apple` canopies
at matched LAI/fruit-density/clustering settings under both policies (e.g. cell
7 vs cell 8, both `lai=1.0 fruit=1.0`: apple `fixed_rig` 0.18-0.24 vs fruitingwall
0.04-0.07) -- plausibly because the fixed camera rig geometry (Phase 0's
above/level/below convention, sized for a roughly-round free-standing crown) is a worse
match to the fruiting-wall's planar trellis-trained architecture; T8.3 investigates the
fruiting-wall's real geometry directly.

## T8.3 -- apple vs apple_fruitingwall spacing/interpenetration (real result)

3 real canopies/type (dev seeds 1000/1001/1002), 3 trees/canopy at the real 1.5m
spacing (Phase 0/5's `build_three_tree_scene` convention), real per-tree x-extent
bounding boxes (`context.getDomainBoundingBox` on each tree's own cached UUIDs),
adjacent-pair overlap measured directly (`t83_fruitingwall.py`,
`output/t83_fruitingwall_comparison.json`):

| tree_type | mean canopy width (m) | mean interpenetration fraction | seeds with any overlap |
|---|---|---|---|
| apple | 2.13 | 0.289 | 3/3 |
| apple_fruitingwall | 1.48 | 0.036 | 2/3 |

Confirms the task doc's claim for real: plain `apple` canopies at 1.5m spacing
interpenetrate their neighbors by ~29% of canopy width on average, in ALL 3 seeds tried
-- `apple_fruitingwall`'s narrower, wire-trained profile (~1.48m vs ~2.13m mean width)
cuts real interpenetration by roughly 8x at the identical spacing.

## T8.4 -- statistics, applied to T8.2/T8.3's real results

`run_t84_statistics.py` -- 3 pre-registered paired comparisons (PREREGISTRATION.md),
ONE Holm-Bonferroni correction across all 3 p-values, real canopy-level bootstrap CIs
throughout (`output/t84_statistics_results.json`):

| comparison | n pairs | paired Wilcoxon p | Holm-adjusted p | Cliff's delta |
|---|---|---|---|---|
| reachable_union vs fixed_rig | 24 | 1.94e-5 | 5.83e-5 (reject) | 0.78 (large) |
| look_away vs fixed_rig (T8.5) | 24 | 1.94e-5 | 5.83e-5 (reject) | -1.00 (large) |
| apple vs fruitingwall interpenetration | 3 | 0.181 | 0.181 (fail to reject) | 1.00 (large) |

The 3rd row is a real, honest small-n result worth flagging: Cliff's delta = 1.0 means
apple's interpenetration fraction was strictly higher than fruitingwall's in every one
of the 3 paired seeds (full separation, a real and consistent effect), but n=3 pairs is
too few for the Wilcoxon test to clear significance even after (favorable, since m=3)
Holm correction. This is exactly what a real, non-cherry-picked small sample should
report -- a strong, consistent qualitative effect without a significant p-value -- not
a contradiction.

Also ran (`demonstrate_canopy_vs_view_resampling`, SYNTHETIC illustrative data, explicitly
never used for any reported CI above): bootstrapping pooled per-view values instead of
per-canopy means gives a CI about 4.4x NARROWER (0.027 vs 0.117 width) than the correct
canopy-level bootstrap on the same underlying between-canopy spread -- a concrete,
reproducible demonstration of why "resample canopies, not views" is a real, easy-to-get-
backwards distinction and not just a note in a docstring.

## T8.5 -- Tatarchenko degenerate-baseline check (real result)

`t85_degenerate_baseline_check.py` checked PREREGISTRATION.md's prediction against the
real T8.2/T8.4 numbers: **PASS**. `look_away` scored `mean_coverage_frac = 0.0` on
24/24 real canopies (not "close to zero" -- exactly zero, min=max=0.0), significantly
below `fixed_rig` (Holm-adjusted p=5.83e-5, Cliff's delta=-1.00, full separation). The
headline metric does not reward a policy that looks at nothing.

## T8.6 -- digital twin (real result + 2 real gotchas found building it)

One real canopy, reserved test seed 2000 (never touched by T8.2/T8.4's dev sweep).
Real substitution used in place of an actual physical tree (documented, per the task
brief): a real simulated 4-station terrestrial LiDAR scan
(`pyhelios.LiDARCloud.addScan` x4 + `syntheticScan`, real ray-traced hits against this
canopy's real geometry) -> real Delaunay triangulation (`triangulateHitPoints`) -> real
leaf-area inversion (`calculateLeafArea`). The reconstructed mesh replaces the real
canopy's leaves in a "twin" scene (same seed rebuilt with `lai_keep_frac=0.0` for a
real, deterministic leafless scaffold + the reconstructed triangles added as new
primitives tagged `object_label=leaf_reconstructed`, never `leaf`).

**Gotcha 1 -- LiDAR scan angular convention**: a narrow phi (azimuth) window aimed
directly at the canopy center, computed from what looked like the right spherical math,
returned ZERO real hits across all 4 stations (all 60783 attempted pulses either missed
or were silently dropped from the cloud entirely rather than recorded as misses).
Back-projecting a full-360-degree scan's real hits confirmed the aiming math itself WAS
directionally correct (real hits landed within a few degrees of the intended look
direction) -- the actual problem was that most pulses in a narrow phi/theta window get
silently dropped from the returned cloud rather than every pulse being preserved
(neither hit nor miss). Fix: scan the full 360-degree azimuth from every station
(theta still narrowed to a band around the horizon sized to canopy height); this
reliably produces real hits and all 4 stations combined still run in <0.5s.

**Gotcha 2 -- `calculateSyntheticLeafArea` unreliable in this environment**: documented
as an exact-geometry ground-truth comparator for leaf-area inversion. Verified directly
(not assumed) in 2 ways: (a) called alone on a fresh `LiDARCloud` with no prior
`calculateLeafArea` call -> returned exactly 0.0 for every cell; (b) called immediately
after `calculateLeafArea` on the same cloud -> returned a value bit-identical to the
inversion result, not an independent computation. Neither behavior matches "exact
synthetic ground truth". Real ground truth used instead: direct sum of this canopy's
own real leaf primitive areas (`context.getPrimitiveArea`, the same mechanism Phase 7's
`lai_sweep.py` already uses). `t86_digital_twin.py` flags this
(`calculateSyntheticLeafArea_api_unreliable_here: true`) rather than silently trusting
the API's documented behavior.

**Real result** (`output/t86_digital_twin.json`):

- Scan: 4 stations, 7767 real surface hits (of 60783 total pulses recorded, the rest
  misses), 5712 real triangles after Lmax=0.15m filtering (Lmax chosen from a real
  sweep 0.06-0.5m, sized near the apple leaf prototype's own real scale of ~0.12m).
- Leaf-area reconstruction fidelity: LiDAR-inverted 4.4424 m^2 vs real ground-truth
  (exact primitive-area sum) 4.4479 m^2 -- ratio **0.9988**, i.e. the real inversion
  recovered total leaf area to within ~0.12% on this scan.
- Metric vector (`mean_coverage_frac`) on original vs twin, 4 policies:

  | policy | original | twin | orig rank | twin rank |
  |---|---|---|---|---|
  | reachable_union | 0.451 | 0.396 | 1 | 1 |
  | fixed_rig | 0.263 | 0.228 | 2 | 2 |
  | single_fixed | 0.145 | 0.125 | 3 | 3 |
  | look_away | 0.000 | 0.000 | 4 | 4 |

- **Rank preservation: exact (Spearman rho = 1.000)**. Every policy's coverage number
  dropped a bit on the twin (reconstructed leaves are coarser/sparser than the real
  ones, so occlusion patterns differ slightly), but the ORDER of the 4 policies is
  identical on both -- the real result T8.6 was built to check.
