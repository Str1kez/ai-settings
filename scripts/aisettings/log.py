"""Tagged log lines on stderr, the same look as scripts/lib/common.sh."""

from __future__ import annotations

import sys

_COLORS = {
    "info": "36",
    "ok": "32",
    "warn": "33",
    "error": "31",
    "dry-run": "35",
}


def _emit(tag: str, message: str) -> None:
    label = f"[{tag}]"
    if sys.stderr.isatty():
        label = f"\033[{_COLORS[tag]}m{label}\033[0m"
    print(f"{label} {message}", file=sys.stderr)


def info(message: str) -> None:
    _emit("info", message)


def ok(message: str) -> None:
    _emit("ok", message)


def warn(message: str) -> None:
    _emit("warn", message)


def error(message: str) -> None:
    _emit("error", message)


def dry_run(message: str) -> None:
    _emit("dry-run", message)
