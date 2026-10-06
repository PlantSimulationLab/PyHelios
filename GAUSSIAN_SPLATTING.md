# Apple Tree → Gaussian Splatting: automation runbook

This documents how `apple_tree_gaussian_splatting.py` was built, so the same
project can be reproduced (or extended) as a scripted process instead of an
interactive back-and-forth. It captures the environment setup, the API facts
that had to be discovered by reading source/testing, the one serious native
bug that was hit and how it was isolated, and the design decisions that
needed a human call vs. ones that could be defaulted automatically.

Source: `apple_tree.py` (tree growth) + `apple_tree_cameras.py` (camera rig
pattern) → `apple_tree_gaussian_splatting.py` (full pipeline).

---

## 1. Objective

Grow apple trees with PyHelios, render a multi-view dataset with known camera
poses, and train a real 3D Gaussian Splat (via the `gsplat` library) on that
dataset — seeding the Gaussians from the tree's own mesh geometry instead of
COLMAP/SfM, since PyHelios already knows exact 3D positions. Training is
restricted to the fruit class only (the semantic mask acts as a prior, see
§5), and is run once per (capture config, densification strategy) pair —
sweeping image count, number of viewing planes, and `gsplat` strategy — so
these can be compared on identical seed points/geometry.

## 2. Prerequisites check (do this first, automatable)

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
find /usr/local -maxdepth 1 -iname "cuda*"      # look for a CUDA toolkit even if nvcc isn't on PATH
/usr/local/cuda-*/bin/nvcc --version            # confirm nvcc directly, not just `which nvcc`
gcc --version && g++ --version                  # gsplat JIT-compiles CUDA kernels, needs a working host compiler
python3 -c "import pyhelios" 2>&1               # confirm pyhelios' compiled extension already works in the base env
```

Key facts learned this way:
- `pyhelios/_stub.cpython-313-*.so` is compiled for a **specific Python ABI**
  (3.13 here). Any new env must match that Python minor version exactly, or
  the import fails. Don't assume `pyhelios` is pip-installable — it's used
  via `sys.path`/cwd from the repo root, not a package registered in `pip
  show`.
- `nvcc` may be installed but simply not on `PATH` (common on machines set up
  for multiple CUDA versions). Check `/usr/local/cuda-*/bin` before assuming
  it's missing.

## 3. Environment setup (scripted)

Do **not** install torch/gsplat into the base env — create a dedicated env
pinned to the same Python version as PyHelios' compiled extension:

```bash
conda create -n gsplat python=3.13 -y
conda activate gsplat
pip install numpy pyyaml pillow scipy      # pyhelios runtime deps + scipy for KDTree init

