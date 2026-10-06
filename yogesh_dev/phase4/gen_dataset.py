"""
Phase 4 real-data generator.

WHY THIS SCRIPT IS SPECIAL (read before touching): this worktree
(`worktree-phase4-map-planner`) has no built native `libhelios.so` of its
own -- each phase's worktree only gets one if that phase's session actually
ran a build, and Phase 4's task brief says to work Python-only against
already-exported data. `worktree-phase2-avub` DOES have a working native
build (confirmed empirically). This script is a standalone entry point (not
part of the normal `yogesh_dev.phase4` package import graph -- it does not
`import yogesh_dev.phase4.anything`) that is meant to be invoked with that
worktree's repo root prepended to PYTHONPATH so `import pyhelios` resolves
to ITS built library, while this file itself, and everything it writes,
lives entirely under THIS worktree's `yogesh_dev/phase4/`:

    PYTHONPATH=/home/yogesh/PyHelios/.claude/worktrees/phase2-avub \\
        /home/yogesh/anaconda3/envs/helios/bin/python \\
        /home/yogesh/PyHelios/.claude/worktrees/phase4-map-planner/yogesh_dev/phase4/gen_dataset.py

Nothing in `worktree-phase2-avub` is read for its Python *source* (that
worktree's `pyhelios/` package is git-identical to this one's -- both are
`apple-tree-cameras` plus each phase's own untouched `yogesh_dev/`); only its
compiled `.so` is dynamically linked at import time. Nothing there is
written to.

WHAT THIS BUILDS (T4's own seeded, reproducible dataset -- see
PHASE4_LOG.md "Note found by Phase 2" about upstream `PlantArchitecture`
growth being stochastic and unseeded): ONE apple tree at the origin,
`context.seedRandomGenerator(SEED)` called before any build call (real API,
confirmed present in `Context.py`), plus the real per-view rendered dataset
(depth EXR, semantic + instance label maps, real branch/twig tube geometry,
real fruit ground truth) that every other `phase4/*.py` module consumes.

Camera rig: reuses Phase 3's single-tree-scaled 5-DOF arm chain
(`kinematics.single_tree_arm_configs`) and Phase 3's placeholder-collision
roadmap builder (`roadmap.build_roadmap`) to generate a REAL, kinematically
grounded candidate pose set per arm (3 arms, non-overlapping z bands), then
renders a stride-sampled subset of each arm's reachable nodes through
PyHelios's RadiationModel (same T0.1-T0.4 recipe as Phase 0/1) to produce
real depth + semantic + instance data at those exact poses.
"""

import itertools
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # so `import kinematics` / `roadmap` / `motion_time` work stand-alone

from kinematics import single_tree_arm_configs, forward_kinematics  # noqa: E402
from roadmap import canopy_box_from_fruit_records, build_roadmap  # noqa: E402

OUTPUT_DIR = os.path.join(HERE, "data")
DEPTH_DIR = os.path.join(OUTPUT_DIR, "depth")
LABELS_DIR = os.path.join(OUTPUT_DIR, "labels")

SEED = 20260729  # today's date at authoring time -- arbitrary but fixed & documented
TREE_AGE_DAYS = 720.0
RESOLUTION = (320, 240)
ANTIALIASING_SAMPLES = 2
RGB_BANDS = {"red": (600.0, 700.0), "green": (500.0, 600.0), "blue": (400.0, 500.0)}
BAND_FLUX = {"red": 9.6, "green": 10.4, "blue": 7.6}  # T0.1 "plausible RGB" values, reused verbatim
DIFFUSE_FRACTION = 0.12
SCATTERING_DEPTH = 1

SEMANTIC_CLASSES = {"fruit": 1, "leaf": 2, "shoot": 3, "petiole": 4, "peduncle": 5}
SEMANTIC_CLASS_ID_FIELD = "semantic_class_id"
VIS_PRIMITIVE_ID_FIELD = "vis_primitive_id"
NO_FRUIT_PRIMITIVE_ID = -1

N_LINEAR = 4       # per-arm joint-space grid resolution (T3.4 style)
N_GIMBAL = 3
K_NN = 6
N_RENDER_PER_ARM = 14  # stride-sampled render subset per arm (keeps this script's wall clock small)


def build_camera_properties(resolution, vfov_deg=45.0):
    import math
    from pyhelios.RadiationModel import CameraProperties
    width, height = resolution
    aspect = width / height
    half_v = math.radians(vfov_deg) / 2.0
    hfov_deg = math.degrees(2.0 * math.atan(aspect * math.tan(half_v)))
    props = CameraProperties(camera_resolution=resolution, lens_diameter=0.0, HFOV=hfov_deg,
                              FOV_aspect_ratio=0.0, exposure="manual")
    return props, hfov_deg


