"""Run repo scripts against a throwaway HOME."""

import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_scripts(repo: Path) -> None:
    """Give repo its own copy of the deploy scripts. A test that changes what
    the repo holds runs this copy, never the scripts of REPO_ROOT."""
    shutil.copytree(
        REPO_ROOT / "scripts",
        repo / "scripts",
        ignore=shutil.ignore_patterns("__pycache__"),
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git_track(repo: Path, *paths: str) -> None:
    """Make repo a git repo if it isn't one yet and stage paths: a staged file
    is tracked, which is all the deploy asks of a skill or an agent."""
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", *paths], cwd=repo, check=True)


def run_sync(repo: Path, home: Path, *args: str) -> str:
    """Run the copy of sync.py in repo with HOME=home, fail on error, return
    its log."""
    command: list[str | Path] = ["python3", repo / "scripts/sync.py", *args]
    # Apple's python3 otherwise caches bytecode under $HOME/Library/Caches.
    return run(command, home, PYTHONDONTWRITEBYTECODE="1").stderr


def run_unchecked(command: list[str | Path], home: Path, **env: str) -> subprocess.CompletedProcess[str]:
    """Run command from the repo root with HOME=home; return the result as is."""
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env={**os.environ, "HOME": str(home), **env},
        capture_output=True,
        text=True,
        check=False,
    )


def run(command: list[str | Path], home: Path, **env: str) -> subprocess.CompletedProcess[str]:
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


def isolated_git_env(home: Path) -> dict[str, str]:
    """Keep the user's global gitignore from hiding a file by accident."""
    return {
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def git(project: Path, home: Path, *args: str) -> str:
    """Run git in project under an isolated HOME; return stdout."""
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        env={**os.environ, "HOME": str(home), **isolated_git_env(home)},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout
