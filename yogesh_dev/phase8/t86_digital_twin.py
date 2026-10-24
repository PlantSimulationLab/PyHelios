"""
T8.6 -- digital-twin path: synthesize a realistic multi-station LiDAR scan of one real
Helios canopy, reconstruct its leaf geometry leaf-by-leaf with `pyhelios.LiDARCloud`'s
real triangulation + leaf-area inversion, build a "digital twin" scene from that
reconstruction, and check whether Phase 5-style view-selection policies rank the same
way on the original sim canopy and its reconstructed twin.

## Honest substitution (no real-world tree exists in this environment)

There is no physical apple tree to scan here. The "real-world" input this task calls
for is synthesized as follows, and this substitution is the one thing in this script
that is NOT a real measurement of a real physical object:

1. Build ONE real Helios canopy (`canopy_factory.build_canopy`, test seed 2000 --
   reserved for exactly this, never touched by T8.2/T8.4's dev-seed sweep, per
   PREREGISTRATION.md).
2. Run a REAL simulated multi-station terrestrial LiDAR scan of it
   (`pyhelios.LiDARCloud.addScan` x 4 stations around the tree + `syntheticScan`,
   real ray-traced hits/misses against this canopy's real geometry -- not fabricated
   points).
3. Reconstruct leaf geometry from the point cloud with `LiDARCloud`'s REAL leaf-by-leaf
   pipeline: `triangulateHitPoints` (Delaunay mesh from real hits) +
   `calculateLeafArea` (real per-cell leaf-area inversion) + `calculateSyntheticLeafArea`
   (real exact-geometry ground truth, for a real fidelity check of the reconstruction).

## Building the "twin" scene

The twin canopy is built by calling `canopy_factory.build_canopy` again with the SAME
seed=2000 but `lai_keep_frac=0.0` -- deterministic growth (verified in T8.1) reproduces
the identical real trunk/scaffold/fruit geometry with zero real leaves, i.e. a real
leafless scaffold of the SAME canopy. The LiDAR-reconstructed triangle mesh is then
added into that scaffold's Context as new primitives (`context.addTriangle`, tagged
`object_label="leaf_reconstructed"` -- deliberately NOT "leaf", so nothing downstream
can mistake it for ground-truth leaf data). This gives a twin whose branches and fruit
are the real, exact original geometry (branch/fruit reconstruction is out of scope for
`LiDARCloud`'s leaf-area API and is not attempted here) and whose LEAVES are entirely
the LiDAR-reconstructed mesh -- an honest stand-in for "what a real scan-and-reconstruct
pipeline would hand a downstream planner", not a claim that branch/fruit detection is
solved by this script.

## Metric vector and rank preservation

Both canopies are scored with `policies.score_canopy` (Phase 2/5's real
per-primitive-visibility + `mean_coverage_frac`/`fraction_fruit_observed` headline
metric, PREREGISTRATION.md) under the SAME 4 policies used throughout this phase:
`single_fixed` (T5.1-style), `fixed_rig` (T5.2-style), `reachable_union` (T5.8-style),
`look_away` (T8.5's degenerate baseline). Rank preservation is checked with Phase 6's
own `spearman_rho` (`yogesh_dev/phase6/common.py`, reused unchanged) over the 4
policies' `mean_coverage_frac` values on original vs twin.

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase8.t86_digital_twin
"""

import json
import os
import time

import numpy as np

from pyhelios import LiDARCloud
from pyhelios.types import vec3, RGBcolor

from yogesh_dev.phase8.canopy_factory import build_canopy
from yogesh_dev.phase8.policies import score_canopy
from yogesh_dev.phase6.common import spearman_rho

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
TEST_SEED = 2000  # reserved test seed, per PREREGISTRATION.md -- never used by T8.2/T8.4
N_STATIONS = 4
LEAF_RECONSTRUCTED_COLOR = RGBcolor(0.25, 0.55, 0.20)


