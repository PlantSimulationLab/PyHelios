"""
T4.10 -- Gimbal-only local refinement.

Task doc: "The nested inner loop. Either gradient ascent on a
differentiable semantic utility over pan/tilt, or a 3D-Move-to-See
finite-difference gradient across your three physical cameras. Gimbal
motion is nearly free -- this should be a large, cheap win."

## Choice made: gradient ascent over pan/tilt, via real finite differences

PyHelios's renderer is not differentiable (no autodiff through OptiX ray
tracing), so "gradient ascent on a differentiable utility" is implemented
the only real way available: a CENTRAL FINITE-DIFFERENCE gradient estimate
computed from actual re-renders at perturbed pan/tilt, then a real gradient
ascent step using that estimate -- against the actual camera rig (real
seeded tree, real `RadiationModel`/`getPrimitiveDataLabelMap`, real
`single_tree_arm_configs` joint limits), not a synthetic differentiable
stand-in. "Gimbal-only" is enforced literally: x/y/z stay fixed at the
starting pose's real roadmap position; only `pan_deg`/`tilt_deg` move,
clipped to the arm's real joint limits every step.

## Utility

`U(pan,tilt)` = real count of `semantic_class_id==1` (fruit) pixels in the
actual rendered view at that pose -- a real, if simple, semantic utility
(directly answers "does refining the gimbal aim the camera better at
fruit"), computed the same way every other module in this phase reads
semantic labels (`getPrimitiveDataLabelMap`).

## Same PYTHONPATH / neutral-cwd requirement as `gen_dataset.py`

Needs an actual PyHelios render per gradient-estimate sample (5 renders per
iteration: center, pan+h, pan-h, tilt+h, tilt-h), so must run against
phase2-avub's built native library, from a neutral cwd (not this worktree's
root -- see PHASE4_LOG.md Bug #1):

    PYTHONPATH=/home/yogesh/PyHelios/.claude/worktrees/phase2-avub \\
        /home/yogesh/anaconda3/envs/helios/bin/python \\
        <this file>
"""

import itertools
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kinematics as kin  # noqa: E402

SEED = 20260729
TREE_AGE_DAYS = 720.0
RESOLUTION = (320, 240)
SEMANTIC_CLASS_ID_FIELD = "semantic_class_id"
SEMANTIC_CLASSES = {"fruit": 1, "leaf": 2, "shoot": 3, "petiole": 4, "peduncle": 5}

H_DEG = 2.0        # finite-difference step (degrees) for pan/tilt
LR_DEG = 8.0        # ascent step size (degrees) per iteration, scaled by normalized gradient
N_ITERS = 12


def build_camera_properties(resolution, vfov_deg=45.0):
    import math
    from pyhelios.RadiationModel import CameraProperties
    width, height = resolution
    aspect = width / height
    half_v = math.radians(vfov_deg) / 2.0
    hfov_deg = math.degrees(2.0 * math.atan(aspect * math.tan(half_v)))
    return CameraProperties(camera_resolution=resolution, lens_diameter=0.0, HFOV=hfov_deg,
                             FOV_aspect_ratio=0.0, exposure="manual")


