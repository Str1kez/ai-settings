#!/usr/bin/env bash
# Project layer of ai-settings: the files my global rules expect in a project.
# Run from the project root: `~/.ai-settings/scripts/init-project.sh [--cursor] [PATH]`
#
# install.sh already brings the global rules, skills and agents to every
# harness, so none of them is copied here. Only files that belong to the
# project are created, and only when missing.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_SETTINGS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export AI_SETTINGS_ROOT
source "$SCRIPT_DIR/lib/common.sh"

usage() {
  cat <<EOF
Usage: $0 [--cursor] [PATH]
  PATH       project root, the current directory by default
  --cursor   also write .cursor/rules/ai-settings.mdc and keep it out of git
EOF
}

CURSOR=0
PROJECT_ROOT="$PWD"
for arg in "$@"; do
  case "$arg" in
    --cursor) CURSOR=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) usage >&2; exit 2 ;;
    *) PROJECT_ROOT="$arg" ;;
  esac
done
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

log_info "Initializing ai-settings for project: $PROJECT_ROOT"

# Claude Code, Codex, OpenCode and Cursor read AGENTS.md from the project root
# (Claude Code checked on 2.1.289). Gemini CLI reads only GEMINI.md unless its
# context.fileName lists AGENTS.md. Codex and Cursor don't read CLAUDE.md, and
# a new AGENTS.md next to it would split the project rules in two files.
if [[ -f "$PROJECT_ROOT/AGENTS.md" ]]; then
  log_info "AGENTS.md exists; not touching it"
elif [[ -f "$PROJECT_ROOT/CLAUDE.md" ]]; then
  log_warn "CLAUDE.md without AGENTS.md: Codex and Cursor don't read it. Consider renaming it to AGENTS.md, Claude Code reads that too"
else
  cat > "$PROJECT_ROOT/AGENTS.md" <<'EOF'
# AGENTS.md

<!-- Instructions for coding agents that are specific to this project.
     Personal preferences belong in the global rules, not here. -->

## Project

<!-- What this project is, in 2-3 sentences. -->

## Stack

<!-- Languages, frameworks and versions used here. -->

## Commands

<!-- How to install, run, test, lint and build. -->

## Conventions

<!-- Project decisions that override the global rules, with the reason. -->
EOF
  log_ok "Created AGENTS.md"
fi

# The global rules keep CHANGELOG.md (Russian, Keep a Changelog) and TODO.md
# in the project root.
if [[ ! -f "$PROJECT_ROOT/CHANGELOG.md" ]]; then
  cat > "$PROJECT_ROOT/CHANGELOG.md" <<'EOF'
# CHANGELOG

Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).

## [Unreleased]

EOF
  log_ok "Created CHANGELOG.md"
fi

if [[ ! -f "$PROJECT_ROOT/TODO.md" ]]; then
  cat > "$PROJECT_ROOT/TODO.md" <<'EOF'
# TODO

## В работе

## Следующее

## Идеи / бэклог
EOF
  log_ok "Created TODO.md"
fi

# Cursor takes user rules only from its settings UI, so the global rules reach
# it as a copy inside the project. The copy is personal: .git/info/exclude
# keeps it out of git and, unlike .gitignore, isn't committed itself.
if [[ $CURSOR -eq 1 ]]; then
  cursor_rule=".cursor/rules/ai-settings.mdc"
  python3 "$SCRIPT_DIR/sync.py" rules --cursor-project "$PROJECT_ROOT"
  if ! git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    log_warn "Not a git repo: after git init, rerun with --cursor to keep $cursor_rule out of git"
  else
    # --no-index: a pattern counts even if the file is already tracked.
    if ! git -C "$PROJECT_ROOT" check-ignore -q --no-index "$cursor_rule"; then
      exclude="$(cd "$PROJECT_ROOT" && git rev-parse --git-path info/exclude)"
      [[ "$exclude" == /* ]] || exclude="$PROJECT_ROOT/$exclude"
      # Exclude patterns are relative to the top of the repo, the project may
      # be a subdirectory of it.
      prefix="$(git -C "$PROJECT_ROOT" rev-parse --show-prefix)"
      mkdir -p "$(dirname "$exclude")"
      echo "/$prefix$cursor_rule" >> "$exclude"
      log_ok "Excluded $cursor_rule from git"
    fi
    if git -C "$PROJECT_ROOT" ls-files --error-unmatch "$cursor_rule" >/dev/null 2>&1; then
      log_warn "$cursor_rule is already in git; untrack it: git rm --cached $cursor_rule"
    fi
  fi
fi

log_ok "Project init complete: $PROJECT_ROOT"
if [[ ! -d "$PROJECT_ROOT/docs/agents" ]]; then
  log_info "Matt's engineering skills need a per-repo setup: run /setup-matt-pocock-skills in the project"
fi
