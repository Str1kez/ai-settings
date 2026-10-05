from pathlib import Path

import pytest

from tests.helpers import REPO_ROOT, run


@pytest.fixture(scope="session")
def installed_home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """HOME after one real install.sh run, shared by read-only install tests."""
    home = tmp_path_factory.mktemp("home")
    run([REPO_ROOT / "scripts/install.sh"], home)
    return home
