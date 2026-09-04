"""
T5.4 -- Random reachable views, sampled from Phase 2's
PLACEHOLDER_reachable_poses (the real V_reach flat candidate list built by
common.render_and_cache_reachable). This is the denominator of the design
doc's planning score Pi -- run enough random trials per k to report a
stable mean +/- std, not a single lucky/unlucky draw.
"""

import random

from .common import coverage_summary, union_of, sequence_motion_time_s


def run_t54(reachable_candidates, fruit_records, fruit_prim_ids, prim_id_to_info,
            k_values=(1, 2, 4, 8), n_trials=200, seed=20260729):
    rng = random.Random(seed)
    n_candidates = len(reachable_candidates)
    results_by_k = {}

    for k in k_values:
        k_eff = min(k, n_candidates)
        mean_fracs, obs_fracs, motion_times = [], [], []
        for _ in range(n_trials):
            sample = rng.sample(reachable_candidates, k_eff)
            union = union_of(c["visible_ids"] for c in sample)
            summary = coverage_summary(union, fruit_records, fruit_prim_ids, prim_id_to_info)
            mean_fracs.append(summary["mean_coverage_frac"])
            obs_fracs.append(summary["fraction_fruit_observed"])
            motion_times.append(sequence_motion_time_s([c["pose"] for c in sample]))

        n = len(mean_fracs)
        mean_of = lambda xs: sum(xs) / len(xs) if xs else 0.0
        std_of = lambda xs, m: (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5 if xs else 0.0

        mean_cov = mean_of(mean_fracs)
        std_cov = std_of(mean_fracs, mean_cov)
        mean_obs = mean_of(obs_fracs)
        std_obs = std_of(obs_fracs, mean_obs)
        mean_time = mean_of(motion_times)
        std_time = std_of(motion_times, mean_time)

        results_by_k[k_eff] = {
            "n_trials": n_trials,
            "n_views_used": k_eff,
            "mean_coverage_frac_mean": mean_cov,
            "mean_coverage_frac_std": std_cov,
            "fraction_fruit_observed_mean": mean_obs,
            "fraction_fruit_observed_std": std_obs,
            "motion_time_s_mean": mean_time,
            "motion_time_s_std": std_time,
        }

    return {
        "baseline": "T5.4_random_reachable_views",
        "label": "Random reachable views (denominator of Pi) -- mean +/- std over trials",
        "by_k": results_by_k,
    }
