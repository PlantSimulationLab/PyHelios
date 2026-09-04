"""
Round 2 / R2-D -- a growth evaluation that is actually a counterfactual.

W6's R3 rolled a growth episode forward and compared "true action" against "action
zeroed". R2-A measured why that test could not work: **every growth episode in the
dataset carries the identical `a_grow` sequence**, so "zero the growth action" asks
the model about a value that appears nowhere in training, and "true action" is
indistinguishable from "count the frames".

This script asks a question the data can answer. The stored growth episodes hold
the SAME camera pose rendered at 8 known ages, so from the frame at 545 d a
one-step prediction with `a_grow = d` has a real ground-truth target for
d in {5, 10, 15, 20, 25, 35} days -- the stored frame at 545 + d. Six genuine
counterfactuals per episode, all of them real renders.

Measured:

  G1  dt response      -- how far apart the predictions for the smallest and
                          largest d are, in units of how far apart the
                          corresponding GROUND-TRUTH frames are. 0 = the model
                          ignores the growth action entirely.
  G2  dt identification -- for each predicted d, which ground-truth age is it
                          closest to? A model that uses the action puts its
                          prediction nearest the target it was asked for.
  G3  accuracy vs d    -- PSNR / depth MAE / mIoU against the correct target,
                          with copy-the-last-observed-frame as the baseline.

Usage:
    python -m yogesh_dev.world_model.run_r2_growth_eval \
        --ckpt .../ckpt_best.pt --tag r2_main [--ckpt2 ... --tag2 r2_growth]
"""

import argparse
import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.rssm import symexp, N_SEMANTIC_CLASSES
from yogesh_dev.world_model.evaluate import load_model, psnr, miou
from yogesh_dev.world_model.data import EpisodeStore

CONTEXT = 2          # observe stages 0 and 1 (540 d, 545 d)
BASE_IDX = 1         # last observed frame = stage 1 = 545 d


def build_episodes(root, split, image_size, limit=None):
    with open(os.path.join(root, "manifest.json")) as f:
        man = json.load(f)
    recs = [e for e in man["episodes"]
            if e["episode_type"] == "growth" and e["split"] == split]
    if limit:
        recs = recs[:limit]
    store = EpisodeStore(root, recs, cache_size=len(recs), image_size=image_size,
                         load_age=True)
    return man, recs, store


