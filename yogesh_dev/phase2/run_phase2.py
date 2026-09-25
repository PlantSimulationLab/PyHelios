"""
Phase 2 end-to-end driver: T2.1-T2.6 (AVUB / NVE visibility ground truth),
per helios_setup_tasks.md.

Builds its OWN fresh 3-apple-tree scene (see "Fresh scene, not Phase 1's" in
PHASE2_LOG.md / below -- plant growth in this apple model is stochastic and
unseeded upstream in Phase 1, and primitive UUIDs from Phase 1's Context
can't be reused across Python processes anyway), then:

    T2.1  per-fruit visible-fraction vis_i(v) for a given pose, area-weighted
          over real ray-traced-visible primitives (see visibility.py for why
          this resolves true per-primitive occlusion, not just the
          object-level fruitID fallback the task brief anticipated), with a
          cross-check against getObjectDataLabelMap pixel-count fractions.
    T2.2  accumulated union visibility v_i_max(t) over a real multi-pose
          sequence (the 3-view rig per tree), demonstrating union > any
          single view.
    T2.3  PLACEHOLDER reachable view set V_reach + free-flying set (see
          reachable_poses.py) -- Phase 3 doesn't exist yet.
    T2.4  AVUB_i / AVUB_i^inf from T2.1+T2.3, and their ratio.
    T2.5  fruit achievability classes (observable/sizeable/graspable).
    T2.6  checked whether an occlusion-regulation module exists to validate
          against -- it doesn't (see t26_check.py); skipped honestly.

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase2.run_phase2
"""

import json
import os
import time

import numpy as np

from pyhelios import Context, PlantArchitecture, RadiationModel

from yogesh_dev.phase0.canopy import build_three_tree_scene
from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights
from yogesh_dev.phase0.radiation_cameras import (
    build_camera_properties, camera_position_for_tree, compute_tree_poses,
    RGB_BAND_LABELS,
)
from yogesh_dev.phase1.ground_truth import enable_fruit_object_data, export_fruit_ground_truth

from yogesh_dev.phase2.visibility import (
    assign_vis_primitive_ids, visible_primitive_ids_for_pose, render_poses_batched,
    fruit_visible_fraction, union_visible_ids,
)
from yogesh_dev.phase2.reachable_poses import placeholder_reachable_poses, placeholder_free_flying_poses
from yogesh_dev.phase2.avub import compute_avub, avub_ratio, summarize_avub
from yogesh_dev.phase2.achievability import classify_fruit, summarize_classes
from yogesh_dev.phase2.t26_check import check_occlusion_regulation_module_exists

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

RESOLUTION = (320, 240)  # reduced from Phase 0/1's 640x480 -- see PHASE2_LOG.md
ANTIALIASING_SAMPLES = 1  # reduced from Phase 0/1's 2 -- see PHASE2_LOG.md
VFOV_DEG = 45.0
CAMERA_LABELS = ["camA", "camB", "camC"]  # 3 reusable slots, T0.4-style
SEED = 20260729  # fixed for reproducibility of THIS run only -- Phase 1 did not seed

# T2.3 placeholder pose-grid density (see PHASE2_LOG.md for the timing test
# that sized these to keep the full sweep under ~10 minutes).
REACHABLE_GRID = dict(n_rail=6, n_height=6, n_depth=3)      # 108 poses/tree
FREE_FLYING_GRID = dict(n_azimuth=12, n_elevation=8, n_radius=3)  # 288 poses/tree

GAMMA_SIZE = 0.30


def _label_map_pixel_counts(label_map):
    valid = ~np.isnan(label_map)
    total_valid = int(valid.sum())
    if total_valid == 0:
        return {}, 0
    ids, counts = np.unique(np.round(label_map[valid]).astype(np.int64), return_counts=True)
    return {int(i): int(c) for i, c in zip(ids, counts)}, total_valid


