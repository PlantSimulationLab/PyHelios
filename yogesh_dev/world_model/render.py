"""
W1 -- Batched observation rig.

One radiative solve serves every registered camera, so the cost of a frame falls
roughly as 1/N up to the point where the per-camera pass starts to dominate. This
module exists to make that batching the *only* way frames are produced.

Per camera we return:
    rgb        uint8   (H,W,3)   tonemapped with a FIXED GLOBAL exposure
    rgb_raw    float32 (H,W,3)   raw getCameraPixelData, before tonemapping
    depth      float32 (H,W)     metres, -1.0 = no hit (sky)
    semantic   uint8   (H,W)     0 other / 1 fruit / 2 leaf / 3 shoot /
                                 4 petiole / 5 peduncle / 255 sky
    instance   int32   (H,W)     fruitID, -1 = not a fruit pixel
    pose       float32 (4,4)     camera-to-world, Phase 0 convention

## Load-bearing setup details (each one was a real failure mode)

1. `setScatteringDepth(band, >=1)` for every camera band. With the default 0 the
   camera pass is skipped entirely: pixel data comes back empty AND
   `writeDepthImageDataEXR` fails with "Depth data for camera 'X' does not exist".
   `phase0/radiation_setup.setup_bands_and_lights` already does this (default 1).
2. `disableEmission(band)` for every band BEFORE any `reflectivity_<band>` /
   `transmissivity_<band>` primitive data takes effect, or `runBand()` aborts with
   "emissivity, transmissivity, and reflectivity must sum to 1".
3. `exposure="manual"` on CameraProperties (phase0/radiation_cameras) -- "auto"
   re-normalises every frame independently, which would mean the world model
   learns the exposure controller instead of the orchard.
4. **One fixed exposure scale for the entire dataset**, computed once by
   `calibrate_exposure()` and then passed in verbatim. Never per-frame.
5. Pixel-array orientation is not assumed. `verify_pixel_orientation()` checks the
   reshaped `getCameraPixelData` array against the label map (whose geometry was
   validated sub-pixel in Phase 0 T0.3) and reports which of the four
   flip conventions actually agrees.

## Sky / background

There is no sky radiance in these bands, so no-hit pixels come back as 0 (black).
Leaving that would teach the model that "background == black", which is both
unrealistic and makes the depth/semantic sky channel redundant. We composite a
fixed sky colour over the no-hit mask taken from the label map (the same ray-hit
topology pass that produces depth's -1 sentinel, so it is pixel-exact). The colour
is a constant, recorded in the manifest -- it carries no information, which is the
point: the model must learn geometry, not a background texture.
"""

import math
import os
import tempfile
import time

import numpy as np

from pyhelios import RadiationModel
from pyhelios.RadiationModel import CameraProperties

from yogesh_dev.phase0.radiation_setup import setup_bands_and_lights, RGB_BANDS
from yogesh_dev.phase0.pose_convention import hfov_from_vfov, look_at_view_matrix, intrinsics_matrix
from yogesh_dev.phase1.depth_export import read_depth_exr, SKY_DEPTH_SENTINEL
from yogesh_dev.phase1.label_maps import SEMANTIC_CLASS_ID_FIELD

BAND_LABELS = ["red", "green", "blue"]
SKY_SEMANTIC_ID = 255
SKY_RGB = (135, 170, 205)     # fixed, information-free background colour
DEFAULT_RESOLUTION = (128, 128)
DEFAULT_VFOV_DEG = 60.0       # wider than Phase 0's 45 deg: an in-lane robot camera
                              # is ~1 m from the canopy, so 45 deg crops badly.
DEFAULT_AA_SAMPLES = 2


# ---------------------------------------------------------------------------
# Tonemapping
# ---------------------------------------------------------------------------
def srgb_transfer(x):
    """Linear [0,1] -> sRGB [0,1]."""
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1.0 / 2.4) - 0.055)