export PATH=/usr/local/cuda-12.9/bin:$PATH  # match whatever toolkit `find /usr/local` found
export CUDA_HOME=/usr/local/cuda-12.9
pip install --index-url https://download.pytorch.org/whl/cu128 torch torchvision  # cuXXX must support the GPU's arch (e.g. cu128 for Blackwell/RTX 50-series)
pip install gsplat                          # JIT-compiles CUDA kernels on first use, needs nvcc from above
```

Validation gate before writing any pipeline code — run all three in the new
env and require all to pass:

```bash
python3 -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"
python3 -c "import gsplat; from gsplat import rasterization, DefaultStrategy, export_splats"
PYTHONPATH=/home/yogesh/PyHelios python3 -c "from pyhelios import Context; Context()"
```
Then confirm pyhelios and torch/gsplat coexist in **one process** (headless
`Visualizer` + `torch.cuda` tensor + `gsplat` import in sequence) before
building anything on top — this is cheap insurance against a GL/CUDA context
conflict that would otherwise surface much later.

## 4. API surface that had to be discovered (not obvious from names alone)

Recorded here so it doesn't need re-discovery. Verify against the installed
version before trusting it — these are pinned to PyHelios (this repo, current
HEAD) and `gsplat==1.5.3`.

**PyHelios `Visualizer`** (`pyhelios/Visualizer.py`):
- `setCameraPosition(position, lookAt)` — up vector is hardcoded to world
  `+Z`, not settable. Z-up world convention throughout Helios.
- `setCameraFieldOfView(angle_FOV)` — **vertical** FOV in degrees, default 45.
- No aspect-ratio, near/far, or orthographic controls. Aspect = `width/height`
  automatically, which combined with a single vertical FOV means `fx == fy`
  (square pixels) always — you cannot reproduce a real camera's `fx != fy`.
- `printWindow()` output resolution == constructor `width`/`height` **only**
  in `headless=True` mode (windowed mode can differ due to DPI scaling).
- No getter for view/projection matrices — must be reconstructed manually
  (see §5).

**PyHelios `Context`** (`pyhelios/Context.py`):
- `getPrimitiveVertices(uuid_list)` → `(flat_float32_array, offsets_uint32)`;
  vertices for primitive `i` are `flat[offsets[i]:offsets[i+1]].reshape(-1,3)`.
- `getPrimitiveColor(uuid_list)` → Nx3 array. **Textured primitives (leaves,
  bark, fruit) return `(0,0,0)`** — flat color is only meaningful for
  untextured primitives. Check `getPrimitiveTextureFile(uuid)` and average
  the texture image (alpha-aware) as a fallback; only 2-3 unique texture
  files exist per plant species, so cache by path.
- `getDomainBoundingSphere(uuids)` / `getDomainBoundingBox(uuids)` — call
  per-tree (not once for the whole orchard) to size each tree's own camera
  rig off its own footprint (see §7); a shared orchard-wide box badly misses
  individual trees that sit off-center in a multi-tree row.

**`gsplat` 1.5.3**:
- `rasterization(means, quats, scales, opacities, colors, viewmats, Ks,
  width, height, sh_degree, backgrounds, ...)` → `(render[C,H,W,3],
  alpha[C,H,W,1], info_dict)`. `viewmats` is **world-to-camera, OpenCV
  convention** (X-right, Y-down, Z-forward) — must match how the training
  images were actually formed, not an idealized convention.
- Two interchangeable densification strategies, same `rasterization()` calls
  but **different constructor args and hook signatures**:
  - `DefaultStrategy` — clone/split/prune (original 3DGS). `params` dict
    needs at least `means`, `scales` (log-space), `quats`, `opacities`
    (logit-space); extra keys (`sh0`, `shN`) ride along generically as long
    as one Adam optimizer per param exists in a matching `optimizers` dict.
    `initialize_state(scene_scale=...)`; `step_pre_backward` and
    `step_post_backward` both take `(params, optimizers, state, step, info)`.
  - `MCMCStrategy` — relocation + noise injection (3DGS-MCMC paper), capped
    at `cap_max` Gaussians. `initialize_state()` takes **no** `scene_scale`
    arg (relocation is opacity-driven, not scale-driven). `step_pre_backward`
    is a no-op (don't call it). `step_post_backward` takes an **extra
    required `lr` kwarg** (the current means learning rate) — omitting it is
    a `TypeError`, not a silent no-op. The paper also expects explicit L1
    opacity/scale regularization added to the loss, since there's no
    split/prune step to keep them in check otherwise.
- `export_splats(means, scales, quats, opacities, sh0, shN, format="ply",
  save_to=path)` — writes a standard 3DGS PLY directly, no manual PLY
  encoding needed. Works identically regardless of which strategy trained
  the params.

## 5. Design decisions that were resolved manually (defaults for next time)

These required a judgment call. Recording the answer chosen so a future
automated run can default to it without asking:

| Decision | Choice made | Why |
|---|---|---|
| Scope of "implement gaussian splatting" | Full training pipeline via `gsplat`, not a from-scratch rasterizer, not export-only | User wanted actual trained output; `gsplat` is the standard CUDA-accelerated library, reimplementing the rasterizer adds risk with no benefit |
| Point cloud init | Sample directly from tree mesh surface (bilinear on patches, barycentric on triangles, area-proportional density) instead of COLMAP/SfM or random init | PyHelios already has exact geometry — this is strictly better-seeded than SfM sparse points, and avoids needing COLMAP at all |
| Camera pose convention | Manually derive OpenCV world-to-camera matrix (X-right, Y-down, Z-forward) from `eye`/`lookAt`/world-up=`(0,0,1)`, verified numerically (`right × down == forward`) | `gsplat` needs OpenCV-convention viewmats; Helios exposes no matrix getter, so it must be reconstructed to exactly match what Helios's internal `glm::lookAt` actually rendered |
| Real camera intrinsics (`fx,fy,cx,cy` + distortion) given by user | Derive render resolution from `(cx,cy)`, vertical FOV from `fy`; drop distortion and off-center principal point; gsplat's K matrix is a **centered** pinhole matching what was actually rendered | Helios's renderer physically cannot produce `fx != fy`, off-center principal point, or lens distortion — passing the raw values into gsplat while training on Helios pixels would be geometrically inconsistent with the images themselves |
| Loss function | `0.8 * L1 + 0.2 * (1 - SSIM)`, compact from-scratch SSIM (11×11 Gaussian window, `conv2d`) | Standard 3DGS recipe; no extra dependency needed for SSIM |
| Camera rig | Treat each tree as independent: per-tree flat-plane grid at a fixed distance from *that tree's own* center, always looking at it, instead of one 360° orbit around the whole orchard | A single orbit around the combined bounding box over/under-frames trees that sit off-center in a multi-tree row; a fixed per-tree plane keeps every tree consistently framed regardless of where it sits, without needing to circle it |
| Target class for training | Restrict to `TARGET_CLASS = "fruit"` always (not a toggle) — seed points, dataset masking, and export are all apples-only | User wants the deliverable to be an apple-only splat, not the whole tree; the semantic mask (§ render_semantic_masks) already exists as a clean prior for this |
| Splat densification strategy | Train **once per strategy** gsplat ships (`DefaultStrategy`, `MCMCStrategy`) on the same seed points/dataset, exporting a separate `.ply` per strategy rather than picking one | Neither strategy is a strict upgrade — comparing both on the same data is cheap (just a second training pass) and avoids committing to one without evidence |
| Number of images / number of viewing planes | Sweep both as separate `CAPTURE_CONFIGS` cases (`sparse`: 1 plane, 4x2 grid; `default`: 1 plane, 8x3 grid; `multi_face`: 4 planes, 8x3 grid each), one variable changed at a time from the `default` baseline, each producing its own dataset + its own `.ply` per strategy | Answers "does more images help" (`sparse` vs `default`) and "does seeing more of the tree help" (`default` vs `multi_face`) independently, rather than guessing one fixed capture density; a full cross product of every count x every plane count wasn't worth the extra training runs for this comparison |

**Cost note:** `CAPTURE_CONFIGS x SPLAT_STRATEGIES` = 3 x 2 = 6 full training
runs by default (each `TRAIN_ITERS` iterations), plus 3 separate render
passes (48 + 144 + 576 = 768 renders total across `sparse`/`default`/
`multi_face`). Trim `CAPTURE_CONFIGS` or lower `TRAIN_ITERS` for a quick
smoke test rather than running the full matrix every time.

## 6. Known bug: PyHelios headless `Visualizer` heap corruption at large resolution

**Symptom:** `malloc(): corrupted top size`, process aborts (SIGABRT/core
dump), no Python traceback — a native heap corruption, not a Python
exception.

**Reproduction:** occurs during multi-view rendering once a render dimension
gets large (observed failures from ~1850px up; the original camera
calibration implied 1957×1286). Always survives the *first* render in a
process; crashes on the *second or later* `plotUpdate()`/`printWindow()`
call.

**Isolation steps that ruled out other causes** (run each independently to
confirm before assuming the fix generalizes to a different PyHelios version):
1. 3 trees / 30K primitives at large res → crashes on view 2.
2. 1 tree / ~10K primitives at the *same* large res → **still crashes** on
   view 2 → not about primitive/tree count.
3. Same test with a **fresh `Visualizer` object per view** (instead of
   reusing one instance across the loop) → **still crashes** → not about
   object reuse/state.
4. Same test with **no `torch`/`gsplat` import anywhere in the process** →
   **still crashes** → not a CUDA/allocator interaction with PyTorch; it's
   internal to PyHelios's own headless rendering path.
5. Bisected resolution: 800×526, 1200×789, 1400×919, 1600×1051, 1800×1182
   all survived a 4-view sequential test; 1850×1215 and 1957×1286 crashed.
   The boundary was **not perfectly monotonic** across separate process runs
   (consistent with genuine heap corruption whose crash point depends on
   allocator/heap layout, not a clean hardcoded limit) — treat any threshold
   found this way as approximate, not exact.

**Workaround implemented:** cap the render resolution to `MAX_RENDER_DIMENSION
= 1000` (comfortably below the entire observed failure zone), scaling both
width and height from the calibration-derived resolution while preserving
aspect ratio. Validated stable across 24 sequential renders in the actual
`render_dataset()` code path before trusting it in the full pipeline. FOV is
unaffected by this scaling since it's an angle, not a pixel count.

**If this shows up again in a different context:** re-run the bisection in
§6 rather than assuming the same numeric threshold — this is a bug in the
native `Visualizer`/Helios core (likely a framebuffer resize or PNG-encode
buffer sizing bug), not something fixable from the Python wrapper beyond
avoiding the trigger condition. Filing it upstream against Helios would be
the real fix.

## 7. Pipeline architecture

```
apple_tree_gaussian_splatting.py
├── build_orchard()                 # reuses build_apple_tree() from apple_tree.py
├── sample_point_cloud()            # mesh-surface sampling + texture-average color fallback, once for all cases
├── plane_camera_poses()            # per-tree grid across num_planes flat faces (num_cols x num_rows each),
│                                    # called once per tree per CAPTURE_CONFIGS case (extends the
│                                    # apple_tree_cameras.py 3-shot rig; no orbiting, fixed distance per tree)
├── look_at_view_matrix()           # OpenCV-convention world-to-camera matrix
├── intrinsics_matrix()             # K from (width, height, vertical FOV)
├── render_dataset()                # headless multi-view render + transforms.json export, once per capture config
├── classify_primitives()           # fruit/leaf/tree split via Helios "object_label" data
├── render_semantic_masks()         # flat-colored mask render -> class-index PNG per view, once per capture config
├── init_gaussians()                # KDTree-based scale init, RGB->SH0 color init
├── train_gaussians()               # gsplat rasterization + L1/SSIM loss, strategy-agnostic
├── _build_strategy()               # DefaultStrategy or MCMCStrategy, per SPLAT_STRATEGIES
├── evaluate()                      # held-out PSNR + side-by-side comparison PNGs
└── export_ply()                    # gsplat.export_splats -> one .ply per (capture config, strategy) pair

