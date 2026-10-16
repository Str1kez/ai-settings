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
    # rtk is gone from the installer; the plan must not bring its steps back.
    plan = (result.stdout + result.stderr).lower()
    for marker in ("rtk hook", "rtk init", "rust token killer"):
        assert marker not in plan, marker
