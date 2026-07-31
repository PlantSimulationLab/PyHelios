"""
Round 2 / R2-C -- where does the error actually come from?

Round 1's headline negative is that the model loses to copy-last-frame on depth
MAE at *every* horizon, including t+1. Two very different causes produce that:

  (a) the DYNAMICS are wrong -- the prior cannot predict one step ahead, so the
      imagined state is bad even though the model could represent the frame; or
  (b) the REPRESENTATION is the bottleneck -- the encoder/decoder cannot render a
      sharp orchard at all, so even a perfect one-step prediction decodes to a
      blur.

The two call for opposite fixes. (a) says train longer / more data / better
transition model. (b) says more capacity or more resolution, and no amount of
extra orchards will help.

The measurement that separates them is the teacher-forced POSTERIOR
reconstruction on held-out orchards: give the model the real frame at time t,
encode it, decode it straight back. That is the best this architecture can
possibly do at this size -- an upper bound on every rollout number. Comparing it
to the one-step open-loop rollout attributes the gap.

    posterior recon   <-- representation ceiling (no dynamics involved)
    open-loop t+1     <-- ceiling + one step of dynamics error
    copy-last t+1     <-- the baseline both must beat

Runs in the `gsplat` env.
"""

import argparse
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.rssm import symexp, N_SEMANTIC_CLASSES
from yogesh_dev.world_model.evaluate import load_model, psnr, ssim, miou, rollout
from yogesh_dev.world_model.data import SequenceSampler


SEM_NAMES = ["ground", "fruit", "leaf", "shoot", "petiole", "peduncle", "sky"]


@torch.no_grad()
def class_stats(pred_cls, gt_cls, n=N_SEMANTIC_CLASSES):
    """Per-class intersection / union / gt-pixels / pred-pixels, summed over the batch.

    mIoU on its own does not say WHY it is low. With 7 classes of which two cover
    <0.3% of pixels, a model that only ever emits ground/leaf/sky scores 0 on
    every class it never predicts, and those zeros are averaged in -- so a
    perfectly good three-class segmenter is capped near 3/6. This breakdown makes
    that visible instead of leaving mIoU as an opaque number.
    """
    out = {}
    for c in range(n):
        pc, tc = (pred_cls == c), (gt_cls == c)
        out[c] = {"inter": float((pc & tc).sum()), "union": float((pc | tc).sum()),
                  "gt": float(tc.sum()), "pred": float(pc.sum())}
    return out


@torch.no_grad()
def score_frame(p_rgb, p_dsl, p_sem_logits, p_fruit, data, t_abs, is_copy=False):
    gt_rgb = data["rgb"][:, t_abs]
    gt_dsl = data["depth_symlog"][:, t_abs]
    gt_sem = data["semantic"][:, t_abs]
    gt_fruit = data["fruit_vis"][:, t_abs]
    not_sky = ~data["sky"][:, t_abs]
    n_valid = not_sky.flatten(1).sum(1).clamp_min(1)
    derr = (symexp(p_dsl) - symexp(gt_dsl)).abs()
    if is_copy:
        oh = F.one_hot(p_sem_logits.long(), N_SEMANTIC_CLASSES).permute(0, 3, 1, 2).float()
        m = miou(oh, gt_sem)
        pred_cls = p_sem_logits.long()
    else:
        m = miou(p_sem_logits, gt_sem)
        pred_cls = p_sem_logits.argmax(1)
    return {
        "psnr_db": float(psnr(p_rgb, gt_rgb).mean()),
        "ssim": float(ssim(p_rgb + 0.5, gt_rgb + 0.5).mean()),
        "depth_mae_m": float(((derr * not_sky).flatten(1).sum(1) / n_valid).mean()),
        "miou": float(np.nanmean(m.cpu().numpy())),
        "fruit_vis_mae": float(((symexp(p_fruit) - symexp(gt_fruit)) / 100.0).abs().mean()),
        "sharpness_ratio": sharpness_ratio(p_rgb, gt_rgb),
        "_cls": class_stats(pred_cls, gt_sem),
        "_depth_bins": depth_error_by_range(symexp(p_dsl), symexp(gt_dsl), not_sky),
    }


DEPTH_BIN_EDGES = (0.0, 2.0, 4.0, 8.0, 1e9)


