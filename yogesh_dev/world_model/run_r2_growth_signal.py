"""
Round 2 / R2-A -- Is the growth channel learnable at all?

Round 1 reported "the growth channel does not work" and attributed it to channel
imbalance (growth frames are 4% of the dataset, ~6% of the loss after pad
masking). Before spending more compute on it, this script asks the prior
question the task calls for: **how much does the ground truth actually change per
growth step, and does the growth ACTION carry any information at all?**

Everything here is measured from the stored dataset -- no rendering, no model, no
GPU. Runs in either env (numpy only).

Four measurements:

  M1  Action degeneracy. Collect the `a_grow` sequence of every growth episode in
      the dataset and count the distinct sequences. If there is only one, the
      growth action is a constant and is informationally identical to "the frame
      index" -- no counterfactual variation exists anywhere in the data, so no
      amount of training can teach a model to respond to a *different* growth
      action, and the "zero the growth action" ablation in W6 is a pure
      out-of-distribution query rather than a counterfactual.

  M2  Per-step ground-truth change in growth episodes, in every modality, against
      (a) the same statistic for the view channel, and (b) the measured 20.8 dB
      simulator RGB noise floor from FINDINGS section 9. A growth step whose RGB
      change sits at the noise floor is unlearnable in RGB by construction;
      depth and semantic are bit-exact so they have no such floor.

  M3  Scene-dependence of the growth transition. For each stage transition, split
      the per-episode delta image into the part explained by the MEAN delta over
      all episodes at that transition (a scene-independent, "everything gets a
      bit greener and denser" effect, which a model can learn from the action
      alone) and the residual (which requires actually understanding this
      canopy). The explained fraction is an upper bound on how much of the growth
      channel is learnable without solving canopy structure.

  M4  How far the growth channel is from the view channel in difficulty: how many
      view-channel steps of camera motion equal one growth step of change.

Usage:
    python -m yogesh_dev.world_model.run_r2_growth_signal \
        --data yogesh_dev/world_model/output/dataset
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

N_SEM = 7
SIM_RGB_NOISE_FLOOR_DB = 20.82   # FINDINGS section 9, run_w3_determinism_probe.py


def psnr(a, b):
    """PSNR between two uint8 images, on the 0..255 scale."""
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    mse = np.mean((a - b) ** 2)
    if mse <= 0:
        return float("inf")
    return float(10.0 * np.log10(255.0 ** 2 / mse))


def depth_mae(a, b, sentinel=-1.0):
    """MAE over pixels where BOTH frames hit geometry (sky is a sentinel)."""
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    m = (a > sentinel + 1e-6) & (b > sentinel + 1e-6)
    if not m.any():
        return float("nan")
    return float(np.abs(a[m] - b[m]).mean())


def miou(a, b, n=N_SEM):
    ious = []
    for c in range(n):
        pa, pb = (a == c), (b == c)
        u = (pa | pb).sum()
        if u == 0:
            continue
        ious.append((pa & pb).sum() / u)
    return float(np.mean(ious)) if ious else float("nan")


def pixel_agreement(a, b):
    return float((a == b).mean())


def load_ep(root, rec, keys):
    with np.load(os.path.join(root, rec["path"]), allow_pickle=False) as z:
        return {k: z[k] for k in keys}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "output", "dataset"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "output", "r2"))
    ap.add_argument("--split", default="test",
                    help="which split to measure on (test = held-out, the honest choice)")
    ap.add_argument("--max-view-episodes", type=int, default=24)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    logf = open(os.path.join(args.out, "r2_growth_signal_log.txt"), "w")

    def log(m):
        print(m, flush=True)
        logf.write(str(m) + "\n")
        logf.flush()

    t0 = time.time()
    with open(os.path.join(args.data, "manifest.json")) as f:
        man = json.load(f)
    stages = man["config"]["stages"]
    log(f"R2-A growth signal analysis  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"  data={args.data}  split={args.split}  stages={stages}")

    growth = [e for e in man["episodes"] if e["episode_type"] == "growth"]
    growth_split = [e for e in growth if e["split"] == args.split]
    views = [e for e in man["episodes"]
             if e["episode_type"] == "view" and e["split"] == args.split]
    log(f"  growth episodes: {len(growth)} total, {len(growth_split)} in split")
    log(f"  view episodes:   {len(views)} in split")

    results = {"data": args.data, "split": args.split, "stages": stages,
               "n_growth_all": len(growth), "n_growth_split": len(growth_split),
               "sim_rgb_noise_floor_db": SIM_RGB_NOISE_FLOOR_DB}

    # ---------------------------------------------------------------- M1 -----
    # Action degeneracy across the WHOLE dataset, not just the split.
    log("\n[M1] growth action degeneracy (all splits)")
    seqs = {}
    for rec in growth:
        ag = load_ep(args.data, rec, ["a_grow"])["a_grow"].reshape(-1)
        key = ",".join(f"{v:g}" for v in ag)
        seqs.setdefault(key, 0)
        seqs[key] += 1
    log(f"  distinct a_grow sequences over {len(growth)} growth episodes: {len(seqs)}")
    for k, v in sorted(seqs.items(), key=lambda kv: -kv[1]):
        log(f"    [{k}] x{v}")
    results["m1_distinct_a_grow_sequences"] = len(seqs)
    results["m1_a_grow_sequences"] = seqs
    if len(seqs) == 1:
        log("  => the growth action is CONSTANT across the entire dataset. It carries no")
        log("     information beyond the frame index, so there is no counterfactual growth")
        log("     variation anywhere in the training data.")

    # Also check the view channel for contrast: how many distinct action vectors?
    va = []
    for rec in views[:args.max_view_episodes]:
        va.append(load_ep(args.data, rec, ["a_view"])["a_view"])
    va = np.concatenate(va, axis=0) if va else np.zeros((0, 4))
    results["m1_view_action_std"] = [float(x) for x in va.std(axis=0)] if va.size else None
    results["m1_view_action_mean"] = [float(x) for x in va.mean(axis=0)] if va.size else None
    if va.size:
        log(f"  contrast: view action per-dim std over {va.shape[0]} steps = "
            f"{np.round(va.std(axis=0), 4).tolist()} (non-degenerate)")

    # ---------------------------------------------------------------- M2 -----
    log("\n[M2] per-step ground-truth change, growth channel")
    per_trans = {}          # transition index -> list of dicts
    deltas_by_trans = {}    # transition index -> list of float delta images
    for rec in growth_split:
        ep = load_ep(args.data, rec, ["rgb", "depth", "semantic", "fruit_vis", "a_grow"])
        rgb, dep, sem = ep["rgb"], ep["depth"].astype(np.float32), ep["semantic"]
        T = rgb.shape[0]
        for t in range(T - 1):
            d = {
                "rgb_psnr": psnr(rgb[t + 1], rgb[t]),
                "depth_mae": depth_mae(dep[t + 1], dep[t]),
                "sem_miou": miou(sem[t + 1], sem[t]),
                "sem_agree": pixel_agreement(sem[t + 1], sem[t]),
                "d_fruit_vis": float(ep["fruit_vis"][t + 1] - ep["fruit_vis"][t]),
                "a_grow": float(ep["a_grow"].reshape(-1)[t]),
            }
            per_trans.setdefault(t, []).append(d)
            deltas_by_trans.setdefault(t, []).append(
                rgb[t + 1].astype(np.float32) - rgb[t].astype(np.float32))

    def agg(rows, key):
        v = np.array([r[key] for r in rows], dtype=np.float64)
        v = v[np.isfinite(v)]
        return float(v.mean()) if v.size else float("nan")

    log(f"  {'t->t+1':>8} {'age':>12} {'a_grow':>7} {'RGB PSNR':>9} {'depth MAE':>10} "
        f"{'sem mIoU':>9} {'sem agree':>10} {'d fruit_vis':>12}")
    m2 = []
    for t in sorted(per_trans):
        rows = per_trans[t]
        rec = {"transition": t,
               "age_from": stages[t], "age_to": stages[t + 1],
               "a_grow": agg(rows, "a_grow"),
               "rgb_psnr": agg(rows, "rgb_psnr"),
               "depth_mae": agg(rows, "depth_mae"),
               "sem_miou": agg(rows, "sem_miou"),
               "sem_agree": agg(rows, "sem_agree"),
               "d_fruit_vis": agg(rows, "d_fruit_vis"),
               "n": len(rows)}
        m2.append(rec)
        log(f"  {t:>3}->{t+1:<4} {stages[t]:>5.0f}->{stages[t+1]:<5.0f} {rec['a_grow']:>7.0f} "
            f"{rec['rgb_psnr']:>9.2f} {rec['depth_mae']:>10.3f} {rec['sem_miou']:>9.3f} "
            f"{rec['sem_agree']:>10.3f} {rec['d_fruit_vis']:>+12.4f}")
    results["m2_growth_per_transition"] = m2
    if m2:
        log(f"  mean over transitions: RGB PSNR {np.mean([r['rgb_psnr'] for r in m2]):.2f} dB "
            f"(simulator noise floor {SIM_RGB_NOISE_FLOOR_DB} dB), "
            f"depth MAE {np.mean([r['depth_mae'] for r in m2]):.3f} m, "
            f"sem mIoU {np.mean([r['sem_miou'] for r in m2]):.3f}")

    # ---- same statistic for the view channel, as a scale reference ----------
    log("\n[M2b] per-step ground-truth change, view channel (same statistics)")
    view_rows = []
    for rec in views[:args.max_view_episodes]:
        ep = load_ep(args.data, rec, ["rgb", "depth", "semantic"])
        rgb, dep, sem = ep["rgb"], ep["depth"].astype(np.float32), ep["semantic"]
        for t in range(0, min(rgb.shape[0] - 1, 32)):
            view_rows.append({
                "rgb_psnr": psnr(rgb[t + 1], rgb[t]),
                "depth_mae": depth_mae(dep[t + 1], dep[t]),
                "sem_miou": miou(sem[t + 1], sem[t]),
                "sem_agree": pixel_agreement(sem[t + 1], sem[t]),
            })
    vstat = {k: agg(view_rows, k) for k in ("rgb_psnr", "depth_mae", "sem_miou", "sem_agree")}
    vstat["n"] = len(view_rows)
    results["m2b_view_per_step"] = vstat
    log(f"  over {vstat['n']} view steps: RGB PSNR {vstat['rgb_psnr']:.2f} dB, "
        f"depth MAE {vstat['depth_mae']:.3f} m, sem mIoU {vstat['sem_miou']:.3f}, "
        f"agree {vstat['sem_agree']:.3f}")

    # ---------------------------------------------------------------- M3 -----
    # How much of the growth delta is a scene-INDEPENDENT effect?
    log("\n[M3] scene-dependence of the growth transition (RGB delta decomposition)")
    log("     explained = variance of the mean delta / total delta variance;")
    log("     it is the fraction of the growth change predictable from the ACTION alone.")
    m3 = []
    for t in sorted(deltas_by_trans):
        D = np.stack(deltas_by_trans[t])          # (E, H, W, 3)
        mu = D.mean(axis=0, keepdims=True)
        tot = float((D ** 2).mean())
        res = float(((D - mu) ** 2).mean())
        expl = 1.0 - res / tot if tot > 0 else float("nan")
        rec = {"transition": t, "age_from": stages[t], "age_to": stages[t + 1],
               "n_episodes": int(D.shape[0]),
               "total_delta_ms": tot, "residual_ms": res, "explained_fraction": expl,
               "mean_delta_rms": float(np.sqrt((mu ** 2).mean())),
               "delta_rms": float(np.sqrt(tot))}
        m3.append(rec)
        log(f"  {t}->{t+1} ({stages[t]:.0f}->{stages[t+1]:.0f} d): "
            f"delta RMS {rec['delta_rms']:6.2f} levels, "
            f"mean-delta RMS {rec['mean_delta_rms']:6.2f}, "
            f"explained by action alone = {expl*100:5.1f}%")
    results["m3_delta_decomposition"] = m3
    if m3:
        log(f"  mean explained fraction: "
            f"{np.mean([r['explained_fraction'] for r in m3])*100:.1f}%")

    # ---------------------------------------------------------------- M4 -----
    log("\n[M4] growth step vs view step, in comparable units")
    if m2 and vstat["n"]:
        g_rgb = np.mean([r["rgb_psnr"] for r in m2])
        g_dep = np.mean([r["depth_mae"] for r in m2])
        # PSNR -> RMS levels
        g_rms = 255.0 * 10 ** (-g_rgb / 20.0)
        v_rms = 255.0 * 10 ** (-vstat["rgb_psnr"] / 20.0)
        floor_rms = 255.0 * 10 ** (-SIM_RGB_NOISE_FLOOR_DB / 20.0)
        log(f"  RGB change per step (RMS levels): growth {g_rms:.2f}, view {v_rms:.2f}, "
            f"simulator noise {floor_rms:.2f}")
        log(f"  growth RGB step is {g_rms/floor_rms:.2f}x the simulator noise, "
            f"view RGB step is {v_rms/floor_rms:.2f}x")
        log(f"  depth change per step: growth {g_dep:.3f} m, view {vstat['depth_mae']:.3f} m "
            f"({g_dep/max(1e-9, vstat['depth_mae']):.3f}x)")
        results["m4"] = {"growth_rgb_rms_levels": g_rms, "view_rgb_rms_levels": v_rms,
                         "noise_rms_levels": floor_rms,
                         "growth_over_noise": g_rms / floor_rms,
                         "view_over_noise": v_rms / floor_rms,
                         "growth_depth_mae": g_dep, "view_depth_mae": vstat["depth_mae"]}

    results["wall_clock_s"] = time.time() - t0
    with open(os.path.join(args.out, "r2_growth_signal.json"), "w") as f:
        json.dump(results, f, indent=1)
    log(f"\nwrote {os.path.join(args.out, 'r2_growth_signal.json')} "
        f"in {results['wall_clock_s']:.0f}s")
    logf.close()


if __name__ == "__main__":
    main()
