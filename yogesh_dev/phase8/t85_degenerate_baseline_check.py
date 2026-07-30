"""
T8.5 -- Tatarchenko degenerate-baseline check, formalized as its own real empirical
result (not just "T8.2 happened to print 0.000 a bunch of times").

PREREGISTRATION.md committed, BEFORE T8.2/T8.3/T8.4 ran, to a specific prediction:
`look_away` (one camera at the fixed rig's own standoff distance/height, boresight
rotated 180 degrees away from the canopy) must score `mean_coverage_frac`
statistically indistinguishable from 0 and far below `fixed_rig`. This script checks
that prediction against the real result T8.2 produced and T8.4 tested statistically,
and reports pass/fail explicitly -- this is the actual check, not a rhetorical one.

Run (after run_t82_factorial.py and run_t84_statistics.py):
    PYTHONPATH=. /home/yogesh/anaconda3/envs/helios/bin/python -m yogesh_dev.phase8.t85_degenerate_baseline_check
"""

import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def main():
    with open(os.path.join(OUTPUT_DIR, "t82_factorial_results.json")) as f:
        t82 = json.load(f)
    with open(os.path.join(OUTPUT_DIR, "t84_statistics_results.json")) as f:
        t84 = json.load(f)

    look_away_values = [
        r["policies"]["look_away"]["mean_coverage_frac"]
        for cell in t82["cells"] for r in cell["results"]
    ]
    fixed_rig_values = [
        r["policies"]["fixed_rig"]["mean_coverage_frac"]
        for cell in t82["cells"] for r in cell["results"]
    ]
    n_zero = sum(1 for v in look_away_values if v == 0.0)

    cmp = t84["comparisons"]["look_away_vs_fixed_rig"]

    report = {
        "pre_registered_prediction": (
            "look_away's mean_coverage_frac must be statistically indistinguishable "
            "from 0 and far below fixed_rig's (PREREGISTRATION.md)"
        ),
        "n_canopies_checked": len(look_away_values),
        "n_canopies_look_away_scored_exactly_zero": n_zero,
        "look_away_min": min(look_away_values), "look_away_max": max(look_away_values),
        "fixed_rig_mean": sum(fixed_rig_values) / len(fixed_rig_values),
        "paired_wilcoxon_p_value": cmp["paired_wilcoxon"]["p_value"],
        "holm_adjusted_p_value": cmp["holm_adjusted_p"],
        "cliffs_delta": cmp["cliffs_delta"]["delta"],
        "cliffs_delta_magnitude": cmp["cliffs_delta"]["magnitude"],
    }
    prediction_confirmed = (
        n_zero == len(look_away_values)
        and cmp["holm_reject_at_0.05"]
        and cmp["cliffs_delta"]["delta"] <= -0.9  # look_away << fixed_rig, large effect
    )
    report["prediction_confirmed"] = prediction_confirmed
    report["conclusion"] = (
        "PASS: mean_coverage_frac does NOT reward a policy that looks at nothing -- "
        "the degenerate baseline scored exactly 0.0 on all "
        f"{len(look_away_values)}/{len(look_away_values)} real canopies, "
        f"significantly below fixed_rig (Holm-adjusted p={cmp['holm_adjusted_p']:.3g}, "
        f"Cliff's delta={cmp['cliffs_delta']['delta']:.2f}). The headline metric is not "
        "degenerate." if prediction_confirmed else
        "FAIL: the degenerate baseline scored competitively with fixed_rig -- "
        "mean_coverage_frac would need further investigation before being trusted."
    )

    out_path = os.path.join(OUTPUT_DIR, "t85_degenerate_baseline_check.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(json.dumps(report, indent=2, default=str))
    print(f"\nwrote {out_path}")
    return report


if __name__ == "__main__":
    main()
