"""
W3 follow-up: WHY is a regenerated shard not byte-identical?

`run_w3_verify.py`'s A1 check regenerated one orchard and found 0/40 episodes
byte-identical -- but its per-array breakdown showed the failure is not general:

    depth      identical
    semantic   identical
    a_view     identical
    rgb        NOT identical
    instance   NOT identical

Geometry and labels are deterministic; radiance and the fruit-instance map are
not. This script quantifies exactly how far apart the two runs are, so the
dataset's reproducibility can be stated precisely instead of as a binary
pass/fail.

Run (helios env):
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.world_model.run_w3_determinism_probe
"""

import json
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.generate import generate_orchard

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "dataset")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w3")


def main():
    with open(os.path.join(DATA, "manifest.json")) as f:
        man = json.load(f)
    cfg = man["config"]
    seed = sorted({e["orchard_seed"] for e in man["episodes"] if e["split"] == "train"})[0]

    tmp = tempfile.mkdtemp(prefix="wm_probe_")
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    try:
        # Regenerate only the first growth stage and one family -- enough to
        # compare, cheap enough to run beside a training job.
        recs = generate_orchard(
            seed, "train", tmp, n_steps=cfg["n_steps"], families=("row_traversal",),
            stages=cfg["stages"][:1], n_growth_probes=2,
            exposure_scale=cfg["exposure_scale"], orientation=cfg["orientation"],
            resolution=tuple(cfg["resolution"]), sun_zenith=cfg["sun_zenith"],
            sun_azimuth=cfg["sun_azimuth"], log=log)
        rec = [r for r in recs if r["episode_type"] == "view"][0]
        a = np.load(os.path.join(DATA, rec["path"]))
        b = np.load(os.path.join(tmp, rec["path"]))

        log(f"\ncomparing {rec['path']}")
        res = {"episode": rec["path"], "seed": seed}

        rgb_a, rgb_b = a["rgb"].astype(np.int16), b["rgb"].astype(np.int16)
        d = np.abs(rgb_a - rgb_b)
        res["rgb"] = {"identical": bool((d == 0).all()),
                      "frac_pixels_differing": float((d > 0).mean()),
                      "mean_abs_diff_levels": float(d.mean()),
                      "max_abs_diff_levels": int(d.max()),
                      "p99_abs_diff_levels": float(np.percentile(d, 99)),
                      "psnr_db": float(10 * np.log10(255.0 ** 2 / max(1e-9, (d.astype(float) ** 2).mean())))}
        log(f"  rgb: {json.dumps(res['rgb'])}")

        ia, ib = a["instance"], b["instance"]
        mask_a, mask_b = ia >= 0, ib >= 0
        res["instance"] = {
            "identical": bool((ia == ib).all()),
            "fruit_mask_identical": bool((mask_a == mask_b).all()),
            "fruit_mask_iou": float((mask_a & mask_b).sum() / max(1, (mask_a | mask_b).sum())),
            "n_unique_ids_run_a": int(len(np.unique(ia[mask_a]))),
            "n_unique_ids_run_b": int(len(np.unique(ib[mask_b]))),
            "id_sets_equal": bool(set(np.unique(ia[mask_a]).tolist()) == set(np.unique(ib[mask_b]).tolist())),
            "frac_pixels_differing": float((ia != ib).mean()),
        }
        log(f"  instance: {json.dumps(res['instance'])}")

        for k in ("depth", "semantic", "a_view", "pose", "state", "fruit_vis"):
            same = bool(np.array_equal(a[k], b[k]))
            res[k] = {"identical": same}
            log(f"  {k}: identical={same}")
        a.close(); b.close()

        with open(os.path.join(OUT_DIR, "w3_determinism_probe.json"), "w") as f:
            json.dump(res, f, indent=2)
        with open(os.path.join(OUT_DIR, "w3_determinism_probe_log.txt"), "w") as f:
            f.write("\n".join(lines) + "\n")
        log(f"\nWrote {OUT_DIR}/w3_determinism_probe.json")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
