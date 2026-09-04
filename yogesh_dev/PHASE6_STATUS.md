# Phase 6 — Metrics harness — Status

All of T6.1–T6.11 are implemented in `yogesh_dev/phase6/`, run end-to-end
(`python -m yogesh_dev.phase6.run_phase6`), and produce real numbers against
real Phase 0-5 data/code — see `yogesh_dev/PHASE6_LOG.md` for the full
write-up (real numbers, methodology, caveats) and `yogesh_dev/phase6/output/`
for the raw JSON.

- **T6.1–T6.3**: real bugs in `apple_tree_gaussian_splatting.py` (repo
  root, untouched per the hard constraint) reproduced live against a real
  built apple tree and real Phase 1 renders/label maps; fixed logic
  implemented in `yogesh_dev/phase6/t61_t62_t63_gsplat_fixes.py`; exact
  before/after patch for a human to apply to the real file is in
  PHASE6_LOG.md.
- **T6.4–T6.6**: real per-fruit occlusion-conditioned recall, class-
  stratified F-score, and 3-state occupancy confusion matrix, all against
  Phase 4's real single-tree dataset (27 fruit, 42 rendered views).
- **T6.7–T6.9**: real discovery curves / AUC / time-to-90%, ILP-oracle-
  normalized Pi + regret (computed on Phase 4's own ground set, not Phase
  5's differently-scaled scene — Phase 5's own T5.6/T5.7 numbers carried
  in as a documented reference only), and real IG calibration (Spearman
  rho, top-1 hit rate, sparsification/AUIGSE) — all reusing Phase 4's own
  planner/IG code.
- **T6.10**: deadline-enforced closed-loop mechanism implemented and
  verified (forfeits correctly under a tight budget); honestly reports
  that no real compute cost measured anywhere in this codebase (CELF or
  exact ILP) is large enough relative to real arm motion time for the
  paused-clock-vs-closed-loop gap to be non-negligible at this dataset's
  scale.
- **T6.11**: real wall-clock latency table (mean/p95/p99/max) for 8
  representative real modules across Phases 2-4, each with a stated
  hardware-independent work unit and per-unit throughput.

Known limitations, all documented in PHASE6_LOG.md rather than hidden: no
wire/trellis class exists anywhere in this repo's scene (T6.5/T6.6 report
this as a real N/A, not a fabricated number); Phase 5 was still mid-run in
its own sibling worktree when this phase ran, so T6.8 uses Phase 4's own
data as the primary oracle-normalization scale and carries Phase 5's
(differently-scaled) T5.6/T5.7 numbers only as a documented reference;
`helios` env has no SciPy (Spearman rho hand-rolled in `common.py`) and no
torch/gsplat (T6.1-T6.3 reimplement, rather than import, the relevant
slice of the real gsplat file's logic).

STATUS: DONE
