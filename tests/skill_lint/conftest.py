"""Pytest configuration and fixtures for skill-lint."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def discover_skill_paths(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Find every git-tracked SKILL.md under skills/.

    skills/ also holds untracked entries (npx symlinks, Claude Code's synced/
    and .trash/) that are not ours to lint.
    """
    # Plain pathspec (no ":(glob)" magic): "*" crosses "/", so this matches
    # SKILL.md at any depth under skills/.
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "skills/**/SKILL.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(repo_root / rel for rel in result.stdout.split("\0") if rel)


@pytest.fixture(
    params=discover_skill_paths(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def skill_path(request: pytest.FixtureRequest) -> Path:
    return request.param


@pytest.fixture
def skill_text(skill_path: Path) -> str:
    return skill_path.read_text(encoding="utf-8")


@pytest.fixture
def skill_frontmatter(skill_text: str) -> dict:
    """Parse YAML frontmatter from SKILL.md."""
    match = re.match(r"^---\n(.*?)\n---\n", skill_text, re.DOTALL)
    if not match:
        pytest.fail("No YAML frontmatter found")
    return yaml.safe_load(match.group(1))