main() renders CAPTURE_CONFIGS once each (shared seed points across all of
them), then trains TARGET_CLASS="fruit" once per (capture config, strategy)
pair -- see §5 for what each axis controls.
```

## 8. Validation checklist before trusting a full run

Always smoke-test at reduced scale first — this is what caught the crash in
§6 before it wasted a full 5000-iteration run:

1. 1 tree, ~16 views, small resolution (e.g. 200×200), ~300-700 iterations,
   a single `CAPTURE_CONFIGS` entry. Confirms: tree build → render → point
   sampling → training forward/backward → `DefaultStrategy` density-control
   path (needs `iters > refine_start_iter`, default 500) → eval → PLY
   export, all with no exceptions.
2. Visually inspect one ground-truth render and one eval comparison PNG
   (`renders/.../eval/<capture>/<strategy>/eval_*.png`, side-by-side
   GT|rendered) — confirms camera orientation is correct (not
   flipped/mirrored) and colors are sane, which numeric checks alone won't
   catch. Do this for **both** strategies, not just the first — a
   strategy-specific bug (e.g. the `MCMCStrategy` missing `lr` kwarg) can
   silently corrupt only one output. For `multi_face`, check at least one
   view from each of the 4 planes, not just the frontal one.
3. Only then run the full default (3 trees, all of `CAPTURE_CONFIGS`, fruit
   class only, 5000 iterations x 2 strategies each — see the cost note in
   §5).

## 9. Reference full run (validates the fix in §6)

The numbers below were measured before the per-tree frontal-plane rig,
fruit-only restriction, and dual-strategy loop (§5) were added — they
validate the §6 workaround, not the current camera/strategy behavior.
**Re-run and replace these once the current pipeline has been executed
end-to-end** rather than trusting these figures for the new code path:

```
3 trees, 72 views (3 elevations x 24 azimuths, whole-tree class), 1000x657
renders, 5000 iterations, DefaultStrategy only, on an RTX 5090:
30,700 seed points -> 62,767 Gaussians after density control
Held-out PSNR: 27.48 dB over 9 views
Output: renders/gaussian_splatting/apple_orchard_splats.ply (3.5 MB)
```

## 10. To run it

```bash
conda activate gsplat
cd /home/yogesh/PyHelios
python3 apple_tree_gaussian_splatting.py
```

Trains `TARGET_CLASS="fruit"` once per (capture config, strategy) pair --
`CAPTURE_CONFIGS` (`sparse`, `default`, `multi_face` by default) x
`SPLAT_STRATEGIES` (`default`, `mcmc`). See the cost note in §5 before
running the full matrix. Output:

```
renders/gaussian_splatting/
├── dataset/{sparse,default,multi_face}/            # per-capture-config RGB + mask renders
├── eval/{sparse,default,multi_face}/{default,mcmc}/ # per-capture-config, per-strategy comparison PNGs
├── apple_splats_fruit_sparse_default.ply
├── apple_splats_fruit_sparse_mcmc.ply
├── apple_splats_fruit_default_default.ply
├── apple_splats_fruit_default_mcmc.ply
├── apple_splats_fruit_multi_face_default.ply
└── apple_splats_fruit_multi_face_mcmc.ply
```
