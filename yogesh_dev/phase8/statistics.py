"""
T8.4 -- statistics: bootstrap CIs resampling CANOPIES (not views), paired Wilcoxon
signed-rank test, Cliff's delta effect size, Holm-Bonferroni correction. Hand-rolled,
no SciPy -- re-verified absent in this env (`import scipy` -> ModuleNotFoundError),
matching Phase 6/7's own finding (`yogesh_dev/phase6/common.py`'s `spearman_rho`
docstring), not assumed.

## The canopies-vs-views resampling distinction (why this is real, not just a comment)

Every function in this module takes a 1-D array where EACH ENTRY IS ALREADY ONE
CANOPY'S metric value (e.g. `mean_coverage_frac` from one whole canopy's rendered view
sequence, as `policies.score_canopy` returns). Resampling that array with replacement
(`bootstrap_ci`) draws whole canopies, never individual views/poses -- there is no
per-view array anywhere in this module for the bootstrap to accidentally resample
instead. `bootstrap_ci_wrong_view_level` below exists ONLY as a runnable demonstration
of the WRONG way (resampling a canopy's individual per-pose visibility indicators
pooled together, which understates the true between-canopy variance because it treats
correlated views from the same canopy as if they were independent draws) -- it is
called once, from `run_t84_statistics.py`, specifically to show the CI is
too narrow, and is never used for any reported result.
"""

import math

import numpy as np


