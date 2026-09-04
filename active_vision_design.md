# Multi-Camera Active Vision for Apple Harvesting — Research Design

**Stage 1: Helios simulation.** Companion to WTFRC proposal *Robotic Harvesting: Multi-Camera Fruit Detection Under Heavy Occlusion* (Vougioukas, Bailey, Kong), Objective 2 and 3.

*Prepared July 2026. Literature current to mid-2026. Verification caveats are collected in the final section — several 2026 arXiv entries and paywalled numbers should be confirmed before they enter a thesis or paper.*

---

## 0. Executive summary — six claims

1. **Vanilla 3DGS is offline, and the reason it is the wrong primary map is not speed — it is that Gaussians represent only *occupied* space.** For a next-best-view planner, *unknown* space is the entire signal. Every serious active-3DGS system in the literature (ActiveGS, GS-Planner, HGS-Planner, ActiveGAMER, NARUTO) bolts a voxel map on the side to fix exactly this. Build the voxel map as the primary substrate and run splatting asynchronously for appearance.

2. **In Helios you have exact camera poses, so you should not run SLAM at all.** Tracking is where most of the compute and nearly all of the fragility of GS-SLAM systems lives. You need a *mapper*, not a SLAM system. This deletes roughly half the engineering in the proposal's Objective 2 and buys you the resolution you actually need.

3. **Exploration and exploitation are not two settings of one objective — they are structurally different optimization problems**, and conflating them is the single most common mistake in this literature. Explore is *quality-constrained* (see everything → minimize time), exploit is *budget-constrained* (fixed time → maximize value). Maximizing information gain during exploration is provably counterproductive. This split is your architectural backbone and it is a defensible novel framing.

4. **Your five DOF are not five equal DOF.** The 2 gimbal axes are ~free; the 3 linear axes are 0.5–3 s each. Nest a cheap gradient-based gimbal refinement inside an expensive sampling-based linear-axis path planner. This decomposition matches your hardware exactly and I could not find it published.

5. **Do not start from VGGT.** Start from a *pose-conditioned* geometry model — MapAnything (Apache-2.0 code and weights) or Depth Anything 3. Your defining asset is that you know the poses; three models released since Sept 2025 are built to consume exactly that, and there is a hard theoretical reason (15-DoF projective ambiguity under small baselines) to expect the uncalibrated path to fail on a canopy scanned through a narrow arc.

6. **The evaluation should be built around three quantities that no field paper can compute**: the Achievable Visibility Upper Bound (what fraction of each fruit is visible from *any* reachable pose), the oracle-normalized planning score Π, and an information-gain calibration score adapted from the optical-flow sparsification literature. These convert "we detected 70% of fruits" — a number that mixes canopy difficulty, hardware limits and algorithm quality — into three separable numbers.

---

## 1. Reframing the problem statement

The proposal says, in effect:

> multi-camera SLAM → 3DGS map → semantic fusion → NBV planner reading the 3DGS map

I would restructure this. The pipeline as written puts a representation that cannot express ignorance at the center of a system whose whole job is to reason about ignorance. Concretely:

| Proposal component | Recommendation | Why |
|---|---|---|
| Multi-camera SLAM for pose | **Drop in Stage 1.** Poses come free from Helios; on the robot they come from arm encoders + a one-time hand-eye calibration, with Kong's SLAM device as a correction/drift term, not the primary source | You have a *gantry*, not a handheld sensor. Encoder-derived pose is better than visual pose in a self-similar canopy, where vision-only 3DGS-SLAM catastrophically fails (see §2.3) |
| 3DGS as the map the planner reads | **Demote to a secondary, asynchronous appearance map.** Primary map = GPU occupancy octree with explicit unknown state | 3DGS cannot represent unknown space; it also systematically renders thin geometry as low-opacity haze, which is the wrong failure mode for a canopy |
| Semantic splats | **Keep the idea, move it to the voxel layer.** Per-voxel semantic posterior p(apple), p(leaf), p(branch), p(wire) | The planner needs semantics on the thing it ray-casts against |
| Single NBV planner with 3 weighted criteria | **Two planners with different objectives**, plus a nested fast local refinement | See §4 |
| "Number of fruits discovered, location/size accuracy, exploration time per fruit" | **Five-tier evaluation suite**, headlined by AVUB/NVE and Π | See §7 |

Everything else in the proposal — the occlusion-regulation module, the Helios orchard, the physical evaluation protocol — I would keep as written. Those are strengths.

### 1.1 The physical scales that govern every decision

Write these on the wall, because most published performance numbers were measured 100× coarser:

| Structure | Scale |
|---|---|
| Apple leaf lamina thickness | 0.15–0.3 mm |
| Petiole / young twig diameter | 2–10 mm |
| Trellis wire | 2–3 mm |
| Fruit diameter | 60–90 mm |

Nearly every mapping benchmark you will read (nvblox 0.4 ms/frame, voxblox 70 ms, wavemap memory tables) was run at **5 cm voxels on indoor rooms** — 150–300× a leaf thickness. Going to 1 mm voxels is a 50× linear increase, implying 10³–10⁴× more work. **Re-derive your compute budget at your own resolution before committing to any architecture.** This is the most likely way the project's real-time claim quietly fails.

---

## 2. Real-time reconstruction

### 2.1 Yes, vanilla 3DGS is a post-process — for four separable reasons

Kerbl et al.'s 3DGS ([arXiv:2308.04079](https://arxiv.org/abs/2308.04079)) is offline because:

1. **Per-scene optimization.** The Gaussians *are* the free parameters. No learned prior; every scene is a fresh gradient-descent problem, 7k–30k iterations.
2. **COLMAP dependency.** Poses and the seed point cloud come from batch SfM — often slower than the splatting it feeds.
3. **Batch view sampling.** The optimizer samples randomly from *all* images every iteration. Not causal; adding an image invalidates convergence state.
4. **Adaptive density control is a global annealing heuristic.** Clone/split/prune from statistics accumulated over the whole image set, with periodic opacity resets.

Recent work attacks 1–3 separately. Point 4 is the least solved and is quietly the source of most artifacts in incremental systems.

### 2.2 The online variants exist, but the honest speed spread is 400×

RGBD GS-ICP SLAM's benchmark is the most useful artifact in this literature because it puts everything on one RTX 4090:

