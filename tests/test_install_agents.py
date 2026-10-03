"""Agents: agents/<name>/AGENT.md is the only source. Claude Code gets a link
per agent, OpenCode a markdown agent rendered from it."""

import os
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.helpers import REPO_ROOT, copy_scripts, run_sync, write

FOREIGN_OPENCODE_AGENT = "---\ndescription: mine\nmode: subagent\n---\nMy prompt.\n"


def _repo_agents() -> dict[str, Path]:
    return {
        path.parent.name: path
        for path in sorted((REPO_ROOT / "agents").glob("*/AGENT.md"))
    }


def _split(path: Path) -> tuple[dict[str, Any], str]:
    """YAML frontmatter and body of a markdown agent."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    assert match, f"{path}: no frontmatter"
    return yaml.safe_load(match.group(1)), match.group(2)


def _opencode_agent(home: Path, name: str) -> Path:
    return home / ".config/opencode/agents" / f"{name}.md"


def test_every_repo_agent_is_linked_into_a_real_claude_agents_dir(
    installed_home: Path,
) -> None:
    claude_agents = installed_home / ".claude/agents"

    assert claude_agents.is_dir() and not claude_agents.is_symlink()
    for name, source in _repo_agents().items():
        assert (claude_agents / f"{name}.md").resolve() == source


def test_every_repo_agent_is_an_opencode_subagent_with_its_prompt(
    installed_home: Path,
) -> None:
    for name, source in _repo_agents().items():
        rendered, prompt = _split(_opencode_agent(installed_home, name))
        original, body = _split(source)

        assert rendered["mode"] == "subagent"
        assert rendered["description"] == original["description"].strip()
        # A subagent without a model runs on the model of its caller.
        assert "model" not in rendered
        assert prompt.strip() == body.strip()


@pytest.mark.parametrize(
    ("name", "edit"),
    [
        pytest.param("code-reviewer", "deny", id="code-reviewer"),
        pytest.param("pr-writer", "deny", id="pr-writer"),
        pytest.param("debugger", "allow", id="debugger"),
    ],
)
def test_only_agents_with_edit_or_write_can_edit_in_opencode(
    installed_home: Path, name: str, edit: str
) -> None:
    rendered, _ = _split(_opencode_agent(installed_home, name))

    assert rendered["permission"]["edit"] == edit


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo with two agents and its own copy of the deploy scripts."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    for name in ("keeper", "goner"):
        write(
            repo / "agents" / name / "AGENT.md",
            f"---\nname: {name}\ndescription: Use for {name} work.\n"
            f"model: sonnet\ntools: [Read, Grep]\n---\n\n# {name}\n",
        )
    return repo


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_agent_gone_from_the_repo_leaves_both_harnesses_and_foreign_ones_stay(
    tmp_path: Path, repo: Path, home: Path
) -> None:
    foreign_target = tmp_path / "dotfiles/mine.md"
    write(foreign_target, "my agent\n")
    (home / ".claude/agents").mkdir(parents=True)
    (home / ".claude/agents/mine.md").symlink_to(foreign_target)
    write(_opencode_agent(home, "mine"), FOREIGN_OPENCODE_AGENT)
    run_sync(repo, home, "agents")
    shutil.rmtree(repo / "agents/goner")

    run_sync(repo, home, "agents")

    assert sorted(os.listdir(home / ".claude/agents")) == ["keeper.md", "mine.md"]
    assert sorted(os.listdir(home / ".config/opencode/agents")) == [
        "keeper.md",
        "mine.md",
    ]
    mine = _opencode_agent(home, "mine").read_text(encoding="utf-8")
    assert mine == FOREIGN_OPENCODE_AGENT


def test_foreign_opencode_agent_under_a_repo_agent_name_moves_to_backups(
    repo: Path, home: Path
) -> None:
    write(_opencode_agent(home, "keeper"), FOREIGN_OPENCODE_AGENT)

    run_sync(repo, home, "agents")

    backups = sorted((repo / "backups").rglob("keeper.md"))
    assert [path.read_text(encoding="utf-8") for path in backups] == [
        FOREIGN_OPENCODE_AGENT
    ]
    rendered, prompt = _split(_opencode_agent(home, "keeper"))
    assert rendered["description"] == "Use for keeper work."
    assert prompt.strip() == "# keeper"