def tonemap(rgb_raw, exposure_scale, sky_mask=None, sky_rgb=SKY_RGB):
    """Raw radiance -> uint8 RGB using a FIXED exposure scale.

    `exposure_scale` is a single float for the whole dataset (see
    `calibrate_exposure`). `sky_mask` (bool, True = no geometry hit) is filled
    with `sky_rgb` after tonemapping so the constant never affects the scale.
    """
    lin = np.asarray(rgb_raw, dtype=np.float32) / float(exposure_scale)
    out = (srgb_transfer(lin) * 255.0 + 0.5).astype(np.uint8)
    if sky_mask is not None:
        out[sky_mask] = np.asarray(sky_rgb, dtype=np.uint8)
    return out


# ---------------------------------------------------------------------------
# Orientation verification (W1 acceptance -- not assumed)
# ---------------------------------------------------------------------------
ORIENTATIONS = {
    "as_is": lambda a: a,
    "flipud": lambda a: a[::-1],
    "fliplr": lambda a: a[:, ::-1],
    "rot180": lambda a: a[::-1, ::-1],
}


def verify_pixel_orientation(rgb_raw_hw, label_map):
    """Which reshape/flip of the raw pixel array lines up with the label map?

    The label map's geometry was validated sub-pixel in Phase 0 T0.3, so it is the
    reference.

    FIRST ATTEMPT, WHICH FAILED -- kept documented because it is an easy trap:
    comparing a "has radiance > 0" mask against the "hit geometry" mask
    (~isnan(label_map)). That does not work, because `setDiffuseRadiationFlux`
    gives *background* pixels non-zero radiance too, so "lit" is not "hit". On a
    real orchard render the best IoU it could reach was 0.87, with lit_frac (0.44)
    exceeding hit_frac (0.40) -- the giveaway.

    WHAT ACTUALLY WORKS: use the per-organ optical properties we ourselves set in
    `orchard.ORGAN_OPTICS`. Leaves are given green-dominant reflectance
    (g/r = 0.170/0.075 = 2.27) and fruit red-dominant (g/r = 0.150/0.420 = 0.36),
    a ~6x separation. Under the correct orientation the mean green/red ratio on
    leaf-labelled pixels is far above that on fruit-labelled pixels; under a wrong
    orientation the labels are scrambled relative to the radiance and the
    separation collapses toward 1. The score below is that ratio-of-ratios, and it
    is a genuinely discriminative test rather than a coincidence-prone one.
    """
    from yogesh_dev.phase1.label_maps import SEMANTIC_CLASSES
    leaf_id, fruit_id = SEMANTIC_CLASSES["leaf"], SEMANTIC_CLASSES["fruit"]
    lm = np.round(np.where(np.isnan(label_map), -1, label_map)).astype(int)
    leaf = lm == leaf_id
    fruit = lm == fruit_id
    eps = 1e-8
    out, diag = {}, {}
    for name, fn in ORIENTATIONS.items():
        cand = fn(rgb_raw_hw)
        gr = cand[..., 1] / (cand[..., 0] + eps)
        if leaf.sum() < 50 or fruit.sum() < 50:
            out[name] = None
            continue
        leaf_gr = float(np.median(gr[leaf]))
        fruit_gr = float(np.median(gr[fruit]))
        out[name] = leaf_gr / (fruit_gr + eps)
        diag[name] = {"leaf_green_over_red": leaf_gr, "fruit_green_over_red": fruit_gr}
    valid = [k for k in out if out[k] is not None]
    best = max(valid, key=lambda k: out[k]) if valid else None
    return {"score_per_orientation": out, "diagnostics": diag, "best": best,
            "best_score": out[best] if best else None,
            "n_leaf_px": int(leaf.sum()), "n_fruit_px": int(fruit.sum()),
            "hit_fraction": float((lm >= 0).mean()),
            "method": "median(green/red) on leaf pixels / same on fruit pixels; "
                      "higher is better, ~1.0 means the labels are scrambled"}


