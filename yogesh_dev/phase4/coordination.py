"""
T4.9 -- Three-arm coordination.

Task doc: "Sequential greedy with randomized arm ordering. Verify the
objective is genuinely submodular -- log-det is, plain trace is not, and a
modular objective will make all three arms converge on the same view."

## Information model: real target centroids, real reachable camera positions

For each real fruit target i (`fruit_ground_truth.json` centroid) and a
real candidate camera position `e_v` (forward-kinematics of a real
reachable roadmap node -- the FULL reachable set per arm this time, 549/
468/468 nodes, not just the 42 rendered ones, since this objective only
needs real geometry (bearing + range), not a rendered image), the standard
bearing-only Fisher-information / triangulation-observability contribution
is `M_i(v) = (I - d d^T) / r^2` where `d` = unit bearing from `e_v` to the
target and `r` = range -- information is high in directions PERPENDICULAR
to the viewing ray (classic triangulation: you learn a point's position
well from directions across the baseline, not along it), scaled down
quadratically with range. This is the real, standard D-optimal-design /
observability-Gramian construction (Krause et al.-style sensor placement),
not an invented metric.

## Why trace(sum M_i(v)) is modular (no coordination signal at all)

`value_trace(A) = sum_i trace(Info_i(A))` where `Info_i(A) = sum_{v in A}
M_i(v)`. Since `trace` is linear, `trace(sum_v M_i(v)) = sum_v
trace(M_i(v))` -- the marginal contribution of adding view `v` is EXACTLY
`sum_i trace(M_i(v))`, independent of what's already in `A`. This is
verified as an executable assertion below (`_assert_trace_is_modular`),
not just claimed: marginal gain computed two ways (via the definition, and
via direct summation of each element's own contribution) must match to
float precision regardless of `A`'s contents. Because trace has zero
interaction term, arms picking sequentially under trace have literally NO
incentive to diversify -- each arm independently picks whatever single
node (in its own disjoint z-band) is closest/most-aligned to the targets,
and with the real 3-arm rig's shared x/y envelope (see `kinematics.py`'s
`single_tree_arm_configs`: all 3 arms share `x=(-0.6,0.6)`,
`y=(-1.10,-0.35)`, differing only in z), that tends to be the SAME (x,y)
approach position for every arm regardless of order.

## Why log-det is genuinely submodular

`value_logdet(A) = sum_i logdet(Info_i(A) + eps*I)`. `logdet` of a sum of
PSD matrices is concave and the marginal gain of adding a near-duplicate
direction (whose `M_i(v)` is nearly parallel to the existing `Info_i(A)`)
is small -- redundant viewing angles buy little extra ellipsoid volume,
genuinely rewarding angular diversity between arms. This IS submodular
(the standard D-optimal-design result), and is what should be used for
real multi-arm coordination instead of trace.

## Demo: sequential greedy, randomized arm order, both objectives

For each of several random arm orderings, each arm (in turn) greedily picks
the single real reachable node from ITS OWN roadmap maximizing the CHOSEN
objective's marginal gain given the arms decided earlier this round. Real
diversity metric reported: mean pairwise bearing-vector dot product across
the 3 chosen views (1.0 = identical direction, 0 = orthogonal) -- lower is
more diverse. Real values (not hand-picked) are compared directly, trace
vs log-det, over the same real target set and real candidate pools.
"""

import json
import os
import random

import numpy as np

import kinematics as kin

EPS_RIDGE = 1e-6


def load_arm_positions(data_dir, arms):
    positions = {}
    for arm in arms:
        joints = np.load(os.path.join(data_dir, f"roadmap_{arm.name}_nodes.npy"))
        pos = np.array([kin.forward_kinematics(kin.JointState(*row), arm).position for row in joints])
        positions[arm.name] = pos
    return positions


def info_matrices(eye_positions, target):
    """eye_positions: (N,3). Returns (N,3,3) real bearing-only information
    matrices for this single target."""
    diff = target[None, :] - eye_positions
    r2 = np.sum(diff ** 2, axis=1)
    r2 = np.clip(r2, 1e-6, None)
    d = diff / np.sqrt(r2)[:, None]
    eye3 = np.eye(3)[None, :, :]
    dd = d[:, :, None] * d[:, None, :]
    return (eye3 - dd) / r2[:, None, None]


def _assert_trace_is_modular(M_per_target_per_arm, targets_idx=(0,), n_check=5, seed=0):
    """Executable check: marginal trace-gain of adding node v is
    independent of the current set A, for real data. `M_per_target_per_arm`:
    list (per target) of dict arm_name -> (N,3,3); concatenated across arms
    here since trace-modularity is a per-element property, arm-independent."""
    rng = random.Random(seed)
    for ti in targets_idx:
        mats = np.concatenate(list(M_per_target_per_arm[ti].values()), axis=0)  # (N_total,3,3)
        n = mats.shape[0]
        base_contribs = np.trace(mats, axis1=1, axis2=2)  # (N,)
        for _ in range(n_check):
            k = rng.randint(0, 3)
            A_idx = rng.sample(range(n), k) if k <= n else []
            A_sum = mats[A_idx].sum(axis=0) if A_idx else np.zeros((3, 3))
            v = rng.randrange(n)
            gain_direct = np.trace(A_sum + mats[v]) - np.trace(A_sum)
            gain_isolated = base_contribs[v]
            assert abs(gain_direct - gain_isolated) < 1e-8, "trace marginal gain depends on A -- should be impossible"
    return True


