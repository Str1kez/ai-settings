"""bump-skill-version.sh raises the version and adds the changelog entry, or
changes nothing."""

import subprocess
from pathlib import Path

import pytest

from tests.helpers import REPO_ROOT, write

SCRIPT = REPO_ROOT / "scripts/bump-skill-version.sh"


def _skill(tmp_path: Path, changelog: str) -> Path:
    skill = tmp_path / "skills/demo"
    write(skill / "SKILL.md", "---\nname: demo\nversion: 1.0.0\n---\n")
    write(skill / "CHANGELOG.md", changelog)
    return skill


def _bump(skill: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", SCRIPT, skill, "patch", "--note", "fix"],
        capture_output=True,
        text=True,
        check=False,
        env={"PYTHONDONTWRITEBYTECODE": "1"},
    )


@pytest.mark.parametrize("header", ["# CHANGELOG — demo", "# Changelog"], ids=["upper", "title-case"])
def test_bump_adds_the_entry_whatever_the_header_case(tmp_path: Path, header: str) -> None:
    skill = _skill(tmp_path, f"{header}\n\n## [1.0.0] — 2026-10-04\n\n- first\n")

    result = _bump(skill)

    assert result.returncode == 0, result.stderr
    assert "version: 1.0.1" in (skill / "SKILL.md").read_text(encoding="utf-8")
    assert "## [1.0.1]" in (skill / "CHANGELOG.md").read_text(encoding="utf-8")


def test_bump_leaves_the_version_alone_when_the_entry_has_no_place(
    tmp_path: Path,
) -> None:
    skill = _skill(tmp_path, "no header here\n")

    result = _bump(skill)

    assert result.returncode != 0
    assert "CHANGELOG" in result.stderr
    assert "version: 1.0.0" in (skill / "SKILL.md").read_text(encoding="utf-8")
