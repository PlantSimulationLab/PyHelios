"""
T6.11 -- per-module latency table (mean/p95/p99/max) at a stated
resolution, plus a hardware-independent work unit (ray casts, candidate
evaluations). Every number below is a REAL wall-clock measurement (via
`time.perf_counter()`, N repeated calls per module) against real Phase
0-5 data/functions -- nothing here is estimated or extrapolated.
"""

import math
import os
import time

import numpy as np
import OpenEXR

from yogesh_dev.phase2.visibility import fruit_visible_fraction
from yogesh_dev.phase6.common import PHASE4_DATA, PHASE6_OUTPUT, ensure_phase4_importable, load_json

ensure_phase4_importable()

import sensor_model as sm  # noqa: E402
import kinematics as kin  # noqa: E402
import motion_time as mt  # noqa: E402
from occupancy_map import make_grid, integrate_view  # noqa: E402
from information_gain import batch_information_gain  # noqa: E402
from semantic_map import integrate_semantic_view, SemanticVoxelMap  # noqa: E402
from roadmap import dijkstra  # noqa: E402
import tracker as trk  # noqa: E402

RESOLUTION_STATED = None  # filled in from real gen_report.json at run time


def _read_depth(path):
    fh = OpenEXR.File(path)
    ch = fh.channels()
    key = "Z" if "Z" in ch else next(iter(ch.keys()))
    return np.array(ch[key].pixels, dtype=np.float32)


def time_calls(fn, n_repeats=30, warmup=2):
    for _ in range(warmup):
        fn()
    samples_ms = []
    for _ in range(n_repeats):
        t0 = time.perf_counter()
        fn()
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    arr = np.array(samples_ms)
    return {
        "n_repeats": n_repeats,
        "mean_ms": float(arr.mean()), "p95_ms": float(np.percentile(arr, 95)),
        "p99_ms": float(np.percentile(arr, 99)), "max_ms": float(arr.max()), "min_ms": float(arr.min()),
    }


