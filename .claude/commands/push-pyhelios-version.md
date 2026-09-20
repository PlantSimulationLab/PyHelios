---
description: Push a new PyHelios version to GitHub and PyPI
---

## Invariants (these are the rules; the steps below exist to satisfy them)

1. **Never force-push `master`.** Master is append-only. If you are about to force-push it,
   the flow has gone wrong -- stop and re-read this file rather than pushing.
2. **Linear history: exactly one commit per version on master**, subject `[vX.Y.Z] YYYY-MM-DD`,
   matching `docs/CHANGELOG.md`. Never two commits for one version.
3. **No redundant CI between `release` and `master`.** They hold the same SHA; anything that
   runs on both runs twice for nothing.
4. **Master is byte-identical to a fully green `release`.** Master only ever fast-forwards to
   a commit that has already passed everything, wheels included.
5. **`docs.yml` runs on master push.** That is master's only workflow.

Invariants 1 and 2 used to conflict: amending a candidate produces a *sibling* of whatever
master holds, so fixing a post-promotion failure meant force-pushing. The ordering below
removes the conflict by promoting master **last**.

## The ordering (this is the whole design)

```
push candidate to release  ->  pytest x3 + FULL wheel pipeline (build, test, GPU)
                           ->  tag vX.Y.Z on that exact commit
                           ->  publish job finds the green release run for this SHA,
                               downloads ITS wheels, import-checks them, pauses at the gate
                           ->  you approve  ->  published to PyPI
                           ->  ONLY NOW: fast-forward master
```

The wheel pipeline runs **once**, on `release`. The tag run does not rebuild: it locates the
successful release-branch run for the same SHA, downloads those artifacts, verifies they
import on a bare image, and uploads them. The bytes tested are the bytes published.

Master is promoted after the wheels are published, so a wheel failure happens while master is
still untouched -- recoverable by amending the candidate and force-pushing `release`, never by
force-pushing master.

**If no successful release run exists for the tagged SHA, publish fails hard.** There is no
fallback to building in the tag run: a silent rebuild would upload bytes nothing had tested.
A tag cut on a commit that never went through `release` cannot publish. Wheel artifacts have
`retention-days: 7`, so a candidate older than a week must be re-validated before tagging.

## Trigger layout

- `pytest-linux`, `pytest-macos`, `pytest-windows`: push to **`release` only**, plus PRs to
  master/main. Not on master pushes -- master only fast-forwards to an already-green SHA, so
  re-running there would duplicate a three-platform native build (invariant 3).
- `build-wheels.yml`: pushes to **`release`**, plus tags `v*` and `testing-v*`. Its four
  validation jobs (`build_wheels`, `test_wheels`, `test_wheels_slim_container`,
  `test_gpu_wheels`) are gated to `release`/`testing-v*` and **do not run on a `v*` tag**.
  `publish` is gated to `refs/tags/v*` and carries no `needs:` -- depending on jobs that are
  skipped would be vacuous, since GitHub treats a skipped dependency as satisfied. The real
  gate is its "Locate validating release run" step.
- `docs.yml`: pushes to master/main.

**Wheel versions.** Every wheel build pins `SETUPTOOLS_SCM_PRETEND_VERSION`. A tag ref takes
it from the tag name; a release-branch build takes it from the newest `docs/CHANGELOG.md`
heading. This matters because under Option B the release-branch artifacts are what get
published -- when the release branch fell through to setuptools-scm it produced
`pyhelios3d-0.1.32.dev1-*.whl`, which would have reached PyPI as a dev release. A side effect
is a free consistency check: if the changelog heading and the tag disagree, the wheel
filenames will not match the tag.

## 1. Prepare the release commit (on master)

1. Confirm the helios-core submodule pin matches the `- Updated helios-core to vX.Y.Z` line in
   the changelog. These drift independently and nothing in CI checks it:
   ```bash
   git submodule status helios-core
   grep -n "helios-core to" docs/CHANGELOG.md | head -1
   ```