@torch.no_grad()
def depth_error_by_range(p_m, gt_m, not_sky):
    """Absolute depth error split by GROUND-TRUTH distance.

    The model is trained on MSE in symlog depth but scored on MAE in metres. The
    two disagree: symlog compresses distance, so a metre of error at 16 m costs
    the loss about a fifth of what it costs at 1 m, while the metric charges full
    price. If the error is concentrated in the far bins, that mismatch -- not the
    dynamics and not the data -- is part of why the model loses to copy-last.
    """
    out = []
    for lo, hi in zip(DEPTH_BIN_EDGES[:-1], DEPTH_BIN_EDGES[1:]):
        m = not_sky & (gt_m >= lo) & (gt_m < hi)
        n = float(m.sum())
        err = float(((p_m - gt_m).abs() * m).sum())
        out.append({"lo": lo, "hi": hi, "abs_err_sum": err, "n": n})
    return out


@torch.no_grad()
def sharpness_ratio(p_rgb, gt_rgb):
    """Mean |spatial gradient| of the prediction / the same for ground truth.

    Round 1 described the model's output as "low-frequency smears" from looking at
    the rollout strips. This is that claim as a number: 1.0 means the prediction
    carries as much high-frequency detail as the real frame, and values well below
    1.0 mean it is blurred.
    """
    def g(x):
        return (x[..., 1:, :] - x[..., :-1, :]).abs().mean() + \
               (x[..., :, 1:] - x[..., :, :-1]).abs().mean()
    return float(g(p_rgb) / g(gt_rgb).clamp_min(1e-9))