# ---------------------------------------------------------------------------
# The rig
# ---------------------------------------------------------------------------
class ObservationRig:
    """N radiation cameras registered against one orchard, solved together.

    Usage:
        rig = ObservationRig(orchard, n_cameras=128)
        rig.open()                      # bands, lights, cameras, updateGeometry
        frames = rig.render_batch(poses)  # len(poses) <= n_cameras
        rig.close()
    """

    def __init__(self, orchard, n_cameras=128, resolution=DEFAULT_RESOLUTION,
                 vfov_deg=DEFAULT_VFOV_DEG, aa_samples=DEFAULT_AA_SAMPLES,
                 sun_zenith=30.0, sun_azimuth=120.0, bands=None,
                 exposure_scale=None, want_depth=True, want_semantic=True,
                 want_instance=True, camera_prefix="wm"):
        self.orchard = orchard
        self.n_cameras = int(n_cameras)
        self.resolution = tuple(resolution)
        self.vfov_deg = float(vfov_deg)
        self.aa_samples = int(aa_samples)
        self.sun_zenith = float(sun_zenith)
        self.sun_azimuth = float(sun_azimuth)
        self.bands = list(bands) if bands else list(BAND_LABELS)
        self.exposure_scale = exposure_scale
        self.want_depth = want_depth
        self.want_semantic = want_semantic
        self.want_instance = want_instance
        self.camera_prefix = camera_prefix

        w, h = self.resolution
        self.aspect = w / h
        self.hfov_deg = hfov_from_vfov(self.vfov_deg, self.aspect)
        self.K = intrinsics_matrix(w, h, self.hfov_deg)
        self.camera_labels = [f"{camera_prefix}{i:04d}" for i in range(self.n_cameras)]
        self.radiation = None
        self._orientation = "as_is"
        self.timings = {}

    # -- lifecycle -----------------------------------------------------------
    def open(self):
        ctx = self.orchard.context
        self.radiation = RadiationModel(ctx)
        self.radiation.__enter__()
        self.radiation.disableMessages()

        setup_bands_and_lights(self.radiation, zenith=self.sun_zenith,
                               azimuth=self.sun_azimuth, scattering_depth=1)
        # Gotcha 3: must disable emission before per-primitive reflectivity/
        # transmissivity are legal, or runBand() aborts on the sum-to-1 check.
        for band in self.bands:
            self.radiation.disableEmission(band)

        w, h = self.resolution
        cam_props = CameraProperties(camera_resolution=self.resolution,
                                     lens_diameter=0.0, HFOV=self.hfov_deg,
                                     FOV_aspect_ratio=0.0, exposure="manual")
        from pyhelios.types import vec3
        for label in self.camera_labels:
            self.radiation.addRadiationCamera(
                label, list(self.bands), vec3(0.0, -3.0, 1.2), vec3(0.0, 0.0, 1.2),
                camera_properties=cam_props, antialiasing_samples=self.aa_samples)

        t0 = time.time()
        self.radiation.updateGeometry()
        self.timings["update_geometry_s"] = time.time() - t0
        return self

    def close(self):
        if self.radiation is not None:
            self.radiation.__exit__(None, None, None)
            self.radiation = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *a):
        self.close()

    # -- rendering -----------------------------------------------------------
    def _set_poses(self, poses):
        from pyhelios.types import vec3
        for label, (eye, lookat) in zip(self.camera_labels, poses):
            self.radiation.setCameraPosition(label, vec3(*[float(v) for v in eye]))
            self.radiation.setCameraLookat(label, vec3(*[float(v) for v in lookat]))

    def solve(self, poses):
        """Move the first len(poses) cameras and run ONE solve over all bands.
        Returns solve wall-clock seconds."""
        if len(poses) > self.n_cameras:
            raise ValueError(f"{len(poses)} poses > {self.n_cameras} registered cameras")
        self._set_poses(poses)
        t0 = time.time()
        self.radiation.runBand(list(self.bands))
        return time.time() - t0

    def _orient(self, arr):
        return ORIENTATIONS[self._orientation](arr)

    def read_camera(self, cam_index, exposure_scale=None, tmpdir=None):
        """Read back everything for one already-solved camera."""
        label = self.camera_labels[cam_index]
        w, h = self.resolution

        raw = np.empty((h, w, 3), dtype=np.float32)
        for k, band in enumerate(self.bands):
            px = np.asarray(self.radiation.getCameraPixelData(label, band), dtype=np.float32)
            if px.size != h * w:
                raise RuntimeError(
                    f"camera '{label}' band '{band}' returned {px.size} pixels, expected {h*w}. "
                    "Most likely the camera pass was skipped -- check setScatteringDepth(band, >=1).")
            raw[:, :, k] = self._orient(px.reshape(h, w))

        out = {"camera_label": label, "rgb_raw": raw}

        semantic_raw = None
        if self.want_semantic:
            semantic_raw = self.radiation.getPrimitiveDataLabelMap(label, SEMANTIC_CLASS_ID_FIELD)
            sem = self._orient(semantic_raw)
            sky = np.isnan(sem)
            sem_u8 = np.where(sky, SKY_SEMANTIC_ID, np.nan_to_num(sem, nan=0.0)).astype(np.uint8)
            out["semantic"] = sem_u8
            out["sky_mask"] = sky
        if self.want_instance:
            inst = self._orient(self.radiation.getObjectDataLabelMap(label, "fruitID"))
            out["instance"] = np.where(np.isnan(inst), -1, np.nan_to_num(inst, nan=-1)).astype(np.int32)
        if self.want_depth:
            own_tmp = tmpdir is None
            td = tempfile.mkdtemp() if own_tmp else tmpdir
            try:
                self.radiation.writeDepthImageDataEXR(label, "d", image_path=td + os.sep)
                depth = read_depth_exr(os.path.join(td, f"{label}_d.exr"))
                out["depth"] = self._orient(depth).astype(np.float32)
            finally:
                if own_tmp:
                    import shutil
                    shutil.rmtree(td, ignore_errors=True)

        scale = exposure_scale if exposure_scale is not None else self.exposure_scale
        if scale is not None:
            out["rgb"] = tonemap(raw, scale, out.get("sky_mask"))
        return out

    def render_batch(self, poses, exposure_scale=None, read=True):
        """Solve once for `poses`, then read every camera back.

        Returns (frames, timing). `frames[i]` also carries `pose` (camera-to-world
        4x4) and `viewmat` (world-to-camera), derived from (eye, lookat) via the
        Phase 0 convention.
        """
        t_solve = self.solve(poses)
        frames, t_read = [], 0.0
        if read:
            td = tempfile.mkdtemp()
            try:
                t0 = time.time()
                for i, (eye, lookat) in enumerate(poses):
                    fr = self.read_camera(i, exposure_scale=exposure_scale, tmpdir=td)
                    viewmat = look_at_view_matrix(_V(eye), _V(lookat))
                    fr["viewmat"] = viewmat.astype(np.float32)
                    fr["pose"] = np.linalg.inv(viewmat).astype(np.float32)
                    fr["eye"] = np.asarray(eye, dtype=np.float32)
                    fr["lookat"] = np.asarray(lookat, dtype=np.float32)
                    frames.append(fr)
                t_read = time.time() - t0
            finally:
                import shutil
                shutil.rmtree(td, ignore_errors=True)
        return frames, {"solve_s": t_solve, "read_s": t_read, "n_cameras": len(poses)}

    # -- calibration ---------------------------------------------------------
    def calibrate_orientation(self, poses):
        """Solve once and pick the pixel-array orientation that matches the label
        map. Sets self._orientation and returns the report."""
        saved = self._orientation
        self._orientation = "as_is"
        self.solve(poses)
        w, h = self.resolution
        per_cam = []
        for i in range(len(poses)):
            label = self.camera_labels[i]
            raw = np.stack([np.asarray(self.radiation.getCameraPixelData(label, b),
                                        dtype=np.float32).reshape(h, w) for b in self.bands], axis=-1)
            lm = self.radiation.getPrimitiveDataLabelMap(label, SEMANTIC_CLASS_ID_FIELD)
            r = verify_pixel_orientation(raw, lm)
            if r["best"] is not None:
                per_cam.append(r)
        if not per_cam:
            self._orientation = saved
            return {"best": saved, "applied": saved, "n_usable_cameras": 0,
                    "note": "no calibration view had enough leaf AND fruit pixels"}
        agg = {k: float(np.mean([c["score_per_orientation"][k] for c in per_cam]))
               for k in ORIENTATIONS}
        best = max(agg, key=lambda k: agg[k])
        votes = {k: 0 for k in ORIENTATIONS}
        for c in per_cam:
            votes[c["best"]] += 1
        self._orientation = best
        return {"score_per_orientation": agg, "best": best, "best_score": agg[best],
                "per_camera_votes": votes, "n_usable_cameras": len(per_cam),
                "applied": best, "method": per_cam[0]["method"],
                "example_diagnostics": per_cam[0]["diagnostics"]}

    def calibrate_exposure(self, poses, percentile=99.0):
        """Compute ONE exposure scale from a set of calibration poses.

        Scale = the `percentile`-th percentile of raw radiance over all
        geometry-hit pixels across all calibration views. Dividing by it puts
        that percentile at 1.0 (white), so ~1% of canopy pixels clip -- which is
        what you want given the Phase 0 saturation artifact (a fixed-value pixel
        cluster that no flux setting removes): a max-based scale would be
        hostage to those pixels and crush everything else to black.
        """
        self.solve(poses)
        vals = []
        for i in range(len(poses)):
            label = self.camera_labels[i]
            w, h = self.resolution
            lm = self.radiation.getPrimitiveDataLabelMap(label, SEMANTIC_CLASS_ID_FIELD)
            hit = ~np.isnan(self._orient(lm))
            for b in self.bands:
                px = self._orient(np.asarray(self.radiation.getCameraPixelData(label, b),
                                              dtype=np.float32).reshape(h, w))
                vals.append(px[hit])
        allv = np.concatenate(vals) if vals else np.array([0.0], dtype=np.float32)
        scale = float(np.percentile(allv, percentile))
        report = {
            "percentile": percentile, "exposure_scale": scale,
            "n_samples": int(allv.size),
            "raw_min": float(allv.min()), "raw_max": float(allv.max()),
            "raw_mean": float(allv.mean()), "raw_median": float(np.median(allv)),
            "frac_above_scale": float((allv > scale).mean()),
        }
        self.exposure_scale = scale
        return report


