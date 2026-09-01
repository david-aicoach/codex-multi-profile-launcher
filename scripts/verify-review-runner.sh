#!/usr/bin/env bash
set -euo pipefail

if ! command -v codex >/dev/null 2>&1; then
  echo "Codex CLI is not installed on this runner." >&2
  exit 1
fi

check_profile() {
  local name="$1"
  local home="$2"
  if [ ! -d "$home" ]; then
    echo "$name profile directory is missing on this runner." >&2
    exit 1
  fi
  if ! CODEX_HOME="$home" codex login status >/dev/null 2>&1; then
    echo "$name profile is not authenticated on this runner." >&2
    exit 1
  fi
}

check_profile "Codex Business" "$HOME/.codex-business"
check_profile "Codex David" "$HOME/.codex-david"

echo "Codex profile review runner is ready."
