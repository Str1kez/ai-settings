"""Rules: AGENTS.md and the docs/ai/ modules it imports.

Claude Code and Gemini CLI follow @imports themselves, so they get links into
the repo. Codex, OpenCode and Cursor don't, so they get a flat copy with every
import inlined.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from aisettings import log
from aisettings.fs import Fs, SyncError

# Only a whole line "@path/to/module.md" is an import.
_IMPORT_RE = re.compile(r"^@([./\w\-/]+\.md)\s*$", re.MULTILINE)
_CURSOR_RULE = Path(".cursor/rules/ai-settings.mdc")
_CURSOR_FRONTMATTER = "---\nalwaysApply: true\n---\n\n"


class _Flat(NamedTuple):
    text: str
    missing: list[str]


def sync(fs: Fs, repo: Path, home: Path) -> None:
    fs.link(repo / "CLAUDE.md", home / ".claude/CLAUDE.md")
    # GEMINI.md imports ./AGENTS.md, which resolves next to the link.
    fs.link(repo / "GEMINI.md", home / ".gemini/GEMINI.md")
    fs.link(repo / "AGENTS.md", home / ".gemini/AGENTS.md")

    flat = _flat_rules(repo)
    fs.write(home / ".codex/AGENTS.md", flat)
    fs.write(home / ".config/opencode/AGENTS.md", flat)
    fs.write(home / _CURSOR_RULE, _CURSOR_FRONTMATTER + flat)


def sync_cursor_project(fs: Fs, repo: Path, project: Path) -> None:
    fs.write(project / _CURSOR_RULE, _CURSOR_FRONTMATTER + _flat_rules(repo))


def check(repo: Path) -> None:
    source = _source(repo)
    flat = _flatten(source)
    if flat.missing:
        raise SyncError(f"{source}: missing imports: {', '.join(flat.missing)}")
    log.ok(f"resolved {source} ({len(flat.text)} chars)")


def _flat_rules(repo: Path) -> str:
    source = _source(repo)
    flat = _flatten(source)
    for rel in flat.missing:
        log.warn(f"{source}: missing import {rel}")
    return flat.text


def _source(repo: Path) -> Path:
    source = repo / "AGENTS.md"
    if not source.is_file():
        raise SyncError(f"source not found: {source}")
    return source


def _flatten(source: Path) -> _Flat:
    """Inline imports recursively. Each file goes in once; a repeated or missing
    import turns into an HTML comment."""
    seen: set[Path] = set()
    missing: list[str] = []

    def inline(text: str, base_dir: Path) -> str:
        def replace(match: re.Match[str]) -> str:
            rel = match.group(1)
            target = (base_dir / rel).resolve()
            if target in seen:
                return f"<!-- skipped cyclic import: {rel} -->"
            if not target.is_file():
                missing.append(rel)
                return f"<!-- missing import: {rel} -->"
            seen.add(target)
            return inline(target.read_text(encoding="utf-8"), target.parent)

        return _IMPORT_RE.sub(replace, text)

    return _Flat(inline(source.read_text(encoding="utf-8"), source.parent), missing)
