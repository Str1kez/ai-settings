"""Migration from the old agent layout: ~/.claude/agents linked to the repo's
agents/, and OpenCode got the agents merged into opencode.jsonc with their
prompts in agent-prompts/.

These tests run a copy of sync.py in a throwaway git repo. The migration moves
whatever git doesn't track out of agents/, and in the real repo that is the
user's own files.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.helpers import copy_scripts, run_sync, tree, write

# Agent name -> tools in its AGENT.md.
AGENTS = {
    "code-reviewer": "Read, Bash",
    "debugger": "Read, Edit",
    "pr-writer": "Read, Bash",
}
# An agent the old merge wrote that is gone from the repo since.
GONE_AGENT = "next-frontend"
# What Claude Code's /agents wrote into the repo through the old link.
MY_AGENT = "---\nname: my-agent\ndescription: Mine.\n---\nMy prompt.\n"
MCP = {"context7": {"type": "remote", "url": "https://mcp.context7.com/mcp"}}
PROVIDER = {"anthropic": {"options": {"timeout": 600000}}}
MY_OPENCODE_AGENT = {
    "description": "Mine",
    "mode": "primary",
    "prompt": "{file:./prompts/mine.md}",
}


def _merged(name: str, permission: dict[str, str]) -> dict[str, object]:
    """An agent entry exactly as the old install.sh merged it."""
    return {
        "description": f"Use for {name} work.",
        "mode": "subagent",
        "permission": permission,
        "prompt": f"{{file:./agent-prompts/{name}.md}}",
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo with tracked agents and its own copy of the deploy scripts."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    for name, tools in AGENTS.items():
        write(
            repo / "agents" / name / "AGENT.md",
            f"---\nname: {name}\ndescription: Use for {name} work.\n"
            f"model: sonnet\ntools: [{tools}]\n---\n\n# {name}\n",
        )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "agents"], cwd=repo, check=True)
    return repo


@pytest.fixture
def dotfiles_config(tmp_path: Path) -> Path:
    """opencode.jsonc in the user's dotfiles, with what the old merge left."""
    config = tmp_path / "dotfiles/opencode.jsonc"
    legacy = {
        "$schema": "https://opencode.ai/config.json",
        "mcp": MCP,
        "provider": PROVIDER,
        "agent": {
            "code-reviewer": {
                **_merged(
                    "code-reviewer",
                    # The merge was deep: webfetch, the user's own key,
                    # survived it.
                    {
                        "read": "allow",
                        "bash": "allow",
                        "edit": "deny",
                        "webfetch": "deny",
                    },
                ),
                "model": "anthropic/claude-opus-4-1",
            },
            "debugger": _merged(
                "debugger", {"read": "allow", "edit": "allow", "bash": "deny"}
            ),
            # The user's own setting for one of our agents: the old merge
            # didn't write it, there is no prompt pointer.
            "pr-writer": {"permission": {"bash": "ask"}},
            GONE_AGENT: _merged(GONE_AGENT, {"read": "allow", "edit": "allow"}),
            "my-agent": MY_OPENCODE_AGENT,
        },
    }
    write(config, json.dumps(legacy, indent=2) + "\n")
    return config


