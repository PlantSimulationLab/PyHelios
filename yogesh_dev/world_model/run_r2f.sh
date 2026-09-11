#!/usr/bin/env bash
# Round 2, phase F: all three metric-directed fixes together.
#
# r2_final = r2_main + relaxed KL bottleneck + class-weighted semantics + L1 depth.
#
# Justified by the phase B-E results, each of which is a single-factor run on the
# same 44-orchard dataset with everything else identical:
#
#   posterior reconstruction on held-out orchards   depth    mIoU   RGB sharp  depth sharp
#     r2_main   (44 orchards, Round 1 recipe)       1.022 m  0.270    0.108      0.220
#     r2_big    (4x parameters, 268-bit latent)     1.009 m  0.271    0.112      0.224
#     r2_sem    (class-weighted semantics)          1.026 m  0.281    0.104      0.214
#     r2_best   (class weights + L1 depth)          0.881 m  0.284    0.105      0.281
#     r2_kl     (free-bits 6, KL 0.2/0.04)          0.887 m  0.287    0.127      0.260
#
# The three effects are mechanistically independent -- the KL relaxation raises how
# much scene information reaches the decoder (its KL runs at 6.3 nats against 1.37
# for every other run), L1 sharpens the depth head specifically, and the class
# weights restore the classes the unweighted cross-entropy drops -- so this run
# tests whether they compose. It runs alone; the GPU is otherwise idle by now.

set -u
cd /home/yogesh/PyHelios
GSPLAT=/home/yogesh/anaconda3/envs/gsplat/bin/python
WM=yogesh_dev/world_model
DATA=$WM/output/dataset
OUT=$WM/output/r2
LOG=$OUT/r2f_pipeline.log
export PATH=/home/yogesh/anaconda3/envs/gsplat/bin:$PATH
say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

say "=== R2-J: KL relaxation + class weights + L1 depth ==="
$GSPLAT -m yogesh_dev.world_model.train --data "$DATA" --steps 30000 \
  --image-size 64 --batch-size 24 --seq-len 32 --growth-fraction 0.25 \
  --free-bits 6.0 --kl-dyn 0.2 --kl-rep 0.04 \
  --sem-class-weights auto --depth-loss l1 --cache-size 1200 \
  --log-every 500 --val-every 1000 --ckpt-every 2000 --tag r2_final \
  >> "$WM/output/train_r2_final_stdout.txt" 2>&1
say "r2_final exit=$?"

say "=== W6 evaluation ==="
$GSPLAT -m yogesh_dev.world_model.evaluate \
  --ckpt "$WM/output/train/r2_final/ckpt_best.pt" \
  --noaction-ckpt "$WM/output/train/r2_noaction/ckpt_best.pt" \
  --data "$DATA" --split test --context 5 --seq-len 32 \
  --batch-size 8 --n-batches 24 --out "$WM/output/r2_w6_final" \
  >> "$OUT/r2_w6_final_stdout.txt" 2>&1
say "evaluation exit=$?"

say "=== R2-C: reconstruction floor, every Round 2 model, held-out ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_recon_floor \
  --ckpt "$WM/output/train/main2/ckpt_best.pt"     --tag r1_main \
  --ckpt "$WM/output/train/r2_main/ckpt_best.pt"   --tag r2_main \
  --ckpt "$WM/output/train/r2_big/ckpt_best.pt"    --tag r2_big \
  --ckpt "$WM/output/train/r2_sem/ckpt_best.pt"    --tag r2_sem \
  --ckpt "$WM/output/train/r2_best/ckpt_best.pt"   --tag r2_best \
  --ckpt "$WM/output/train/r2_kl/ckpt_best.pt"     --tag r2_kl \
  --ckpt "$WM/output/train/r2_final/ckpt_best.pt"  --tag r2_final \
  --split test --name r2_recon_floor_all >> "$OUT/r2_recon_floor_all_stdout.txt" 2>&1
say "recon floor exit=$?"

say "=== R2-D: growth counterfactual including the final model ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_growth_eval --data "$DATA" --split test \
  --ckpt "$WM/output/train/main2/ckpt_best.pt"     --tag r1_main \
  --ckpt "$WM/output/train/r2_main/ckpt_best.pt"   --tag r2_main \
  --ckpt "$WM/output/train/r2_growth/ckpt_best.pt" --tag r2_growth \
  --ckpt "$WM/output/train/r2_final/ckpt_best.pt"  --tag r2_final \
  >> "$OUT/r2_growth_eval_all_stdout.txt" 2>&1
say "growth counterfactual exit=$?"

say "=== curves ==="
$GSPLAT -m yogesh_dev.world_model.plot_curves \
  --tags r2_main,r2_big,r2_sem,r2_best,r2_kl,r2_final --out "$OUT" --name r2_curves_all \
  --title "Round 2: 44 train orchards -- data scaling, capacity, class balance, L1 depth, KL relaxation" \
  >> "$OUT/r2_curves_stdout.txt" 2>&1
say "curves exit=$?"
say "ROUND 2 PHASE F DONE"
