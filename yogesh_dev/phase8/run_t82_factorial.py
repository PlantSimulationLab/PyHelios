"""
T8.2 -- execute the resolution-IV screening design (factorial_design.phase8_screening_design,
8 cells) at REDUCED scale: 3 canopies/cell (dev seeds 1000/1001/1002), 1 tree/canopy, a
small reachable-pose grid -- see PREREGISTRATION.md for why these are the pre-registered
numbers and PHASE8_LOG.md for the real per-canopy cost this reduction is based on.

For each (cell, seed) this builds ONE real canopy at that cell's factor levels, scores
`fixed_rig` / `reachable_union` / `look_away` on it (policies.py), and records the real
per-canopy build+render time. Output feeds T8.4's statistics directly (paired by seed
within each cell) and T8.5's degenerate-baseline check (look_away across all 24 canopies).

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase8.run_t82_factorial
"""

import json
import os
import time

from yogesh_dev.phase8.canopy_factory import build_canopy
from yogesh_dev.phase8.policies import score_canopy
from yogesh_dev.phase8.factorial_design import phase8_screening_design, phase8_full_design, cell_label

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# Pre-registered in PREREGISTRATION.md.
DEV_SEEDS_USED = [1000, 1001, 1002]
N_TREES_PER_CANOPY = 1  # reduced from Phase 0/5's 3-tree row -- see PHASE8_LOG.md


def run_cell(cell, seed):
    t0 = time.time()
    canopy = build_canopy(
        seed=seed,
        tree_type=cell["trellis"],
        n_trees=N_TREES_PER_CANOPY,
        lai_keep_frac=cell["lai"],
        fruit_keep_frac=cell["fruit_density"],
        clustering=cell["clustering"],
    )
    build_s = time.time() - t0
    try:
        score = score_canopy(canopy)
    finally:
        canopy.close()
    total_s = time.time() - t0
    return {
        "cell": cell,
        "seed": seed,
        "n_fruit": len(canopy.fruit_records) if hasattr(canopy, "fruit_records") else None,
        "thinning_report": canopy.thinning_report,
        "build_s": build_s,
        "total_s": total_s,
        **score,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    screening_cells = phase8_screening_design()
    full_cells = phase8_full_design()

    report = {
        "design": "resolution-IV half-fraction (generator trellis=lai*fruit_density*clustering)",
        "n_screening_cells": len(screening_cells),
        "n_full_cells": len(full_cells),
        "full_spec_note": (
            f"Full spec would run all {len(full_cells)} cells x >=20 canopies/cell "
            f"(task doc's stated minimum) = {len(full_cells) * 20}+ canopy builds. "
            f"This run executes the {len(screening_cells)}-cell screening design x "
            f"{len(DEV_SEEDS_USED)} canopies/cell = {len(screening_cells) * len(DEV_SEEDS_USED)} "
            "canopy builds -- see PHASE8_LOG.md for the real measured per-canopy cost "
            "this reduction is based on and the resulting full-scale cost estimate."
        ),
        "dev_seeds_used": DEV_SEEDS_USED,
        "n_trees_per_canopy": N_TREES_PER_CANOPY,
        "cells": [],
    }

    t_start = time.time()
    for i, cell in enumerate(screening_cells):
        label = cell_label(cell)
        cell_results = []
        for seed in DEV_SEEDS_USED:
            t0 = time.time()
            result = run_cell(cell, seed)
            dt = time.time() - t0
            cell_results.append(result)
            fr = result["policies"]["fixed_rig"]["mean_coverage_frac"]
            ru = result["policies"]["reachable_union"]["mean_coverage_frac"]
            la = result["policies"]["look_away"]["mean_coverage_frac"]
            print(f"[cell {i+1}/{len(screening_cells)} {label} seed={seed}] "
                  f"fixed_rig={fr:.3f} reachable_union={ru:.3f} look_away={la:.3f} "
                  f"({dt:.2f}s)", flush=True)
        report["cells"].append({"label": label, "cell": cell, "results": cell_results})

    report["total_time_s"] = time.time() - t_start
    all_total_s = [r["total_s"] for c in report["cells"] for r in c["results"]]
    report["mean_per_canopy_total_s"] = sum(all_total_s) / len(all_total_s)
    report["n_canopies_built"] = len(all_total_s)

    out_path = os.path.join(OUTPUT_DIR, "t82_factorial_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nWrote {out_path}")
    print(f"Total: {report['n_canopies_built']} canopies in {report['total_time_s']:.1f}s "
          f"(mean {report['mean_per_canopy_total_s']:.2f}s/canopy)")
    return report


if __name__ == "__main__":
    main()
