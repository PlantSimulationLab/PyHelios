"""
Phase 3 integration demo: T3.1 (FK) + T3.2 (IK + round-trip verification) +
T3.3 (execution-time model) + T3.4 (roadmap building) + T3.5 (arm geometry +
vertical-band verification), run for real against the actual fruit
bounding-box geometry exported in Phase 1
(`yogesh_dev/phase3/reference_data/fruit_ground_truth.json`, copied from
`worktree-phase1-groundtruth:yogesh_dev/phase1/output/fruit_ground_truth.json`
-- 73 real fruit objects across 3 apple trees).

Run:
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase3.run_phase3_demo

Requires a working pyhelios native build only for the T3.5 live-Context
section (Context + addBox + getDomainBoundingBox); T3.1-T3.4 need nothing
beyond the standard library + numpy.
"""

import json
import os
import time

from .kinematics import default_arm_configs, verify_roundtrip
from .motion_time import demonstrate_asymmetry, move_time
from .roadmap import canopy_boxes_from_ground_truth, build_roadmap, dijkstra
from .arm_geometry import verify_non_overlapping_bands

REFERENCE_DATA = os.path.join(os.path.dirname(__file__), "reference_data", "fruit_ground_truth.json")


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def run_t31_t32(arms):
    section("T3.1/T3.2 -- Forward/inverse kinematics + round-trip verification")
    results = []
    for arm in arms:
        r = verify_roundtrip(arm, n_per_axis=5, seed=hash(arm.name) & 0xFFFF)
        results.append(r)
        print(f"[{arm.name}] limits: x={arm.limits.x} y={arm.limits.y} z(band)={arm.limits.z} "
              f"pan={arm.limits.pan_deg}deg tilt={arm.limits.tilt_deg}deg")
        print(f"[{arm.name}] round-trip over {r['n_checked']} samples: "
              f"max_position_error={r['max_position_error_m']:.3e} m, "
              f"max_lookat_error={r['max_lookat_error_m']:.3e} m, "
              f"max_joint_error={r['max_joint_error']:.3e}, "
              f"limit_violations={r['n_limit_violations']}, PASSED={r['passed']}")
        assert r["passed"], f"FK(IK(pose)) round-trip failed for {arm.name}"
    return results


def run_t33():
    section("T3.3 -- Execution-time model (trapezoidal velocity profile)")
    asym = demonstrate_asymmetry()
    for k, v in asym.items():
        print(f"  {k}: {v:.3f} s")
    rail_vs_pan = asym["full_rail_traverse_s"] / asym["full_pan_sweep_s"]
    print(f"  cost asymmetry (full rail traverse / full pan sweep): {rail_vs_pan:.1f}x")
    return asym


def run_t34(arms, fruit_records):
    section("T3.4 -- Roadmap building (discretize -> placeholder-collision-reject -> k-NN, real exec-time weights)")
    boxes = canopy_boxes_from_ground_truth(fruit_records)
    print(f"Placeholder canopy collision boxes (per-plant fruit AABB, from Phase 1 ground truth):")
    for pid, (bmin, bmax) in boxes.items():
        print(f"  plant {pid}: min={bmin.tolist()} max={bmax.tolist()}")

    roadmap_summary = {}
    for arm in arms:
        t0 = time.time()
        nodes, adjacency, n_rejected = build_roadmap(arm, boxes, n_linear=6, n_gimbal=4, k=6)
        build_time = time.time() - t0
        n_edges = sum(len(v) for v in adjacency.values())
        print(f"[{arm.name}] grid_samples={n_rejected + len(nodes)} rejected(placeholder collision)={n_rejected} "
              f"reachable_nodes={len(nodes)} edges={n_edges} build_time={build_time:.3f}s")

        path_info = None
        if len(nodes) > 1:
            start, goal = 0, len(nodes) - 1
            path, cost = dijkstra(adjacency, start, goal)
            if path is not None:
                print(f"[{arm.name}] shortest path node[{start}] -> node[{goal}]: "
                      f"{len(path)} nodes, total_exec_time={cost:.3f}s")
                path_info = {"start": start, "goal": goal, "n_hops": len(path), "total_time_s": cost}
            else:
                print(f"[{arm.name}] node[{start}] and node[{goal}] are not connected in the k-NN graph")

        roadmap_summary[arm.name] = {
            "grid_samples": n_rejected + len(nodes),
            "rejected": n_rejected,
            "reachable_nodes": len(nodes),
            "edges": n_edges,
            "build_time_s": build_time,
            "shortest_path_demo": path_info,
        }
    return roadmap_summary


