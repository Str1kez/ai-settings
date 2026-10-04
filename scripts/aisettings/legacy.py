"""One-off migrations from the old layout, where install.sh linked whole repo
dirs into harness homes and every tool that wrote there wrote into the repo.

Each migration looks for the old state and does nothing without it, so sync.py
runs them on every call. The module is temporary: it goes once both machines
have migrated (ADR 0001).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from aisettings import agents, log
from aisettings.fs import Fs, SyncError, link_target

# What the old install.sh wrote to ~/.claude/commands/<ns>/<skill>.md for every
# skill: a command that only invokes the skill. Every version of the generator
# wrote exactly this, with " in the description replaced by '.
_SHIM_RE = re.compile(
    r'---\ndescription: "[^"\n]*"\n---\nInvoke the `(?P<skill>[^`\n]+)` skill\.\n'
)
# The old install.sh merged these and permission into every agent entry of
# opencode.jsonc. Its prompt pointed at agent-prompts/<name>.md, which is how
# an entry of the merge is told from the user's.
_MERGED_AGENT_FIELDS = ("description", "mode", "prompt")
_PROMPT_DIR_REF = "{file:./agent-prompts/"


def migrate_skills(fs: Fs, repo: Path, home: Path) -> None:
    migrate_dir_link(fs, repo, home / ".claude/skills", repo / "skills")
    # Claude Code serves every skill as /<name> itself now.
    _remove_command_shims(fs, home / ".claude/commands")
    # Gemini CLI reads ~/.agents/skills; this one pointed at Superpowers.
    _remove_repo_link(fs, repo, home / ".gemini/skills")


def migrate_agents(fs: Fs, repo: Path, home: Path) -> None:
    migrate_dir_link(fs, repo, home / ".claude/agents", repo / "agents")
    # OpenCode gets markdown agents now, the old merge goes.
    permissions = {
        agent.name: agents.opencode_permission(agent.tools)
        for agent in agents.collect(repo)
    }
    opencode = home / ".config/opencode"
    config = opencode / "opencode.jsonc"
    before = config.read_text(encoding="utf-8") if config.is_file() else ""
    after = _unmerge_opencode_agents(fs, config, before, permissions)
    _remove_merged_prompts(
        fs, opencode / "agent-prompts", before, after, set(permissions)
    )


def migrate_hooks(fs: Fs, repo: Path, home: Path) -> None:
    migrate_dir_link(fs, repo, home / ".claude/hooks", repo / "settings/hooks")


def migrate_dir_link(fs: Fs, repo: Path, link: Path, source: Path) -> None:
    """Turn link, an old symlink to the repo dir source, into a real dir.

    What harness tools wrote through the link sits in source untracked by git;
    it moves into the new dir. Tracked entries stay in the repo.
    """
    fs.finish_link_replacement(link)
    if not link.is_symlink() or link.resolve() != source.resolve():
        return
    fs.replace_link_with_dir(link, _untracked_entries(repo, source))


def _untracked_entries(repo: Path, source: Path) -> list[Path]:
    """Top-level entries of source that hold no file git tracks."""
    if not source.is_dir():
        return []
    rel = source.relative_to(repo).as_posix()
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", rel],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SyncError(
            f"can't list tracked files in {source} with git: {exc}"
        ) from exc
    tracked = {
        Path(path).relative_to(rel).parts[0]
        for path in result.stdout.split("\0")
        if path
    }
    return sorted(entry for entry in source.iterdir() if entry.name not in tracked)


def _prompt_ref(name: str) -> str:
    return f"{_PROMPT_DIR_REF}{name}.md}}"


def _unmerge_opencode_agents(
    fs: Fs, config: Path, text: str, permissions: dict[str, dict[str, str]]
) -> str:
    """Drop what the old merge wrote from the agent entries it wrote. An entry
    left empty goes, so does an agent block left empty; model and the user's
    other fields stay. Return the config text as it is after that.

    A rewrite would lose JSONC comments, so a file with them stays as is.
    """
    if _PROMPT_DIR_REF not in text:
        return text
    try:
        settings = json.loads(text)
    except ValueError:
        log.warn(
            f"{config} is not plain JSON, maybe it has comments: left as is. "
            "Drop description, mode, permission and prompt by hand from the "
            "agents whose prompt points into agent-prompts/, then rerun"
        )
        return text
    entries = settings.get("agent") if isinstance(settings, dict) else None
    if not isinstance(entries, dict):
        return text
    merged = [
        name
        for name, entry in entries.items()
        if isinstance(entry, dict) and entry.get("prompt") == _prompt_ref(name)
    ]
    if not merged:
        return text
    for name in merged:
        _unmerge_entry(entries[name], permissions.get(name))
        if not entries[name]:
            del entries[name]
    if not entries:
        del settings["agent"]
    log.info(
        f"{config}: dropping what the old install.sh merged into agent "
        f"{', '.join(merged)}"
    )
    new_text = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
    fs.update_in_place(config, new_text)
    return new_text


def _unmerge_entry(entry: dict[str, Any], rendered: dict[str, str] | None) -> None:
    """The merge was deep: a permission key the user added survived it, so of
    permission only the keys the render sets to the same value go. An agent
    gone from the repo has no render, its permission goes whole."""
    for field in _MERGED_AGENT_FIELDS:
        entry.pop(field, None)
    permission = entry.get("permission")
    if not isinstance(permission, dict):
        return
    if rendered is None:
        del entry["permission"]
        return
    for key, value in rendered.items():
        if permission.get(key) == value:
            del permission[key]
    if not permission:
        del entry["permission"]


def _remove_merged_prompts(
    fs: Fs, prompts: Path, before: str, after: str, repo_agents: set[str]
) -> None:
    """Remove a prompt file of the old merge once the config no longer points
    at it, and agent-prompts/ if that empties it. The file is the merge's if
    it belongs to a repo agent or the config pointed at it before."""
    if not prompts.is_dir():
        return
    entries = sorted(prompts.iterdir())
    old: list[Path] = []
    for entry in entries:
        if entry.suffix != ".md" or entry.is_symlink() or not entry.is_file():
            continue
        ref = _prompt_ref(entry.stem)
        if (entry.stem in repo_agents or ref in before) and ref not in after:
            old.append(entry)
    for prompt in old:
        fs.remove_file(prompt)
    if old and len(old) == len(entries):
        fs.remove_empty_dir(prompts)


def _remove_repo_link(fs: Fs, repo: Path, link: Path) -> None:
    """Remove link if it points into the repo itself. A link to another link
    that leads into the repo is the user's."""
    if link.is_symlink() and link_target(link).is_relative_to(repo):
        fs.unlink(link)


def _remove_command_shims(fs: Fs, commands: Path) -> None:
    """Remove generated shims and the namespace dirs they leave empty.
    Any other file in commands/ is the user's and stays."""
    if not commands.is_dir():
        return
    for ns_dir in sorted(commands.iterdir()):
        if ns_dir.is_symlink() or not ns_dir.is_dir():
            continue
        entries = sorted(ns_dir.iterdir())
        shims = [entry for entry in entries if _is_shim(entry)]
        for shim in shims:
            fs.remove_file(shim)
        if shims and len(shims) == len(entries):
            fs.remove_empty_dir(ns_dir)


def _is_shim(path: Path) -> bool:
    if path.suffix != ".md" or path.is_symlink() or not path.is_file():
        return False
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return False
    match = _SHIM_RE.fullmatch(text)
    return match is not None and match["skill"] == f"{path.parent.name}:{path.stem}"
