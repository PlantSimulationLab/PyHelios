"""
T3.4 -- Reachability roadmap.

Nodes = discretized reachable 5-DOF joint-space samples per arm, with FK (and
trivially, IK -- see below) cached. Edges = k-NN in joint space, weighted by
REAL execution time from `motion_time.move_time` (T3.3) rather than raw
joint-space distance, so planning over this structure reduces to graph
search (Dijkstra / shortest path), matching the task doc.

On "IK cached": since roadmap nodes are enumerated directly as joint-space
grid points (not sampled in camera-pose/workspace space and then inverted),
IK is not doing new work here -- each node already stores its own joints
alongside its FK-derived pose. The place IK actually gets *used* is
`kinematics.verify_roundtrip` and any future planner that proposes a desired
camera pose and needs the nearest graph node (`nearest_node_to_pose` below
uses IK for exactly that).

On "cart position" (task doc T3.4: "Precompute once per cart position"):
this codebase's 5-DOF chain already includes the rail axis (x, "left-right")
as one of the 5 discretized DOFs, rather than treating "cart position" as a
separate outer loop -- so a "cart position" in the task doc's sense
corresponds to one x-slice of this roadmap. Building the full 5-DOF roadmap
once (as done here) is equivalent to precomputing it for every cart position
simultaneously; a real deployment that wants to precompute the (cheaper) y/z
/pan/tilt sub-roadmap once per discrete cart stop instead of the full 5-DOF
product could slice this module's `discretize_joint_space` by fixing x per
call -- not implemented separately since it's a straightforward reslicing of
the same grid, not new machinery.

============================================================================
COLLISION CAVEAT -- READ BEFORE TRUSTING ANY "REACHABLE" NUMBER BELOW
============================================================================
`CollisionDetection` (`castRaysSoA` / `findCollisions` /
`findCollisionsWithinDistance` / `buildBVH`) is NOT exposed in PyHelios
(`pyhelios/config/plugin_metadata.py`: "CollisionDetection dependency
handled at C++ level, not exposed in Python API"). This is blocked on T0.6
and nothing below fakes it.

The collision check actually used here (`point_in_any_box` /
`canopy_boxes_from_ground_truth`) rejects a candidate node if the CAMERA'S
OPTICAL-CENTER POINT falls inside the coarse per-tree axis-aligned bounding
box of that tree's fruit, aggregated from Phase 1's real
`fruit_ground_truth.json` export. Precisely, this is:
  - a POINT-vs-BOX test on one point (the camera position) -- not a
    ray-traced test against actual leaf/branch/fruit triangle geometry;
  - a box built from FRUIT bounding boxes only, not the full canopy (leaves
    and branches extend beyond the fruit envelope in both directions -- this
    box is neither a superset nor subset of the true canopy volume);
  - evaluated once per discrete node -- no continuous sweep along the path
    an arm would travel between two connected roadmap nodes;
  - blind to the T3.5 arm-link boxes -- it does not check whether the mast/
    column itself (as opposed to the camera point) would clip the canopy.

Swapping in real `findCollisions`/`castRaysSoA` (once T0.6 lands) would
change all four of the above: per-primitive resolution instead of a coarse
box (fixing both false rejections in empty space inside the box and false
acceptances from geometry poking outside it), continuous path sweeps instead
of discrete endpoints, checks against the T3.5 arm volume instead of a bare
point, and support for arbitrary ray origins (needed for Phase 2's
fruit-outward visibility too, which this bounding-box test cannot do at
all).
============================================================================
"""

import heapq
import itertools
import math
from typing import Dict, List, Tuple

import numpy as np

from .kinematics import ArmConfig, JointState, CameraPose, forward_kinematics, inverse_kinematics
from .motion_time import move_time


def discretize_joint_space(arm: ArmConfig, n_linear: int = 4, n_gimbal: int = 3):
    """Yield JointState samples on a regular grid spanning `arm`'s limits.

    n_linear/n_gimbal are demo-scale grid resolutions (n_linear^3 * n_gimbal^2
    total samples before collision rejection) -- real deployment would tune
    these against the T0.5 render-cost budget and the actual required pose
    density, not hardcode 4/3.
    """
    lim = arm.limits
    xs = np.linspace(lim.x[0], lim.x[1], n_linear)
    ys = np.linspace(lim.y[0], lim.y[1], n_linear)
    zs = np.linspace(lim.z[0], lim.z[1], n_linear)
    pans = np.linspace(lim.pan_deg[0], lim.pan_deg[1], n_gimbal)
    tilts = np.linspace(lim.tilt_deg[0], lim.tilt_deg[1], n_gimbal)
    for x, y, z, pan, tilt in itertools.product(xs, ys, zs, pans, tilts):
        yield JointState(x=float(x), y=float(y), z=float(z),
                          pan_deg=float(pan), tilt_deg=float(tilt))


def canopy_boxes_from_ground_truth(fruit_records: List[dict]) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
    """Coarse per-plant axis-aligned bounding box built from Phase 1's real
    `fruit_ground_truth.json` records (`bbox_min`/`bbox_max` per fruit,
    unioned per `plant_id`). See module docstring for exactly what this
    placeholder collision volume is NOT."""
    boxes: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}
    for rec in fruit_records:
        pid = rec["plant_id"]
        bmin = np.array(rec["bbox_min"], dtype=float)
        bmax = np.array(rec["bbox_max"], dtype=float)
        if pid not in boxes:
            boxes[pid] = (bmin.copy(), bmax.copy())
        else:
            cur_min, cur_max = boxes[pid]
            boxes[pid] = (np.minimum(cur_min, bmin), np.maximum(cur_max, bmax))
    return boxes


