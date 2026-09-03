#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKER=""
TASK_FILE=""
WORKDIR="$ROOT"
CODEX_PERMISSION_PROFILE=":workspace"
CODEX_EXEC_TIMEOUT_SECONDS=300

while [ "$#" -gt 0 ]; do
  case "$1" in
    --worker) WORKER="$2"; shift 2 ;;
    --task-file) TASK_FILE="$2"; shift 2 ;;
    --workdir) WORKDIR="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$WORKER" ] || [ -z "$TASK_FILE" ]; then
  echo "Usage: $0 --worker C2|C1 --task-file PATH [--workdir PATH]" >&2
  exit 2
fi

case "$WORKER" in
  C2)
    export CODEX_HOME="$HOME/.codex-david"
    export CODEX_BRIDGE_WORKER_ID="C2"
    export CODEX_BRIDGE_WORKER_NAME="Codex David"
    ;;
  C1)
    export CODEX_HOME="$HOME/.codex-business"
    export CODEX_BRIDGE_WORKER_ID="C1"
    export CODEX_BRIDGE_WORKER_NAME="Codex Business"
    ;;
  *)
    echo "Forbidden worker ID: $WORKER" >&2
    exit 2
    ;;
esac

TASK_FILE="$(cd "$(dirname "$TASK_FILE")" && pwd)/$(basename "$TASK_FILE")"
if [ ! -f "$TASK_FILE" ]; then
  echo "Task file not found: $TASK_FILE" >&2
  exit 2
fi
if [ ! -d "$WORKDIR" ]; then
  echo "Work directory not found: $WORKDIR" >&2
  exit 2
fi
WORKDIR="$(cd "$WORKDIR" && pwd)"

TASK_BASENAME="$(basename "$TASK_FILE")"
if [[ "$TASK_BASENAME" =~ ^(TASK-[0-9]+) ]]; then
  TASK_ID="${BASH_REMATCH[1]}"
elif [[ "$TASK_BASENAME" =~ ^([0-9]{3})- ]]; then
  TASK_ID="FD-${BASH_REMATCH[1]}"
else
  TASK_ID="$(printf '%s' "$TASK_BASENAME" | sed -E 's/\.[^.]+$//; s/[^A-Za-z0-9]+/-/g; s/^-+|-+$//g' | cut -c1-80)"
  if [ -z "$TASK_ID" ]; then
    echo "Could not derive task id from task filename: $TASK_FILE" >&2
    exit 2
  fi
fi

OUTPUT_DIR="$ROOT/runtime/outputs/$TASK_ID"
LOCK_DIR="$ROOT/runtime/tmp/$TASK_ID.lock"
mkdir -p "$OUTPUT_DIR/artifacts" "$ROOT/runtime/tmp"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Task is already locked: $TASK_ID" >&2
  exit 3
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

python3 "$ROOT/tools/aosctl.py" activate-worker "$WORKER" --codex-home "$CODEX_HOME"

STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
set +e
python3 - "$TASK_FILE" "$WORKDIR" "$OUTPUT_DIR/events.jsonl" "$OUTPUT_DIR/run.log" "$OUTPUT_DIR/summary.md" "$CODEX_PERMISSION_PROFILE" "$CODEX_EXEC_TIMEOUT_SECONDS" <<'PY_RUN'
import os
import pathlib
import signal
import subprocess
import sys

task_file = pathlib.Path(sys.argv[1])
workdir = pathlib.Path(sys.argv[2])
events_path = pathlib.Path(sys.argv[3])
log_path = pathlib.Path(sys.argv[4])
summary_path = pathlib.Path(sys.argv[5])
permission_profile = sys.argv[6]
timeout_seconds = int(sys.argv[7])

command = [
    "codex", "exec",
    "--strict-config",
    "--ignore-user-config",
    "--ephemeral",
    "--skip-git-repo-check",
    "-C", str(workdir),
    "-c", f'default_permissions="{permission_profile}"',
    "-c", 'approval_policy="never"',
    "--json",
    "--output-last-message", str(summary_path),
    "-",
]

with task_file.open("r", encoding="utf-8") as task, \
     events_path.open("w", encoding="utf-8") as events, \
     log_path.open("w", encoding="utf-8") as log:
    try:
        process = subprocess.Popen(
            command,
            stdin=task,
            stdout=events,
            stderr=log,
            cwd=workdir,
            env=os.environ.copy(),
            text=True,
            start_new_session=True,
        )
    except OSError:
        raise SystemExit(126)

    try:
        exit_code = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        log.write(f"\nCodex execution exceeded fixed {timeout_seconds}-second timeout; terminating process group.\n")
        log.flush()
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        exit_code = 124

raise SystemExit(exit_code)
PY_RUN
EXIT_CODE=$?
set -e
FINISHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

STATUS="success"
ERRORS='[]'
if [ "$EXIT_CODE" -ne 0 ]; then
  STATUS="failed"
  if [ "$EXIT_CODE" -eq 124 ]; then
    ERRORS='["codex exec exceeded the fixed 300-second execution timeout"]'
  else
    ERRORS='["codex exec returned a non-zero exit code"]'
  fi
  printf '# Execution failure\n\nWorker: %s\nExit code: %s\nSee run.log and events.jsonl.\n' "$CODEX_BRIDGE_WORKER_NAME" "$EXIT_CODE" > "$OUTPUT_DIR/error.md"
fi

python3 - "$OUTPUT_DIR/status.json" "$TASK_ID" "$WORKER" "$CODEX_BRIDGE_WORKER_NAME" "$STATUS" "$STARTED_AT" "$FINISHED_AT" "$EXIT_CODE" "$ERRORS" "$WORKDIR" "$CODEX_EXEC_TIMEOUT_SECONDS" <<'PY_STATUS'
import json, sys
path, task_id, worker_id, worker_name, status, started, finished, exit_code, errors, workdir, timeout_seconds = sys.argv[1:]
data = {
    "task_id": task_id,
    "worker_id": worker_id,
    "worker_name": worker_name,
    "status": status,
    "started_at": started,
    "finished_at": finished,
    "exit_code": int(exit_code),
    "artifacts": [],
    "errors": json.loads(errors),
    "tests": [],
    "review_recommended": True,
    "workdir": workdir,
    "permission_profile": ":workspace",
    "approval_policy": "never",
    "user_config": "ignored",
    "session_persistence": "ephemeral",
    "execution_timeout_seconds": int(timeout_seconds),
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY_STATUS

exit "$EXIT_CODE"
