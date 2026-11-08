"""OpenCode: the shell its agents run commands in, pinned in the global config.

~/.config/opencode/opencode.jsonc belongs to the user: providers, models and
keys live there. The installer owns one thing, the top-level `shell` key, and
only adds it. A `shell` the user set to another value stays, with a warning.

The file is JSONC with comments that a rewrite would lose, and stdlib has no
JSONC parser. So the file is scanned, not parsed: _scan finds the root object
and its top-level `shell`, and the key goes in as text right after the root `{`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aisettings import log
from aisettings.fs import Fs, SyncError

# The same shell as CLAUDE_CODE_SHELL in settings/claude-settings.json; the
# tests keep the two equal.
SHELL = "/bin/bash"

_CONFIG_DIR = Path(".config/opencode")
# opencode.jsonc first: it is the one the user already keeps.
_CONFIGS = ("opencode.jsonc", "opencode.json")
_KEY = "shell"
_NOT_A_STRING = "(not a string)"
_INDENT = "  "


@dataclass(frozen=True)
class _Scan:
    open_at: int
    empty: bool
    shell: str | None


def sync(fs: Fs, home: Path) -> None:
    directory = home / _CONFIG_DIR
    path = next((directory / name for name in _CONFIGS if (directory / name).is_file()), None)
    if path is None:
        fs.write(directory / _CONFIGS[0], f'{{\n{_INDENT}"{_KEY}": "{SHELL}"\n}}\n')
        return
    text = path.read_text(encoding="utf-8")
    scan = _scan(text, path)
    if scan.shell is None:
        fs.update_in_place(path, _with_shell(text, scan))
    elif scan.shell != SHELL:
        log.warn(f'{path}: "{_KEY}" is {scan.shell}, not {SHELL}; left as is, agents will run in another shell')
    else:
        log.info(f"up to date {path}")


def _with_shell(text: str, scan: _Scan) -> str:
    head = text[: scan.open_at + 1]
    rest = text[scan.open_at + 1 :]
    member = f'\n{_INDENT}"{_KEY}": "{SHELL}"'
    if scan.empty:
        return f"{head}{member}\n{rest.lstrip()}"
    return f"{head}{member},{rest}"


def _scan(text: str, path: Path) -> _Scan:
    """Where the root object opens, whether it has members, and its top-level
    `shell`: the string value, _NOT_A_STRING, or None if there is no such key."""
    open_at = -1
    depth = 0
    members = 0
    shell: str | None = None
    i = 0
    while i < len(text):
        char = text[i]
        if char == '"':
            end = _string_end(text, i, path)
            after = _skip_trivia(text, end, path)
            if depth == 1 and text.startswith(":", after):
                members += 1
                if text[i + 1 : end - 1] == _KEY:
                    shell = _string_at(text, _skip_trivia(text, after + 1, path), path)
            i = end
        elif text.startswith(("//", "/*"), i):
            i = _skip_trivia(text, i, path)
        else:
            if char in "{[":
                if open_at < 0 and char == "{":
                    open_at = i
                depth += 1
            elif char in "}]":
                depth -= 1
            i += 1
    if open_at < 0 or depth != 0:
        raise SyncError(f"{path}: not a JSON object, left the file as is")
    return _Scan(open_at, members == 0, shell)


def _string_at(text: str, start: int, path: Path) -> str:
    """The raw content of the string that opens at start, else _NOT_A_STRING."""
    if text[start : start + 1] != '"':
        return _NOT_A_STRING
    return text[start + 1 : _string_end(text, start, path) - 1]


def _string_end(text: str, start: int, path: Path) -> int:
    """The index after the string that opens at start."""
    i = start + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
        elif text[i] == '"':
            return i + 1
        else:
            i += 1
    raise SyncError(f"{path}: a string is never closed, left the file as is")


def _skip_trivia(text: str, start: int, path: Path) -> int:
    """The index of the first character at or after start that is not
    whitespace or part of a comment."""
    i = start
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text.startswith("//", i):
            newline = text.find("\n", i)
            i = len(text) if newline < 0 else newline
        elif text.startswith("/*", i):
            close = text.find("*/", i + 2)
            if close < 0:
                raise SyncError(f"{path}: a comment is never closed, left the file as is")
            i = close + 2
        else:
            break
    return i
