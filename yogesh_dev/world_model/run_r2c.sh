#!/usr/bin/env bash
# Round 2, phase C: the CLASS-BALANCE experiment. Runs concurrently with phase B.
#
#   bash yogesh_dev/world_model/run_r2c.sh <run_r2_pid>
#
# Why this run exists. R2-C's per-class breakdown of the Round 1 model's
# teacher-forced reconstruction on held-out orchards:
#
#   class      IoU     gt pixels   predicted pixels
#   ground    0.857      42.37%        46.80%
#   fruit     0.000       2.04%         0.00%
#   leaf      0.374      19.62%        18.80%
#   shoot     0.013       6.33%         0.19%
#   petiole   0.000       0.22%         0.00%
#   peduncle  0.000       0.03%         0.00%
#   sky       0.618      29.39%        34.20%
#
# (0.857 + 0 + 0.374 + 0.013 + 0 + 0 + 0.618) / 7 = 0.266 -- exactly the "flat
# mIoU ~0.26" Round 1 reported. It is not a plateau the model is stuck at, it is
# class collapse: four of seven classes are never predicted at all, and the
# unweighted cross-entropy has no reason to predict them when the rarest is 0.03%
# of pixels. Copy-last-frame scores 0.328 purely because it reproduces every
# class for free.
#
# So this run is identical to r2_main except for sqrt-inverse-frequency class
# weights on the semantic cross-entropy. Note that this changes the SCALE of the
# semantic loss term, so r2_sem's validation-reconstruction number is not
# comparable with r2_main's -- the comparison that matters is the held-out mIoU
# from evaluate.py, which is unweighted.

set -u
cd /home/yogesh/PyHelios

WAIT_PID="${1:-0}"
GSPLAT=/home/yogesh/anaconda3/envs/gsplat/bin/python
WM=yogesh_dev/world_model
DATA=$WM/output/dataset
OUT=$WM/output/r2
LOG=$OUT/r2c_pipeline.log
mkdir -p "$OUT"
export PATH=/home/yogesh/anaconda3/envs/gsplat/bin:$PATH

say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

if [ "$WAIT_PID" != "0" ]; then
  say "waiting for run_r2.sh (pid $WAIT_PID)"
  while ps -p "$WAIT_PID" >/dev/null 2>&1; do sleep 60; done
  say "run_r2.sh exited"
fi

say "=== R2-F: class-balanced semantic loss ==="
$GSPLAT -m yogesh_dev.world_model.train --data "$DATA" --steps 30000 \
  --image-size 64 --batch-size 24 --seq-len 32 --growth-fraction 0.25 \
  --sem-class-weights auto --cache-size 1200 \
  --log-every 500 --val-every 1000 --ckpt-every 2000 --tag r2_sem \
  >> "$WM/output/train_r2_sem_stdout.txt" 2>&1
say "r2_sem exit=$?"

say "=== W6 evaluation of the class-balanced model ==="
$GSPLAT -m yogesh_dev.world_model.evaluate \
  --ckpt "$WM/output/train/r2_sem/ckpt_best.pt" \
  --noaction-ckpt "$WM/output/train/r2_noaction/ckpt_best.pt" \
  --data "$DATA" --split test --context 5 --seq-len 32 \
  --batch-size 8 --n-batches 24 --out "$WM/output/r2_w6_sem" \
  >> "$OUT/r2_w6_sem_stdout.txt" 2>&1
say "evaluation exit=$?"

say "=== R2-C: reconstruction floor / per-class IoU for the class-balanced model ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_recon_floor \
  --ckpt "$WM/output/train/r2_sem/ckpt_best.pt" --tag r2_sem --split test \
  --name r2_recon_floor_sem >> "$OUT/r2_recon_floor_sem_stdout.txt" 2>&1
say "recon floor exit=$?"

say "ROUND 2 PHASE C DONE"
