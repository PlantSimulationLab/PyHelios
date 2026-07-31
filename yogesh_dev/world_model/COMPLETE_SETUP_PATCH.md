# Proposed addition to `yogesh_dev/COMPLETE_SETUP.md`

W7 of `WORLD_MODEL_PLAN.md` asks for a pointer to this work in
`yogesh_dev/COMPLETE_SETUP.md`. That file is outside this task's write scope
(`yogesh_dev/world_model/` only), so the text is proposed here rather than applied —
the same pattern Phase 6 used for the gsplat fixes it could not apply directly.

**Where:** immediately after the "Full plan status: all 9 phases (0-8) complete" section,
before "Upstream patches worth contributing".

**Text to insert:**

```markdown
---

## Follow-on work: world model (post-Phase-8)

### World model — action-conditioned latent dynamics on a 2x10 orchard
`world_model/` · [plan](world_model/WORLD_MODEL_PLAN.md) · [log](world_model/WORLD_MODEL_LOG.md)
· [status](world_model/WORLD_MODEL_STATUS.md) · [findings](world_model/FINDINGS.md)

A DreamerV3-family RSSM (GRU carry + 32x32 discrete stochastic latent) trained to predict
RGB-D + semantics of a simulated 2-row x 10-tree apple orchard under two action channels:
camera pose deltas (seconds) and `advanceTime(dt)` growth (days). Helios is the data
generator; the RSSM is the learned model. Reuses `phase0/radiation_setup.py`,
`phase0/pose_convention.py`, `phase1/label_maps.py`, `phase1/depth_export.py` and
`phase8/canopy_factory.py`'s seeding discipline unchanged.

Three findings that matter beyond this work:

1. **The `apple` growth model is piecewise constant in age.** Every organ count and area
   is bit-identical from 580 d to 730 d, and leaves/fruit are gone by 740 d. The only
   window where geometry actually changes is ~540-580 d. Any experiment that varies plant
   age must check this first — several plausible-looking schedules are no-ops.
2. **Registering N radiation cameras costs the same as registering 1.** Solve time is flat
   at ~4.85 s from N=1 to N=256 on an 830 k-primitive orchard, i.e. 0.019 s/image at
   N=256 versus 4.85 s at N=1. Every render-heavy phase in this repo would benefit.
3. **`advanceTime` on a 20-tree canopy costs 1-5 s**, versus 7-38 s for a rebuild, and is
   equivalent to rebuilding at the target age (organ counts identical, areas agreeing to
   ~1e-7 relative).
```