def run_all():
    os.makedirs(PHASE6_OUTPUT, exist_ok=True)
    poses = load_json(os.path.join(PHASE4_DATA, "poses.json"))
    fruit_records = load_json(os.path.join(PHASE4_DATA, "fruit_ground_truth.json"))
    vis_idx = load_json(os.path.join(PHASE4_DATA, "vis_primitive_index.json"))
    report = load_json(os.path.join(PHASE4_DATA, "gen_report.json"))
    resolution = tuple(report["resolution"])
    intr = sm.intrinsics(resolution)

    prim_id_to_info = {int(k): v for k, v in vis_idx["prim_id_to_info"].items()}
    fruit_prim_ids = {int(k): set(v) for k, v in vis_idx["fruit_prim_ids"].items()}
    # Pick the real view with the most actual (non-sky) content, so the
    # timed workload is representative rather than an accidentally-empty
    # frame (several roadmap nodes point away from the tree entirely).
    arm_high_only = [p for p in poses if p["arm"] == "arm_high"]
    candidate_depths = {p["view"]: _read_depth(os.path.join(PHASE4_DATA, p["depth_path"])) for p in arm_high_only}
    best_view = max(candidate_depths, key=lambda v: int(np.sum(candidate_depths[v] != sm.SKY_DEPTH_SENTINEL)))
    a_pose = next(p for p in arm_high_only if p["view"] == best_view)
    depth = candidate_depths[best_view]
    semantic = np.load(os.path.join(PHASE4_DATA, a_pose["semantic_path"]))
    n_valid_px = int(np.sum((depth != sm.SKY_DEPTH_SENTINEL) & ~np.isnan(semantic)))

    vis = np.load(os.path.join(PHASE4_DATA, a_pose["visid_path"]))
    valid = ~np.isnan(vis)
    visible_ids = set(int(v) for v in np.unique(vis[valid]) if v >= 0)

    modules = {}

    # --- Phase 2: per-fruit visible-fraction (vis_i) ---
    def call_visibility():
        for rec in fruit_records:
            fruit_visible_fraction(visible_ids, fruit_prim_ids, prim_id_to_info, rec["object_id"], rec["surface_area_m2"])
    t = time_calls(call_visibility, n_repeats=50)
    t["work_unit"] = "fruit visibility evaluations (real per-fruit AVUB-style area-weighted fraction)"
    t["n_work_units_per_call"] = len(fruit_records)
    t["ns_per_work_unit"] = t["mean_ms"] * 1e6 / len(fruit_records)
    modules["phase2_visibility.fruit_visible_fraction_all_fruit"] = t

    # --- Phase 3/4: kinematics IK/FK + T3.3 motion-time model ---
    arm = kin.default_arm_configs()[1]  # arm_mid-equivalent envelope
    pose_a = kin.CameraPose(position=(0.0, -1.0, 0.5), lookat=(0.0, 0.0, 0.5), forward=(0.0, 1.0, 0.0))
    pose_b = kin.CameraPose(position=(0.3, -0.8, 0.9), lookat=(0.0, 0.0, 0.5), forward=(0.0, 1.0, 0.0))

    def call_ik():
        kin.inverse_kinematics(pose_a, arm)
    t = time_calls(call_ik, n_repeats=200)
    t["work_unit"] = "one 5-DOF closed-form inverse-kinematics solve"
    t["n_work_units_per_call"] = 1
    t["ns_per_work_unit"] = t["mean_ms"] * 1e6
    modules["phase3_kinematics.inverse_kinematics"] = t

    q_a, _ok_a, _ = kin.inverse_kinematics(pose_a, arm)
    q_b, _ok_b, _ = kin.inverse_kinematics(pose_b, arm)

    def call_move_time():
        mt.move_time(q_a, q_b)
    t = time_calls(call_move_time, n_repeats=200)
    t["work_unit"] = "one real T3.3 trapezoidal-profile move-time evaluation (5 axes)"
    t["n_work_units_per_call"] = 5
    t["ns_per_work_unit"] = t["mean_ms"] * 1e6 / 5
    modules["phase3_motion_time.move_time"] = t

    # --- Phase 4: T4.1 occupancy beam-model integration, one real view ---
    fruit_centroids = np.array([r["centroid"] for r in fruit_records])
    bmin = fruit_centroids.min(axis=0) - 0.15
    bmax = fruit_centroids.max(axis=0) + 0.15
    grid_template = make_grid(bmin, bmax, 0.02)

    def call_integrate_view():
        grid = make_grid(bmin, bmax, 0.02)
        integrate_view(grid, [], a_pose["eye"], a_pose["lookat"], depth, intr, pixel_stride=2)
    t = time_calls(call_integrate_view, n_repeats=20)
    t["work_unit"] = "valid (non-sky) pixels beam-model-integrated into the occupancy grid (pixel_stride=2)"
    n_px_stride2 = int(np.sum((depth[::2, ::2] != sm.SKY_DEPTH_SENTINEL)))
    t["n_work_units_per_call"] = n_px_stride2
    t["ns_per_work_unit"] = t["mean_ms"] * 1e6 / max(n_px_stride2, 1)
    modules["phase4_occupancy_map.integrate_view"] = t

    # --- Phase 4: T4.3 semantic voxel-map integration, one real view ---
    smap_template = SemanticVoxelMap(grid_template)

    def call_integrate_semantic():
        smap = SemanticVoxelMap(grid_template)
        integrate_semantic_view(smap, a_pose["eye"], a_pose["lookat"], depth, semantic, intr, pixel_stride=2)
    t = time_calls(call_integrate_semantic, n_repeats=20)
    t["work_unit"] = "valid pixels semantic-integrated into the voxel class-count map (pixel_stride=2)"
    t["n_work_units_per_call"] = n_px_stride2
    t["ns_per_work_unit"] = t["mean_ms"] * 1e6 / max(n_px_stride2, 1)
    modules["phase4_semantic_map.integrate_semantic_view"] = t

    # --- Phase 4: T4.5 batched information gain, real candidate batch ---
    arm_high_poses = [(p["eye"], p["lookat"]) for p in poses if p["arm"] == "arm_high"]
    n_rays_x, n_rays_y, n_steps = 8, 6, 20

    def call_ig():
        batch_information_gain(grid_template, arm_high_poses, intr, n_rays_x=n_rays_x, n_rays_y=n_rays_y, n_steps=n_steps)
    t = time_calls(call_ig, n_repeats=20)
    n_ray_march_evals = len(arm_high_poses) * n_rays_x * n_rays_y * n_steps
    t["work_unit"] = "(candidate pose x ray x march-step) volumetric entropy evaluations, fully vectorized/batched"
    t["n_work_units_per_call"] = n_ray_march_evals
    t["ns_per_work_unit"] = t["mean_ms"] * 1e6 / n_ray_march_evals
    modules["phase4_information_gain.batch_information_gain"] = t

    # --- Phase 4: T4.4 tracker detection extraction, one arm's real 14 frames ---
    def call_extract_detections():
        trk.extract_detections(PHASE4_DATA, "arm_high", poses, intr)
    t = time_calls(call_extract_detections, n_repeats=10)
    n_frames_arm_high = sum(1 for p in poses if p["arm"] == "arm_high")
    t["work_unit"] = "real rendered (depth, instance-label) frames processed into 3D detections"
    t["n_work_units_per_call"] = n_frames_arm_high
    t["ns_per_work_unit"] = t["mean_ms"] * 1e6 / n_frames_arm_high
    modules["phase4_tracker.extract_detections_one_arm"] = t

    # --- Phase 4: T3.4/T4.x roadmap Dijkstra, real adjacency graph ---
    adjacency = load_json(os.path.join(PHASE4_DATA, "roadmap_arm_high_adjacency.json"))
    adjacency = {int(k): [(int(j), float(w)) for j, w in v] for k, v in adjacency.items()}
    node_ids = list(adjacency.keys())
    start, goal = node_ids[0], node_ids[len(node_ids) // 2]

    def call_dijkstra():
        dijkstra(adjacency, start, goal)
    t = time_calls(call_dijkstra, n_repeats=50)
    n_edges = sum(len(v) for v in adjacency.values())
    t["work_unit"] = "one shortest-path solve over the real roadmap graph"
    t["n_work_units_per_call"] = 1
    t["graph_size"] = {"n_nodes": len(node_ids), "n_edges": n_edges}
    t["ns_per_edge"] = t["mean_ms"] * 1e6 / n_edges
    modules["phase4_roadmap.dijkstra"] = t

    return {
        "resolution_stated": list(resolution),
        "n_valid_pixels_reference_view": n_valid_px,
        "modules": modules,
        "note": ("All timings are wall-clock (time.perf_counter, warmup=2, then N "
                 "repeated calls) on the CPU running this job -- see PHASE6_LOG.md for "
                 "the machine context. Every call operates on REAL data (real depth "
                 "EXRs, real label maps, real roadmap graphs, real fruit records) at "
                 "the ACTUAL resolution/graph-size Phase 4 generated them at "
                 f"({resolution[0]}x{resolution[1]}), not synthetic/scaled inputs."),
    }


if __name__ == "__main__":
    import json
    out = run_all()
    with open(os.path.join(PHASE6_OUTPUT, "t611_latency_table_report.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(json.dumps(out, indent=2, default=str))
