#!/usr/bin/env bash
# Round 2 pipeline: wait for the extended dataset, retrain, re-evaluate.
#
#   bash yogesh_dev/world_model/run_r2.sh <generator_pid>
#
# Three models are trained CONCURRENTLY on one RTX 5090. They are independent and
# none saturates the card alone, so this is roughly 3x cheaper in wall clock than
# running them in sequence:
#
#   r2_main      identical hyperparameters to Round 1's `main2`, so the only
#                difference from the Round 1 baseline is the number of orchards
#                (12 -> 44). That is the controlled data-scaling experiment.
#   r2_noaction  same, with --zero-actions: the trained no-action ablation.
#   r2_growth    same, plus --growth-subsample. R2-A measured that every stored
#                growth episode carries the identical a_grow sequence, so the
#                growth action is a constant; subsampling the stage sequence
#                turns it into a real 5/10/15/20-day action at zero render cost.
#                --growth-fraction is raised 0.25 -> 0.40 because subsampled
#                windows average ~3.8 frames instead of 8, and without that the
#                growth channel's share of the loss would shrink by half.

set -u
cd /home/yogesh/PyHelios

GEN_PID="${1:-0}"
GSPLAT=/home/yogesh/anaconda3/envs/gsplat/bin/python
HELIOS=/home/yogesh/anaconda3/envs/helios/bin/python
WM=yogesh_dev/world_model
DATA=$WM/output/dataset
OUT=$WM/output/r2
LOG=$OUT/r2_pipeline.log
mkdir -p "$OUT"
export PATH=/home/yogesh/anaconda3/envs/gsplat/bin:$PATH

say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

n_train() {
  $GSPLAT -c "import json;print(len(json.load(open('$DATA/manifest.json'))['splits']['train']))" 2>/dev/null || echo 0
}

if [ "$GEN_PID" != "0" ]; then
  say "waiting for generator pid $GEN_PID"
  while ps -p "$GEN_PID" >/dev/null 2>&1; do sleep 60; done
  say "generator exited"
fi
say "dataset: $(du -sh $DATA | cut -f1), train orchards = $(n_train)"

# Seed-split integrity has to be re-checked after EXTENDING the dataset, not
# assumed from Round 1: the extension adds new train seeds and a bug there would
# leak test orchards into training silently.
say "=== split integrity check ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_check_split --data "$DATA" 2>&1 | tee -a "$LOG"

say "=== R2-B: RGB noise floor at the growth probe poses (helios env) ==="
$HELIOS -m yogesh_dev.world_model.run_r2_noise_floor \
  >> "$OUT/r2_noise_floor_stdout.txt" 2>&1
say "noise floor exit=$?"

say "=== R2-A: growth signal analysis on the extended dataset ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_growth_signal --data "$DATA" --split test \
  >> "$OUT/r2_growth_signal_stdout.txt" 2>&1
say "growth signal exit=$?"

say "=== training: r2_main + r2_noaction + r2_growth, concurrently ==="
COMMON="--data $DATA --steps 40000 --image-size 64 --batch-size 24 --seq-len 32 \
        --cache-size 1200 --log-every 500 --val-every 1000 --ckpt-every 2000"

$GSPLAT -m yogesh_dev.world_model.train $COMMON --growth-fraction 0.25 --tag r2_main \
  >> "$WM/output/train_r2_main_stdout.txt" 2>&1 &
P1=$!
$GSPLAT -m yogesh_dev.world_model.train $COMMON --growth-fraction 0.25 --zero-actions \
  --tag r2_noaction >> "$WM/output/train_r2_noaction_stdout.txt" 2>&1 &
P2=$!
$GSPLAT -m yogesh_dev.world_model.train $COMMON --growth-fraction 0.40 --growth-subsample \
  --tag r2_growth >> "$WM/output/train_r2_growth_stdout.txt" 2>&1 &
P3=$!
wait $P1; say "r2_main exit=$?"
wait $P2; say "r2_noaction exit=$?"
wait $P3; say "r2_growth exit=$?"

say "=== W6 evaluation on the held-out test orchards ==="
$GSPLAT -m yogesh_dev.world_model.evaluate \
  --ckpt "$WM/output/train/r2_main/ckpt_best.pt" \
  --noaction-ckpt "$WM/output/train/r2_noaction/ckpt_best.pt" \
  --data "$DATA" --split test --context 5 --seq-len 32 \
  --batch-size 8 --n-batches 24 --out "$WM/output/r2_w6" \
  >> "$OUT/r2_w6_stdout.txt" 2>&1
say "evaluation exit=$?"

say "=== R2-D: growth counterfactual, Round 1 vs Round 2 models ==="
$GSPLAT -m yogesh_dev.world_model.run_r2_growth_eval --data "$DATA" --split test \
  --ckpt "$WM/output/train/main2/ckpt_best.pt"      --tag r1_main \
  --ckpt "$WM/output/train/r2_main/ckpt_best.pt"    --tag r2_main \
  --ckpt "$WM/output/train/r2_growth/ckpt_best.pt"  --tag r2_growth \
  >> "$OUT/r2_growth_eval_stdout.txt" 2>&1
say "growth counterfactual exit=$?"

say "=== curves ==="
$GSPLAT -m yogesh_dev.world_model.plot_curves \
  --tags r2_main,r2_noaction,r2_growth --out "$OUT" --name r2_curves \
  --title "Round 2: 44 train orchards (Round 1 had 12). Val reconstruction dashed." \
  >> "$OUT/r2_curves_stdout.txt" 2>&1
say "curves exit=$?"

say "ROUND 2 PIPELINE DONE"
