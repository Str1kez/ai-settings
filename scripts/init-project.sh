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
Usage: $0 [--cursor] [--claude-models SPEC] [--opencode-models SPEC] [PATH]
  PATH                  project root, the current directory by default
  --cursor              also write .cursor/rules/ai-settings.mdc and keep it out of git
  --claude-models SPEC  write the agent templates into .claude/agents, SPEC like
                        frontier=opus,standard=sonnet
  --opencode-models SPEC
                        the same into .opencode/agents, models as provider/model:
                        frontier=anthropic/opus,standard=openai/gpt
Project agents are personal: they are kept out of git through .git/info/exclude.
EOF
}

CURSOR=0
CLAUDE_MODELS=""
OPENCODE_MODELS=""
HAVE_CLAUDE_MODELS=0
HAVE_OPENCODE_MODELS=0
PROJECT_ROOT="$PWD"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cursor) CURSOR=1 ;;
    --claude-models=*) CLAUDE_MODELS="${1#*=}"; HAVE_CLAUDE_MODELS=1 ;;
    --opencode-models=*) OPENCODE_MODELS="${1#*=}"; HAVE_OPENCODE_MODELS=1 ;;
    --claude-models|--opencode-models)
      if [[ $# -lt 2 ]]; then log_error "$1 needs a value"; usage >&2; exit 2; fi
      if [[ "$1" == --claude-models ]]; then
        CLAUDE_MODELS="$2"; HAVE_CLAUDE_MODELS=1
      else
        OPENCODE_MODELS="$2"; HAVE_OPENCODE_MODELS=1
      fi
      shift ;;
    -h|--help) usage; exit 0 ;;
    -*) usage >&2; exit 2 ;;
    *) PROJECT_ROOT="$1" ;;
  esac
  shift
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
  git_exclude "$PROJECT_ROOT" "$cursor_rule" || {
    log_warn "Not a git repo: after git init, rerun with --cursor to keep $cursor_rule out of git"
  }
fi

# Project agents: the agent templates with concrete models for each level.
# They are personal (the models follow my subscription), so they are kept out
# of git the same way. sync.py prints the files it wrote, one per line.
if [[ $HAVE_CLAUDE_MODELS -eq 0 && $HAVE_OPENCODE_MODELS -eq 0 ]]; then
  log_info "No project agents: pass --claude-models and/or --opencode-models to create them"
else
  agent_args=()
  [[ $HAVE_CLAUDE_MODELS -eq 1 ]] && agent_args+=(--claude-models "$CLAUDE_MODELS")
  [[ $HAVE_OPENCODE_MODELS -eq 1 ]] && agent_args+=(--opencode-models "$OPENCODE_MODELS")
  # A failure aborts here (set -e): sync.py has already said why.
  written="$(python3 "$SCRIPT_DIR/sync.py" project-agents "$PROJECT_ROOT" "${agent_args[@]}")"
  not_git=0
  while IFS= read -r agent_file; do
    [[ -n "$agent_file" ]] || continue
    git_exclude "$PROJECT_ROOT" "$agent_file" || not_git=1
  done <<< "$written"
  if [[ $not_git -eq 1 ]]; then
    log_warn "Not a git repo: after git init, rerun to keep the project agents out of git"
  fi
fi

log_ok "Project init complete: $PROJECT_ROOT"
if [[ ! -d "$PROJECT_ROOT/docs/agents" ]]; then
  log_info "Matt's engineering skills need a per-repo setup: run /setup-matt-pocock-skills in the project"
fi
