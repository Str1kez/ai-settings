#!/usr/bin/env bash
# Common utilities for ai-settings scripts.
# Source this: `source "$(dirname "$0")/lib/common.sh"`

set -euo pipefail

AI_SETTINGS_ROOT="${AI_SETTINGS_ROOT:-$HOME/.ai-settings}"

log_info()  { echo -e "\033[36m[info]\033[0m  $*" >&2; }
log_warn()  { echo -e "\033[33m[warn]\033[0m  $*" >&2; }
log_error() { echo -e "\033[31m[error]\033[0m $*" >&2; }
log_ok()    { echo -e "\033[32m[ok]\033[0m    $*" >&2; }
