"""
Phase 6 orchestrator -- runs T6.1-T6.11 in order and writes each module's
own JSON report under yogesh_dev/phase6/output/ (each module can also be
run standalone; see PHASE6_LOG.md for exact commands). T6.1-T6.3 need a
live PyHelios scene (run in-process, ~1-2 min); T6.4-T6.11 are pure-Python
over Phase 4's already-generated real dataset (fast).
"""

import json
import os
import time

from yogesh_dev.phase6.common import PHASE6_OUTPUT


def main():
    os.makedirs(PHASE6_OUTPUT, exist_ok=True)
    summary = {}

    print("=== T6.1-T6.3 (live PyHelios scene) ===")
    t0 = time.time()
    from yogesh_dev.phase6.t61_t62_t63_gsplat_fixes import run_all as run_t61_t62_t63
    r = run_t61_t62_t63()
    with open(os.path.join(PHASE6_OUTPUT, "t61_t62_t63_report.json"), "w") as fh:
        json.dump(r, fh, indent=2, default=str)
    summary["T6.1_T6.2_T6.3"] = {"elapsed_s": time.time() - t0}

    print("=== T6.4-T6.6 (perception metrics) ===")
    t0 = time.time()
    from yogesh_dev.phase6.t64_t65_t66_perception_metrics import run_all as run_t64_t65_t66
    r = run_t64_t65_t66()
    with open(os.path.join(PHASE6_OUTPUT, "t64_t65_t66_report.json"), "w") as fh:
        json.dump(r, fh, indent=2, default=str)
    summary["T6.4_T6.5_T6.6"] = {"elapsed_s": time.time() - t0}

    print("=== T6.7-T6.9 (planning metrics) ===")
    t0 = time.time()
    from yogesh_dev.phase6.t67_t68_t69_planning_metrics import run_all as run_t67_t68_t69
    r = run_t67_t68_t69()
    with open(os.path.join(PHASE6_OUTPUT, "t67_t68_t69_report.json"), "w") as fh:
        json.dump(r, fh, indent=2, default=str)
    summary["T6.7_T6.8_T6.9"] = {"elapsed_s": time.time() - t0}

    print("=== T6.10 (deadline / closed-loop) ===")
    t0 = time.time()
    from yogesh_dev.phase6.t610_deadline_closed_loop import run_all as run_t610
    r = run_t610()
    with open(os.path.join(PHASE6_OUTPUT, "t610_deadline_closed_loop_report.json"), "w") as fh:
        json.dump(r, fh, indent=2, default=str)
    summary["T6.10"] = {"elapsed_s": time.time() - t0}

    print("=== T6.11 (latency table) ===")
    t0 = time.time()
    from yogesh_dev.phase6.t611_latency_table import run_all as run_t611
    r = run_t611()
    with open(os.path.join(PHASE6_OUTPUT, "t611_latency_table_report.json"), "w") as fh:
        json.dump(r, fh, indent=2, default=str)
    summary["T6.11"] = {"elapsed_s": time.time() - t0}

    with open(os.path.join(PHASE6_OUTPUT, "phase6_run_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
