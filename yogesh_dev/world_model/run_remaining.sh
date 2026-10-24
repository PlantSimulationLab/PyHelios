#!/usr/bin/env bash
# W3-verify -> W5 training -> W6 evaluation, chained so the whole tail of the
# plan runs unattended after dataset generation finishes.
#
# Usage:
#   bash yogesh_dev/world_model/run_remaining.sh <generator_pid> <min_train_seeds>
#
# Stops the generator once `min_train_seeds` train orchards are on disk (or when
# it exits on its own), because the generator writes its manifest after every
# completed orchard and killing it between orchards leaves a valid dataset.

set -u
cd /home/yogesh/PyHelios

GEN_PID="${1:-0}"
MIN_TRAIN="${2:-12}"
HELIOS=/home/yogesh/anaconda3/envs/helios/bin/python
GSPLAT=/home/yogesh/anaconda3/envs/gsplat/bin/python
WM=yogesh_dev/world_model
DATA=$WM/output/dataset
LOG=$WM/output/remaining.log
export PATH=/home/yogesh/anaconda3/envs/gsplat/bin:$PATH   # gsplat JIT needs ninja

say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

n_train() {
  $GSPLAT - <<'PY' 2>/dev/null || echo 0
import json
m = json.load(open("yogesh_dev/world_model/output/dataset/manifest.json"))
print(len(m["splits"]["train"]))
PY
}

say "waiting for >= $MIN_TRAIN train orchards (generator pid $GEN_PID)"
while true; do
  if [ "$GEN_PID" != "0" ] && ! ps -p "$GEN_PID" >/dev/null 2>&1; then
    say "generator exited on its own"; break
  fi
  n=$(n_train)
  if [ "${n:-0}" -ge "$MIN_TRAIN" ]; then
    say "reached $n train orchards; stopping generator"
    [ "$GEN_PID" != "0" ] && kill "$GEN_PID" 2>/dev/null
    sleep 10
    break
  fi
  sleep 60
done

say "dataset: $(du -sh $DATA | cut -f1), train orchards = $(n_train)"

say "=== W3 verification (helios env; re-renders one orchard for byte equality) ==="
$HELIOS -m yogesh_dev.world_model.run_w3_verify --data "$DATA" \
  >> "$WM/output/w3_verify_stdout.txt" 2>&1
say "W3 verification exit=$?"

# Main model and the no-action ablation are trained CONCURRENTLY. They are
# independent, each peaks at ~3 GB on a 32 GB card, and neither saturates the
# GPU alone, so running them in parallel roughly halves wall-clock time. Same
# seed, same steps, same everything except --zero-actions, which is what makes
# the ablation a controlled comparison rather than a differently-trained model.
say "=== W5 training: main + no-action ablation, concurrently ==="
$GSPLAT -m yogesh_dev.world_model.train --data "$DATA" --steps 40000 \
  --image-size 64 --batch-size 24 --seq-len 32 --growth-fraction 0.25 \
  --log-every 200 --val-every 1000 --ckpt-every 1000 --tag main \
  >> "$WM/output/train_main_stdout.txt" 2>&1 &
PID_MAIN=$!
$GSPLAT -m yogesh_dev.world_model.train --data "$DATA" --steps 40000 \
  --image-size 64 --batch-size 24 --seq-len 32 --growth-fraction 0.25 \
  --zero-actions --log-every 200 --val-every 1000 --ckpt-every 1000 --tag noaction \
  >> "$WM/output/train_noaction_stdout.txt" 2>&1 &
PID_NOACT=$!
wait $PID_MAIN; say "main training exit=$?"
wait $PID_NOACT; say "no-action training exit=$?"

say "=== W6 evaluation ==="
$GSPLAT -m yogesh_dev.world_model.evaluate \
  --ckpt "$WM/output/train/main/ckpt_best.pt" \
  --noaction-ckpt "$WM/output/train/noaction/ckpt_best.pt" \
  --data "$DATA" --split test --context 5 --seq-len 32 \
  --batch-size 8 --n-batches 24 \
  >> "$WM/output/w6_stdout.txt" 2>&1
say "evaluation exit=$?"

say "=== W6 gsplat view-synthesis reference ==="
$GSPLAT -m yogesh_dev.world_model.gsplat_baseline --data "$DATA" --split test \
  --context 5 --seq-len 32 --n-episodes 6 --iters 3000 --image-size 64 \
  >> "$WM/output/gsplat_stdout.txt" 2>&1
say "gsplat baseline exit=$?"

say "ALL DONE"
$GSPLAT notify_slack.py "World model W3-W6 finished: dataset $(du -sh $DATA | cut -f1), \
train orchards $(n_train). See yogesh_dev/world_model/output/." || true
