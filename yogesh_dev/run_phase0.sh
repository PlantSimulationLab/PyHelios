#!/usr/bin/env bash
set -uo pipefail

REPO="/home/yogesh/PyHelios"
DEV="$REPO/yogesh_dev"
CLAUDE_BIN="/home/yogesh/.vscode-server/extensions/anthropic.claude-code-2.1.220-linux-x64/resources/native-binary/claude"
LOG="$DEV/phase0_run.log"
STATUS="$DEV/PHASE0_STATUS.md"

cd "$REPO"

"$CLAUDE_BIN" -p "$(cat "$DEV/PHASE0_PROMPT.md")" \
  --dangerously-skip-permissions \
  --output-format text \
  --max-budget-usd 100 \
  -n phase0-build \
  > "$LOG" 2>&1
EXIT_CODE=$?

echo "RUN_EXIT_CODE=$EXIT_CODE" >> "$LOG"

if [ ! -f "$STATUS" ]; then
  echo "STATUS: BLOCKED: agent process exited (code $EXIT_CODE) without writing a status file" > "$STATUS"
fi

SUMMARY="$(tail -1 "$STATUS")"
/home/yogesh/anaconda3/envs/helios/bin/python "$REPO/notify_slack.py" "Phase 0 build (tmux gsplat) finished, exit=$EXIT_CODE. $SUMMARY" || true

echo "___PHASE0_WRAPPER_DONE___" >> "$LOG"
