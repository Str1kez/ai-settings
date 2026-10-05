from pathlib import Path

from tests.helpers import REPO_ROOT

CURSOR_FRONTMATTER = "---\nalwaysApply: true\n---\n\n"


def test_install_deploys_rules_to_codex_cursor_and_claude(installed_home: Path) -> None:
    # test_install_opencode checks the flat render itself.
    flat = (installed_home / ".config/opencode/AGENTS.md").read_text(encoding="utf-8")
    codex = installed_home / ".codex/AGENTS.md"
    cursor = installed_home / ".cursor/rules/ai-settings.mdc"

    assert not codex.is_symlink()
    assert codex.read_text(encoding="utf-8") == flat
    assert cursor.read_text(encoding="utf-8") == CURSOR_FRONTMATTER + flat
    assert (installed_home / ".claude/CLAUDE.md").resolve() == REPO_ROOT / "CLAUDE.md"