def extract_branch_segments(context, all_uuids):
    """Real per-segment tube geometry (node positions + radii) for every
    shoot/petiole/peduncle compound object -- the real ground truth T4.2
    measures voxel-resolution recall against. `getTubeObjectNodeRadii` /
    `getTubeObjectNodes` are real Context API calls (confirmed present in
    Context.py); not every compound object those primitive labels ever
    appear on need be Tube-typed (verified empirically per label, reported
    below rather than assumed).

    IMPORTANT (confirmed by crash + isolation, see PHASE4_LOG.md): calling
    the tube-node accessors on a non-Tube object does not raise a catchable
    Python/C++ exception -- it SEGFAULTS the native library (hard process
    crash, not a Python exception `except Exception` can catch). Empirically,
    apple `petiole` objects are `helios::ObjectType` code 6 (cone), not 2
    (tube); `shoot` and `peduncle` objects ARE tube-typed. We therefore MUST
    check `context.getObjectType(oid) == 2` before calling any tube accessor,
    rather than relying on try/except."""
    OBJECT_TYPE_TUBE = 2
    segments = []
    per_label_object_type_counts = {}
    for label in ("shoot", "petiole", "peduncle"):
        uuids = context.filterPrimitivesByData(all_uuids, "object_label", label)
        obj_ids = context.getUniquePrimitiveParentObjectIDs(uuids, include_zero=False)
        n_tube = 0
        n_other = 0
        for oid in obj_ids:
            if context.getObjectType(oid) != OBJECT_TYPE_TUBE:
                n_other += 1
                continue
            nodes = context.getTubeObjectNodes(oid)
            radii = context.getTubeObjectNodeRadii(oid)
            n_tube += 1
            for i in range(len(nodes) - 1):
                p0 = (nodes[i].x, nodes[i].y, nodes[i].z)
                p1 = (nodes[i + 1].x, nodes[i + 1].y, nodes[i + 1].z)
                r0, r1 = float(radii[i]), float(radii[i + 1])
                segments.append({
                    "object_id": oid, "label": label,
                    "p0": p0, "p1": p1, "r0_m": r0, "r1_m": r1,
                    "mid_diameter_mm": (r0 + r1) * 1000.0,
                })
        per_label_object_type_counts[label] = {"n_objects": len(obj_ids), "n_tube": n_tube, "n_other": n_other}
    return segments, per_label_object_type_counts


def export_fruit_ground_truth(context, plantarch, plant_id):
    import math
    uuids = plantarch.getAllPlantUUIDs(plant_id)
    uuid_set = set(uuids)
    fruit_uuids = context.filterPrimitivesByData(uuids, "object_label", "fruit")
    fruit_uuid_set = set(fruit_uuids)
    fruit_objs = context.getUniquePrimitiveParentObjectIDs(fruit_uuids, include_zero=False)

    records = []
    for oid in fruit_objs:
        obj_uuids = context.getObjectPrimitiveUUIDs(oid)
        obj_fruit_uuids = [u for u in obj_uuids if u in fruit_uuid_set]
        if not obj_fruit_uuids:
            continue
        center = context.getObjectCenter(oid)
        bbox_min, bbox_max = context.getObjectBoundingBox(oid)
        surface_area = sum(context.getPrimitiveArea(u) for u in obj_fruit_uuids)
        diameter = math.sqrt(surface_area / math.pi) if surface_area > 0 else 0.0
        record = {
            "object_id": oid, "plant_id": plant_id,
            "centroid": [center.x, center.y, center.z],
            "bbox_min": [bbox_min.x, bbox_min.y, bbox_min.z],
            "bbox_max": [bbox_max.x, bbox_max.y, bbox_max.z],
            "equivalent_diameter_m": diameter,
            "surface_area_m2": surface_area,
            "primitive_uuids": [int(u) for u in obj_fruit_uuids],
        }
        for field in ("fruitID", "rank", "age", "phenology_stage"):
            if context.doesObjectDataExist(oid, field):
                record[field] = context.getObjectData(oid, field)
        records.append(record)
    return records


