"""
T1.6 -- RGB-D noise model. Helios depth is perfect (exact ray-primitive
intersection); real RealSense/ZED-class stereo depth over foliage is not:
it has flying/mixed pixels at depth discontinuities and range-dependent
noise that grows with distance. Feeding a fusion/reconstruction pipeline
perfect depth removes exactly the artifact that would otherwise make it
carve through occluding leaves, so this module injects both effects and
makes them toggleable so the effect size can be quantified (see
`compare_before_after`).

This is a plausible, documented model -- not a calibrated match to any
specific sensor. The `valid_mask` (real ray hit vs. sky/no-return) is taken
from the semantic label map's NaN mask (see label_maps.py), not guessed from
a depth sentinel value, since it comes from the exact same ray-hit-topology
pass as the depth buffer and is guaranteed pixel-aligned with it.
"""

import numpy as np

DEFAULT_EDGE_THRESHOLD_M = 0.15   # depth jump (m) between neighboring pixels considered an edge.
                                  # Picked empirically (not guessed): on a real rendered view of
                                  # this dense 3-tree canopy, ~90% of foreground pixel-to-pixel
                                  # depth gradients are already >0.48m (see PHASE1_LOG.md) because
                                  # thin leaves/branches at very different depths sit right next
                                  # to each other in-frame. A threshold as low as the 0.03m a
                                  # RealSense-class sensor would use flags ~37% of all foreground
                                  # pixels as "edges" here, which stops being a sparse artifact and
                                  # starts being most of the image. 0.15m keeps the effect
                                  # concentrated near genuine occlusion boundaries for this scene.
DEFAULT_EDGE_BAND_ITERS = 1       # how many times to dilate the edge mask by one pixel
DEFAULT_MAX_MIX_FRACTION = 0.35   # cap on how far a mixed pixel is pulled toward its discontinuity
                                  # partner (as a fraction of the full near/far gap), so a mixed
                                  # pixel lands somewhere between the two surfaces, not on top of
                                  # (or past) the far one.
DEFAULT_RANGE_SIGMA_COEFF = 0.0015  # sigma(z) = coeff * z^2, loosely modeled on stereo depth noise
                                    # growing quadratically with range (e.g. RealSense D435 whitepaper)


def _dilate(mask, iterations):
    out = mask
    for _ in range(iterations):
        out = (
            out
            | np.roll(out, 1, axis=0) | np.roll(out, -1, axis=0)
            | np.roll(out, 1, axis=1) | np.roll(out, -1, axis=1)
        )
    return out


def add_depth_edge_mixed_pixels(depth, valid_mask, edge_threshold_m=DEFAULT_EDGE_THRESHOLD_M,
                                 band_iterations=DEFAULT_EDGE_BAND_ITERS,
                                 max_mix_fraction=DEFAULT_MAX_MIX_FRACTION, rng=None):
    """Simulate flying/mixed pixels: at a genuine depth discontinuity, pull
    each edge pixel partway toward whichever of its 8 neighbors sits on the
    other side of that discontinuity (the neighbor with the largest depth
    difference), by a random fraction capped at `max_mix_fraction`. This
    approximates a stereo-matcher return that partially interpolated between
    two surfaces straddling the edge, without ever landing on top of (or
    past) the far surface. Sky (invalid) neighbors are excluded so real
    geometry never gets mixed toward the -1.0 sky sentinel."""
    if rng is None:
        rng = np.random.default_rng()

    depth_for_grad = np.where(valid_mask, depth, np.nan)
    gx = np.abs(np.diff(depth_for_grad, axis=1, append=depth_for_grad[:, -1:]))
    gy = np.abs(np.diff(depth_for_grad, axis=0, append=depth_for_grad[-1:, :]))
    grad = np.nan_to_num(np.maximum(gx, gy), nan=0.0)

    edge_mask = _dilate(grad > edge_threshold_m, band_iterations) & valid_mask

    shifts = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    neighbor_depths = np.stack([np.roll(depth, s, axis=(0, 1)) for s in shifts], axis=0)
    neighbor_valid = np.stack([np.roll(valid_mask, s, axis=(0, 1)) for s in shifts], axis=0)
    # Invalid (sky) neighbors are replaced with the pixel's own depth so they
    # can never be picked as the "largest difference" partner.
    neighbor_depths = np.where(neighbor_valid, neighbor_depths, depth[None, ...])

    diffs = np.abs(neighbor_depths - depth[None, ...])
    partner_idx = np.argmax(diffs, axis=0)
    partner_depth = np.take_along_axis(neighbor_depths, partner_idx[None, ...], axis=0)[0]

    blend = rng.uniform(0.05, max_mix_fraction, size=depth.shape)
    mixed = depth * (1.0 - blend) + partner_depth * blend

    noisy = np.where(edge_mask, mixed, depth)
    return noisy, edge_mask


def add_range_dependent_noise(depth, valid_mask, sigma_coeff=DEFAULT_RANGE_SIGMA_COEFF, rng=None):
    """Additive Gaussian noise whose std grows with the square of range."""
    if rng is None:
        rng = np.random.default_rng()
    sigma = sigma_coeff * np.square(depth)
    noise = rng.normal(0.0, 1.0, size=depth.shape) * sigma
    return depth + np.where(valid_mask, noise, 0.0)


def apply_rgbd_noise_model(depth, valid_mask, enable=True, seed=0,
                            edge_threshold_m=DEFAULT_EDGE_THRESHOLD_M,
                            range_sigma_coeff=DEFAULT_RANGE_SIGMA_COEFF):
    """Toggleable end-to-end noise model. `enable=False` is a true no-op
    (returns an unmodified copy) so before/after can be diffed meaningfully."""
    if not enable:
        return depth.copy()
    rng = np.random.default_rng(seed)
    noisy, _edge_mask = add_depth_edge_mixed_pixels(
        depth, valid_mask, edge_threshold_m=edge_threshold_m, rng=rng)
    noisy = add_range_dependent_noise(noisy, valid_mask, sigma_coeff=range_sigma_coeff, rng=rng)
    return noisy


def compare_before_after(clean_depth, noisy_depth, valid_mask):
    """Quantify the noise model's effect: report it, don't just assert it."""
    diff = noisy_depth - clean_depth
    diff_valid = diff[valid_mask]
    if diff_valid.size == 0:
        return {"n_valid_pixels": 0}
    return {
        "n_valid_pixels": int(diff_valid.size),
        "mean_abs_diff_m": float(np.mean(np.abs(diff_valid))),
        "max_abs_diff_m": float(np.max(np.abs(diff_valid))),
        "rmse_m": float(np.sqrt(np.mean(diff_valid ** 2))),
        "fraction_changed_gt_1mm": float(np.mean(np.abs(diff_valid) > 0.001)),
        "fraction_changed_gt_1cm": float(np.mean(np.abs(diff_valid) > 0.01)),
    }