def run_t35_bands(arms):
    section("T3.5 -- Vertical-band non-overlap check (pure Python interval math, not findCollisions)")
    ok, conflicts = verify_non_overlapping_bands(arms)
    for arm in arms:
        print(f"  {arm.name}: z-band = {arm.limits.z}")
    print(f"All bands disjoint: {ok}" + ("" if ok else f", conflicts: {conflicts}"))
    assert ok, f"arm z-bands overlap: {conflicts}"
    return ok


def run_t35_context(arms):
    """T3.5's live-Context half: add arm link boxes to an actual Helios
    Context and cross-check via getDomainBoundingBox. Requires a working
    pyhelios native build."""
    section("T3.5 -- Arm link geometry in a live Helios Context")
    try:
        from pyhelios import Context
        from .arm_geometry import add_arm_link_geometry, verify_geometry_bands_via_context
    except Exception as e:  # pragma: no cover - environment-dependent
        print(f"SKIPPED: pyhelios native library not available in this environment ({e}).")
        print("Vertical-band non-overlap was already verified in pure Python above (T3.5 part 1);")
        print("this section only exercises adding the same bands as real Context geometry.")
        return None

    with Context() as context:
        uuids = add_arm_link_geometry(context, arms, mast_x_positions=[0.0, 1.5, 3.0])
        for name, u in uuids.items():
            print(f"  {name}: added {len(u)} primitive(s) as its arm-link mast box")
        ok, zranges = verify_geometry_bands_via_context(context, uuids)
        print(f"  Context-derived z-ranges (via getDomainBoundingBox): {zranges}")
        print(f"  Bands disjoint per live Context geometry: {ok}")
        assert ok, "Context-derived arm geometry bands overlap"
    return {"context_zranges": zranges, "disjoint": ok}


def main():
    with open(REFERENCE_DATA) as f:
        fruit_records = json.load(f)
    print(f"Loaded {len(fruit_records)} real fruit records from Phase 1 ground truth "
          f"({REFERENCE_DATA})")

    arms = default_arm_configs()

    t31_t32 = run_t31_t32(arms)
    t33 = run_t33()
    t34 = run_t34(arms, fruit_records)
    t35_bands_ok = run_t35_bands(arms)
    t35_context = run_t35_context(arms)

    section("SUMMARY")
    print(f"Arms: {[a.name for a in arms]}")
    print(f"FK/IK round-trip: {'PASS' if all(r['passed'] for r in t31_t32) else 'FAIL'} "
          f"(max errors all < {t31_t32[0]['tolerance']:.0e})")
    print(f"Cost asymmetry (rail traverse / pan sweep): "
          f"{t33['full_rail_traverse_s'] / t33['full_pan_sweep_s']:.1f}x")
    for name, s in t34.items():
        print(f"Roadmap[{name}]: {s['reachable_nodes']}/{s['grid_samples']} nodes reachable "
              f"(placeholder collision), {s['edges']} edges")
    print(f"Vertical bands non-overlapping (structural arm-arm collision guarantee): {t35_bands_ok}")
    if t35_context is not None:
        print(f"Live-Context arm geometry bands disjoint: {t35_context['disjoint']}")
    else:
        print("Live-Context arm geometry check: SKIPPED (no pyhelios native build in this run)")


if __name__ == "__main__":
    main()
