"""Claude Code: settings.json takes from the template what the installer owns
and keeps the rest; the hook scripts the template runs are linked one by one
into ~/.claude/hooks."""

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from tests.helpers import (
    REPO_ROOT,
    copy_scripts,
    run,
    run_sync,
    run_unchecked,
    tree,
    write,
)
from tests.skill_lint.conftest import discover_skill_paths

SCHEMA = "https://json.schemastore.org/claude-code-settings"
BANNER = "~/.claude/hooks/banner.sh"
RTK = "rtk hook claude"
AGTERM = "'/Users/me/.config/agterm/agent-status/agterm-agent-status.sh'"


def _command(command: str) -> dict[str, str]:
    return {"type": "command", "command": command}


TEMPLATE = {
    "$schema": SCHEMA,
    "permissions": {
        "allow": ["Read(**)", "Bash(.venv/bin/pytest:*)"],
        "ask": ["Bash(git commit:*)"],
        "deny": ["Bash(rm -rf*)"],
    },
    "hooks": {
        "SessionStart": [{"hooks": [_command(BANNER)]}],
        "PreToolUse": [{"matcher": "Bash", "hooks": [_command(RTK)]}],
    },
}
# What agterm adds to settings.json, the installer leaves it alone.
AGTERM_HOOKS = {
    "Notification": [
        {"matcher": "permission_prompt", "hooks": [_command(f"{AGTERM} blocked")]}
    ],
    "PostToolUse": [{"hooks": [_command(f"{AGTERM} active --blink")]}],
    "Stop": [{"hooks": [_command(f"{AGTERM} completed --auto-reset")]}],
}
LIVE = {
    "$schema": SCHEMA,
    "env": {"DISABLE_TELEMETRY": "1"},
    "permissions": {
        "allow": ["Read(**)", "Bash(rtk gain:*)", "Bash(uv run:*)"],
        "deny": ["Bash(rm -rf*)"],
        "ask": ["Bash(git commit:*)", "Write(**)", "Edit(**)"],
        "defaultMode": "acceptEdits",
    },
    "model": "sonnet",
    "hooks": {
        **AGTERM_HOOKS,
        "PreToolUse": [
            # The user's own Bash hook shares a group with the installer's.
            {"matcher": "Bash", "hooks": [_command(RTK), _command("my-audit.sh")]},
            {"matcher": "Bash", "hooks": [_command(RTK)]},
        ],
        "SessionStart": [{"hooks": [_command(BANNER)]}],
    },
    "enabledPlugins": {"pyright-lsp@claude-plugins-official": True},
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo with the template above, the script it runs and its own copy of
    the deploy scripts."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    write(repo / "settings/claude-settings.json", json.dumps(TEMPLATE, indent=4))
    write(repo / "settings/hooks/banner.sh", "#!/bin/sh\necho banner\n")
    return repo


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def _write_settings(home: Path, settings: dict[str, Any]) -> Path:
    path = home / ".claude/settings.json"
    write(path, json.dumps(settings, indent=2) + "\n")
    return path


def _settings(home: Path) -> Any:
    return json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))


def test_merge_takes_permissions_from_the_template_and_keeps_the_rest(
    repo: Path, home: Path
) -> None:
    _write_settings(home, LIVE)

    run_sync(repo, home, "claude")

    assert _settings(home) == {
        "$schema": SCHEMA,
        "env": {"DISABLE_TELEMETRY": "1"},
        "permissions": {
            "allow": ["Read(**)", "Bash(.venv/bin/pytest:*)"],
            "deny": ["Bash(rm -rf*)"],
            "ask": ["Bash(git commit:*)"],
            "defaultMode": "acceptEdits",
        },
        "model": "sonnet",
        "hooks": {
            **AGTERM_HOOKS,
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [_command("my-audit.sh")]},
                {"matcher": "Bash", "hooks": [_command(RTK)]},
            ],
            "SessionStart": [{"hooks": [_command(BANNER)]}],
        },
        "enabledPlugins": {"pyright-lsp@claude-plugins-official": True},
    }