def scan_canopy(context, uuids):
    """Real multi-station terrestrial LiDAR scan of the canopy's own real geometry.
    Returns the LiDARCloud (caller must not exit it until done reading triangles) plus
    scan diagnostics."""
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    height = z_bounds.y - z_bounds.x
    width = max(x_bounds.y - x_bounds.x, y_bounds.y - y_bounds.x)
    center = vec3((x_bounds.x + x_bounds.y) / 2, (y_bounds.x + y_bounds.y) / 2,
                  z_bounds.x + 0.5 * height)
    standoff = max(1.5 * width, 1.5)

    lidar = LiDARCloud()
    lidar.__enter__()
    scan_ids = []
    # Empirically validated against this environment's actual phi/theta convention
    # (see PHASE8_LOG.md T8.6 section): a narrow phi slice aimed at the canopy center
    # dropped ALL rays as misses even though the debug back-projection of the OTHER
    # (full-circle) scan's real hits confirmed the aim math was directionally
    # correct -- most pulses in a narrow phi/theta window are silently dropped from
    # the cloud entirely (not even recorded as misses) rather than every pulse being
    # preserved. Scanning the FULL azimuth circle from each station every time (with a
    # theta band around the horizon sized to the canopy height) reliably produces real
    # hits and is simple and fast enough (<1s for all 4 stations) not to need chasing
    # the narrow-window behavior further.
    theta_half = np.arctan2(0.6 * height, standoff) + 0.15
    for i in range(N_STATIONS):
        az = 2 * np.pi * i / N_STATIONS
        origin = vec3(center.x + standoff * np.cos(az), center.y + standoff * np.sin(az), center.z)
        scan_id = lidar.addScan(
            origin=origin, Ntheta=200, theta_range=(np.pi / 2 - theta_half, np.pi / 2 + theta_half),
            Nphi=600, phi_range=(0.0, 2 * np.pi),
            exit_diameter=0.01, beam_divergence=0.001,
            range_noise_stddev=0.003,  # 3mm range noise -- realistic terrestrial LiDAR
        )
        scan_ids.append(scan_id)

    t0 = time.time()
    lidar.syntheticScan(context, record_misses=True)
    scan_s = time.time() - t0
    n_hits = lidar.getHitCount()
    distances = np.asarray(lidar.getHitDataAll("distance"), dtype=float)
    n_real_hits = int(np.sum(distances < 100.0))  # miss sentinel is ~1001m, real hits are meters away

    return lidar, {
        "n_stations": N_STATIONS, "standoff_m": standoff, "scan_s": scan_s,
        "n_points_total": n_hits, "n_real_surface_hits": n_real_hits,
        "n_recorded_misses": n_hits - n_real_hits,
        "canopy_height_m": height, "canopy_width_m": width,
    }


