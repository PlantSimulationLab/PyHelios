"""
W1 -- verify and characterise the batched observation rig.

Produces, all from real renders of a real 2x10 orchard:
  V1  pixel-array orientation, checked against the label map (not assumed)
  V2  fixed global exposure scale + its calibration statistics
  V3  camera-batching throughput table (N = 1,4,16,32,64,128,256) -- re-verifies
      the plan's measured table and probes 256
  V4  a human-inspectable contact sheet (RGB / depth / semantic / instance)
  V5  depth sanity: min/max/sky-fraction against the orchard's real bounding box
  V6  semantic class histogram vs the organ primitive counts from W0

Run:
    cd /home/yogesh/PyHelios && \
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.world_model.run_w1
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.orchard import build_orchard, orchard_extent, SEMANTIC_CLASS_NAMES
from yogesh_dev.world_model.render import (
    ObservationRig, contact_sheet, colorize_depth, tonemap, SKY_SEMANTIC_ID,
    DEFAULT_RESOLUTION,
)
from yogesh_dev.phase1.label_maps import _colorize_semantic, _colorize_instance
from yogesh_dev.phase1.depth_export import SKY_DEPTH_SENTINEL

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w1")
DEFAULT_AGE = 720.0
DEFAULT_SEED = 10000


def _log(msg, lines):
    print(msg, flush=True)
    lines.append(str(msg))


def lane_poses(n, ext, height=1.2, look_ahead=1.0, look_y=0.0, jitter=0.0, rng=None):
    """Simple down-the-lane camera path used for calibration and smoke tests.

    Drives along +x at y=lane_y, looking mostly forward and slightly toward a row.
    The real trajectory samplers live in `actions.py` (W2); this is deliberately
    a fixed, boring path so W1's numbers are not entangled with W2's sampling.
    """
    xs = np.linspace(ext["x_min"], ext["x_max"], n)
    poses = []
    for i, x in enumerate(xs):
        dy = 0.0 if rng is None or jitter == 0 else float(rng.uniform(-jitter, jitter))
        eye = (float(x), float(ext["lane_y"] + dy), float(height))
        # Look across the lane at row 0 with a forward component -- gives the
        # canopy in frame rather than an empty corridor.
        lookat = (float(x + look_ahead), float(ext["row_y"][0] + look_y), float(height * 0.85))
        poses.append((eye, lookat))
    return poses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--age", type=float, default=DEFAULT_AGE)
    ap.add_argument("--max-batch", type=int, default=256)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    lines, results = [], {"script": "run_w1.py", "seed": args.seed, "age_days": args.age}
    import imageio.v3 as iio

    _log("=" * 78, lines)
    _log("W1 -- batched observation rig", lines)
    _log("=" * 78, lines)

    _log(f"\n[build] 2x10 orchard seed={args.seed} age={args.age}d", lines)
    t0 = time.time()
    orch = build_orchard(seed=args.seed, age_days=args.age)
    _log(f"  {orch.n_primitives()} primitives in {orch.build_time_s:.1f}s "
         f"(total incl. ground truth {time.time()-t0:.1f}s)", lines)
    results["orchard"] = orch.summary()
    ext = orchard_extent()

    try:
        batch_sizes = [1, 4, 16, 32] if args.quick else [1, 4, 16, 32, 64, 128, args.max_batch]
        batch_sizes = sorted(set(b for b in batch_sizes if b > 0))
        n_max = max(batch_sizes)

        _log(f"\n[rig] registering {n_max} cameras at {DEFAULT_RESOLUTION}", lines)
        rig = ObservationRig(orch, n_cameras=n_max)
        rig.open()
        _log(f"  updateGeometry: {rig.timings['update_geometry_s']:.2f}s  "
             f"HFOV={rig.hfov_deg:.2f} deg", lines)

        # -- V1 orientation --------------------------------------------------
        _log("\n[V1] pixel-array orientation vs label map", lines)
        cal_poses = lane_poses(8, ext)
        orient = rig.calibrate_orientation(cal_poses)
        results["orientation"] = orient
        _log(f"  method: {orient.get('method')}", lines)
        for k, v in orient.get("score_per_orientation", {}).items():
            _log(f"  {k:8s} leaf/fruit green-red score = {v}", lines)
        _log(f"  per-camera votes: {orient.get('per_camera_votes')} "
             f"(n usable views {orient.get('n_usable_cameras')})", lines)
        _log(f"  example diagnostics: {orient.get('example_diagnostics')}", lines)
        _log(f"  -> applying '{orient['applied']}' (score {orient.get('best_score')})", lines)

        # -- V2 exposure -----------------------------------------------------
        _log("\n[V2] fixed global exposure calibration", lines)
        expo = rig.calibrate_exposure(lane_poses(16, ext), percentile=99.0)
        results["exposure"] = expo
        _log(f"  {json.dumps(expo, indent=2)}", lines)

        # -- V3 batching throughput -----------------------------------------
        _log("\n[V3] camera-batching throughput (solve only, 3 bands)", lines)
        table = []
        for n in batch_sizes:
            poses = lane_poses(n, ext)
            rig.solve(poses)                       # warm
            ts = [rig.solve(poses) for _ in range(2)]
            t = float(np.mean(ts))
            table.append({"n_cameras": n, "solve_s": t, "per_image_s": t / n})
            _log(f"  N={n:4d}  solve={t:7.3f}s  per-image={t/n:.4f}s", lines)
        results["batching_table"] = table

        # -- readback cost ---------------------------------------------------
        _log("\n[V3b] readback cost per image (128 cameras)", lines)
        n_rb = min(128, n_max)
        poses = lane_poses(n_rb, ext)
        frames, timing = rig.render_batch(poses)
        _log(f"  solve={timing['solve_s']:.2f}s  read={timing['read_s']:.2f}s  "
             f"({timing['read_s']/n_rb:.4f}s/image, all 4 modalities)", lines)
        results["readback"] = {**timing, "read_per_image_s": timing["read_s"] / n_rb}

        # -- V4 contact sheets ----------------------------------------------
        _log("\n[V4] contact sheets", lines)
        sub = frames[:32]
        iio.imwrite(os.path.join(OUT_DIR, "contact_rgb.png"), contact_sheet(sub, cols=8, key="rgb"))
        iio.imwrite(os.path.join(OUT_DIR, "contact_depth.png"),
                    contact_sheet([{"rgb": colorize_depth(f["depth"])} for f in sub], cols=8))
        iio.imwrite(os.path.join(OUT_DIR, "contact_semantic.png"),
                    contact_sheet([{"rgb": _colorize_semantic(
                        np.where(f["semantic"] == SKY_SEMANTIC_ID, np.nan,
                                 f["semantic"]).astype(float))} for f in sub], cols=8))
        iio.imwrite(os.path.join(OUT_DIR, "contact_instance.png"),
                    contact_sheet([{"rgb": _colorize_instance(
                        np.where(f["instance"] < 0, np.nan,
                                 f["instance"]).astype(float))} for f in sub], cols=8))
        # full-res single frame for qualitative eval
        _log(f"  wrote 4 contact sheets to {OUT_DIR}", lines)

        # -- V5 depth sanity -------------------------------------------------
        _log("\n[V5] depth sanity vs orchard bounding box", lines)
        lo, hi = orch.bounds()
        dstats = []
        for f in frames[:16]:
            d = f["depth"]
            v = d[d != SKY_DEPTH_SENTINEL]
            dstats.append({"min": float(v.min()) if v.size else None,
                           "max": float(v.max()) if v.size else None,
                           "mean": float(v.mean()) if v.size else None,
                           "sky_frac": float((d == SKY_DEPTH_SENTINEL).mean())})
        diag = float(np.linalg.norm(hi - lo))
        results["depth"] = {"per_frame": dstats, "orchard_diag_m": diag,
                            "bounds_min": lo.tolist(), "bounds_max": hi.tolist()}
        mins = [s["min"] for s in dstats if s["min"] is not None]
        maxs = [s["max"] for s in dstats if s["max"] is not None]
        _log(f"  over 16 frames: depth min={min(mins):.3f}m max={max(maxs):.3f}m; "
             f"orchard bbox diagonal={diag:.2f}m", lines)
        _log(f"  mean sky fraction = {np.mean([s['sky_frac'] for s in dstats]):.3f}", lines)
        results["depth"]["sane"] = bool(min(mins) > 0.0 and max(maxs) < diag * 1.5)
        _log(f"  sane (0 < depth < 1.5x bbox diagonal): {results['depth']['sane']}", lines)

        # -- V5b depth/semantic sky-mask agreement ---------------------------
        agree = []
        for f in frames[:16]:
            a = (f["depth"] == SKY_DEPTH_SENTINEL)
            b = (f["semantic"] == SKY_SEMANTIC_ID)
            agree.append(float((a == b).mean()))
        results["depth"]["sky_mask_agreement_with_semantic"] = float(np.mean(agree))
        _log(f"  depth-sky vs semantic-sky pixel agreement: {np.mean(agree):.6f}", lines)

        # -- V6 semantic histogram vs W0 organ counts ------------------------
        _log("\n[V6] semantic class histogram over 128 views", lines)
        hist = {}
        for f in frames:
            u, c = np.unique(f["semantic"], return_counts=True)
            for k, v in zip(u.tolist(), c.tolist()):
                hist[int(k)] = hist.get(int(k), 0) + int(v)
        total = sum(hist.values())
        named = {}
        for k, v in sorted(hist.items()):
            nm = "sky" if k == SKY_SEMANTIC_ID else SEMANTIC_CLASS_NAMES.get(k, f"class_{k}")
            named[nm] = {"pixels": v, "fraction": v / total}
            _log(f"  {nm:9s} {v:9d}  {v/total*100:6.2f}%", lines)
        results["semantic_histogram"] = named
        results["organ_primitive_counts"] = dict(orch.organ_counts)
        _log(f"  W0 organ primitive counts: {orch.organ_counts}", lines)

        # -- full-res qualitative frame --------------------------------------
        _log("\n[extra] full-resolution qualitative frame (512x512)", lines)
        rig.close()
        rig_hi = ObservationRig(orch, n_cameras=4, resolution=(512, 512),
                                exposure_scale=expo["exposure_scale"])
        rig_hi.open()
        rig_hi._orientation = orient["applied"]
        hi_poses = lane_poses(4, ext)
        hi_frames, _ = rig_hi.render_batch(hi_poses)
        for i, f in enumerate(hi_frames):
            iio.imwrite(os.path.join(OUT_DIR, f"hires_{i}_rgb.png"), f["rgb"])
            iio.imwrite(os.path.join(OUT_DIR, f"hires_{i}_depth.png"), colorize_depth(f["depth"]))
        rig_hi.close()
        _log(f"  wrote {len(hi_frames)} 512x512 frames", lines)

    finally:
        orch.close()

    with open(os.path.join(OUT_DIR, "w1_measurements.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(OUT_DIR, "w1_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    _log(f"\nWrote {OUT_DIR}/w1_measurements.json", lines)
    return results


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            sys.path.insert(0, "/home/yogesh/PyHelios")
            from notify_slack import notify_slack
            notify_slack(f"World model W1 FAILED: {traceback.format_exc()[-1200:]}")
        except Exception:
            pass
        raise
