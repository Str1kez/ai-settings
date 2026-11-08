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
                        frontier=opus,standard=sonnet,fast=haiku
  --opencode-models SPEC
                        the same into .opencode/agents, models as provider/model:
                        frontier=anthropic/opus,standard=openai/gpt,fast=openai/mini
In a terminal, a harness without a flag is asked for: whether to create its
agents (only when it has none yet) and a model for each level still missing.
A rerun without these flags updates the agents already there and keeps their models.
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

# Bad flag values must fail before the first file is written. A dry run of
# sync.py applies its own validation. A level without a model is fatal here
# only for a harness the flags cover: the prompts below fill the others.
if [[ $HAVE_CLAUDE_MODELS -eq 1 || $HAVE_OPENCODE_MODELS -eq 1 ]]; then
  early_args=()
  [[ $HAVE_CLAUDE_MODELS -eq 1 ]] && early_args+=(--claude-models "$CLAUDE_MODELS")
  [[ $HAVE_OPENCODE_MODELS -eq 1 ]] && early_args+=(--opencode-models "$OPENCODE_MODELS")
  early_code=0
  early_err="$(python3 "$SCRIPT_DIR/sync.py" project-agents --dry-run "$PROJECT_ROOT" "${early_args[@]}" 2>&1 >/dev/null)" || early_code=$?
  if [[ $early_code -eq 3 ]]; then
    covered=""
    [[ $HAVE_CLAUDE_MODELS -eq 1 ]] && covered+="claude "
    [[ $HAVE_OPENCODE_MODELS -eq 1 ]] && covered+="opencode "
    for harness in $covered; do
      if printf '%s\n' "$early_err" | grep -q "^missing-model: $harness "; then
        printf '%s\n' "$early_err" >&2
        exit 3
      fi
    done
  elif [[ $early_code -ne 0 ]]; then
    printf '%s\n' "$early_err" >&2
    exit "$early_code"
  fi
fi

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

<!-- Makefile targets for install, run, test, lint and build. The agent,
     a human and CI run the same targets; a new script or CI step gets a
     target first. -->

## Where to look

<!-- One line per doc an agent must read before a kind of work:
     - <trigger> → `<file>`
     For example: writing or changing tests → `docs/agents/testing.md` -->

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
  exclude_code=0
  git_exclude "$PROJECT_ROOT" "$cursor_rule" || exclude_code=$?
  case "$exclude_code" in
    0) ;;
    2) log_warn "Not a git repo: after git init, rerun with --cursor to keep $cursor_rule out of git" ;;
    *) log_error "Could not exclude $cursor_rule from git"; exit "$exclude_code" ;;
  esac
fi

# Project agents: the agent templates with concrete models for each level.
# They are personal (the models follow my subscription), so they are kept out
# of git the same way. sync.py prints the files it wrote, one per line.
agent_args=()
[[ $HAVE_CLAUDE_MODELS -eq 1 ]] && agent_args+=(--claude-models "$CLAUDE_MODELS")
[[ $HAVE_OPENCODE_MODELS -eq 1 ]] && agent_args+=(--opencode-models "$OPENCODE_MODELS")

# probe_missing HARNESS [bind]: the levels sync.py reports as `missing-model`
# for HARNESS, one per line. With `bind` the probe also asks for HARNESS with
# an empty binding, so a harness that holds no agents yet shows up too. It is a
# dry run: nothing is written. Any other failure (a conflict between files)
# stops init with sync.py's message.
probe_missing() {
  local harness="$1" bind="${2:-}" probe_args=() err code=0
  [[ -n "$bind" ]] && probe_args=("--$harness-models" "")
  err="$(python3 "$SCRIPT_DIR/sync.py" project-agents --dry-run "$PROJECT_ROOT" \
    ${agent_args[@]+"${agent_args[@]}"} ${probe_args[@]+"${probe_args[@]}"} 2>&1 >/dev/null)" || code=$?
  case "$code" in
    0) ;;
    3) printf '%s\n' "$err" | sed -n "s/^missing-model: $harness //p" ;;
    *) printf '%s\n' "$err" >&2; exit "$code" ;;
  esac
}

