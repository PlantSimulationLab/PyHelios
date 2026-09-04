"""
T7.5 (D4) -- thin-structure recall by diameter class.

Task doc: "reusing Phase 4's real diameter-class methodology
(phase4/voxel_sweep.py) against this phase's own data. Benchmark to beat:
<55% recall below 10mm."

## Two recall numbers, both real, answering different questions

1. **Theoretical geometric detectability** -- Phase 4's OWN criterion,
   imported and reused verbatim (`DIAMETER_CLASSES`, `classify_diameter`,
   and the one-voxel/two-voxel Nyquist-like standard: a diameter-D
   structure is detectable at voxel size v if D>=v, robustly resolved if
   D>=2v). This is a best-case upper bound: it ignores occlusion, view
   coverage, and reconstruction noise entirely -- it only asks "could this
   structure register at all given its size vs. the voxel grid."
2. **Empirical reconstruction recall (new to Phase 7)** -- for each real
   branch/peduncle/shoot segment, sample points along its real length and
   check whether T7.6's ACTUAL fused reconstruction (real depth, real
   exact poses, real occlusion/coverage limits and all) produced an
   occupied voxel near it. This is the real "did the classical baseline
   actually recover this thin structure" number T7.5 is asking for --
   Phase 4's criterion alone cannot answer it, since Phase 4's sweep never
   checks against an actual reconstruction.

Both are reported side by side, at both of T7.6's voxel resolutions
(2cm -- Phase 4 notes "every published mapping benchmark you will read was
measured at 5cm", so 2cm is already finer than that literature baseline --
and 5mm).
"""

import json
import os
import sys

import numpy as np

_PHASE4_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phase4")
if _PHASE4_DIR not in sys.path:
    sys.path.insert(0, _PHASE4_DIR)

from voxel_sweep import DIAMETER_CLASSES, classify_diameter  # noqa: E402  (phase4 module, path-injected above)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
SAMPLES_PER_SEGMENT = 5


def _theoretical_recall(segments, voxel_size_m):
    """Phase 4's own criterion, unmodified: does mid_diameter_mm >= voxel
    size (one-voxel) / >= 2x voxel size (two-voxel, robust)."""
    v_mm = voxel_size_m * 1000.0
    by_class_total = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
    by_class_hit = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
    by_class_robust = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
    for seg in segments:
        cls = classify_diameter(seg["mid_diameter_mm"])
        by_class_total[cls] += 1
        if seg["mid_diameter_mm"] >= v_mm:
            by_class_hit[cls] += 1
        if seg["mid_diameter_mm"] >= 2 * v_mm:
            by_class_robust[cls] += 1
    recall = {n: (by_class_hit[n] / by_class_total[n] if by_class_total[n] else None) for n, _, _ in DIAMETER_CLASSES}
    recall_robust = {n: (by_class_robust[n] / by_class_total[n] if by_class_total[n] else None)
                      for n, _, _ in DIAMETER_CLASSES}
    return recall, recall_robust, by_class_total


