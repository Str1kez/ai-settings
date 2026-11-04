"""init-project.sh puts a copy of my personal rules into the project for
Cursor; it must never reach the project's history."""

from pathlib import Path

from tests.helpers import REPO_ROOT, git, isolated_git_env, run

CURSOR_RULE = ".cursor/rules/ai-settings.mdc"


def test_cursor_rule_stays_out_of_git_across_reruns(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    repo = tmp_path / "repo"
    project = repo / "services/api"
    project.mkdir(parents=True)
    git(repo, home, "init", "-q")

    for _ in range(2):
        run(
            [REPO_ROOT / "scripts/init-project.sh", "--cursor", project],
            home,
            **isolated_git_env(home),
        )

    assert (project / CURSOR_RULE).is_file()
    untracked = git(repo, home, "status", "--porcelain", "--untracked-files=all")
    assert CURSOR_RULE not in untracked
    assert "services/api/AGENTS.md" in untracked
    exclude = (repo / ".git/info/exclude").read_text(encoding="utf-8")
    assert exclude.count(CURSOR_RULE) == 1
