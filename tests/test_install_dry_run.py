from pathlib import Path

from tests.helpers import REPO_ROOT, run


def test_install_dry_run_leaves_home_untouched(tmp_path: Path) -> None:
    # Apple's python3 otherwise caches bytecode under $HOME/Library/Caches.
    run(
        [REPO_ROOT / "scripts/install.sh", "--dry-run"],
        tmp_path,
        PYTHONDONTWRITEBYTECODE="1",
    )

    assert list(tmp_path.iterdir()) == []
