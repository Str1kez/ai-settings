import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_install_writes_flat_opencode_instructions(tmp_path):
    subprocess.run(
        [REPO_ROOT / "scripts/install.sh"],
        cwd=REPO_ROOT,
        env={**os.environ, "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    )

    instructions = tmp_path / ".config/opencode/AGENTS.md"
    content = instructions.read_text(encoding="utf-8")

    assert not instructions.is_symlink()
    assert "@docs/ai/persona.md" not in content
    assert "# Persona:" in content