def _V(v):
    """Duck-typed (x,y,z) accessor so poses may be tuples, lists, arrays or vec3."""
    class _P:
        __slots__ = ("x", "y", "z")
    p = _P()
    if hasattr(v, "x"):
        p.x, p.y, p.z = float(v.x), float(v.y), float(v.z)
    else:
        p.x, p.y, p.z = float(v[0]), float(v[1]), float(v[2])
    return p


def contact_sheet(frames, cols=8, key="rgb"):
    """Tile frames into one image for human inspection (W1 acceptance)."""
    imgs = [f[key] for f in frames]
    if imgs[0].ndim == 2:
        imgs = [np.stack([im] * 3, axis=-1) for im in imgs]
    h, w = imgs[0].shape[:2]
    rows = int(math.ceil(len(imgs) / cols))
    sheet = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = im
    return sheet


def colorize_depth(depth, dmin=None, dmax=None):
    """Grayscale depth preview; sky (-1) rendered black."""
    valid = depth != SKY_DEPTH_SENTINEL
    if not valid.any():
        return np.zeros(depth.shape + (3,), dtype=np.uint8)
    lo = float(np.min(depth[valid])) if dmin is None else dmin
    hi = float(np.max(depth[valid])) if dmax is None else dmax
    norm = np.zeros_like(depth)
    if hi > lo:
        norm[valid] = 1.0 - (depth[valid] - lo) / (hi - lo)
    g = (np.clip(norm, 0, 1) * 255).astype(np.uint8)
    return np.stack([g] * 3, axis=-1)
