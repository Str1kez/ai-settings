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


def run(command: list[str | Path], home: Path, **env: str) -> None:
    """Run command from the repo root with HOME=home; fail with its stderr."""
    result = run_unchecked(command, home, **env)
    assert result.returncode == 0, result.stderr
