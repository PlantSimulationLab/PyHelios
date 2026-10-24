"""
Phase 1 end-to-end driver: builds the real 3-apple-tree scene, enables the
optional plant-architecture object data (T1.1), renders all 9 views (3 trees
x 3 rig positions, reusing Phase 0's validated radiation-camera rig and
render loop), and exports:

    T1.2  fruit_ground_truth.json
    T1.3  per-view semantic + instance label maps (.npy + PNG preview)
    T1.4  per-view depth (.exr)
    T1.5  transforms.json (gsplat-compatible, extended)
    T1.6  a before/after RGB-D noise-model comparison on a couple of views

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase1.run_phase1
"""

import json
import os
import time

import numpy as np

from pyhelios import Context, PlantArchitecture, RadiationModel

from yogesh_dev.phase0.canopy import build_three_tree_scene
from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights
from yogesh_dev.phase0.radiation_cameras import (
    compute_tree_poses, register_camera_rig,
    DEFAULT_RESOLUTION, DEFAULT_ANTIALIASING_SAMPLES, RGB_BAND_LABELS,
)

from yogesh_dev.phase1.ground_truth import (
    enable_fruit_object_data, verify_object_data_on_fruit, export_fruit_ground_truth,
)
from yogesh_dev.phase1.label_maps import assign_semantic_class_ids, export_label_maps
from yogesh_dev.phase1.depth_export import export_depth_exr, read_depth_exr, depth_stats
from yogesh_dev.phase1.transforms_export import build_transforms, write_transforms
from yogesh_dev.phase1.noise_model import apply_rgbd_noise_model, compare_before_after

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
RGB_DIR = os.path.join(OUTPUT_DIR, "rgb")
LABELS_DIR = os.path.join(OUTPUT_DIR, "labels")
DEPTH_DIR = os.path.join(OUTPUT_DIR, "depth")
NOISE_DIR = os.path.join(OUTPUT_DIR, "noise_model_demo")

# How many of the 9 views to run the (more expensive, EXR read-back) T1.6
# noise-model before/after comparison on -- it's a demonstration of the
# model's effect size, not something that needs to run on every view.
N_NOISE_DEMO_VIEWS = 3


