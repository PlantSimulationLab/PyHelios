"""
Shared paths + loaders for Phase 6. Phase 4's modules (`sensor_model.py`,
`occupancy_map.py`, `information_gain.py`, `semantic_map.py`,
`explore_planner.py`, `exploit_planner.py`, `roadmap.py`, `kinematics.py`,
`hungarian.py`, `tracker.py`) are flat standalone scripts that `import X`
each other by bare module name (not package-relative) -- Phase 5 hit the
same thing and worked around it with a `sys.path` insert, so we do the
same rather than editing those files (out of bounds anyway, they're
Phase 4's, though inside yogesh_dev/ so not hard-blocked -- we just leave
working code alone).
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
YOGESH_DEV = os.path.join(REPO_ROOT, "yogesh_dev")

PHASE1_OUTPUT = os.path.join(YOGESH_DEV, "phase1", "output")
PHASE2_OUTPUT = os.path.join(YOGESH_DEV, "phase2", "output")
PHASE4_DIR = os.path.join(YOGESH_DEV, "phase4")
PHASE4_DATA = os.path.join(PHASE4_DIR, "data")
PHASE5_OUTPUT = os.path.join(YOGESH_DEV, "phase5", "output")

PHASE6_DIR = os.path.dirname(__file__)
PHASE6_OUTPUT = os.path.join(PHASE6_DIR, "output")


def ensure_phase4_importable():
    """Phase 4's own scripts assume `cwd`/`sys.path` includes their own
    directory (flat imports). Idempotent."""
    if PHASE4_DIR not in sys.path:
        sys.path.insert(0, PHASE4_DIR)


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def phase5_available():
    return os.path.isdir(PHASE5_OUTPUT) and os.path.isfile(
        os.path.join(PHASE5_OUTPUT, "phase5_run_report.json"))


def spearman_rho(a, b):
    """Spearman rank correlation without SciPy (not installed in this env
    -- see PHASE6_LOG.md env notes). Standard average-rank tie handling,
    then Pearson correlation of the ranks (mathematically identical to
    scipy.stats.spearmanr's rho for the non-degenerate case)."""
    import numpy as np

    def ranks(x):
        x = np.asarray(x, dtype=float)
        order = np.argsort(x, kind="mergesort")
        r = np.empty(len(x), dtype=float)
        sorted_x = x[order]
        i = 0
        n = len(x)
        while i < n:
            j = i
            while j + 1 < n and sorted_x[j + 1] == sorted_x[i]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0
            r[order[i:j + 1]] = avg_rank
            i = j + 1
        return r

    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) < 2 or np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    ra, rb = ranks(a), ranks(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = float(np.sqrt((ra ** 2).sum() * (rb ** 2).sum()))
    if denom < 1e-12:
        return float("nan")
    return float((ra * rb).sum() / denom)
