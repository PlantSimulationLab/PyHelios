"""
W4 acceptance: can the model overfit a single trajectory?

The plan's criterion is "overfits a single trajectory to near-zero reconstruction
loss. If it cannot, the model is wrong -- fix it before running the full
training." This script trains on exactly one recorded episode and then reports
what that loss means in interpretable units (PSNR, depth MAE in metres, semantic
mIoU) for both teacher-forced reconstruction and open-loop imagination, plus a
side-by-side image.

Note on the loss floor: with KL free bits at 1.0 nat and weights 0.5/0.1, the
total loss cannot go below 0.6 no matter how good the reconstruction is. So
"near zero" must be read on the reconstruction terms, not on `loss`.

Run (gsplat env):
    /home/yogesh/anaconda3/envs/gsplat/bin/python -m yogesh_dev.world_model.run_w4 \
        --steps 8000
"""

import argparse
import json
import os
import subprocess
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.data import SequenceSampler
from yogesh_dev.world_model.evaluate import psnr, ssim, miou, rollout, load_model
from yogesh_dev.world_model.rssm import symexp

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w4")
PY = "/home/yogesh/anaconda3/envs/gsplat/bin/python"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "output", "dataset"))
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--image-size", type=int, default=64)
    ap.add_argument("--seq-len", type=int, default=32)
    ap.add_argument("--tag", default="overfit")
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    train_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "train", args.tag)
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    if not args.skip_train:
        cmd = [PY, "-m", "yogesh_dev.world_model.train", "--overfit-one",
               "--data", args.data, "--steps", str(args.steps),
               "--image-size", str(args.image_size), "--seq-len", str(args.seq_len),
               "--log-every", "500", "--ckpt-every", str(args.steps), "--tag", args.tag]
        log(f"running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, cwd="/home/yogesh/PyHelios")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, ck = load_model(os.path.join(train_out, "ckpt.pt"), device)
    sampler = SequenceSampler(args.data, "train", args.seq_len, args.image_size,
                              growth_fraction=0.0, seed=0)
    rec, ep = next(sampler.iter_episodes("view", limit=1, seq_len=args.seq_len))
    data = model.preprocess({k: torch.from_numpy(v) for k, v in ep.items()}, device)
    log(f"\nepisode: {rec['path']} ({rec['family']}, seed {rec['orchard_seed']}, "
        f"stage {rec['stage_index']}), T={data['obs'].shape[1]}, "
        f"image_size={args.image_size}, trained {ck['step']} steps")

    results = {"episode": rec["path"], "steps": ck["step"], "image_size": args.image_size}

    # -- teacher-forced reconstruction ---------------------------------------
    with torch.no_grad():
        state = model.observe(data["obs"], data["action"])
        pred = model.decode(state["h"], state["z"])
    not_sky = ~data["sky"][0]
    d_err = (symexp(pred["depth_symlog"][0]) - symexp(data["depth_symlog"][0])).abs()
    recon = {
        "psnr_db": float(psnr(pred["rgb"][0], data["rgb"][0]).mean()),
        "ssim": float(ssim(pred["rgb"][0] + 0.5, data["rgb"][0] + 0.5).mean()),
        "depth_mae_m": float((d_err * not_sky).sum() / not_sky.sum().clamp_min(1)),
        "miou": float(np.nanmean(miou(pred["semantic_logits"][0], data["semantic"][0]).cpu().numpy())),
        "rgb_mse": float(((pred["rgb"][0] - data["rgb"][0]) ** 2).mean()),
    }
    results["teacher_forced_reconstruction"] = recon
    log("\n[teacher-forced reconstruction over the whole trajectory]")
    for k, v in recon.items():
        log(f"  {k:14s} {v:.5f}")

    # -- open-loop imagination on the same (memorised) trajectory ------------
    log("\n[open-loop imagination on the SAME trajectory, context=5]")
    imag = {}
    for hzn in (1, 5, 10, 25):
        t_abs = 5 + hzn - 1
        if t_abs >= data["obs"].shape[1]:
            continue
        with torch.no_grad():
            p = rollout(model, data, 5)
        idx = hzn - 1
        if idx >= p["rgb"].shape[1]:
            continue
        ns = ~data["sky"][:, t_abs]
        de = (symexp(p["depth_symlog"][:, idx]) - symexp(data["depth_symlog"][:, t_abs])).abs()
        imag[f"t+{hzn}"] = {
            "psnr_db": float(psnr(p["rgb"][:, idx], data["rgb"][:, t_abs]).mean()),
            "ssim": float(ssim(p["rgb"][:, idx] + 0.5, data["rgb"][:, t_abs] + 0.5).mean()),
            "depth_mae_m": float((de * ns).sum() / ns.sum().clamp_min(1)),
            "miou": float(np.nanmean(miou(p["semantic_logits"][:, idx],
                                          data["semantic"][:, t_abs]).cpu().numpy())),
        }
        r = imag[f"t+{hzn}"]
        log(f"  t+{hzn:<3d} PSNR={r['psnr_db']:6.2f}dB  SSIM={r['ssim']:.4f}  "
            f"depthMAE={r['depth_mae_m']:.3f}m  mIoU={r['miou']:.4f}")
    results["imagination"] = imag

    # -- acceptance ----------------------------------------------------------
    ok = recon["psnr_db"] > 25.0 and recon["miou"] > 0.7
    results["acceptance"] = {
        "criterion": "teacher-forced reconstruction PSNR > 25 dB AND semantic mIoU > 0.7 "
                     "on the single memorised trajectory",
        "passed": bool(ok),
        "psnr_db": recon["psnr_db"], "miou": recon["miou"]}
    log(f"\nACCEPTANCE (recon PSNR > 25 dB and mIoU > 0.7): {ok}  "
        f"[PSNR {recon['psnr_db']:.2f} dB, mIoU {recon['miou']:.4f}]")

    # -- qualitative ---------------------------------------------------------
    try:
        import imageio.v3 as iio
        ts = [0, 8, 16, 24]
        ts = [t for t in ts if t < data["obs"].shape[1]]
        gt = np.concatenate([((data["rgb"][0, t] + 0.5).clamp(0, 1) * 255)
                             .permute(1, 2, 0).cpu().numpy().astype(np.uint8) for t in ts], 1)
        pr = np.concatenate([((pred["rgb"][0, t] + 0.5).clamp(0, 1) * 255)
                             .permute(1, 2, 0).cpu().numpy().astype(np.uint8) for t in ts], 1)
        iio.imwrite(os.path.join(OUT_DIR, "overfit_recon.png"), np.concatenate([gt, pr], 0))
        log(f"wrote {OUT_DIR}/overfit_recon.png (top = Helios, bottom = model)")
    except Exception as e:
        log(f"qualitative render failed: {type(e).__name__}: {e}")

    with open(os.path.join(OUT_DIR, "w4_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(OUT_DIR, "w4_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    log(f"Wrote {OUT_DIR}/w4_results.json")
    return results


if __name__ == "__main__":
    main()
