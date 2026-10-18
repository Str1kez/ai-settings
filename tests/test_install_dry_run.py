from pathlib import Path

from tests.helpers import REPO_ROOT, run


def test_install_dry_run_leaves_home_untouched(tmp_path: Path) -> None:
    # Apple's python3 otherwise caches bytecode under $HOME/Library/Caches.
    result = run(
        [REPO_ROOT / "scripts/install.sh", "--dry-run"],
        tmp_path,
        PYTHONDONTWRITEBYTECODE="1",
    )

    assert list(tmp_path.iterdir()) == []
    # rtk is gone from the installer; the plan must not bring it back. Any
    # mention counts: a renamed step would slip past an "rtk hook" marker.
    # The checkout and home paths go first, so a worktree under a path like
    # .../ai-settings-worktrees/rtk-teardown can neither fake a step nor mask
    # one.
    plan = (result.stdout + result.stderr).lower()
    for path in (REPO_ROOT, tmp_path):
        plan = plan.replace(str(path).lower(), "<path>")
        plan = plan.replace(str(path.resolve()).lower(), "<path>")
    assert "rtk" not in plan
