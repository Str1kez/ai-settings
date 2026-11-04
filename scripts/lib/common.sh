#!/usr/bin/env bash
# Common utilities for ai-settings scripts.
# Source this: `source "$(dirname "$0")/lib/common.sh"`

set -euo pipefail

AI_SETTINGS_ROOT="${AI_SETTINGS_ROOT:-$HOME/.ai-settings}"

log_info()  { echo -e "\033[36m[info]\033[0m  $*" >&2; }
log_warn()  { echo -e "\033[33m[warn]\033[0m  $*" >&2; }
log_error() { echo -e "\033[31m[error]\033[0m $*" >&2; }
log_ok()    { echo -e "\033[32m[ok]\033[0m    $*" >&2; }

# git_exclude PROJECT_ROOT REL_PATH
# Keep a personal file out of git through .git/info/exclude: unlike
# .gitignore it isn't committed itself. REL_PATH is relative to PROJECT_ROOT,
# which may be a subdirectory of the repo. One line per file, however often
# this runs. Returns 2 outside a git repo (the caller decides what to say) and
# 1 when a step failed. Callers run it on the left of `||`, where set -e is
# off, so every failing step returns explicitly.
git_exclude() {
  local root="$1" rel="$2" exclude prefix ignored=0
  git -C "$root" rev-parse --git-dir >/dev/null 2>&1 || return 2
  # --no-index: a pattern counts even if the file is already tracked.
  git -C "$root" check-ignore -q --no-index "$rel" || ignored=$?
  case "$ignored" in
    0) ;;
    1)
      exclude="$(cd "$root" && git rev-parse --git-path info/exclude)" || return 1
      [[ "$exclude" == /* ]] || exclude="$root/$exclude"
      # Exclude patterns are relative to the top of the repo.
      prefix="$(git -C "$root" rev-parse --show-prefix)" || return 1
      mkdir -p "$(dirname "$exclude")" || return 1
      echo "/$prefix$rel" >> "$exclude" || return 1
      log_ok "Excluded $rel from git"
      ;;
    *) return 1 ;;
  esac
  if git -C "$root" ls-files --error-unmatch "$rel" >/dev/null 2>&1; then
    log_warn "$rel is already in git; untrack it: git rm --cached $rel"
  fi
}