def main():
    report = {}
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RGB_DIR, exist_ok=True)
    os.makedirs(LABELS_DIR, exist_ok=True)
    os.makedirs(DEPTH_DIR, exist_ok=True)
    os.makedirs(NOISE_DIR, exist_ok=True)

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            # --- T1.1: enable optional object data BEFORE building any tree ---
            enabled_labels = enable_fruit_object_data(plantarch)
            print(f"T1.1: enabled optional object data: {enabled_labels}")

            t0 = time.time()
            plant_ids, positions = build_three_tree_scene(context, plantarch)
            build_time = time.time() - t0
            prim_counts = {pid: len(plantarch.getAllPlantUUIDs(pid)) for pid in plant_ids}
            print(f"Built {len(plant_ids)} trees in {build_time:.2f}s, primitive counts: {prim_counts}")

            all_uuids = []
            for pid in plant_ids:
                all_uuids.extend(plantarch.getAllPlantUUIDs(pid))

            # --- T1.1 verification: real listObjectData() check on a real fruit object ---
            fruit_uuids_check = context.filterPrimitivesByData(all_uuids, "object_label", "fruit")
            fruit_objs_check = context.getUniquePrimitiveParentObjectIDs(fruit_uuids_check, include_zero=False)
            t11_report = verify_object_data_on_fruit(context, fruit_objs_check)
            print(f"T1.1 verification: {t11_report}")
            report["T1.1_verification"] = t11_report
            if not t11_report["all_expected_present"]:
                raise RuntimeError(
                    "T1.1 [BLOCKER]: optionalOutputObjectData did not actually populate "
                    f"expected labels on a real fruit object. Report: {t11_report}"
                )

            # --- T1.2: fruit ground truth export ---
            fruit_gt_path = os.path.join(OUTPUT_DIR, "fruit_ground_truth.json")
            fruit_records, t12_report = export_fruit_ground_truth(
                context, plantarch, plant_ids, fruit_gt_path)
            print(f"T1.2: {t12_report}")
            report["T1.2_fruit_ground_truth"] = t12_report

            # --- T1.3 setup: derive semantic_class_id from object_label ---
            semantic_class_counts = assign_semantic_class_ids(context, all_uuids)
            print(f"T1.3 setup: semantic_class_id assigned, per-label primitive counts: {semantic_class_counts}")
            report["T1.3_semantic_class_counts"] = semantic_class_counts

            tree_poses = compute_tree_poses(context, plantarch, plant_ids, positions,
                                             resolution=DEFAULT_RESOLUTION)

            with RadiationModel(context) as radiation:
                setup_bands_and_lights(radiation)
                camera_labels, hfov_deg = register_camera_rig(
                    radiation, tree_poses[0], resolution=DEFAULT_RESOLUTION,
                    antialiasing_samples=DEFAULT_ANTIALIASING_SAMPLES)
                print(f"Registered cameras {camera_labels}, HFOV={hfov_deg:.3f} deg")

                radiation.updateGeometry()  # ONCE, per T0.4

                frames_info = []
                per_view_reports = []
                noise_demo_reports = []
                t_render_start = time.time()

                view_index = 0
                for plant_id, poses in zip(plant_ids, tree_poses):
                    for cam, (eye, lookat) in zip(camera_labels, poses):
                        radiation.setCameraPosition(cam, eye)
                        radiation.setCameraLookat(cam, lookat)

                    radiation.runBand(RGB_BAND_LABELS)  # ONE call, all bands, per T0.4

                    for cam, (eye, lookat) in zip(camera_labels, poses):
                        view_name = f"tree{plant_id}_{cam}"

                        rgb_filename = radiation.writeCameraImage(
                            camera=cam, bands=RGB_BAND_LABELS,
                            imagefile_base=view_name, image_path=RGB_DIR + os.sep,
                            flux_to_pixel_conversion=1.0,
                        )

                        label_report = export_label_maps(radiation, cam, LABELS_DIR, view_name)
                        per_view_reports.append(label_report)

                        depth_path = export_depth_exr(radiation, cam, DEPTH_DIR, view_name)

                        frames_info.append({
                            "eye": eye, "lookat": lookat,
                            "camera_label": cam, "plant_id": plant_id,
                            "file_path": os.path.relpath(rgb_filename, OUTPUT_DIR),
                            "depth_path": os.path.relpath(depth_path, OUTPUT_DIR),
                            "semantic_path": os.path.relpath(
                                os.path.join(LABELS_DIR, f"{view_name}_semantic.npy"), OUTPUT_DIR),
                            "instance_path": os.path.relpath(
                                os.path.join(LABELS_DIR, f"{view_name}_instance.npy"), OUTPUT_DIR),
                            "split": "test" if view_index % 8 == 0 else "train",
                        })

                        # --- T1.6: noise-model before/after demo on the first few views ---
                        if view_index < N_NOISE_DEMO_VIEWS:
                            clean_depth = read_depth_exr(depth_path)
                            semantic_map = np.load(os.path.join(LABELS_DIR, f"{view_name}_semantic.npy"))
                            valid_mask = ~np.isnan(semantic_map)
                            noisy_depth = apply_rgbd_noise_model(clean_depth, valid_mask, enable=True, seed=view_index)
                            cmp_report = compare_before_after(clean_depth, noisy_depth, valid_mask)
                            cmp_report["view"] = view_name
                            cmp_report["clean_depth_stats"] = depth_stats(clean_depth, valid_mask)
                            noise_demo_reports.append(cmp_report)
                            np.save(os.path.join(NOISE_DIR, f"{view_name}_depth_clean.npy"), clean_depth)
                            np.save(os.path.join(NOISE_DIR, f"{view_name}_depth_noisy.npy"), noisy_depth)

                        view_index += 1

                t_render_total = time.time() - t_render_start
                print(f"Rendered + exported {view_index} views in {t_render_total:.2f}s "
                      f"({t_render_total / view_index:.2f}s/view)")
                report["render_total_s"] = t_render_total
                report["render_per_view_s"] = t_render_total / view_index
                report["n_views"] = view_index
                report["T1.3_per_view"] = per_view_reports

                # --- T1.5: transforms.json ---
                transforms = build_transforms(hfov_deg, DEFAULT_RESOLUTION, frames_info)
                write_transforms(transforms, os.path.join(OUTPUT_DIR, "transforms.json"))
                report["T1.5_transforms"] = {
                    "n_frames": len(transforms["frames"]),
                    "hfov_deg": hfov_deg,
                    "fl_x": transforms["fl_x"], "fl_y": transforms["fl_y"],
                    "cx": transforms["cx"], "cy": transforms["cy"],
                }

                report["T1.6_noise_demo"] = noise_demo_reports

    with open(os.path.join(OUTPUT_DIR, "phase1_run_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
