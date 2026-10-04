"""Claude Code: ~/.claude/settings.json and the hook scripts it runs.

settings.json belongs to the user: Claude Code itself, plugins and tools like
agterm write there too. The installer owns only what the template
settings/claude-settings.json holds: $schema, permissions.allow, .ask and
.deny, and the template's hooks. Everything else stays as it is.

The template is also the list of hook scripts: every ~/.claude/hooks/<script>
it runs is linked from settings/hooks/<script>. ~/.claude/hooks is a real dir,
so the user can keep their own scripts there.
"""

from __future__ import annotations

import difflib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, NoReturn

from aisettings import log
from aisettings.fs import Fs, SyncError, link_target

_TEMPLATE = Path("settings/claude-settings.json")
_REPO_HOOKS = Path("settings/hooks")
_SETTINGS = Path(".claude/settings.json")
_HOOKS = Path(".claude/hooks")
_PERMISSION_LISTS = ("allow", "ask", "deny")
# The one form in which the template runs a hook script; Claude Code runs a
# hook command in a shell, which expands ~. Group 1 is the script's name.
_HOOK_SCRIPT_RE = re.compile(r"~/\.claude/hooks/([^/\s]+)(?=\s|$)")
_HOOKS_DIR_MENTION = ".claude/hooks/"

# Runtime aliases: no `X | Y` here, they must evaluate on Python 3.9.
_Json = dict[str, Any]
# Tells the installer's hook entry from the user's.
_HookTest = Callable[[Any], bool]


def sync(fs: Fs, repo: Path, home: Path) -> None:
    # Both files are read and checked before the first change in home.
    template_path = repo / _TEMPLATE
    template = _read(template_path)
    scripts = _scripts(template, template_path)
    path = home / _SETTINGS
    existed = path.exists()
    settings = _read(path) if existed else {}

    source = repo / _REPO_HOOKS
    hooks_dir = home / _HOOKS
    # Taken before _sync_scripts drops the links the template no longer needs.
    linked = _linked_scripts(source, hooks_dir)
    _sync_scripts(fs, source, hooks_dir, scripts)

    is_installers = _installers_test(template, set(scripts) | linked)
    merged = _merge(settings, template, is_installers)
    if merged == settings:
        log.info(f"up to date {path}")
        return
    if existed:
        log.info(f"{path} changes:\n{_diff(settings, merged)}")
    fs.update_in_place(path, _dump(merged))


def _read(path: Path) -> _Json:
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SyncError(f"can't read {path} as JSON, left it as is: {exc}") from exc
    return _checked(settings, path)


def _checked(settings: Any, path: Path) -> _Json:
    """settings, if the merge won't trip over it halfway."""

    def fail(where: str, kind: str) -> NoReturn:
        raise SyncError(f"{path}: {where} is not a JSON {kind}, left the file as is")

    if not isinstance(settings, dict):
        fail("the top level", "object")
    if not isinstance(settings.get("permissions", {}), dict):
        fail("permissions", "object")
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        fail("hooks", "object")
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            fail(f"hooks.{event}", "array")
        for i, group in enumerate(groups):
            if not isinstance(group, dict):
                fail(f"hooks.{event}[{i}]", "object")
            if not isinstance(group.get("hooks", []), list):
                fail(f"hooks.{event}[{i}].hooks", "array")
    return settings


def _scripts(template: _Json, path: Path) -> list[str]:
    """Names of the scripts the template runs from ~/.claude/hooks."""
    scripts: set[str] = set()
    for command in _commands(template.get("hooks", {})):
        script = _script(command)
        if script is not None:
            scripts.add(script)
        elif _HOOKS_DIR_MENTION in command:
            raise SyncError(
                f"{path}: a hook command runs a script as ~/.claude/hooks/<script> "
                f"at its start, not like this: {command}"
            )
    return sorted(scripts)


def _sync_scripts(fs: Fs, source: Path, hooks_dir: Path, names: list[str]) -> None:
    """Link every script the template runs. A link into source the template
    doesn't run any more goes; the rest of hooks_dir is the user's."""
    missing = [name for name in names if not (source / name).is_file()]
    if missing:
        raise SyncError(f"the template runs scripts missing in {source}: {missing}")
    for name in names:
        fs.link(source / name, hooks_dir / name)
    if not hooks_dir.is_dir():
        return
    for entry in sorted(hooks_dir.iterdir()):
        if entry.name not in names and _links_into(entry, source):
            fs.unlink(entry)


