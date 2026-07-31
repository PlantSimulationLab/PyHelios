"""
W4/W5 -- training the RSSM world model. Runs in the `gsplat` env.

    /home/yogesh/anaconda3/envs/gsplat/bin/python -m yogesh_dev.world_model.train \
        --data yogesh_dev/world_model/output/dataset --steps 20000

Modes:
  --overfit-one     W4 acceptance: train on a SINGLE trajectory and check the
                    reconstruction loss goes to near zero. If it cannot, the model
                    is wrong and there is no point running the full training.
  (default)         W5: full training with validation, checkpointing, resumability.

Checkpoints are written every `--ckpt-every` steps to `<out>/ckpt.pt` (plus
`ckpt_best.pt` on validation improvement) and `--resume` picks up optimiser state,
step count and RNG so an interrupted run continues rather than restarts.
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from yogesh_dev.world_model.rssm import WorldModel, count_parameters
from yogesh_dev.world_model.data import SequenceSampler


def to_device_batch(batch, device, zero_actions=False):
    out = {k: (torch.from_numpy(v) if isinstance(v, np.ndarray) else v) for k, v in batch.items()}
    if zero_actions and "action" in out:
        out["action"] = torch.zeros_like(out["action"])
    return out


def evaluate(model, sampler, device, n_batches, batch_size, zero_actions=False):
    model.eval()
    accum = {}
    with torch.no_grad():
        for _ in range(n_batches):
            b = sampler.sample_batch(batch_size)
            data = model.preprocess(to_device_batch(b, device, zero_actions), device)
            _, m, _, _ = model.loss(data)
            for k, v in m.items():
                accum[k] = accum.get(k, 0.0) + float(v)
    model.train()
    return {k: v / n_batches for k, v in accum.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "output", "dataset"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "output", "train"))
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--seq-len", type=int, default=32)
    ap.add_argument("--image-size", type=int, default=64)
    ap.add_argument("--base-channels", type=int, default=32)
    ap.add_argument("--deter", type=int, default=512)
    ap.add_argument("--stoch", type=int, default=32)
    ap.add_argument("--classes", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--adam-eps", type=float, default=1e-5,
                    help="Adam epsilon. 1e-8 is NOT safe here: the W4 overfit run reached a "
                         "reconstruction loss of ~8e-4 and then diverged in its last 500 steps "
                         "(rgb 0.00077 -> 0.01345, depth 0.00023 -> 0.03768). Once gradients "
                         "are that small, eps dominates the Adam denominator and the effective "
                         "step size explodes. 1e-5 is the DreamerV2/V3 value.")
    ap.add_argument("--grad-clip", type=float, default=100.0)
    ap.add_argument("--growth-fraction", type=float, default=0.25)
    ap.add_argument("--free-bits", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--log-every", type=int, default=50)
    ap.add_argument("--val-every", type=int, default=500)
    ap.add_argument("--val-batches", type=int, default=8)
    ap.add_argument("--ckpt-every", type=int, default=500)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--overfit-one", action="store_true",
                    help="W4 acceptance: one fixed trajectory, no validation")
    ap.add_argument("--amp", action="store_true", help="bfloat16 autocast")
    ap.add_argument("--cache-size", type=int, default=64)
    ap.add_argument("--prefetch", action="store_true", default=True)
    ap.add_argument("--no-prefetch", dest="prefetch", action="store_false")
    ap.add_argument("--zero-actions", action="store_true",
                    help="W6 no-action ablation: train with all actions set to zero. "
                         "A model trained this way CANNOT use actions, so it is the "
                         "control that proves the full model does.")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    out = os.path.join(args.out, args.tag) if args.tag else args.out
    os.makedirs(out, exist_ok=True)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    logf = open(os.path.join(out, "train_log.txt"), "a")

    def log(m):
        print(m, flush=True)
        logf.write(str(m) + "\n")
        logf.flush()

    log("=" * 78)
    log(f"train.py {time.strftime('%Y-%m-%d %H:%M:%S')} device={device}")
    log(f"args: {vars(args)}")

    train_sampler = SequenceSampler(args.data, "train", args.seq_len, args.image_size,
                                    args.growth_fraction, cache_size=args.cache_size,
                                    seed=args.seed)
    log(f"train data: {train_sampler.stats()}")
    val_sampler = None
    if not args.overfit_one:
        val_sampler = SequenceSampler(args.data, "val", args.seq_len, args.image_size,
                                      args.growth_fraction, cache_size=max(8, args.cache_size // 4),
                                      seed=args.seed + 1)
        log(f"val data: {val_sampler.stats()}")

    # -- W4: overfit a single trajectory ------------------------------------
    fixed_batch = None
    if args.overfit_one:
        rec, ep = next(train_sampler.iter_episodes("view", limit=1, seq_len=args.seq_len))
        log(f"overfitting single episode: {rec['path']} ({rec['family']}, "
            f"seed {rec['orchard_seed']}, stage {rec.get('stage_index')})")
        fixed_batch = {"rgb": ep["rgb"], "depth": ep["depth"], "semantic": ep["semantic"],
                       "action": ep["action"], "fruit_vis": ep["fruit_vis"]}

    model = WorldModel(action_dim=5, image_size=args.image_size, base=args.base_channels,
                       deter=args.deter, stoch=args.stoch, classes=args.classes,
                       free_bits=args.free_bits).to(device)
    log(f"model parameters: {count_parameters(model):,}")
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, eps=args.adam_eps)

    start_step, best_val = 0, float("inf")
    ckpt_path = os.path.join(out, "ckpt.pt")
    if args.resume and os.path.isfile(ckpt_path):
        ck = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        start_step = ck["step"]
        best_val = ck.get("best_val", float("inf"))
        log(f"resumed from step {start_step} (best_val={best_val:.5f})")

    history_path = os.path.join(out, "history.jsonl")
    hist = open(history_path, "a")
    t0 = time.time()
    running = {}
    amp_ctx = (torch.autocast("cuda", dtype=torch.bfloat16) if (args.amp and device == "cuda")
               else torch.autocast("cpu", enabled=False))

    producer = None
    if fixed_batch is None and args.prefetch:
        producer = train_sampler.prefetch(args.batch_size)

    for step in range(start_step, args.steps):
        if fixed_batch is not None:
            batch = fixed_batch
        elif producer is not None:
            batch = next(producer)
        else:
            batch = train_sampler.sample_batch(args.batch_size)
        data = model.preprocess(to_device_batch(batch, device, args.zero_actions), device)
        with amp_ctx:
            total, metrics, _, _ = model.loss(data)
        opt.zero_grad(set_to_none=True)
        total.backward()
        gn = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
        opt.step()

        for k, v in metrics.items():
            running[k] = running.get(k, 0.0) + float(v)
        running["grad_norm"] = running.get("grad_norm", 0.0) + float(gn)

        if (step + 1) % args.log_every == 0:
            n = args.log_every
            row = {"step": step + 1, "split": "train",
                   **{k: v / n for k, v in running.items()},
                   "elapsed_s": time.time() - t0,
                   "steps_per_s": (step + 1 - start_step) / max(1e-9, time.time() - t0)}
            hist.write(json.dumps(row) + "\n"); hist.flush()
            log(f"  step {step+1:6d}  loss={row['loss']:.4f}  rgb={row['rgb']:.5f}  "
                f"depth={row['depth']:.5f}  sem={row['semantic']:.4f}  "
                f"fruit={row['fruit']:.4f}  kl_dyn={row['kl_dyn']:.3f}  "
                f"kl_rep={row['kl_rep']:.3f}  |g|={row['grad_norm']:.1f}  "
                f"{row['steps_per_s']:.2f} it/s")
            running = {}

        if val_sampler is not None and (step + 1) % args.val_every == 0:
            vm = evaluate(model, val_sampler, device, args.val_batches, args.batch_size,
                          args.zero_actions)
            row = {"step": step + 1, "split": "val", **vm, "elapsed_s": time.time() - t0}
            hist.write(json.dumps(row) + "\n"); hist.flush()
            log(f"  VAL step {step+1}: " + "  ".join(f"{k}={v:.5f}" for k, v in vm.items()))
            # Select on validation RECONSTRUCTION, not on total loss. The KL term
            # rises steadily as the model uses more latent capacity, so total loss
            # can go UP while every reconstruction term goes DOWN -- a first run
            # selected step 5000 as "best" when validation reconstruction actually
            # kept improving to step 14000. Checkpoint selection must track what
            # the model is being evaluated on.
            recon = float(vm["rgb"] + vm["depth"] + vm["semantic"] + vm["fruit"])
            row["val_recon"] = recon
            if recon < best_val:
                best_val = recon
                torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                            "step": step + 1, "best_val": best_val, "args": vars(args)},
                           os.path.join(out, "ckpt_best.pt"))

        if val_sampler is None and (step + 1) % args.log_every == 0:
            # No validation split (overfit mode): track the best TRAIN loss instead, so a
            # late divergence cannot destroy the run's result. See --adam-eps.
            cur = row["loss"]
            if cur < best_val:
                best_val = cur
                torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                            "step": step + 1, "best_val": best_val, "args": vars(args)},
                           os.path.join(out, "ckpt_best.pt"))

        if (step + 1) % args.ckpt_every == 0:
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                        "step": step + 1, "best_val": best_val, "args": vars(args)}, ckpt_path)

    if producer is not None:
        producer.close()
    torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                "step": args.steps, "best_val": best_val, "args": vars(args)}, ckpt_path)
    log(f"done in {time.time()-t0:.0f}s; final ckpt at {ckpt_path}")
    log(f"train sampler stats: {train_sampler.stats()}")
    hist.close(); logf.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            sys.path.insert(0, "/home/yogesh/PyHelios")
            from notify_slack import notify_slack
            notify_slack(f"World model training FAILED: {traceback.format_exc()[-1200:]}")
        except Exception:
            pass
        raise
