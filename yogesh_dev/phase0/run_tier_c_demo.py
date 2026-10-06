"""
Integration demo for T0.1 + T0.2 + T0.4: build the standard 3-apple-tree
scene, register the 3-camera radiation rig, run the correct render loop
(updateGeometry once, one runBand per pose), and write one PNG per
camera/tree to yogesh_dev/phase0/renders_tier_c/ so the render can be
eyeballed for sanity (not black, not blown out, trees recognizable).

Run:
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase0.run_tier_c_demo
"""

import os
import time

from pyhelios import Context, PlantArchitecture, RadiationModel

from .canopy import build_three_tree_scene
from .radiation_setup import setup_bands_and_lights
from .radiation_cameras import (
    compute_tree_poses, register_camera_rig,
    DEFAULT_RESOLUTION, DEFAULT_ANTIALIASING_SAMPLES, RGB_BAND_LABELS,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "renders_tier_c")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with Context() as context:
        with PlantArchitecture(context) as plantarch:
            plant_ids, positions = build_three_tree_scene(context, plantarch)
            for plant_id in plant_ids:
                n_prim = len(plantarch.getAllPlantUUIDs(plant_id))
                print(f"Tree plant_id={plant_id}: {n_prim} primitives")

            tree_poses = compute_tree_poses(context, plantarch, plant_ids, positions,
                                             resolution=DEFAULT_RESOLUTION)

            with RadiationModel(context) as radiation:
                setup_bands_and_lights(radiation)
                camera_labels, hfov_deg = register_camera_rig(
                    radiation, tree_poses[0], resolution=DEFAULT_RESOLUTION,
                    antialiasing_samples=DEFAULT_ANTIALIASING_SAMPLES)
                print(f"Registered cameras {camera_labels}, HFOV={hfov_deg:.3f} deg")

                # T0.4 render loop, inlined here with image writing per pose
                # (the reusable, no-file-IO version lives in
                # radiation_cameras.run_render_loop and is what T0.5 times).
                radiation.updateGeometry()  # ONCE, outside the pose loop
                t0 = time.time()
                for plant_id, poses in zip(plant_ids, tree_poses):
                    for cam, (eye, lookat) in zip(camera_labels, poses):
                        radiation.setCameraPosition(cam, eye)
                        radiation.setCameraLookat(cam, lookat)

                    radiation.runBand(RGB_BAND_LABELS)  # ONE call, all bands

                    for cam in camera_labels:
                        filename = radiation.writeCameraImage(
                            camera=cam, bands=RGB_BAND_LABELS,
                            imagefile_base=f"tree{plant_id}_{cam}",
                            image_path=OUTPUT_DIR + os.sep,
                            # See radiation_setup.py's DEFAULT_BAND_FLUX comment: the
                            # sRGB gamma step clips raw radiance >= 1.0 to solid white
                            # *before* this factor is applied, so exposure is tuned via
                            # flux, not here. ~15-20% of foliage pixels will still clip
                            # regardless of flux -- see the "KNOWN ARTIFACT" note.
                            flux_to_pixel_conversion=1.0,
                        )
                        print(f"  wrote {filename}")
                t1 = time.time()
                print(f"Rendered {len(tree_poses)} tree poses x {len(camera_labels)} cams "
                      f"in {t1 - t0:.3f}s total ({(t1 - t0) / len(tree_poses):.3f}s/pose)")


if __name__ == "__main__":
    main()
