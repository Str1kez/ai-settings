"""Migration from the old layout: ~/.claude/skills linked to the repo's skills/,
so every tool that installs skills for Claude Code wrote into the repo.

These tests run a copy of sync.py in a throwaway git repo. The migration moves
whatever git doesn't track out of skills/, and in the real repo that is the
user's own foreign skills.
"""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.helpers import copy_scripts, run_sync, tree, write

TRACKED_SKILL = "---\nname: tracked-skill\n---\n"
# Where the migration gathers entries before the new dir takes the link's
# place. Its error message names it, so it's part of what the user sees.
STAGING = ".claude/.skills.ai-settings-migration"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo with one tracked skill and its own copy of the deploy scripts."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    write(repo / "skills/ns/tracked-skill/SKILL.md", TRACKED_SKILL)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "skills"], cwd=repo, check=True)
    return repo


@pytest.fixture
def home(tmp_path: Path, repo: Path) -> Path:
    """HOME on the old layout, with what tools wrote into the repo through it."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude/skills").symlink_to(repo / "skills")
    matt = home / ".agents/skills/matt"
    matt.mkdir(parents=True)
    # npx skills writes the link relative to the real dir it lands in.
    (repo / "skills/matt").symlink_to(os.path.relpath(matt, repo / "skills"))
    write(repo / "skills/synced/account-skill/SKILL.md", "synced\n")
    write(repo / "skills/.trash/old-skill/SKILL.md", "trashed\n")
    # A link to another entry that moves too.
    (repo / "skills/pinned").symlink_to("synced/account-skill")
    return home


def _shim(skill_ref: str) -> str:
    """A command exactly as the old install.sh generated it for a skill."""
    return (
        "---\n"
        "description: \"Use when the user asks 'обнови changelog'\"\n"
        "---\n"
        f"Invoke the `{skill_ref}` skill.\n"
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _planned(plan: list[str], action: str, path: Path) -> bool:
    return any(f"{action} {path}" in line for line in plan)


def test_old_skills_link_becomes_a_real_dir_with_everything_git_does_not_track(
    repo: Path, home: Path
) -> None:
    run_sync(repo, home, "skills")

    claude_skills = home / ".claude/skills"
    assert claude_skills.is_dir() and not claude_skills.is_symlink()
    assert (claude_skills / "matt").resolve() == home / ".agents/skills/matt"
    assert _read(claude_skills / "synced/account-skill/SKILL.md") == "synced\n"
    assert _read(claude_skills / ".trash/old-skill/SKILL.md") == "trashed\n"
    pinned = (claude_skills / "pinned").resolve()
    assert pinned == claude_skills / "synced/account-skill"
    assert os.listdir(repo / "skills") == ["ns"]
    assert _read(repo / "skills/ns/tracked-skill/SKILL.md") == TRACKED_SKILL
    for skills_home in (".claude/skills", ".agents/skills"):
        linked = home / skills_home / "tracked-skill"
        assert linked.resolve() == repo / "skills/ns/tracked-skill"


def test_second_run_changes_nothing(repo: Path, home: Path) -> None:
    run_sync(repo, home, "skills")
    first = tree(home), tree(repo / "skills")

    run_sync(repo, home, "skills")

    assert (tree(home), tree(repo / "skills")) == first


def _stop_after_first_move(repo: Path, home: Path) -> None:
    """The first entry reached the staging dir; the old link is still there."""
    (home / STAGING).mkdir()
    (repo / "skills/.trash").rename(home / STAGING / ".trash")


def _stop_before_swap(repo: Path, home: Path) -> None:
    """Every entry reached the staging dir; the old link is already gone."""
    run_sync(repo, home, "skills")
    (home / ".claude/skills").rename(home / STAGING)


@pytest.mark.parametrize(
    "stop",
    [
        pytest.param(_stop_after_first_move, id="after-first-move"),
        pytest.param(_stop_before_swap, id="before-swap"),
    ],
)
def test_rerun_finishes_a_migration_that_stopped_halfway(
    repo: Path, home: Path, stop: Callable[[Path, Path], None]
) -> None:
    stop(repo, home)

    run_sync(repo, home, "skills")

    claude_skills = home / ".claude/skills"
    assert claude_skills.is_dir() and not claude_skills.is_symlink()
    assert not (home / STAGING).exists()
    assert _read(claude_skills / ".trash/old-skill/SKILL.md") == "trashed\n"
    assert _read(claude_skills / "synced/account-skill/SKILL.md") == "synced\n"
    assert (claude_skills / "matt").resolve() == home / ".agents/skills/matt"
    assert os.listdir(repo / "skills") == ["ns"]


def test_only_exact_generated_shims_are_removed(repo: Path, home: Path) -> None:
    commands = home / ".claude/commands"
    write(commands / "ns/tracked-skill.md", _shim("ns:tracked-skill"))
    write(commands / "ns/alias.md", _shim("ns:tracked-skill"))
    write(commands / "ns/edited.md", _shim("ns:edited") + "Then commit.\n")
    write(commands / "old/gone.md", _shim("old:gone"))

    run_sync(repo, home, "skills")

    assert tree(commands) == {
        "ns": "dir",
        "ns/alias.md": "file",
        "ns/edited.md": "file",
    }


@pytest.mark.parametrize(
    ("target", "removed"),
    [
        # The old install.sh linked Gemini to Superpowers, gone from the repo.
        pytest.param("repo/skills/superpowers", True, id="into-repo"),
        pytest.param("home/.agents/skills", False, id="elsewhere"),
    ],
)
def test_gemini_skills_link_goes_only_if_it_points_into_the_repo(
    tmp_path: Path, repo: Path, home: Path, target: str, removed: bool
) -> None:
    gemini_skills = home / ".gemini/skills"
    gemini_skills.parent.mkdir()
    gemini_skills.symlink_to(tmp_path / target)

    run_sync(repo, home, "skills")

    assert os.path.lexists(gemini_skills) is not removed


def test_dry_run_lists_moves_and_removals_and_changes_nothing(
    repo: Path, home: Path
) -> None:
    shim = home / ".claude/commands/ns/tracked-skill.md"
    write(shim, _shim("ns:tracked-skill"))
    (home / ".gemini").mkdir()
    (home / ".gemini/skills").symlink_to(repo / "skills/superpowers")
    before = tree(home), tree(repo / "skills")

    log = run_sync(repo, home, "skills", "--dry-run")

    assert (tree(home), tree(repo / "skills")) == before
    plan = [line for line in log.splitlines() if line.startswith("[dry-run]")]
    for moved in ("matt", "synced", ".trash", "pinned"):
        assert _planned(plan, "would move", repo / "skills" / moved)
    assert _planned(plan, "would remove", shim)
    assert _planned(plan, "would remove", home / ".gemini/skills")
    # The rest of the plan is made against the migrated layout.
    assert _planned(plan, "would link", home / ".claude/skills/tracked-skill")