| System | FPS (RTX 4090, Replica) |
|---|---|
| Point-SLAM | 0.30 |
| SplaTAM ([2312.02126](https://arxiv.org/abs/2312.02126)) | 0.23 |
| GS-SLAM | 8.34 |
| Orbeez-SLAM | 24.15 |
| RGBD GS-ICP SLAM ([2403.12550](https://arxiv.org/abs/2403.12550)) | **98.11** |

Anyone saying "real-time 3DGS SLAM" without naming a system is making a meaningless claim. And note *how* GS-ICP buys its speed: by leaning entirely on the depth sensor and skipping photometric optimization. On thin foliage, RGB-D depth is at its noisiest and most flying-pixel-prone. The speed/robustness trade is aimed away from your scene.

Others worth knowing: MonoGS ([2312.06741](https://arxiv.org/abs/2312.06741), 3 FPS, monocular), Photo-SLAM ([2311.16728](https://arxiv.org/abs/2311.16728), runs on Jetson Orin), RTG-SLAM (SIGGRAPH 2024, [2404.19706](https://arxiv.org/abs/2404.19706)), LoopSplat (3DV 2025, loop closure causes latency spikes — bad for a fixed-rate control loop), WildGS-SLAM (CVPR 2025, [2504.03886](https://arxiv.org/abs/2504.03886)) — that last one is a cautionary tale: it identifies and *deletes* dynamic objects, which in a windy canopy means deleting the canopy.

### 2.3 The orchard evidence is damning for vision-only splatting

AgriGS-SLAM ([2510.26358](https://arxiv.org/abs/2510.26358), Usuelli/Rapado-Rincón/Kootstra/Matteucci) is the paper your proposal cites. Read its **baseline** table, not its headline:

| Method (apple orchard, dormancy) | PSNR | ATE (m) |
|---|---|---|
| AgriGS-SLAM (visual + LiDAR) | 29.90 | **0.519** |
| DLO + 3DGS | 25.05 | 0.576 |
| Splat-SLAM | 19.69 | 5.26 |
| OpenGS-SLAM | 12.97 | **20.70** |
| Photo-SLAM | 8.16 | **18.95** |

Photo-SLAM and OpenGS-SLAM do not degrade in an orchard — they *diverge*, by 19–21 metres. Two CVPR-caliber systems, total failure. AgriGS-SLAM only works because a 32-beam LiDAR is carrying the pose estimate, and even then its own ATE is 0.52 m, which is enormous for a system meant to produce per-fruit geometry.

Also note what the paper does *not* contain: no GPU model, no runtime, no FPS anywhere in the experiments, and no thin-structure evaluation despite a densification rule explicitly motivated by "leaves and thin branches." That is a conspicuous hole and an opening for you.

Other agricultural radiance-field work, for context: FruitNeRF (IROS 2024, [2408.06190](https://arxiv.org/abs/2408.06190)) — 12 min to 2.5 h training, authors state plainly it is "not yet suitable for real-time applications," degrades under wind. PAg-NeRF (RA-L 2023, [2309.05339](https://arxiv.org/abs/2309.05339)) — ~27 min training, 5.6 s/image inference, explicitly names thin structures as a challenge. GrowSplat (CASE 2025) — multi-session, offline alignment.

### 2.4 The decisive argument is representational, not computational

ActiveGS ([2412.17769](https://arxiv.org/abs/2412.17769)) states it directly:

> "the Gaussian primitives represent only occupied space, making it hard to distinguish between unknown and free space, which are important for exploration and path planning."

GS-Planner concurs. For an NBV planner, "I have never looked here" **is** the signal. A representation structurally incapable of expressing it cannot be the primary substrate for exploration no matter how fast it runs.

The same argument disqualifies **surfel maps** (ElasticFusion, SuMa) entirely, and it partially disqualifies **TSDF**. In a TSDF, weight w=0 conflates three distinct conditions: never observed; observed but beyond truncation in front of the surface; and behind the surface, permanently occluded. That conflates "I should look here" with "I can never see here" — opposite conclusions for a planner. You can disambiguate by space carving, but carving is precisely the mechanism that destroys thin structures.

**The thin-structure mechanism, precisely.** A TSDF encodes a surface as a zero crossing between a positive and a negative band of thickness τ. This requires the object be thicker than ~2τ. A leaf thinner than τ has back-face rays writing negative-then-positive into the same voxels front-face rays wrote positive-then-negative; the updates destructively average toward zero and **the surface dissolves**. Space carving makes it worse: a ray grazing a leaf edge, or a mixed pixel at a depth discontinuity (endemic on RealSense-class sensors over foliage), carves free space straight through neighbouring leaf voxels. **The failure mode is that the more views you take, the more foliage disappears** — catastrophic for a system whose entire premise is taking more views.

The cleanest published evidence is wavemap (RSS 2023, [2306.01279](https://arxiv.org/abs/2306.01279)), which ran the controlled comparison and reported that TSDF (voxblox) "has better [surface] reconstruction performance while our approach is better at reconstructing thin objects" — illustrated by the chair that **is missing its legs** in the voxblox reconstruction. Their named target class is "thin objects such as branches, cables, or fences." That maps almost exactly onto twigs, trellis wires, and canopy support structure.

By contrast, an **occupancy log-odds map with a proper beam model degrades gracefully**: a leaf thinner than a voxel produces a voxel converging to intermediate occupancy — which is *correct*, and which is *high entropy*, so an NBV planner naturally wants to re-observe it. A TSDF forced to place a zero crossing with insufficient thickness places nothing. For a leaf-dominated scene that asymmetry is the whole argument.

3DGS has the analogous bias for a different reason: the photometric loss is nearly as well satisfied by a fat, low-opacity Gaussian that blurs a leaf into its background as by a correctly thin one, and the latter has weaker gradient support. **3DGS systematically represents thin high-frequency geometry as semi-transparent haze.** It renders beautifully and is geometrically wrong — exactly the failure you cannot tolerate when the downstream consumer is a grasp planner deciding whether an apple is occluded.

### 2.5 What I would actually build

**Primary substrate: a GPU-resident, multi-resolution occupancy map with explicit unknown state.**

- **Three-state semantics from UFOMap** (RA-L 2020, [2003.04749](https://arxiv.org/abs/2003.04749)): occupied / free / **unknown** as first-class states, with inner nodes tagged by which states their subtree contains. This makes "does this frustum contain unknown volume?" an O(depth) query instead of O(leaves), and makes frontier extraction native. The reason every agricultural NBV paper reports 0.5–1.5 s planning cycles is that they all use OctoMap, where unknown is represented by *absence* and must be discovered by raycasting one step at a time.
- **Sensor model from wavemap**: uncertainty-aware beam model over both range σ_r *and angular* σ_θ. Their ablation shows this specific component is what recovers thin structures. It also makes voxel entropy H(p) a real quantity, so expected information gain E[ΔH] is well-posed rather than a heuristic unknown-voxel count.
- **Dual resolution**, following Freeman & Kantor's apple-fruitlet work ([2309.13669](https://arxiv.org/html/2309.13669)): coarse ~1–2 cm map over the whole canopy, fine ~3 mm maps instantiated on demand as "attention regions" around fruit clusters. GS-NBV runs a 3 mm semantic OctoMap for avocado at ~1.5 s/cycle on a laptop GPU, so millimetre-scale occupancy is demonstrably tractable.
- **Semantic layer**: per-voxel class posterior, fused from 2D detections/segmentations projected through known poses.
- **GPU-batched information-gain raycasting.** This is the single highest-leverage engineering decision in the project. In GS-NBV, viewpoint evaluation is 1.473 s of a 1.576 s cycle — **93% of the loop**. It is embarrassingly parallel. And **no agricultural NBV paper has done it**, because they are all on CPU OctoMap. That is your speedup and it is large.

**Secondary, asynchronous: splatting for appearance and refinement scoring.** Run off the critical path, gated by an HGS-Planner-style coverage weight λ_o (the fraction of observed voxels in the local region): while a region is unexplored, drive purely on voxel IG; as λ_o → 1, let a Gaussian-derived quality term take over to decide which already-observed surfaces need a better look. HGS-Planner ([2409.17624](https://arxiv.org/abs/2409.17624)) writes this as G = G(C) + λ_o·G(Q), which is the field's own equation for "Fisher information only works once coverage is achieved."

Two notes on the splatting branch:
- If your deliverable is canopy *surface/structure* rather than novel views, use **2DGS**, not 3DGS (cf. Sparfels, [2505.02178](https://arxiv.org/abs/2505.02178)).
- **Feed-forward 3DGS is genuinely interesting for you and under-explored in agriculture**, for one specific reason: three cameras with known 5-DOF poses give you a *calibrated multi-view rig with commandable baseline* — the ideal input regime for MVSplat ([2403.14627](https://arxiv.org/abs/2403.14627), ~45 ms/forward pass) or GS-LRM-class models. A 45 ms forward pass producing canopy Gaussians is genuinely real-time. The catch is that all of these are trained on RealEstate10K/ScanNet++/DTU — indoor real estate, not foliage — and cost-volume methods will suffer most because photo-consistency matching fails on repetitive leaf texture. Helios is exactly the fix: you can render unlimited canopy views with perfect ground truth and *retrain or fine-tune*, and you have the ground truth to evaluate it honestly. That is a legitimately strong paper on its own.

**The trick worth stealing** from GS-Planner / HGS-Planner / MAGICIAN: rather than keeping two maps separate and fusing scores at the end, **make unknown space renderable** — inject unknown voxels as primitives into the same rasterizer as the Gaussians. Then coverage gain and quality gain both come from *one render pass per candidate pose*, at rasterizer speed, instead of a CPU raycast plus a GPU render.

**Cheapest viable fallback:** ActiveGS's confidence accumulator, k_i = γ_i·exp(β_i) with γ_i = Σ_j (1 − d_ij/d_far)·n_i·v_ij. No gradients, no backward pass — a running per-primitive accumulator that captures the two things that matter for apples: were you close and face-on, and did you see it from diverse angles.

### 2.6 What "real-time" actually needs to mean here

Define it as **p99 decision latency ≤ the deadline it must meet**, and report mean/p95/p99/max. Mean latency conceals exactly what breaks closed-loop systems.

Then note the structural slack in your favour: **arm motion dominates.** A 5-DOF viewpoint change takes 0.5–3 s (gimbal retargets in a few hundred ms; linear stages are slow). An NBV decision taking 200–500 ms is effectively *free* — it hides under motion. The reason to go faster is not loop rate; it is that you can evaluate **more candidate viewpoints** in the same wall-clock, which is what actually improves NBV quality. **Budget for candidate count, not for latency.**

And: **do not integrate at frame rate.** Three cameras at 30 Hz is 90 frames/s, but with known poses and a mostly-static canopy you only need to integrate when a camera has *arrived somewhere new*. Frame-rate integration is a SLAM habit, not a requirement. Keyframe-on-arrival (~1–3 Hz per arm) cuts integration load by an order of magnitude and buys back the resolution you need for leaves.

**Recommended budget:**

| Stage | Target | Ceiling |
|---|---|---|
| Map integration, per keyframe per camera | 30–100 ms | — |
| IG evaluation (all candidates, all arms) | 200–500 ms | 1.5 s |
| Motion planning to selected viewpoint | 20–50 ms | — |
| **End-to-end per viewpoint decision** | **~250 ms** | **~2 s** |

against 0.5–3 s of arm motion. Healthy headroom. For reference, FUEL does full UAV exploration replanning in 24 ms on a laptop CPU; HGS-Planner does a full cycle in 129–151 ms; the agricultural literature sits at 1.5–20 s.

---

## 3. Moving the cameras: exploiting the 5-DOF cost asymmetry

### 3.1 The structural insight

Your five DOF per camera decompose into two classes with radically different cost:

| DOF class | Axes | Motion cost | Workspace effect |
|---|---|---|---|
| **Linear** | left-right, up-down, in-out | 0.5–3 s, collision-relevant, shared corridor | Changes *position* → changes what is occluded |
| **Gimbal** | pan, tilt | ~0.1–0.3 s, collision-free, no shared resource | Changes *what is in frame* → cannot resolve occlusion |

This asymmetry is not incidental — it maps onto a real algorithmic split. Position changes are what defeat occlusion; orientation changes only re-aim. So:

**Outer loop (expensive, sampling-based): plan positions over the 3 linear axes.**
**Inner loop (cheap, gradient-based): refine orientation over the 2 gimbal axes.**

For the inner loop you have two ready-made options, and they are the same idea arrived at from opposite directions:

- **Burusa et al., Gradient-based Local NBV** (ICRA 2024, [2311.16759](https://arxiv.org/html/2311.16759)). Make the utility differentiable through the ray sampling and do gradient ascent on camera pose — visual-servoing the camera up the semantic-IG gradient. Reported vs their own sampling-based semantic NBV: **10× less computation, 28% more efficient trajectories, equivalent accuracy.**
- **Lehnert et al., 3D Move-to-See** (IROS 2019, [1809.07896](https://arxiv.org/abs/1809.07896)). Estimate the *spatial gradient* of a semantic objective by finite-differencing across a physical camera array, then servo along it. **This is structurally exactly your three-camera rig.** You can estimate the gradient without moving anything, then move all three arms along it. No map, no ray casting, one control cycle.

Gimbal motion is nearly free relative to linear-axis motion, so this nested refinement is essentially a free 10–30% improvement. **I could not find this decomposition published, and it matches your hardware precisely. That is a paper.**

### 3.2 Precompute a reachability/visibility roadmap

Do not run IK and collision checking inside the planning loop. Once per cart position:

- Sample the 5-DOF joint space densely per arm → forward kinematics → camera pose.
- Reject self-collision and canopy collision (Helios's `CollisionDetection` plugin does this; see §6).
- Nodes = surviving poses with IK cached. Edges = k-NN in joint space, **edge weight = actual execution time** under your trapezoidal velocity profiles.

Because your linear axes are decoupled and gimbal motion is cheap, edge cost is nearly analytic — you don't need MoveIt in the loop. This is Zaenker et al.'s graph-based VMP structure (IROS 2023, [2303.03048](https://arxiv.org/abs/2303.03048)) adapted to a much simpler kinematic chain, and it turns planning into graph search.

**Two practical findings from the literature you should honour:**
- **Do not cast rays outward from targets to generate candidate views.** Zaenker explicitly reports this fails in confined workspaces — reachability rates are too low. Sample view poses *from the reachable workspace, looking at* targets. [arXiv:2412.10515](https://arxiv.org/abs/2412.10515) independently confirms frontier-sampled candidates have poor arm reachability.
- **Normalize gain by execution time, always.** Zaenker names this as their single most important design decision.

### 3.3 Three-arm coordination

**Enforce non-overlapping vertical bands per arm.** With three arms in horizontally-stacked cells, this makes arm–arm collision *structurally impossible*, and coordination reduces to (i) managing the shared in-out extension corridor and (ii) deciding what each arm looks at. That trades a small loss of optimality for an enormous reduction in planning complexity, and it is how the Vougioukas hardware already works.

**For the assignment, use sequential greedy over a submodular objective:**

```
A ← ∅
for i = 1 … 3:                    # randomize arm order each round
    a_i ← argmax_{a ∈ A_i}  F(A ∪ {a}) − F(A)
    A ← A ∪ {a_i}
```

Fifteen lines of code, and it carries a real guarantee: F(A_seq-greedy) ≥ ½·F(A*) for monotone submodular F under a matroid constraint (Fisher–Nemhauser–Wolsey). Redundancy is eliminated *structurally* — once arm 1 commits to a cluster, that cluster contributes zero marginal gain to arms 2 and 3. Randomized ordering avoids systematic bias (Corah & Michael, Auton. Robots 2019).

**Watch out for a specific hazard here.** Three cameras choosing simultaneously is a *set* selection problem, and **modular criteria have no diminishing returns, so all three arms will converge on the same maximally-informative view.** POp-GS ([2503.07819](https://arxiv.org/abs/2503.07819)) gives direct evidence: FisherRF's criterion fails at batch selection, 18.37 dB vs D-optimality's 24.53 dB, a 6.16 dB diversity gap. Use a genuinely submodular objective — log-det is submodular, plain trace is not. I found no agricultural NBV paper handling multi-camera batch selection correctly.

**Also exploit what three simultaneous cameras give you that one moving camera cannot:**
1. Instantaneous gradient estimation (§3.1).
2. **Instantaneous occlusion resolution** — a voxel occluded from camera 1 but visible from camera 2 is resolved *now*, not after a motion. The joint visibility V(ξ₁,ξ₂,ξ₃) is what matters.
3. Immediate stereo baseline widening for depth on thin structures where RGB-D fails.
4. **Cross-view data association at zero latency** — three simultaneous views of one apple make instance re-ID far easier than three sequential views with motion between them.

### 3.4 The cart is an outer loop, and it makes the problem time-dependent

A viewpoint available now may be unreachable after the cart advances. Solve over an **overlapping window** of the row rather than the whole row, re-solving as the cart moves — the MPC-style approach your own group already uses for harvest scheduling.

Cart speed then becomes a decision variable coupling everything: slower = more views per tree = better recall = lower throughput. **Plot the recall-vs-throughput Pareto front as a function of cart speed.** That is the plot a harvesting audience actually wants, and it is not in any active-vision paper I found.

---

## 4. Exploration then exploitation

### 4.1 Why they need different objectives, not different weights

This is the most important algorithmic idea in this document.

Ericson, Molina & Jensfelt, *Information Gain Is Not All You Need* ([2504.01980](https://arxiv.org/abs/2504.01980)), make a sharp argument. If you are **quality-constrained** — you *must* cover everything — then the total information to be gathered is **a constant**, fixed by the requirement. Maximizing per-step gain therefore just *reorders the same work*, and does so badly: it chases distant high-entropy regions and accumulates frontier "debt" requiring backtracking. Their numbers: a simple distance-advantage heuristic gave 16% shorter paths than nearest-frontier, while IG maximization was **23% worse** than nearest-frontier, with 2× the frontier debt.

If you are **budget-constrained** — fixed time, take the most valuable subset — then IG maximization is exactly right.

Your Phase 1 is quality-constrained (see the whole tree). Your Phase 2 is budget-constrained (spend the remaining time where the apples are). **So they should not share an objective function.** This is a clean, defensible architectural claim and, as far as I can tell, nobody has framed agricultural active vision this way.

### 4.2 Phase 1 — EXPLORE

**Objective:** min T(P) subject to ∪_{ξ∈P} V(ξ) ⊇ S_reachable.

**Define "seen" honestly.** A surface element s is *covered* iff there exists a taken view ξ with s ∈ FOV(ξ), unoccluded, at range d ∈ [d_min, d_max], and incidence angle θ_s ≤ θ_max. The range gate and incidence-angle gate are essential for RGB-D on thin structures and are routinely omitted in papers — which is one reason simulated results don't transfer.

**You cannot guarantee 100% coverage** and should not claim it. Some canopy surface is geometrically unreachable — interior branches fully enclosed by foliage. What you *can* guarantee is coverage of the **reachable-visible subset**, and the frontier criterion determines this automatically: when no surface frontier is reachably visible, you are done. Define the guarantee that way and it is defensible.

**Frontier definition must be re-derived** — you are covering a *surface*, not exploring free space:
- **Surface frontier:** occupied voxel adjacent to unknown → the tree surface is not yet delineated here.
- **ROI frontier:** apple-labelled voxel adjacent to unknown → there may be more apple here.
- **Free-space frontier:** the classical one, for gross workspace coverage.

**Planner:** receding-horizon path search over the roadmap, utility

    U(ψ) = |∪_{ξ∈ψ} V_new(ξ)| / T(ψ)

Execute the first 1–2 edges, replan. Horizon 3–5 views. This is Bircher et al.'s RH-NBVP structure with a coverage numerator and a time-normalized denominator.

The coverage function F(A) = |∪ V(ξ)| is **monotone submodular** by construction, so greedy gives (1−1/e) ≈ 0.632 of optimal for the cardinality-constrained problem, and cost-benefit greedy with the CELF lazy-evaluation trick gives ½(1−1/e) under a time budget. Use CELF — because marginal gains are non-increasing you keep a max-heap of stale gains and only recompute the top element, typically 10–100× cheaper.

**Be honest about the guarantee.** (1−1/e) holds for the *set* problem. Once you add ordering and travel you are in orienteering territory and the best known bound for submodular orienteering is O(log OPT). Don't overclaim.

**Baselines you must beat**, and one you might not:
- Boustrophedon raster over the 3 linear axes at fixed gimbal angles. **This is the real commercial competitor.**
- Ericson's "distance advantage" nearest-frontier variant — five lines of code, and it beat IG maximization by ~39 percentage points of relative path length. Implement it; it may win.

> ⚠️ **A risk you should test in week 2, not month 6.** For a fruiting-wall / V-trellis canopy with a cart moving along the row, the geometry is quasi-planar, and raster scanning is genuinely competitive. The tomato-greenhouse papers report large NBV gains partly because tomato plants are fully 3D. **If the explore-phase gap over raster turns out small, say so early and shift the emphasis to the exploit phase**, where the gains from occlusion reasoning are large regardless of canopy planarity. Reviewers will ask about this.

### 4.3 The switch — three criteria, take the disjunction

**(a) Frontier exhaustion.** No reachable, visible surface frontiers remain. Hard guarantee, no tuning. Downside: the tail is expensive, since the last few frontiers are deep in the canopy. Mitigate with a reachability filter and a per-frontier attempt limit.

**(b) Marginal value theorem.** Because F is submodular, marginal gain is non-increasing in expectation. Stop when

    ΔF(ξ_t) / c(ξ_t) < η

i.e. when *gain per unit time* falls below a threshold. Set **η equal to the predicted gain rate of the exploit phase**, and the switch happens automatically at the moment exploiting becomes more valuable per second than exploring. This is the economically correct rule and it unifies the two phases with one number. **Recommend as primary.**

**(c) Good–Turing / Chao1 coverage estimate on apple discoveries.** Track new *apple instances* found. This is formally a species-discovery problem. With f₁ apples seen in exactly one view and f₂ seen in exactly two, the estimated number of *unseen* apples is

    f̂₀ ≈ f₁² / (2f₂),    Ĉ = 1 − f₁/n

Stop exploring when Ĉ > 0.95. **I found no use of this in robotic active vision.** It gives you a statistically principled answer to "have I found all the apples?" that depends on no voxel map, no reconstruction, and no tuning. It also directly answers the proposal's stated interest in "the rate of new fruit discovery." **This is a genuinely novel and cheap contribution — do it.**

Also enforce a **hard cap** T_explore ≤ ρ·T_total. Start at ρ = 0.4 and **sweep it** — the explore/exploit budget split is a first-class experimental variable and one of your best plots.

*A fourth option worth knowing:* Zaenker's VMP uses no hard switch at all — instead a **probabilistic mixture** over the three frontier types with user-set weights. That is a softer blend and arguably more elegant. Compare against it.

*A fifth, cheap and Helios-native:* train a **learned map-completeness estimator** (Luperto et al., [2406.13482](https://arxiv.org/html/2406.13482) — 92.9% accuracy, 31–37% time saved). You have unlimited ground-truth partial-vs-complete tree pairs, so training one is nearly free.

### 4.4 Phase 2 — EXPLOIT

**Objective:** max F(P₁ ∪ P₂ ∪ P₃) s.t. T(P_j) ≤ B_j. This is a **submodular team orienteering problem**. Your own group already speaks this language — Vougioukas's lab formulated multi-arm harvest scheduling as a time-dependent team orienteering problem and later as a minimum-makespan VRP (Zhu & Vougioukas, [2505.10028](https://arxiv.org/html/2505.10028)). **Reuse that formulation for *views* rather than *picks*.** The mapping is exact and it gives you a decoupling template (assignment → timing → trajectory) plus their yielding rules for free.

**Value function** — make it submodular by construction:

    F(A) = Σ_i w_i · φ( Σ_{ξ∈A} q_i(ξ) ),    φ(z) = 1 − e^(−z)

where
- **q_i(ξ)** = view quality of apple i from ξ = (visible surface fraction) × (incidence-angle term) × (range validity gate) × (predicted detector confidence)
- **w_i** = apple priority: low observation count, high current occlusion, high size-estimate uncertainty, or high prior p̂_apple
- **φ concave ⇒ F submodular ⇒ greedy guarantees apply.** The fourth view of an apple is worth less than the second, which is exactly right.

**Include predicted-but-never-seen apples** with a discount factor. Which brings us to the strongest original idea available here.

### 4.5 The fruit-occupancy prior — where to look for fruit you have never seen

All existing shape-completion work (NBV-SC's superellipsoids, Pred-NBV's PoinTr-C, DM-OSVP++'s diffusion) completes *partially visible* fruit. **Nobody predicts the location of fruit that is 100% occluded.** Yet that is the dominant failure mode in apple harvesting — your own lab addresses it with physical foliage agitation precisely because vision alone can't see fully-hidden fruit.

**Helios makes this uniquely tractable.** You have complete ground-truth canopies with known fruit positions, so you can learn

    p̂(apple at x | observed canopy geometry near x)

conditioned on local branch structure, foliage density, height, and distance from the trunk — all strongly predictive, because apples grow on spurs at characteristic positions relative to branch architecture. Then the exploit-phase gain becomes

    I_exploit(ξ) = Σ_x P_vis(x) · p̂_apple(x) · H(x)

i.e. you preferentially look where apples are *likely*, even where you have never seen one. No published work does this; it is Helios-native; and it directly serves the harvesting objective rather than a generic reconstruction objective.

A useful simplification: for apples, a diffusion model is overkill. Apple *shape* is a very strong prior — near-spheres of known size distribution — so a parametric sphere/superellipsoid prior with a learned size distribution gets you 90% of the benefit at 1% of the cost.

### 4.6 Data association: what "seen at least once" is defined over

**This is a gap you must close explicitly.** With three cameras and a moving cart, "have I already seen this apple?" is a *data-association* problem, not a mapping problem. Count apples in a voxel map and you will double-count under registration error; track instances and you will not.

**Define your coverage guarantee over tracked apple instances, not voxels.** Maintain a 3D multi-object track database with re-ID descriptors, per-instance observation count, confidence, estimated pose and size. Rapado-Rincón's Wageningen thesis is the reference; Wang et al. 2025 (the paper your proposal already cites) makes the point that multi-view active vision is only useful *if* you can associate detections across views — otherwise extra views produce duplicate counts rather than better recall.

Budget real effort for this. It is unglamorous and it will otherwise silently corrupt every headline number.

### 4.7 Summary of the planner architecture

```
CART (outer, MPC over overlapping row window; speed = decision variable)
  │
  ├─ SHARED REPRESENTATION (one process, all 3 arms)
  │    • coarse occupancy octree, ~2 cm, 3-state, + semantic posterior
  │    • fine octree, ~3 mm, instantiated per fruit cluster
  │    • apple instance track database  ← "seen once" defined here
  │    • fruit-occupancy prior p̂(apple | local canopy geometry)
  │    • reachability roadmap per arm (IK + collision precomputed,
  │      edge weight = real execution time)
  │    • [async] 2DGS/3DGS appearance map, gated by λ_o
  │
  ├─ PHASE 1: EXPLORE   — quality-constrained
  │    objective:  min time  s.t.  coverage ⊇ reachable surface
  │    method:     submodular max-coverage + CELF + RH path search
  │    coordination: sequential greedy, randomized arm order, ½ guarantee
  │    switch:     frontier exhaustion ∨ marginal-value-rate ∨ Good–Turing Ĉ>0.95
  │                (hard cap ρ·T_total, sweep ρ)
  │
  └─ PHASE 2: EXPLOIT   — budget-constrained
       objective:  max Σ w_i φ(Σ q_i(ξ))  s.t.  T(P_j) ≤ B_j
                   = submodular team orienteering
       method:     cost-benefit greedy + CELF over roadmap paths
       coordination: sequential greedy over paths
       inner loop: gimbal-only gradient refinement (free)
       termination: budget spent ∨ all apples above per-instance threshold
```

---

## 5. Foundation models — where to start, and what to do when it fails

### 5.1 The headline: don't start from VGGT

VGGT won CVPR 2025 Best Paper and it is the reference everyone knows, but it is **batch, bidirectional, and pose-solving** — three properties you specifically do not want. It has no pose-input path, memory grows quadratically (5.6 GB at 20 views → 40.6 GB at 200), and it is now beaten on accuracy by three successors.

**Your defining asset is that you know the poses.** In Helios exactly; on the robot from arm encoders plus hand-eye calibration. Three models released since Sept 2025 accept poses, intrinsics, and/or depth as *optional conditioning inputs*:

| Model | Pose conditioning | Streaming | License | Why it matters |
|---|---|---|---|---|
| **MapAnything** ([2509.13414](https://arxiv.org/abs/2509.13414)) | intrinsics as ray directions, poses as quat+t, depth as ray depth — 12+ input combos, per-view optional | No (batch) | **Apache-2.0 code AND `map-anything-apache` weights** | **Primary recommendation.** Factored output (depth + local raymaps + poses + metric scale) means capacity goes to depth, not pose. 2000 views on 140 GB. Training framework can fine-tune VGGT/π³/MoGe-2 as guests — one Helios loader serves every later experiment |
| **Depth Anything 3** ([2511.10647](https://arxiv.org/abs/2511.10647)) | explicit "Pose-Conditioned Depth Estimation" mode, `use_ray_pose` | **Yes** — DA3-Streaming, ultra-long video <12 GB | Apache-2.0 for BASE/SMALL/METRIC-LARGE/MONO-LARGE | Only model answering both pose-conditioning *and* streaming. +23–25% geometric accuracy over VGGT. Also finds a plain DINO transformer suffices — you can fine-tune without inventing architecture |
| **Pi3X** (Dec 2025, in [yyfz/Pi3](https://github.com/yyfz/Pi3)) | optional poses, intrinsics, depth | No | code BSD-3, weights CC-BY-NC | Base π³ is permutation-equivariant with no reference-view dependence and 56% better ATE than VGGT on Sintel, 10× more stable across runs. Use base π³ as the *unconditioned control* that pose-conditioning must beat. Note: no standalone Pi3X paper |

Include VGGT anyway as the citation anchor (`VGGT-1B-Commercial` is license-clean), but budget about a day for it.

### 5.2 Two theoretical reasons to expect the uncalibrated path to fail on your scene

**(a) Projective ambiguity under small baselines.** VGGT-SLAM ([2505.12549](https://arxiv.org/abs/2505.12549)) reports:

> "the feed-forward nature of VGGT with uncalibrated cameras introduces a **projective ambiguity**, which in addition to the Sim(3) DOF includes **shear, stretch, and perspective DOF, especially when the disparity between frames becomes small**."

Submaps cannot be aligned by a 7-DoF similarity; they need a **15-DoF SL(4) projective homography**. For a camera on a 5-DOF arm orbiting a canopy through a narrow arc, the output is not merely noisy — it is *structurally ambiguous up to projective warp*. Your canopy comes out geometrically self-consistent and **silently metrically wrong**, corrupting canopy volume, fruit diameter, branch angle, internode length. **Known extrinsics eliminate this by construction.** This is the single best argument for the pose-conditioned path and it belongs in your introduction.

**(b) Attention collapse under self-similar tokens.** [arXiv:2512.21691](https://arxiv.org/abs/2512.21691) formalizes VGGT's attention degeneration: global attention matrices become near rank-one, token geometry degenerates to an almost one-dimensional subspace, entropy and effective rank decay as O(1/L) in depth, and error accumulates super-linearly. The diffusion coefficient scales inversely with token count, so collapse *accelerates* with more tokens. **A dense orbit of a leaf-covered canopy is the worst case: maximal token count, minimal token diversity.**

### 5.3 The domain evidence

**Nobody has benchmarked this model family on apple canopies, orchards, or fruit trees.** I searched hard. The only plant-domain evaluation is [arXiv:2607.01753](https://arxiv.org/abs/2607.01753) (July 2026), testing VGGT and π³ on 26 sequences of maize, tobacco, wheat, soybean, bamboo, rapeseed, pea, broccoli. Their results are genuinely encouraging *in their regime* — initialization 6.52 min (COLMAP) → 1.58 s (π³), leaf area R² 0.936–0.944, mean leaf-angle error ≈2.04°, and COLMAP fails outright below ~30–45 views while the π³ pipeline stays usable far below that.

But read their protocol: **closed-loop spiral orbit, 80–100 frames, single isolated potted plant.** And their own limitations section: *"repetitive textures, thin organs, occlusions, and uneven views reduce matching stability"; "Dense canopies, dynamic disturbances, cluttered backgrounds, and persistent occlusion remain challenging"; most reliable for "single-plant, close-range, closed-loop acquisition"; **"not suitable for dense field canopies."*** They fence off exactly your regime.

Supporting out-of-domain evidence:
- **Aerial photogrammetry evaluation** ([2507.14798](https://arxiv.org/abs/2507.14798)): in the *sparse* regime these models win decisively (1 image: 0.36–0.70 m accuracy where COLMAP fails entirely; 38 images at 10% overlap: VGGT holds 35–59% completeness while COLMAP crashes from 24% to 8%). In the *standard* regime they lose badly (~70% overlap: learned 0.44–1.12 m vs COLMAP-HR 0.06–0.16 m; MASt3R camera position error 8.22–62.14 m; orientation error up to 122.6°). Effective resolution ceiling 518 px.
- **E3D-Bench** ([2506.01933](https://arxiv.org/abs/2506.01933)), 16 geometric foundation models: "current GFMs excel on simpler sub-tasks but struggle as complexity grows"; pair-view beats multi-view; **metric-scale prediction is where they fail worst**; none are real-time. Contains **no vegetation domain at all**.
- **Fruit-tree canopy reconstruction review** (Agronomy 2026, [10.3390/agronomy16131274](https://www.mdpi.com/2073-4395/16/13/1274)): SfM+MVS completeness in heavily occluded inner canopy "typically falls below 60 percent"; point-cloud networks reach >85% accuracy on primary branches but **recall below 55% for branches thinner than 10 mm** under leaf occlusion; "weak and repetitive texture of branches leads to poor feature matching stability"; wind causes "fractures in fine branches thinner than 8 mm." **DUSt3R/MASt3R/VGGT: not mentioned at all.**

### 5.4 The reframe that opens the best toolbox

**With exact poses and RGB-D, your problem is no longer "3D reconstruction" — it is multi-view stereo / depth fusion / depth completion.** That reframing is worth taking seriously, because it opens a much better-conditioned toolbox that cannot be corrupted by pose error at all: classical MVS, TSDF/occupancy fusion, and modern depth-completion models.

The one to know: **PromptDA** ([2412.14015](https://arxiv.org/abs/2412.14015), Apache-2.0, ViT-S is 25 M params) takes RGB + sparse/low-res metric depth and produces 4K metric depth. That is *precisely* the primitive for cleaning up RealSense/ZED depth on a canopy.

**Treat "does a pose-conditioned geometry model actually beat a well-tuned depth-completion + fusion pipeline?" as a live open question that your Helios stage can answer definitively.** If the classical pipeline wins, that is a more useful finding than "the foundation model worked."

### 5.5 Complementary models, with license traps flagged

| Role | Pick | License | Note |
|---|---|---|---|
| Metric monocular depth | **MoGe-2** ([2507.02546](https://arxiv.org/abs/2507.02546)) | **MIT** | 60 ms on A100/3090, ViT-S is 35 M. Best license/capability trade in the category |
| | Metric3D v2 | BSD-2 | ONNX export |
| Depth completion | **PromptDA** | Apache-2.0 | RGB + sparse depth → 4K metric |
| Segmentation / tracking | **SAM 2.1** | Apache-2.0 | tiny 91 FPS / large 40 FPS on A100 |
| | **EfficientSAM3** ([2511.15833](https://arxiv.org/abs/2511.15833)) | Apache-2.0 | Distills SAM 3's text-prompted concept segmentation to ~90 M params. Best route to SAM 3 capability without SAM 3's gated custom license |
| Dense features | DINOv2 (Apache) / DINOv3 (custom Meta, mandatory "Built with DINOv3" attribution that propagates) | — | See warning below |
| Matching | **XFeat** ([2404.19174](https://arxiv.org/abs/2404.19174)) Apache-2.0, or LightGlue + **DISK/ALIKED** | — | See warning below |
| Point tracking (wind) | **TAPNext++** ([2604.10582](https://arxiv.org/abs/2604.10582)) | repo Apache, weights CC-BY-SA | Causal, constant memory, 191 FPS @1024 points, explicit re-detection after occlusion |

⚠️ **License traps that will bite you:**
- **DUSt3R, MASt3R, and anything inheriting their checkpoints (including MASt3R-SLAM) are CC-BY-NC-SA with additional MapFree restrictions.** Fast3R is FAIR non-commercial. π³ weights are CC-BY-NC.
- **SuperPoint and SuperGlue weights are academic/non-commercial only.** The ubiquitous LightGlue+SuperPoint combo is therefore non-commercial, even though LightGlue itself is Apache-2.0. Swap in DISK (Apache) or ALIKED (BSD-3).
- **YOLO-World is GPL-3.0; YOLOE is AGPL-3.0.** Copyleft traps for anything you plan to release under the project's GPLv2 or hand to a startup.
- Default **Depth Anything V2** Base/Large/Giant checkpoints are CC-BY-NC; only Small is Apache.

⚠️ **One directly relevant empirical warning:** "DINOv3 Visual Representations for Blueberry Perception" ([2603.02419](https://arxiv.org/abs/2603.02419)) finds segmentation quality scales monotonically with backbone size but **detection does not** — ~16% mAP50 with ViT-L, and **cluster detection collapsed to below 2% mAP50.** Apple clusters are the same structure. **Use DINOv3 for dense semantic heads; use SAM-family for instance detection of clustered fruit.**

### 5.6 Diagnostic experiments — the six that would actually tell you something

Ordered by information per day. Each targets a specific documented failure mechanism. **This is where I would stop and wait for your Helios setup.**

**D1 — The pose-conditioning ablation.** Same canopy, same views, four conditions: (a) images only, (b) + known intrinsics, (c) + known intrinsics and extrinsics, (d) + intrinsics, extrinsics, and simulated RGB-D depth. Report Chamfer, completeness, per-organ error. **This measurement does not exist in the literature — MapAnything's own paper never published it.** If (c)/(d) don't substantially beat (a), your central efficiency thesis is wrong and you learn it in week one. It is also a publishable figure.

**D2 — The baseline-angle sweep.** Fix the canopy; vary arc width: 5°, 10°, 20°, 45°, 90°, 180°, 360° closed loop. Plot accuracy vs arc width, with and without pose conditioning. VGGT-SLAM's projective-ambiguity result predicts a *sharp collapse* at small disparity for uncalibrated inference and *no such collapse* with poses given. **If that prediction holds, it is the core figure of your first paper.** Nobody has published this curve.

**D3 — Leaf-density / self-similarity sweep.** Helios lets you vary leaf area index continuously on a *fixed branch skeleton* (this is exactly what the proposal's occlusion-regulation module does). Sweep LAI from dormant to dense and measure (i) reconstruction error on the **branch geometry specifically** and (ii) attention effective rank in the aggregator. This tests the attention-collapse mechanism directly and would be the first parametric self-similarity study for this model family.

**D4 — Thin-structure recall by diameter class.** Bin ground-truth branches by diameter (<5 mm, 5–10, 10–20, >20 mm) and report recall per bin. Benchmark to beat, from the domain literature: **<55% recall below 10 mm under leaf occlusion.** This is the metric an orchard scientist actually cares about.

**D5 — The honest classical baseline.** With exact poses, run classical MVS / TSDF fusion / PromptDA depth-completion on the same views. **If a well-tuned classical pipeline with known poses matches the foundation model, that is the finding.**

**D6 — Metric-scale integrity.** Check that predicted canopy volume, leaf area, fruit diameter and internode length are *metrically* correct, not just visually plausible. E3D-Bench found metric scale is where these models fail worst. A projectively-warped reconstruction can look perfect and be metrically useless.

*Protocol note:* use a **shared global alignment** for joint camera+geometry evaluation (the UAVFF3D convention). Aligning cameras and geometry separately biases results.

### 5.7 Decision tree for when it fails

```
START: D1 + D2 in Helios on MapAnything, DA3, π³ (VGGT as anchor)

├─ Works (metric error acceptable, thin-branch recall ≥ classical MVS)
│    → move to streaming: DA3-Streaming / LONG3R / HorizonStream,
│      or the ASYNC pattern: heavy model once per settled viewpoint,
│      tiny model during motion (AsyncMDE-style). Close the loop.
│
├─ Works with poses, fails without      ← MOST LIKELY OUTCOME
│    → this IS the contribution. Commit to the pose-conditioned path.
│      Cite the SL(4) projective-ambiguity result as the theoretical reason.
│      Thesis framing: "known-pose geometry models for agricultural
│      active vision."
│
├─ Fails on foliage (branches fine, leaves wrong)
│    TIER 1: LoRA3D-style self-supervised LoRA on Helios data
│            ([2412.07746]: ~5 min, 18 MB adapter, no labels, self-supervised).
│            Cheapest possible fix — always try first. Per-cultivar,
│            per-lighting adapters then become practical on-robot.
│    TIER 2: full fine-tune via MapAnything's training framework on
│            Helios apple / apple_fruitingwall.
│            • copy the AerialMegaDepth recipe ([2504.13157]): mixing
│              synthetic renders with real images took DUSt3R from <5%
│              to ~56% on extreme-viewpoint localization — an ~11× gain
│            • sample MANY orchard configurations, not many frames of few
│              (TartanGround: environment count, not sample count, is the
│              generalization bottleneck)
│            • include SAGE-style anti-forgetting regularization —
│              narrow fine-tuning WILL destroy general geometry priors
│            • read the Infinigen-Stereo ablation tables ([2504.16930]) —
│              the only systematic study of which randomization axes
│              matter for geometry on *vegetation* scenes
│    TIER 3: hybrid. Model as PRIOR only — initialize bundle adjustment
│            and 2DGS (not 3DGS) with joint pose refinement.
│            Add dynamic-area suppression for wind.
│
├─ Fails sim→real (works in Helios, fails on the robot)
│    → do NOT immediately add noise to Helios. Try the INVERTED approach
│      first: Camera Depth Models ([2509.02530]) that denoise REAL depth
│      toward sim. That paper shows policies trained on raw simulated
│      depth transfer with no noise augmentation and no real fine-tuning,
│      including on "articulated, reflective, and slender objects."
│      Slender = branches.
│      Then Wat3R-style teacher–student adaptation on unlabelled real
│      orchard video (zero annotations needed).
│
└─ Works but too slow
     (1) systems-level speedups first — Speedy-MASt3R-style, free
     (2) QuantVGGT 4-bit: >98% FP accuracy retained, 2.5× hardware
     (3) VERIFY token-merging speedups hold at YOUR 5–20 view scale —
         they are measured at ~1000 views and will badly underdeliver
     (4) only then distill (eVGGT ~9×, Distill3R 5×) or go async
```

**One caveat on the fine-tuning literature:** nobody publishes a layer-wise LoRA ablation for VGGT-family models specifically. VGGT's own default config freezes the aggregator and trains heads only; other work suggests that for *modality* shift the problem lives inside the aggregator. This is a genuine open question and a legitimate thesis ablation.

### 5.8 The dataset gap that justifies the whole Stage 1

**There is no public plant or orchard dataset providing multi-view RGB *with camera poses* plus ground-truth dense geometry** — i.e. exactly the tuple a DUSt3R/VGGT-family fine-tune consumes. Every candidate is either LiDAR/TLS point clouds with no images or poses (AgriField3D, PLANesT-3D, TreeScope), or images with 2D labels and at best stereo (AppleGrowthVision, MinneApple, PhenoBench).

Helios fills exactly this gap, and it emits the complete tuple already: physically-based RGB + lossless float depth + exact intrinsics/extrinsics + per-pixel semantic and instance masks. **This is your Stage 1 justification, stated in one sentence.**

---

## 6. Helios: what you get, what you must build

I had the repo audited at `v1.3.78` (HEAD, 2026-07-26). Summary: **Helios covers roughly 70% of what this project needs, and covers it unusually well. Every gap is on the robotics side, plus one performance issue.**

### 6.1 The parts that are better than expected

**Programmatic multi-camera control is first-class.** `RadiationModel::addRadiationCamera(label, bands, position, lookat, props, AA)`, `setCameraPosition()`, `setCameraLookat()`, `setCameraOrientation()`, `getAllCameraLabels()`, and `runRadiationImaging(vector<cameralabels>, ...)`. Cameras are stored as a map and `runBand()` iterates all of them in one dispatch — **your three-arm rig maps directly onto this.** Camera model is thin-lens with depth of field (pinhole if `lens_diameter = 0`), with real intrinsics (resolution, focal length, HFOV, sensor width) and radial/tangential distortion.

**Real per-pixel float depth**, pushed into Context global data after every render — no file I/O needed:
```cpp
context.getGlobalData("camera_<label>_pixel_depth", depth);   // vector<float>
context.getGlobalData("camera_<label>_pixel_UUID",  uuids);   // vector<uint>, 0 = sky
```
Plus `writeDepthImageDataEXR()` for lossless float EXR.

**The per-pixel UUID buffer is the single most valuable thing in the whole library for you.** It gives you, in memory, for free: perfect instance segmentation, perfect semantic segmentation (map UUID → `object_label` primitive data), per-pixel occlusion ground truth, and the exact set of primitives visible from any pose. **Your entire visibility/coverage reward function can be computed directly from it with zero extra ray casting.**

**A full BVH ray-casting plugin most people don't know exists.** `plugins/collisiondetection/`, class `CollisionDetection` — CPU (OpenMP) with optional CUDA:
```cpp
castRays(vector<RayQuery>&, RayTracingStats*);
castRaysSoA(const vec3* origins, const vec3* dirs, size_t n, float max_d,
            float* out_dist, vec3* out_normal, uint* out_UUID, ...);
castRaysGPU(...); processRayStream(...);
findCollisions(UUIDs, allow_spatial_culling);
findCollisionsWithinDistance(query, target, max_distance);
findNearestSolidObstacleInCone(apex, axis, half_angle, height, candidates, ...);
calculateGridIntersection(...);  performGridRayIntersection(...);
```
with mature BVH management (`setStaticGeometry()`, `enableTreeBasedBVH()`, `disableAutomaticBVHRebuilds()`, `enableGPUAcceleration()`). **This is your NBV inner loop and your arm collision checker, already written.**

**Annotations:** YOLO-format bounding boxes, COCO segmentation masks with traced polygons, in-memory `generateLabelMasks()`, EXIF/XMP on every JPEG (so output drops straight into COLMAP if you want an SfM comparison).

**Plant models:** `plantarchitecture` ships **`apple`** (*Malus pumila*, Fuji) and — crucially — **`apple_fruitingwall`**, a trellised fruiting-wall training system, which is precisely the modern high-density geometry your rig is designed for. Pruning (`pruneBranch`), phenology, collision-aware growth around trellis wires, and all architectural parameters are `RandomParameter` types seeded from the Context RNG, so **domain randomization is built in, not bolted on.**

**Ground truth access** is comprehensive: `getObjectCenter(objID)` and `getObjectBoundingBox()` for fruit centroids and sizes, `getPrimitiveArea()` summed over `getAllLeafUUIDs()` for leaf area, `getPlantFruitObjectIDs(plantID)`, and pre-populated primitive data `"object_label"` ∈ {leaf, fruit, peduncle, petiole, shoot} plus object data `plantID`/`leafID`/`fruitID`/`phenology_stage`.

**The LiDAR plugin is more capable than "point cloud dump":** `addScanMoving(scan, traj_t, traj_pos, traj_quat, lever_arm, boresight_rpy, ...)` simulates a sensor moving along a trajectory with lever arm and boresight offset — i.e. a sensor on a moving arm — and its poses are quaternions, so it handles full 6-DOF including roll.

**A note on the visibility metric you already plan to compute.** Your "virtual camera on each fruit" construction is the *inverse visibility* formulation. It is not novel in graphics or horticulture — it is mathematically identical to **ambient occlusion** and to the **sky-view factor / light interception efficiency** that canopy radiative-transfer modelling has computed for decades. It *is* novel in robotic harvesting evaluation. And the punchline: **Helios's radiation plugin is exactly that solver already**, built for radiation rather than robotics. Reuse it; don't write a new one.

### 6.2 The gaps you must build

| # | Gap | Severity | Notes |
|---|---|---|---|
| 1 | **No arm kinematics.** Zero hits for `kinematic`, `manipulator`, `inverse kinematics` anywhere in the codebase | Blocking | Use Pinocchio/KDL/`ikpy`, or hand-roll 5-DOF FK/IK. Helios only needs the resulting camera pose |
| 2 | **No robot time-stepping.** `advanceTime()` advances *plant growth in days*, not robot state. No simulation clock | Blocking | You write the loop. Helios is a renderer + geometry engine called *from* your loop, not a robot simulator |
| 3 | **`runBand()` re-solves the whole scene radiative transfer on every render**, even when only the camera moved | **High — this is your frame rate** | The backend already has `launchCameraRays()` (`RayTracingBackend.h:153`) but it is not exposed publicly. Adding `runCamerasOnly()` is a small patch and probably the difference between a 1 Hz and a 10 Hz loop. Excellent upstream PR |
| 4 | **No RGB-D sensor noise model.** Renders are perfect | **High for sim-to-real** | Real RealSense/ZED have flying pixels, holes, stereo shadowing, IR dropout. See risk #2 in §8 |
| 5 | **Camera has no roll / up-vector.** Position + look-at only; EXIF roll hardcoded 0 | Medium | Fine if your 5 DOF omit roll. Otherwise patch `RadiationCamera` and the three raygen programs — or use the LiDAR scanner path, which takes quaternions |
| 6 | No ROS/ROS2 | Medium | Only matters if you need it |
| 7 | **PyHelios is incomplete** — `CollisionDetection` explicitly not exposed; no in-memory depth getter | Medium | Either write the loop in C++, or contribute the missing bindings |
| 8 | No incremental reconstruction / TSDF / octree | Expected | This is your research contribution, not a gap |

### 6.3 The three-tier rendering strategy

This is the key architectural decision for closed-loop viability. **You do not need photorealism to decide where to look next.**

| Tier | Mechanism | Speed | Use for |
|---|---|---|---|
| **A** | `CollisionDetection::castRaysSoA` / `castRaysGPU` — one ray per pixel, take distance + primitive UUID | **milliseconds** for 10⁴–10⁶ rays | NBV inner loop, visibility gain, coverage reward, RL rollouts, arm collision |
| **B** | `Visualizer` (headless OpenGL) `getDepthMap()` + legacy `syntheticannotation` plugin (batch pose API) | **~30 Hz** | Fast RGB-D + masks, debugging, mid-fidelity training |
| **C** | `RadiationModel` cameras, RGB bands, low AA | **~1–10 s/view** — benchmark this yourself | Final evaluation, sim-to-real dataset generation, paper figures |

Published Tier-C numbers disagree by an order of magnitude because they measure different things: Lei & Bailey report 11 s/image for a 120k-primitive bean scene on an RTX A2000 (hyperspectral, 100 rays/pixel, 5 scattering iterations), while `doc/Benchmarks.dox` reports a 1.05 s direct trace on an RTX 6000 Ada. **An RGB-only, 3-band, low-sample render of a single apple tree should land sub-second to few-seconds on a modern card — but benchmark it before committing to any architecture.** Optimizations: don't call `updateGeometry()` per view (only when the tree changes, ~0.5–1.3 s); render all three cameras in one `runBand()`; drop antialiasing to 1–4 samples (tutorial 12 uses 100).

### 6.4 The precedent, and the absence of one

**No published work uses Helios for next-best-view planning, active vision, or closed-loop perception.** Every Helios paper to date is offline dataset generation: render a batch, train a network, done. Nobody has put Helios inside a control loop.

That is simultaneously the risk (no precedent, no reference implementation, the render path was never optimized for it) and the contribution. **"First closed-loop active-vision benchmark in a physically-based plant simulator" is a real, defensible claim.**

Two pieces of adjacent Davis work you should read and whose authors are down the hall:
- **Fu, Wei, Villacres, Ke, ..., Kong, Vougioukas, Bailey, "Fusion-driven Tree Reconstruction and Fruit Localization," IROS 2023** — orchard robotics using Helios-generated data. Closest existing work, same two labs.
- **Choi, Guevara, Bandodkar, Cheng, Wang, Bailey, Earles, Liu, "DAVIS-Ag: A Synthetic Plant Dataset for Prototyping Domain-Inspired Active Vision in Agricultural Robots," IROS 2024** ([2303.05764](https://arxiv.org/abs/2303.05764)). 502K HD images from 30K sampling locations across 632 simulated orchards, three crops, with boxes and instance masks. **It defines a "Fruit Search Optimization" task — sequential viewpoint planning to maximize fruit discovery — which is exactly your explore phase.** It has no apple crop, no multi-camera setting, and no budgeted-IPP baselines. Their reported numbers are also revealing: on multi-plant goblet vine over 10 steps, Random scores 0.114, the greedy "To-More"/"To-Less" heuristics score *worse* than random (0.108/0.106), and DQN reaches only 0.155. **Multi-plant fruit search is genuinely hard and largely unsolved.** Extending DAVIS-Ag to apples with three coordinated 5-DOF cameras and a proper budgeted formulation is an obvious and well-received contribution.

---

## 7. Evaluation design

The proposal's current metrics — "number of fruits discovered, accuracy of their locations and sizes, average exploration time per fruit" — are the standard set, and they have a specific flaw: **they pool three different things into one number.** When your system detects 62% of fruits, that could mean the canopy is impossible, or your arm workspace is badly designed, or your planner is bad. Those call for completely different responses, and only the third is your algorithm's fault.

The simulator lets you separate them. Below is a five-tier suite. Metrics marked **[SIM]** are the ones that are impossible without a simulator — those are what justify the whole Stage 1 methodology.

**Prerequisite, computed once per canopy:** define the **reachable view set** 𝒱_reach by densely sampling the 5-DOF joint space, forward-kinematics to camera pose, rejecting self-collision and canopy collision. **Every oracle and upper bound below is defined over this set.**

### 7.1 The three headline metrics

#### (A) Achievable Visibility Upper Bound and Normalized Visibility Efficiency **[SIM]**

First, define per-fruit visibility properly. Fruit *i* has surface S_i of area A_i, discretized into primitives {s_ij} with areas a_ij and outward normals n_ij. For camera pose *v* centered at p_v:

    vis_i(v) = (1/A_i) · Σ_j a_ij · 1[unoccluded(s_ij, p_v)]
                              · 1[n_ij · (p_v − s_ij) > 0]
                              · 1[s_ij ∈ frustum(v)]
                              · w(θ_ij, r_ij)

Three deliberate choices:
- **Weight by primitive area, not pixel count.** Pixel-fraction conflates visibility with distance and resolution; area-fraction is a scene property, pixel-fraction is a sensor property. Report both; define area-fraction as primary.
- w(θ, r) is an optional observation-quality weight (cos θ grazing-angle degradation, range-dependent depth noise). Set w ≡ 1 for pure geometric visibility, report the weighted variant separately.
- Occlusion is resolved by ray-casting from s_ij to p_v against all scene primitives — Helios's ray tracer.

Accumulated visibility over a trial, v_i^max(t), is a **union over primitives** seen by at least one camera at any time — not a max over views. A fruit seen 40% from the left and 40% from the right is 80% covered.

Now the novel quantity:

    AVUB_i = (1/A_i) · |∪_{v ∈ 𝒱_reach} {j : s_ij visible from v}|_area

the fraction of fruit *i*'s surface visible from **any** collision-free, kinematically reachable camera pose. This is a reachability-constrained ambient-occlusion computation, and Helios's radiation plugin computes it directly.

Then the headline score:

    NVE = Σ_i A_i · v_i^max(T) / Σ_i A_i · AVUB_i

**NVE = 100% means the system did as well as is physically possible given the arm's workspace and the canopy's geometry.**

This cleanly separates three failure sources that every existing paper pools:

| Source | Quantity | Who cares |
|---|---|---|
| **Canopy-imposed** | the distribution of AVUB_i itself | Growers, and it characterizes orchard difficulty comparably across trellis types |
| **Workspace-imposed** | AVUB / AVUB^∞, comparing 𝒱_reach against an unconstrained free-flying camera | **Hardware designers.** This tells you how much visibility your 5-DOF arm design leaves on the table — and can be used to argue for a different arm |
| **Planner-imposed** | NVE < 1 | Reviewers. The only part that is your algorithm's fault |

Also define a **fruit-level achievability class**: observable if AVUB_i > 0; sizeable if AVUB_i > γ_size (the visible fraction empirically needed for sizing within tolerance, calibrated from Tier 1); graspable if the approach cone is clear. **Report recall against the *observable* denominator, not the total** — failing to detect a fruit that is 100% occluded from every reachable pose is not a failure of your system, and reporting it as one understates your result and overstates the achievable ceiling.

> Targeted searches for "oracle visibility," "maximum achievable visibility," "reachability-constrained visibility" returned no on-topic hits. Verify against Scopus/WoS with institutional access before claiming novelty in writing, but the balance of evidence is that no one has published a reachability-constrained achievable-visibility bound for orchard fruit. It should be a named quantity in your thesis.

This also gives you the rigorous version of the proposal's 70% ± 10% visibility target — and lets you say whether 70% was easy or near-impossible for a given canopy.

#### (B) Oracle-normalized planning score Π **[SIM]**

Build three reference planners in Helios:
- **Greedy oracle** π^orc: at each step evaluate *every* candidate in 𝒱_reach against ground truth and greedily pick the truly best. This is VIN-NBV's "Oracle NBV" construction ([2505.06219](https://arxiv.org/abs/2505.06219)), transplanted. Greedy, hence within (1−1/e) of true optimum for a submodular objective, and computable.
- **Offline set-cover optimum** π^opt for small budgets: solve k-view maximum coverage exactly by ILP over 𝒱_reach with ground-truth visibility as the coverage matrix. Feasible for k ≲ 8. This is the true ceiling and makes the greedy oracle's own gap measurable. (Note this is the art-gallery problem, and in Helios you know the geometry, so it is available to you and to essentially nobody else.)
- **Random** and **raster/lawnmower** floors.

Then:

    Π = [AUC_T(π) − AUC_T(π^rand)] / [AUC_T(π^orc) − AUC_T(π^rand)]

Π = 0 means no better than random; Π = 1 means you matched an omniscient greedy planner. **It is scale-free across canopies of different difficulty** — a canopy where everything is visible compresses both ends and Π correctly reports "this canopy was uninformative" rather than inflating your score.

Notably, **the foundational IG-comparison papers (Delmerico et al. 2018, Isler et al. 2016) and essentially all agricultural NBV papers compute no oracle upper bound at all.** They compare heuristics against each other and against random. Closing that gap is a contribution in itself.

Also report **per-step regret**: regret_k = u*_k − u_k, where both are true realized gains measured after the fact. Plot it against step. The shape is diagnostic — regret concentrated early means poor initial heuristics; regret concentrated late means your utility function fails on the last hard-to-see fruit, **which is the regime that actually determines harvest completeness.**

#### (C) Information-gain calibration: AUIGSE **[SIM]**

Your planner's utility function is a *prediction*. Nobody in NBV audits whether it is right. Here is how, adapted from the optical-flow uncertainty literature (Ilg et al., ECCV 2018, [1802.07095](https://arxiv.org/abs/1802.07095)).

At each step you score candidates 𝒞_k with predicted utility û(v). Execute the chosen one — but *also* compute from Helios ground truth the **true realized gain u(v) that every candidate would have produced.** Then:

1. **Rank correlation.** ρ_k = Spearman(û, u) over 𝒞_k. Report the distribution *and* ρ_k **as a function of step index** — utility functions are typically well-calibrated early (everything is unknown, any view helps) and badly calibrated late. Late-step calibration is what determines whether you find the last 15%. Also report **top-1 hit rate** and top-1 regret, because a planner only ever acts on the argmax; high global correlation with a bad argmax is worthless.

2. **Sparsification curve.** Sort candidates by *predicted* utility descending; for fraction φ, take the top-φ and compute mean *true* utility. A well-calibrated function gives a monotonically decreasing curve.

3. **Oracle curve.** Same, sorting by *true* utility. The achievable envelope.

4. **Sparsification error** = their difference. This normalizes out how intrinsically informative the candidate set was — critical, because candidate-set quality varies enormously between an early step and a late one.

5. **AUIGSE** = area under the sparsification-error curve. **One scalar characterizing the quality of your utility function, decoupled from the quality of your reconstruction and from canopy difficulty.**

Complement with a simple **regression audit**: scatter û against u pooled over all candidates and steps, report slope, intercept, R². **Slope ≠ 1 matters practically**: if you trade IG against motion cost in a weighted objective, a miscalibrated slope silently changes the exchange rate between information and motion.

FisherRF applies AUSE to per-pixel depth uncertainty, not to view utility. I found no NBV paper doing this. Cite the Ilg lineage explicitly and it is a clean methodological contribution.

### 7.2 The rest of the suite, in brief

**Tier 1 — Perception level**
- **Occlusion-conditioned detection recall [SIM].** Recall stratified by ground-truth occlusion decile. In every field paper, recall is computed against *visible-in-image* fruit count, so detection quality and occlusion are permanently entangled. **Your simulator dissolves this confound completely** — plot recall vs occlusion decile and you separate "the detector is weak" from "the planner never gave the detector a chance."
- **Phantom-fruit rate.** False positives corresponding to *no* ground-truth fruit, separated from duplicate detections of a real fruit. Two different failure modes; real datasets cannot distinguish them.
- **Amodal size error vs visible fraction [SIM].** MAE_d reported as a *curve* against v_i^max. This quantifies the marginal value of additional visibility for the sizing task, which is what a size-driven planner implicitly assumes.
- **Localization error** as a distribution (median, p90), **decomposed into radial vs lateral** in each camera frame. Depth error and lateral error have different causes and different consequences for grasping; pooling hides which one you have.

**Tier 2 — Reconstruction level**
- **Semantically stratified F-score at class-specific τ [SIM]**, per Knapitsch et al. but per semantic class with τ scaled to the class's characteristic dimension: fruit 5 mm (~7% of diameter, grasp-relevant), branch/trunk 10 mm (collision-relevant), trellis wire 5 mm (safety-critical), leaf 10 mm. **Report the vector, never the average.** And note: **no Sim(3)/ICP alignment step is needed** — you know the exact ground-truth frame. Skipping alignment is itself a rigor gain, since ICP-based evaluation can mask systematic scale or pose bias.
- **Skeleton metrics for branch architecture [SIM].** Topological similarity (graph edit distance, branch-count and connectivity agreement), centeredness, smoothness, plus branch volume error. Helios gives you the *exact* ground-truth branch graph from procedural generation — the reference skeleton is known, not estimated. Impossible with scanned data.
- **Three-state occupancy confusion matrix [SIM].** Instead of IoU, evaluate {occ, free, unk} against exact ground truth. The interesting cells are the ones IoU throws away: M(occ|free) = **hallucinated geometry** (phantom obstacles, wasted motion); M(free|occ) = **missed geometry** (the dangerous one — collisions with branches and wires); M(unk|·) = residual ignorance, the natural denominator for exploration efficiency. **Report M(free|occ) restricted to trellis wires and branches separately — that is your safety-critical miss rate.**
- Chamfer distance is a trap for canopies (outlier-dominated, density-biased). Report density-aware CD per class, and report plain CD only so reviewers can compare to prior work — saying explicitly why it is not the headline.
- If you use a radiance field: PSNR/SSIM/LPIPS on a **held-out camera trajectory geometrically distinct from the acquisition trajectory**, never interleaved frames, and labelled clearly as diagnostic, not as evidence of geometric quality.

**Tier 3 — Planning level** (beyond Π and regret)
- **Discovery curve D̄(t) plotted against three x-axes**, because they answer different questions: view index (sample efficiency of the utility function), cumulative joint-space path length (motion efficiency), and **wall-clock time including compute** (the only axis a grower cares about). Summarize by normalized AUC over budget T, and report **Final Discovery** and **time-to-90%** separately. AUC rewards early discovery, final rewards eventual completeness, and a planner can win one while losing the other.
- **Multi-camera coordination gain [SIM]:** G_coord = AUC(π^joint) − AUC(π^indep). **This is your core multi-camera claim** — it isolates the benefit of coordination from the benefit of simply having three cameras. Additionally report **view redundancy**: the fraction of newly-covered fruit surface covered by more than one camera simultaneously. High redundancy with low coordination gain is direct evidence the cameras are duplicating work.
- **Counterfactual view value [SIM].** Re-run a completed trial with view k replaced by a random reachable view, all else fixed. The drop in final performance is the *causal* value of that view. Averaged over k this attributes where the planner's value actually came from — and frequently reveals that most of it comes from 2–3 views and the rest is noise. Only tractable because you can replay a deterministic simulator.

**Tier 4 — Task level**
- **Harvestability / approach-cone clearance [SIM].** Harvest success in the field is gated by reachability, not just detection. For fruit *i* with peduncle axis p̂_i, define the approach cone as end-effector directions within α of p̂_i free of collision along a straight insertion of length L. Report the fraction with Clearance_i > 0 (*theoretically harvestable*), and — **the metric that ties perception to the task** — the fraction both *discovered* and theoretically harvestable: **effective harvestable yield.** That is the number growers' economics respond to, and it should headline the task tier.
- **Peduncle pose error** in degrees, the quantity that determines whether gripper approach succeeds.
- Counting MAE/MAPE/R² for comparability with Häni/Roy/Isler, but reported **twice** — against total fruit count and against *observable* fruit count — with the difference quantifying the irreducible counting error the canopy imposes.
- **Multi-view identity metrics.** The apple-counting literature does tracking-based counting but has **not adopted MOT identity metrics** (MOTA, IDF1, ID switches). Aggregate MAE cannot distinguish "two errors that cancel" from "no errors." In your simulator every fruit has a persistent ground-truth ID, so computing IDF1 and ID-switch counts over the multi-view aggregation is trivial — and would be novel in this domain.

**Tier 5 — Systems**
- Per-module latency table at a **stated operating point** (resolution matters; a timing number without it is meaningless): depth ingestion, map update, candidate generation, utility evaluation, 3-arm assignment, motion planning, end-to-end. **Report mean / p95 / p99 / max**, and define real-time as p99 ≤ deadline.
- Report a **hardware-independent work unit** (ray casts, candidate evaluations) alongside wall-clock, so the numbers survive a GPU upgrade. This is GradientNBV's convention and it is a good one.
- **Compute-vs-quality Pareto [SIM].** Sweep voxel resolution, candidate count, raycast density, horizon; plot NVE or Π against p99 latency with the deadline as a vertical line. This turns "we chose 2 cm voxels" from an unjustified hyperparameter into a defended operating point.
- **Deadline-enforced closed-loop check [SIM].** Easy trap in simulation: the planner gets unlimited thinking time because the simulator pauses. Run a variant where the simulated arm keeps moving during planning and the planner must return within budget or forfeit the step. **Report the gap between paused-clock and deadline-enforced evaluation.** Most simulation NBV papers report only the paused number and the gap is often large. Reporting it is a credibility win.

### 7.3 The baseline ladder

Every metric should be reported against this, spanning "trivially achievable" to "physically impossible":

| Baseline | Role |
|---|---|
| Single fixed camera, one view | Absolute floor; the value of *any* motion |
| **Static 3-camera rig, no arm motion** | **The realistic commercial alternative your system must beat** |
| **Raster / lawnmower sweep** | The engineering-practical alternative. Notably **absent from the entire NBV reconstruction literature** — including it is a genuine methodological addition, not box-ticking |
| Random reachable views | Stochastic floor; the denominator of Π |
| Frontier-based exploration | Standard NBV baseline |
| Published IG heuristics (Delmerico/Isler occlusion-aware) | Re-implemented on your map |
| Semantics-aware NBV (Burusa), graph-based VMP (Zaenker) | **The real competitors** |
| **Your planner** | |
| **Perfect-perception ablation** | GT detections fed to the planner. Separates *planning* error from *perception* error — one of the most informative single ablations available |
| Greedy oracle | Numerator of Π |
| Offline set-cover ILP optimum (small k) | True ceiling; measures the greedy oracle's own gap |
| All-reachable-views fusion | Sensor + workspace ceiling, independent of planning |
| Unconstrained free-flying camera | Isolates the arm design's contribution to the ceiling |

### 7.4 Experimental design and statistics

**The simulator changes the epistemics.** You are no longer sampling opportunistically from whatever orchard you could access — you are *designing* the experiment, and you inherit the obligations of designed experiments.

**Factorial structure.** Natural factors: occlusion level / LAI (3), fruit density (3), fruit clustering (2), trellis type (3), cultivar geometry (2–3), illumination (2–3), camera configuration (your ablation axis). A full crossing of the first four is 54 cells; at 20 canopies per cell that is 1080 trials — **feasible in simulation and flatly infeasible in an orchard. That asymmetry is the argument for the whole approach and should be stated as such.** In practice: fractional factorial to screen which factors dominate, then full factorial on the 2–3 that survive.

**Everything is paired.** Because Helios canopies are procedurally generated from a seed, you can run *every* planner on *exactly the same* canopy. This is a large variance reduction and lets you use paired tests. Use the same seed set across all conditions and say so.

**The statistical bar in this literature is low — clear it decisively.** Several CVPR/ICRA NBV papers report single-run point estimates with no seeds and no variance despite stochastic candidate sampling and RL policies. The agricultural papers are the outliers in a *good* way: Zaenker et al. run 20 trials per scenario with one-sided Mann-Whitney U. So:
- Pre-specify a **development canopy set and a held-out test set with disjoint seeds.** Tune only on dev. Report test once.
- ≥20 seeded canopies per cell, ≥5 planner seeds per canopy where the planner is stochastic.
- **Bootstrap 95% CIs resampling canopies, not views** — canopy is the unit of independence.
- Paired Wilcoxon signed-rank for planner-vs-planner; report an **effect size** (Cliff's δ), not just p.
- Holm–Bonferroni across the family of planner comparisons.
- A short power analysis justifying n from a pilot run's variance.

**Sim-to-real protocol, designed before you need it:**
1. Build a *matched* real scenario — same trellis type, measured LAI and fruit count, fruit positions hand-measured with a total station.
2. **Reconstruct that real tree in Helios** using its LiDAR plugin's leaf-by-leaf reconstruction from terrestrial scans — this is the intended path and gives you a digital twin.
3. Report the *same metric vector* in sim and on the twin, and report the **sim-real gap per metric**, not overall success. Some metrics will transfer (fruit count recall); others will not (sub-mm geometric error).
4. **Validate that the *ordering* of planners is preserved sim→real even if absolute values are not.** Rank preservation is the claim that actually matters, it is testable with a rank correlation over the planner set on a handful of real trees, and it is far cheaper than matching absolute numbers.

### 7.5 One safeguard

Because Helios lets you compute anything, it also lets you compute a metric your own system happens to be good at. Two cheap protections:
1. **Pre-register the metric set and test canopy seeds before the final comparison.**
2. **Run the Tatarchenko degenerate-baseline check.** Their CVPR 2019 result — a trivial retrieval baseline matching SOTA under Chamfer and IoU — is the canonical warning. The analogue: verify that a *stupid* baseline (static rig, or "always look at the geometric centroid of the unknown region") does not already score well on your headline metric. If it does, the metric is measuring the canopy, not the planner. **Π is designed to be robust to this by construction, which is the main reason to headline it.**

---

## 8. Risks worth naming now

1. **Resolution budget.** Every headline speed number in the mapping literature was measured at 5 cm voxels on indoor rooms. Your leaves are 0.2 mm and your twigs 2 mm. A 50–100× linear increase implies 10³–10⁴× more work. **Re-derive the budget at your actual resolution before committing to an architecture.** This is the most likely way this project goes wrong.

2. **Helios will flatter a TSDF pipeline.** Perfect geometry and perfect poses mean synthetic depth lacks the flying-pixel and mixed-pixel artifacts at leaf boundaries that dominate real RealSense foliage data — which is *precisely* what triggers carving-through-leaves. **Inject realistic depth-edge noise before trusting any Stage 1 geometric result.** Consider the inverted approach (denoise real depth toward sim) as the sim-to-real strategy rather than randomizing noise into Helios.

3. **The fruiting wall is nearly planar.** Raster scanning may be much more competitive than the tomato-greenhouse literature suggests. Test this in week 2 and be ready to shift emphasis to the exploit phase.

4. **Detection, not planning, is usually the bottleneck.** Freeman & Kantor's misses were mostly Mask R-CNN failures, not planning failures; [2412.10515](https://arxiv.org/abs/2412.10515) lost 17% surface coverage to segmentation noise. **Always report planner performance with an oracle detector *and* a real one.** Otherwise your planner ablations are measuring your detector.

5. **Wind.** FruitNeRF reports it as a failure cause; WildGS-SLAM's mechanism would actively *delete* wind-moving foliage as dynamic; AgriGS-SLAM names it as motivation and never quantifies the degradation. Stage 1 in Helios lets you defer it. It is the hardest Stage 2 problem and nobody has solved it.

6. **Scope.** Sections 4, 5 and 7 each contain at least one publishable contribution. Resist doing all of them at once. The ordering I would pick is in §9.

---

## 9. Suggested framing and sequencing

**Paper 1 (ICRA/IROS) — "Budget-aware two-phase active vision for multi-camera fruit mapping."** Core claims: (i) exploration and exploitation require structurally different objectives, with a Good–Turing switching criterion; (ii) sequential-greedy multi-camera coordination with a ½-optimality guarantee; (iii) Helios evaluation with an offline ILP oracle and the Π score. Highest value, most defensible, and every component is independently useful.

**Paper 2 — "Hierarchical gimbal-gradient / linear-axis IPP decomposition."** Exploits the DOF cost asymmetry. Fast to execute, cleanly novel, and directly motivated by your hardware.

**Paper 3 — "Learned canopy-conditioned fruit-occupancy priors for occlusion-aware view planning."** The hidden-fruit gap in §4.5. Helios-native, and it is the piece that most directly serves the harvesting objective.

**Possible Paper 0, cheap and self-contained** — "Do 3D foundation models work on fruit-tree canopies?" The D1/D2 experiments in §5.6. Nobody has run them; the theoretical prediction is sharp; the answer is useful to the whole field regardless of which way it comes out; and it de-risks everything downstream.

---

## 10. Where I would stop and hand back to you

Everything below needs the actual Helios setup, and the ordering matters because each result constrains the next decision.

**E0 — Benchmark Helios honestly. This single number decides the entire architecture.**
Build one `apple_fruitingwall` tree at ~1460 days. Record primitive count. Then time, in a Release build, with `updateGeometry()` called *once outside* the loop:
- `runBand({"red","green","blue"})` at 640×480, AA=1, 3 cameras, scattering depth 1 → your Tier-C cost
- `castRaysSoA` with 640×480×3 rays → your Tier-A cost
- `Visualizer::getDepthMap()` headless → your Tier-B cost

Also verify `getGlobalData("camera_<label>_pixel_depth")` returns sane metric depth and that `camera_<label>_pixel_UUID` maps back correctly to `object_label`.

**E1 — Resolution/thin-structure budget.** At what voxel size does your occupancy map retain 2 mm twigs and 2–3 mm trellis wire? Sweep resolution against branch-recall-by-diameter-class (§5.6 D4) and against map update time. This gives you the operating point everything else is built on.

**E2 — Foundation model diagnostics.** D1 (pose-conditioning ablation) and D2 (baseline-angle sweep) on MapAnything, DA3, π³, with VGGT as anchor and a classical MVS/PromptDA pipeline as the honest baseline (D5). Expected outcome: works with poses, fails without — in which case that *is* the contribution.

**E3 — The planarity check.** Greedy coverage vs raster on a single fruiting-wall tree, coverage-vs-time curves. If the gap is small, you learn early that the explore phase is not where your novelty lives, and you shift weight to §4.4–4.5.

**E4 — Coordination delta.** Sequential greedy across 3 arms with vertical band constraints vs 3 independent greedy arms. **This is your headline multi-camera number** and it is cheap to get once E3 is running.

Then we can work through: the exact occupancy map implementation (UFOMap semantics + wavemap beam model on GPU is a real engineering project — we should scope whether to build, fork, or fall back to nvblox's occupancy/freespace layers), the roadmap construction and IK for the 5-DOF chain, the fruit-occupancy prior's feature design and training setup, and the ILP formulation for the offline set-cover oracle.

Send me the Helios setup and the E0 numbers when you have them and we'll take it from there.

---

## 11. Verification caveats

Please confirm these before anything here goes into a proposal, thesis, or paper.

- **2026 arXiv identifiers cited above** (2603.22650, 2603.22786, 2604.12942, 2606.20842, 2605.23889, 2607.01753, 2603.02419, 2604.10582, 2605.17942, and others) are recent preprints whose venue status is unconfirmed. Verify each before citing as published.
- **Delmerico et al. 2018** (the volumetric IG comparison) could not be retrieved in full — Springer paywalled, four access routes blocked. The metric *names* are confirmed from the landing page; **the ranking claim and the individual formulas should be checked against the PDF** via UC Davis library.
- **Villacrés & Vougioukas 2024**, **Wang et al. 2025**, **Bulanon et al. 2009**, **Gené-Mola et al. 2020/2023**, and several Elsevier/ASABE sources are bibliographically verified (title/authors/DOI via Crossref) but full text was blocked. **Do not quote experimental design or numbers for these from this document** — get institutional full text. This matters most for Villacrés & Vougioukas, which is your single most directly relevant prior work.
- **DA3's reported improvement over VGGT differs between paper versions** (+35.7%/+23.6% vs +44.3%/+25.1%). Check which benchmark and version.
- **LoRA3D's "88% improvement"** — the abstract does not state relative to what, or on which dataset.
- **AVUB novelty**: verify against Scopus/Web of Science before claiming it in writing. The searches available here returned no on-topic hits, but access was degraded.
- **Helios timing figures** in §6.3 come from two sources that disagree by an order of magnitude because they measure different things. **Benchmark it yourself (E0); do not plan around either published number.**
- **Highest-value single follow-up read**: the ablation tables in *Procedural Dataset Generation for Zero-Shot Stereo Matching* ([2504.16930](https://arxiv.org/abs/2504.16930), InfinigenStereo). It is the only systematic study of which domain-randomization axes actually matter for geometry on *vegetation* scenes, and the findings are not in the abstract.
- Web-search quotas were exhausted partway through this review; later sections were completed via direct page fetches. Coverage of very recent (June–July 2026) releases may be incomplete.