@torch.no_grad()
def evaluate_ckpt(ckpt, root, split, device, limit, batch, log, train_max_dt=20.0):
    model, ck = load_model(ckpt, device)
    img = ck["args"]["image_size"]
    man, recs, store = build_episodes(root, split, img, limit)
    stages = man["config"]["stages"]
    base_age = stages[BASE_IDX]
    # candidate growth actions, and the stage index each one lands on
    cands = [(stages[j] - base_age, j) for j in range(BASE_IDX + 1, len(stages))]
    log(f"  ckpt={ckpt} step={ck['step']} image_size={img}")
    log(f"  base age {base_age:.0f} d; candidate dt -> target stage: "
        + ", ".join(f"{d:.0f}d->{stages[j]:.0f}d" for d, j in cands))

    # ---- assemble all growth episodes into one tensor ----------------------
    rgb, dep, sem, fv = [], [], [], []
    for i in range(len(recs)):
        ep = store.load(i)
        rgb.append(ep["rgb"]); dep.append(ep["depth"])
        sem.append(ep["semantic"]); fv.append(ep["fruit_vis"])
    rgb = np.stack(rgb); dep = np.stack(dep); sem = np.stack(sem); fv = np.stack(fv)
    E, T = rgb.shape[:2]
    log(f"  {E} growth episodes x {T} stages at {img}x{img}")

    per_d = {}
    resp = {"pred_pairs": [], "gt_pairs": []}
    # Per-episode error matrix rather than just the argmin, so identification
    # accuracy can be recomputed on any subset of the candidates. That matters
    # because only the candidates with dt <= --train-max-dt are values the stage
    # subsampling actually produces (5/10/15/20 d at stride <= 3); 25 d and 35 d
    # are out of distribution for every model here, and scoring them together
    # with the rest would blame a model for failing on an action it never saw.
    err_mats = []

    for s in range(0, E, batch):
        sl = slice(s, min(s + batch, E))
        B = rgb[sl].shape[0]
        data = model.preprocess({"rgb": rgb[sl], "depth": dep[sl], "semantic": sem[sl],
                                 "fruit_vis": fv[sl]}, device)
        obs = data["obs"]
        preds = {}
        for d, j in cands:
            act = torch.zeros((B, CONTEXT, 5), device=device)
            act[:, 0, 4] = (stages[1] - stages[0]) / 10.0     # true 540->545 step
            act[:, 1, 4] = d / 10.0                            # the counterfactual
            ctx = model.observe(obs[:, :CONTEXT], act)
            h, z = ctx["h"][:, -1], ctx["z"][:, -1]
            hs, zs = model.imagine(h, z, act[:, CONTEXT - 1:CONTEXT])
            preds[d] = model.decode(hs, zs)

        # ---- G3: accuracy against the correct target ----------------------
        for d, j in cands:
            p = preds[d]
            gt_rgb = data["rgb"][:, j]
            gt_dsl = data["depth_symlog"][:, j]
            gt_sem = data["semantic"][:, j]
            not_sky = ~data["sky"][:, j]
            n_valid = not_sky.flatten(1).sum(1).clamp_min(1)
            derr = (symexp(p["depth_symlog"][:, 0]) - symexp(gt_dsl)).abs()
            rec = per_d.setdefault(d, {"psnr": [], "depth_mae": [], "miou": [],
                                       "copy_psnr": [], "copy_depth_mae": [],
                                       "copy_miou": []})
            rec["psnr"].append(float(psnr(p["rgb"][:, 0], gt_rgb).mean()))
            rec["depth_mae"].append(float(((derr * not_sky).flatten(1).sum(1)
                                           / n_valid).mean()))
            rec["miou"].append(float(np.nanmean(
                miou(p["semantic_logits"][:, 0], gt_sem).cpu().numpy())))
            # copy-last baseline: repeat the frame at BASE_IDX
            c_rgb = data["rgb"][:, BASE_IDX]
            c_derr = (symexp(data["depth_symlog"][:, BASE_IDX]) - symexp(gt_dsl)).abs()
            oh = torch.nn.functional.one_hot(
                data["semantic"][:, BASE_IDX], N_SEMANTIC_CLASSES).permute(0, 3, 1, 2).float()
            rec["copy_psnr"].append(float(psnr(c_rgb, gt_rgb).mean()))
            rec["copy_depth_mae"].append(float(((c_derr * not_sky).flatten(1).sum(1)
                                                / n_valid).mean()))
            rec["copy_miou"].append(float(np.nanmean(miou(oh, gt_sem).cpu().numpy())))

        # ---- G1: dt response ----------------------------------------------
        d_lo, j_lo = cands[0]
        d_hi, j_hi = cands[-1]
        resp["pred_pairs"].append(float(torch.sqrt(
            ((preds[d_lo]["rgb"][:, 0] - preds[d_hi]["rgb"][:, 0]) ** 2).mean())))
        resp["gt_pairs"].append(float(torch.sqrt(
            ((data["rgb"][:, j_lo] - data["rgb"][:, j_hi]) ** 2).mean())))

        # ---- G2: dt identification ----------------------------------------
        rows = []
        for a, (d, j) in enumerate(cands):
            errs = [((preds[d]["rgb"][:, 0] - data["rgb"][:, j2]) ** 2).flatten(1).mean(1)
                    for _, j2 in cands]
            rows.append(torch.stack(errs, 1))          # (B, n_cands)
        err_mats.append(torch.stack(rows, 1).cpu().numpy())   # (B, asked, target)

    out = {"ckpt": ckpt, "step": int(ck["step"]), "split": split,
           "n_episodes": int(E), "base_age_days": float(base_age),
           "candidate_dt_days": [float(d) for d, _ in cands],
           "candidate_target_age": [float(stages[j]) for _, j in cands]}

    out["g1_dt_response"] = {
        "pred_rms_lo_vs_hi": float(np.mean(resp["pred_pairs"])),
        "gt_rms_lo_vs_hi": float(np.mean(resp["gt_pairs"])),
        "ratio": float(np.mean(resp["pred_pairs"]) / max(1e-9, np.mean(resp["gt_pairs"]))),
        "dt_lo_days": float(cands[0][0]), "dt_hi_days": float(cands[-1][0])}
    log(f"  [G1] dt response: predictions for dt={cands[0][0]:.0f}d and "
        f"dt={cands[-1][0]:.0f}d differ by RMS {out['g1_dt_response']['pred_rms_lo_vs_hi']:.5f}; "
        f"the ground-truth frames differ by {out['g1_dt_response']['gt_rms_lo_vs_hi']:.5f} "
        f"=> {out['g1_dt_response']['ratio']*100:.1f}% of real growth change")

    EM = np.concatenate(err_mats, axis=0)              # (E, asked, target)
    nc = len(cands)

    def identification(keep):
        """Accuracy when both the question and the answer set are restricted to
        the candidate indices in `keep`."""
        k = np.asarray(keep)
        sub = EM[:, k][:, :, k]
        pick = sub.argmin(2)
        correct = (pick == np.arange(len(k))[None, :]).mean()
        conf = np.zeros((len(k), len(k)), dtype=np.int64)
        for a in range(len(k)):
            for v in pick[:, a]:
                conf[a, int(v)] += 1
        return float(correct), conf

    all_idx = list(range(nc))
    in_idx = [i for i, (d, _) in enumerate(cands) if d <= train_max_dt]
    acc_all, conf_all = identification(all_idx)
    out["g2_confusion"] = conf_all.tolist()
    out["g2_identification_accuracy"] = acc_all
    out["g2_chance"] = 1.0 / nc
    log(f"  [G2] dt identification accuracy {acc_all*100:.1f}% (chance {100.0/nc:.1f}%) "
        f"over all {nc} candidates")
    log("       rows = dt asked for, cols = nearest ground-truth age")
    log("        " + "".join(f"{stages[j]:>7.0f}" for _, j in cands))
    for a, (d, j) in enumerate(cands):
        log(f"   {d:>3.0f}d " + "".join(f"{v:>7d}" for v in conf_all[a]))
    if 1 < len(in_idx) < nc:
        acc_in, _ = identification(in_idx)
        out["g2_identification_accuracy_in_distribution"] = acc_in
        out["g2_chance_in_distribution"] = 1.0 / len(in_idx)
        out["g2_train_max_dt_days"] = float(train_max_dt)
        log(f"       restricted to dt <= {train_max_dt:.0f} d (the values stage "
            f"subsampling actually produces): {acc_in*100:.1f}% "
            f"(chance {100.0/len(in_idx):.1f}%)")

    g3 = {}
    log(f"  [G3] {'dt':>4} {'target':>7} | {'PSNR':>7} {'copy':>7} | "
        f"{'depthMAE':>9} {'copy':>7} | {'mIoU':>6} {'copy':>6}")
    for d, j in cands:
        r = per_d[d]
        rec = {k: float(np.mean(v)) for k, v in r.items()}
        rec["target_age"] = float(stages[j])
        g3[f"dt{int(d)}"] = rec
        log(f"       {d:>4.0f} {stages[j]:>7.0f} | {rec['psnr']:>7.2f} {rec['copy_psnr']:>7.2f} | "
            f"{rec['depth_mae']:>9.3f} {rec['copy_depth_mae']:>7.3f} | "
            f"{rec['miou']:>6.3f} {rec['copy_miou']:>6.3f}")
    out["g3_accuracy_vs_dt"] = g3
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "output", "dataset"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "output", "r2"))
    ap.add_argument("--ckpt", action="append", required=True,
                    help="repeatable: one checkpoint per model to compare")
    ap.add_argument("--tag", action="append", default=None)
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--train-max-dt", type=float, default=20.0,
                    help="largest a_grow value the training augmentation can produce "
                         "(stage subsampling with stride <= 3 yields 5/10/15/20 d). "
                         "Candidates above this are out of distribution for every "
                         "model and are reported separately.")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    lines = []

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    tags = args.tag or [f"model{i}" for i in range(len(args.ckpt))]
    results = {"split": args.split, "device": device, "models": {}}
    for ck, tag in zip(args.ckpt, tags):
        log(f"\n=== {tag} ===")
        results["models"][tag] = evaluate_ckpt(ck, args.data, args.split, device,
                                               args.limit, args.batch, log,
                                               args.train_max_dt)

    with open(os.path.join(args.out, "r2_growth_eval.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(args.out, "r2_growth_eval_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    log(f"\nwrote {args.out}/r2_growth_eval.json")


if __name__ == "__main__":
    main()