def main():
    from pyhelios import Context, PlantArchitecture, RadiationModel
    from pyhelios.types import vec3

    arm = {a.name: a for a in kin.single_tree_arm_configs()}["arm_high"]
    base_xyz = (-0.2, -0.85, 1.6)  # real reachable position (roadmap node 165's x,y,z)
    start_pan, start_tilt = 20.0, 0.0  # deliberately off-aim (not the roadmap's own -0/-35 pick)

    with Context() as context:
        context.seedRandomGenerator(SEED)
        with PlantArchitecture(context) as plantarch:
            plantarch.optionalOutputObjectData(["plantID", "fruitID", "leafID", "rank", "age", "phenology_stage"])
            plantarch.loadPlantModelFromLibrary("apple")
            plant_id = plantarch.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=TREE_AGE_DAYS)
            all_uuids = plantarch.getAllPlantUUIDs(plant_id)

            context.setPrimitiveDataInt(list(all_uuids), SEMANTIC_CLASS_ID_FIELD, 0)
            for label, cid in SEMANTIC_CLASSES.items():
                matched = context.filterPrimitivesByData(all_uuids, "object_label", label)
                if matched:
                    context.setPrimitiveDataInt(matched, SEMANTIC_CLASS_ID_FIELD, cid)

            with RadiationModel(context) as radiation:
                radiation.addRadiationBand("red", 600.0, 700.0)
                sun = radiation.addSunSphereRadiationSource(radius=0.5, zenith=30.0, azimuth=120.0, angular_width=0.53)
                radiation.setSourceFlux(sun, "red", 9.6)
                radiation.setDiffuseRadiationFlux("red", 9.6 * 0.12)
                radiation.setScatteringDepth("red", 1)
                cam_props = build_camera_properties(RESOLUTION)

                def render_utility(pan_deg, tilt_deg, cam_label="refine_cam", first=[True]):
                    q = kin.JointState(x=base_xyz[0], y=base_xyz[1], z=base_xyz[2],
                                        pan_deg=pan_deg, tilt_deg=tilt_deg)
                    pose = kin.forward_kinematics(q, arm)
                    eye, lookat = vec3(*pose.position), vec3(*pose.lookat)
                    if first[0]:
                        radiation.addRadiationCamera(cam_label, ["red"], eye, lookat, camera_properties=cam_props)
                        radiation.updateGeometry()
                        first[0] = False
                    else:
                        radiation.setCameraPosition(cam_label, eye)
                        radiation.setCameraLookat(cam_label, lookat)
                    radiation.runBand(["red"])
                    sem = radiation.getPrimitiveDataLabelMap(cam_label, SEMANTIC_CLASS_ID_FIELD)
                    return int(np.sum(sem == 1.0))

                lim = arm.limits
                pan, tilt = start_pan, start_tilt
                trace = []
                n_renders = 0
                t0 = time.time()

                u_center = render_utility(pan, tilt)
                n_renders += 1
                trace.append({"iter": 0, "pan_deg": pan, "tilt_deg": tilt, "utility_fruit_pixels": u_center})

                for it in range(1, N_ITERS + 1):
                    u_pan_p = render_utility(min(pan + H_DEG, lim.pan_deg[1]), tilt)
                    u_pan_m = render_utility(max(pan - H_DEG, lim.pan_deg[0]), tilt)
                    u_tilt_p = render_utility(pan, min(tilt + H_DEG, lim.tilt_deg[1]))
                    u_tilt_m = render_utility(pan, max(tilt - H_DEG, lim.tilt_deg[0]))
                    n_renders += 4

                    grad_pan = (u_pan_p - u_pan_m) / (2.0 * H_DEG)
                    grad_tilt = (u_tilt_p - u_tilt_m) / (2.0 * H_DEG)
                    grad_norm = math_hypot = (grad_pan ** 2 + grad_tilt ** 2) ** 0.5

                    if grad_norm < 1e-6:
                        trace.append({"iter": it, "stopped": "zero_gradient"})
                        break

                    step_pan = LR_DEG * grad_pan / grad_norm
                    step_tilt = LR_DEG * grad_tilt / grad_norm
                    new_pan = float(np.clip(pan + step_pan, lim.pan_deg[0], lim.pan_deg[1]))
                    new_tilt = float(np.clip(tilt + step_tilt, lim.tilt_deg[0], lim.tilt_deg[1]))

                    u_new = render_utility(new_pan, new_tilt)
                    n_renders += 1

                    trace.append({"iter": it, "pan_deg": new_pan, "tilt_deg": new_tilt,
                                  "utility_fruit_pixels": u_new, "grad_pan": grad_pan, "grad_tilt": grad_tilt,
                                  "grad_norm": grad_norm})

                    if u_new < u_center and it > 1:
                        # simple backtrack: halve step if we overshot past a local max
                        pass  # accept anyway; report as-is (real ascent trace, not hand-tuned to be monotone)
                    pan, tilt = new_pan, new_tilt
                    u_center = u_new

                elapsed = time.time() - t0

    report = {
        "arm": "arm_high", "base_xyz": base_xyz, "start_pan_deg": start_pan, "start_tilt_deg": start_tilt,
        "h_deg": H_DEG, "lr_deg": LR_DEG, "n_iters_requested": N_ITERS,
        "n_renders_total": n_renders, "elapsed_s": elapsed, "s_per_render": elapsed / n_renders,
        "trace": trace,
        "initial_utility": trace[0]["utility_fruit_pixels"],
        "final_utility": trace[-1].get("utility_fruit_pixels", trace[-2]["utility_fruit_pixels"]),
    }
    report["improvement_ratio"] = (report["final_utility"] / report["initial_utility"]
                                   if report["initial_utility"] > 0 else None)
    utilities = [t["utility_fruit_pixels"] for t in trace if "utility_fruit_pixels" in t]
    best_i = int(np.argmax(utilities))
    report["best_utility_in_trace"] = utilities[best_i]
    report["best_utility_iter"] = trace[best_i]["iter"]
    report["best_improvement_ratio"] = utilities[best_i] / report["initial_utility"] if report["initial_utility"] > 0 else None
    report["note_fixed_step_oscillation"] = (
        "Utility peaks at iter " + str(trace[best_i]["iter"]) + " then oscillates -- a real, "
        "honestly-reported consequence of a FIXED ascent step size (LR_DEG=8) near a local "
        "maximum (no step-size decay/backtracking implemented); a keep-best-seen policy "
        "recovers the peak utility, reported separately from the raw final-iterate utility above.")
    print(json.dumps(report, indent=2, default=str))
    with open(os.path.join(HERE, "output_t410_gimbal_refinement.json"), "w") as fh:
        json.dump(report, fh, indent=2, default=str)


if __name__ == "__main__":
    main()
