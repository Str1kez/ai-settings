"""Agent-lint: every agent under agents/ passes, and the lint catches what it
claims to."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.agent_lint.rules import REPO_ROOT, discover_agent_dirs, problems
from tests.helpers import write

GOOD = """\
---
name: sample
description: |
  Use when the user asks for a sample, or when a sample is missing in the repo.
  SKIP: when the sample already exists and nobody asked to change it.
model: sonnet
tools: [Read, Grep]
---

# Role

Sample agent.
"""


@pytest.fixture(params=discover_agent_dirs(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def agent_dir(request: pytest.FixtureRequest) -> Path:
    path: Path = request.param
    return path


def test_repo_agent_passes_the_lint(agent_dir: Path) -> None:
    assert problems(agent_dir) == []


def _sample(tmp_path: Path, text: str) -> Path:
    agent_dir = tmp_path / "sample"
    write(agent_dir / "AGENT.md", text)
    return agent_dir


def test_a_well_formed_agent_passes(tmp_path: Path) -> None:
    assert problems(_sample(tmp_path, GOOD)) == []


@pytest.mark.parametrize(
    ("broken", "expected"),
    [
        pytest.param(GOOD.replace("name: sample", "name: other"), "must equal", id="name"),
        pytest.param(GOOD.replace("Use when", "When"), "when to use", id="trigger"),
        pytest.param(GOOD.replace("SKIP", "NOPE"), "SKIP", id="skip"),
        pytest.param(
            GOOD.replace("when the sample already exists", "<when not to call>"),
            "placeholder",
            id="placeholder",
        ),
        pytest.param(GOOD.replace("[Read, Grep]", "[Read, Bsh]"), "unknown tools", id="tools"),
        pytest.param(
            GOOD.replace("description: |", "description: >-"),
            "differently from YAML",
            id="yaml-subset",
        ),
        pytest.param(GOOD.split("---\n")[0] + "no frontmatter", "frontmatter", id="fm"),
        pytest.param(GOOD.replace("Sample agent.", "Use ''' here."), "'''", id="toml"),
    ],
)
def test_lint_catches_a_broken_agent(tmp_path: Path, broken: str, expected: str) -> None:
    found = problems(_sample(tmp_path, broken))

    assert any(expected in problem for problem in found), found


def test_agent_dir_without_agent_md_is_reported(tmp_path: Path) -> None:
    (tmp_path / "sample").mkdir()

    assert any("missing" in problem for problem in problems(tmp_path / "sample"))
