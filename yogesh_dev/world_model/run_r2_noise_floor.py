"""
Round 2 / R2-B -- the RGB noise floor measured AT THE GROWTH PROBE POSES.

R2-A found that consecutive growth stages differ by ~20.6 dB RGB PSNR while
FINDINGS section 9 measured the simulator's own re-render reproducibility at
20.82 dB. Those two numbers came from different poses and different orchards, so
comparing them is suggestive rather than conclusive. This script measures both in
the SAME run, at the SAME poses, on the SAME orchard:

  * render the fixed growth-probe rig twice at each stage without touching the
    scene -> PSNR between repeats = the Monte-Carlo radiance noise floor
  * render the next stage -> PSNR between stages = the growth signal + that noise

If the two are equal, the RGB growth signal is buried in render noise and no
model can recover it, whatever the training budget. Depth and semantic are
bit-exact (FINDINGS section 9) so the same script reports those as a control:
they should show zero repeat-to-repeat difference and a real stage-to-stage one.

Runs in the `helios` env (needs PyHelios + OpenEXR).

    /home/yogesh/anaconda3/envs/helios/bin/python \
        -m yogesh_dev.world_model.run_r2_noise_floor
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.orchard import build_orchard, orchard_extent
from yogesh_dev.world_model.render import ObservationRig
from yogesh_dev.world_model import actions as A
from yogesh_dev.world_model.generate import GROWTH_STAGES


def psnr_u8(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return float("inf") if mse <= 0 else float(10.0 * np.log10(255.0 ** 2 / mse))


def depth_mae(a, b):
    m = (a > -0.5) & (b > -0.5)
    return float(np.abs(a[m] - b[m]).mean()) if m.any() else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=12000, help="a TEST-split orchard seed")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "output", "r2"))
    ap.add_argument("--n-probes", type=int, default=16)
    ap.add_argument("--resolution", type=int, default=128)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    logf = open(os.path.join(args.out, "r2_noise_floor_log.txt"), "w")

    def log(m):
        print(m, flush=True)
        logf.write(str(m) + "\n")
        logf.flush()

    man_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "output", "dataset", "manifest.json")
    with open(man_path) as f:
        man = json.load(f)
    cfg = man["config"]
    stages = cfg["stages"] or GROWTH_STAGES
    expo = cfg["exposure_scale"]
    orient = cfg["orientation"]
    log(f"R2-B noise floor at growth probe poses  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"  seed={args.seed} stages={stages} exposure={expo:.6f} orientation={orient}")

    ext = orchard_extent()
    # exactly the probe rig generate.py uses for this seed
    probe_rng = np.random.default_rng(args.seed * 7919 + 13)
    probe_states = A.sample_random_walk(args.n_probes, ext, probe_rng)
    probe_poses = A.states_to_poses(probe_states)

    orch = build_orchard(seed=args.seed, age_days=stages[0])
    rig = None
    rows = []
    try:
        rig = ObservationRig(orch, n_cameras=args.n_probes,
                             resolution=(args.resolution, args.resolution),
                             sun_zenith=cfg["sun_zenith"], sun_azimuth=cfg["sun_azimuth"],
                             exposure_scale=expo)
        rig.open()
        rig._orientation = orient

        prev = None
        for si, age in enumerate(stages):
            if si > 0:
                orch.grow(age - stages[si - 1])
                rig.radiation.updateGeometry()
            fa, _ = rig.render_batch(probe_poses)
            fb, _ = rig.render_batch(probe_poses)     # identical scene, second solve
            rep_rgb = float(np.mean([psnr_u8(x["rgb"], y["rgb"]) for x, y in zip(fa, fb)]))
            rep_dep = float(np.mean([depth_mae(x["depth"], y["depth"]) for x, y in zip(fa, fb)]))
            rep_sem = float(np.mean([(x["semantic"] == y["semantic"]).mean()
                                     for x, y in zip(fa, fb)]))
            row = {"stage": si, "age_days": age, "repeat_rgb_psnr_db": rep_rgb,
                   "repeat_depth_mae_m": rep_dep, "repeat_semantic_agreement": rep_sem}
            if prev is not None:
                row["stage_step_rgb_psnr_db"] = float(np.mean(
                    [psnr_u8(x["rgb"], y["rgb"]) for x, y in zip(prev, fa)]))
                row["stage_step_depth_mae_m"] = float(np.mean(
                    [depth_mae(x["depth"], y["depth"]) for x, y in zip(prev, fa)]))
                row["stage_step_semantic_agreement"] = float(np.mean(
                    [(x["semantic"] == y["semantic"]).mean() for x, y in zip(prev, fa)]))
            rows.append(row)
            log(f"  stage {si} age={age:.0f}d prims={orch.n_primitives()}  "
                f"repeat: RGB {rep_rgb:6.2f} dB, depth MAE {rep_dep:.4f} m, "
                f"sem agree {rep_sem:.6f}"
                + ("" if prev is None else
                   f"  |  vs previous stage: RGB {row['stage_step_rgb_psnr_db']:6.2f} dB, "
                   f"depth MAE {row['stage_step_depth_mae_m']:.4f} m, "
                   f"sem agree {row['stage_step_semantic_agreement']:.4f}"))
            prev = fa
    finally:
        if rig is not None:
            rig.close()
        orch.close()

    rep = float(np.mean([r["repeat_rgb_psnr_db"] for r in rows]))
    stp = float(np.mean([r["stage_step_rgb_psnr_db"] for r in rows if "stage_step_rgb_psnr_db" in r]))
    rep_rms = 255.0 * 10 ** (-rep / 20.0)
    stp_rms = 255.0 * 10 ** (-stp / 20.0)
    signal_rms = float(np.sqrt(max(0.0, stp_rms ** 2 - rep_rms ** 2)))
    summary = {
        "seed": args.seed, "stages": stages, "rows": rows,
        "mean_repeat_rgb_psnr_db": rep,
        "mean_stage_step_rgb_psnr_db": stp,
        "repeat_rms_levels": rep_rms, "stage_step_rms_levels": stp_rms,
        "implied_growth_signal_rms_levels": signal_rms,
        "signal_to_noise_rms": signal_rms / max(1e-9, rep_rms),
        "mean_repeat_depth_mae_m": float(np.mean([r["repeat_depth_mae_m"] for r in rows])),
        "mean_stage_step_depth_mae_m": float(np.mean(
            [r["stage_step_depth_mae_m"] for r in rows if "stage_step_depth_mae_m" in r])),
    }
    log("")
    log(f"  RGB: repeat {rep:.2f} dB ({rep_rms:.2f} RMS levels), "
        f"stage step {stp:.2f} dB ({stp_rms:.2f} RMS levels)")
    log(f"  => growth signal RMS = sqrt(step^2 - noise^2) = {signal_rms:.2f} levels, "
        f"SNR = {summary['signal_to_noise_rms']:.2f}")
    log(f"  depth: repeat MAE {summary['mean_repeat_depth_mae_m']:.6f} m, "
        f"stage step MAE {summary['mean_stage_step_depth_mae_m']:.4f} m")

    with open(os.path.join(args.out, "r2_noise_floor.json"), "w") as f:
        json.dump(summary, f, indent=1)
    log(f"wrote {os.path.join(args.out, 'r2_noise_floor.json')}")
    logf.close()


if __name__ == "__main__":
    main()
