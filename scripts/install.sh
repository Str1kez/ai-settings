#!/usr/bin/env bash
# Global install: configure Claude Code, Codex, OpenCode, Gemini, and Cursor.
# Idempotent. Supports --dry-run.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_SETTINGS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export AI_SETTINGS_ROOT
source "$SCRIPT_DIR/lib/common.sh"

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--dry-run]
  --dry-run   Show actions without applying.
EOF
      exit 0
      ;;
  esac
done

log_info "ai-settings root: $AI_SETTINGS_ROOT"

# --- Windows check ---
if [[ -z "${WSL_DISTRO_NAME:-}" ]]; then
  case "$OSTYPE" in
    msys*|cygwin*|win32*)
      echo "Windows detected without WSL."
      echo "This script requires WSL (Windows Subsystem for Linux)."
      echo "Please run this script from a WSL terminal."
      echo "Manual setup instructions: docs/setup/claude-code.md (Windows section)"
      exit 1
      ;;
  esac
fi

[[ $DRY_RUN -eq 1 ]] && log_warn "DRY RUN — no changes will be made"

# --- Skills, rules, agents and Claude Code settings, for every harness ---
# sync.py links every skill flat into ~/.claude/skills and ~/.agents/skills,
# links CLAUDE.md and GEMINI.md, writes the flat AGENTS.md that Codex,
# OpenCode and Cursor need (they don't follow @imports), links every agent
# into ~/.claude/agents and renders it for the other harnesses. It merges
# settings/claude-settings.json into ~/.claude/settings.json and links the
# hook scripts it runs into ~/.claude/hooks. It handles --dry-run itself.
log_info "Syncing skills, rules, agents and Claude Code settings..."
if [[ $DRY_RUN -eq 0 ]]; then
  python3 "$SCRIPT_DIR/sync.py" all
else
  python3 "$SCRIPT_DIR/sync.py" all --dry-run
fi

log_ok "ai-settings installation complete."
