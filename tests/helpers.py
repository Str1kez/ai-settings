"""Run repo scripts against a throwaway HOME."""

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_unchecked(
    command: list[str | Path], home: Path, **env: str
) -> subprocess.CompletedProcess[str]:
    """Run command from the repo root with HOME=home; return the result as is."""
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env={**os.environ, "HOME": str(home), **env},
        capture_output=True,
        text=True,
        check=False,
    )


def run(
    command: list[str | Path], home: Path, **env: str
) -> subprocess.CompletedProcess[str]:
    """Run command from the repo root with HOME=home; fail with its stderr."""
    result = run_unchecked(command, home, **env)
    assert result.returncode == 0, result.stderr
    return result


def tree(root: Path) -> dict[str, str]:
    """Every path under root with its link target, or "dir"/"file"."""
    return {
        str(path.relative_to(root)): f"-> {os.readlink(path)}"
        if path.is_symlink()
        else "dir"
        if path.is_dir()
        else "file"
        for path in sorted(root.rglob("*"))
    }
