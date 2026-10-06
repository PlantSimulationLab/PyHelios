"""
Phase 7 end-to-end driver: runs T7.1-T7.7 in the dependency order they
actually require (T7.6 before T7.5/T7.7, since those consume T7.6's
persisted reconstruction/ground-truth of the SAME tree instance -- see
each module's docstring for why a rebuild would silently be a different
tree, growth being stochastic).

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python \
        -m yogesh_dev.phase7.run_phase7
"""

import json
import os
import time

from yogesh_dev.phase7 import (
    run_t71_wai_writer,
    pose_conditioning_ablation,
    baseline_angle_sweep,
    lai_sweep,
    classical_baseline,
    thin_structure_recall,
    metric_scale_integrity,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

STEPS = [
    ("T7.1_wai_writer", run_t71_wai_writer.main),
    ("T7.2_D1_pose_conditioning_ablation", pose_conditioning_ablation.main),
    ("T7.3_D2_baseline_angle_sweep", baseline_angle_sweep.main),
    ("T7.4_D3_lai_sweep", lai_sweep.main),
    ("T7.6_D5_classical_baseline", classical_baseline.main),
    ("T7.5_D4_thin_structure_recall", thin_structure_recall.main),
    ("T7.7_D6_metric_scale_integrity", metric_scale_integrity.main),
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timings = {}
    for name, fn in STEPS:
        print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
        t0 = time.time()
        fn()
        timings[name] = time.time() - t0

    summary = {"timings_s": timings, "total_s": sum(timings.values())}
    with open(os.path.join(OUTPUT_DIR, "phase7_run_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
