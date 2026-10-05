"""scripts/new.py scaffolds a skill or an agent in a repo and never overwrites."""

from pathlib import Path

import pytest
import yaml

from tests.agent_lint.rules import problems
from tests.helpers import copy_scripts, run_unchecked
from tests.skill_lint.test_skills import PLACEHOLDER_RE


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """An empty repo with its own copy of the scripts: new.py scaffolds into the
    repo it lives in."""
    repo = tmp_path / "repo"
    copy_scripts(repo)
    return repo


def _new(repo: Path, tmp_path: Path, *args: str) -> tuple[int, str]:
    result = run_unchecked(["python3", repo / "scripts/new.py", *args], tmp_path)
    return result.returncode, result.stderr


def test_new_skill_gets_the_three_files_with_a_frontmatter_that_names_it(
    repo: Path, tmp_path: Path
) -> None:
    code, log = _new(repo, tmp_path, "skill", "my-skill")

    skill_dir = repo / "skills/my-skill"
    assert code == 0, log
    assert sorted(path.name for path in skill_dir.iterdir()) == [
        "CHANGELOG.md",
        "README.md",
        "SKILL.md",
    ]
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---\n")[1])
    assert frontmatter["name"] == "my-skill"
    assert f"[{frontmatter['version']}]" in (skill_dir / "CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    assert "git add skills/my-skill" in log


def test_new_skill_is_a_draft_that_the_lint_rejects_until_it_is_filled_in(
    repo: Path, tmp_path: Path
) -> None:
    code, log = _new(repo, tmp_path, "skill", "my-skill")

    assert code == 0, log
    text = (repo / "skills/my-skill/SKILL.md").read_text(encoding="utf-8")
    description = yaml.safe_load(text.split("---\n")[1])["description"]
    assert PLACEHOLDER_RE.search(description)


def test_new_agent_is_a_draft_that_the_lint_rejects_until_it_is_filled_in(
    repo: Path, tmp_path: Path
) -> None:
    code, log = _new(repo, tmp_path, "agent", "my-agent")

    assert code == 0, log
    found = problems(repo / "agents/my-agent")
    assert len(found) == 1 and "placeholder" in found[0]
    assert "git add agents/my-agent" in log


@pytest.mark.parametrize("kind", ["skill", "agent"])
def test_existing_dir_is_never_overwritten(
    repo: Path, tmp_path: Path, kind: str
) -> None:
    _new(repo, tmp_path, kind, "mine")
    marker = next((repo / f"{kind}s/mine").iterdir())
    marker.write_text("my work\n", encoding="utf-8")

    code, log = _new(repo, tmp_path, kind, "mine")

    assert code != 0
    assert "already exists" in log
    assert marker.read_text(encoding="utf-8") == "my work\n"


@pytest.mark.parametrize(
    "name", ["Bad_Name", "trail-", "double--hyphen", "../escape", "a b"]
)
def test_name_outside_the_agent_skills_regex_is_refused_and_nothing_is_written(
    repo: Path, tmp_path: Path, name: str
) -> None:
    code, log = _new(repo, tmp_path, "skill", name)

    assert code != 0
    assert "bad name" in log
    assert not (repo / "skills").exists()
    assert not (tmp_path / "escape").exists()
