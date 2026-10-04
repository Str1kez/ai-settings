"""Migration from the old hooks layout: ~/.claude/hooks linked to the repo's
settings/hooks/, so a script the user put there landed in the repo.

These tests run a copy of sync.py in a throwaway git repo. The migration moves
whatever git doesn't track out of settings/hooks/, and in the real repo that
is the user's own files.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.helpers import copy_scripts, run_sync, tree, write

BANNER = "#!/bin/sh\necho banner\n"
# What the user put into ~/.claude/hooks through the old link.
MINE = "#!/bin/sh\necho mine\n"
TEMPLATE = {
    "hooks": {
        "SessionStart": [
            {"hooks": [{"type": "command", "command": "~/.claude/hooks/banner.sh"}]}
        ]
    }
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo with a template, the script it runs and its own copy of the
    deploy scripts."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    write(repo / "settings/claude-settings.json", json.dumps(TEMPLATE))
    write(repo / "settings/hooks/banner.sh", BANNER)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "settings"], cwd=repo, check=True)
    return repo


@pytest.fixture
def home(tmp_path: Path, repo: Path) -> Path:
    """HOME on the old layout, with a script the user put in through it."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude/hooks").symlink_to(repo / "settings/hooks")
    write(repo / "settings/hooks/mine.sh", MINE)
    return home


def test_old_hooks_link_becomes_a_real_dir_with_a_link_per_script(
    repo: Path, home: Path
) -> None:
    run_sync(repo, home, "claude")

    hooks = home / ".claude/hooks"
    assert hooks.is_dir() and not hooks.is_symlink()
    assert (hooks / "banner.sh").resolve() == repo / "settings/hooks/banner.sh"
    assert not (hooks / "mine.sh").is_symlink()
    assert (hooks / "mine.sh").read_text(encoding="utf-8") == MINE
    assert os.listdir(repo / "settings/hooks") == ["banner.sh"]


def test_dry_run_plans_the_migration_and_backs_up_nothing(
    repo: Path, home: Path
) -> None:
    before = tree(home), tree(repo / "settings")

    log = run_sync(repo, home, "claude", "--dry-run")

    assert (tree(home), tree(repo / "settings")) == before
    plan = "\n".join(line for line in log.splitlines() if line.startswith("[dry-run]"))
    assert f"would move {repo / 'settings/hooks/mine.sh'}" in plan
    # The rest of the plan is made against the migrated layout.
    assert f"would link {home / '.claude/hooks/banner.sh'}" in plan
    assert "would back up" not in plan
