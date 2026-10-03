from pathlib import Path


def test_install_writes_flat_opencode_instructions(installed_home: Path) -> None:
    instructions = installed_home / ".config/opencode/AGENTS.md"
    content = instructions.read_text(encoding="utf-8")

    assert not instructions.is_symlink()
    assert "@docs/ai/persona.md" not in content
    assert "# Persona:" in content