def bootstrap_ci(values, n_boot=2000, alpha=0.05, seed=0):
    """Percentile bootstrap CI for the mean of `values`, resampling CANOPIES (one
    array entry = one canopy). This is the only bootstrap this module reports."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return {"mean": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n_canopies": 0}
    rng = np.random.default_rng(seed)
    boot_means = np.empty(n_boot)
    for b in range(n_boot):
        sample = values[rng.integers(0, n, size=n)]  # resample CANOPIES with replacement
        boot_means[b] = sample.mean()
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return {"mean": float(values.mean()), "ci_low": lo, "ci_high": hi,
            "n_canopies": n, "n_boot": n_boot, "alpha": alpha}


def bootstrap_ci_wrong_view_level(per_canopy_view_values, n_boot=2000, alpha=0.05, seed=0):
    """DEMONSTRATION ONLY, never used for a reported result (see module docstring).
    `per_canopy_view_values`: list of arrays, one per canopy, of that canopy's
    individual per-view/per-pose values. The WRONG bootstrap pools every view from
    every canopy into one flat array and resamples individual views -- this treats
    (say) 18 correlated views from 3 canopies as 54 independent draws, understating
    the true between-canopy uncertainty. Returns the same CI shape as `bootstrap_ci`
    plus `n_views_pooled` so the two CI widths can be compared directly."""
    pooled = np.concatenate([np.asarray(v, dtype=float) for v in per_canopy_view_values])
    n = len(pooled)
    rng = np.random.default_rng(seed)
    boot_means = np.empty(n_boot)
    for b in range(n_boot):
        sample = pooled[rng.integers(0, n, size=n)]
        boot_means[b] = sample.mean()
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return {"mean": float(pooled.mean()), "ci_low": lo, "ci_high": hi,
            "n_views_pooled": n, "n_boot": n_boot, "alpha": alpha}


def paired_wilcoxon_signed_rank(x, y):
    """Paired Wilcoxon signed-rank test (two-sided), hand-rolled, normal approximation
    with continuity correction (standard for n large enough that exact tables aren't
    used -- matches what scipy.stats.wilcoxon's 'approx' mode computes). `x`, `y` must
    be the same length, one entry per MATCHED canopy (same seed, see
    PREREGISTRATION.md's pairing).

    Returns dict with statistic (sum of positive ranks, W+), z, p_value (two-sided),
    n_effective (after dropping zero differences), and n_ties (tied |diff| groups).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) != len(y):
        raise ValueError("x and y must be the same length (paired samples)")
    diff = x - y
    nonzero = diff[diff != 0]
    n = len(nonzero)
    if n == 0:
        return {"statistic": 0.0, "z": 0.0, "p_value": 1.0, "n_effective": 0, "n_ties_dropped": len(diff)}

    abs_diff = np.abs(nonzero)
    signs = np.sign(nonzero)

    # Rank |diff|, average rank for ties (standard tie handling).
    order = np.argsort(abs_diff, kind="mergesort")
    ranks = np.empty(n, dtype=float)
    sorted_abs = abs_diff[order]
    i = 0
    tie_correction_terms = []
    while i < n:
        j = i
        while j + 1 < n and sorted_abs[j + 1] == sorted_abs[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks[order[i:j + 1]] = avg_rank
        t = j - i + 1
        if t > 1:
            tie_correction_terms.append(t ** 3 - t)
        i = j + 1

    w_plus = float(ranks[signs > 0].sum())
    w_minus = float(ranks[signs < 0].sum())
    statistic = w_plus

    mean_w = n * (n + 1) / 4.0
    tie_term = sum(tie_correction_terms)
    var_w = (n * (n + 1) * (2 * n + 1) - tie_term / 2.0) / 24.0
    if var_w <= 0:
        return {"statistic": statistic, "z": 0.0, "p_value": 1.0, "n_effective": n,
                "n_ties_dropped": len(diff) - n}

    # Continuity correction toward the mean.
    diff_from_mean = statistic - mean_w
    cc = 0.5 if diff_from_mean > 0 else (-0.5 if diff_from_mean < 0 else 0.0)
    z = (diff_from_mean - cc) / math.sqrt(var_w)
    p_value = 2.0 * (1.0 - _standard_normal_cdf(abs(z)))
    p_value = min(1.0, max(0.0, p_value))

    return {
        "statistic": statistic, "w_minus": w_minus, "z": float(z), "p_value": float(p_value),
        "n_effective": n, "n_ties_dropped": len(diff) - n,
    }


def _standard_normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def cliffs_delta(x, y):
    """Cliff's delta effect size for two (here: paired, but the statistic itself is
    defined for any two samples) groups: delta = P(x > y) - P(x < y) over all pairs,
    in [-1, 1]. Hand-rolled O(n*m) (n, m are canopy counts -- tens, not a concern).
    Magnitude thresholds from Romano et al. 2006 (negligible < .147, small < .33,
    medium < .474, else large), applied to |delta|.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n, m = len(x), len(y)
    if n == 0 or m == 0:
        return {"delta": float("nan"), "magnitude": "undefined"}
    gt = 0
    lt = 0
    for xi in x:
        gt += int(np.sum(xi > y))
        lt += int(np.sum(xi < y))
    delta = (gt - lt) / (n * m)
    ad = abs(delta)
    if ad < 0.147:
        magnitude = "negligible"
    elif ad < 0.33:
        magnitude = "small"
    elif ad < 0.474:
        magnitude = "medium"
    else:
        magnitude = "large"
    return {"delta": float(delta), "magnitude": magnitude, "n_x": n, "n_y": m}


def holm_bonferroni(p_values, alpha=0.05):
    """Holm step-down correction over a list of p-values (from possibly-different
    tests, applied once across every comparison this phase makes -- see
    PREREGISTRATION.md). Returns, in the ORIGINAL input order: adjusted p-values
    (monotone, capped at 1) and per-comparison reject/fail-to-reject decisions at
    `alpha`.
    """
    p_values = list(p_values)
    m = len(p_values)
    if m == 0:
        return {"adjusted_p": [], "reject": [], "alpha": alpha}

    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted_sorted = [0.0] * m
    running_max = 0.0
    for rank, idx in enumerate(order):
        factor = m - rank
        val = min(1.0, p_values[idx] * factor)
        running_max = max(running_max, val)
        adjusted_sorted[rank] = running_max

    adjusted_p = [0.0] * m
    for rank, idx in enumerate(order):
        adjusted_p[idx] = adjusted_sorted[rank]

    reject = [adjusted_p[i] < alpha for i in range(m)]
    return {"adjusted_p": adjusted_p, "reject": reject, "alpha": alpha, "n_comparisons": m}
