#!/usr/bin/env bash
# PostToolUse (Write|Edit): format a .py file with the project's ruff.
# Never calls uv: `uv run` initializes the uv cache on every call and dies where
# it is read-only. No ruff or no jq means nothing to do, not an error.

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null) || exit 0
# An absolute path only: the walk up from a relative one would never end.
[[ "$file" == /*.py && -f "$file" ]] || exit 0

# The nearest .venv/bin/ruff above the file, then ruff from PATH.
find_ruff() {
  local dir="${1%/*}"
  while [[ -n "$dir" ]]; do
    if [[ -x "$dir/.venv/bin/ruff" ]]; then
      echo "$dir/.venv/bin/ruff"
      return 0
    fi
    dir="${dir%/*}"
  done
  if [[ -x "/.venv/bin/ruff" ]]; then
    echo "/.venv/bin/ruff"
    return 0
  fi
  command -v ruff
}

ruff=$(find_ruff "$file") || exit 0

# Lint findings ruff can't fix are not a hook failure.
"$ruff" check --fix "$file" || true
"$ruff" format "$file" || true