def run_t21_t22_demo(radiation, plant_ids, positions, tree_poses, fruit_records_by_plant,
                      fruit_prim_ids, prim_id_to_info):
    """T2.1 (vis_i(v) + cross-validation against getObjectDataLabelMap pixel
    counts) and T2.2 (union accumulation over the 3-view rig per tree),
    using the SAME real 3-pose-per-tree rig Phase 0/1 used.
    """
    per_view_pairs = []  # (vis_area_frac, pixel_count_frac) for correlation
    union_demo = []       # per-fruit {object_id, per_view_fracs, union_frac, max_single_view_frac}

    for plant_id, poses in zip(plant_ids, tree_poses):
        for cam, (eye, lookat) in zip(CAMERA_LABELS, poses):
            radiation.setCameraPosition(cam, eye)
            radiation.setCameraLookat(cam, lookat)
        radiation.runBand(RGB_BAND_LABELS)

        view_visible_ids = []
        view_fruitid_counts = []
        view_total_valid = []
        for cam in CAMERA_LABELS[:len(poses)]:
            visible_ids, _pixel_counts = visible_primitive_ids_for_pose(radiation, cam)
            fruitid_map = radiation.getObjectDataLabelMap(cam, "fruitID")
            fruitid_counts, total_valid = _label_map_pixel_counts(fruitid_map)
            view_visible_ids.append(visible_ids)
            view_fruitid_counts.append(fruitid_counts)
            view_total_valid.append(total_valid)

        cumulative_union = union_visible_ids(view_visible_ids)

        for rec in fruit_records_by_plant.get(plant_id, []):
            oid = rec["object_id"]
            area = rec["surface_area_m2"]
            per_view_fracs = []
            for v in range(len(poses)):
                vis_frac, _ = fruit_visible_fraction(
                    view_visible_ids[v], fruit_prim_ids, prim_id_to_info, oid, area)
                pixel_frac = (
                    view_fruitid_counts[v].get(oid, 0) / view_total_valid[v]
                    if view_total_valid[v] > 0 else 0.0
                )
                per_view_fracs.append(vis_frac)
                if vis_frac > 0 or pixel_frac > 0:
                    per_view_pairs.append((vis_frac, pixel_frac))

            union_frac, _ = fruit_visible_fraction(
                cumulative_union[-1], fruit_prim_ids, prim_id_to_info, oid, area)
            max_single = max(per_view_fracs) if per_view_fracs else 0.0
            union_demo.append({
                "object_id": oid, "plant_id": plant_id,
                "per_view_fracs": per_view_fracs,
                "union_frac": union_frac,
                "max_single_view_frac": max_single,
                "union_minus_max_single": union_frac - max_single,
            })

    pairs = np.array(per_view_pairs)
    correlation = float(np.corrcoef(pairs[:, 0], pairs[:, 1])[0, 1]) if len(pairs) >= 2 else None

    n_improved = sum(1 for d in union_demo if d["union_minus_max_single"] > 1e-9)
    mean_delta = (
        sum(d["union_minus_max_single"] for d in union_demo) / len(union_demo)
        if union_demo else 0.0
    )
    best_example = max(union_demo, key=lambda d: d["union_minus_max_single"]) if union_demo else None

    return {
        "T2.1_cross_validation": {
            "n_fruit_view_pairs_with_signal": len(pairs),
            "pearson_correlation_vis_area_frac_vs_pixel_count_frac": correlation,
        },
        "T2.2_union_demo": {
            "n_fruit_seen_in_at_least_one_view": len(union_demo),
            "n_fruit_where_union_exceeds_max_single_view": n_improved,
            "mean_union_minus_max_single_view": mean_delta,
            "best_example": best_example,
        },
        "per_fruit_union_demo": union_demo,
    }