def test_hook_of_a_script_the_template_dropped_goes_and_the_users_scripts_stay(
    repo: Path, home: Path
) -> None:
    hooks = home / ".claude/hooks"
    hooks.mkdir(parents=True)
    # Linked by an earlier run, when the template still ran gone.sh.
    (hooks / "gone.sh").symlink_to(repo / "settings/hooks/gone.sh")
    write(hooks / "mine.sh", "#!/bin/sh\n")
    users_hooks = {
        "Stop": [{"hooks": [_command("~/.claude/hooks/mine.sh --quiet")]}],
        # settings.json came from dotfiles, the script isn't on this machine yet.
        "Notification": [{"hooks": [_command("~/.claude/hooks/elsewhere.sh")]}],
    }
    _write_settings(
        home,
        {
            "hooks": {
                "UserPromptSubmit": [{"hooks": [_command("~/.claude/hooks/gone.sh")]}],
                **users_hooks,
            }
        },
    )

    run_sync(repo, home, "claude")

    assert _settings(home)["hooks"] == {**users_hooks, **TEMPLATE["hooks"]}
    assert sorted(os.listdir(hooks)) == ["banner.sh", "mine.sh"]
    assert (hooks / "banner.sh").resolve() == repo / "settings/hooks/banner.sh"


def test_template_hook_that_runs_no_command_stays_single(
    repo: Path, home: Path
) -> None:
    prompt_hook = {"type": "prompt", "prompt": "Check the plan before stopping."}
    template = {**TEMPLATE, "hooks": {"Stop": [{"hooks": [prompt_hook]}]}}
    write(repo / "settings/claude-settings.json", json.dumps(template))
    run_sync(repo, home, "claude")

    run_sync(repo, home, "claude")

    assert _settings(home)["hooks"] == {"Stop": [{"hooks": [prompt_hook]}]}


def test_second_run_changes_nothing(repo: Path, home: Path) -> None:
    settings = _write_settings(home, LIVE)
    run_sync(repo, home, "claude")
    first = tree(home), settings.read_bytes()

    run_sync(repo, home, "claude")

    assert (tree(home), settings.read_bytes()) == first


def test_dry_run_shows_only_what_the_merge_changes_and_changes_nothing(
    repo: Path, home: Path
) -> None:
    token = "ghp_not-a-real-token"
    settings = home / ".claude/settings.json"
    # Formatted unlike the installer writes it: a diff of the raw text would
    # show every line, the token too.
    write(settings, json.dumps({**LIVE, "env": {"GITHUB_TOKEN": token}}, indent=4))
    before = tree(home), settings.read_bytes()

    log = run_sync(repo, home, "claude", "--dry-run")

    assert (tree(home), settings.read_bytes()) == before
    lines = log.splitlines()
    assert any(line.startswith("-") and "Bash(uv run:*)" in line for line in lines)
    assert any(
        line.startswith("+") and "Bash(.venv/bin/pytest:*)" in line for line in lines
    )
    assert token not in log


@pytest.mark.parametrize(
    "text",
    [
        pytest.param('{\n  // my note\n  "model": "sonnet"\n}\n', id="not-json"),
        pytest.param('{"permissions": null}\n', id="permissions-not-an-object"),
        pytest.param('{"hooks": []}\n', id="hooks-not-an-object"),
        pytest.param('{"hooks": {"Stop": {"hooks": []}}}\n', id="event-not-a-list"),
    ],
)
def test_unreadable_settings_stop_the_run_before_anything_changes(
    repo: Path, home: Path, text: str
) -> None:
    settings = home / ".claude/settings.json"
    write(settings, text)
    before = tree(home)

    result = run_unchecked(
        ["python3", repo / "scripts/sync.py", "claude"],
        home,
        PYTHONDONTWRITEBYTECODE="1",
    )

    assert result.returncode != 0
    assert str(settings) in result.stderr
    assert "Traceback" not in result.stderr
    assert tree(home) == before
    assert settings.read_text(encoding="utf-8") == text


def test_session_start_banner_counts_the_installed_skills_and_agents(
    installed_home: Path,
) -> None:
    [group] = _settings(installed_home)["hooks"]["SessionStart"]
    [hook] = group["hooks"]

    banner = run(["bash", "-c", hook["command"]], installed_home, AI_SETTINGS_QUIET="0")

    counts = re.search(r"Loaded: (\d+) skill\(s\), (\d+) subagent\(s\)", banner.stdout)
    assert counts, banner.stdout
    assert int(counts[1]) == len(discover_skill_paths())
    assert int(counts[2]) == len(list((REPO_ROOT / "agents").glob("*/AGENT.md")))