def main():
    os.makedirs(DEPTH_DIR, exist_ok=True)
    os.makedirs(LABELS_DIR, exist_ok=True)
    report = {"seed": SEED, "tree_age_days": TREE_AGE_DAYS, "resolution": list(RESOLUTION)}

    from pyhelios import Context, PlantArchitecture, RadiationModel
    from pyhelios.types import vec3

    with Context() as context:
        context.seedRandomGenerator(SEED)  # BEFORE any build call -- see module docstring
        with PlantArchitecture(context) as plantarch:
            plantarch.optionalOutputObjectData(["plantID", "fruitID", "leafID", "rank", "age", "phenology_stage"])
            plantarch.loadPlantModelFromLibrary("apple")

            t0 = time.time()
            plant_id = plantarch.buildPlantInstanceFromLibrary(base_position=vec3(0, 0, 0), age=TREE_AGE_DAYS)
            build_time = time.time() - t0
            all_uuids = plantarch.getAllPlantUUIDs(plant_id)
            report["build_time_s"] = build_time
            report["n_primitives"] = len(all_uuids)
            print(f"Built 1 seeded apple tree (seed={SEED}) in {build_time:.2f}s, {len(all_uuids)} primitives")

            # --- semantic_class_id (T1.3 pattern) ---
            context.setPrimitiveDataInt(list(all_uuids), SEMANTIC_CLASS_ID_FIELD, 0)
            class_counts = {}
            for label, cid in SEMANTIC_CLASSES.items():
                matched = context.filterPrimitivesByData(all_uuids, "object_label", label)
                if matched:
                    context.setPrimitiveDataInt(matched, SEMANTIC_CLASS_ID_FIELD, cid)
                class_counts[label] = len(matched)
            report["semantic_class_counts"] = class_counts
            print(f"Semantic class counts: {class_counts}")

            # --- fruit ground truth ---
            fruit_records = export_fruit_ground_truth(context, plantarch, plant_id)
            with open(os.path.join(OUTPUT_DIR, "fruit_ground_truth.json"), "w") as f:
                json.dump(fruit_records, f, indent=2)
            report["n_fruit"] = len(fruit_records)
            print(f"Fruit ground truth: {len(fruit_records)} fruit objects")

            # --- vis_primitive_id (T2.1 pattern): globally unique id per fruit-surface primitive ---
            context.setPrimitiveDataInt(list(all_uuids), VIS_PRIMITIVE_ID_FIELD, NO_FRUIT_PRIMITIVE_ID)
            prim_id_to_info = {}
            fruit_prim_ids = {}
            next_id = 0
            for rec in fruit_records:
                oid = rec["object_id"]
                ids_here = []
                for u in rec["primitive_uuids"]:
                    area = context.getPrimitiveArea(u)
                    context.setPrimitiveDataInt(u, VIS_PRIMITIVE_ID_FIELD, next_id)
                    prim_id_to_info[next_id] = {"uuid": int(u), "object_id": oid, "area": float(area)}
                    ids_here.append(next_id)
                    next_id += 1
                fruit_prim_ids[oid] = ids_here
            with open(os.path.join(OUTPUT_DIR, "vis_primitive_index.json"), "w") as f:
                json.dump({"prim_id_to_info": prim_id_to_info, "fruit_prim_ids": fruit_prim_ids}, f, indent=2)

            # --- T4.2 branch/twig ground truth geometry ---
            t0 = time.time()
            segments, tube_type_report = extract_branch_segments(context, all_uuids)
            with open(os.path.join(OUTPUT_DIR, "branch_segments_gt.json"), "w") as f:
                json.dump(segments, f)
            report["branch_segment_extraction_s"] = time.time() - t0
            report["n_branch_segments"] = len(segments)
            report["tube_type_report"] = tube_type_report
            print(f"Branch/twig segments: {len(segments)} real tube segments, "
                  f"tube-type coverage: {tube_type_report}")

            # --- roadmap: single-tree-scaled 3-arm chain, real placeholder-collision roadmap ---
            arms = single_tree_arm_configs()
            canopy_box = canopy_box_from_fruit_records(fruit_records)
            roadmap_report = {}
            render_poses = []  # (arm_name, node_id, joint, eye, lookat)
            for arm in arms:
                t0 = time.time()
                nodes, adjacency, n_rejected = build_roadmap(arm, canopy_box, n_linear=N_LINEAR,
                                                              n_gimbal=N_GIMBAL, k=K_NN)
                rt = time.time() - t0
                n_edges = sum(len(v) for v in adjacency.values())
                roadmap_report[arm.name] = {
                    "grid_samples": n_rejected + len(nodes), "rejected": n_rejected,
                    "reachable_nodes": len(nodes), "edges": n_edges, "build_time_s": rt,
                }
                print(f"[{arm.name}] roadmap: {len(nodes)}/{n_rejected + len(nodes)} reachable, "
                      f"{n_edges} edges, built in {rt:.3f}s")

                stride = max(1, len(nodes) // N_RENDER_PER_ARM)
                chosen = nodes[::stride][:N_RENDER_PER_ARM]
                for node in chosen:
                    eye = vec3(*node.position)
                    lookat = vec3(*node.lookat)
                    render_poses.append((arm.name, node.node_id, node.joint, eye, lookat))

                # persist full node/edge set for the planners (T4.6/T4.8/T4.9) --
                # candidate pool graph search does NOT require these to have
                # been rendered.
                np.save(os.path.join(OUTPUT_DIR, f"roadmap_{arm.name}_nodes.npy"),
                        np.array([n.joint.as_tuple() for n in nodes]))
                with open(os.path.join(OUTPUT_DIR, f"roadmap_{arm.name}_adjacency.json"), "w") as f:
                    json.dump({str(k): v for k, v in adjacency.items()}, f)
            report["roadmap"] = roadmap_report
            report["n_render_poses"] = len(render_poses)
            print(f"Total render poses (stride-sampled across 3 arms): {len(render_poses)}")

            # --- radiation setup (T0.1) + camera rig (T0.2), 3 reusable camera slots per arm ---
            with RadiationModel(context) as radiation:
                for band, (lo, hi) in RGB_BANDS.items():
                    radiation.addRadiationBand(band, lo, hi)
                sun = radiation.addSunSphereRadiationSource(radius=0.5, zenith=30.0, azimuth=120.0, angular_width=0.53)
                for band in RGB_BANDS:
                    radiation.setSourceFlux(sun, band, BAND_FLUX[band])
                    radiation.setDiffuseRadiationFlux(band, BAND_FLUX[band] * DIFFUSE_FRACTION)
                    radiation.setScatteringDepth(band, SCATTERING_DEPTH)

                cam_props, hfov_deg = build_camera_properties(RESOLUTION)
                cam_labels = [f"cam{i}" for i in range(len(arms))]
                for label, (_, _, _, eye, lookat) in zip(cam_labels, render_poses[:len(arms)]):
                    radiation.addRadiationCamera(label, ["red", "green", "blue"], eye, lookat,
                                                  camera_properties=cam_props,
                                                  antialiasing_samples=ANTIALIASING_SAMPLES)
                radiation.updateGeometry()  # ONCE (T0.4)

                frames = []
                t_render0 = time.time()
                for start in range(0, len(render_poses), len(cam_labels)):
                    batch = render_poses[start:start + len(cam_labels)]
                    cams_used = cam_labels[:len(batch)]
                    for cam, (arm_name, node_id, joint, eye, lookat) in zip(cams_used, batch):
                        radiation.setCameraPosition(cam, eye)
                        radiation.setCameraLookat(cam, lookat)
                    radiation.runBand(["red", "green", "blue"])  # ONE call, all bands (T0.4)

                    for cam, (arm_name, node_id, joint, eye, lookat) in zip(cams_used, batch):
                        view_name = f"{arm_name}_{node_id}"
                        semantic = radiation.getPrimitiveDataLabelMap(cam, SEMANTIC_CLASS_ID_FIELD)
                        instance = radiation.getObjectDataLabelMap(cam, "fruitID")
                        vis_ids = radiation.getPrimitiveDataLabelMap(cam, VIS_PRIMITIVE_ID_FIELD)
                        np.save(os.path.join(LABELS_DIR, f"{view_name}_semantic.npy"), semantic)
                        np.save(os.path.join(LABELS_DIR, f"{view_name}_instance.npy"), instance)
                        np.save(os.path.join(LABELS_DIR, f"{view_name}_visid.npy"), vis_ids)
                        radiation.writeDepthImageDataEXR(cam, view_name, image_path=DEPTH_DIR + os.sep)

                        frames.append({
                            "view": view_name, "arm": arm_name, "node_id": node_id,
                            "joint": list(joint.as_tuple()),
                            "eye": [eye.x, eye.y, eye.z], "lookat": [lookat.x, lookat.y, lookat.z],
                            "camera_label": cam,
                            "depth_path": os.path.relpath(os.path.join(DEPTH_DIR, f"{cam}_{view_name}.exr"), OUTPUT_DIR),
                            "semantic_path": os.path.relpath(os.path.join(LABELS_DIR, f"{view_name}_semantic.npy"), OUTPUT_DIR),
                            "instance_path": os.path.relpath(os.path.join(LABELS_DIR, f"{view_name}_instance.npy"), OUTPUT_DIR),
                            "visid_path": os.path.relpath(os.path.join(LABELS_DIR, f"{view_name}_visid.npy"), OUTPUT_DIR),
                        })
                render_time = time.time() - t_render0
                report["render_total_s"] = render_time
                report["render_per_view_s"] = render_time / max(1, len(frames))
                report["hfov_deg"] = hfov_deg
                report["fl_x"] = 0.5 * RESOLUTION[0] / np.tan(np.radians(hfov_deg) / 2.0)
                print(f"Rendered {len(frames)} views in {render_time:.2f}s "
                      f"({render_time / max(1, len(frames)):.3f}s/view)")

    with open(os.path.join(OUTPUT_DIR, "poses.json"), "w") as f:
        json.dump(frames, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, "gen_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