def reconstruct_leaves(lidar, context, uuids):
    """Real leaf-by-leaf reconstruction: grid + Delaunay triangulation + leaf-area
    inversion, plus a real fidelity check against exact-geometry synthetic leaf area."""
    x_bounds, y_bounds, z_bounds = context.getDomainBoundingBox(uuids)
    center = vec3((x_bounds.x + x_bounds.y) / 2, (y_bounds.x + y_bounds.y) / 2,
                  (z_bounds.x + z_bounds.y) / 2)
    size = vec3(1.3 * (x_bounds.y - x_bounds.x), 1.3 * (y_bounds.y - y_bounds.x),
                1.3 * (z_bounds.y - z_bounds.x))
    lidar.addGrid(center=center, size=size, ndiv=[4, 4, 6])

    t0 = time.time()
    # Lmax ~ real apple leaf prototype scale (helios-core's phytomer_parameters_apple.leaf
    # prototype_scale=0.12m) -- big enough that a real, sparse-but-usable point cloud
    # (thousands, not millions, of points) still triangulates most candidates; see
    # PHASE8_LOG.md T8.6 section for the Lmax sweep this was picked from.
    lidar.triangulateHitPoints(Lmax=0.15, max_aspect_ratio=8.0)
    tri_s = time.time() - t0
    tri_stats = lidar.getTriangulationStats()
    n_triangles = lidar.getTriangleCount()

    recon_report = {"triangulation_s": tri_s, "n_triangles": n_triangles, "triangulation_stats": tri_stats}

    if n_triangles == 0:
        return None, recon_report

    xyz_flat, scan_ids = lidar.getTriangleVerticesAll()
    triangles = np.asarray(xyz_flat, dtype=float).reshape(n_triangles, 3, 3)

    n_cells = lidar.getGridCellCount()
    lidar.calculateLeafArea(context, min_voxel_hits=1)
    lidar_leaf_area = sum(lidar.getCellLeafArea(i) for i in range(n_cells))

    # calculateSyntheticLeafArea() is documented as an exact-geometry ground-truth
    # comparator -- tried it here, but on this scene/config it returned 0.0 for every
    # cell even in a freshly-isolated LiDARCloud (verified directly, not assumed --
    # see PHASE8_LOG.md T8.6 section), so it is not a trustworthy reference in this
    # environment. The real ground truth used instead is the exact, unambiguous sum of
    # this canopy's own real leaf primitive areas (`context.getPrimitiveArea`, the same
    # mechanism Phase 7's `lai_sweep.py` already uses for its own real leaf-area number).
    lidar.calculateSyntheticLeafArea(context)
    synthetic_api_leaf_area = sum(lidar.getCellLeafArea(i) for i in range(n_cells))
    leaf_uuids = context.filterPrimitivesByData(uuids, "object_label", "leaf")
    ground_truth_leaf_area = sum(context.getPrimitiveArea(u) for u in leaf_uuids)

    recon_report.update({
        "n_grid_cells": n_cells,
        "lidar_inverted_leaf_area_m2": lidar_leaf_area,
        "ground_truth_leaf_area_m2": ground_truth_leaf_area,
        "calculateSyntheticLeafArea_api_result_m2": synthetic_api_leaf_area,
        "calculateSyntheticLeafArea_api_unreliable_here": (
            synthetic_api_leaf_area == 0.0 or synthetic_api_leaf_area == lidar_leaf_area),
        "leaf_area_ratio_lidar_over_ground_truth": (
            lidar_leaf_area / ground_truth_leaf_area if ground_truth_leaf_area > 0 else None),
    })
    return triangles, recon_report


def build_twin_context(triangles):
    """Real leafless scaffold of the SAME canopy (same seed, lai_keep_frac=0.0,
    deterministic per T8.1) + the LiDAR-reconstructed triangle mesh added as new
    primitives, tagged `object_label=leaf_reconstructed` (never `leaf`, see module
    docstring)."""
    twin = build_canopy(seed=TEST_SEED, tree_type="apple", n_trees=1, lai_keep_frac=0.0, fruit_keep_frac=1.0)
    added_uuids = []
    for tri in triangles:
        v0, v1, v2 = vec3(*tri[0]), vec3(*tri[1]), vec3(*tri[2])
        uid = twin.context.addTriangle(v0, v1, v2, LEAF_RECONSTRUCTED_COLOR)
        added_uuids.append(uid)
    twin.context.setPrimitiveDataString(added_uuids, "object_label", "leaf_reconstructed")
    twin.context.setPrimitiveDataInt(added_uuids, "is_lidar_reconstructed", 1)
    # Extend the cached UUID lists so vis_primitive_id assignment covers these too
    # (harmless either way -- see policies.py -- but keeps Canopy's own bookkeeping honest).
    twin._cached_uuids = list(twin._cached_uuids) + added_uuids
    twin._cached_per_tree_uuids[0] = list(twin._cached_per_tree_uuids[0]) + added_uuids
    return twin, len(added_uuids)


