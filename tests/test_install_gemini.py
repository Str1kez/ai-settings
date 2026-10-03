from pathlib import Path

from tests.helpers import REPO_ROOT


def test_install_links_gemini_import(installed_home: Path) -> None:
    gemini_home = installed_home / ".gemini"

    assert (gemini_home / "GEMINI.md").resolve() == REPO_ROOT / "GEMINI.md"
    assert (gemini_home / "AGENTS.md").resolve() == REPO_ROOT / "AGENTS.md"
