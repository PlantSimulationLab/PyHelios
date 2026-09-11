"""
T6.4 -- occlusion-conditioned detection recall, stratified by GT occlusion
decile.
T6.5 -- semantically stratified F-score at class-specific tau.
T6.6 -- three-state occupancy confusion matrix + M(free|occ) safety metric.

All three run against Phase 4's real single-tree dataset
(`yogesh_dev/phase4/data/`: 27 fruit, 42 real rendered views across 3 arms,
real depth/semantic/instance/vis-primitive-id label maps, exactly known
poses via `poses.json` -- no ICP/registration needed anywhere here).
"""

import math
import os

import numpy as np
import OpenEXR

from yogesh_dev.phase2.visibility import fruit_visible_fraction
from yogesh_dev.phase6.common import (
    PHASE4_DATA, PHASE6_OUTPUT, ensure_phase4_importable, load_json,
)

ensure_phase4_importable()

import sensor_model as sm  # noqa: E402  (flat Phase 4 module, see common.py)
import tracker as trk  # noqa: E402
from occupancy_map import build_dual_resolution_map  # noqa: E402

SEMANTIC_FRUIT, SEMANTIC_LEAF, SEMANTIC_SHOOT = 1, 2, 3
ARMS = ("arm_low", "arm_mid", "arm_high")


def _read_depth(path):
    fh = OpenEXR.File(path)
    ch = fh.channels()
    key = "Z" if "Z" in ch else next(iter(ch.keys()))
    return np.array(ch[key].pixels, dtype=np.float32)


# ---------------------------------------------------------------------------
# T6.4 -- occlusion-conditioned detection recall by GT occlusion decile
# ---------------------------------------------------------------------------

def compute_fruit_occlusion(poses, vis_idx, fruit_records):
    """Real per-fruit occlusion measure: 1 - (area-weighted fraction of the
    fruit's surface EVER visible across all 42 real rendered views, any
    arm) -- i.e. the AVUB-style union-visibility fraction restricted to the
    actual captured dataset (Phase 2's own `fruit_visible_fraction`, reused
    verbatim), not re-derived on a different scene."""
    prim_id_to_info = {int(k): v for k, v in vis_idx["prim_id_to_info"].items()}
    fruit_prim_ids = {int(k): set(v) for k, v in vis_idx["fruit_prim_ids"].items()}

    union_visible = set()
    for p in poses:
        vis = np.load(os.path.join(PHASE4_DATA, p["visid_path"]))
        valid = ~np.isnan(vis)
        union_visible |= set(int(v) for v in np.unique(vis[valid]) if v >= 0)

    occlusion = {}
    vis_frac = {}
    for rec in fruit_records:
        oid = rec["object_id"]
        frac, _area = fruit_visible_fraction(union_visible, fruit_prim_ids, prim_id_to_info,
                                              oid, rec["surface_area_m2"])
        vis_frac[oid] = frac
        occlusion[oid] = 1.0 - frac
    return occlusion, vis_frac


def detected_fruit_ids(poses, intr):
    """Union, over all 3 arms, of every true fruit id that was EVER a real
    detection (>=5 valid pixels at >=1 frame, per Phase 4's own
    `tracker.extract_detections` -- reused verbatim, not reimplemented)."""
    detected = set()
    per_arm_n_detections = {}
    for arm_name in ARMS:
        frames = trk.extract_detections(PHASE4_DATA, arm_name, poses, intr)
        n = 0
        for fr in frames:
            for det in fr["detections"]:
                detected.add(det["true_id"])
                n += 1
        per_arm_n_detections[arm_name] = n
    return detected, per_arm_n_detections


