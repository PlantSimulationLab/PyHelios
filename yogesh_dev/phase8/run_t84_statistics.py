"""
T8.4 -- apply statistics.py's real bootstrap/Wilcoxon/Cliff's-delta/Holm-Bonferroni to
the real T8.2 (factorial sweep) and T8.3 (apple vs fruitingwall) results.

Three pre-registered comparisons (PREREGISTRATION.md), all paired by construction
(same seed / same canopy across the two arms being compared):

1. `reachable_union` vs `fixed_rig`, per canopy, pooled across all 8 screening cells x
   3 seeds = 24 paired canopies (T8.2's real result data).
2. `look_away` vs `fixed_rig`, same 24 canopies (T8.5's degenerate-baseline check,
   formalized statistically here rather than just eyeballing "0.000 every time").
3. `apple` vs `apple_fruitingwall` mean_interpenetration_frac, paired by seed, n=3
   (T8.3's real result data) -- small n, reported honestly as such.

Every p-value from these 3 comparisons goes into ONE Holm-Bonferroni correction, per
PREREGISTRATION.md ("applied once at the end over the full set, not per-family").

Also demonstrates, using clearly-labeled SYNTHETIC illustrative data (not this phase's
real canopies -- our real per-canopy results only ever recorded each canopy's aggregate
`mean_coverage_frac`, not a raw per-view array to resample from), why resampling
canopies vs resampling pooled views gives different (and for the wrong method,
misleadingly narrow) bootstrap CIs. This does NOT feed into any reported CI above --
every real CI in this file resamples the real per-canopy array.

Run:
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase8.run_t84_statistics
"""

import json
import os

import numpy as np

