import json
import shutil
from pathlib import Path

import pytest

from tests.helpers import run


def test_install_writes_flat_opencode_instructions(installed_home: Path) -> None:
    instructions = installed_home / ".config/opencode/AGENTS.md"
    content = instructions.read_text(encoding="utf-8")

    assert not instructions.is_symlink()
    assert "@docs/ai/persona.md" not in content
    assert "# Persona:" in content


@pytest.mark.skipif(shutil.which("jq") is None, reason="the agent merge needs jq")
def test_agents_merge_keeps_user_fields_and_dotfiles_link(tmp_path: Path) -> None:
    dotfiles_config = tmp_path / "dotfiles/opencode.jsonc"
    dotfiles_config.parent.mkdir()
    user_config = {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {"context7": {"type": "remote"}},
        "agent": {"code-reviewer": {"model": "anthropic/claude-opus"}},
    }
    dotfiles_config.write_text(json.dumps(user_config), encoding="utf-8")
    config = tmp_path / ".config/opencode/opencode.jsonc"
    config.parent.mkdir(parents=True)
    config.symlink_to(dotfiles_config)

    run(["python3", "scripts/sync.py", "agents"], tmp_path)

    merged = json.loads(dotfiles_config.read_text(encoding="utf-8"))
    reviewer = merged["agent"]["code-reviewer"]
    assert config.is_symlink()
    assert merged["mcp"] == user_config["mcp"]
    assert reviewer["model"] == "anthropic/claude-opus"
    assert reviewer["mode"] == "subagent"
    assert reviewer["permission"]["edit"] == "deny"
