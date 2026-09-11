"""
W0b -- fine-grained age sweep, written because the coarse W0 sweep produced a
surprise that gates the whole growth channel.

W0's single-tree curve found the apple model's organ counts are *piecewise
constant* in age, not smoothly increasing:

    age 400 d  ->  4,886 prims,  0 fruit
    age 500 d  ->  4,886 prims,  0 fruit     (identical to 400 d)
    age 540 d  -> 34,001 prims,  0 fruit
    age 600 d  -> 34,024 prims, 20 fruit
    age 720 d  -> 34,024 prims, 20 fruit     (identical to 600 d)
    age 800 d  -> 16,058 prims,  0 fruit     (leaf drop / dormancy, fruit gone)
    age 900 d  -> 85,340 prims,  0 fruit

If organ counts are the only thing that changes, then "advance 20 days" is a
no-op inside the fruiting window and the growth action channel is degenerate.
This script checks whether *continuous* quantities (leaf area, total fruit
surface area, mean fruit diameter, plant height) still vary with age even where
counts are frozen -- i.e. whether there is any signal for the growth channel to
predict at all.

Every quantity here is measured from real geometry (`context.getPrimitiveArea`
summed over the real primitives), not from `calculateSyntheticLeafArea`, which
Phase 8 found unreliable in this environment.

Run:
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.world_model.run_w0b
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from pyhelios import Context, PlantArchitecture
from pyhelios.types import vec3

from yogesh_dev.phase1.ground_truth import enable_fruit_object_data

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w0")


def _organ_area(context, uuids, label):
    matched = context.filterPrimitivesByData(uuids, "object_label", label)
    if not matched:
        return 0.0, 0
    return float(sum(context.getPrimitiveArea(u) for u in matched)), len(matched)


def measure_single_tree(age, seed=10000, tree_type="apple"):
    with Context() as context:
        context.seedRandomGenerator(seed)
        with PlantArchitecture(context) as pa:
            enable_fruit_object_data(pa)
            t0 = time.time()
            pa.loadPlantModelFromLibrary(tree_type)
            pid = pa.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=float(age))
            build_s = time.time() - t0
            uuids = pa.getAllPlantUUIDs(pid)
            leaf_area, n_leaf_prims = _organ_area(context, uuids, "leaf")
            fruit_area, n_fruit_prims = _organ_area(context, uuids, "fruit")
            shoot_area, n_shoot_prims = _organ_area(context, uuids, "shoot")
            fruit_uuids = context.filterPrimitivesByData(uuids, "object_label", "fruit")
            fruit_objs = (list(context.getUniquePrimitiveParentObjectIDs(fruit_uuids, include_zero=False))
                          if fruit_uuids else [])
            # per-fruit equivalent diameter from real per-object surface area
            diams = []
            for oid in fruit_objs:
                a = sum(context.getPrimitiveArea(u) for u in context.getObjectPrimitiveUUIDs(oid))
                if a > 0:
                    diams.append(float(np.sqrt(a / np.pi)))
            height = pa.getPlantHeight(pid)
    return {
        "age_days": float(age), "build_s": build_s, "n_primitives": len(uuids),
        "n_fruit_objects": len(fruit_objs), "n_leaf_prims": n_leaf_prims,
        "n_shoot_prims": n_shoot_prims, "n_fruit_prims": n_fruit_prims,
        "leaf_area_m2": leaf_area, "fruit_area_m2": fruit_area, "shoot_area_m2": shoot_area,
        "mean_fruit_diameter_m": float(np.mean(diams)) if diams else 0.0,
        "max_fruit_diameter_m": float(np.max(diams)) if diams else 0.0,
        "height_m": float(height),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=float, default=520.0)
    ap.add_argument("--hi", type=float, default=800.0)
    ap.add_argument("--step", type=float, default=10.0)
    ap.add_argument("--seed", type=int, default=10000)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    ages = np.arange(args.lo, args.hi + 1e-6, args.step)
    rows, lines = [], []
    hdr = (f"{'age':>6} {'prims':>7} {'fruit':>6} {'leafA(m2)':>10} {'fruitA(m2)':>11} "
           f"{'meanD(mm)':>10} {'h(m)':>6} {'build(s)':>9}")
    print(hdr, flush=True); lines.append(hdr)
    for age in ages:
        r = measure_single_tree(float(age), seed=args.seed)
        rows.append(r)
        line = (f"{r['age_days']:6.0f} {r['n_primitives']:7d} {r['n_fruit_objects']:6d} "
                f"{r['leaf_area_m2']:10.4f} {r['fruit_area_m2']:11.5f} "
                f"{r['mean_fruit_diameter_m']*1000:10.2f} {r['height_m']:6.2f} {r['build_s']:9.2f}")
        print(line, flush=True); lines.append(line)

    # Where does anything actually change?
    def frac_unique(key):
        vals = [round(r[key], 9) for r in rows]
        return len(set(vals)) / len(vals)

    summary = {
        "seed": args.seed, "ages": ages.tolist(),
        "distinct_value_fraction": {k: frac_unique(k) for k in
                                     ("n_primitives", "n_fruit_objects", "leaf_area_m2",
                                      "fruit_area_m2", "mean_fruit_diameter_m", "height_m")},
        "fruiting_ages": [r["age_days"] for r in rows if r["n_fruit_objects"] > 0],
        "rows": rows,
    }
    print("\ndistinct-value fraction over the age grid (1.0 = every age differs, "
          "1/N = constant):", flush=True)
    for k, v in summary["distinct_value_fraction"].items():
        line = f"  {k:24s} {v:.3f}"
        print(line, flush=True); lines.append(line)
    fa = summary["fruiting_ages"]
    line = (f"\nfruit present at ages: {fa[0]:.0f}-{fa[-1]:.0f} d ({len(fa)} of {len(rows)} sampled)"
            if fa else "\nNO fruit at any sampled age")
    print(line, flush=True); lines.append(line)

    with open(os.path.join(OUT_DIR, "w0b_age_curve.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT_DIR, "w0b_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {OUT_DIR}/w0b_age_curve.json")
    return summary


if __name__ == "__main__":
    main()
