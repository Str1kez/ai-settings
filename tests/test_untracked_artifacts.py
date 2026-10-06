"""Skills and agents deploy only when git tracks them. An untracked real dir
with a SKILL.md or AGENT.md looks like a forgotten `git add`, and sync.py says
so; what the old layout left in skills/ stays quiet."""

import os
from pathlib import Path

import pytest

from tests.helpers import copy_scripts, git_track, run_sync, write

SKILL = "---\nname: {name}\n---\n"
AGENT = "---\nname: {name}\ndescription: Use for work.\ntools: [Read]\n---\n\nBody.\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo with a tracked skill and a tracked agent."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    write(repo / "skills/tracked/SKILL.md", SKILL.format(name="tracked"))
    write(repo / "agents/tracked/AGENT.md", AGENT.format(name="tracked"))
    git_track(repo, "skills", "agents")
    return repo


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_untracked_skill_and_agent_are_warned_about_and_not_deployed(repo: Path, home: Path) -> None:
    write(repo / "skills/forgotten/SKILL.md", SKILL.format(name="forgotten"))
    write(repo / "agents/forgotten/AGENT.md", AGENT.format(name="forgotten"))

    log = run_sync(repo, home, "skills") + run_sync(repo, home, "agents")

    assert "skills/forgotten/SKILL.md is not tracked by git" in log
    assert "git add skills/forgotten" in log
    assert "agents/forgotten/AGENT.md is not tracked by git" in log
    assert sorted(os.listdir(home / ".claude/skills")) == ["tracked"]
    assert sorted(os.listdir(home / ".claude/agents")) == ["tracked.md"]
    assert sorted(os.listdir(home / ".config/opencode/agents")) == ["tracked.md"]


def test_staged_skill_is_deployed_without_a_warning(repo: Path, home: Path) -> None:
    write(repo / "skills/fresh/SKILL.md", SKILL.format(name="fresh"))
    git_track(repo, "skills/fresh")

    log = run_sync(repo, home, "skills")

    assert "not tracked" not in log
    assert sorted(os.listdir(home / ".claude/skills")) == ["fresh", "tracked"]


def test_leftovers_of_the_old_layout_in_skills_dir_raise_no_warning(tmp_path: Path, repo: Path, home: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    write(elsewhere / "SKILL.md", SKILL.format(name="npx"))
    (repo / "skills/npx").symlink_to(elsewhere)
    write(repo / "skills/synced/account/SKILL.md", "synced\n")
    write(repo / "skills/.trash/old/SKILL.md", "trashed\n")
    write(repo / ".gitignore", "skills/ignored/\n")
    write(repo / "skills/ignored/SKILL.md", "ignored\n")

    log = run_sync(repo, home, "skills")

    assert "not tracked" not in log