def run_pose_sweep(radiation, context, plantarch, plant_id, base_position, pose_kind):
    if pose_kind == "reachable":
        poses = placeholder_reachable_poses(context, plantarch, plant_id, base_position,
                                             vfov_deg=VFOV_DEG, aspect_ratio=RESOLUTION[0] / RESOLUTION[1],
                                             **REACHABLE_GRID)
    elif pose_kind == "free_flying":
        poses = placeholder_free_flying_poses(context, plantarch, plant_id, base_position,
                                               vfov_deg=VFOV_DEG, aspect_ratio=RESOLUTION[0] / RESOLUTION[1],
                                               **FREE_FLYING_GRID)
    else:
        raise ValueError(pose_kind)

    t0 = time.time()
    results = render_poses_batched(radiation, CAMERA_LABELS, poses, RGB_BAND_LABELS)
    dt = time.time() - t0
    per_pose_visible_ids = [r[0] for r in results]
    return poses, per_pose_visible_ids, dt


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = {}
    t_start = time.time()

    with Context() as context:
        context.seedRandomGenerator(SEED)
        report["seed"] = SEED

        with PlantArchitecture(context) as plantarch:
            enable_fruit_object_data(plantarch)
            t0 = time.time()
            plant_ids, positions = build_three_tree_scene(context, plantarch)
            report["build_time_s"] = time.time() - t0

            all_uuids = []
            for pid in plant_ids:
                all_uuids.extend(plantarch.getAllPlantUUIDs(pid))

            fruit_gt_path = os.path.join(OUTPUT_DIR, "phase2_fruit_ground_truth.json")
            fruit_records, gt_report = export_fruit_ground_truth(
                context, plantarch, plant_ids, fruit_gt_path)
            report["fruit_ground_truth"] = gt_report
            print(f"Built {len(plant_ids)} trees, {len(fruit_records)} fruit "
                  f"(Phase 1's own run had 73 -- see PHASE2_LOG.md for why this "
                  f"differs)", flush=True)

            fruit_records_by_plant = {}
            for rec in fruit_records:
                fruit_records_by_plant.setdefault(rec["plant_id"], []).append(rec)

            t1 = time.time()
            prim_id_to_info, fruit_prim_ids = assign_vis_primitive_ids(context, all_uuids, fruit_records)
            report["assign_vis_primitive_ids_s"] = time.time() - t1
            report["n_fruit_surface_primitives"] = len(prim_id_to_info)

            # T2.6: check whether an occlusion-regulation module exists at all
            report["T2.6"] = check_occlusion_regulation_module_exists(
                repo_dir=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            print("T2.6:", report["T2.6"]["conclusion"], flush=True)

            with RadiationModel(context) as radiation:
                setup_bands_and_lights(radiation)
                cam_props, hfov_deg = build_camera_properties(RESOLUTION, VFOV_DEG)
                aspect = RESOLUTION[0] / RESOLUTION[1]
                init_eye, init_lookat = camera_position_for_tree(
                    context, plantarch, plant_ids[0], positions[0], {"height_frac": 0.5}, aspect)
                for label in CAMERA_LABELS:
                    radiation.addRadiationCamera(
                        label, RGB_BAND_LABELS, init_eye, init_lookat,
                        camera_properties=cam_props, antialiasing_samples=ANTIALIASING_SAMPLES)

                radiation.updateGeometry()  # ONCE, per T0.4 -- geometry never changes below

                # --- T2.1 + T2.2 demo: real 3-view-per-tree rig ---
                tree_poses = compute_tree_poses(context, plantarch, plant_ids, positions, resolution=RESOLUTION)
                t2 = time.time()
                demo_report = run_t21_t22_demo(
                    radiation, plant_ids, positions, tree_poses, fruit_records_by_plant,
                    fruit_prim_ids, prim_id_to_info)
                report["T2.1_T2.2_demo_time_s"] = time.time() - t2
                report.update({k: v for k, v in demo_report.items() if k != "per_fruit_union_demo"})
                print(f"T2.1 cross-validation: {demo_report['T2.1_cross_validation']}", flush=True)
                print(f"T2.2 union demo: {demo_report['T2.2_union_demo']['n_fruit_where_union_exceeds_max_single_view']}"
                      f"/{demo_report['T2.2_union_demo']['n_fruit_seen_in_at_least_one_view']} fruit improved by union, "
                      f"mean delta {demo_report['T2.2_union_demo']['mean_union_minus_max_single_view']:.4f}", flush=True)

                # --- T2.3 + T2.4: placeholder reachable / free-flying sweeps, per tree ---
                per_fruit_avub = {}
                per_fruit_best_reach_eye = {}
                sweep_timing = {}
                for plant_id, base_position in zip(plant_ids, positions):
                    reach_poses, reach_visible, reach_dt = run_pose_sweep(
                        radiation, context, plantarch, plant_id, base_position, "reachable")
                    free_poses, free_visible, free_dt = run_pose_sweep(
                        radiation, context, plantarch, plant_id, base_position, "free_flying")
                    sweep_timing[plant_id] = {
                        "n_reachable_poses": len(reach_poses), "reachable_render_s": reach_dt,
                        "n_free_flying_poses": len(free_poses), "free_flying_render_s": free_dt,
                    }
                    print(f"Tree {plant_id}: {len(reach_poses)} reachable poses in {reach_dt:.1f}s, "
                          f"{len(free_poses)} free-flying poses in {free_dt:.1f}s", flush=True)

                    tree_fruit = fruit_records_by_plant.get(plant_id, [])
                    avub = compute_avub(reach_visible, tree_fruit, fruit_prim_ids, prim_id_to_info)
                    avub_inf = compute_avub(free_visible, tree_fruit, fruit_prim_ids, prim_id_to_info)
                    for rec in tree_fruit:
                        oid = rec["object_id"]
                        per_fruit_avub[oid] = {"AVUB_i": avub[oid], "AVUB_i_inf": avub_inf[oid]}

                    # best single reachable-pose view per fruit, for T2.5's approach-cone proxy
                    for rec in tree_fruit:
                        oid = rec["object_id"]
                        best_frac, best_eye = -1.0, None
                        for pose, visible_ids in zip(reach_poses, reach_visible):
                            frac, _ = fruit_visible_fraction(
                                visible_ids, fruit_prim_ids, prim_id_to_info, oid, rec["surface_area_m2"])
                            if frac > best_frac:
                                best_frac = frac
                                best_eye = (pose[0].x, pose[0].y, pose[0].z) if frac > 0 else None
                        per_fruit_best_reach_eye[oid] = best_eye

                report["sweep_timing"] = sweep_timing

                avub_only = {oid: v["AVUB_i"] for oid, v in per_fruit_avub.items()}
                avub_inf_only = {oid: v["AVUB_i_inf"] for oid, v in per_fruit_avub.items()}
                report["T2.4_AVUB_summary"] = summarize_avub(avub_only, avub_inf_only)
                report["T2.4_AVUB_summary"]["CAVEAT"] = (
                    "V_reach and the free-flying set are BOTH documented placeholders "
                    "(see reachable_poses.py) -- these numbers will change once Phase 3's "
                    "real kinematics-constrained roadmap replaces the placeholder grid."
                )
                print(f"T2.4 AVUB summary: {report['T2.4_AVUB_summary']}", flush=True)

                # --- T2.5: achievability classes ---
                classes = classify_fruit(fruit_records, avub_only, per_fruit_best_reach_eye, gamma_size=GAMMA_SIZE)
                report["T2.5_achievability_summary"] = summarize_classes(classes)
                report["T2.5_achievability_summary"]["gamma_size_used"] = GAMMA_SIZE
                print(f"T2.5 achievability: {report['T2.5_achievability_summary']}", flush=True)

                per_fruit_table = []
                for rec in fruit_records:
                    oid = rec["object_id"]
                    row = {
                        "object_id": oid, "plant_id": rec["plant_id"],
                        "surface_area_m2": rec["surface_area_m2"],
                        "AVUB_i": per_fruit_avub[oid]["AVUB_i"],
                        "AVUB_i_inf": per_fruit_avub[oid]["AVUB_i_inf"],
                    }
                    row["AVUB_over_AVUB_inf"] = avub_ratio(
                        {oid: row["AVUB_i"]}, {oid: row["AVUB_i_inf"]})[oid]
                    row.update(classes[oid])
                    per_fruit_table.append(row)

    with open(os.path.join(OUTPUT_DIR, "per_fruit_avub.json"), "w") as f:
        json.dump(per_fruit_table, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "per_fruit_union_demo.json"), "w") as f:
        json.dump(demo_report["per_fruit_union_demo"], f, indent=2)

    report["total_time_s"] = time.time() - t_start
    with open(os.path.join(OUTPUT_DIR, "phase2_run_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    main()
