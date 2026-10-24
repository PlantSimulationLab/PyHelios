"""
W6 baseline 3 -- 3D Gaussian Splatting as a view-synthesis reference.

Runs in the `gsplat` env (gsplat 1.5.3, torch 2.7.0+cu128). Does **not** import
pyhelios, and does **not** touch `apple_tree_gaussian_splatting.py` at the repo
root (which is out of write scope, is hard-wired to its own 3-tree scene and its
own capture rig, and would need pyhelios and gsplat in the same env anyway). This
is a small, self-contained 3DGS fit on the same episodes the world model is
evaluated on, so the two numbers are directly comparable.

## What this comparison can and cannot mean

3DGS is **not** a world model. It reconstructs one static scene from posed views;
it has no action conditioning and no notion of a future. Putting it next to an
RSSM is only meaningful if you fix what information each method gets. Two
settings are run, and both are reported:

  **matched** -- the splat sees exactly the `context` frames the world model
      conditions on (5 by default), and is then asked to render the same target
      frames at their true poses. This is apples-to-apples on information, and is
      brutally hard for 3DGS: 5 views over a ~0.5 m baseline.

  **generous** -- the splat sees every frame in the episode EXCEPT the targets.
      This is an upper reference, not a fair fight: it gets ~27 posed views of the
      exact scene it must render, while the world model gets 5 and must also
      predict the camera motion's effect. If the world model beats *this*, the
      comparison is decisive; if it does not, that is expected and says nothing
      bad about the world model.

Both settings give 3DGS the **true camera pose** of every target frame, which the
world model is never given -- it only gets the action sequence.

## Initialisation

Gaussians are seeded by unprojecting the depth maps of the training views through
their own poses (real geometry, not random noise), which is the strongest honest
init available and again favours the baseline.
"""

import argparse
import json
import math
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.data import SequenceSampler
from yogesh_dev.world_model.evaluate import psnr as psnr_fn, ssim as ssim_fn

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w6")


