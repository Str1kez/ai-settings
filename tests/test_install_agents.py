"""Agents: agents/<name>/AGENT.md is the only source. Claude Code gets a link
per agent, OpenCode an agent rendered from it."""

import os
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from aisettings.agents import Permission
from tests.helpers import (
    REPO_ROOT,
    copy_scripts,
    git_track,
    run_sync,
    run_unchecked,
    write,
)

FOREIGN_OPENCODE_AGENT = "---\ndescription: mine\nmode: subagent\n---\nMy prompt.\n"


def _repo_agents() -> dict[str, Path]:
    return {path.parent.name: path for path in sorted((REPO_ROOT / "agents").glob("*/AGENT.md"))}


def _split(path: Path) -> tuple[dict[str, Any], str]:
    """YAML frontmatter and body of a markdown agent."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    assert match, f"{path}: no frontmatter"
    return yaml.safe_load(match.group(1)), match.group(2)


def _opencode_agent(home: Path, name: str) -> Path:
    return home / ".config/opencode/agents" / f"{name}.md"


def test_every_repo_agent_is_a_marked_claude_render_on_the_session_model(
    installed_home: Path,
) -> None:
    claude_agents = installed_home / ".claude/agents"

    assert claude_agents.is_dir() and not claude_agents.is_symlink()
    for name, source in _repo_agents().items():
        path = claude_agents / f"{name}.md"
        rendered, prompt = _split(path)
        original, body = _split(source)

        assert not path.is_symlink()
        assert path.read_text(encoding="utf-8").startswith("---\n# managed-by: ai-settings\n")
        assert rendered["name"] == name
        assert rendered["description"] == original["description"].strip()
        assert rendered["model"] == "inherit"
        assert rendered.get("effort") == original.get("effort")
        assert prompt.strip() == body.strip()


def test_repo_templates_are_code_reviewer_and_coder_with_their_effort_and_tools(installed_home: Path) -> None:
    assert sorted(_repo_agents()) == ["code-reviewer", "coder"]

    reviewer, _ = _split(installed_home / ".claude/agents/code-reviewer.md")
    coder, _ = _split(installed_home / ".claude/agents/coder.md")

    assert reviewer["effort"] == "high"
    assert reviewer["tools"] == "Read, Grep, Glob, Bash, Skill"
    assert coder["effort"] == "medium"
    assert coder["tools"] == "Read, Grep, Glob, Bash, Edit, Write, Skill"


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


# The v2 `permissions` rules per repo agent, in render order: the source's
# tools mapped to actions, read-only roles with the explicit edit deny. Bash
# never yields a shell allow: the global ask/deny rules must stay the last
# word on the shell. Same Permission shape the renderer emits, so the fixture
# and the producer cannot drift.
OPENCODE_PERMISSIONS = {
    "code-reviewer": [
        Permission("read", "*", "allow"),
        Permission("grep", "*", "allow"),
        Permission("glob", "*", "allow"),
        Permission("skill", "*", "allow"),
        Permission("edit", "*", "deny"),
    ],
}


def _opencode_rules(path: Path) -> list[Permission]:
    """The `permissions` rules of a rendered opencode agent, in the same
    shape the renderer emits."""
    rendered, _ = _split(path)
    return [Permission(rule["action"], rule["resource"], rule["effect"]) for rule in rendered["permissions"]]


@pytest.mark.parametrize("name", sorted(OPENCODE_PERMISSIONS))
def test_opencode_agents_render_v2_permission_rules_per_role(installed_home: Path, name: str) -> None:
    assert _opencode_rules(_opencode_agent(installed_home, name)) == OPENCODE_PERMISSIONS[name]


@pytest.mark.parametrize("name", sorted(_repo_agents()))
def test_no_opencode_agent_gets_a_shell_allow(installed_home: Path, name: str) -> None:
    assert Permission("shell", "*", "allow") not in _opencode_rules(_opencode_agent(installed_home, name))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo with two agents and its own copy of the deploy scripts."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    for name in ("keeper", "goner"):
        write(
            repo / "agents" / name / "AGENT.md",
            f"---\nname: {name}\ndescription: Use for {name} work.\n"
            f"model: standard\ntools: [Read, Grep]\n---\n\n# {name}\n",
        )
    git_track(repo, "agents")
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
    assert (home / ".claude/agents/mine.md").resolve() == foreign_target


def test_links_into_the_repo_left_by_older_versions_make_way_for_the_renders(
    tmp_path: Path, repo: Path, home: Path
) -> None:
    foreign_target = tmp_path / "dotfiles/mine.md"
    write(foreign_target, "my agent\n")
    claude_agents = home / ".claude/agents"
    claude_agents.mkdir(parents=True)
    (claude_agents / "keeper.md").symlink_to(repo / "agents/keeper/AGENT.md")
    (claude_agents / "goner.md").symlink_to(repo / "agents/goner/AGENT.md")
    (claude_agents / "old-one.md").symlink_to(repo / "agents/old-one/AGENT.md")
    (claude_agents / "mine.md").symlink_to(foreign_target)

    run_sync(repo, home, "agents")

    assert sorted(os.listdir(claude_agents)) == ["goner.md", "keeper.md", "mine.md"]
    assert not (claude_agents / "keeper.md").is_symlink()
    assert not (claude_agents / "goner.md").is_symlink()
    assert (claude_agents / "mine.md").resolve() == foreign_target
    assert not (repo / "backups").exists()


def test_foreign_claude_agent_under_a_repo_agent_name_moves_to_backups(repo: Path, home: Path) -> None:
    write(home / ".claude/agents/keeper.md", FOREIGN_OPENCODE_AGENT)

    run_sync(repo, home, "agents")

    backups = sorted((repo / "backups").rglob("keeper.md"))
    assert [path.read_text(encoding="utf-8") for path in backups] == [FOREIGN_OPENCODE_AGENT]
    rendered, _ = _split(home / ".claude/agents/keeper.md")
    assert rendered["model"] == "inherit"


def test_foreign_opencode_agent_under_a_repo_agent_name_moves_to_backups(repo: Path, home: Path) -> None:
    write(_opencode_agent(home, "keeper"), FOREIGN_OPENCODE_AGENT)

    run_sync(repo, home, "agents")

    backups = sorted((repo / "backups").rglob("keeper.md"))
    assert [path.read_text(encoding="utf-8") for path in backups] == [FOREIGN_OPENCODE_AGENT]
    rendered, prompt = _split(_opencode_agent(home, "keeper"))
    assert rendered["description"] == "Use for keeper work."
    assert prompt.strip() == "# keeper"


def test_opencode_render_drops_the_legacy_list_tool(repo: Path, home: Path) -> None:
    # OpenCode v2 has no `list` action: the legacy List tool maps to nothing,
    # the rules for the remaining tools stay.
    write(
        repo / "agents/keeper/AGENT.md",
        "---\nname: keeper\ndescription: Use for keeper work.\nmodel: standard\ntools: [Read, List]\n---\n\n# keeper\n",
    )

    run_sync(repo, home, "agents")

    assert _opencode_rules(_opencode_agent(home, "keeper")) == [
        Permission("read", "*", "allow"),
        Permission("edit", "*", "deny"),
        Permission("shell", "*", "deny"),
    ]


# No repo agent calls these tools, so a broken mapping line would fail
# silently: a synthetic agent pins each one.
@pytest.mark.parametrize(
    ("tool", "action"),
    [("Task", "subagent"), ("Skill", "skill"), ("WebFetch", "webfetch"), ("WebSearch", "websearch")],
)
def test_opencode_maps_a_tool_no_repo_agent_uses_to_its_permission(
    repo: Path, home: Path, tool: str, action: str
) -> None:
    write(
        repo / "agents/keeper/AGENT.md",
        "---\nname: keeper\ndescription: Use for keeper work.\n"
        f"model: standard\ntools: [Read, {tool}]\n---\n\n# keeper\n",
    )

    run_sync(repo, home, "agents")

    assert Permission(action, "*", "allow") in _opencode_rules(_opencode_agent(home, "keeper"))


@pytest.mark.parametrize("agents_dir", [".codex/agents", ".gemini/agents", ".cursor/agents"])
def test_agents_are_not_rendered_for_codex_gemini_and_cursor(repo: Path, home: Path, agents_dir: str) -> None:
    run_sync(repo, home, "agents")

    assert not (home / agents_dir).exists()


def test_agent_whose_frontmatter_name_differs_from_its_dir_fails_the_sync(repo: Path, home: Path) -> None:
    write(
        repo / "agents/keeper/AGENT.md",
        "---\nname: keeper-v2\ndescription: Keeps.\nmodel: standard\ntools: [Read]\n---\n\nKeeps.\n",
    )

    result = run_unchecked(["python3", repo / "scripts/sync.py", "agents"], home)

    assert result.returncode != 0
    assert "keeper-v2" in result.stderr and "'keeper'" in result.stderr
    assert not (home / ".claude/agents").exists()