# prompt TEXT: reads one line into REPLY_LINE. EOF (Ctrl-D) aborts: under
# set -e a failed read would end the script without a word.
prompt() {
  REPLY_LINE=""
  if ! read -r -p "$1" REPLY_LINE; then
    echo >&2
    log_error "Input closed before the questions were answered; no project agents were written"
    exit 1
  fi
}

# ask_model HARNESS LEVEL: one model for one level, asked until it is valid.
# Claude Code has defaults for the known levels, Enter takes them; OpenCode
# has none and needs provider/model.
ask_model() {
  local harness="$1" level="$2" default="" answer
  if [[ "$harness" == claude ]]; then
    case "$level" in frontier) default="opus" ;; standard) default="sonnet" ;; fast) default="haiku" ;; esac
  fi
  while true; do
    if [[ -n "$default" ]]; then
      prompt "  $harness: model for $level [$default]: "
      answer="${REPLY_LINE:-$default}"
    else
      prompt "  $harness: model for $level: "
      answer="$REPLY_LINE"
    fi
    if [[ -z "$answer" || "$answer" == *[,=\ ]* ]]; then
      log_warn "Give one model name, without spaces, commas or '='"
    elif [[ "$harness" == opencode && "$answer" != */* ]]; then
      log_warn "OpenCode models look like provider/model, for example anthropic/opus"
    else
      REPLY_MODEL="$answer"
      return 0
    fi
  done
}

# ask_harness HARNESS LABEL: asks for the models of one harness when stdin is a
# terminal and no flag covers it, then adds the answers to agent_args. "Do you
# want it" is asked only for a harness without our agents; a harness that has
# them is updated, and only its missing levels are asked.
ask_harness() {
  local harness="$1" label="$2" have_flag="$3" gaps all level answer spec=""
  [[ $have_flag -eq 0 && -t 0 ]] || return 0
  gaps="$(probe_missing "$harness")"
  all="$(probe_missing "$harness" bind)"
  [[ -n "$all" ]] || return 0
  if [[ -n "$gaps" ]]; then
    all="$gaps"
  else
    prompt "Project agents for $label? [y/N] "
    answer="$REPLY_LINE"
    [[ "$answer" == [yY] || "$answer" == [yY][eE][sS] ]] || return 0
  fi
  log_info "$label models"
  # Levels are plain words; a here-string loop would feed them to ask_model's read.
  for level in $all; do
    ask_model "$harness" "$level"
    spec+="${spec:+,}$level=$REPLY_MODEL"
  done
  agent_args+=("--$harness-models" "$spec")
}
ask_harness claude "Claude Code" "$HAVE_CLAUDE_MODELS"
ask_harness opencode "OpenCode" "$HAVE_OPENCODE_MODELS"

# Without flags sync.py reruns the harnesses that already hold our agents,
# with the models found in those files. A failure aborts here (set -e) with
# sync.py's code: 3 is a level without a model, named on stderr as
# `missing-model: HARNESS LEVEL`.
written="$(python3 "$SCRIPT_DIR/sync.py" project-agents "$PROJECT_ROOT" ${agent_args[@]+"${agent_args[@]}"})"
not_git=0
while IFS= read -r agent_file; do
  [[ -n "$agent_file" ]] || continue
  exclude_code=0
  git_exclude "$PROJECT_ROOT" "$agent_file" || exclude_code=$?
  case "$exclude_code" in
    0) ;;
    2) not_git=1 ;;
    *) log_error "Could not exclude $agent_file from git"; exit "$exclude_code" ;;
  esac
done <<< "$written"
if [[ $not_git -eq 1 ]]; then
  log_warn "Not a git repo: after git init, rerun to keep the project agents out of git"
fi

log_ok "Project init complete: $PROJECT_ROOT"
if [[ ! -d "$PROJECT_ROOT/docs/agents" ]]; then
  log_info "Matt's engineering skills need a per-repo setup: run /setup-matt-pocock-skills in the project"
fi