def run_t64(poses, vis_idx, fruit_records, intr, n_deciles=10):
    occlusion, vis_frac = compute_fruit_occlusion(poses, vis_idx, fruit_records)
    detected, per_arm_n_detections = detected_fruit_ids(poses, intr)

    oids = [rec["object_id"] for rec in fruit_records]
    occl_vals = np.array([occlusion[o] for o in oids])
    order = np.argsort(occl_vals)  # ascending occlusion (least occluded first)
    n = len(oids)
    decile_edges = np.linspace(0, n, n_deciles + 1).round().astype(int)

    deciles = []
    for d in range(n_deciles):
        idx_in_decile = order[decile_edges[d]:decile_edges[d + 1]]
        if len(idx_in_decile) == 0:
            continue
        decile_oids = [oids[i] for i in idx_in_decile]
        recalls = [1.0 if o in detected else 0.0 for o in decile_oids]
        deciles.append({
            "decile": d,
            "n_fruit": len(decile_oids),
            "mean_occlusion": float(np.mean([occlusion[o] for o in decile_oids])),
            "mean_vis_frac": float(np.mean([vis_frac[o] for o in decile_oids])),
            "detection_recall": float(np.mean(recalls)),
        })

    return {
        "n_fruit_total": n,
        "n_fruit_ever_detected": len(detected),
        "overall_detection_recall": len(detected) / n if n else None,
        "per_arm_n_detections": per_arm_n_detections,
        "deciles": deciles,
        "note": ("Occlusion measure = 1 - (union-visible-fraction across all 42 real "
                 "rendered views), Phase 2's own fruit_visible_fraction reused on this "
                 "dataset's real vis_primitive_id maps. 'Detected' = appeared as a real "
                 ">=5px instance-map detection (Phase 4 T4.4's own extract_detections) "
                 "in >=1 of the 42 views, any arm. With only 27 fruit, each decile bucket "
                 "holds ~2-3 fruit -- real numbers, small-N caveat noted rather than "
                 "hidden."),
    }


# ---------------------------------------------------------------------------
# T6.5 -- semantically stratified F-score at class-specific tau
# ---------------------------------------------------------------------------

CLASS_TAU_M = {"fruit": 0.005, "branch": 0.010, "leaf": 0.010}  # wire: N/A, see note
PIXEL_STRIDE_GT = 4
DEDUPE_CELL_M = 0.002


def _dedupe_points(points, cell_m=DEDUPE_CELL_M):
    if len(points) == 0:
        return points
    keys = np.floor(points / cell_m).astype(np.int64)
    _, idx = np.unique(keys, axis=0, return_index=True)
    return points[idx]


def collect_gt_points_by_class(poses, resolution, pixel_stride=PIXEL_STRIDE_GT):
    """Real per-class 3D ground-truth points via multi-view unprojection of
    EXACT (noiseless) depth at exactly-known poses, keyed by the real
    per-pixel semantic label -- no ICP/registration needed since poses are
    exact. Subsampled (pixel_stride) and voxel-deduped for tractability;
    documented, not hidden."""
    intr = sm.intrinsics(resolution)
    class_ids = {"fruit": SEMANTIC_FRUIT, "leaf": SEMANTIC_LEAF, "branch": SEMANTIC_SHOOT}
    pts_by_class = {name: [] for name in class_ids}

    for p in poses:
        depth = _read_depth(os.path.join(PHASE4_DATA, p["depth_path"]))
        semantic = np.load(os.path.join(PHASE4_DATA, p["semantic_path"]))
        eye, lookat = p["eye"], p["lookat"]
        f, r, u = sm.camera_basis(eye, lookat)
        H, W = depth.shape
        rr, cc = np.meshgrid(np.arange(0, H, pixel_stride), np.arange(0, W, pixel_stride), indexing="ij")
        rr, cc = rr.reshape(-1), cc.reshape(-1)
        d = depth[rr, cc]
        sem = semantic[rr, cc]
        valid = (d != sm.SKY_DEPTH_SENTINEL) & ~np.isnan(sem)
        rr, cc, d, sem = rr[valid], cc[valid], d[valid], sem[valid]
        if len(d) == 0:
            continue
        for name, cid in class_ids.items():
            m = np.round(sem) == cid
            if not np.any(m):
                continue
            pts = sm.unproject(rr[m], cc[m], d[m], eye, f, r, u, intr)
            pts_by_class[name].append(pts)

    out = {}
    for name, chunks in pts_by_class.items():
        pts = np.concatenate(chunks, axis=0) if chunks else np.zeros((0, 3))
        out[name] = _dedupe_points(pts)
    return out


def _hash_buckets(points, cell_size):
    keys = np.floor(points / cell_size).astype(np.int64)
    buckets = {}
    for i, k in enumerate(map(tuple, keys)):
        buckets.setdefault(k, []).append(i)
    return buckets, keys


