#!/usr/bin/env bash
# Round 2, phase E: the INFORMATION-BOTTLENECK run.
#
#   bash yogesh_dev/world_model/run_r2e.sh <run_r2c_pid>
#
# Chained on phase C rather than on phase A so that the number of concurrent
# training jobs stays at three: this run starts as r2_sem finishes.
#
# Why this run exists. R2-C established that depth is a SHARPNESS problem -- a
# perfectly correct depth map blurred to the model's measured sharpness (0.115 of
# the ground truth's gradient energy) still scores ~0.94 m against copy-last's
# 0.657 m. So the question becomes: why is the output blurred?
#
# The training logs answer it. Round 1 ran free_bits 1.0 with kl_dyn 0.5 /
# kl_rep 0.1, and the KL settled at 1.371 nats and stayed there
# (val 1.58 -> 1.64 over the last 3k steps). The latent is 32 categorical
# variables of 32 classes = 160 bits per frame of capacity, and the posterior is
# diverging from the prior by 1.37 nats = 2.0 bits. The encoder is very nearly
# bypassed: almost nothing about the specific canopy reaches the decoder, so the
# decoder renders the pose-conditioned average orchard -- which is exactly what
# Round 1 observed qualitatively ("global layout, essentially no canopy
# structure") and what a blur is.
#
# This run relaxes the bottleneck: free-bits 1.0 -> 6.0 (the model may transmit
# up to 6 nats per step at no cost) and the KL weights 0.5/0.1 -> 0.2/0.04.
# Both changes push the same way on the same hypothesis, so this is one
# intervention with two knobs, not two isolated ablations -- stated plainly
# rather than dressed up as a controlled pair. Everything else is identical to
# r2_main.

set -u
cd /home/yogesh/PyHelios

WAIT_PID="${1:-0}"
GSPLAT=/home/yogesh/anaconda3/envs/gsplat/bin/python
WM=yogesh_dev/world_model
DATA=$WM/output/dataset
OUT=$WM/output/r2
LOG=$OUT/r2e_pipeline.log
mkdir -p "$OUT"
export PATH=/home/yogesh/anaconda3/envs/gsplat/bin:$PATH

say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

if [ "$WAIT_PID" != "0" ]; then
  say "waiting for phase C (pid $WAIT_PID)"
  while ps -p "$WAIT_PID" >/dev/null 2>&1; do sleep 60; done
  say "phase C exited"
fi

say "=== R2-I: relaxed information bottleneck (free-bits 6, kl 0.2/0.04) ==="
$GSPLAT -m yogesh_dev.world_model.train --data "$DATA" --steps 30000 \
  --image-size 64 --batch-size 24 --seq-len 32 --growth-fraction 0.25 \
  --free-bits 6.0 --kl-dyn 0.2 --kl-rep 0.04 --cache-size 1200 \
  --log-every 500 --val-every 1000 --ckpt-every 2000 --tag r2_kl \
  >> "$WM/output/train_r2_kl_stdout.txt" 2>&1
say "r2_kl exit=$?"

say "=== W6 evaluation of the relaxed-bottleneck model ==="
$GSPLAT -m yogesh_dev.world_model.evaluate \
  --ckpt "$WM/output/train/r2_kl/ckpt_best.pt" \
  --noaction-ckpt "$WM/output/train/r2_noaction/ckpt_best.pt" \
  --data "$DATA" --split test --context 5 --seq-len 32 \
  --batch-size 8 --n-batches 24 --out "$WM/output/r2_w6_kl" \
  >> "$OUT/r2_w6_kl_stdout.txt" 2>&1
say "evaluation exit=$?"

say "=== R2-C: reconstruction floor / sharpness for the relaxed-bottleneck model ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_recon_floor \
  --ckpt "$WM/output/train/r2_kl/ckpt_best.pt" --tag r2_kl --split test \
  --name r2_recon_floor_kl >> "$OUT/r2_recon_floor_kl_stdout.txt" 2>&1
say "recon floor exit=$?"

say "ROUND 2 PHASE E DONE"
