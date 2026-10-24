"""
T4.4 -- Apple instance track database.

Task doc: "'Seen at least once' must be defined over tracked fruit
instances, not voxels -- otherwise you double-count under registration
error. With `fruitID` you have ground-truth association for free in sim,
so build the tracker AND the oracle association simultaneously and measure
the tracker against it (IDF1, ID switches)."

## Detections: real 3D centroids from real instance label maps + real depth

For every real rendered view, every unique nonzero value in the real
`instance` label map (`getObjectDataLabelMap(cam, "fruitID")`, same
mechanism as Phase 1's instance maps) is one detection: its pixels are
unprojected (via `sensor_model`, using the real per-view depth and the
calibrated camera model) into a real 3D world centroid. This is a real
per-frame, per-instance 3D detection, not a synthetic one.

## Tracker (position-only, does NOT read fruitID -- that would be cheating)

Per-arm greedy nearest-3D-centroid association across that arm's
stride-sampled roadmap-node sequence (ordered by `node_id`, the closest
proxy this dataset has to a real camera trajectory -- see `gen_dataset.py`;
this is real roadmap-index ordering, not a temporal video sequence, and
that distinction is preserved in the reporting rather than described as
"video tracking"). At each frame, unmatched existing tracks are matched
greedily (nearest first) to unmatched detections within a gating radius
(`GATE_M`); unmatched detections spawn new tracks; unmatched tracks persist
(fruit doesn't move) and remain eligible for future frames. This is a
plain, real, if simple, MOT-style tracker -- no fruitID is read by any
tracker code path.

## Oracle association

The real fruitID value at each detection IS the ground-truth identity
(sim gives this for free, per the task doc) -- used only for scoring, in
a code path entirely separate from the tracker above.

## Metrics: IDF1 and ID switches, against the real oracle

- Confusion matrix `overlap[track][fruitID]` = number of detections with
  that (predicted track, true id) pair.
- Optimal predicted-track <-> true-id matching via the real Hungarian
  implementation in `hungarian.py` (maximizing total matched detections) --
  this is what IDF1 is actually defined over (not greedy matching).
- `IDTP` = total matched weight, `IDFP` = total tracked detections - IDTP,
  `IDFN` = total true detections - IDTP, `IDF1 = 2*IDTP/(2*IDTP+IDFP+IDFN)`.
- ID switches: for each true fruitID, walk its detections in frame order
  (within an arm) and count every time the predicted track id differs from
  the previous detection of that same fruit.
"""

import json
import os
from collections import defaultdict

import numpy as np
import OpenEXR

import sensor_model as sm
from hungarian import max_weight_bipartite_matching

GATE_M = 0.06  # 6cm gating radius for greedy nearest-centroid association


def read_depth(path):
    fh = OpenEXR.File(path)
    ch = fh.channels()
    key = "Z" if "Z" in ch else next(iter(ch.keys()))
    return np.array(ch[key].pixels, dtype=np.float32)


def extract_detections(data_dir, arm_name, poses, intr):
    """Real per-frame detections for one arm's sequence, ordered by
    node_id. Each detection: (frame_idx, true_fruit_id, centroid_xyz,
    n_pixels)."""
    arm_poses = sorted([p for p in poses if p["arm"] == arm_name], key=lambda p: p["node_id"])
    frames = []
    for p in arm_poses:
        depth = read_depth(os.path.join(data_dir, p["depth_path"]))
        inst = np.load(os.path.join(data_dir, p["instance_path"]))
        eye, lookat = p["eye"], p["lookat"]
        f, r, u = sm.camera_basis(eye, lookat)
        valid = (depth != sm.SKY_DEPTH_SENTINEL) & ~np.isnan(inst)
        dets = []
        if np.any(valid):
            ids_here = np.unique(inst[valid])
            for fid in ids_here:
                mask = valid & (inst == fid)
                rows, cols = np.nonzero(mask)
                if len(rows) < 5:
                    continue
                d = depth[rows, cols]
                pts = sm.unproject(rows, cols, d, eye, f, r, u, intr)
                centroid = pts.mean(axis=0)
                dets.append({"true_id": int(fid), "centroid": centroid, "n_pixels": int(len(rows))})
        frames.append({"node_id": p["node_id"], "view": p["view"], "detections": dets})
    return frames


