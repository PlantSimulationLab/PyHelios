"""
T7.1 driver -- builds one real apple tree, renders a real 16-view 360 deg
orbit (RGB + depth + semantic mask + exact pose/intrinsics for every
view), and writes it as one real WAI-format scene under
`yogesh_dev/phase7/output/wai_dataset/`.

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python \
        -m yogesh_dev.phase7.run_t71_wai_writer
"""

import json
import os

from pyhelios import Context, PlantArchitecture, RadiationModel

from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights
from yogesh_dev.phase1.ground_truth import enable_fruit_object_data

from yogesh_dev.phase7.render_utils import (
    RESOLUTION, build_tree_scene, tree_lookat_and_radius, full_circle_poses, register_camera_pool,
)
from yogesh_dev.phase7.wai_writer import write_wai_scene

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
WAI_ROOT = os.path.join(OUTPUT_DIR, "wai_dataset")
N_VIEWS = 16
TREE_AGE_DAYS = 720.0


def main():
    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            enable_fruit_object_data(plantarch)
            plant_id, position, all_uuids = build_tree_scene(context, plantarch, age_days=TREE_AGE_DAYS)
            lookat, radius, height, width = tree_lookat_and_radius(context, all_uuids, position)
            poses, azs_deg = full_circle_poses(lookat, radius, N_VIEWS, elevation_deg=12.0)

            with RadiationModel(context) as radiation:
                setup_bands_and_lights(radiation)
                labels, hfov_deg = register_camera_pool(radiation, N_VIEWS)
                radiation.updateGeometry()

                for label, (eye, lookat_p) in zip(labels, poses):
                    radiation.setCameraPosition(label, eye)
                    radiation.setCameraLookat(label, lookat_p)
                radiation.runBand(["red", "green", "blue"])

                extra = [{"azimuth_deg": float(a), "plant_id": plant_id,
                          "split": "test" if i % 8 == 0 else "train"}
                         for i, a in enumerate(azs_deg)]
                scene_meta = write_wai_scene(
                    radiation, labels, poses, hfov_deg, RESOLUTION, WAI_ROOT,
                    dataset_name="helios_apple_tree", scene_name="tree0_orbit16",
                    write_rgb=True, write_depth=True, write_semantic_mask=True,
                    extra_frame_fields=extra,
                )

    report = {
        "n_frames": len(scene_meta["frames"]),
        "scene_meta_path": os.path.join(WAI_ROOT, "helios_apple_tree", "tree0_orbit16", "scene_meta.json"),
        "fl_x": scene_meta["fl_x"], "fl_y": scene_meta["fl_y"],
        "cx": scene_meta["cx"], "cy": scene_meta["cy"], "w": scene_meta["w"], "h": scene_meta["h"],
        "sample_frame": scene_meta["frames"][0],
    }
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "t71_wai_writer_report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    main()