from yogesh_dev.phase8.statistics import (
    bootstrap_ci, bootstrap_ci_wrong_view_level, paired_wilcoxon_signed_rank,
    cliffs_delta, holm_bonferroni,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def load_t82_paired_arrays():
    with open(os.path.join(OUTPUT_DIR, "t82_factorial_results.json")) as f:
        t82 = json.load(f)
    fixed_rig, reachable_union, look_away, labels = [], [], [], []
    for cell in t82["cells"]:
        for r in cell["results"]:
            fixed_rig.append(r["policies"]["fixed_rig"]["mean_coverage_frac"])
            reachable_union.append(r["policies"]["reachable_union"]["mean_coverage_frac"])
            look_away.append(r["policies"]["look_away"]["mean_coverage_frac"])
            labels.append(f"{cell['label']}_seed{r['seed']}")
    return {
        "fixed_rig": np.array(fixed_rig), "reachable_union": np.array(reachable_union),
        "look_away": np.array(look_away), "labels": labels,
    }


def load_t83_paired_arrays():
    with open(os.path.join(OUTPUT_DIR, "t83_fruitingwall_comparison.json")) as f:
        t83 = json.load(f)
    apple = [r["mean_interpenetration_frac"] for r in t83["results"]["apple"]]
    fruitingwall = [r["mean_interpenetration_frac"] for r in t83["results"]["apple_fruitingwall"]]
    return np.array(apple), np.array(fruitingwall)


def compare(name, x, y, x_label, y_label):
    """x, y: paired arrays (same canopy/seed order). Returns a result dict with both
    arrays' own canopy-level bootstrap CIs, the paired Wilcoxon test, and Cliff's delta."""
    return {
        "name": name,
        f"{x_label}_ci": bootstrap_ci(x, seed=1),
        f"{y_label}_ci": bootstrap_ci(y, seed=1),
        "paired_wilcoxon": paired_wilcoxon_signed_rank(x, y),
        "cliffs_delta": cliffs_delta(x, y),
        "n_pairs": len(x),
    }


def demonstrate_canopy_vs_view_resampling():
    """SYNTHETIC illustrative data only -- see module docstring. 5 illustrative
    canopies, each with 20 illustrative per-view coverage values, correlated within a
    canopy (a real between-canopy variance component + real within-canopy noise) so the
    two bootstraps' CI widths can be compared on data with a KNOWN generating process,
    not fitted to look a particular way."""
    rng = np.random.default_rng(42)
    n_canopies = 5
    canopy_means = rng.normal(0.30, 0.06, n_canopies)  # real between-canopy spread
    per_canopy_views = [cm + rng.normal(0, 0.02, 20) for cm in canopy_means]  # small within-canopy noise
    wrong = bootstrap_ci_wrong_view_level(per_canopy_views, seed=1)
    right = bootstrap_ci([np.mean(v) for v in per_canopy_views], seed=1)
    return {
        "note": "SYNTHETIC illustrative data, not real Phase 8 canopies -- see module docstring",
        "true_between_canopy_std": float(np.std(canopy_means, ddof=1)),
        "wrong_view_level_bootstrap": wrong,
        "right_canopy_level_bootstrap": right,
        "wrong_ci_width": wrong["ci_high"] - wrong["ci_low"],
        "right_ci_width": right["ci_high"] - right["ci_low"],
        "wrong_ci_is_narrower": (wrong["ci_high"] - wrong["ci_low"]) < (right["ci_high"] - right["ci_low"]),
    }


def main():
    t82 = load_t82_paired_arrays()
    apple_interp, fruitingwall_interp = load_t83_paired_arrays()

    comparisons = {}
    comparisons["reachable_union_vs_fixed_rig"] = compare(
        "reachable_union_vs_fixed_rig", t82["reachable_union"], t82["fixed_rig"],
        "reachable_union", "fixed_rig")
    comparisons["look_away_vs_fixed_rig"] = compare(
        "look_away_vs_fixed_rig (T8.5 degenerate-baseline check)", t82["look_away"], t82["fixed_rig"],
        "look_away", "fixed_rig")
    comparisons["apple_vs_fruitingwall_interpenetration"] = compare(
        "apple_vs_fruitingwall_interpenetration (T8.3, n=3, small-n caveat)",
        apple_interp, fruitingwall_interp, "apple", "fruitingwall")

    # ONE Holm-Bonferroni correction across all 3 comparisons' p-values (PREREGISTRATION.md).
    names = list(comparisons.keys())
    p_values = [comparisons[n]["paired_wilcoxon"]["p_value"] for n in names]
    holm = holm_bonferroni(p_values, alpha=0.05)
    for i, n in enumerate(names):
        comparisons[n]["holm_adjusted_p"] = holm["adjusted_p"][i]
        comparisons[n]["holm_reject_at_0.05"] = holm["reject"][i]

    illustration = demonstrate_canopy_vs_view_resampling()

    report = {
        "comparisons": comparisons,
        "holm_bonferroni_summary": holm,
        "canopy_vs_view_resampling_illustration": illustration,
    }

    out_path = os.path.join(OUTPUT_DIR, "t84_statistics_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    for n in names:
        c = comparisons[n]
        print(f"\n{c['name']}:")
        print(f"  n_pairs={c['n_pairs']}  wilcoxon p={c['paired_wilcoxon']['p_value']:.4g} "
              f"(holm-adjusted={c['holm_adjusted_p']:.4g}, reject@0.05={c['holm_reject_at_0.05']})")
        print(f"  cliffs_delta={c['cliffs_delta']['delta']:.3f} ({c['cliffs_delta']['magnitude']})")

    print("\ncanopy-vs-view resampling illustration (SYNTHETIC, see docstring):")
    print(f"  wrong(view-level) CI width={illustration['wrong_ci_width']:.4f}  "
          f"right(canopy-level) CI width={illustration['right_ci_width']:.4f}  "
          f"wrong_is_narrower={illustration['wrong_ci_is_narrower']}")
    print(f"\nwrote {out_path}")
    return report


if __name__ == "__main__":
    main()
