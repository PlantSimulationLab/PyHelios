#!/usr/bin/env bash
# Round 2, phase D: the combined "both fixes" run. Concurrent with phases B and C.
#
#   bash yogesh_dev/world_model/run_r2d.sh <run_r2_pid>
#
# r2_best = r2_main + class-weighted semantic cross-entropy + L1 depth loss.
#
# The two changes target the two things Round 2's success criteria ask for, and
# each was chosen from a measurement rather than from a hunch:
#
#   mIoU   R2-C found the Round 1 model never predicts fruit, petiole or peduncle
#          at all, so four of seven per-class IoUs are exactly 0 and mIoU is
#          pinned at 0.266. Class weights address that directly.
#   depth  R2-C measured the reconstruction carrying 11% of the ground truth's
#          gradient energy. An MSE decoder's optimum IS the conditional mean, and
#          a blurred depth map is exactly what loses to a sharp copy-last frame.
#          L1's optimum is the conditional median, and it is also the loss that
#          matches the reported metric (MAE), which MSE-in-symlog does not.
#
# Isolation: r2_sem (phase C) is class weights ALONE, so r2_best vs r2_sem
# isolates the L1 depth change and r2_sem vs r2_main isolates the class weights.
# Both r2_sem's and r2_best's validation-reconstruction numbers are on different
# scales from r2_main's -- the comparison that counts is the held-out eval.

set -u
cd /home/yogesh/PyHelios

WAIT_PID="${1:-0}"
GSPLAT=/home/yogesh/anaconda3/envs/gsplat/bin/python
WM=yogesh_dev/world_model
DATA=$WM/output/dataset
OUT=$WM/output/r2
LOG=$OUT/r2d_pipeline.log
mkdir -p "$OUT"
export PATH=/home/yogesh/anaconda3/envs/gsplat/bin:$PATH

say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

if [ "$WAIT_PID" != "0" ]; then
  say "waiting for run_r2.sh (pid $WAIT_PID)"
  while ps -p "$WAIT_PID" >/dev/null 2>&1; do sleep 60; done
  say "run_r2.sh exited"
fi

say "=== R2-G: class-weighted semantics + L1 depth ==="
$GSPLAT -m yogesh_dev.world_model.train --data "$DATA" --steps 30000 \
  --image-size 64 --batch-size 24 --seq-len 32 --growth-fraction 0.25 \
  --sem-class-weights auto --depth-loss l1 --cache-size 1200 \
  --log-every 500 --val-every 1000 --ckpt-every 2000 --tag r2_best \
  >> "$WM/output/train_r2_best_stdout.txt" 2>&1
say "r2_best exit=$?"

say "=== W6 evaluation of the combined model ==="
$GSPLAT -m yogesh_dev.world_model.evaluate \
  --ckpt "$WM/output/train/r2_best/ckpt_best.pt" \
  --noaction-ckpt "$WM/output/train/r2_noaction/ckpt_best.pt" \
  --data "$DATA" --split test --context 5 --seq-len 32 \
  --batch-size 8 --n-batches 24 --out "$WM/output/r2_w6_best" \
  >> "$OUT/r2_w6_best_stdout.txt" 2>&1
say "evaluation exit=$?"

say "=== R2-C: reconstruction floor / per-class IoU / sharpness for the combined model ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_recon_floor \
  --ckpt "$WM/output/train/r2_best/ckpt_best.pt" --tag r2_best --split test \
  --name r2_recon_floor_best >> "$OUT/r2_recon_floor_best_stdout.txt" 2>&1
say "recon floor exit=$?"

say "ROUND 2 PHASE D DONE"
