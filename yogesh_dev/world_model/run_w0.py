"""
W0 -- measure the orchard factory. Everything here writes a JSON to
`yogesh_dev/world_model/output/w0/` so every number in the reports is
re-derivable by re-running this file.

Measurements (all real, none estimated):
  M1  determinism      -- same seed twice => identical primitive/fruit counts;
                          a different seed => different counts.
  M2  build cost       -- wall-clock build time + primitive count for the full
                          2x10 orchard at several ages.
  M3  advanceTime cost -- the plan flags this as UNMEASURED at 20-tree scale.
                          Measured here for a few dt values.
  M4  age -> fruit     -- the gate on the growth schedule (gotcha 7: age 540 d
                          produces zero fruit). Measured on a SINGLE tree over a
                          dense age grid (cheap) and confirmed at full 2x10 scale
                          at a few ages.

Run (helios env -- see W0 findings for why not `base`):
    cd /home/yogesh/PyHelios && \
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.world_model.run_w0
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
from yogesh_dev.world_model.orchard import (
    build_orchard, verify_seed_split, orchard_extent, ORGAN_OPTICS,
    TREES_PER_ROW, ROWS, IN_ROW_SPACING, ROW_SPACING,
)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w0")


def _log(msg, lines):
    print(msg, flush=True)
    lines.append(msg)


def _organ_counts(context, uuids):
    out = {}
    for organ in ("leaf", "shoot", "petiole", "peduncle", "fruit"):
        out[organ] = len(context.filterPrimitivesByData(uuids, "object_label", organ))
    return out


# ---------------------------------------------------------------------------
# M4a: single-tree age -> fruit curve (cheap; dense age grid)
# ---------------------------------------------------------------------------
def single_tree_age_curve(ages, tree_type="apple", seed=10000, lines=None):
    rows = []
    for age in ages:
        with Context() as context:
            context.seedRandomGenerator(seed)
            with PlantArchitecture(context) as pa:
                enable_fruit_object_data(pa)
                t0 = time.time()
                pa.loadPlantModelFromLibrary(tree_type)
                pid = pa.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=float(age))
                dt = time.time() - t0
                uuids = pa.getAllPlantUUIDs(pid)
                counts = _organ_counts(context, uuids)
                fruit_uuids = context.filterPrimitivesByData(uuids, "object_label", "fruit")
                n_fruit_obj = len(context.getUniquePrimitiveParentObjectIDs(
                    fruit_uuids, include_zero=False)) if fruit_uuids else 0
                try:
                    height = pa.getPlantHeight(pid)
                    leaf_area = pa.getPlantLeafArea(pid)
                except Exception:
                    height, leaf_area = None, None
        rec = {"age_days": float(age), "build_s": dt, "n_primitives": len(uuids),
               "n_fruit_objects": n_fruit_obj, "height_m": height,
               "leaf_area_m2": leaf_area, **{f"n_{k}_prims": v for k, v in counts.items()}}
        rows.append(rec)
        _log(f"  [1-tree] age={age:6.0f}d  prims={len(uuids):7d}  fruit_objs={n_fruit_obj:4d}  "
             f"build={dt:6.2f}s  h={height if height is None else round(height,2)}m", lines)
    return rows


# ---------------------------------------------------------------------------
# M2/M4b: full 2x10 orchard at several ages
# ---------------------------------------------------------------------------
def orchard_age_sweep(ages, tree_type="apple", seed=10000, lines=None):
    rows = []
    for age in ages:
        orch = build_orchard(seed=seed, age_days=age, tree_type=tree_type)
        try:
            lo, hi = orch.bounds()
            counts = _organ_counts(orch.context, orch.all_uuids())
            rec = {
                "age_days": float(age), "seed": seed, "tree_type": tree_type,
                "build_s": orch.build_time_s, "n_primitives": orch.n_primitives(),
                "n_fruit_objects": len(orch.fruit_records),
                "bounds_min": lo.tolist(), "bounds_max": hi.tolist(),
                **{f"n_{k}_prims": v for k, v in counts.items()},
            }
            rows.append(rec)
            _log(f"  [2x10]  age={age:6.0f}d  prims={orch.n_primitives():8d}  "
                 f"fruit_objs={len(orch.fruit_records):5d}  build={orch.build_time_s:7.2f}s  "
                 f"bbox_x=[{lo[0]:.2f},{hi[0]:.2f}] y=[{lo[1]:.2f},{hi[1]:.2f}] z=[{lo[2]:.2f},{hi[2]:.2f}]", lines)
        finally:
            orch.close()
    return rows


# ---------------------------------------------------------------------------
# M1: determinism
# ---------------------------------------------------------------------------
def determinism_check(age_days, tree_type="apple", seed_a=10000, seed_b=10001, lines=None):
    def build_and_measure(s):
        orch = build_orchard(seed=s, age_days=age_days, tree_type=tree_type)
        try:
            return {"seed": s, "n_primitives": orch.n_primitives(),
                    "n_fruit_objects": len(orch.fruit_records),
                    "organ_counts": _organ_counts(orch.context, orch.all_uuids()),
                    "build_s": orch.build_time_s}
        finally:
            orch.close()

    a1 = build_and_measure(seed_a)
    a2 = build_and_measure(seed_a)
    b1 = build_and_measure(seed_b)
    same = (a1["n_primitives"] == a2["n_primitives"]
            and a1["n_fruit_objects"] == a2["n_fruit_objects"]
            and a1["organ_counts"] == a2["organ_counts"])
    differ = (a1["n_primitives"] != b1["n_primitives"]
              or a1["n_fruit_objects"] != b1["n_fruit_objects"])
    _log(f"  seed {seed_a} build#1: prims={a1['n_primitives']} fruit={a1['n_fruit_objects']}", lines)
    _log(f"  seed {seed_a} build#2: prims={a2['n_primitives']} fruit={a2['n_fruit_objects']}", lines)
    _log(f"  seed {seed_b} build  : prims={b1['n_primitives']} fruit={b1['n_fruit_objects']}", lines)
    _log(f"  same-seed identical: {same}   different-seed differs: {differ}", lines)
    return {"same_seed_identical": same, "different_seed_differs": differ,
            "builds": [a1, a2, b1], "acceptance_passed": bool(same and differ)}


# ---------------------------------------------------------------------------
# M3: advanceTime cost at 20-tree scale
# ---------------------------------------------------------------------------
def advance_time_cost(start_age, dts, tree_type="apple", seed=10000, lines=None):
    """Build ONE orchard at start_age, then advanceTime repeatedly, timing each
    call and recording primitive count + fruit count after each step."""
    orch = build_orchard(seed=seed, age_days=start_age, tree_type=tree_type)
    steps = [{"cumulative_age_days": float(start_age), "dt": 0.0,
              "seconds": orch.build_time_s, "n_primitives": orch.n_primitives(),
              "n_fruit_prims": len(orch.context.filterPrimitivesByData(
                  orch.all_uuids(), "object_label", "fruit")),
              "note": "initial build"}]
    _log(f"  built at age={start_age}d: prims={orch.n_primitives()} in {orch.build_time_s:.2f}s", lines)
    try:
        for dt in dts:
            elapsed = orch.grow(dt)
            n_fruit_prims = len(orch.context.filterPrimitivesByData(
                orch.all_uuids(), "object_label", "fruit"))
            steps.append({"cumulative_age_days": orch.age_days, "dt": float(dt),
                          "seconds": elapsed, "n_primitives": orch.n_primitives(),
                          "n_fruit_prims": n_fruit_prims})
            _log(f"  advanceTime(dt={dt:5.1f}) -> age={orch.age_days:6.1f}d  "
                 f"{elapsed:8.2f}s  prims={orch.n_primitives():8d}  fruit_prims={n_fruit_prims}", lines)
    except Exception as e:
        _log(f"  advanceTime FAILED after {len(steps)-1} steps: {type(e).__name__}: {e}", lines)
        steps.append({"error": f"{type(e).__name__}: {e}"})
    finally:
        orch.close()
    return steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="reduced age grids, for smoke-testing the script itself")
    ap.add_argument("--skip-advance", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    lines = []
    results = {"script": "run_w0.py", "quick": args.quick,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    _log("=" * 78, lines)
    _log("W0 -- orchard factory measurement", lines)
    _log("=" * 78, lines)

    _log("\n[layout] fixed geometry", lines)
    ext = orchard_extent()
    results["layout"] = {"rows": ROWS, "trees_per_row": TREES_PER_ROW,
                         "in_row_spacing_m": IN_ROW_SPACING, "row_spacing_m": ROW_SPACING,
                         "extent": ext}
    _log(f"  {ROWS} rows x {TREES_PER_ROW} trees, in-row {IN_ROW_SPACING} m, row {ROW_SPACING} m", lines)
    _log(f"  tree-base grid: x in [{ext['x_min']}, {ext['x_max']}], y in {ext['row_y']}", lines)

    _log("\n[seeds] train/val/test seed-stream disjointness", lines)
    results["seed_split"] = verify_seed_split()
    _log(f"  {results['seed_split']}", lines)

    ages_single = [400, 500, 540, 600, 650, 700, 720, 800, 900] if not args.quick else [540, 720]
    _log("\n[M4a] single-tree age -> fruit curve", lines)
    results["single_tree_age_curve"] = single_tree_age_curve(ages_single, lines=lines)

    ages_orchard = [540, 720] if args.quick else [540, 650, 720, 800]
    _log("\n[M2/M4b] full 2x10 orchard age sweep", lines)
    results["orchard_age_sweep"] = orchard_age_sweep(ages_orchard, lines=lines)

    _log("\n[M1] determinism (2x10 orchard, age 720 d)", lines)
    results["determinism"] = determinism_check(720.0, lines=lines)

    if not args.skip_advance:
        _log("\n[M3] advanceTime cost at 20-tree scale (start 650 d)", lines)
        dts = [10.0, 10.0] if args.quick else [10.0, 10.0, 20.0, 20.0, 40.0]
        results["advance_time"] = advance_time_cost(650.0, dts, lines=lines)

    results["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(OUT_DIR, "w0_measurements.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(OUT_DIR, "w0_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    _log(f"\nWrote {OUT_DIR}/w0_measurements.json", lines)
    return results


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            sys.path.insert(0, "/home/yogesh/PyHelios")
            from notify_slack import notify_slack
            notify_slack(f"World model W0 FAILED: {traceback.format_exc()[-1200:]}")
        except Exception:
            pass
        raise