def logdet_value(info_sum):
    return float(np.linalg.slogdet(info_sum + EPS_RIDGE * np.eye(3))[1])


def trace_value(info_sum):
    return float(np.trace(info_sum))


def sequential_greedy_round(arm_names, M_per_target, positions, objective, order):
    """One round: process arms in `order`; each picks its own best node.
    M_per_target: dict target_idx -> {arm_name: (N,3,3)}. Returns chosen
    node index + eye position + bearing per arm, and the objective's total
    final value."""
    n_targets = len(M_per_target)
    info_sum = [np.zeros((3, 3)) for _ in range(n_targets)]
    chosen = {}
    for arm in order:
        best_gain, best_idx = -1e18, None
        n_nodes = next(iter(M_per_target[0].values())).shape[0] if False else M_per_target[0][arm].shape[0]
        for v in range(n_nodes):
            total_gain = 0.0
            for ti in range(n_targets):
                m = M_per_target[ti][arm][v]
                if objective == "trace":
                    total_gain += trace_value(m)
                else:
                    total_gain += logdet_value(info_sum[ti] + m) - logdet_value(info_sum[ti])
            if total_gain > best_gain:
                best_gain, best_idx = total_gain, v
        chosen[arm] = best_idx
        for ti in range(n_targets):
            info_sum[ti] = info_sum[ti] + M_per_target[ti][arm][best_idx]

    final_value = sum(trace_value(info_sum[ti]) if objective == "trace" else logdet_value(info_sum[ti])
                       for ti in range(n_targets))
    return chosen, final_value


def bearing_diversity(chosen, positions, targets):
    """Mean pairwise dot product of unit bearing vectors (to the FIRST
    target, for a simple single-number diversity metric) across the chosen
    arms' eye positions. Lower = more diverse viewing angles."""
    target = targets[0]
    bearings = []
    for arm, idx in chosen.items():
        eye = positions[arm][idx]
        d = target - eye
        bearings.append(d / np.linalg.norm(d))
    dots = []
    for i in range(len(bearings)):
        for j in range(i + 1, len(bearings)):
            dots.append(float(np.dot(bearings[i], bearings[j])))
    return float(np.mean(dots))


def run_t49(data_dir, n_orderings=6, n_targets=5, seed=0):
    arms = kin.single_tree_arm_configs()
    arm_names = [a.name for a in arms]
    positions = load_arm_positions(data_dir, arms)

    fruit = json.load(open(os.path.join(data_dir, "fruit_ground_truth.json")))
    targets = np.array([r["centroid"] for r in fruit[:n_targets]])

    M_per_target = []
    for t in targets:
        M_per_target.append({arm.name: info_matrices(positions[arm.name], t) for arm in arms})

    modularity_check = _assert_trace_is_modular(M_per_target, targets_idx=range(len(targets)))

    rng = random.Random(seed)
    orderings = []
    base = list(arm_names)
    for _ in range(n_orderings):
        perm = base[:]
        rng.shuffle(perm)
        orderings.append(perm)

    results = {"trace": [], "logdet": []}
    for objective in ("trace", "logdet"):
        for order in orderings:
            chosen, final_value = sequential_greedy_round(arm_names, M_per_target, positions, objective, order)
            diversity = bearing_diversity(chosen, positions, targets)
            chosen_positions = {arm: positions[arm][idx].tolist() for arm, idx in chosen.items()}
            results[objective].append({
                "order": order, "chosen_node_idx": chosen, "chosen_eye_positions": chosen_positions,
                "final_objective_value": final_value, "mean_pairwise_bearing_dot": diversity,
            })

    trace_mean_div = float(np.mean([r["mean_pairwise_bearing_dot"] for r in results["trace"]]))
    logdet_mean_div = float(np.mean([r["mean_pairwise_bearing_dot"] for r in results["logdet"]]))

    return {
        "trace_is_modular_verified": modularity_check,
        "n_targets": n_targets, "n_orderings_tested": n_orderings,
        "trace_objective": results["trace"],
        "logdet_objective": results["logdet"],
        "mean_bearing_dot_trace": trace_mean_div,
        "mean_bearing_dot_logdet": logdet_mean_div,
        "logdet_more_diverse": logdet_mean_div < trace_mean_div,
    }


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    DATA = os.path.join(HERE, "data")
    out = run_t49(DATA)
    print(json.dumps(out, indent=2, default=str))
    with open(os.path.join(HERE, "output_t49_coordination.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
