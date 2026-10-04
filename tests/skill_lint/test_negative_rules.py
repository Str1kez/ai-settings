"""Meta-test: the link and duplicate rules must fail on known-bad fixtures."""

from __future__ import annotations

from pathlib import Path

from tests.skill_lint.rules import Declaration, find_broken_links, find_duplicates
from tests.skill_lint.test_duplicates import _skill_declarations

FIXTURES = Path(__file__).parent / "fixtures"


def test_broken_links_fixture_reports_only_the_bad_references() -> None:
    root = FIXTURES / "broken-links"

    problems = find_broken_links(root / "SKILL.md", root, root)

    assert sorted(problems) == [
        "../bad-skill/SKILL.md: points outside the repo",
        "/etc/hosts: absolute path, use a relative one",
        "references/gone.md: not found",
        "references/missing.md: not found",
    ]


def test_duplicates_fixture_reports_name_agent_and_description_clashes() -> None:
    skill_files = sorted((FIXTURES / "duplicate-skills").rglob("SKILL.md"))
    agent = Declaration(
        name="gamma", description="", path=Path("agents/gamma/AGENT.md")
    )

    problems = find_duplicates(_skill_declarations(skill_files), [agent])

    assert len(problems) == 3
    assert any("skill name 'alpha' declared in" in p for p in problems)
    assert any("collides with agent agents/gamma/AGENT.md" in p for p in problems)
    assert any(
        "identical description in skills ['alpha', 'alpha', 'beta']" in p
        for p in problems
    )
