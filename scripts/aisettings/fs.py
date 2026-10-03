"""Links and files in harness homes.

Every change in a harness home goes through Fs, so --dry-run, the repo guard
and backups work the same way for every artifact type. The only place in the
repo Fs writes to is backups/, which git ignores.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from aisettings import log


class SyncError(Exception):
    """A sync step can't go on. sync.py reports it and exits non-zero."""


class GuardError(SyncError):
    """The target directory resolves into the repo, e.g. through an old dir symlink."""


class Fs:
    def __init__(self, repo: Path, *, dry_run: bool) -> None:
        self._repo = repo.resolve()
        self._dry_run = dry_run
        self._backup_dir = self._repo / "backups" / time.strftime("%Y%m%d-%H%M%S")

    def link(self, src: Path, dst: Path) -> None:
        """Point dst at src. Replaces another symlink, backs up a real file or dir."""
        self._guard(dst)
        if dst.is_symlink():
            old_target = os.readlink(dst)
            if old_target == str(src):
                log.info(f"already linked {dst}")
                return
            change = f"relink {dst} -> {src} (was -> {old_target})"
        else:
            change = f"link {dst} -> {src}"
            if dst.exists():
                self._backup(dst)
        if self._dry_run:
            log.dry_run(f"would {change}")
            return
        if dst.is_symlink():
            dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src)
        log.ok(change)

    def unlink(self, link: Path) -> None:
        """Remove a symlink. Refuses a real file or dir: that isn't ours to delete."""
        self._guard(link)
        if not link.is_symlink():
            raise SyncError(f"refusing to remove {link}: not a symlink")
        if self._dry_run:
            log.dry_run(f"would remove {link} (was -> {os.readlink(link)})")
            return
        link.unlink()
        log.ok(f"removed {link}")

    def write(self, dst: Path, content: str) -> None:
        """Write a generated file. A symlink at dst is replaced, not written through."""
        self._guard(dst)
        if not dst.is_symlink() and _has_content(dst, content):
            log.info(f"up to date {dst}")
            return
        if self._dry_run:
            log.dry_run(f"would write {dst}")
            return
        if dst.is_symlink():
            dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
        log.ok(f"wrote {dst}")

    def update_in_place(self, path: Path, content: str) -> None:
        """Rewrite a user-owned file where it lives, following a symlink at path.

        Unlike write(), keeps the link: the file may live in the user's dotfiles.
        """
        real = path.resolve()
        self._guard(real)
        if _has_content(real, content):
            log.info(f"up to date {path}")
            return
        if self._dry_run:
            log.dry_run(f"would update {path}")
            return
        real.parent.mkdir(parents=True, exist_ok=True)
        real.write_text(content, encoding="utf-8")
        log.ok(f"updated {path}")

    def _backup(self, path: Path) -> None:
        """Move path under backups/<ts>/, mirroring its absolute location."""
        target = self._backup_dir / path.relative_to(path.anchor)
        if target.exists() or target.is_symlink():
            raise SyncError(f"backup target already exists: {target}")
        if self._dry_run:
            log.dry_run(f"would back up {path} -> {target}")
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
        log.info(f"backed up {path} -> {target}")

    def _guard(self, target: Path) -> None:
        real_parent = target.parent.resolve()
        if real_parent.is_relative_to(self._repo):
            raise GuardError(
                f"refusing to write {target}: {target.parent} resolves into the repo "
                f"({real_parent})"
            )


def _has_content(path: Path, content: str) -> bool:
    return path.is_file() and path.read_bytes() == content.encode("utf-8")
