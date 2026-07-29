"""
T0.3 [BLOCKER] -- Empirically verify the RadiationCamera pose convention.

The radiation camera is configured with only `position` + `lookat` (see
`addRadiationCamera` in pyhelios/RadiationModel.py); there is no explicit
up-vector parameter and no matrix getter. `apple_tree_gaussian_splatting.py`'s
`look_at_view_matrix()` assumes an OpenCV-style camera frame (X-right,
Y-down, Z-forward) built from `world_up=(0,0,1)`, reverse-engineered against
the Visualizer. This script does NOT assume that convention carries over to
the radiation camera -- it tests it.

Method
------
1. Build a scene with N spheres at known world coordinates spanning the
   frame in front of one radiation camera.
2. Tag each sphere with a unique integer `sphere_id` primitive-data value.
3. Run the radiation model once (`updateGeometry` + `runBand`), then read
   back the per-pixel primitive-data label map (`getPrimitiveDataLabelMap`),
   which for each pixel gives the `sphere_id` of whatever the camera ray hit
   (or NaN for background).
4. For each sphere, compute the MEASURED pixel centroid = mean (row, col)
   over all pixels labeled with that sphere's id.
5. Compute the PREDICTED pixel coordinate for the sphere's world-space
   center by projecting it through a candidate camera model:
   K @ [R|t] @ X, where [R|t] comes from `look_at_view_matrix()` (OpenCV
   convention, world_up=+Z) and K is the pinhole intrinsics matrix implied
   by the camera's HFOV/resolution.
6. Compare measured vs. predicted. If they don't line up, sweep a small set
   of candidate pixel-axis flips (row/col) to find which transform (if any)
   reproduces the image sub-pixel. Report whatever is ACTUALLY true, not
   what was assumed.

Run directly:
    /home/yogesh/anaconda3/envs/helios/bin/python yogesh_dev/phase0/pose_convention.py
"""

import math
import numpy as np

from pyhelios import Context, RadiationModel
from pyhelios.RadiationModel import CameraProperties
from pyhelios.types import vec3, RGBcolor


def hfov_from_vfov(vfov_deg, aspect_ratio):
    """HFOV = 2*atan(aspect * tan(VFOV/2)) -- see T0.2 / apple_tree_cameras.py's
    CAMERA_FOV_DEG, which is VERTICAL, not horizontal as CameraProperties expects."""
    half_vfov = math.radians(vfov_deg) / 2.0
    half_hfov = math.atan(aspect_ratio * math.tan(half_vfov))
    return math.degrees(2.0 * half_hfov)


def look_at_view_matrix(eye, lookat, world_up=(0.0, 0.0, 1.0)):
    """World-to-camera matrix, OpenCV convention (X-right, Y-down, Z-forward).

    Copied from apple_tree_gaussian_splatting.py's look_at_view_matrix() --
    this is the candidate convention under test, not an assumption we bake in.
    """
    eye_np = np.array([eye.x, eye.y, eye.z], dtype=np.float64)
    center_np = np.array([lookat.x, lookat.y, lookat.z], dtype=np.float64)
    up_np = np.array(world_up, dtype=np.float64)

    forward = center_np - eye_np
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up_np)
    if np.linalg.norm(right) < 1e-6:
        up_np = np.array([1.0, 0.0, 0.0])
        right = np.cross(forward, up_np)
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)

    rotation_c2w = np.stack([right, down, forward], axis=1)
    viewmat = np.eye(4, dtype=np.float64)
    viewmat[:3, :3] = rotation_c2w.T
    viewmat[:3, 3] = -rotation_c2w.T @ eye_np
    return viewmat


