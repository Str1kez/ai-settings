"""Skills: skills/<skill>/ in the repo, linked under the same name in every
harness.

Claude Code reads ~/.claude/skills/<name>/SKILL.md; Codex, OpenCode, Gemini
CLI and Cursor read ~/.agents/skills/<name>/SKILL.md.
"""

from __future__ import annotations

from pathlib import Path

from aisettings import tracked
from aisettings.fs import Fs, SyncError, link_target

_HARNESS_SKILL_DIRS = (Path(".claude/skills"), Path(".agents/skills"))


def sync(fs: Fs, repo: Path, home: Path) -> None:
    skills = collect(repo)
    tracked.warn_untracked(repo, "skills", "SKILL.md")
    targets = [home / rel for rel in _HARNESS_SKILL_DIRS]
    # Check every target before the first link: no half-done skill deploy.
    for skills_home in targets:
        _refuse_repo_link(fs, skills_home)
    for skills_home in targets:
        _sync_dir(fs, repo, skills_home, skills)


def collect(repo: Path) -> dict[str, Path]:
    """Map skill name to its directory. Only git-tracked skills count: on a
    machine not yet migrated, skills/ still holds npx symlinks and Claude
    Code's own synced/ and .trash/."""
    return {d.name: d for d in tracked.tracked_dirs(repo, "skills", "SKILL.md")}


def _sync_dir(fs: Fs, repo: Path, skills_home: Path, skills: dict[str, Path]) -> None:
    for name, skill_dir in sorted(skills.items()):
        fs.link(skill_dir, skills_home / name)
    _remove_stale_links(fs, repo, skills_home, skills)


def _refuse_repo_link(fs: Fs, skills_home: Path) -> None:
    """A dir link into the repo would turn every skill link below it into a
    write to the repo."""
    if skills_home.is_symlink() and fs.inside_repo(skills_home):
        raise SyncError(
            f"{skills_home} is a symlink into the repo: replace it with a real "
            "directory, nothing was changed"
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
        if link_target(entry).is_relative_to(repo_skills):
            fs.unlink(entry)
