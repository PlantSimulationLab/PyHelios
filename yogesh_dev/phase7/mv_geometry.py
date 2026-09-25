"""
Hand-rolled classical multi-view geometry, used as the real, honest proxy
for the named foundation-model anchors (MapAnything/DA3/pi-cubed/VGGT)
that T7.2/T7.3 call for -- see PHASE7_LOG.md "Environment check" for why:
none of those packages (nor torch/opencv/scipy/sklearn) are installed in
the `helios` conda env, and this phase did not install them.

Every function here is standard textbook multi-view geometry (Hartley &
Zisserman), implemented directly on top of `numpy.linalg` (SVD, lstsq) --
no external CV library. This is what lets T7.2/T7.3 test the REAL
underlying hypothesis ("does more pose/depth conditioning improve
reconstruction, especially at small baseline") with a real (if much
smaller/simpler than a transformer) reconstruction pipeline, rather than
fabricating numbers from a foundation model that never ran.

Four building blocks, matching the four T7.2 conditions:
  - `project_point`                          : forward model shared by all conditions
  - `triangulate_linear` (DLT)                : used when K,R,t are all known (condition C/D)
  - `eight_point_fundamental` + `canonical_P2_from_F` : uncalibrated two-view (condition A)
  - `eight_point_essential` + `decompose_essential` + `select_pose_from_essential`
                                               : calibrated-but-unposed two-view (condition B)
  - `umeyama_alignment` / `affine_alignment`  : honest post-hoc alignment for the
    ambiguity each condition actually leaves unresolved (similarity for B's
    unknown scale, full affine for A's unknown projective-to-affine gap) --
    never silently given ground-truth scale/rotation.
"""

import math

import numpy as np


# ---------------------------------------------------------------------------
# Forward projection (shared ground-truth-generation step: since Helios gives
# exact 3D landmark truth, this stands in for feature detection + matching --
# a documented simplification, not an attempt to fake a correspondence-finding
# step no anchor here actually needs).
# ---------------------------------------------------------------------------

def project_point(K, viewmat, X):
    """World point (3,) -> ((u,v), camera-space depth) via K @ [R|t]."""
    Xh = np.array([X[0], X[1], X[2], 1.0])
    cam = viewmat @ Xh
    p = K @ cam[:3]
    if abs(p[2]) < 1e-12:
        return None, cam[2]
    return np.array([p[0] / p[2], p[1] / p[2]]), cam[2]


def add_pixel_noise(pts, sigma_px, seed):
    rng = np.random.default_rng(seed)
    pts = np.asarray(pts, dtype=float)
    return pts + rng.normal(0.0, sigma_px, size=pts.shape)


# ---------------------------------------------------------------------------
# Condition C/D: known K, R, t for every view -> linear (DLT) triangulation.
# ---------------------------------------------------------------------------

def projection_matrix(K, viewmat):
    return K @ viewmat[:3, :]


def triangulate_linear(Ps, pts):
    """N-view DLT triangulation of one 3D point. Ps: list of 3x4 projection
    matrices. pts: list of (u,v). Returns (3,) world point."""
    A = []
    for P, (u, v) in zip(Ps, pts):
        A.append(u * P[2] - P[0])
        A.append(v * P[2] - P[1])
    A = np.asarray(A)
    _, _, Vt = np.linalg.svd(A)
    X = Vt[-1]
    return X[:3] / X[3]


# ---------------------------------------------------------------------------
# Condition A: uncalibrated two-view -> normalized 8-point fundamental matrix
# + canonical projective reconstruction (Hartley & Zisserman ch.9).
# ---------------------------------------------------------------------------

def _normalize_points(pts):
    pts = np.asarray(pts, dtype=float)
    centroid = pts.mean(axis=0)
    shifted = pts - centroid
    mean_dist = np.mean(np.linalg.norm(shifted, axis=1))
    scale = math.sqrt(2.0) / mean_dist if mean_dist > 1e-9 else 1.0
    T = np.array([[scale, 0.0, -scale * centroid[0]],
                  [0.0, scale, -scale * centroid[1]],
                  [0.0, 0.0, 1.0]])
    pts_h = np.hstack([pts, np.ones((len(pts), 1))])
    pts_norm = (T @ pts_h.T).T
    return pts_norm[:, :2], T


def eight_point_fundamental(pts1, pts2):
    """Normalized 8-point algorithm. pts1/pts2: (N,2) pixel coordinates,
    N >= 8. Returns 3x3 F with x2^T F x1 = 0, rank enforced to 2."""
    p1n, T1 = _normalize_points(pts1)
    p2n, T2 = _normalize_points(pts2)
    N = len(p1n)
    A = np.zeros((N, 9))
    for i in range(N):
        x1, y1 = p1n[i]
        x2, y2 = p2n[i]
        A[i] = [x2 * x1, x2 * y1, x2, y2 * x1, y2 * y1, y2, x1, y1, 1.0]
    _, _, Vt = np.linalg.svd(A)
    F = Vt[-1].reshape(3, 3)
    U, S, Vt2 = np.linalg.svd(F)
    S[2] = 0.0
    F = U @ np.diag(S) @ Vt2
    F = T2.T @ F @ T1
    return F / np.linalg.norm(F)


