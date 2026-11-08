import json
from pathlib import Path

import pytest

from aisettings import opencode
from tests.helpers import REPO_ROOT, run_sync, run_unchecked, write


def test_install_writes_flat_opencode_instructions(installed_home: Path) -> None:
    instructions = installed_home / ".config/opencode/AGENTS.md"
    content = instructions.read_text(encoding="utf-8")

    assert not instructions.is_symlink()
    assert "@docs/ai/persona.md" not in content
    assert "# Persona:" in content


SHELL_LINE = '"shell": "/bin/bash"'


def _opencode_config(home: Path) -> Path:
    return home / ".config/opencode/opencode.jsonc"


def test_shell_is_pinned_to_the_same_value_in_both_harnesses() -> None:
    template = json.loads((REPO_ROOT / "settings/claude-settings.json").read_text(encoding="utf-8"))

    assert template["env"]["CLAUDE_CODE_SHELL"] == opencode.SHELL


def test_shell_goes_into_a_new_config_when_there_is_none(tmp_path: Path) -> None:
    run_sync(REPO_ROOT, tmp_path, "opencode")

    assert json.loads(_opencode_config(tmp_path).read_text(encoding="utf-8")) == {"shell": "/bin/bash"}


def test_shell_goes_first_into_the_users_config_and_keeps_the_rest(tmp_path: Path) -> None:
    rest = '  // my providers\n  "provider": {"x": {"apiKey": "secret"}},\n  "theme": "dark" /* tui */\n}\n'
    write(_opencode_config(tmp_path), "{\n" + rest)

    log = run_sync(REPO_ROOT, tmp_path, "opencode")

    assert _opencode_config(tmp_path).read_text(encoding="utf-8") == "{\n  " + SHELL_LINE + ",\n" + rest
    assert "secret" not in log


def test_second_run_changes_nothing(tmp_path: Path) -> None:
    write(_opencode_config(tmp_path), '{\n  "theme": "dark"\n}\n')
    run_sync(REPO_ROOT, tmp_path, "opencode")
    once = _opencode_config(tmp_path).read_text(encoding="utf-8")

    run_sync(REPO_ROOT, tmp_path, "opencode")

    assert _opencode_config(tmp_path).read_text(encoding="utf-8") == once


@pytest.mark.parametrize(
    "config",
    [
        '{"mcp": {"local": {"shell": "/bin/zsh"}}}',
        '{"command": ["shell", {"shell": "/bin/zsh"}]}',
        '{\n  // "shell": "/bin/zsh"\n  "theme": "dark"\n}',
        '{"note": "\\"shell\\": \\"/bin/zsh\\""}',
        "{}",
    ],
)
def test_shell_is_added_when_it_is_not_a_top_level_key(tmp_path: Path, config: str) -> None:
    write(_opencode_config(tmp_path), config)

    run_sync(REPO_ROOT, tmp_path, "opencode")

    after = _opencode_config(tmp_path).read_text(encoding="utf-8")
    assert after.startswith(f"{{\n  {SHELL_LINE}")
    assert after.count(SHELL_LINE) == 1


def test_another_shell_of_the_user_stays_with_a_warning(tmp_path: Path) -> None:
    config = '{"shell": "/bin/zsh"}\n'
    write(_opencode_config(tmp_path), config)

    log = run_sync(REPO_ROOT, tmp_path, "opencode")

    assert _opencode_config(tmp_path).read_text(encoding="utf-8") == config
    assert "/bin/zsh" in log
    assert "warn" in log


def test_config_that_is_not_an_object_is_left_alone(tmp_path: Path) -> None:
    write(_opencode_config(tmp_path), '["not", "an object"]')

    result = run_unchecked(["python3", REPO_ROOT / "scripts/sync.py", "opencode"], tmp_path)

    assert result.returncode != 0
    assert _opencode_config(tmp_path).read_text(encoding="utf-8") == '["not", "an object"]'
