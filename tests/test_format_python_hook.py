"""The Claude Code hook that formats a .py file after Write|Edit: it runs the
project's ruff and never uv."""

import json
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from tests.helpers import REPO_ROOT, write

HOOK = REPO_ROOT / "settings/hooks/format-python.sh"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq")


def _executable(path: Path, text: str) -> None:
    write(path, text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _fake_ruff(path: Path, log: Path) -> None:
    _executable(path, f'#!/bin/sh\necho "$@" >> {log}\n')


@pytest.fixture
def path_dir(tmp_path: Path) -> Path:
    """A PATH of its own: jq and a uv that fails if anything calls it."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "jq").symlink_to(shutil.which("jq") or "")
    _executable(bin_dir / "uv", f"#!/bin/sh\necho uv >> {tmp_path}/uv.log\nexit 1\n")
    return bin_dir


def _run_hook(path_dir: Path, file: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(HOOK)],
        input=json.dumps({"tool_input": {"file_path": str(file)}}),
        env={"PATH": str(path_dir), "HOME": str(path_dir)},
        capture_output=True,
        text=True,
        check=False,
    )


def test_python_file_is_formatted_with_the_project_ruff_and_uv_never_runs(
    tmp_path: Path, path_dir: Path
) -> None:
    ruff_log = tmp_path / "ruff.log"
    _fake_ruff(tmp_path / "project/.venv/bin/ruff", ruff_log)
    source = tmp_path / "project/pkg/mod.py"
    write(source, "x=1\n")

    result = _run_hook(path_dir, source)

    assert result.returncode == 0, result.stderr
    assert ruff_log.read_text().splitlines() == [
        f"check --fix {source}",
        f"format {source}",
    ]
    assert not (tmp_path / "uv.log").exists()


def test_ruff_from_path_is_used_without_a_venv(tmp_path: Path, path_dir: Path) -> None:
    ruff_log = tmp_path / "ruff.log"
    _fake_ruff(path_dir / "ruff", ruff_log)
    source = tmp_path / "loose/mod.py"
    write(source, "x=1\n")

    result = _run_hook(path_dir, source)

    assert result.returncode == 0, result.stderr
    assert len(ruff_log.read_text().splitlines()) == 2
    assert not (tmp_path / "uv.log").exists()


def test_file_that_is_not_python_is_left_alone(tmp_path: Path, path_dir: Path) -> None:
    ruff_log = tmp_path / "ruff.log"
    _fake_ruff(path_dir / "ruff", ruff_log)
    source = tmp_path / "notes.md"
    write(source, "# notes\n")

    result = _run_hook(path_dir, source)

    assert result.returncode == 0, result.stderr
    assert not ruff_log.exists()
    assert not (tmp_path / "uv.log").exists()


def test_no_ruff_anywhere_is_a_silent_exit(tmp_path: Path, path_dir: Path) -> None:
    source = tmp_path / "loose/mod.py"
    write(source, "x=1\n")

    result = _run_hook(path_dir, source)

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert not (tmp_path / "uv.log").exists()


def test_findings_ruff_cannot_fix_do_not_fail_the_hook(
    tmp_path: Path, path_dir: Path
) -> None:
    _executable(path_dir / "ruff", "#!/bin/sh\nexit 1\n")
    source = tmp_path / "mod.py"
    write(source, "import os\n")

    assert _run_hook(path_dir, source).returncode == 0


def test_missing_jq_is_a_silent_exit(tmp_path: Path, path_dir: Path) -> None:
    (path_dir / "jq").unlink()
    _fake_ruff(path_dir / "ruff", tmp_path / "ruff.log")
    source = tmp_path / "mod.py"
    write(source, "x=1\n")

    result = _run_hook(path_dir, source)

    assert result.returncode == 0
    assert not (tmp_path / "ruff.log").exists()


def test_relative_path_is_skipped_instead_of_looping(
    tmp_path: Path, path_dir: Path
) -> None:
    _fake_ruff(path_dir / "ruff", tmp_path / "ruff.log")
    write(tmp_path / "pkg/mod.py", "x=1\n")
    result = subprocess.run(
        ["/bin/bash", str(HOOK)],
        input=json.dumps({"tool_input": {"file_path": "pkg/mod.py"}}),
        env={"PATH": str(path_dir), "HOME": str(path_dir)},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0
    assert not (tmp_path / "ruff.log").exists()
