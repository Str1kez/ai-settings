#!/usr/bin/env bash
# SessionStart reminder for Claude Code: quick inventory of skills and agents.
# Silence with AI_SETTINGS_QUIET=1.

set -euo pipefail

if [[ "${AI_SETTINGS_QUIET:-0}" == "1" ]]; then
  exit 0
fi

# Counts the paths that are files; a link counts if its target is one.
# Globs follow the links install.sh puts in ~/.claude.
count_files() {
  local count=0 path
  for path in "$@"; do
    if [[ -f "$path" ]]; then
      count=$((count + 1))
    fi
  done
  echo "$count"
}

# Claude Code loads ~/.claude/skills/<name>/SKILL.md and ~/.claude/agents/<name>.md.
skill_count=$(count_files "$HOME"/.claude/skills/*/SKILL.md)
agent_count=$(count_files "$HOME"/.claude/agents/*.md)

RTK_WARNING=""
if ! command -v rtk &>/dev/null; then
  RTK_WARNING=$'\nrtk hook is wired (rtk hook claude) but rtk binary not found. Install: brew install rtk'
fi

cat <<EOF
[ai-settings] Loaded: ${skill_count} skill(s), ${agent_count} subagent(s).
Reminder: check for relevant skill/subagent BEFORE non-trivial tasks.
Silence: AI_SETTINGS_QUIET=1${RTK_WARNING}
EOF
