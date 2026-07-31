"""
W6 -- Evaluation. Runs in the `gsplat` env.

The point of a world model is multi-step *imagination*, not single-step
reconstruction, so everything here is measured as a function of rollout horizon:
condition on `--context` real frames (posterior), then roll the prior forward
with the recorded actions and decode at every step.

## What is measured

  R1  Open-loop rollout quality vs horizon -- RGB PSNR and SSIM, depth MAE in
      metres, semantic mIoU, fruit-visibility MAE at t+1, t+5, t+10, t+25.
  R2  Action fidelity -- the same rollout with (a) the true actions,
      (b) actions zeroed, (c) actions taken from a DIFFERENT episode. If the
      model uses actions at all, (a) must beat both (b) and (c).
  R3  Counterfactual growth -- the same protocol on growth episodes, where the
      action is days advanced rather than a camera move.
  R4  Baselines -- copy-last-frame, plus (if `--noaction-ckpt` is given) a model
      that was TRAINED with actions zeroed, which is the real no-action ablation.

## LPIPS

The plan asks for LPIPS. `lpips` is not installed in the `gsplat` env and this
machine has no network access to install it, so it is **not reported**. SSIM is
computed instead (implemented here, no extra dependency) and the substitution is
stated rather than silently made. PSNR and depth MAE are unaffected.
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
from yogesh_dev.world_model.data import SequenceSampler

DEFAULT_HORIZONS = (1, 5, 10, 25)


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
def psnr(pred, target, data_range=1.0):
    """pred/target in [-0.5,0.5] -> PSNR in dB, per frame."""
    mse = ((pred - target) ** 2).flatten(1).mean(1).clamp_min(1e-12)
    return (10.0 * torch.log10(data_range ** 2 / mse))


def _gauss_kernel(size=11, sigma=1.5, device="cpu"):
    c = torch.arange(size, dtype=torch.float32, device=device) - size // 2
    g = torch.exp(-(c ** 2) / (2 * sigma ** 2))
    g = g / g.sum()
    return (g[:, None] @ g[None, :])


def ssim(pred, target, data_range=1.0, size=11, sigma=1.5):
    """Standard SSIM with a Gaussian window, per frame. pred/target (N,C,H,W)."""
    C = pred.shape[1]
    k = _gauss_kernel(size, sigma, pred.device).expand(C, 1, size, size).contiguous()
    pad = size // 2
    mu1 = F.conv2d(pred, k, padding=pad, groups=C)
    mu2 = F.conv2d(target, k, padding=pad, groups=C)
    mu1s, mu2s, mu12 = mu1 ** 2, mu2 ** 2, mu1 * mu2
    s1 = F.conv2d(pred * pred, k, padding=pad, groups=C) - mu1s
    s2 = F.conv2d(target * target, k, padding=pad, groups=C) - mu2s
    s12 = F.conv2d(pred * target, k, padding=pad, groups=C) - mu12
    c1, c2 = (0.01 * data_range) ** 2, (0.03 * data_range) ** 2
    m = ((2 * mu12 + c1) * (2 * s12 + c2)) / ((mu1s + mu2s + c1) * (s1 + s2 + c2))
    return m.flatten(1).mean(1)


def miou(pred_logits, target, n_classes=N_SEMANTIC_CLASSES):
    """Mean IoU over classes PRESENT in either prediction or target, per frame.

    Classes absent from both are excluded rather than counted as IoU=1 -- with 7
    classes and two of them (petiole, peduncle) covering <0.3% of pixels, the
    'absent counts as perfect' convention would inflate mIoU by ~0.3 for free.
    """
    pred = pred_logits.argmax(1)
    out = []
    for i in range(pred.shape[0]):
        ious = []
        p, t = pred[i], target[i]
        for c in range(n_classes):
            pc, tc = (p == c), (t == c)
            union = (pc | tc).sum()
            if union == 0:
                continue
            ious.append(((pc & tc).sum().float() / union.float()).item())
        out.append(float(np.mean(ious)) if ious else float("nan"))
    return torch.tensor(out, device=pred_logits.device)


# ---------------------------------------------------------------------------
# rollout
# ---------------------------------------------------------------------------
@torch.no_grad()
def rollout(model, data, context, actions_override=None):
    """Condition on `context` frames, then imagine the rest with `actions`.

    Returns predictions for the imagined steps only, shape (B, T-context, ...).
    `actions_override` replaces the recorded actions during imagination (used for
    the zeroed / shuffled ablations); the context phase always uses the true
    actions, because the ablation is about *prediction*, not about corrupting the
    evidence the model conditions on.
    """
    obs, act = data["obs"], data["action"]
    B, T = obs.shape[:2]
    ctx = model.observe(obs[:, :context], act[:, :context])
    h, z = ctx["h"][:, -1], ctx["z"][:, -1]
    fut = act[:, context - 1:T - 1]
    if actions_override is not None:
        fut = actions_override[:, context - 1:T - 1]
    hs, zs = model.imagine(h, z, fut)
    return model.decode(hs, zs)


@torch.no_grad()
def copy_last_baseline(data, context, n_future):
    """Repeat the last observed frame for every future step."""
    return {
        "rgb": data["rgb"][:, context - 1:context].repeat(1, n_future, 1, 1, 1),
        "depth_symlog": data["depth_symlog"][:, context - 1:context].repeat(1, n_future, 1, 1),
        "semantic_onehot": data["semantic"][:, context - 1:context].repeat(1, n_future, 1, 1),
        "fruit_vis": data["fruit_vis"][:, context - 1:context].repeat(1, n_future),
    }


def score_predictions(pred, data, context, horizons, is_baseline=False):
    """Per-horizon metrics. `pred` covers steps context..T-1."""
    T = data["obs"].shape[1]
    out = {}
    for hzn in horizons:
        idx = context - 1 + hzn - (context - 1) - 1  # index within pred
        t_abs = context + hzn - 1
        if t_abs >= T or idx < 0 or idx >= pred["rgb"].shape[1]:
            continue
        gt_rgb = data["rgb"][:, t_abs]
        gt_depth_sl = data["depth_symlog"][:, t_abs]
        gt_sem = data["semantic"][:, t_abs]
        gt_fruit = data["fruit_vis"][:, t_abs]

        p_rgb = pred["rgb"][:, idx]
        p_depth_sl = pred["depth_symlog"][:, idx]
        p_fruit = pred["fruit_vis"][:, idx]

        depth_mae = (symexp(p_depth_sl) - symexp(gt_depth_sl)).abs().flatten(1).mean(1)
        rec = {
            "psnr_db": float(psnr(p_rgb, gt_rgb).mean()),
            "ssim": float(ssim(p_rgb + 0.5, gt_rgb + 0.5).mean()),
            "depth_mae_m": float(depth_mae.mean()),
            "fruit_vis_mae": float((p_fruit - gt_fruit).abs().mean()),
        }
        if is_baseline:
            # baseline "semantic" is a copied class map, not logits
            p_sem = pred["semantic_onehot"][:, idx]
            oh = F.one_hot(p_sem.long(), N_SEMANTIC_CLASSES).permute(0, 3, 1, 2).float()
            rec["miou"] = float(np.nanmean(miou(oh, gt_sem).cpu().numpy()))
        else:
            rec["miou"] = float(np.nanmean(miou(pred["semantic_logits"][:, idx], gt_sem).cpu().numpy()))
        out[f"t+{hzn}"] = rec
    return out


def _merge(accum, new):
    for hz, rec in new.items():
        a = accum.setdefault(hz, {})
        for k, v in rec.items():
            a.setdefault(k, []).append(v)


def _finalize(accum):
    return {hz: {k: {"mean": float(np.nanmean(v)), "std": float(np.nanstd(v)), "n": len(v)}
                 for k, v in rec.items()} for hz, rec in accum.items()}


def run_eval(model, sampler, device, context, horizons, n_batches, batch_size,
             episode_type="view", noaction_model=None, log=print):
    variants = {"full": {}, "zero_action": {}, "shuffled_action": {}, "copy_last": {}}
    if noaction_model is not None:
        variants["noaction_model"] = {}
    T_needed = context + max(horizons)

    for _ in range(n_batches):
        b = sampler.sample_batch(batch_size)
        if episode_type == "growth":
            pass
        data = model.preprocess({k: torch.from_numpy(v) if isinstance(v, np.ndarray) else v
                                 for k, v in b.items()}, device)
        T = data["obs"].shape[1]
        if T < T_needed:
            continue
        n_future = T - context

        pred = rollout(model, data, context)
        _merge(variants["full"], score_predictions(pred, data, context, horizons))

        zero_act = torch.zeros_like(data["action"])
        _merge(variants["zero_action"],
               score_predictions(rollout(model, data, context, zero_act), data, context, horizons))

        perm = torch.randperm(data["action"].shape[0], device=device)
        _merge(variants["shuffled_action"],
               score_predictions(rollout(model, data, context, data["action"][perm]),
                                 data, context, horizons))

        _merge(variants["copy_last"],
               score_predictions(copy_last_baseline(data, context, n_future),
                                 data, context, horizons, is_baseline=True))

        if noaction_model is not None:
            _merge(variants["noaction_model"],
                   score_predictions(rollout(noaction_model, data, context), data, context, horizons))

    return {k: _finalize(v) for k, v in variants.items() if v}


def load_model(ckpt_path, device):
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    a = ck["args"]
    m = WorldModel(action_dim=5, image_size=a["image_size"], base=a["base_channels"],
                   deter=a["deter"], stoch=a["stoch"], classes=a["classes"],
                   free_bits=a["free_bits"]).to(device)
    m.load_state_dict(ck["model"])
    m.eval()
    return m, ck


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--noaction-ckpt", default=None)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "output", "dataset"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "output", "w6"))
    ap.add_argument("--split", default="test")
    ap.add_argument("--context", type=int, default=5)
    ap.add_argument("--seq-len", type=int, default=32)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--n-batches", type=int, default=16)
    ap.add_argument("--horizons", default="1,5,10,25")
    ap.add_argument("--qualitative", type=int, default=2, help="episodes to render as PNG strips")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    horizons = tuple(int(h) for h in args.horizons.split(","))
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    model, ck = load_model(args.ckpt, device)
    log(f"loaded {args.ckpt} (step {ck['step']}, image_size {ck['args']['image_size']})")
    noaction = None
    if args.noaction_ckpt and os.path.isfile(args.noaction_ckpt):
        noaction, nck = load_model(args.noaction_ckpt, device)
        log(f"loaded no-action ablation {args.noaction_ckpt} (step {nck['step']})")
    else:
        log("no-action ABLATION MODEL NOT PROVIDED -- reporting the eval-time "
            "zero_action variant only, which is a weaker control")

    img = ck["args"]["image_size"]
    results = {"ckpt": args.ckpt, "step": ck["step"], "split": args.split,
               "context": args.context, "horizons": list(horizons),
               "image_size": img, "note_lpips": "LPIPS not reported: `lpips` is not "
               "installed in the gsplat env and no network access is available. "
               "SSIM is reported instead."}

    # -- R1/R2/R4: view episodes -------------------------------------------
    view_sampler = SequenceSampler(args.data, args.split, args.seq_len, img,
                                   growth_fraction=0.0, seed=1234)
    log(f"\nview episodes: {view_sampler.stats()}")
    results["view"] = run_eval(model, view_sampler, device, args.context, horizons,
                               args.n_batches, args.batch_size, "view", noaction, log)

    log("\n=== R1/R2/R4  VIEW CHANNEL (open-loop rollout) ===")
    for hz in [f"t+{h}" for h in horizons]:
        if hz not in results["view"]["full"]:
            continue
        log(f"  {hz}")
        for variant, table in results["view"].items():
            if hz not in table:
                continue
            r = table[hz]
            log(f"    {variant:16s} PSNR={r['psnr_db']['mean']:6.2f}dB  "
                f"SSIM={r['ssim']['mean']:.4f}  depthMAE={r['depth_mae_m']['mean']:6.3f}m  "
                f"mIoU={r['miou']['mean']:.4f}  fruitMAE={r['fruit_vis_mae']['mean']:.4f}")

    # -- R3: growth episodes -----------------------------------------------
    growth_sampler = SequenceSampler(args.data, args.split, args.seq_len, img,
                                     growth_fraction=1.0, seed=4321)
    if growth_sampler.growth_records:
        n_stages = growth_sampler.growth_records[0]["n_steps"]
        g_context = min(2, n_stages - 1)
        g_horizons = tuple(h for h in (1, 2, 3, 5) if g_context + h <= n_stages)
        log(f"\ngrowth episodes: {growth_sampler.stats()} (n_stages={n_stages}, "
            f"context={g_context}, horizons={g_horizons})")
        results["growth"] = run_eval(model, growth_sampler, device, g_context, g_horizons,
                                     max(4, args.n_batches // 2), args.batch_size,
                                     "growth", noaction, log)
        results["growth_config"] = {"context": g_context, "horizons": list(g_horizons),
                                    "n_stages": n_stages}
        log("\n=== R3  GROWTH CHANNEL (counterfactual advanceTime) ===")
        for hz in [f"t+{h}" for h in g_horizons]:
            if hz not in results["growth"].get("full", {}):
                continue
            log(f"  {hz}")
            for variant, table in results["growth"].items():
                if hz not in table:
                    continue
                r = table[hz]
                log(f"    {variant:16s} PSNR={r['psnr_db']['mean']:6.2f}dB  "
                    f"SSIM={r['ssim']['mean']:.4f}  depthMAE={r['depth_mae_m']['mean']:6.3f}m  "
                    f"mIoU={r['miou']['mean']:.4f}  fruitMAE={r['fruit_vis_mae']['mean']:.4f}")
    else:
        log("\nno growth episodes in this split -- R3 skipped")

    # -- acceptance ---------------------------------------------------------
    acc = {}
    for hz in [f"t+{h}" for h in horizons]:
        v = results["view"]
        if hz not in v.get("full", {}):
            continue
        acc[hz] = {
            "full_beats_copy_last_psnr": bool(
                v["full"][hz]["psnr_db"]["mean"] > v["copy_last"][hz]["psnr_db"]["mean"]),
            "full_beats_zero_action_psnr": bool(
                v["full"][hz]["psnr_db"]["mean"] > v["zero_action"][hz]["psnr_db"]["mean"]),
            "full_beats_shuffled_action_psnr": bool(
                v["full"][hz]["psnr_db"]["mean"] > v["shuffled_action"][hz]["psnr_db"]["mean"]),
        }
        if "noaction_model" in v:
            acc[hz]["full_beats_trained_noaction_psnr"] = bool(
                v["full"][hz]["psnr_db"]["mean"] > v["noaction_model"][hz]["psnr_db"]["mean"])
    results["acceptance"] = acc
    log(f"\n=== ACCEPTANCE ===\n{json.dumps(acc, indent=2)}")

    # -- qualitative strips --------------------------------------------------
    if args.qualitative > 0:
        try:
            import imageio.v3 as iio
            strips = []
            for i, (rec, ep) in enumerate(view_sampler.iter_episodes(
                    "view", limit=args.qualitative, seq_len=args.seq_len)):
                data = model.preprocess({k: torch.from_numpy(v) for k, v in ep.items()}, device)
                pred = rollout(model, data, args.context)
                T = data["obs"].shape[1]
                show = [h for h in horizons if args.context + h - 1 < T]
                gt_row, pr_row = [], []
                for h in show:
                    t_abs = args.context + h - 1
                    gt_row.append(((data["rgb"][0, t_abs] + 0.5).clamp(0, 1) * 255)
                                  .permute(1, 2, 0).cpu().numpy().astype(np.uint8))
                    pr_row.append(((pred["rgb"][0, h - 1] + 0.5).clamp(0, 1) * 255)
                                  .permute(1, 2, 0).cpu().numpy().astype(np.uint8))
                strip = np.concatenate([np.concatenate(gt_row, 1), np.concatenate(pr_row, 1)], 0)
                iio.imwrite(os.path.join(args.out, f"rollout_{i}_{rec['family']}.png"), strip)
                strips.append(rec["path"])
            log(f"\nwrote {len(strips)} qualitative rollout strips "
                f"(top row = Helios ground truth at t+{show}, bottom = model imagination)")
        except Exception as e:
            log(f"qualitative rendering failed: {type(e).__name__}: {e}")

    with open(os.path.join(args.out, "w6_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(args.out, "w6_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    log(f"\nWrote {args.out}/w6_results.json")
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
            notify_slack(f"World model W6 eval FAILED: {traceback.format_exc()[-1200:]}")
        except Exception:
            pass
        raise
