"""Skills must not duplicate each other or shadow an agent."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.skill_lint.conftest import REPO_ROOT, discover_skill_paths
from tests.skill_lint.rules import Declaration, find_duplicates, parse_frontmatter


def _skill_declarations(skill_paths: list[Path]) -> list[Declaration]:
    declarations = []
    for path in skill_paths:
        frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        declarations.append(
            Declaration(
                name=str(frontmatter.get("name", "")),
                description=str(frontmatter.get("description", "")),
                path=path,
            )
        )
    return declarations


def _agent_declarations(repo_root: Path) -> list[Declaration]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "agents/*/AGENT.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        Declaration(name=path.parent.name, description="", path=path)
        for path in sorted(repo_root / rel for rel in result.stdout.split("\0") if rel)
    ]


def test_no_duplicate_skills_or_agent_name_collisions() -> None:
    skills = _skill_declarations(discover_skill_paths())
    agents = _agent_declarations(REPO_ROOT)

    problems = find_duplicates(skills, agents)

    assert not problems, "\n".join(problems)
