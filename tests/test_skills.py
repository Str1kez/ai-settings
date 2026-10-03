import subprocess
from pathlib import Path

import pytest

from aisettings import skills
from aisettings.fs import SyncError


def _tracked_skill(repo: Path, rel: str) -> None:
    path = repo / rel / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: x\n---\n", encoding="utf-8")
    subprocess.run(["git", "add", rel], cwd=repo, check=True)


def test_same_skill_name_in_two_namespaces_is_rejected(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _tracked_skill(tmp_path, "skills/one/commit")
    _tracked_skill(tmp_path, "skills/two/commit")

    with pytest.raises(SyncError, match="commit"):
        skills.collect(tmp_path)
