import os
import subprocess
from pathlib import Path

from tests.helpers import REPO_ROOT, run, run_unchecked, tree
from tests.skill_lint.conftest import discover_skill_paths

INSTALL = REPO_ROOT / "scripts/install.sh"


def _repo_skills() -> dict[str, Path]:
    return {path.parent.name: path.parent for path in discover_skill_paths()}


def _repo_snapshot() -> tuple[str, list[str]]:
    """What git and backups/ show about the repo, to spot any write into it."""
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return status, sorted(os.listdir(REPO_ROOT / "backups")) if (
        REPO_ROOT / "backups"
    ).is_dir() else []


def test_every_repo_skill_is_linked_flat_into_claude_and_agents(
    installed_home: Path,
) -> None:
    skills = _repo_skills()

    assert "feature-architecture" in skills
    assert skills["feature-architecture"].parent.name == "strikez"
    for harness_skills in (
        installed_home / ".claude/skills",
        installed_home / ".agents/skills",
    ):
        assert harness_skills.is_dir() and not harness_skills.is_symlink()
        for name, skill_dir in skills.items():
            assert (harness_skills / name).resolve() == skill_dir


def test_install_generates_no_claude_command_shims(installed_home: Path) -> None:
    assert not (installed_home / ".claude/commands").exists()


def test_install_does_not_touch_the_repo(tmp_path: Path) -> None:
    before = _repo_snapshot()

    run([INSTALL], tmp_path)

    assert _repo_snapshot() == before


def test_second_install_changes_nothing(tmp_path: Path) -> None:
    run([INSTALL], tmp_path)
    first = [tree(tmp_path / rel) for rel in (".claude/skills", ".agents/skills")]

    run([INSTALL], tmp_path)

    assert first == [
        tree(tmp_path / rel) for rel in (".claude/skills", ".agents/skills")
    ]


def test_stale_link_into_repo_skills_is_removed_and_foreign_links_stay(
    tmp_path: Path,
) -> None:
    foreign_target = tmp_path / "elsewhere/matt-skill"
    foreign_target.mkdir(parents=True)
    for skills_home in (".claude/skills", ".agents/skills"):
        home_dir = tmp_path / skills_home
        home_dir.mkdir(parents=True)
        (home_dir / "ru-commit-message").symlink_to(
            REPO_ROOT / "skills/strikez/ru-commit-message"
        )
        (home_dir / "matt-skill").symlink_to(foreign_target)

    run([INSTALL], tmp_path)

    for skills_home in (".claude/skills", ".agents/skills"):
        assert not (tmp_path / skills_home / "ru-commit-message").is_symlink()
        assert (tmp_path / skills_home / "matt-skill").resolve() == foreign_target


def test_legacy_agents_skills_symlink_stops_before_any_claude_link(
    tmp_path: Path,
) -> None:
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents/skills").symlink_to(REPO_ROOT / "skills")

    result = run_unchecked(["python3", "scripts/sync.py", "skills"], tmp_path)

    assert result.returncode != 0
    assert not (tmp_path / ".claude/skills").exists()
