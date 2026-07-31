"""
Round 2 / R2-H -- how much of the depth gap is blur, and nothing else?

R2-C measured that the model's reconstruction carries 0.113 of the ground truth's
spatial gradient energy, and that its depth MAE (1.03 m) is worse than
copy-last-frame (0.65 m) at every distance. Those two facts might be the same
fact. This script separates them with a model-free control:

    take the GROUND-TRUTH frame -- the perfect prediction -- blur it, and score it.

If a blurred copy of the correct answer already scores worse than copy-last on
depth MAE at the blur level the model actually operates at, then the model's
depth deficit is a resolution/sharpness deficit and *nothing else*: not the
dynamics, not the orchard diversity, not the action conditioning. Improving
prediction accuracy without improving sharpness cannot help.

Blur is applied in the space the model works in -- symlog depth and [-0.5, 0.5]
RGB -- and the score is computed exactly as evaluate.py computes it: MAE in
metres over non-sky ground-truth pixels.

Runs in the `gsplat` env; needs no checkpoint.
"""

import argparse
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.rssm import WorldModel, symexp, N_SEMANTIC_CLASSES
from yogesh_dev.world_model.evaluate import psnr, miou
from yogesh_dev.world_model.data import SequenceSampler


def gauss1d(sigma, device):
    r = max(1, int(3 * sigma))
    x = torch.arange(-r, r + 1, dtype=torch.float32, device=device)
    k = torch.exp(-(x ** 2) / (2 * sigma ** 2))
    return (k / k.sum()), r


def blur(x, sigma):
    """Separable Gaussian blur over the last two dims of (N,C,H,W)."""
    if sigma <= 0:
        return x
    k, r = gauss1d(sigma, x.device)
    C = x.shape[1]
    kx = k.view(1, 1, 1, -1).expand(C, 1, 1, -1)
    ky = k.view(1, 1, -1, 1).expand(C, 1, -1, 1)
    x = F.conv2d(F.pad(x, (r, r, 0, 0), mode="replicate"), kx, groups=C)
    x = F.conv2d(F.pad(x, (0, 0, r, r), mode="replicate"), ky, groups=C)
    return x


def sharpness_ratio(p, g):
    def gr(x):
        return (x[..., 1:, :] - x[..., :-1, :]).abs().mean() + \
               (x[..., :, 1:] - x[..., :, :-1]).abs().mean()
    return float(gr(p) / gr(g).clamp_min(1e-9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "output", "dataset"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "output", "r2"))
    ap.add_argument("--split", default="test")
    ap.add_argument("--image-size", type=int, default=64)
    ap.add_argument("--seq-len", type=int, default=32)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--n-batches", type=int, default=24)
    ap.add_argument("--context", type=int, default=5)
    ap.add_argument("--sigmas", default="0,0.5,1,1.5,2,3,4,6")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    sigmas = [float(s) for s in args.sigmas.split(",")]
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    sampler = SequenceSampler(args.data, args.split, args.seq_len, args.image_size,
                              growth_fraction=0.0, seed=1234)
    acc = {s: {"depth_mae": [], "psnr": [], "miou": [], "sharp": []} for s in sigmas}
    copy_acc = {"depth_mae": [], "psnr": [], "miou": []}

    with torch.no_grad():
        for _ in range(args.n_batches):
            b = sampler.sample_batch(args.batch_size)
            data = WorldModel.preprocess(
                {k: torch.from_numpy(v) if isinstance(v, np.ndarray) else v
                 for k, v in b.items()}, device)
            t = args.context                       # the frame evaluate.py scores as t+1
            gt_rgb = data["rgb"][:, t]
            gt_dsl = data["depth_symlog"][:, t]
            gt_sem = data["semantic"][:, t]
            not_sky = ~data["sky"][:, t]
            n_valid = not_sky.flatten(1).sum(1).clamp_min(1)
            gt_oh = F.one_hot(gt_sem, N_SEMANTIC_CLASSES).permute(0, 3, 1, 2).float()

            for s in sigmas:
                p_rgb = blur(gt_rgb, s)
                p_dsl = blur(gt_dsl.unsqueeze(1), s).squeeze(1)
                p_sem = blur(gt_oh, s)
                derr = (symexp(p_dsl) - symexp(gt_dsl)).abs()
                acc[s]["depth_mae"].append(
                    float(((derr * not_sky).flatten(1).sum(1) / n_valid).mean()))
                acc[s]["psnr"].append(float(psnr(p_rgb, gt_rgb).mean()))
                acc[s]["miou"].append(float(np.nanmean(miou(p_sem, gt_sem).cpu().numpy())))
                acc[s]["sharp"].append(sharpness_ratio(p_rgb, gt_rgb))

            # copy-last, for the reference line
            c_rgb = data["rgb"][:, t - 1]
            c_dsl = data["depth_symlog"][:, t - 1]
            c_oh = F.one_hot(data["semantic"][:, t - 1], N_SEMANTIC_CLASSES).permute(0, 3, 1, 2).float()
            cerr = (symexp(c_dsl) - symexp(gt_dsl)).abs()
            copy_acc["depth_mae"].append(
                float(((cerr * not_sky).flatten(1).sum(1) / n_valid).mean()))
            copy_acc["psnr"].append(float(psnr(c_rgb, gt_rgb).mean()))
            copy_acc["miou"].append(float(np.nanmean(miou(c_oh, gt_sem).cpu().numpy())))

    res = {"split": args.split, "image_size": args.image_size, "context": args.context,
           "note": "the 'prediction' here is the GROUND TRUTH frame, blurred. It is an "
                   "upper bound on what any predictor with that sharpness can score.",
           "copy_last": {k: float(np.mean(v)) for k, v in copy_acc.items()},
           "blurred_ground_truth": {}}
    log(f"Blurred-ground-truth control, {args.split} split, {args.image_size}x{args.image_size}")
    log(f"  the 'prediction' is the CORRECT frame, blurred by sigma pixels.")
    log(f"  {'sigma':>6} {'sharpness':>10} {'depth MAE m':>12} {'PSNR dB':>9} {'mIoU':>7}")
    for s in sigmas:
        r = {k: float(np.mean(v)) for k, v in acc[s].items()}
        res["blurred_ground_truth"][str(s)] = r
        log(f"  {s:>6.1f} {r['sharp']:>10.3f} {r['depth_mae']:>12.3f} "
            f"{r['psnr']:>9.2f} {r['miou']:>7.4f}")
    c = res["copy_last"]
    log(f"  {'copy-last':>6s} {1.0:>10.3f} {c['depth_mae']:>12.3f} {c['psnr']:>9.2f} "
        f"{c['miou']:>7.4f}")

    with open(os.path.join(args.out, "r2_blur_baseline.json"), "w") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(args.out, "r2_blur_baseline_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    log(f"\nwrote {args.out}/r2_blur_baseline.json")


if __name__ == "__main__":
    main()