@torch.no_grad()
def run(model, sampler, device, context, n_batches, batch_size, log):
    acc = {"posterior_recon": [], "openloop_t1": [], "copy_last_t1": []}
    for _ in range(n_batches):
        b = sampler.sample_batch(batch_size)
        data = model.preprocess({k: torch.from_numpy(v) if isinstance(v, np.ndarray) else v
                                 for k, v in b.items()}, device)
        T = data["obs"].shape[1]
        if T < context + 1:
            continue
        # -- teacher-forced posterior reconstruction, scored on the SAME frame the
        #    open-loop rollout is scored on, so the two are directly comparable.
        post = model.observe(data["obs"], data["action"])
        dec = model.decode(post["h"], post["z"])
        t_abs = context
        acc["posterior_recon"].append(score_frame(
            dec["rgb"][:, t_abs], dec["depth_symlog"][:, t_abs],
            dec["semantic_logits"][:, t_abs], dec["fruit_vis"][:, t_abs], data, t_abs))
        # -- open-loop one step
        pred = rollout(model, data, context)
        acc["openloop_t1"].append(score_frame(
            pred["rgb"][:, 0], pred["depth_symlog"][:, 0],
            pred["semantic_logits"][:, 0], pred["fruit_vis"][:, 0], data, t_abs))
        # -- copy the last observed frame
        acc["copy_last_t1"].append(score_frame(
            data["rgb"][:, context - 1], data["depth_symlog"][:, context - 1],
            data["semantic"][:, context - 1], data["fruit_vis"][:, context - 1],
            data, t_abs, is_copy=True))
    out = {}
    for k, v in acc.items():
        if not v:
            continue
        rec = {kk: float(np.nanmean([r[kk] for r in v]))
               for kk in v[0] if not kk.startswith("_")}
        # Per-class IoU is pooled over the WHOLE split (sum intersections, sum
        # unions) rather than averaged per frame: a per-frame average would let a
        # single frame containing three fruit pixels dominate the fruit IoU.
        per_cls = {}
        for c in range(N_SEMANTIC_CLASSES):
            inter = sum(r["_cls"][c]["inter"] for r in v)
            union = sum(r["_cls"][c]["union"] for r in v)
            gt = sum(r["_cls"][c]["gt"] for r in v)
            pr = sum(r["_cls"][c]["pred"] for r in v)
            tot = sum(sum(r["_cls"][cc]["gt"] for cc in range(N_SEMANTIC_CLASSES)) for r in v)
            per_cls[SEM_NAMES[c]] = {
                "iou": (inter / union) if union > 0 else None,
                "gt_pixel_fraction": gt / max(1.0, tot),
                "pred_pixel_fraction": pr / max(1.0, tot),
            }
        rec["per_class"] = per_cls
        rec["n_classes_ever_predicted"] = sum(
            1 for c in per_cls.values() if c["pred_pixel_fraction"] > 1e-6)
        bins = []
        for i in range(len(DEPTH_BIN_EDGES) - 1):
            s = sum(r["_depth_bins"][i]["abs_err_sum"] for r in v)
            n = sum(r["_depth_bins"][i]["n"] for r in v)
            tot_n = sum(sum(b["n"] for b in r["_depth_bins"]) for r in v)
            bins.append({"lo": DEPTH_BIN_EDGES[i], "hi": DEPTH_BIN_EDGES[i + 1],
                         "mae_m": (s / n) if n else None,
                         "pixel_fraction": n / max(1.0, tot_n)})
        rec["depth_mae_by_range"] = bins
        out[k] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", action="append", required=True)
    ap.add_argument("--tag", action="append", default=None)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "output", "dataset"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "output", "r2"))
    ap.add_argument("--split", default="test")
    ap.add_argument("--context", type=int, default=5)
    ap.add_argument("--seq-len", type=int, default=32)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--n-batches", type=int, default=24)
    ap.add_argument("--name", default="r2_recon_floor")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    tags = args.tag or [f"model{i}" for i in range(len(args.ckpt))]
    results = {"split": args.split, "context": args.context, "models": {}}
    for ck_path, tag in zip(args.ckpt, tags):
        model, ck = load_model(ck_path, device)
        img = ck["args"]["image_size"]
        sampler = SequenceSampler(args.data, args.split, args.seq_len, img,
                                  growth_fraction=0.0, seed=1234)
        r = run(model, sampler, device, args.context, args.n_batches, args.batch_size, log)
        r["ckpt"] = ck_path
        r["step"] = int(ck["step"])
        results["models"][tag] = r
        log(f"\n=== {tag}  (step {ck['step']}, {img}x{img}, split={args.split}) ===")
        log(f"  {'variant':18s} {'PSNR dB':>8} {'SSIM':>7} {'depth MAE m':>12} "
            f"{'mIoU':>7} {'fruitMAE':>9}")
        for k in ("posterior_recon", "openloop_t1", "copy_last_t1"):
            if k not in r:
                continue
            v = r[k]
            log(f"  {k:18s} {v['psnr_db']:8.2f} {v['ssim']:7.4f} {v['depth_mae_m']:12.3f} "
                f"{v['miou']:7.4f} {v['fruit_vis_mae']:9.4f}")
        log(f"  per-class IoU (pooled over the split); "
            f"gt% / pred% = share of pixels in ground truth / prediction")
        log(f"    {'class':10s} " + "".join(f"{k:>26s}"
                                            for k in ("posterior_recon", "copy_last_t1")))
        for name in SEM_NAMES:
            cells = ""
            for k in ("posterior_recon", "copy_last_t1"):
                c = r[k]["per_class"][name]
                iou = "  --  " if c["iou"] is None else f"{c['iou']:.3f}"
                cells += f"  IoU {iou}  gt {c['gt_pixel_fraction']*100:5.2f}% " \
                         f"pred {c['pred_pixel_fraction']*100:5.2f}%"
            log(f"    {name:10s}{cells}")
        log(f"  classes the model ever predicts: "
            f"{r['posterior_recon']['n_classes_ever_predicted']} of {N_SEMANTIC_CLASSES}")
        log(f"  depth MAE by ground-truth distance (posterior recon / copy-last):")
        for i, b in enumerate(r["posterior_recon"]["depth_mae_by_range"]):
            c = r["copy_last_t1"]["depth_mae_by_range"][i]
            hi = "inf" if b["hi"] > 1e8 else f"{b['hi']:.0f}"
            mm = "  --  " if b["mae_m"] is None else f"{b['mae_m']:.3f}"
            cm = "  --  " if c["mae_m"] is None else f"{c['mae_m']:.3f}"
            log(f"    {b['lo']:>4.0f}-{hi:>4s} m  ({b['pixel_fraction']*100:5.1f}% of pixels)  "
                f"{mm} m   vs copy-last {cm} m")
        log(f"  RGB sharpness (mean |gradient| relative to ground truth): "
            f"posterior recon {r['posterior_recon']['sharpness_ratio']:.3f}, "
            f"open-loop t+1 {r['openloop_t1']['sharpness_ratio']:.3f}, "
            f"copy-last {r['copy_last_t1']['sharpness_ratio']:.3f}")
        if "posterior_recon" in r and "openloop_t1" in r:
            a, b = r["posterior_recon"], r["openloop_t1"]
            log(f"  attribution: of the depth error at t+1, "
                f"{a['depth_mae_m']:.3f} m is already present in the teacher-forced "
                f"reconstruction ({100*a['depth_mae_m']/max(1e-9,b['depth_mae_m']):.0f}% "
                f"of it); one step of dynamics adds "
                f"{b['depth_mae_m']-a['depth_mae_m']:+.3f} m.")

    with open(os.path.join(args.out, f"{args.name}.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(args.out, f"{args.name}_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    log(f"\nwrote {args.out}/{args.name}.json")


if __name__ == "__main__":
    main()
