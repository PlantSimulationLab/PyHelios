"""
W2 -- verify the action space and trajectory samplers.

Acceptance criteria from the plan:
  A1  trajectories stay inside the orchard bounds and inside the inter-row lane
  A2  replaying recorded actions from the start pose reproduces the recorded
      poses to < 1e-6

Plus honest reporting of what the samplers actually produce: action magnitude
statistics per family, and how much of an `orbit` passes through canopy volume
(orbits cannot stay in the lane -- that is the point of the family -- so A1 is
checked against the lane for the two lane families and against the orchard's
outer bounds for orbits, with the canopy intrusion reported as a real number).

This task needs no rendering, so it is pure NumPy and runs in seconds.

Run:
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.world_model.run_w2
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.orchard import orchard_extent
from yogesh_dev.world_model import actions as A

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w2")


def main(n_traj=200, n_steps=128):
    os.makedirs(OUT_DIR, exist_ok=True)
    ext = orchard_extent()
    lines, results = [], {"script": "run_w2.py", "n_traj_per_family": n_traj,
                          "n_steps": n_steps, "extent": ext}

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    log("=" * 78)
    log("W2 -- action space + trajectory samplers")
    log("=" * 78)
    b = A.lane_bounds(ext)
    log(f"lane box: x={b['x']} y={b['y']} z={b['z']}")

    per_family = {}
    worst_replay = 0.0
    for family in A.TRAJECTORY_FAMILIES:
        in_bounds_all, replay_errs, intrusions, stats = [], [], [], []
        for i in range(n_traj):
            states, acts, meta = A.sample_trajectory(family, n_steps, ext, seed=90000 + i)

            # A2: replay
            replay = A.actions_to_states(states[0], acts)
            err = A.state_error(states, replay)
            replay_errs.append(err)
            worst_replay = max(worst_replay, err)

            # A1: bounds
            if family == "orbit":
                # orbits leave the lane by construction; check outer bounds
                ok = ((states[:, 0] >= ext["x_min"] - 3.0) & (states[:, 0] <= ext["x_max"] + 3.0)
                      & (states[:, 1] >= min(ext["row_y"]) - 3.0)
                      & (states[:, 1] <= max(ext["row_y"]) + 3.0)
                      & (states[:, 2] >= A.CAMERA_Z_MIN - 1e-9)
                      & (states[:, 2] <= A.CAMERA_Z_MAX + 1e-9))
                intrusions.append(A.orbit_intrusion(states, ext))
            else:
                ok = A.in_lane(states, b)
            in_bounds_all.append(float(ok.mean()))
            stats.append(A.action_stats(acts))

        abs_mean = np.mean([s["abs_mean"] for s in stats], axis=0)
        abs_max = np.max([s["abs_max"] for s in stats], axis=0)
        rec = {
            "in_bounds_fraction_mean": float(np.mean(in_bounds_all)),
            "in_bounds_all_trajectories": bool(np.all(np.array(in_bounds_all) == 1.0)),
            "replay_max_error": float(np.max(replay_errs)),
            "replay_mean_error": float(np.mean(replay_errs)),
            "action_abs_mean_dx_dy_dz_dyaw": abs_mean.tolist(),
            "action_abs_max_dx_dy_dz_dyaw": abs_max.tolist(),
        }
        if intrusions:
            rec["canopy_intrusion_fraction_mean"] = float(np.mean(intrusions))
            rec["canopy_intrusion_fraction_max"] = float(np.max(intrusions))
        per_family[family] = rec

        log(f"\n[{family}] {n_traj} trajectories x {n_steps} steps")
        log(f"  in-bounds fraction: mean={rec['in_bounds_fraction_mean']:.6f}  "
            f"all-in-bounds={rec['in_bounds_all_trajectories']}")
        log(f"  replay error: max={rec['replay_max_error']:.3e}  mean={rec['replay_mean_error']:.3e}")
        log(f"  |action| mean (dx,dy,dz,dyaw) = "
            f"{', '.join(f'{v:.4f}' for v in abs_mean)}")
        log(f"  |action| max  (dx,dy,dz,dyaw) = "
            f"{', '.join(f'{v:.4f}' for v in abs_max)}")
        if intrusions:
            log(f"  canopy intrusion (orbit passes inside a canopy cylinder): "
                f"mean={rec['canopy_intrusion_fraction_mean']:.3f} "
                f"max={rec['canopy_intrusion_fraction_max']:.3f}")

    # determinism of the samplers themselves
    s1, a1, _ = A.sample_trajectory("row_traversal", n_steps, ext, seed=12345)
    s2, a2, _ = A.sample_trajectory("row_traversal", n_steps, ext, seed=12345)
    s3, _, _ = A.sample_trajectory("row_traversal", n_steps, ext, seed=12346)
    sampler_det = {"same_seed_identical": bool(np.array_equal(s1, s2)),
                   "different_seed_differs": bool(not np.array_equal(s1, s3))}
    log(f"\n[sampler determinism] {sampler_det}")

    results["per_family"] = per_family
    results["sampler_determinism"] = sampler_det
    results["acceptance"] = {
        "A1_all_in_bounds": bool(all(v["in_bounds_all_trajectories"] for v in per_family.values())),
        "A2_replay_under_1e-6": bool(worst_replay < 1e-6),
        "worst_replay_error": float(worst_replay),
    }
    log(f"\nACCEPTANCE: {results['acceptance']}")

    with open(os.path.join(OUT_DIR, "w2_measurements.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(OUT_DIR, "w2_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {OUT_DIR}/w2_measurements.json")
    return results


if __name__ == "__main__":
    main()
