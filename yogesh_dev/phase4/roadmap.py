"""
Reference copy of `worktree-phase3-kinematics:yogesh_dev/phase3/roadmap.py`
(T3.4 reachability roadmap: discretize joint space -> placeholder-collision
reject -> k-NN graph, edge weight = real T3.3 execution time), vendored here
per the cross-worktree reason in `kinematics.py`.

============================================================================
COLLISION CAVEAT -- carried forward unchanged from Phase 3, still true here
============================================================================
`CollisionDetection` (`castRaysSoA` / `findCollisions` / `buildBVH`) is not
exposed in PyHelios (T0.6, still unresolved as of Phase 4). The collision
check below is the SAME placeholder as Phase 3: reject a candidate node if
the camera's optical-center POINT falls inside a coarse per-plant AABB built
from real fruit bounding boxes -- not a ray-traced check against actual
leaf/branch/fruit triangle geometry, not swept along edges, blind to arm-link
volume. Every planner in Phase 4 (T4.6/T4.8/T4.9) that searches over this
roadmap inherits this placeholder-ness; it is not silently upgraded to real
collision anywhere in this phase either.
============================================================================
"""

import heapq
import itertools
import math
from typing import Dict, List, Tuple

import numpy as np

try:
    from .kinematics import ArmConfig, JointState, CameraPose, forward_kinematics, inverse_kinematics
    from .motion_time import move_time
except ImportError:  # standalone script use (e.g. gen_dataset.py), no package context
    from kinematics import ArmConfig, JointState, CameraPose, forward_kinematics, inverse_kinematics
    from motion_time import move_time


def discretize_joint_space(arm: ArmConfig, n_linear: int = 4, n_gimbal: int = 3):
    lim = arm.limits
    xs = np.linspace(lim.x[0], lim.x[1], n_linear)
    ys = np.linspace(lim.y[0], lim.y[1], n_linear)
    zs = np.linspace(lim.z[0], lim.z[1], n_linear)
    pans = np.linspace(lim.pan_deg[0], lim.pan_deg[1], n_gimbal)
    tilts = np.linspace(lim.tilt_deg[0], lim.tilt_deg[1], n_gimbal)
    for x, y, z, pan, tilt in itertools.product(xs, ys, zs, pans, tilts):
        yield JointState(x=float(x), y=float(y), z=float(z), pan_deg=float(pan), tilt_deg=float(tilt))


def canopy_box_from_fruit_records(fruit_records: List[dict], margin: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """Single-tree analogue of Phase 3's per-plant box dict: one AABB unioned
    over every fruit record's bbox_min/bbox_max, since Phase 4's dataset is
    one tree (see `gen_dataset.py`)."""
    bmin = None
    bmax = None
    for rec in fruit_records:
        lo = np.array(rec["bbox_min"], dtype=float)
        hi = np.array(rec["bbox_max"], dtype=float)
        bmin = lo if bmin is None else np.minimum(bmin, lo)
        bmax = hi if bmax is None else np.maximum(bmax, hi)
    return bmin - margin, bmax + margin


def point_in_box(point, bmin, bmax) -> bool:
    p = np.array(point, dtype=float)
    return bool(np.all(p >= bmin) and np.all(p <= bmax))


class RoadmapNode:
    __slots__ = ("node_id", "joint", "position", "lookat", "forward")

    def __init__(self, node_id: int, joint: JointState, pose: CameraPose):
        self.node_id = node_id
        self.joint = joint
        self.position = pose.position
        self.lookat = pose.lookat
        self.forward = pose.forward


def build_roadmap(arm: ArmConfig, canopy_box: Tuple[np.ndarray, np.ndarray],
                   n_linear: int = 4, n_gimbal: int = 3, k: int = 6,
                   ) -> Tuple[List[RoadmapNode], Dict[int, List[Tuple[int, float]]], int]:
    """Same algorithm as Phase 3's `build_roadmap`, adapted to a single AABB
    (canopy_box) instead of a per-plant dict, since a candidate node here is
    only ever rejected for being INSIDE the fruit-bearing volume it's
    supposed to be looking AT from outside (a real rail-mounted camera can't
    occupy the space its own tree's fruit occupies)."""
    bmin, bmax = canopy_box
    nodes: List[RoadmapNode] = []
    n_rejected = 0
    for joint in discretize_joint_space(arm, n_linear, n_gimbal):
        pose = forward_kinematics(joint, arm)
        if point_in_box(pose.position, bmin, bmax):
            n_rejected += 1
            continue
        nodes.append(RoadmapNode(len(nodes), joint, pose))

    lim = arm.limits
    ranges = np.array([lim.x[1] - lim.x[0], lim.y[1] - lim.y[0], lim.z[1] - lim.z[0],
                        lim.pan_deg[1] - lim.pan_deg[0], lim.tilt_deg[1] - lim.tilt_deg[0]], dtype=float)
    ranges[ranges == 0] = 1.0

    n = len(nodes)
    adjacency: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(n)}
    if n > 1:
        coords = np.array([node.joint.as_tuple() for node in nodes], dtype=float) / ranges
        k_eff = min(k, n - 1)
        best: Dict[int, Dict[int, float]] = {i: {} for i in range(n)}
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


def all_pairs_time(adjacency: Dict[int, List[Tuple[int, float]]], sources: List[int]) -> Dict[int, Dict[int, float]]:
    """Dijkstra from each of `sources` to every reachable node -- used by the
    receding-horizon planners (T4.6/T4.8) to get a real execution-time cost
    from 'wherever the arm currently is' to any candidate node, without
    recomputing shortest paths from scratch at every planning step."""
    out = {}
    for s in sources:
        dist = {s: 0.0}
        visited = set()
        pq = [(0.0, s)]
        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            for v, w in adjacency.get(u, []):
                nd = d + w
                if v not in dist or nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        out[s] = dist
    return out
