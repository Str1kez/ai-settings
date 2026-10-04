import subprocess
from pathlib import Path

from aisettings import skills


def _tracked_skill(repo: Path, rel: str) -> None:
    path = repo / rel / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: x\n---\n", encoding="utf-8")
    subprocess.run(["git", "add", rel], cwd=repo, check=True)


def test_only_tracked_top_level_skill_dirs_are_collected(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _tracked_skill(tmp_path, "skills/commit")
    _tracked_skill(tmp_path, "skills/commit/examples/nested")
    untracked = tmp_path / "skills/matt-skill/SKILL.md"
    untracked.parent.mkdir(parents=True)
    untracked.write_text("---\nname: x\n---\n", encoding="utf-8")

    found = skills.collect(tmp_path)

    assert found == {"commit": tmp_path / "skills/commit"}