def any_within_tau(query_points, ref_points, tau):
    """For each query point, is there ANY ref point within `tau`? O(N)
    average via a spatial hash at cell size `tau` (so the true nearest
    neighbor, if within tau, always lives in one of the 27 neighboring
    cells)."""
    if len(ref_points) == 0 or len(query_points) == 0:
        return np.zeros(len(query_points), dtype=bool)
    buckets, _ref_keys = _hash_buckets(ref_points, tau)
    qkeys = np.floor(query_points / tau).astype(np.int64)
    out = np.zeros(len(query_points), dtype=bool)
    offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)]
    for i in range(len(query_points)):
        qk = qkeys[i]
        qp = query_points[i]
        found = False
        for dx, dy, dz in offsets:
            key = (int(qk[0]) + dx, int(qk[1]) + dy, int(qk[2]) + dz)
            for j in buckets.get(key, ()):
                if np.linalg.norm(qp - ref_points[j]) <= tau:
                    found = True
                    break
            if found:
                break
        out[i] = found
    return out


def f_score_at_tau(candidate_points, gt_points, tau):
    if len(candidate_points) == 0 or len(gt_points) == 0:
        return {"precision": 0.0, "recall": 0.0, "f_score": 0.0,
                "n_candidate": len(candidate_points), "n_gt": len(gt_points)}
    precision = float(np.mean(any_within_tau(candidate_points, gt_points, tau)))
    recall = float(np.mean(any_within_tau(gt_points, candidate_points, tau)))
    f = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f_score": f,
            "n_candidate": len(candidate_points), "n_gt": len(gt_points), "tau_m": tau}


def voxel_centers(grid, state_value):
    state = grid.state_grid()
    idx = np.argwhere(state == state_value)
    if len(idx) == 0:
        return np.zeros((0, 3))
    return grid.bmin[None, :] + (idx + 0.5) * grid.voxel_size


def run_t65(poses, resolution, coarse_grid, fine_grids):
    gt_points = collect_gt_points_by_class(poses, resolution)

    coarse_occupied = voxel_centers(coarse_grid, 2)
    fine_occupied = (np.concatenate([voxel_centers(g, 2) for g, _b0, _b1 in fine_grids], axis=0)
                      if fine_grids else np.zeros((0, 3)))

    results = {}
    # Fruit scored against the FINE (attention-region, ~3mm) grid -- the
    # only grid resolution finer than fruit's own 5mm tau; the coarse grid
    # (2cm) can't meaningfully resolve a 5mm threshold at all.
    results["fruit"] = f_score_at_tau(fine_occupied, gt_points["fruit"], CLASS_TAU_M["fruit"])
    results["fruit"]["candidate_grid"] = "fine (attention-region, ~3mm voxels)"
    # Branch/leaf scored against the COARSE (whole-scene, ~2cm) grid --
    # there's no fine grid over branch/leaf regions (fine grids are fruit-
    # cluster-only by construction, see occupancy_map.py's attention_regions).
    results["branch"] = f_score_at_tau(coarse_occupied, gt_points["branch"], CLASS_TAU_M["branch"])
    results["branch"]["candidate_grid"] = "coarse (whole-scene, ~2cm voxels)"
    results["leaf"] = f_score_at_tau(coarse_occupied, gt_points["leaf"], CLASS_TAU_M["leaf"])
    results["leaf"]["candidate_grid"] = "coarse (whole-scene, ~2cm voxels)"
    results["wire"] = {
        "note": ("No wire/trellis geometry exists in this repo's scene at all -- "
                 "single freestanding apple tree, no fruiting-wall/trellis (that's "
                 "Phase 8 scope, T8.3). 0 GT wire elements; tau=5mm not applicable. "
                 "Same 'real, not fabricated' policy as T2.6's missing-module finding."),
        "n_gt": 0,
    }
    return results


# ---------------------------------------------------------------------------
# T6.6 -- three-state occupancy confusion matrix + M(free|occ)
# ---------------------------------------------------------------------------

def gt_occupied_mask_for_grid(grid, fruit_records, branch_segments, branch_label="shoot", n_samples_per_segment=6):
    """Real geometric GT-occupied test for each voxel CENTER of `grid`:
    within a fruit's real equivalent radius of a real fruit centroid, OR
    within a real branch tube segment's real radius (sampled at
    `n_samples_per_segment` points along p0->p1, per `branch_segments_gt.json`,
    itself extracted from the real mesh in Phase 4's gen_dataset.py)."""
    idx = np.indices(grid.dims).reshape(3, -1).T
    centers = grid.bmin[None, :] + (idx + 0.5) * grid.voxel_size
    occupied = np.zeros(len(centers), dtype=bool)

    for rec in fruit_records:
        c = np.array(rec["centroid"])
        r = rec["equivalent_diameter_m"] / 2.0
        d = np.linalg.norm(centers - c[None, :], axis=1)
        occupied |= d <= r

    for seg in branch_segments:
        if seg["label"] != branch_label:
            continue
        p0, p1 = np.array(seg["p0"]), np.array(seg["p1"])
        for t in np.linspace(0.0, 1.0, n_samples_per_segment):
            c = p0 + t * (p1 - p0)
            r = seg["r0_m"] + t * (seg["r1_m"] - seg["r0_m"])
            d = np.linalg.norm(centers - c[None, :], axis=1)
            occupied |= d <= max(r, grid.voxel_size * 0.5)

    return occupied.reshape(grid.dims)