def _linked_scripts(source: Path, hooks_dir: Path) -> set[str]:
    """Scripts an earlier run linked into hooks_dir."""
    if not hooks_dir.is_dir():
        return set()
    return {entry.name for entry in hooks_dir.iterdir() if _links_into(entry, source)}


def _links_into(entry: Path, source: Path) -> bool:
    return entry.is_symlink() and link_target(entry).is_relative_to(source)


def _installers_test(template: _Json, scripts: set[str]) -> _HookTest:
    """A hook entry is the installer's if the template holds it or its command,
    or if the script it runs from ~/.claude/hooks is in scripts: the template
    runs it or an earlier run linked it. Any other script there is the user's,
    even one that isn't on this machine yet."""
    hooks = [hook for group in _groups(template.get("hooks", {})) for hook in group]
    commands = _commands(template.get("hooks", {}))

    def is_installers(hook: Any) -> bool:
        if hook in hooks:
            return True
        command = _command(hook)
        if command is None:
            return False
        return command in commands or _script(command) in scripts

    return is_installers


def _merge(settings: _Json, template: _Json, is_installers: _HookTest) -> _Json:
    """settings with what the installer owns taken from template."""
    merged: _Json = {}
    if "$schema" in template:
        merged["$schema"] = template["$schema"]
    merged.update((key, value) for key, value in settings.items() if key != "$schema")
    merged["permissions"] = _merge_permissions(
        settings.get("permissions", {}), template.get("permissions", {})
    )
    merged["hooks"] = _merge_hooks(
        settings.get("hooks", {}), template.get("hooks", {}), is_installers
    )
    return merged


def _merge_permissions(permissions: _Json, template: _Json) -> _Json:
    """The template's lists replace the user's; other keys like defaultMode stay."""
    merged = dict(permissions)
    for key in _PERMISSION_LISTS:
        if key in template:
            merged[key] = template[key]
        else:
            merged.pop(key, None)
    return merged


def _merge_hooks(hooks: _Json, template: _Json, is_installers: _HookTest) -> _Json:
    """Per event the installer's hooks go and the template's follow the rest.
    A group or an event that held only the installer's hooks goes."""
    merged: dict[str, list[Any]] = {}
    for event, groups in hooks.items():
        stripped = (_strip(group, is_installers) for group in groups)
        merged[event] = [group for group in stripped if group is not None]
    for event, groups in template.items():
        merged.setdefault(event, []).extend(groups)
    return {
        event: groups
        for event, groups in merged.items()
        if groups or not hooks.get(event)
    }


def _strip(group: _Json, is_installers: _HookTest) -> _Json | None:
    """group without the installer's hooks; None if it held nothing else."""
    hooks = group.get("hooks", [])
    kept = [hook for hook in hooks if not is_installers(hook)]
    if len(kept) == len(hooks):
        return group
    return {**group, "hooks": kept} if kept else None


def _groups(hooks: _Json) -> list[list[Any]]:
    """The hook lists of every group of every event."""
    return [group.get("hooks", []) for groups in hooks.values() for group in groups]


def _commands(hooks: _Json) -> set[str]:
    return {
        command
        for group in _groups(hooks)
        for hook in group
        if (command := _command(hook)) is not None
    }


def _command(hook: Any) -> str | None:
    if not isinstance(hook, dict) or hook.get("type") != "command":
        return None
    command = hook.get("command")
    return command if isinstance(command, str) else None


def _script(command: str) -> str | None:
    match = _HOOK_SCRIPT_RE.match(command)
    return match[1] if match else None


def _dump(settings: _Json) -> str:
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"


def _diff(before: _Json, after: _Json) -> str:
    """The lines the merge changes, without context: a context line could show
    a value of the user's, such as a token in env."""
    lines = difflib.unified_diff(
        _dump(before).splitlines(),
        _dump(after).splitlines(),
        "before",
        "after",
        n=0,
        lineterm="",
    )
    return "\n".join(lines)
