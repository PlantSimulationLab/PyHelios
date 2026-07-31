"""
Dataset loader for the world model. Runs in the `gsplat` env -- **never imports
pyhelios**. Files on disk are the only interface between the two conda envs.

Reads the shards written by `generate.py` and serves fixed-length sequence
batches. Episodes are memory-mapped lazily and cached, because a full 128-step
128x128 episode is ~30 MB uncompressed and holding the whole dataset in RAM is
neither necessary nor kind to the machine.
"""

import json
import os

import numpy as np

SEMANTIC_SKY = 6
N_SEMANTIC_CLASSES = 7


class EpisodeStore:
    """Lazily-decompressed npz episodes with a bounded LRU cache."""

    def __init__(self, root, records, cache_size=32, image_size=None):
        self.root = root
        self.records = records
        self.cache_size = cache_size
        self.image_size = image_size
        self._cache = {}
        self._order = []

    def __len__(self):
        return len(self.records)

    def _resize(self, arr, mode):
        """Nearest-neighbour downscale by an integer factor. Nearest is used for
        every modality on purpose: bilinear on a semantic map invents classes,
        and bilinear on depth invents surfaces that straddle an occlusion edge."""
        if self.image_size is None:
            return arr
        s = arr.shape[1]
        if s == self.image_size:
            return arr
        if s % self.image_size != 0:
            raise ValueError(f"image_size {self.image_size} must divide stored size {s}")
        k = s // self.image_size
        return arr[:, ::k, ::k] if arr.ndim == 3 else arr[:, ::k, ::k, :]

    def load(self, idx):
        if idx in self._cache:
            return self._cache[idx]
        rec = self.records[idx]
        with np.load(os.path.join(self.root, rec["path"]), allow_pickle=False) as z:
            ep = {
                "rgb": self._resize(z["rgb"], "nearest"),
                "depth": self._resize(z["depth"], "nearest").astype(np.float32),
                "semantic": self._resize(z["semantic"], "nearest"),
                "a_view": z["a_view"],
                "a_grow": z["a_grow"],
                "fruit_vis": z["fruit_vis"],
                "pose": z["pose"],
                "state": z["state"],
            }
        self._cache[idx] = ep
        self._order.append(idx)
        while len(self._order) > self.cache_size:
            self._cache.pop(self._order.pop(0), None)
        return ep