def run_t66(coarse_grid, fruit_records, branch_segments):
    pred_state = coarse_grid.state_grid()  # 0=unknown,1=free,2=occupied
    gt_occ = gt_occupied_mask_for_grid(coarse_grid, fruit_records, branch_segments, branch_label="shoot")
    gt_occ_branch_only = gt_occupied_mask_for_grid(coarse_grid, [], branch_segments, branch_label="shoot")

    confusion = {}
    for pred_name, pred_val in (("unknown", 0), ("free", 1), ("occupied", 2)):
        pred_mask = pred_state == pred_val
        confusion[pred_name] = {
            "gt_occupied": int(np.sum(pred_mask & gt_occ)),
            "gt_free": int(np.sum(pred_mask & ~gt_occ)),
        }

    n_gt_occ_branch = int(gt_occ_branch_only.sum())
    n_pred_free_given_gt_occ_branch = int(np.sum((pred_state == 1) & gt_occ_branch_only))
    m_free_given_occ_branch = (n_pred_free_given_gt_occ_branch / n_gt_occ_branch) if n_gt_occ_branch else None

    n_gt_occ_all = int(gt_occ.sum())
    n_pred_free_given_gt_occ_all = int(np.sum((pred_state == 1) & gt_occ))
    m_free_given_occ_all = (n_pred_free_given_gt_occ_all / n_gt_occ_all) if n_gt_occ_all else None

    return {
        "grid_dims": list(coarse_grid.dims), "voxel_size_m": coarse_grid.voxel_size,
        "confusion_matrix_pred_x_gt": confusion,
        "n_gt_occupied_voxels_branch_only": n_gt_occ_branch,
        "n_gt_occupied_voxels_all_classes": n_gt_occ_all,
        "M_free_given_occ__branch_only__safety_critical": m_free_given_occ_branch,
        "M_free_given_occ__all_classes__for_reference": m_free_given_occ_all,
        "note": ("GT occupancy is a real-geometry proxy: fruit = sphere of real "
                 "equivalent_diameter_m around real centroid; branch = real tube "
                 "segments from branch_segments_gt.json (label=='shoot'; leaf has no "
                 "tube/sphere geometric proxy available and is excluded from GT-occupied "
                 "here, so 'gt_free' includes true leaf-occupied space -- a known "
                 "under-count of GT occupancy, documented rather than hidden). No wire "
                 "class exists in this scene (see T6.5 note)."),
    }


def run_all():
    os.makedirs(PHASE6_OUTPUT, exist_ok=True)
    poses = load_json(os.path.join(PHASE4_DATA, "poses.json"))
    fruit_records = load_json(os.path.join(PHASE4_DATA, "fruit_ground_truth.json"))
    vis_idx = load_json(os.path.join(PHASE4_DATA, "vis_primitive_index.json"))
    branch_segments = load_json(os.path.join(PHASE4_DATA, "branch_segments_gt.json"))
    report = load_json(os.path.join(PHASE4_DATA, "gen_report.json"))
    resolution = tuple(report["resolution"])
    intr = sm.intrinsics(resolution)

    t64 = run_t64(poses, vis_idx, fruit_records, intr)

    coarse_grid, fine_grids, occ_build_report = build_dual_resolution_map(PHASE4_DATA, pixel_stride=2)
    t65 = run_t65(poses, resolution, coarse_grid, fine_grids)
    t66 = run_t66(coarse_grid, fruit_records, branch_segments)

    return {"T6.4": t64, "T6.5": t65, "T6.6": t66, "occupancy_build_report": occ_build_report}


if __name__ == "__main__":
    import json
    report = run_all()
    with open(os.path.join(PHASE6_OUTPUT, "t64_t65_t66_report.json"), "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))
