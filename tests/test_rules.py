from pathlib import Path

import pytest

from aisettings import rules
from aisettings.fs import SyncError
from tests.helpers import run


def test_check_fails_on_missing_import(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text(
        "# Rules\n\n@docs/ai/gone.md\n", encoding="utf-8"
    )

    with pytest.raises(SyncError, match="docs/ai/gone.md"):
        rules.check(tmp_path)


def test_repo_rules_pass_check(tmp_path: Path) -> None:
    run(["python3", "scripts/sync.py", "rules", "--check"], tmp_path)
