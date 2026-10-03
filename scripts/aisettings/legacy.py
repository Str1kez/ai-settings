"""One-off migrations from the old layout, where install.sh linked whole repo
dirs into harness homes and every tool that wrote there wrote into the repo.

Each migration looks for the old state and does nothing without it, so sync.py
runs them on every call. The module is temporary: it goes once both machines
have migrated (ADR 0001).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from aisettings.fs import Fs, SyncError, link_target

# What the old install.sh wrote to ~/.claude/commands/<ns>/<skill>.md for every
# skill: a command that only invokes the skill. Every version of the generator
# wrote exactly this, with " in the description replaced by '.
_SHIM_RE = re.compile(
    r'---\ndescription: "[^"\n]*"\n---\nInvoke the `(?P<skill>[^`\n]+)` skill\.\n'
)


def migrate_skills(fs: Fs, repo: Path, home: Path) -> None:
    migrate_dir_link(fs, repo, home / ".claude/skills", repo / "skills")
    # Claude Code serves every skill as /<name> itself now.
    _remove_command_shims(fs, home / ".claude/commands")
    # Gemini CLI reads ~/.agents/skills; this one pointed at Superpowers.
    _remove_repo_link(fs, repo, home / ".gemini/skills")


def migrate_dir_link(fs: Fs, repo: Path, link: Path, source: Path) -> None:
    """Turn link, an old symlink to the repo dir source, into a real dir.

    What harness tools wrote through the link sits in source untracked by git;
    it moves into the new dir. Tracked entries stay in the repo.
    """
    fs.finish_link_replacement(link)
    if not link.is_symlink() or link.resolve() != source.resolve():
        return
    fs.replace_link_with_dir(link, _untracked_entries(repo, source))


def _untracked_entries(repo: Path, source: Path) -> list[Path]:
    """Top-level entries of source that hold no file git tracks."""
    if not source.is_dir():
        return []
    rel = source.relative_to(repo).as_posix()
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", rel],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SyncError(
            f"can't list tracked files in {source} with git: {exc}"
        ) from exc
    tracked = {
        Path(path).relative_to(rel).parts[0]
        for path in result.stdout.split("\0")
        if path
    }
    return sorted(entry for entry in source.iterdir() if entry.name not in tracked)


def _remove_repo_link(fs: Fs, repo: Path, link: Path) -> None:
    """Remove link if it points into the repo itself. A link to another link
    that leads into the repo is the user's."""
    if link.is_symlink() and link_target(link).is_relative_to(repo):
        fs.unlink(link)


def _remove_command_shims(fs: Fs, commands: Path) -> None:
    """Remove generated shims and the namespace dirs they leave empty.
    Any other file in commands/ is the user's and stays."""
    if not commands.is_dir():
        return
    for ns_dir in sorted(commands.iterdir()):
        if ns_dir.is_symlink() or not ns_dir.is_dir():
            continue
        entries = sorted(ns_dir.iterdir())
        shims = [entry for entry in entries if _is_shim(entry)]
        for shim in shims:
            fs.remove_file(shim)
        if shims and len(shims) == len(entries):
            fs.remove_empty_dir(ns_dir)


def _is_shim(path: Path) -> bool:
    if path.suffix != ".md" or path.is_symlink() or not path.is_file():
        return False
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return False
    match = _SHIM_RE.fullmatch(text)
    return match is not None and match["skill"] == f"{path.parent.name}:{path.stem}"
