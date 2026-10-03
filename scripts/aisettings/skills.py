"""Skills: skills/<namespace>/<skill>/ in the repo, flat in every harness.

The namespace only groups skills in the repo. Claude Code reads
~/.claude/skills/<name>/SKILL.md; Codex, OpenCode, Gemini CLI and Cursor read
~/.agents/skills/<name>/SKILL.md. The name is the same everywhere, so it has
to be unique across namespaces.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from aisettings.fs import Fs, SyncError

_SKILL_PATHSPEC = "skills/*/*/SKILL.md"
# <namespace>/<skill>/SKILL.md below skills/; "*" in a pathspec crosses "/".
_SKILL_FILE_DEPTH_IN_SKILLS = 3
_HARNESS_SKILL_DIRS = (Path(".claude/skills"), Path(".agents/skills"))


def sync(fs: Fs, repo: Path, home: Path) -> None:
    skills = collect(repo)
    targets = [home / rel for rel in _HARNESS_SKILL_DIRS]
    # Check every target before the first write: no half-done deploy.
    for skills_home in targets:
        _refuse_legacy_layout(repo, skills_home)
    for skills_home in targets:
        _sync_dir(fs, repo, skills_home, skills)


def collect(repo: Path) -> dict[str, Path]:
    """Map skill name to its directory. Only git-tracked skills count: skills/
    also holds npx symlinks and Claude Code's own synced/ and .trash/."""
    by_name: dict[str, list[Path]] = {}
    for skill_dir in _tracked_skill_dirs(repo):
        by_name.setdefault(skill_dir.name, []).append(skill_dir)
    duplicates = {name: dirs for name, dirs in by_name.items() if len(dirs) > 1}
    if duplicates:
        lines = [
            f"  {name}: {', '.join(str(d.relative_to(repo)) for d in dirs)}"
            for name, dirs in sorted(duplicates.items())
        ]
        raise SyncError("duplicate skill names:\n" + "\n".join(lines))
    return {name: dirs[0] for name, dirs in by_name.items()}


def _tracked_skill_dirs(repo: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", _SKILL_PATHSPEC],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SyncError(f"can't list tracked skills with git: {exc}") from exc
    files = (Path(rel) for rel in result.stdout.split("\0") if rel)
    return sorted(
        repo / f.parent
        for f in files
        if len(f.relative_to("skills").parts) == _SKILL_FILE_DEPTH_IN_SKILLS
    )


def _sync_dir(fs: Fs, repo: Path, skills_home: Path, skills: dict[str, Path]) -> None:
    for name, skill_dir in sorted(skills.items()):
        fs.link(skill_dir, skills_home / name)
    _remove_stale_links(fs, repo, skills_home, skills)


def _refuse_legacy_layout(repo: Path, skills_home: Path) -> None:
    if skills_home.is_symlink() and skills_home.resolve().is_relative_to(repo):
        raise SyncError(
            f"{skills_home} is a symlink into the repo (old layout): "
            "migrate it to a real directory first, nothing was changed"
        )


def _remove_stale_links(
    fs: Fs, repo: Path, skills_home: Path, skills: dict[str, Path]
) -> None:
    """Drop links that point into repo/skills/ but belong to no current skill,
    e.g. a skill that was renamed or deleted. Links elsewhere aren't ours."""
    if not skills_home.is_dir():
        return
    repo_skills = repo / "skills"
    for entry in sorted(skills_home.iterdir()):
        if not entry.is_symlink() or entry.name in skills:
            continue
        target = Path(os.path.normpath(skills_home / os.readlink(entry)))
        if target.is_relative_to(repo_skills):
            fs.unlink(entry)