2. Set the date on the newest `docs/CHANGELOG.md` entry to today; make the commit date match.
3. Squash all commits for this version into one, message matching the changelog entry.

If the commit touches `native/src/*`, `native/include/*`, ctypes wrappers, or core
functionality, CLAUDE.md's **Full Verification Protocol** applies before anything is pushed:
a clean rebuild (`build_scripts/build_helios --clean`) and the full suite (`pytest`, with
`forked-X.X.X` in the plugin line), plus the selection CI uses:

```bash
HELIOS_NO_GPU=1 pytest -m "not requires_gpu and not slow"
```

## 2. Validate everything on the release branch

```bash
git push -f origin <candidate-sha>:refs/heads/release
gh run list --branch release
```

This runs the three `pytest-*` workflows **and** the full wheel pipeline. Wait for all of them.

Poll runs by explicit ID (`gh run view <id>`). `gh run list --json` can return a different
result set than the plain listing and may show stale runs from previous releases.

If anything fails: fix on the candidate, `git commit --amend`, and force-push `release` again.
Force-pushing `release` is safe -- nobody pulls it and it never becomes history. Repeat until
green. **Master is not involved in this loop at all.**

## 3. Tag and publish

Only once every release-branch run is green:

```bash
git tag vX.Y.Z <candidate-sha> && git push origin vX.Y.Z
```

The tag run does not rebuild. It resolves the green release run for this SHA, downloads its
wheels, import-checks them on a bare `python:3.12-slim` image, then **pauses**: the `pypi` environment
has a required reviewer, so `publish` waits for manual approval. Review, then approve.

If a job fails before `publish`, nothing was uploaded and master is still untouched. Delete
the tag, fix via `release`, and re-cut the **same** version:

```bash
git push origin --delete vX.Y.Z && git tag -d vX.Y.Z
```

Note `can_admins_bypass` is true on the `pypi` environment: an admin *can* skip the gate, so
treat it as a deliberate checkpoint, not a hard lock.

## 4. Promote master (last)

Only after `publish` has succeeded:

```bash
git push origin <candidate-sha>:refs/heads/master   # must be a true fast-forward
```

Verify first that the candidate's parent is the current remote master. If it is not, do **not**
force-push -- that means master moved, and the candidate must be rebuilt on the new tip.
Pushing master triggers `docs.yml` only.

## 5. Clean up

```bash
git push origin --delete release   # optional
```

Safe only *after* step 4: the commit is then held by both the tag and master. Deleting
`release` before the tag exists would orphan the candidate. The branch is a per-release
workspace -- recreate it next time; the `pytest-*` and wheel triggers depend on the name.

## When to use a testing-v* dry run

Rarely, now that the full pipeline runs on `release`. Reach for `testing-v*` only to rehearse
the *tag-specific* path -- the version-from-tag derivation and the publish gate -- e.g. after
editing `build-wheels.yml`'s version step. It runs everything and cannot publish.

## Recovery

- **Wheel build fails after tagging:** delete the tag, amend the candidate, force-push
  `release`, re-validate, re-tag. Master is untouched throughout.
- **Master is somehow red or holds a bad commit:** this should be impossible under this
  ordering. If it happens, the flow was not followed -- work out which step was skipped before
  reaching for a force-push, and fix this file so it cannot recur.
- **Candidate is a sibling of master, not a descendant:** master was promoted too early.
  Do not force-push master. Rebuild the candidate on the current master tip instead.

## After a successful publish

A problem found after publish gets a new patch version, never a re-cut:

- `git fetch` will not update an existing tag, so anyone who pulled inside the window keeps the
  stale one with no signal anything changed.
- PyPI reserves the filename permanently. Re-releasing a fixed `0.1.X` needs a `.postN` suffix
  and the corresponding `case` entry in `build-wheels.yml`.