def canonical_P2_from_F(F):
    """Canonical projective camera pair P1=[I|0], P2=[[e']_x F | e'] for an
    uncalibrated two-view reconstruction (H&Z Result 9.14/9.15)."""
    P1 = np.hstack([np.eye(3), np.zeros((3, 1))])
    _, _, Vt = np.linalg.svd(F.T)
    e2 = Vt[-1]
    if abs(e2[2]) > 1e-9:
        e2 = e2 / e2[2]
    ex = np.array([[0.0, -e2[2], e2[1]],
                   [e2[2], 0.0, -e2[0]],
                   [-e2[1], e2[0], 0.0]])
    P2 = np.hstack([ex @ F, e2.reshape(3, 1)])
    return P1, P2


# ---------------------------------------------------------------------------
# Condition B: known K but unknown R,t -> essential matrix, pose recovery up
# to an unresolvable global scale (classic monocular ambiguity).
# ---------------------------------------------------------------------------

def eight_point_essential(pts1_px, pts2_px, K1, K2=None):
    """F in pixel space (8-point), then E = K2^T F K1 with the two unit
    singular values enforced (the essential-matrix constraint)."""
    if K2 is None:
        K2 = K1
    F = eight_point_fundamental(pts1_px, pts2_px)
    E = K2.T @ F @ K1
    U, S, Vt = np.linalg.svd(E)
    E = U @ np.diag([1.0, 1.0, 0.0]) @ Vt
    return E


def decompose_essential(E):
    """4 candidate (R, t) [t unit-norm, true scale unrecoverable from E alone]."""
    U, _, Vt = np.linalg.svd(E)
    if np.linalg.det(U) < 0:
        U = -U
    if np.linalg.det(Vt) < 0:
        Vt = -Vt
    W = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    R1 = U @ W @ Vt
    R2 = U @ W.T @ Vt
    t = U[:, 2]
    return [(R1, t), (R1, -t), (R2, t), (R2, -t)]


def select_pose_from_essential(E, K1, K2, pts1_px, pts2_px):
    """Cheirality check across all correspondences: pick the (R,t) that
    puts the most triangulated points in front of BOTH cameras."""
    candidates = decompose_essential(E)
    P1 = K1 @ np.hstack([np.eye(3), np.zeros((3, 1))])
    best = None
    best_score = -1
    for R, t in candidates:
        P2 = K2 @ np.hstack([R, t.reshape(3, 1)])
        good = 0
        for pt1, pt2 in zip(pts1_px, pts2_px):
            X = triangulate_linear([P1, P2], [pt1, pt2])
            depth1 = X[2]
            depth2 = (R @ X + t)[2]
            if depth1 > 0 and depth2 > 0:
                good += 1
        if good > best_score:
            best_score, best = good, (R, t, P2)
    R, t, P2 = best
    return R, t, P2, best_score


# ---------------------------------------------------------------------------
# Post-hoc alignment: honest about what each condition leaves ambiguous.
# ---------------------------------------------------------------------------

def umeyama_alignment(src, dst, with_scale=True):
    """Least-squares similarity transform (rotation + isotropic scale +
    translation) mapping src -> dst (Umeyama 1991, closed form). Used for
    condition B: essential-matrix reconstruction is correct up to an
    unknown global scale + rigid transform, so "shape accuracy" is only
    fairly measured after removing that ambiguity -- the ambiguity itself
    (the recovered scale factor `s`) is reported separately, since a
    monocular/unposed model recovering the wrong absolute scale IS part
    of the finding, not something to hide by aligning it away silently.
    """
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    n, dim = src.shape
    mu_src, mu_dst = src.mean(axis=0), dst.mean(axis=0)
    src_c, dst_c = src - mu_src, dst - mu_dst
    cov = (dst_c.T @ src_c) / n
    U, S, Vt = np.linalg.svd(cov)
    D = np.eye(dim)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[-1, -1] = -1.0
    R = U @ D @ Vt
    if with_scale:
        var_src = (src_c ** 2).sum() / n
        s = float(np.trace(np.diag(S) @ D) / var_src) if var_src > 1e-12 else 1.0
    else:
        s = 1.0
    t = mu_dst - s * (R @ mu_src)
    aligned = (s * (R @ src.T)).T + t
    rmse = float(np.sqrt(np.mean(np.sum((aligned - dst) ** 2, axis=1))))
    return {"R": R, "t": t, "s": s, "aligned": aligned, "rmse": rmse}


def affine_alignment(src, dst):
    """Best-fit full affine (12-DOF: 3x4) map src -> dst, least squares.
    Used for condition A: uncalibrated canonical reconstruction is only
    defined up to an unknown projective transform in general; fitting the
    best AFFINE map (a strict subset of projective) and reporting its
    residual is a generous upper bound on how good an uncalibrated
    reconstruction could look after the best possible rectification --
    real error for a genuinely projective (non-affine) ambiguity is
    typically worse than this number, not better."""
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    n = len(src)
    src_h = np.hstack([src, np.ones((n, 1))])
    A, *_ = np.linalg.lstsq(src_h, dst, rcond=None)
    aligned = src_h @ A
    rmse = float(np.sqrt(np.mean(np.sum((aligned - dst) ** 2, axis=1))))
    return {"A": A, "aligned": aligned, "rmse": rmse}


def rmse_rigid(points_a, points_b):
    """Plain RMSE, no alignment -- used for conditions C/D where the
    reconstruction is already in the true metric world frame (known K,R,t),
    so ANY residual error is real reconstruction error, not a gauge
    freedom to be aligned away."""
    a = np.asarray(points_a, dtype=float)
    b = np.asarray(points_b, dtype=float)
    return float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1))))
