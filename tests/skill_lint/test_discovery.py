"""skill-lint checks only SKILL.md files that git tracks."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.skill_lint.conftest import discover_skill_paths


def _write_skill(root: Path, rel: str) -> None:
    path = root / rel / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: x\n---\n", encoding="utf-8")


def test_untracked_and_ignored_skills_are_not_linted(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _write_skill(tmp_path, "skills/tracked")
    _write_skill(tmp_path, "skills/synced/untracked")
    _write_skill(tmp_path, "skills/ignored")
    (tmp_path / ".gitignore").write_text("/skills/ignored\n", encoding="utf-8")
    subprocess.run(["git", "add", "skills/tracked"], cwd=tmp_path, check=True)

    found = discover_skill_paths(tmp_path)

    assert found == [tmp_path / "skills/tracked/SKILL.md"]