@pytest.fixture
def home(tmp_path: Path, repo: Path, dotfiles_config: Path) -> Path:
    """HOME on the old layout, with what tools wrote into the repo through it."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude/agents").symlink_to(repo / "agents")
    write(repo / "agents/my-agent.md", MY_AGENT)
    opencode = home / ".config/opencode"
    opencode.mkdir(parents=True)
    (opencode / "opencode.jsonc").symlink_to(dotfiles_config)
    for name in [*AGENTS, GONE_AGENT]:
        write(opencode / "agent-prompts" / f"{name}.md", f"# {name}\n")
    return home


def _snapshot(home: Path, repo: Path, config: Path) -> tuple[object, ...]:
    return tree(home), tree(repo / "agents"), config.read_text(encoding="utf-8")


def _planned(plan: list[str], action: str, path: Path) -> bool:
    return any(f"{action} {path}" in line for line in plan)


def test_old_agents_link_becomes_a_real_dir_with_what_git_does_not_track(
    repo: Path, home: Path
) -> None:
    run_sync(repo, home, "agents")

    claude_agents = home / ".claude/agents"
    assert claude_agents.is_dir() and not claude_agents.is_symlink()
    assert (claude_agents / "my-agent.md").read_text(encoding="utf-8") == MY_AGENT
    assert sorted(os.listdir(repo / "agents")) == sorted(AGENTS)
    for name in AGENTS:
        linked = (claude_agents / f"{name}.md").resolve()
        assert linked == repo / "agents" / name / "AGENT.md"


def test_old_merge_leaves_opencode_config_and_only_the_users_fields_stay(
    repo: Path, home: Path, dotfiles_config: Path
) -> None:
    run_sync(repo, home, "agents")

    assert (home / ".config/opencode/opencode.jsonc").is_symlink()
    assert json.loads(dotfiles_config.read_text(encoding="utf-8")) == {
        "$schema": "https://opencode.ai/config.json",
        "mcp": MCP,
        "provider": PROVIDER,
        "agent": {
            "code-reviewer": {
                "model": "anthropic/claude-opus-4-1",
                "permission": {"webfetch": "deny"},
            },
            "pr-writer": {"permission": {"bash": "ask"}},
            "my-agent": MY_OPENCODE_AGENT,
        },
    }
    assert not (home / ".config/opencode/agent-prompts").exists()


def test_opencode_config_with_comments_is_left_alone_with_a_warning(
    repo: Path, home: Path, dotfiles_config: Path
) -> None:
    commented = (
        "{\n"
        "  // Agents from ai-settings\n"
        '  "agent": {\n'
        '    "code-reviewer": {\n'
        '      "mode": "subagent",\n'
        '      "prompt": "{file:./agent-prompts/code-reviewer.md}"\n'
        "    }\n"
        "  }\n"
        "}\n"
    )
    write(dotfiles_config, commented)

    log = run_sync(repo, home, "agents")

    assert dotfiles_config.read_text(encoding="utf-8") == commented
    # The config still points at it, and OpenCode fails on a missing file.
    assert (home / ".config/opencode/agent-prompts/code-reviewer.md").is_file()
    warnings = [line for line in log.splitlines() if line.startswith("[warn]")]
    assert any(str(home / ".config/opencode/opencode.jsonc") in w for w in warnings)


def test_second_run_changes_nothing(
    repo: Path, home: Path, dotfiles_config: Path
) -> None:
    run_sync(repo, home, "agents")
    first = _snapshot(home, repo, dotfiles_config)

    run_sync(repo, home, "agents")

    assert _snapshot(home, repo, dotfiles_config) == first


def test_dry_run_lists_the_migration_and_changes_nothing(
    repo: Path, home: Path, dotfiles_config: Path
) -> None:
    before = _snapshot(home, repo, dotfiles_config)

    log = run_sync(repo, home, "agents", "--dry-run")

    assert _snapshot(home, repo, dotfiles_config) == before
    plan = [line for line in log.splitlines() if line.startswith("[dry-run]")]
    opencode = home / ".config/opencode"
    assert _planned(plan, "would move", repo / "agents/my-agent.md")
    assert _planned(plan, "would update", opencode / "opencode.jsonc")
    for name in [*AGENTS, GONE_AGENT]:
        prompt = opencode / "agent-prompts" / f"{name}.md"
        assert _planned(plan, "would remove", prompt)
    # The rest of the plan is made against the migrated layout.
    assert _planned(plan, "would link", home / ".claude/agents/code-reviewer.md")
    assert _planned(plan, "would write", opencode / "agents/code-reviewer.md")
