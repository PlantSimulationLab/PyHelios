"""
T2.6 -- Validate the proposal's occlusion-regulation module against AVUB.

Before doing anything else here: does an occlusion-regulation module (the
WTFRC proposal's leaf add/remove control that targets a per-fruit occlusion
level) actually exist ANYWHERE in this codebase? Checked by searching every
commit reachable from every branch in this repo (not just the working tree)
for "occlusion.regulat" / "occlusion.control" (case-insensitive):

    git grep -niE "occlusion.regulat|occlusion.control" $(git rev-list --all) --

The only hits are prose *describing* the WTFRC proposal's module, in
`active_vision_design.md` (the design doc being implemented from) and
`helios_setup_tasks.md` (this task list) itself -- e.g. "the proposal's
occlusion-regulation module does" (active_vision_design.md line ~440),
referring to something in the external WTFRC grant proposal this repo is
implementing infrastructure for. No leaf add/remove control, no per-fruit
occlusion target, no calibration sweep of any kind exists as CODE anywhere
in this repository's history.

Conclusion: T2.6 is genuinely blocked on a module that has never been built
here -- not a bug, not a missed search, not something to approximate. Per
the task brief, do not fabricate one. `run_phase2.py` calls
`check_occlusion_regulation_module_exists()` below and records its result
in the run report / log; T2.6 itself is not attempted beyond that.
"""

import subprocess


SEARCH_PATTERN = r"occlusion.regulat|occlusion.control"


def check_occlusion_regulation_module_exists(repo_dir="."):
    """Search every commit on every branch for an occlusion-regulation
    module. Returns a report dict: {"exists": bool, "hits": [...]}."""
    try:
        rev_list = subprocess.run(
            ["git", "rev-list", "--all"], cwd=repo_dir,
            capture_output=True, text=True, check=True,
        ).stdout.split()
        result = subprocess.run(
            ["git", "grep", "-niE", SEARCH_PATTERN] + rev_list + ["--"],
            cwd=repo_dir, capture_output=True, text=True,
        )
        hits = [line for line in result.stdout.splitlines() if line.strip()]
    except Exception as exc:  # pragma: no cover -- diagnostic path only
        return {"exists": None, "hits": [], "error": str(exc)}

    # Every hit is prose in a design/task doc describing the module (not
    # code) iff every hit's path ends in .md. Anything else would mean a
    # real implementation exists somewhere.
    code_hits = [h for h in hits if ":" in h and not h.split(":", 2)[1].endswith(".md")]
    return {
        "exists": len(code_hits) > 0,
        "n_hits_total": len(hits),
        "n_code_hits": len(code_hits),
        "hits": hits,
        "conclusion": (
            "occlusion-regulation module found in code -- T2.6 is NOT blocked"
            if code_hits else
            "no occlusion-regulation module exists anywhere in this repo's history "
            "(all hits are prose in .md design/task docs describing the external "
            "WTFRC proposal's module) -- T2.6 is blocked, skipped honestly per task brief"
        ),
    }