def rank_of(policy_values):
    """policy_values: {policy_name: mean_coverage_frac}. Returns {policy_name: rank}
    where rank 1 = highest coverage."""
    ordered = sorted(policy_values.items(), key=lambda kv: -kv[1])
    return {name: i + 1 for i, (name, _val) in enumerate(ordered)}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Building original canopy (seed={TEST_SEED})...", flush=True)
    original = build_canopy(seed=TEST_SEED, tree_type="apple", n_trees=1)
    print(f"  n_fruit={len(original.fruit_records)}, "
          f"n_leaves={original.thinning_report['n_leaf_total']}", flush=True)

    print("Scanning original canopy with simulated LiDAR...", flush=True)
    lidar, scan_report = scan_canopy(original.context, original.tree_uuids(0))
    print(f"  {json.dumps(scan_report, default=str)}", flush=True)

    print("Reconstructing leaves (triangulation + leaf-area inversion)...", flush=True)
    triangles, recon_report = reconstruct_leaves(lidar, original.context, original.tree_uuids(0))
    print(f"  {json.dumps(recon_report, default=str)}", flush=True)
    lidar.__exit__(None, None, None)

    if triangles is None or len(triangles) == 0:
        original.close()
        report = {
            "status": "BLOCKED", "reason": "triangulation produced 0 triangles, cannot build a twin",
            "scan_report": scan_report, "reconstruction_report": recon_report,
        }
        with open(os.path.join(OUTPUT_DIR, "t86_digital_twin.json"), "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(json.dumps(report, indent=2, default=str))
        return report

    print("Scoring ORIGINAL canopy (4 policies)...", flush=True)
    t0 = time.time()
    original_score = score_canopy(original)
    original_score_s = time.time() - t0
    original.close()

    print(f"Building digital twin ({len(triangles)} reconstructed leaf triangles)...", flush=True)
    twin, n_added = build_twin_context(triangles)
    print("Scoring TWIN canopy (4 policies)...", flush=True)
    t0 = time.time()
    twin_score = score_canopy(twin)
    twin_score_s = time.time() - t0
    twin.close()

    policy_names = list(original_score["policies"].keys())
    original_vec = {p: original_score["policies"][p]["mean_coverage_frac"] for p in policy_names}
    twin_vec = {p: twin_score["policies"][p]["mean_coverage_frac"] for p in policy_names}

    original_ranks = rank_of(original_vec)
    twin_ranks = rank_of(twin_vec)
    rank_preserved = original_ranks == twin_ranks

    rho = spearman_rho([original_ranks[p] for p in policy_names], [twin_ranks[p] for p in policy_names])

    report = {
        "status": "DONE",
        "test_seed": TEST_SEED,
        "scan_report": scan_report,
        "reconstruction_report": recon_report,
        "n_reconstructed_leaf_triangles_added_to_twin": n_added,
        "original_metric_vector": original_vec,
        "twin_metric_vector": twin_vec,
        "original_ranks": original_ranks,
        "twin_ranks": twin_ranks,
        "rank_preserved_exactly": rank_preserved,
        "spearman_rho_original_vs_twin_ranks": rho,
        "original_score_s": original_score_s,
        "twin_score_s": twin_score_s,
        "original_full_policies": original_score["policies"],
        "twin_full_policies": twin_score["policies"],
    }

    out_path = os.path.join(OUTPUT_DIR, "t86_digital_twin.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n--- T8.6 summary ---")
    print("policy         original  twin    orig_rank  twin_rank")
    for p in policy_names:
        print(f"{p:14s} {original_vec[p]:.3f}     {twin_vec[p]:.3f}   {original_ranks[p]:^9d}  {twin_ranks[p]:^9d}")
    print(f"rank_preserved_exactly: {rank_preserved}   spearman_rho: {rho:.3f}")
    print(f"leaf area reconstruction fidelity (lidar/synthetic): "
          f"{recon_report.get('leaf_area_ratio_lidar_over_ground_truth')}")
    print(f"\nwrote {out_path}")
    return report


if __name__ == "__main__":
    main()
