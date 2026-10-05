"""Which artifact dirs git tracks: skills/<name>/SKILL.md, agents/<name>/AGENT.md.

Only tracked ones deploy, so every machine gets the same set from the repo. A
dir nobody ran `git add` on would land on this machine and nowhere else.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from aisettings import log
from aisettings.fs import SyncError

# <kind>/<name>/<marker>: "*" in a pathspec crosses "/", so a marker nested
# deeper (skills/synced/x/SKILL.md) matches too and is dropped by depth.
_MARKER_DEPTH = 3


def tracked_dirs(repo: Path, kind: str, marker: str) -> list[Path]:
    """Dirs <kind>/<name>/ whose marker file git tracks and the disk still has.

    A dir deleted without `git rm` is still in the index; it counts as gone,
    so its links get removed.
    """
    dirs = _dirs(repo, kind, marker, ["--cached"])
    return [d for d in dirs if (d / marker).is_file()]


def warn_untracked(repo: Path, kind: str, marker: str) -> None:
    """Warn about real dirs with a marker that git neither tracks nor ignores:
    most likely a forgotten `git add`. Symlinks and nested dirs never match."""
    for untracked in _dirs(repo, kind, marker, ["--others", "--exclude-standard"]):
        rel = untracked.relative_to(repo)
        log.warn(
            f"{rel}/{marker} is not tracked by git, so {rel} isn't deployed: "
            f"git add {rel}"
        )


def _dirs(repo: Path, kind: str, marker: str, flags: list[str]) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", *flags, "--", f"{kind}/*/{marker}"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SyncError(f"can't list tracked {kind} with git: {exc}") from exc
    files = (Path(rel) for rel in result.stdout.split("\0") if rel)
    return sorted(repo / f.parent for f in files if len(f.parts) == _MARKER_DEPTH)