class SequenceSampler:
    """Samples fixed-length windows from episodes.

    `growth_fraction` controls how often a batch element comes from a growth
    episode. The two channels are wildly imbalanced by construction (a growth
    episode is 8 frames, a view episode is 128), so leaving it to uniform
    sampling over frames would make the growth channel ~1% of the data. This is
    the loss-weighting mitigation the plan's risk table calls for, applied at the
    sampling level, and the realised ratio is reported rather than assumed.
    """

    def __init__(self, root, split="train", seq_len=32, image_size=None,
                 growth_fraction=0.25, cache_size=32, seed=0, manifest=None):
        self.root = root
        if manifest is None:
            with open(os.path.join(root, "manifest.json")) as f:
                manifest = json.load(f)
        self.manifest = manifest
        eps = [e for e in manifest["episodes"] if e["split"] == split]
        self.view_records = [e for e in eps if e["episode_type"] == "view"]
        self.growth_records = [e for e in eps if e["episode_type"] == "growth"]
        self.view_store = EpisodeStore(root, self.view_records, cache_size, image_size)
        self.growth_store = EpisodeStore(root, self.growth_records, cache_size, image_size)
        self.seq_len = seq_len
        self.growth_fraction = growth_fraction if self.growth_records else 0.0
        self.rng = np.random.default_rng(seed)
        self.image_size = image_size
        self.split = split
        self._n_growth_drawn = 0
        self._n_drawn = 0

    def n_frames(self):
        return sum(e["n_steps"] for e in self.view_records + self.growth_records)

    def _window(self, ep, is_growth):
        T = ep["rgb"].shape[0]
        L = min(self.seq_len, T)
        t0 = int(self.rng.integers(0, T - L + 1)) if T > L else 0
        sl = slice(t0, t0 + L)
        a_view = ep["a_view"][sl]
        a_grow = ep["a_grow"][sl]
        # Action vector = 4 view dims + 1 growth dim (days/10, so both channels
        # sit at a comparable scale; view deltas are ~0.1 m and growth steps are
        # 5-10 days).
        action = np.concatenate([a_view, a_grow / 10.0], axis=1).astype(np.float32)
        out = {"rgb": ep["rgb"][sl], "depth": ep["depth"][sl],
               "semantic": ep["semantic"][sl], "action": action,
               "fruit_vis": ep["fruit_vis"][sl], "is_growth": is_growth}
        if L < self.seq_len:  # pad by repeating the last frame with zero actions
            pad = self.seq_len - L
            for k in ("rgb", "depth", "semantic", "fruit_vis"):
                out[k] = np.concatenate([out[k], np.repeat(out[k][-1:], pad, axis=0)], axis=0)
            out["action"] = np.concatenate(
                [out["action"], np.zeros((pad, out["action"].shape[1]), np.float32)], axis=0)
            out["pad_mask"] = np.concatenate([np.ones(L, bool), np.zeros(pad, bool)])
        else:
            out["pad_mask"] = np.ones(self.seq_len, bool)
        return out

    def sample_batch(self, batch_size):
        items = []
        for _ in range(batch_size):
            use_growth = (self.growth_records
                          and self.rng.random() < self.growth_fraction)
            self._n_drawn += 1
            if use_growth:
                self._n_growth_drawn += 1
                i = int(self.rng.integers(0, len(self.growth_records)))
                items.append(self._window(self.growth_store.load(i), True))
            else:
                i = int(self.rng.integers(0, len(self.view_records)))
                items.append(self._window(self.view_store.load(i), False))
        return {
            "rgb": np.stack([x["rgb"] for x in items]),
            "depth": np.stack([x["depth"] for x in items]),
            "semantic": np.stack([x["semantic"] for x in items]),
            "action": np.stack([x["action"] for x in items]),
            "fruit_vis": np.stack([x["fruit_vis"] for x in items]),
            "pad_mask": np.stack([x["pad_mask"] for x in items]),
            "is_growth": np.array([x["is_growth"] for x in items]),
        }

    def iter_episodes(self, episode_type="view", limit=None, seq_len=None):
        """Deterministic full-episode iteration, for evaluation."""
        store = self.view_store if episode_type == "view" else self.growth_store
        recs = self.view_records if episode_type == "view" else self.growth_records
        n = len(recs) if limit is None else min(limit, len(recs))
        L = seq_len
        for i in range(n):
            ep = store.load(i)
            T = ep["rgb"].shape[0] if L is None else min(L, ep["rgb"].shape[0])
            action = np.concatenate([ep["a_view"][:T], ep["a_grow"][:T] / 10.0],
                                    axis=1).astype(np.float32)
            yield recs[i], {"rgb": ep["rgb"][:T][None], "depth": ep["depth"][:T][None],
                            "semantic": ep["semantic"][:T][None], "action": action[None],
                            "fruit_vis": ep["fruit_vis"][:T][None]}

    def prefetch(self, batch_size, queue_size=4, n_workers=1):
        """Background-thread batch producer.

        npz decompression is the real bottleneck once the model step is ~0.03 s
        (measured), so batches are built on a worker thread while the GPU is busy.
        numpy releases the GIL inside decompression, so a thread (not a process)
        is enough and avoids copying arrays across a process boundary.

        `n_workers` defaults to 1 **on purpose**: the sampler's RNG and the
        EpisodeStore LRU cache are not thread-safe, so more than one producer
        would race on them and (worse) silently break reproducibility. One
        producer already overlaps decompression with the GPU step, which is the
        whole point.
        """
        import queue
        import threading
        q = queue.Queue(maxsize=queue_size)
        stop = threading.Event()

        def worker():
            while not stop.is_set():
                try:
                    q.put(self.sample_batch(batch_size), timeout=1.0)
                except Exception:
                    continue

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(n_workers)]
        for t in threads:
            t.start()

        class _Iter:
            def __iter__(self_):
                return self_

            def __next__(self_):
                return q.get()

            def close(self_):
                stop.set()

        return _Iter()

    def stats(self):
        return {"split": self.split, "n_view_episodes": len(self.view_records),
                "n_growth_episodes": len(self.growth_records),
                "n_frames": self.n_frames(),
                "growth_fraction_requested": self.growth_fraction,
                "growth_fraction_realised": (self._n_growth_drawn / self._n_drawn
                                             if self._n_drawn else None)}