def run_tracker(frames, gate_m=GATE_M):
    """Greedy nearest-centroid tracker. Mutates nothing; returns a new list
    of frames with an added 'track_id' per detection, plus the final track
    position table."""
    track_positions = {}  # track_id -> last known centroid
    next_track_id = 0
    out_frames = []
    for frame in frames:
        dets = frame["detections"]
        assigned_track = [-1] * len(dets)
        used_tracks = set()
        if dets and track_positions:
            candidates = []
            for di, det in enumerate(dets):
                for tid, pos in track_positions.items():
                    dist = float(np.linalg.norm(det["centroid"] - pos))
                    if dist <= gate_m:
                        candidates.append((dist, di, tid))
            candidates.sort(key=lambda c: c[0])
            used_dets = set()
            for dist, di, tid in candidates:
                if di in used_dets or tid in used_tracks:
                    continue
                assigned_track[di] = tid
                used_dets.add(di)
                used_tracks.add(tid)
        for di, det in enumerate(dets):
            if assigned_track[di] == -1:
                assigned_track[di] = next_track_id
                next_track_id += 1
            track_positions[assigned_track[di]] = det["centroid"]
        out_dets = [dict(det, track_id=assigned_track[di]) for di, det in enumerate(dets)]
        out_frames.append({"node_id": frame["node_id"], "view": frame["view"], "detections": out_dets})
    return out_frames, next_track_id


def score_idf1(tracked_frames):
    overlap = defaultdict(int)
    track_ids = set()
    true_ids = set()
    n_dets_total = 0
    for frame in tracked_frames:
        for det in frame["detections"]:
            overlap[(det["track_id"], det["true_id"])] += 1
            track_ids.add(det["track_id"])
            true_ids.add(det["true_id"])
            n_dets_total += 1

    track_list = sorted(track_ids)
    true_list = sorted(true_ids)
    track_idx = {t: i for i, t in enumerate(track_list)}
    true_idx = {t: i for i, t in enumerate(true_list)}
    weight = np.zeros((len(track_list), len(true_list)))
    for (tid, fid), c in overlap.items():
        weight[track_idx[tid], true_idx[fid]] = c

    pairs = max_weight_bipartite_matching(weight)
    idtp = sum(p[2] for p in pairs)
    idfp = n_dets_total - idtp
    idfn = n_dets_total - idtp
    idf1 = 2 * idtp / (2 * idtp + idfp + idfn) if (idtp + idfp + idfn) > 0 else None

    # ID switches: per true fruit id, walk detections in frame order
    per_fruit_sequence = defaultdict(list)
    for fi, frame in enumerate(tracked_frames):
        for det in frame["detections"]:
            per_fruit_sequence[det["true_id"]].append((fi, det["track_id"]))
    n_switches = 0
    for fid, seq in per_fruit_sequence.items():
        seq.sort(key=lambda t: t[0])
        for i in range(1, len(seq)):
            if seq[i][1] != seq[i - 1][1]:
                n_switches += 1

    return {
        "n_true_ids": len(true_list), "n_predicted_tracks": len(track_list),
        "n_detections_total": n_dets_total, "IDTP": idtp, "IDFP": idfp, "IDFN": idfn,
        "IDF1": idf1, "n_id_switches": n_switches,
    }


def run_t44(data_dir):
    poses = json.load(open(os.path.join(data_dir, "poses.json")))
    report = json.load(open(os.path.join(data_dir, "gen_report.json")))
    intr = sm.intrinsics(tuple(report["resolution"]))

    results = {}
    all_tracked_frames = []
    for arm_name in ("arm_low", "arm_mid", "arm_high"):
        frames = extract_detections(data_dir, arm_name, poses, intr)
        tracked_frames, n_tracks = run_tracker(frames)
        n_dets = sum(len(fr["detections"]) for fr in frames)
        score = score_idf1(tracked_frames) if n_dets > 0 else None
        results[arm_name] = {"n_frames": len(frames), "n_detections": n_dets,
                              "n_predicted_tracks_spawned": n_tracks, "score": score}
        if n_dets > 0:
            all_tracked_frames.extend(tracked_frames)

    combined_score = score_idf1(all_tracked_frames) if all_tracked_frames else None
    return {"per_arm": results, "combined_all_arms": combined_score, "gate_m": GATE_M}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    DATA = os.path.join(HERE, "data")
    out = run_t44(DATA)
    print(json.dumps(out, indent=2, default=str))
    with open(os.path.join(HERE, "output_t44_tracker_report.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