def intrinsics(width, height, hfov_deg):
    f = (width / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
    K = torch.eye(3)
    K[0, 0] = f
    K[1, 1] = f
    K[0, 2] = width / 2.0
    K[1, 2] = height / 2.0
    return K


def unproject(depth, rgb, c2w, K, stride=2):
    """Depth map + camera-to-world -> world points and colours."""
    H, W = depth.shape
    ys, xs = np.mgrid[0:H:stride, 0:W:stride]
    d = depth[::stride, ::stride]
    m = d > 0
    xs, ys, d = xs[m], ys[m], d[m]
    fx, fy, cx, cy = K[0, 0].item(), K[1, 1].item(), K[0, 2].item(), K[1, 2].item()
    # depth here is the RadiationModel's ray distance; treat as z-depth. The
    # resulting point cloud is only an initialisation, so the small difference
    # between ray length and z-depth is refined away by the optimiser.
    cam = np.stack([(xs - cx) / fx * d, (ys - cy) / fy * d, d], axis=1)
    world = (c2w[:3, :3] @ cam.T).T + c2w[:3, 3]
    col = rgb[::stride, ::stride][m].astype(np.float32) / 255.0
    return world.astype(np.float32), col


def fit_and_render(train_idx, target_idx, ep, K, width, height, iters=1500,
                   device="cuda", lr_scale=1.0, log=print):
    from gsplat import rasterization

    rgb = ep["rgb"]
    depth = ep["depth"]
    c2w = ep["pose"]

    pts, cols = [], []
    for i in train_idx:
        p, c = unproject(depth[i].astype(np.float32), rgb[i], c2w[i], K, stride=2)
        pts.append(p)
        cols.append(c)
    pts = np.concatenate(pts)
    cols = np.concatenate(cols)
    if len(pts) > 120000:
        sel = np.random.default_rng(0).choice(len(pts), 120000, replace=False)
        pts, cols = pts[sel], cols[sel]
    if len(pts) < 100:
        return None

    means = torch.tensor(pts, device=device, requires_grad=True)
    n = means.shape[0]
    # scale init from mean nearest-neighbour spacing proxy: scene extent / n^(1/3)
    extent = float(np.linalg.norm(pts.max(0) - pts.min(0)))
    s0 = math.log(max(1e-4, extent / (n ** (1 / 3)) * 0.5))
    scales = torch.full((n, 3), s0, device=device, requires_grad=True)
    quats = torch.zeros(n, 4, device=device)
    quats[:, 0] = 1.0
    quats.requires_grad_(True)
    opac = torch.full((n,), 2.0, device=device, requires_grad=True)   # sigmoid(2)=0.88
    colors = torch.tensor(cols, device=device, requires_grad=True)

    opt = torch.optim.Adam([
        {"params": [means], "lr": 1.6e-4 * extent * lr_scale},
        {"params": [scales], "lr": 5e-3},
        {"params": [quats], "lr": 1e-3},
        {"params": [opac], "lr": 5e-2},
        {"params": [colors], "lr": 2.5e-2},
    ])

    w2c_train = torch.tensor(np.stack([np.linalg.inv(c2w[i]) for i in train_idx]),
                             device=device, dtype=torch.float32)
    gt_train = torch.tensor(np.stack([rgb[i] for i in train_idx]), device=device,
                            dtype=torch.float32) / 255.0
    Kb = K.to(device)[None].repeat(len(train_idx), 1, 1)

    for it in range(iters):
        out, _, _ = rasterization(
            means, torch.nn.functional.normalize(quats, dim=-1), torch.exp(scales),
            torch.sigmoid(opac), torch.sigmoid(colors), w2c_train, Kb, width, height,
            packed=False)
        loss = (out - gt_train).abs().mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if (it + 1) % max(1, iters // 3) == 0:
            log(f"      gsplat iter {it+1}/{iters} train L1={loss.item():.5f}")

    with torch.no_grad():
        w2c_t = torch.tensor(np.stack([np.linalg.inv(c2w[i]) for i in target_idx]),
                             device=device, dtype=torch.float32)
        Kt = K.to(device)[None].repeat(len(target_idx), 1, 1)
        pred, _, _ = rasterization(
            means, torch.nn.functional.normalize(quats, dim=-1), torch.exp(scales),
            torch.sigmoid(opac), torch.sigmoid(colors), w2c_t, Kt, width, height,
            packed=False)
    return pred.clamp(0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "output", "dataset"))
    ap.add_argument("--split", default="test")
    ap.add_argument("--context", type=int, default=5)
    ap.add_argument("--seq-len", type=int, default=32)
    ap.add_argument("--horizons", default="1,5,10,25")
    ap.add_argument("--n-episodes", type=int, default=4)
    ap.add_argument("--iters", type=int, default=1500)
    ap.add_argument("--image-size", type=int, default=None,
                    help="render/evaluate at this size instead of the stored size. "
                         "MUST match the world model's training resolution or the PSNR "
                         "numbers are not comparable -- PSNR rises under downsampling.")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    with open(os.path.join(args.data, "manifest.json")) as f:
        man = json.load(f)
    W, H = man["config"]["resolution"]
    stride = 1
    if args.image_size and args.image_size != W:
        if W % args.image_size:
            raise ValueError(f"--image-size {args.image_size} must divide stored {W}")
        stride = W // args.image_size
        W = H = args.image_size
    hfov = man["episodes"][0]["hfov_deg"]
    K = intrinsics(W, H, hfov)
    horizons = [int(h) for h in args.horizons.split(",")]
    log(f"gsplat baseline: {W}x{H} (stride {stride} from stored), HFOV={hfov:.2f} deg, "
        f"context={args.context}, horizons={horizons}, iters={args.iters}")

    sampler = SequenceSampler(args.data, args.split, args.seq_len, None,
                              growth_fraction=0.0, seed=7)
    device = "cuda"
    results = {"matched": {}, "generous": {}}

    for ei in range(min(args.n_episodes, len(sampler.view_records))):
        rec = sampler.view_records[ei]
        with np.load(os.path.join(args.data, rec["path"])) as z:
            ep = {"rgb": z["rgb"][:args.seq_len, ::stride, ::stride],
                  "depth": z["depth"][:args.seq_len, ::stride, ::stride].astype(np.float32),
                  "pose": z["pose"][:args.seq_len].astype(np.float64)}
        T = ep["rgb"].shape[0]
        target_idx = [args.context + h - 1 for h in horizons if args.context + h - 1 < T]
        if not target_idx:
            continue
        log(f"  [{ei+1}] {rec['path']} ({rec['family']}) targets={target_idx}")

        settings = {
            "matched": list(range(args.context)),
            "generous": [i for i in range(T) if i not in target_idx],
        }
        gt = torch.tensor(np.stack([ep["rgb"][i] for i in target_idx]),
                          device=device, dtype=torch.float32) / 255.0
        for name, train_idx in settings.items():
            log(f"    setting '{name}': {len(train_idx)} training views")
            pred = fit_and_render(train_idx, target_idx, ep, K, W, H,
                                  iters=args.iters, device=device, log=log)
            if pred is None:
                log("      skipped (no depth points)")
                continue
            p = pred.permute(0, 3, 1, 2) - 0.5
            g = gt.permute(0, 3, 1, 2) - 0.5
            ps = psnr_fn(p, g).cpu().numpy()
            ss = ssim_fn(p + 0.5, g + 0.5).cpu().numpy()
            for j, h in enumerate([h for h in horizons if args.context + h - 1 < T]):
                d = results[name].setdefault(f"t+{h}", {"psnr_db": [], "ssim": []})
                d["psnr_db"].append(float(ps[j]))
                d["ssim"].append(float(ss[j]))
                log(f"      t+{h:<3d} PSNR={ps[j]:6.2f}dB  SSIM={ss[j]:.4f}")

    summary = {name: {hz: {k: {"mean": float(np.mean(v)), "std": float(np.std(v)), "n": len(v)}
                           for k, v in rec.items()}
                      for hz, rec in tab.items()}
               for name, tab in results.items()}
    log("\n=== gsplat view-synthesis reference ===")
    for name, tab in summary.items():
        for hz, rec in tab.items():
            log(f"  {name:9s} {hz:5s} PSNR={rec['psnr_db']['mean']:6.2f}dB  "
                f"SSIM={rec['ssim']['mean']:.4f}  (n={rec['psnr_db']['n']})")

    out = {"config": {"context": args.context, "horizons": horizons, "iters": args.iters,
                      "n_episodes": args.n_episodes, "split": args.split,
                      "resolution": [W, H], "hfov_deg": hfov},
           "summary": summary,
           "caveat": "3DGS is given the TRUE camera pose of every target frame; the world "
                     "model is not. The 'generous' setting additionally gives it ~27 posed "
                     "views of the exact scene. It is an upper reference, not a peer."}
    with open(os.path.join(OUT_DIR, "gsplat_baseline.json"), "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(OUT_DIR, "gsplat_baseline_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    log(f"\nWrote {OUT_DIR}/gsplat_baseline.json")


if __name__ == "__main__":
    main()
