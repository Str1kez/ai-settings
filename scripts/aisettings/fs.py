"""Links and files in harness homes.

Every change in a harness home goes through Fs, so --dry-run, the repo guard
and backups work the same way for every artifact type. In the repo Fs writes
only to backups/, which git ignores. The one exception is replacing an old dir
link: what git doesn't track moves out of the repo into the new dir.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import NamedTuple

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
        # Dir links this dry run would have replaced with real dirs. The rest of
        # the plan treats them as real.
        self._planned_dirs: list[Path] = []

    def inside_repo(self, path: Path) -> bool:
        """path really lies in the repo, e.g. behind an old dir symlink.

        A dir link this dry run would replace with a real dir doesn't count.
        """
        if any(path.is_relative_to(planned) for planned in self._planned_dirs):
            return False
        return path.resolve().is_relative_to(self._repo)

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
                self.backup(dst)
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

    def remove_file(self, path: Path) -> None:
        """Delete a regular file the installer wrote, now or in the old layout."""
        self._guard(path)
        if path.is_symlink() or not path.is_file():
            raise SyncError(f"refusing to remove {path}: not a regular file")
        if self._dry_run:
            log.dry_run(f"would remove {path}")
            return
        path.unlink()
        log.ok(f"removed {path}")

    # Migration from the old layout. Only legacy.py calls the methods below,
    # and they go away together with it (ADR 0001), as does _planned_dirs.

    def remove_empty_dir(self, path: Path) -> None:
        """Delete a dir the caller has emptied; rmdir fails on anything left."""
        self._guard(path)
        if self._dry_run:
            log.dry_run(f"would remove empty dir {path}")
            return
        path.rmdir()
        log.ok(f"removed empty dir {path}")

    def replace_link_with_dir(self, link: Path, entries: list[Path]) -> None:
        """Turn the dir symlink at link into a real dir and move entries, children
        of the dir it points to, into it. A moved symlink keeps its target.

        Entries gather in a hidden sibling dir that takes the link's place last.
        A failed move leaves the old link working and the next run resumes; a
        stop right before the swap is for finish_link_replacement().
        """
        self._guard(link)
        if not link.is_symlink():
            raise SyncError(f"refusing to replace {link}: not a symlink")
        old_target = os.readlink(link)
        staging = _staging_dir(link)
        moves = _plan_moves(link, entries, staging)
        if self._dry_run:
            for entry, link_text in moves:
                note = _relink_note(link_text)
                log.dry_run(f"would move {entry} -> {link / entry.name}{note}")
            log.dry_run(f"would replace {link} (-> {old_target}) with a real dir")
            self._planned_dirs.append(link)
            return
        try:
            staging.mkdir(exist_ok=True)
            for entry, link_text in moves:
                _move(entry, staging / entry.name, link_text)
                note = _relink_note(link_text)
                log.ok(f"moved {entry} -> {link / entry.name}{note}")
        except OSError as exc:
            raise SyncError(
                f"migrating {link} stopped: {exc}. The old link is in place, "
                f"moved entries wait in {staging}: rerun to resume"
            ) from exc
        link.unlink()
        staging.rename(link)
        log.ok(f"replaced {link} (was -> {old_target}) with a real dir")

    def finish_link_replacement(self, link: Path) -> None:
        """Put the gathered dir in place if replace_link_with_dir() stopped
        between dropping the link and the swap. Otherwise does nothing."""
        staging = _staging_dir(link)
        if os.path.lexists(link) or not staging.is_dir():
            return
        self._guard(link)
        if self._dry_run:
            log.dry_run(f"would move {staging} -> {link}, left by a stopped run")
            return
        staging.rename(link)
        log.ok(f"moved {staging} -> {link}, left by a stopped run")

    def backup(self, path: Path) -> None:
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
        if self.inside_repo(target.parent):
            raise GuardError(
                f"refusing to write {target}: {target.parent} resolves into the repo "
                f"({target.parent.resolve()})"
            )


def link_target(link: Path) -> Path:
    """Where the symlink link points, one hop: a chain of links isn't followed."""
    return Path(os.path.normpath(link.parent / os.readlink(link)))


def _has_content(path: Path, content: str) -> bool:
    return path.is_file() and path.read_bytes() == content.encode("utf-8")


# Helpers of the migration methods; they go together with them.


def _staging_dir(link: Path) -> Path:
    return link.with_name(f".{link.name}.ai-settings-migration")


class _Relocation(NamedTuple):
    """Entries move out of the real dir source into new_dir; the entries
    named in staying keep their place."""

    source: Path
    new_dir: Path
    staying: frozenset[str]

    def new_location(self, path: Path) -> Path:
        """Where path is after the move: inside a moving entry it moves along."""
        if path == self.source or not path.is_relative_to(self.source):
            return path
        rel = path.relative_to(self.source)
        return path if rel.parts[0] in self.staying else self.new_dir / rel

    def link_text(self, entry: Path) -> str | None:
        """New text that keeps the symlink entry pointing at its target once
        both have moved; None if the current text already does.

        npx skills writes links relative to the real dir they sit in, so a
        plain mv to another depth breaks them.
        """
        if not entry.is_symlink():
            return None
        text = os.readlink(entry)
        target = self.new_location(Path(os.path.normpath(self.source / text)))
        if os.path.isabs(text):
            new_text = str(target)
        else:
            new_text = os.path.relpath(target, self.new_dir)
        return None if new_text == text else new_text


def _plan_moves(
    link: Path, entries: list[Path], staging: Path
) -> list[tuple[Path, str | None]]:
    """Pair each entry with the new text it needs as a symlink. Refuses an
    entry outside the dir link points to, or one staging already holds."""
    source = Path(os.path.realpath(link))
    names = {child.name for child in source.iterdir()} if source.is_dir() else set()
    relocation = _Relocation(
        source=source,
        new_dir=Path(os.path.realpath(link.parent)) / link.name,
        staying=frozenset(names - {entry.name for entry in entries}),
    )
    moves: list[tuple[Path, str | None]] = []
    for entry in entries:
        if Path(os.path.realpath(entry.parent)) != source:
            raise SyncError(f"refusing to move {entry}: not in {source}")
        if os.path.lexists(staging / entry.name):
            raise SyncError(
                f"can't move {entry}: {staging / entry.name} already exists"
            )
        moves.append((entry, relocation.link_text(entry)))
    return moves


def _move(entry: Path, dst: Path, link_text: str | None) -> None:
    if link_text is None:
        entry.rename(dst)
        return
    dst.symlink_to(link_text)
    entry.unlink()


def _relink_note(link_text: str | None) -> str:
    return "" if link_text is None else f", link now -> {link_text}"
