"""Every relative link and bundled-file reference in a skill must resolve."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.skill_lint.conftest import REPO_ROOT
from tests.skill_lint.rules import find_broken_links


def _tracked_markdown(skill_dir: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=skill_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(skill_dir / rel for rel in result.stdout.split("\0") if rel)


def test_skill_links_resolve(skill_path: Path) -> None:
    skill_dir = skill_path.parent
    problems = [
        f"{md.relative_to(REPO_ROOT)}: {problem}"
        for md in _tracked_markdown(skill_dir)
        for problem in find_broken_links(md, skill_dir, REPO_ROOT)
    ]

    assert not problems, "\n".join(problems)
