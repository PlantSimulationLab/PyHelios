#!/usr/bin/env bash
# Round 2, phase B: the CAPACITY experiment, chained after run_r2.sh.
#
#   bash yogesh_dev/world_model/run_r2b.sh <run_r2_pid>
#
# Why this run exists. R2-C (run_r2_recon_floor.py) measured the Round 1 model's
# TEACHER-FORCED posterior reconstruction -- encode a real held-out frame, decode
# it straight back, no dynamics involved:
#
#                       PSNR    depth MAE   mIoU
#   posterior recon    18.10 dB   1.012 m   0.266      <- representation ceiling
#   open-loop t+1      18.03 dB   1.040 m   0.264
#   copy-last t+1      16.57 dB   0.650 m   0.328      <- the baseline to beat
#
# 97% of the depth error at t+1 is already present in the reconstruction; one step
# of dynamics adds 0.028 m. And on TRAIN orchards the same model reconstructs at
# 0.997 m / 0.294 mIoU -- barely better than on held-out orchards. So the model
# cannot render a sharp orchard even from a frame it is looking at, on data it was
# trained on. That is a capacity limit, not a data-diversity limit, and no number
# of extra orchards can move it.
#
# This run therefore scales the model instead of the data, holding everything else
# identical to r2_main so the comparison is controlled:
#   base channels 32 -> 64, deter 512 -> 1024, stoch/classes 32x32 -> 48x48
# (32x32 categorical latents carry 160 bits per frame; 48x48 carries 268.)
#
# It runs ALONE rather than concurrently: it is ~4x the parameters and would slow
# the three Round 2 runs it is being compared against.

set -u
cd /home/yogesh/PyHelios

WAIT_PID="${1:-0}"
GSPLAT=/home/yogesh/anaconda3/envs/gsplat/bin/python
WM=yogesh_dev/world_model
DATA=$WM/output/dataset
OUT=$WM/output/r2
LOG=$OUT/r2b_pipeline.log
mkdir -p "$OUT"
export PATH=/home/yogesh/anaconda3/envs/gsplat/bin:$PATH

say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

if [ "$WAIT_PID" != "0" ]; then
  say "waiting for run_r2.sh (pid $WAIT_PID)"
  while ps -p "$WAIT_PID" >/dev/null 2>&1; do sleep 60; done
  say "run_r2.sh exited"
fi

say "=== R2-E: capacity run (base 64, deter 1024, stoch 48x48) ==="
$GSPLAT -m yogesh_dev.world_model.train --data "$DATA" --steps 30000 \
  --image-size 64 --batch-size 24 --seq-len 32 --growth-fraction 0.25 \
  --base-channels 64 --deter 1024 --stoch 48 --classes 48 \
  --cache-size 1200 --log-every 500 --val-every 1000 --ckpt-every 2000 --tag r2_big \
  >> "$WM/output/train_r2_big_stdout.txt" 2>&1
say "r2_big exit=$?"

say "=== R2-C: reconstruction floor, every model, held-out and train splits ==="
CKPTS="--ckpt $WM/output/train/main2/ckpt_best.pt    --tag r1_main \
       --ckpt $WM/output/train/r2_main/ckpt_best.pt  --tag r2_main \
       --ckpt $WM/output/train/r2_growth/ckpt_best.pt --tag r2_growth \
       --ckpt $WM/output/train/r2_big/ckpt_best.pt   --tag r2_big"
$GSPLAT -m yogesh_dev.world_model.run_r2_recon_floor $CKPTS --split test \
  --name r2_recon_floor_test >> "$OUT/r2_recon_floor_stdout.txt" 2>&1
say "recon floor (test) exit=$?"
$GSPLAT -m yogesh_dev.world_model.run_r2_recon_floor $CKPTS --split train \
  --name r2_recon_floor_train >> "$OUT/r2_recon_floor_stdout.txt" 2>&1
say "recon floor (train) exit=$?"

say "=== W6 evaluation of the capacity model ==="
$GSPLAT -m yogesh_dev.world_model.evaluate \
  --ckpt "$WM/output/train/r2_big/ckpt_best.pt" \
  --noaction-ckpt "$WM/output/train/r2_noaction/ckpt_best.pt" \
  --data "$DATA" --split test --context 5 --seq-len 32 \
  --batch-size 8 --n-batches 24 --out "$WM/output/r2_w6_big" \
  >> "$OUT/r2_w6_big_stdout.txt" 2>&1
say "evaluation exit=$?"

say "=== curves including the capacity run ==="
$GSPLAT -m yogesh_dev.world_model.plot_curves \
  --tags r2_main,r2_noaction,r2_growth,r2_big --out "$OUT" --name r2_curves_all \
  --title "Round 2: 44 train orchards, three matched runs + a 4x-capacity run" \
  >> "$OUT/r2_curves_stdout.txt" 2>&1
say "curves exit=$?"

say "ROUND 2 PHASE B DONE"