def _empirical_recall(segments, occupied, bmin, voxel_size_m, samples_per_segment=SAMPLES_PER_SEGMENT,
                       tol_voxels=1):
    """Real recall against T7.6's actual fused reconstruction: sample
    points along each segment's real length, check for an occupied voxel
    within `tol_voxels` (index-space neighborhood window; fast, avoids an
    O(segments x occupied_voxels) distance matrix).

    `tol_voxels=1` (a fixed ~1-voxel allowance for pose/discretization
    slop, not a physically-scaled radius+voxel_size tolerance): a
    physically-scaled tolerance balloons at coarse resolution (e.g. at
    2cm voxels, radius+voxel_size for a 2mm twig is already ~1cm = a
    5x5x5-voxel, 10cm-wide search cube), which stops measuring "was THIS
    thin structure specifically resolved" and starts measuring "is there
    reconstructed matter somewhere in this neighborhood" (trivially true
    near a trunk/larger branch) -- exactly the false-positive Phase 4's
    own theoretical criterion is designed to avoid by being strict about
    voxel-vs-diameter. A fixed small window keeps this empirical check
    answering the same question the theoretical one asks, just against a
    real reconstruction instead of an idealized geometric bound.
    """
    dims = np.array(occupied.shape)
    by_class_total = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
    by_class_hit = {name: 0 for name, _lo, _hi in DIAMETER_CLASSES}
    for seg in segments:
        cls = classify_diameter(seg["mid_diameter_mm"])
        by_class_total[cls] += 1
        p0 = np.array(seg["p0"])
        p1 = np.array(seg["p1"])
        tol_vox = tol_voxels
        ts = np.linspace(0.0, 1.0, samples_per_segment)
        pts = p0[None, :] + ts[:, None] * (p1 - p0)[None, :]
        idx = np.floor((pts - bmin) / voxel_size_m).astype(np.int64)
        hit = False
        for center_idx in idx:
            lo = np.clip(center_idx - tol_vox, 0, dims - 1)
            hi = np.clip(center_idx + tol_vox + 1, 0, dims)
            if np.any(lo >= hi):
                continue
            window = occupied[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
            if window.size and np.any(window):
                hit = True
                break
        if hit:
            by_class_hit[cls] += 1
    recall = {n: (by_class_hit[n] / by_class_total[n] if by_class_total[n] else None) for n, _, _ in DIAMETER_CLASSES}
    return recall, by_class_total, by_class_hit


def run():
    with open(os.path.join(OUTPUT_DIR, "t76_branch_segments.json")) as f:
        segments = json.load(f)

    results = {}
    for res_name, npz_name in [("coarse_2cm", "t76_grid_coarse.npz"), ("fine_5mm", "t76_grid_fine.npz")]:
        data = np.load(os.path.join(OUTPUT_DIR, npz_name))
        occupied, bmin, voxel_size_m = data["occupied"], data["bmin"], float(data["voxel_size"])

        theo_recall, theo_recall_robust, by_class_total = _theoretical_recall(segments, voxel_size_m)
        emp_recall, _by_class_total2, by_class_hit = _empirical_recall(segments, occupied, bmin, voxel_size_m)

        results[res_name] = {
            "voxel_size_m": voxel_size_m,
            "n_by_class": by_class_total,
            "theoretical_geometric_recall_one_voxel": theo_recall,
            "theoretical_geometric_recall_two_voxel_robust": theo_recall_robust,
            "empirical_reconstruction_recall": emp_recall,
            "empirical_n_hit_by_class": by_class_hit,
        }

    below_10mm_classes = ["<5mm", "5-10mm"]
    below_10mm_total = sum(results["fine_5mm"]["n_by_class"][c] for c in below_10mm_classes)
    below_10mm_hit = sum(results["fine_5mm"]["empirical_n_hit_by_class"][c] for c in below_10mm_classes)
    empirical_recall_below_10mm = below_10mm_hit / below_10mm_total if below_10mm_total else None

    report = {
        "n_segments_total": len(segments),
        "samples_per_segment": SAMPLES_PER_SEGMENT,
        "by_resolution": results,
        "benchmark": {
            "target": "recall < 55% below 10mm (a benchmark to BEAT, i.e. this baseline should exceed it)",
            "empirical_recall_below_10mm_fine_5mm_grid": empirical_recall_below_10mm,
            "n_segments_below_10mm": below_10mm_total,
            "beats_55pct_benchmark": (
                bool(empirical_recall_below_10mm > 0.55) if empirical_recall_below_10mm is not None else None
            ),
        },
    }
    return report


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = run()
    out_path = os.path.join(OUTPUT_DIR, "t75_thin_structure_recall.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=float)
    for res_name, r in report["by_resolution"].items():
        print(f"--- {res_name} (voxel={r['voxel_size_m']}m) ---")
        print("  n_by_class:", r["n_by_class"])
        print("  theoretical (1-voxel):", r["theoretical_geometric_recall_one_voxel"])
        print("  empirical (real reconstruction):", r["empirical_reconstruction_recall"])
    print(json.dumps(report["benchmark"], indent=2))
    print("wrote", out_path)
    return report


if __name__ == "__main__":
    main()
