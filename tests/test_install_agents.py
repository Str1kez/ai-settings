"""Agents: agents/<name>/AGENT.md is the only source. Claude Code gets a link
per agent, the other harnesses an agent rendered from it."""

import os
import re
import shutil
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.helpers import REPO_ROOT, copy_scripts, run_sync, run_unchecked, write

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


def _toml_agent(home: Path, name: str) -> dict[str, Any]:
    path = home / ".codex/agents" / f"{name}.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_every_repo_agent_is_a_codex_toml_with_its_prompt(
    installed_home: Path,
) -> None:
    for name, source in _repo_agents().items():
        agent = _toml_agent(installed_home, name)
        original, body = _split(source)

        assert agent["name"] == name
        assert agent["description"] == original["description"].strip()
        assert agent["developer_instructions"].strip() == body.strip()


def test_every_repo_agent_is_a_gemini_and_a_cursor_agent_with_its_prompt(
    installed_home: Path,
) -> None:
    for name, source in _repo_agents().items():
        original, body = _split(source)
        for agents_dir in (".gemini/agents", ".cursor/agents"):
            rendered, prompt = _split(installed_home / agents_dir / f"{name}.md")

            assert rendered["name"] == name
            assert rendered["description"] == original["description"].strip()
            assert prompt.strip() == body.strip()
        cursor, _ = _split(installed_home / ".cursor/agents" / f"{name}.md")
        assert cursor["model"] == "inherit"


@pytest.mark.parametrize("name", ["code-reviewer", "pr-writer"])
def test_read_only_agents_cannot_write_in_codex_cursor_and_gemini(
    installed_home: Path, name: str
) -> None:
    gemini, _ = _split(installed_home / ".gemini/agents" / f"{name}.md")
    cursor, _ = _split(installed_home / ".cursor/agents" / f"{name}.md")

    assert _toml_agent(installed_home, name)["sandbox_mode"] == "read-only"
    assert cursor["readonly"] is True
    assert not {"replace", "write_file"} & set(gemini["tools"])


def test_agent_that_edits_is_not_read_only_and_has_gemini_edit_tools(
    installed_home: Path,
) -> None:
    gemini, _ = _split(installed_home / ".gemini/agents/debugger.md")
    cursor, _ = _split(installed_home / ".cursor/agents/debugger.md")

    assert "sandbox_mode" not in _toml_agent(installed_home, "debugger")
    assert "readonly" not in cursor
    assert "replace" in gemini["tools"]


@pytest.mark.parametrize(
    "foreign_path",
    [
        pytest.param(".codex/agents/{}.toml", id="codex"),
        pytest.param(".gemini/agents/{}.md", id="gemini"),
        pytest.param(".cursor/agents/{}.md", id="cursor"),
    ],
)
def test_render_of_an_agent_gone_from_the_repo_goes_and_foreign_file_stays(
    repo: Path, home: Path, foreign_path: str
) -> None:
    write(home / foreign_path.format("mine"), "mine\n")
    run_sync(repo, home, "agents")
    gone = home / foreign_path.format("goner")
    assert gone.is_file()
    shutil.rmtree(repo / "agents/goner")

    run_sync(repo, home, "agents")

    assert not gone.exists()
    assert (home / foreign_path.format("mine")).read_text(encoding="utf-8") == "mine\n"


def test_foreign_codex_agent_under_a_repo_agent_name_moves_to_backups(
    repo: Path, home: Path
) -> None:
    write(home / ".codex/agents/keeper.toml", 'name = "mine"\n')

    run_sync(repo, home, "agents")

    backups = sorted((repo / "backups").rglob("keeper.toml"))
    assert [path.read_text(encoding="utf-8") for path in backups] == ['name = "mine"\n']
    assert _toml_agent(home, "keeper")["name"] == "keeper"


def test_agent_prompt_with_toml_literal_quotes_fails_the_codex_sync(
    repo: Path, home: Path
) -> None:
    write(
        repo / "agents/keeper/AGENT.md",
        "---\nname: keeper\ndescription: Keeps.\ntools: [Read]\n---\n\nUse ''' here.\n",
    )

    result = run_unchecked(["python3", repo / "scripts/sync.py", "agents"], home)

    assert result.returncode != 0
    assert "keeper" in result.stderr
