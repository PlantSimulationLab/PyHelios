"""
Minimal O(n^3) Hungarian algorithm (Kuhn-Munkres, successive shortest
augmenting path with potentials), pure Python -- no scipy in the `helios`
conda env (checked; not installed to avoid touching a conda env shared
across every phase's worktree for one small dependency). Used by
`tracker.py` (T4.4) to find the optimal predicted-track <-> true-fruitID
matching for the IDF1 metric; a real bipartite maximum-weight matching, not
a greedy approximation, since IDF1 specifically requires the OPTIMAL
identity assignment.

Solves: given an n x m non-negative weight matrix, find an assignment
(subset of cells, at most one per row and per column) maximizing total
weight, with no requirement that every row/column be matched. Implemented
by padding to a square matrix with zero-weight dummy rows/columns (so a
real row/column can "match a dummy" at zero cost, i.e. legitimately stay
unmatched) and running the classic min-cost perfect-matching algorithm on
`-weight`.
"""

import numpy as np


def _hungarian_min_cost_square(cost):
    """cost: (n,n) real matrix. Returns col_for_row: array of length n,
    col_for_row[i] = matched column for row i, minimizing total cost of a
    perfect matching. Standard e-maxx-style implementation."""
    n = cost.shape[0]
    INF = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)   # p[j] = row (1-indexed) matched to column j
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0 != 0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1

    col_for_row = [0] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            col_for_row[p[j] - 1] = j - 1
    return col_for_row


def max_weight_bipartite_matching(weight: np.ndarray):
    """weight: (n_rows, n_cols) non-negative. Returns list of (row, col,
    weight) for the optimal matching, omitting any pair whose weight is 0
    (treated as "left unmatched", since padding rows/cols and any genuine
    zero-overlap pair both produce weight 0 -- callers with `weight`
    guaranteed >0 for genuine overlaps can rely on this to drop dummies)."""
    n, m = weight.shape
    size = max(n, m)
    padded = np.zeros((size, size), dtype=float)
    padded[:n, :m] = weight
    cost = -padded
    col_for_row = _hungarian_min_cost_square(cost)
    pairs = []
    for i in range(n):
        j = col_for_row[i]
        if j < m and weight[i, j] > 0:
            pairs.append((i, j, float(weight[i, j])))
    return pairs


def _self_test():
    rng = np.random.RandomState(0)
    for trial in range(200):
        n = rng.randint(1, 6)
        m = rng.randint(1, 6)
        w = rng.randint(0, 10, size=(n, m)).astype(float)
        pairs = max_weight_bipartite_matching(w)
        total = sum(p[2] for p in pairs)
        rows_used = {p[0] for p in pairs}
        cols_used = {p[1] for p in pairs}
        assert len(rows_used) == len(pairs) and len(cols_used) == len(pairs), "matching not 1-1"

        best = 0.0
        import itertools
        small_dim = min(n, m)
        rows = list(range(n))
        cols = list(range(m))
        if n <= m:
            for perm in itertools.permutations(cols, n):
                best = max(best, sum(w[i, perm[i]] for i in range(n)))
        else:
            for perm in itertools.permutations(rows, m):
                best = max(best, sum(w[perm[j], j] for j in range(m)))
        assert abs(best - total) < 1e-6, f"trial {trial}: got {total}, brute force best {best}, w={w}"
    print(f"hungarian self-test: 200/200 random trials match brute force")


if __name__ == "__main__":
    _self_test()