def intrinsics_matrix(width, height, hfov_deg):
    focal = (width / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
    return np.array([[focal, 0.0, width / 2.0],
                      [0.0, focal, height / 2.0],
                      [0.0, 0.0, 1.0]])


def project(K, viewmat, world_point):
    """Project a world point through [R|t] then K. Returns (u, v) in pixel space,
    OpenCV convention: u=0 at left edge, v=0 at top edge."""
    X = np.array([world_point.x, world_point.y, world_point.z, 1.0])
    cam = viewmat @ X
    p = K @ cam[:3]
    return p[0] / p[2], p[1] / p[2]


def run_pose_convention_test(resolution=(320, 240), vfov_deg=45.0, n_grid=3,
                              antialiasing_samples=8, log_lines=None,
                              eye=None, lookat=None, camera_label="posecam"):
    """Places a grid of spheres in front of one radiation camera, renders,
    and reports measured-vs-predicted pixel centroids under several candidate
    pixel-axis conventions. Returns a dict of results (see bottom of function).

    `eye`/`lookat` default to an axis-aligned pose (camera on -Y looking at
    +Y); pass an off-axis pose (e.g. not aligned with any single world axis)
    to rule out the axis-aligned case being a coincidental match.
    """
    if log_lines is None:
        log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    width, height = resolution
    aspect = width / height
    hfov_deg = hfov_from_vfov(vfov_deg, aspect)

    if eye is None:
        eye = vec3(0.0, -5.0, 1.0)
    if lookat is None:
        lookat = vec3(0.0, 0.0, 1.0)

    # Grid of sphere centers spanning the frame around the lookat point:
    # offset in {-1.2,0,1.2} along camera-frame "right"-ish (world X) and
    # {-0.8,0,0.8} in Z (down/up), with a small jitter along the third axis
    # per sphere so they aren't perfectly coplanar (closer to a real scene).
    xs = np.linspace(-1.2, 1.2, n_grid)
    zs = np.linspace(-0.8, 0.8, n_grid)
    jitter = [-0.4, 0.0, 0.4]

    spheres = []  # (sphere_id, center vec3)
    sphere_id = 1
    for zi, z in enumerate(zs):
        for xi, x in enumerate(xs):
            j = jitter[(xi + zi) % len(jitter)]
            spheres.append((sphere_id, vec3(lookat.x + x, lookat.y + j, lookat.z + z)))
            sphere_id += 1

    log(f"Camera: eye={eye}, lookat={lookat}, VFOV={vfov_deg} deg -> HFOV={hfov_deg:.4f} deg, "
        f"resolution={width}x{height}, aspect={aspect:.4f}")
    log(f"Placed {len(spheres)} spheres spanning x in [{xs.min():.2f},{xs.max():.2f}], "
        f"z in [{zs.min():.2f},{zs.max():.2f}]")

    with Context() as context:
        for sid, center in spheres:
            uuids = context.addSphere(center=center, radius=0.06, ndivs=12,
                                       color=RGBcolor(0.8, 0.8, 0.8))
            context.setPrimitiveDataInt(uuids, "sphere_id", sid)

        with RadiationModel(context) as radiation:
            radiation.addRadiationBand("red", 600, 700)
            sun = radiation.addSunSphereRadiationSource(radius=0.5, zenith=30.0, azimuth=0.0)
            radiation.setSourceFlux(sun, "red", 500.0)
            radiation.setDiffuseRadiationFlux("red", 50.0)
            radiation.setScatteringDepth("red", 1)

            cam_props = CameraProperties(
                camera_resolution=(width, height),
                lens_diameter=0.0,
                HFOV=hfov_deg,
                FOV_aspect_ratio=0.0,
            )
            radiation.addRadiationCamera(camera_label, ["red"], eye, lookat,
                                          camera_properties=cam_props,
                                          antialiasing_samples=antialiasing_samples)

            radiation.updateGeometry()
            radiation.runBand("red")

            label_map = radiation.getPrimitiveDataLabelMap(camera_label, "sphere_id")

    H, W = label_map.shape
    assert (H, W) == (height, width), f"label map shape {label_map.shape} != ({height},{width})"

    K = intrinsics_matrix(width, height, hfov_deg)
    viewmat = look_at_view_matrix(eye, lookat, world_up=(0.0, 0.0, 1.0))

    measured = {}   # sphere_id -> (row, col) centroid, raw array indices
    predicted = {}  # sphere_id -> (u, v) OpenCV pixel coords (u=col-like, v=row-like)
    for sid, center in spheres:
        rows, cols = np.where(label_map == sid)
        if len(rows) == 0:
            measured[sid] = None
        else:
            measured[sid] = (float(rows.mean()), float(cols.mean()))
        u, v = project(K, viewmat, center)
        predicted[sid] = (u, v)

    # Candidate pixel-array <-> (u,v) mappings to test. "row" and "col" here
    # are the raw label_map array indices; u,v are the OpenCV-style predicted
    # pixel coordinates (u: 0=left..W=right, v: 0=top..H=bottom).
    candidates = {
        "row=v, col=u (standard top-left origin)":
            lambda row, col: (col, row),
        "row=H-1-v, col=u (vertical flip)":
            lambda row, col: (col, height - 1 - row),
        "row=v, col=W-1-u (horizontal flip)":
            lambda row, col: (width - 1 - col, row),
        "row=H-1-v, col=W-1-u (both flipped / 180 rot)":
            lambda row, col: (width - 1 - col, height - 1 - row),
    }

    results = {}
    for name, to_uv in candidates.items():
        errors = []
        for sid, _ in spheres:
            if measured[sid] is None:
                continue
            row, col = measured[sid]
            u_meas, v_meas = to_uv(row, col)
            u_pred, v_pred = predicted[sid]
            err = math.hypot(u_meas - u_pred, v_meas - v_pred)
            errors.append(err)
        results[name] = {
            "n": len(errors),
            "mean_err_px": float(np.mean(errors)) if errors else None,
            "max_err_px": float(np.max(errors)) if errors else None,
        }

    n_hit = sum(1 for sid, _ in spheres if measured[sid] is not None)
    log(f"{n_hit}/{len(spheres)} spheres visible (nonzero pixel count) in the render")

    log("\nCandidate convention -> reprojection error (pixels):")
    best_name, best = None, None
    for name, r in results.items():
        if r["mean_err_px"] is None:
            log(f"  {name}: no data")
            continue
        log(f"  {name}: mean={r['mean_err_px']:.3f}px  max={r['max_err_px']:.3f}px  (n={r['n']})")
        if best is None or r["mean_err_px"] < best["mean_err_px"]:
            best_name, best = name, r

    log(f"\nBest-fitting convention: '{best_name}' "
        f"(mean {best['mean_err_px']:.3f}px, max {best['max_err_px']:.3f}px)")
    sub_pixel = best["mean_err_px"] < 1.0
    log(f"Sub-pixel match: {sub_pixel}")

    return {
        "results": results,
        "best_name": best_name,
        "best": best,
        "sub_pixel": sub_pixel,
        "n_visible": n_hit,
        "n_total": len(spheres),
        "log_lines": log_lines,
        "hfov_deg": hfov_deg,
        "resolution": (width, height),
    }


def main():
    print("=" * 70)
    print("Pose 1: axis-aligned (eye on -Y, looking down +Y, up ~ +Z)")
    print("=" * 70)
    r1 = run_pose_convention_test(
        eye=vec3(0.0, -5.0, 1.0), lookat=vec3(0.0, 0.0, 1.0), camera_label="posecam_axis")

    print()
    print("=" * 70)
    print("Pose 2: off-axis (eye not aligned with any single world axis)")
    print("=" * 70)
    r2 = run_pose_convention_test(
        eye=vec3(3.2, -4.1, 2.6), lookat=vec3(0.3, 0.2, 0.9), camera_label="posecam_oblique")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, r in (("axis-aligned", r1), ("off-axis", r2)):
        b = r["best"]
        print(f"{name}: convention='{r['best_name']}', mean={b['mean_err_px']:.3f}px, "
              f"max={b['max_err_px']:.3f}px, sub_pixel={r['sub_pixel']}, "
              f"visible={r['n_visible']}/{r['n_total']}")
    return r1, r2


if __name__ == "__main__":
    main()
