from collections.abc import Callable
from pathlib import Path

import pytest

from aisettings.fs import Fs, GuardError


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "skills/ns/foo").mkdir(parents=True)
    (repo / "skills/ns/foo/SKILL.md").write_text(
        "---\nname: foo\n---\n", encoding="utf-8"
    )
    return repo


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def tree(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


@pytest.mark.parametrize(
    "create",
    [
        pytest.param(lambda fs, src, dst: fs.link(src, dst), id="link"),
        pytest.param(lambda fs, src, dst: fs.write(dst, "text\n"), id="write"),
    ],
)
def test_refuses_to_create_in_dir_that_resolves_into_repo(
    repo: Path, home: Path, create: Callable[[Fs, Path, Path], None]
) -> None:
    legacy_skills = home / ".claude/skills"
    legacy_skills.parent.mkdir()
    legacy_skills.symlink_to(repo / "skills")
    before = tree(repo)

    with pytest.raises(GuardError):
        create(Fs(repo, dry_run=False), repo / "skills/ns/foo", legacy_skills / "foo")

    assert tree(repo) == before


def test_write_replaces_symlink_instead_of_writing_through_it(
    repo: Path, home: Path
) -> None:
    source = repo / "AGENTS.md"
    source.write_text("source\n", encoding="utf-8")
    dst = home / ".codex/AGENTS.md"
    dst.parent.mkdir()
    dst.symlink_to(source)

    Fs(repo, dry_run=False).write(dst, "flat\n")

    assert source.read_text(encoding="utf-8") == "source\n"
    assert not dst.is_symlink()
    assert dst.read_text(encoding="utf-8") == "flat\n"


def test_link_moves_existing_file_to_backups(repo: Path, home: Path) -> None:
    source = repo / "GEMINI.md"
    source.write_text("repo\n", encoding="utf-8")
    dst = home / ".gemini/GEMINI.md"
    dst.parent.mkdir()
    dst.write_text("mine\n", encoding="utf-8")

    Fs(repo, dry_run=False).link(source, dst)

    assert dst.resolve() == source.resolve()
    backups = [path for path in (repo / "backups").rglob("*") if path.is_file()]
    assert [(path.name, path.read_text(encoding="utf-8")) for path in backups] == [
        ("GEMINI.md", "mine\n")
    ]