def point_in_any_box(point: Tuple[float, float, float],
                      boxes: Dict[int, Tuple[np.ndarray, np.ndarray]],
                      margin: float = 0.0) -> Tuple[bool, object]:
    p = np.array(point, dtype=float)
    for pid, (bmin, bmax) in boxes.items():
        if np.all(p >= bmin - margin) and np.all(p <= bmax + margin):
            return True, pid
    return False, None


class RoadmapNode:
    __slots__ = ("node_id", "joint", "position", "lookat", "forward")

    def __init__(self, node_id: int, joint: JointState, pose: CameraPose):
        self.node_id = node_id
        self.joint = joint
        self.position = pose.position
        self.lookat = pose.lookat
        self.forward = pose.forward


def build_roadmap(arm: ArmConfig, canopy_boxes: Dict[int, Tuple[np.ndarray, np.ndarray]],
                   n_linear: int = 4, n_gimbal: int = 3, k: int = 6,
                   collision_margin: float = 0.0) -> Tuple[List[RoadmapNode], Dict[int, List[Tuple[int, float]]], int]:
    """Build the roadmap for one arm: discretize -> reject via the placeholder
    collision check -> connect surviving nodes with a k-NN graph in
    normalized joint space, edge weight = real T3.3 execution time.

    Returns (nodes, adjacency, n_rejected) where adjacency[i] is a list of
    (neighbor_node_id, weight_seconds).
    """
    nodes: List[RoadmapNode] = []
    n_rejected = 0
    for joint in discretize_joint_space(arm, n_linear, n_gimbal):
        pose = forward_kinematics(joint, arm)
        blocked, _pid = point_in_any_box(pose.position, canopy_boxes, margin=collision_margin)
        if blocked:
            n_rejected += 1
            continue
        nodes.append(RoadmapNode(len(nodes), joint, pose))

    lim = arm.limits
    ranges = np.array([
        lim.x[1] - lim.x[0], lim.y[1] - lim.y[0], lim.z[1] - lim.z[0],
        lim.pan_deg[1] - lim.pan_deg[0], lim.tilt_deg[1] - lim.tilt_deg[0],
    ], dtype=float)
    ranges[ranges == 0] = 1.0

    n = len(nodes)
    adjacency: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(n)}
    if n > 1:
        coords = np.array([node.joint.as_tuple() for node in nodes], dtype=float) / ranges
        k_eff = min(k, n - 1)
        best: Dict[int, Dict[int, float]] = {i: {} for i in range(n)}
        # Brute-force k-NN in normalized joint space -- no scipy/networkx in
        # the `helios` env; fine at this demo's node counts (low thousands).
        for i in range(n):
            d = np.linalg.norm(coords - coords[i], axis=1)
            d[i] = np.inf
            knn = np.argpartition(d, k_eff - 1)[:k_eff] if k_eff < n - 1 else np.argsort(d)[:k_eff]
            for j in knn:
                j = int(j)
                w = move_time(nodes[i].joint, nodes[j].joint)
                if j not in best[i] or w < best[i][j]:
                    best[i][j] = w
                if i not in best[j] or w < best[j][i]:
                    best[j][i] = w
        adjacency = {i: sorted(best[i].items()) for i in range(n)}

    return nodes, adjacency, n_rejected


def dijkstra(adjacency: Dict[int, List[Tuple[int, float]]], start: int, goal: int) -> Tuple[List[int], float]:
    """Shortest path by real execution-time weight. Returns (path_node_ids,
    total_time_seconds); (None, inf) if unreachable."""
    dist = {start: 0.0}
    prev: Dict[int, int] = {}
    visited = set()
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        if u == goal:
            break
        for v, w in adjacency.get(u, []):
            nd = d + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    if goal not in dist:
        return None, math.inf

    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path, dist[goal]


def nearest_node_to_pose(nodes: List[RoadmapNode], arm: ArmConfig, pose: CameraPose) -> Tuple[int, float]:
    """IK the requested pose, then find the roadmap node closest to the
    resulting joint state (normalized joint-space distance). Demonstrates
    the IK-cached-node lookup path referenced in the module docstring."""
    q, _ok, _violations = inverse_kinematics(pose, arm)
    lim = arm.limits
    ranges = np.array([
        lim.x[1] - lim.x[0], lim.y[1] - lim.y[0], lim.z[1] - lim.z[0],
        lim.pan_deg[1] - lim.pan_deg[0], lim.tilt_deg[1] - lim.tilt_deg[0],
    ], dtype=float)
    ranges[ranges == 0] = 1.0
    q_norm = np.array(q.as_tuple()) / ranges
    best_id, best_dist = None, math.inf
    for node in nodes:
        d = np.linalg.norm(np.array(node.joint.as_tuple()) / ranges - q_norm)
        if d < best_dist:
            best_id, best_dist = node.node_id, d
    return best_id, best_dist
