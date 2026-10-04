"""init-project.sh puts a copy of my personal rules into the project for
Cursor; it must never reach the project's history."""

import os
import subprocess
from pathlib import Path

from tests.helpers import REPO_ROOT, run

CURSOR_RULE = ".cursor/rules/ai-settings.mdc"


def _isolated_git_env(home: Path) -> dict[str, str]:
    """Keep the user's global gitignore from hiding the file by accident."""
    return {
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _git(project: Path, home: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        env={**os.environ, "HOME": str(home), **_isolated_git_env(home)},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_cursor_rule_stays_out_of_git_across_reruns(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    repo = tmp_path / "repo"
    project = repo / "services/api"
    project.mkdir(parents=True)
    _git(repo, home, "init", "-q")

    for _ in range(2):
        run(
            [REPO_ROOT / "scripts/init-project.sh", "--cursor", project],
            home,
            **_isolated_git_env(home),
        )

    assert (project / CURSOR_RULE).is_file()
    untracked = _git(repo, home, "status", "--porcelain", "--untracked-files=all")
    assert CURSOR_RULE not in untracked
    assert "services/api/AGENTS.md" in untracked
    exclude = (repo / ".git/info/exclude").read_text(encoding="utf-8")
    assert exclude.count(CURSOR_RULE) == 1
