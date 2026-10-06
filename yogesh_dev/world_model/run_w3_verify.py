"""
W3 acceptance checks against a real generated dataset.

  A1  Regenerating one orchard's episodes with the same seed is byte-identical.
  A2  The train/val/test seed sets are provably disjoint, both as declared
      ranges and as actually used in the manifest.
  A3  No frame-level leakage: no orchard seed appears in more than one split.
  A4  Content sanity: value ranges, class histograms, depth/semantic sky
      agreement, action statistics, and the realised growth/view frame balance.

A1 re-renders a whole orchard into a scratch directory and compares the npz
bytes, which is a genuinely end-to-end determinism check (Helios growth RNG,
camera batching, tonemapping and compression all included) rather than a
re-hash of the same file.

Run (helios env, needs pyhelios for A1):
    /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.world_model.run_w3_verify \
        --data yogesh_dev/world_model/output/dataset
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.orchard import verify_seed_split, TRAIN_SEEDS, VAL_SEEDS, TEST_SEEDS

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "w3")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "output", "dataset"))
    ap.add_argument("--skip-regen", action="store_true",
                    help="skip A1 (the expensive end-to-end determinism re-render)")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    lines, res = [], {}

    def log(m):
        print(m, flush=True)
        lines.append(str(m))

    with open(os.path.join(args.data, "manifest.json")) as f:
        man = json.load(f)
    eps = man["episodes"]
    log("=" * 78)
    log(f"W3 verification of {args.data}")
    log("=" * 78)
    log(f"episodes={len(eps)}  frames={sum(e['n_steps'] for e in eps)}  "
        f"bytes={sum(e['bytes'] for e in eps)/1e9:.2f} GB")
    log(f"config: {json.dumps(man['config'])}")

    # -- A2/A3 splits --------------------------------------------------------
    log("\n[A2] declared seed streams")
    sp = verify_seed_split()
    log(f"  {sp}")
    used = {}
    for e in eps:
        used.setdefault(e["split"], set()).add(e["orchard_seed"])
    log("\n[A3] seeds actually used per split")
    for k, v in used.items():
        log(f"  {k}: {len(v)} seeds -> {sorted(v)}")
    pairs = [("train", "val"), ("train", "test"), ("val", "test")]
    overlaps = {f"{a}&{b}": sorted(used.get(a, set()) & used.get(b, set())) for a, b in pairs}
    log(f"  overlaps: {overlaps}")
    a3 = all(len(v) == 0 for v in overlaps.values())
    log(f"  A3 no cross-split seed reuse: {a3}")
    res["A2_declared_disjoint"] = sp
    res["A3_used_overlaps"] = overlaps
    res["A3_pass"] = bool(a3)

    # -- A4 content sanity ---------------------------------------------------
    log("\n[A4] content sanity over a sample of episodes")
    rng = np.random.default_rng(0)
    sample = [eps[i] for i in rng.choice(len(eps), size=min(24, len(eps)), replace=False)]
    hist = np.zeros(7, dtype=np.int64)
    depth_min, depth_max = np.inf, -np.inf
    sky_agree, n_nan, n_frames = [], 0, 0
    fruit_vis_all, act_all = [], []
    for e in sample:
        with np.load(os.path.join(args.data, e["path"])) as z:
            rgb, depth, sem = z["rgb"], z["depth"].astype(np.float32), z["semantic"]
            n_frames += rgb.shape[0]
            u, c = np.unique(sem, return_counts=True)
            for k, v in zip(u, c):
                hist[int(k)] += int(v)
            valid = depth > 0
            if valid.any():
                depth_min = min(depth_min, float(depth[valid].min()))
                depth_max = max(depth_max, float(depth[valid].max()))
            sky_agree.append(float(((depth < 0) == (sem == 6)).mean()))
            n_nan += int(np.isnan(depth).sum())
            fruit_vis_all.append(z["fruit_vis"])
            act_all.append(np.concatenate([z["a_view"], z["a_grow"]], axis=1))
    tot = hist.sum()
    names = ["other/ground", "fruit", "leaf", "shoot", "petiole", "peduncle", "sky"]
    log(f"  sampled {len(sample)} episodes / {n_frames} frames")
    for i, n in enumerate(names):
        log(f"    {n:14s} {hist[i]:10d}  {hist[i]/tot*100:6.2f}%")
    log(f"  depth range over non-sky pixels: [{depth_min:.3f}, {depth_max:.3f}] m")
    log(f"  depth NaNs: {n_nan}")
    log(f"  depth-sky vs semantic-sky pixel agreement: {np.mean(sky_agree):.6f}")
    fv = np.concatenate(fruit_vis_all)
    log(f"  fruit visibility: mean={fv.mean():.5f} max={fv.max():.5f} "
        f"frames with zero fruit={float((fv == 0).mean()):.3f}")
    aa = np.concatenate(act_all)
    log(f"  action |mean| per dim (dx,dy,dz,dyaw,dgrow): "
        f"{np.abs(aa).mean(0).round(4).tolist()}")
    res["A4"] = {"class_fractions": {names[i]: float(hist[i] / tot) for i in range(7)},
                 "depth_min_m": depth_min, "depth_max_m": depth_max, "depth_nans": n_nan,
                 "sky_mask_agreement": float(np.mean(sky_agree)),
                 "fruit_vis_mean": float(fv.mean()), "fruit_vis_max": float(fv.max()),
                 "frac_frames_zero_fruit": float((fv == 0).mean()),
                 "action_abs_mean": np.abs(aa).mean(0).tolist(),
                 "n_episodes_sampled": len(sample), "n_frames_sampled": n_frames}

    # -- channel balance -----------------------------------------------------
    view_fr = sum(e["n_steps"] for e in eps if e["episode_type"] == "view")
    grow_fr = sum(e["n_steps"] for e in eps if e["episode_type"] == "growth")
    log(f"\n[balance] view frames={view_fr}  growth frames={grow_fr}  "
        f"growth share={grow_fr/(view_fr+grow_fr):.4f}")
    res["channel_balance"] = {"view_frames": view_fr, "growth_frames": grow_fr,
                              "growth_share": grow_fr / max(1, view_fr + grow_fr)}

    # -- A1 determinism ------------------------------------------------------
    if not args.skip_regen:
        log("\n[A1] byte-identical regeneration of one orchard")
        from yogesh_dev.world_model.generate import generate_orchard
        cfg = man["config"]
        seed = sorted(used["train"])[0] if used.get("train") else eps[0]["orchard_seed"]
        tmp = tempfile.mkdtemp(prefix="wm_regen_")
        try:
            recs = generate_orchard(
                seed, "train", tmp, n_steps=cfg["n_steps"], families=tuple(cfg["families"]),
                stages=cfg["stages"], n_growth_probes=cfg["n_growth_probes"],
                exposure_scale=cfg["exposure_scale"], orientation=cfg["orientation"],
                resolution=tuple(cfg["resolution"]), sun_zenith=cfg["sun_zenith"],
                sun_azimuth=cfg["sun_azimuth"], log=log)
            same, diff = [], []
            for r in recs:
                orig = os.path.join(args.data, r["path"])
                new = os.path.join(tmp, r["path"])
                if not os.path.isfile(orig):
                    diff.append((r["path"], "missing in original"))
                    continue
                (same if sha256(orig) == sha256(new) else diff).append(r["path"])
            log(f"  {len(same)}/{len(recs)} episodes byte-identical")
            if diff:
                log(f"  DIFFERING: {diff[:5]}")
                # tell apart "different bytes" from "different content"
                p = diff[0] if isinstance(diff[0], str) else diff[0][0]
                with np.load(os.path.join(args.data, p)) as a, np.load(os.path.join(tmp, p)) as b:
                    for k in ("rgb", "depth", "semantic", "instance", "a_view"):
                        eq = bool(np.array_equal(a[k], b[k]))
                        log(f"    array '{k}' identical: {eq}")
            res["A1"] = {"seed": seed, "n_episodes": len(recs),
                         "n_byte_identical": len(same),
                         "pass": bool(len(same) == len(recs)),
                         "differing": [d if isinstance(d, str) else d[0] for d in diff]}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        log("\n[A1] SKIPPED (--skip-regen)")
        res["A1"] = {"skipped": True}

    log(f"\nACCEPTANCE: A1={res.get('A1', {}).get('pass')} "
        f"A2={sp['disjoint']} A3={res['A3_pass']}")
    with open(os.path.join(OUT_DIR, "w3_verification.json"), "w") as f:
        json.dump(res, f, indent=2)
    with open(os.path.join(OUT_DIR, "w3_log.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    log(f"Wrote {OUT_DIR}/w3_verification.json")
    return res


if __name__ == "__main__":
    main()
