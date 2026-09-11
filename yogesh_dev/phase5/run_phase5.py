"""
Phase 5 end-to-end driver: T5.1-T5.8 (baselines and oracles), per
helios_setup_tasks.md.

Builds ONE fresh 3-apple-tree scene (real Phase 0/1/2 machinery), renders +
caches the real V_reach (Phase 2's PLACEHOLDER_reachable_poses, 108
poses/tree) and the static 3-camera rig (9 poses) ONCE, then scores every
baseline from that cached real data -- see common.py's module docstring for
why this makes all eight numbers directly comparable.

T5.9 is intentionally NOT run here -- it's a separate, fully offline
(no live pyhelios) ablation against Phase 4's existing dataset/exploit
planner. See t59_perfect_perception.py.

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase5.run_phase5
"""

import json
import os
import time

from .common import (
    OUTPUT_DIR, build_scene, open_radiation,
    render_and_cache_reachable, render_static_rig_and_single_fixed,
)
from .t51_single_fixed import run_t51
from .t52_static_rig import run_t52
from .t53_boustrophedon import run_t53
from .t54_random_reachable import run_t54
from .t55_nearest_frontier import run_t55
from .t56_greedy_oracle import run_t56
from .t57_ilp_setcover import run_t57
from .t58_all_reachable_fusion import run_t58


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = {}
    t_start = time.time()

    scene = build_scene()
    report["seed"] = scene["seed"]
    report["build_time_s"] = scene["build_time_s"]
    report["fruit_ground_truth"] = scene["gt_report"]
    report["n_fruit"] = len(scene["fruit_records"])
    report["n_fruit_surface_primitives"] = scene["n_fruit_surface_primitives"]
    print(f"Built {len(scene['plant_ids'])} trees, {len(scene['fruit_records'])} fruit, "
          f"{scene['n_fruit_surface_primitives']} fruit-surface primitives, "
          f"build_time={scene['build_time_s']:.1f}s", flush=True)

    fruit_records = scene["fruit_records"]
    fruit_prim_ids = scene["fruit_prim_ids"]
    prim_id_to_info = scene["prim_id_to_info"]

    try:
        radiation, hfov_deg = open_radiation(scene)
        report["hfov_deg"] = hfov_deg

        t0 = time.time()
        reachable_candidates, per_tree_timing = render_and_cache_reachable(radiation, scene)
        report["reachable_render_s"] = time.time() - t0
        report["n_reachable_candidates"] = len(reachable_candidates)
        report["per_tree_reachable_timing"] = per_tree_timing
        print(f"Rendered+cached {len(reachable_candidates)} real V_reach poses in "
              f"{report['reachable_render_s']:.1f}s", flush=True)

        t0 = time.time()
        static_rig, single_fixed = render_static_rig_and_single_fixed(radiation, scene)
        report["static_rig_render_s"] = time.time() - t0
        print(f"Rendered+cached static 3-camera rig (9 poses) + single-fixed pose in "
              f"{report['static_rig_render_s']:.1f}s", flush=True)

        results = {}

        t0 = time.time()
        results["T5.1"] = run_t51(single_fixed, fruit_records, fruit_prim_ids, prim_id_to_info)
        print("T5.1 single fixed camera:", {k: v for k, v in results["T5.1"].items() if k != "trace"}, flush=True)

        results["T5.2"] = run_t52(static_rig, fruit_records, fruit_prim_ids, prim_id_to_info)
        print("T5.2 static 3-camera rig:", {k: v for k, v in results["T5.2"].items() if k != "trace"}, flush=True)

        results["T5.3"] = run_t53(reachable_candidates, scene["plant_ids"], fruit_records, fruit_prim_ids, prim_id_to_info)
        print("T5.3 boustrophedon raster:",
              {k: v for k, v in results["T5.3"].items() if k not in ("trace", "discovery_curve")}, flush=True)

        results["T5.4"] = run_t54(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info)
        print("T5.4 random reachable (by k):", results["T5.4"]["by_k"], flush=True)

        results["T5.5"] = run_t55(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info)
        print("T5.5 nearest-frontier + distance advantage:",
              {k: v for k, v in results["T5.5"].items() if k != "trace"}, flush=True)

        results["T5.6"] = run_t56(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info)
        print("T5.6 greedy oracle:", {k: v for k, v in results["T5.6"].items() if k not in ("trace", "at_k")}, flush=True)
        print("T5.6 at_k:", results["T5.6"]["at_k"], flush=True)

        # T5.6's real brute-force greedy trace, restated as {k: [selected candidate indices]}
        # -- a real, independently-computed lower bound T5.7 cross-validates against
        # (see t57_ilp_setcover.py's module docstring: CBC's own "Optimal" status
        # cannot be trusted alone at this problem's scale).
        greedy_trace = results["T5.6"]["trace"]
        greedy_selected_by_k = {
            k: [step["candidate_index"] for step in greedy_trace[:k]]
            for k in range(1, len(greedy_trace) + 1)
        }
        results["T5.7"] = run_t57(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info,
                                   greedy_selected_by_k=greedy_selected_by_k)
        print("T5.7 ILP set-cover optimum (by k):", results["T5.7"]["by_k"], flush=True)

        results["T5.8"] = run_t58(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info)
        print("T5.8 all-reachable fusion:", results["T5.8"], flush=True)

        report["baseline_compute_time_s"] = time.time() - t0
        report["results"] = results
    finally:
        # radiation/plantarch/context are context managers entered manually
        # in common.py (build_scene/open_radiation) -- close in reverse order.
        try:
            radiation.__exit__(None, None, None)
        except NameError:
            pass
        scene["plantarch"].__exit__(None, None, None)
        scene["context"].__exit__(None, None, None)

    report["total_time_s"] = time.time() - t_start

    with open(os.path.join(OUTPUT_DIR, "phase5_run_report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2, default=str))
    return report


if __name__ == "__main__":
    main()
