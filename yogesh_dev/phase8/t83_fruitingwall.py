"""
T8.3 -- apple vs apple_fruitingwall at the SAME real inter-tree spacing (1.5 m, Phase
0/5's convention), measuring real canopy-width/interpenetration behavior for each.

Task doc's own note (helios_setup_tasks.md, T8.3): "Your current 1.5m spacing already
interpenetrates canopies [under the plain `apple` type], which is realistic for
high-density, but the fruiting-wall model is the architecture your rig is actually
designed for." This script checks that claim directly and quantifies the fruiting-wall
alternative, both from real per-tree bounding boxes (`context.getDomainBoundingBox` on
each tree's own real primitive UUIDs -- no synthetic geometry).

Metric: for each pair of adjacent trees (row of 3 -> 2 adjacent pairs), the real overlap
of their x-extent bounding intervals, reported both as an absolute width (meters) and as
a fraction of one tree's own canopy width (interpenetration_frac -- >0 means the two
trees' bounding boxes genuinely overlap in x, not just get close).

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase8.t83_fruitingwall
"""

import json
import os

from yogesh_dev.phase8.canopy_factory import build_canopy

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
SPACING_M = 1.5  # matches Phase 0/5's build_three_tree_scene convention
SEEDS = [1000, 1001, 1002]


def tree_x_extent(context, uuids):
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    return float(x_bounds.x), float(x_bounds.y)


def adjacent_overlaps(extents):
    """extents: list of (x_min, x_max) per tree, in row order. Returns list of
    {pair, overlap_m, tree_width_m, interpenetration_frac} for each adjacent pair."""
    results = []
    for i in range(len(extents) - 1):
        a_min, a_max = extents[i]
        b_min, b_max = extents[i + 1]
        overlap_m = max(0.0, min(a_max, b_max) - max(a_min, b_min))
        width_a = a_max - a_min
        width_b = b_max - b_min
        mean_width = (width_a + width_b) / 2.0
        results.append({
            "pair": (i, i + 1),
            "overlap_m": overlap_m,
            "tree_i_width_m": width_a,
            "tree_i1_width_m": width_b,
            "interpenetration_frac": (overlap_m / mean_width) if mean_width > 0 else 0.0,
        })
    return results


def run_one(tree_type, seed):
    canopy = build_canopy(seed=seed, tree_type=tree_type, n_trees=3, spacing=SPACING_M)
    try:
        extents = [tree_x_extent(canopy.context, canopy.tree_uuids(i))
                   for i in range(len(canopy.plant_ids))]
        overlaps = adjacent_overlaps(extents)
        mean_width = sum(e[1] - e[0] for e in extents) / len(extents)
        return {
            "tree_type": tree_type, "seed": seed, "spacing_m": SPACING_M,
            "per_tree_x_extent": extents, "mean_tree_width_m": mean_width,
            "adjacent_overlaps": overlaps,
            "mean_interpenetration_frac": sum(o["interpenetration_frac"] for o in overlaps) / len(overlaps),
        }
    finally:
        canopy.close()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = {"apple": [], "apple_fruitingwall": []}
    for tree_type in ("apple", "apple_fruitingwall"):
        for seed in SEEDS:
            r = run_one(tree_type, seed)
            results[tree_type].append(r)
            print(f"[{tree_type} seed={seed}] mean_tree_width_m={r['mean_tree_width_m']:.3f} "
                  f"mean_interpenetration_frac={r['mean_interpenetration_frac']:.3f} "
                  f"overlaps_m={[round(o['overlap_m'], 3) for o in r['adjacent_overlaps']]}", flush=True)

    summary = {}
    for tree_type in ("apple", "apple_fruitingwall"):
        rs = results[tree_type]
        summary[tree_type] = {
            "mean_tree_width_m": sum(r["mean_tree_width_m"] for r in rs) / len(rs),
            "mean_interpenetration_frac": sum(r["mean_interpenetration_frac"] for r in rs) / len(rs),
            "n_seeds_with_any_overlap": sum(1 for r in rs if r["mean_interpenetration_frac"] > 0),
            "n_seeds": len(rs),
        }

    report = {
        "spacing_m": SPACING_M, "seeds": SEEDS, "results": results, "summary": summary,
        "task_doc_claim": (
            "current 1.5m spacing already interpenetrates canopies under the plain "
            "apple type"
        ),
        "task_doc_claim_supported": bool(summary["apple"]["n_seeds_with_any_overlap"] == len(SEEDS)),
    }

    out_path = os.path.join(OUTPUT_DIR, "t83_fruitingwall_comparison.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\nSummary:")
    print(json.dumps(summary, indent=2))
    print(f"task_doc_claim_supported: {report['task_doc_claim_supported']}")
    print(f"wrote {out_path}")
    return report


if __name__ == "__main__":
    main()
