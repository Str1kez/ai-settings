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

# --- Claude Code ---
log_info "Setting up Claude Code..."
if [[ $DRY_RUN -eq 0 ]]; then
  ensure_dir "$HOME/.claude"
  ensure_symlink "$AI_SETTINGS_ROOT/settings/hooks"    "$HOME/.claude/hooks"
else
  echo "[dry-run] ensure_dir $HOME/.claude"
  echo "[dry-run] ensure_symlink $AI_SETTINGS_ROOT/settings/hooks -> $HOME/.claude/hooks"
fi

# settings.json — merge managed keys (permissions, hooks, $schema) into existing file.
# User-owned keys (enabledPlugins, extraKnownMarketplaces, etc.) are preserved.
settings_target="$HOME/.claude/settings.json"
settings_source="$AI_SETTINGS_ROOT/settings/claude-settings.json"
if [[ ! -f "$settings_target" ]]; then
  log_info "No existing ~/.claude/settings.json — installing from template"
  if [[ $DRY_RUN -eq 0 ]]; then
    cp "$settings_source" "$settings_target"
  else
    echo "[dry-run] cp $settings_source $settings_target"
  fi
else
  log_info "Merging managed keys into ~/.claude/settings.json..."
  if [[ $DRY_RUN -eq 0 ]]; then
    if command -v jq &>/dev/null; then
      tmp=$(mktemp)
      jq --argjson tpl "$(cat "$settings_source")" \
        '. * {"$schema": $tpl["$schema"], permissions: $tpl.permissions, hooks: $tpl.hooks}' \
        "$settings_target" > "$tmp" && mv "$tmp" "$settings_target"
      log_ok "settings.json updated (permissions + hooks merged)"
    else
      log_warn "jq not found — skipping merge. Install jq or manually copy: diff $settings_source $settings_target"
    fi
  else
    echo "[dry-run] jq-merge permissions + hooks from $settings_source -> $settings_target"
  fi
fi

# --- Skills, rules and agents: Claude Code, Codex, OpenCode, Gemini CLI, Cursor ---
# sync.py links every skill flat into ~/.claude/skills and ~/.agents/skills,
# links CLAUDE.md and GEMINI.md, writes the flat AGENTS.md that Codex,
# OpenCode and Cursor need (they don't follow @imports), links every agent
# into ~/.claude/agents and renders it as an OpenCode markdown agent. It
# handles --dry-run itself.
log_info "Syncing skills, rules and agents..."
if [[ $DRY_RUN -eq 0 ]]; then
  python3 "$SCRIPT_DIR/sync.py" all
else
  python3 "$SCRIPT_DIR/sync.py" all --dry-run
fi

# --- RTK (Rust Token Killer) ---
log_info "Setting up RTK (Rust Token Killer)..."
if command -v rtk &>/dev/null; then
  log_ok "rtk already installed: $(rtk --version 2>/dev/null || echo 'unknown version')"
else
  log_info "rtk not found. Installing..."
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] install rtk binary"
  elif command -v brew &>/dev/null; then
    brew install rtk
    log_ok "rtk installed via Homebrew"
  else
    curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
    log_ok "rtk installed via install script"
  fi
fi

# Claude Code hook is wired via the claude-settings.json merge above
# (PreToolUse -> "rtk hook claude", native binary command, no extra setup).
# OpenCode has no equivalent settings.json merge, so wire its plugin explicitly.
log_info "Setting up RTK OpenCode plugin..."
if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] rtk init -g --opencode --hook-only --no-patch"
elif command -v rtk &>/dev/null; then
  if rtk init -g --opencode --hook-only --no-patch &>/dev/null; then
    log_ok "RTK OpenCode plugin installed (~/.config/opencode/plugins/rtk.ts)"
  else
    log_warn "RTK OpenCode plugin install failed — run manually: rtk init -g --opencode"
  fi
else
  log_warn "rtk binary not found — skipping OpenCode plugin (run 'rtk init -g --opencode' after installing rtk)"
fi

log_ok "ai-settings installation complete."
