"""
W5 deliverable: training / validation curves from `history.jsonl`.

Plots the four reconstruction terms separately from the KL terms, because the
total loss is misleading here: the KL rises steadily as the model uses more
latent capacity, so `loss` can go UP while every reconstruction term goes DOWN.
That is also why `train.py`'s best-checkpoint-by-total-loss selected step 5000
even though reconstruction kept improving until ~15k -- documented, not hidden.

Run (gsplat env):
    /home/yogesh/anaconda3/envs/gsplat/bin/python -m yogesh_dev.world_model.plot_curves
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w5")


def load(path):
    tr, va = [], []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            (tr if r["split"] == "train" else va).append(r)
    return tr, va


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", default="main,noaction")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "train")
    keys = ["rgb", "depth", "semantic", "fruit", "kl_dyn", "loss"]
    tags = [t for t in args.tags.split(",") if os.path.isfile(os.path.join(base, t, "history.jsonl"))]

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    summary = {}
    for tag in tags:
        tr, va = load(os.path.join(base, tag, "history.jsonl"))
        summary[tag] = {
            "n_train_points": len(tr), "n_val_points": len(va),
            "final_step": tr[-1]["step"] if tr else None,
            "best_val_recon_step": None, "best_val_recon": None,
        }
        if va:
            recon = [v["rgb"] + v["depth"] + v["semantic"] + v["fruit"] for v in va]
            i = int(np.argmin(recon))
            summary[tag]["best_val_recon_step"] = va[i]["step"]
            summary[tag]["best_val_recon"] = float(recon[i])
            summary[tag]["final_val_recon"] = float(recon[-1])
        for ax, k in zip(axes.ravel(), keys):
            ax.plot([r["step"] for r in tr], [r[k] for r in tr], label=f"{tag} train", lw=1)
            if va:
                ax.plot([r["step"] for r in va], [r[k] for r in va], "--", label=f"{tag} val", lw=1.5)
            ax.set_title(k)
            ax.set_xlabel("step")
            ax.grid(alpha=0.3)
    axes.ravel()[0].legend(fontsize=7)
    fig.suptitle("World model training / validation curves "
                 "(val reconstruction bottoms out ~15k steps, then overfits 12 orchards)")
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "curves.png")
    fig.savefig(path, dpi=110)
    with open(os.path.join(OUT_DIR, "curve_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
