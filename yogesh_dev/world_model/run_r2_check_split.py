"""
Round 2 -- re-verify the train/val/test split AFTER extending the dataset.

W3 checked this once, on the 20-orchard dataset. The Round 2 extension adds new
train seeds to an existing manifest with `--resume`, which is exactly the kind of
operation that can quietly put a test orchard into the training split (a
mis-typed range, a re-used seed, an episode written to the wrong directory). The
check is cheap and the failure mode is invisible in the loss curves, so it is run
again rather than assumed.

Checks, all against the manifest AS WRITTEN, not against the declared ranges:
  1. the seed sets actually present in each split are pairwise disjoint
  2. every episode's `split` field matches the directory its file lives in
  3. every episode file referenced by the manifest exists
  4. no two episodes share a path
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.orchard import verify_seed_split


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "output", "dataset"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "output", "r2"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    with open(os.path.join(args.data, "manifest.json")) as f:
        man = json.load(f)
    eps = man["episodes"]

    present = {}
    for e in eps:
        present.setdefault(e["split"], set()).add(int(e["orchard_seed"]))

    pairs = [("train", "val"), ("train", "test"), ("val", "test")]
    overlaps = {f"{a}_{b}": sorted(present.get(a, set()) & present.get(b, set()))
                for a, b in pairs}

    mismatched_dir = [e["path"] for e in eps
                      if e["path"].split(os.sep)[0] != e["split"]]
    missing = [e["path"] for e in eps
               if not os.path.isfile(os.path.join(args.data, e["path"]))]
    paths = [e["path"] for e in eps]
    dupes = sorted({p for p in paths if paths.count(p) > 1}) if len(set(paths)) != len(paths) else []

    counts = {s: {"n_seeds": len(present.get(s, set())),
                  "n_episodes": sum(1 for e in eps if e["split"] == s),
                  "n_frames": sum(e["n_steps"] for e in eps if e["split"] == s),
                  "seeds": sorted(present.get(s, set()))}
              for s in ("train", "val", "test")}

    ok = (all(len(v) == 0 for v in overlaps.values())
          and not mismatched_dir and not missing and not dupes)

    report = {"data": args.data, "declared_ranges": verify_seed_split(),
              "present_split_overlaps": overlaps, "counts": counts,
              "episodes_in_wrong_directory": mismatched_dir,
              "missing_files": missing, "duplicate_paths": dupes,
              "total_episodes": len(eps),
              "total_frames": sum(e["n_steps"] for e in eps),
              "disjoint_and_consistent": ok}

    for s in ("train", "val", "test"):
        c = counts[s]
        print(f"  {s:5s}: {c['n_seeds']:3d} orchards, {c['n_episodes']:4d} episodes, "
              f"{c['n_frames']:6d} frames  seeds {c['seeds'][:3]}..{c['seeds'][-1:]}")
    print(f"  pairwise seed overlaps: {overlaps}")
    print(f"  episodes in the wrong directory: {len(mismatched_dir)}   "
          f"missing files: {len(missing)}   duplicate paths: {len(dupes)}")
    print(f"  DISJOINT AND CONSISTENT: {ok}")

    with open(os.path.join(args.out, "r2_split_check.json"), "w") as f:
        json.dump(report, f, indent=1)
    if not ok:
        raise SystemExit("SPLIT CHECK FAILED -- refusing to continue")


if __name__ == "__main__":
    main()
