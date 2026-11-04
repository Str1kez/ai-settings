"""Agents: agents/<name>/AGENT.md is the only source, a template that names a
model level (and an optional effort) instead of a model.

Each template becomes a global agent on the session's model: a marked render
for Claude Code and a subagent without a model for OpenCode.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import NamedTuple, Union

from aisettings import tracked
from aisettings.fs import Fs, SyncError, link_target

# Claude Code tool -> OpenCode v2 permission action. In OpenCode, edit covers
# write, edit and apply_patch; the legacy List tool has no v2 action.
_TOOL_TO_PERMISSION = {
    "Read": "read",
    "Grep": "grep",
    "Glob": "glob",
    "Edit": "edit",
    "Write": "edit",
    "Bash": "shell",
    "Task": "subagent",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
}
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_CLAUDE_AGENTS = Path(".claude/agents")
_OPENCODE_AGENTS = Path(".config/opencode/agents")
# The first lines of a render: the mark tells our files from the user's.
_MARKER = "# managed-by: ai-settings"
_MARKDOWN_HEADER = f"---\n{_MARKER}\n"

# A tool outside this set is dropped silently by the render, so a typo would
# quietly cost an agent its permission. The agent lint holds tools to it.
KNOWN_TOOLS = frozenset(_TOOL_TO_PERMISSION)

# A template names a model level, never a model. One list: the render and the
# agent lint both read it.
MODEL_LEVELS = ("frontier", "standard")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
# What a global agent runs on in Claude Code: the model of the session.
_INHERIT = "inherit"

# Runtime alias: no `X | Y` here, it must evaluate on Python 3.9.
_Fields = dict[str, Union[str, list[str]]]


class Agent(NamedTuple):
    name: str
    description: str
    tools: list[str]
    body: str
    path: Path
    model: str
    effort: str | None


def sync(fs: Fs, repo: Path, home: Path) -> None:
    agents = _collect(repo)
    tracked.warn_untracked(repo, "agents", "AGENT.md")
    _drop_repo_links(fs, repo, home / _CLAUDE_AGENTS)
    claude = {f"{agent.name}.md": _render_claude(agent, _INHERIT) for agent in agents}
    _sync_renders(fs, home / _CLAUDE_AGENTS, claude, _MARKDOWN_HEADER)
    opencode = {f"{agent.name}.md": _render_opencode(agent) for agent in agents}
    _sync_renders(fs, home / _OPENCODE_AGENTS, opencode, _MARKDOWN_HEADER)


def _collect(repo: Path) -> list[Agent]:
    agents_dir = repo / "agents"
    if not agents_dir.is_dir():
        raise SyncError(f"agents dir not found: {agents_dir}")
    return [load(agent_dir / "AGENT.md") for agent_dir in tracked.tracked_dirs(repo, "agents", "AGENT.md")]


def _drop_repo_links(fs: Fs, repo: Path, claude_agents: Path) -> None:
    """Earlier versions linked each agent into Claude Code. Those links into
    repo/agents/ make way for the renders. Links elsewhere aren't ours."""
    if not claude_agents.is_dir():
        return
    for entry in sorted(claude_agents.iterdir()):
        if entry.is_symlink() and link_target(entry).is_relative_to(repo / "agents"):
            fs.unlink(entry)


def _sync_renders(fs: Fs, agents_home: Path, renders: dict[str, str], header: str) -> None:
    """Write renders by file name. A file without the marked header isn't
    ours: under a render's name it moves to backups, under another name it
    stays. A render left from an agent that is gone goes."""
    for file_name, content in sorted(renders.items()):
        dst = agents_home / file_name
        if os.path.lexists(dst) and not _is_render(dst, header):
            fs.backup(dst)
        fs.write(dst, content)
    if not agents_home.is_dir():
        return
    for entry in sorted(agents_home.iterdir()):
        if entry.name not in renders and _is_render(entry, header):
            fs.remove_file(entry)


def _is_render(path: Path, header: str) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    return path.read_bytes().startswith(header.encode("utf-8"))


def _markdown_agent(frontmatter: list[str], agent: Agent) -> str:
    """The marked header, frontmatter lines and the agent's body as prompt."""
    return _MARKDOWN_HEADER + "\n".join([*frontmatter, "---", "", agent.body.strip(), ""])


def _render_claude(agent: Agent, model: str) -> str:
    """A Claude Code agent. The model is passed in: a global agent inherits
    the session's, a project agent will get the model its level is bound to."""
    frontmatter = [
        f"name: {agent.name}",
        f"description: {_yaml_string(agent.description)}",
        f"model: {model}",
    ]
    if agent.effort:
        frontmatter.append(f"effort: {agent.effort}")
    frontmatter.append(f"tools: {', '.join(agent.tools)}")
    return _markdown_agent(frontmatter, agent)


def _render_opencode(agent: Agent) -> str:
    """A markdown agent, its body is the prompt. No model: a subagent without
    one runs on the model of the agent that called it."""
    frontmatter = [
        f"description: {_yaml_string(agent.description)}",
        "mode: subagent",
        "permissions:",
    ]
    for rule in _opencode_permissions(agent.tools):
        frontmatter.append(f"  - action: {rule.action}")
        # A bare * reads as a YAML alias, the resource is always quoted.
        frontmatter.append(f'    resource: "{rule.resource}"')
        frontmatter.append(f"    effect: {rule.effect}")
    return _markdown_agent(frontmatter, agent)


def _yaml_string(text: str) -> str:
    """YAML reads a JSON string as a double-quoted scalar, so quotes, colons
    and line breaks in text survive as they are."""
    return json.dumps(text, ensure_ascii=False)


def load(path: Path) -> Agent:
    """Read one AGENT.md the way the renders see it; SyncError if it can't be."""
    match = _FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise SyncError(f"{path}: no frontmatter found")
    fields = _parse_fields(match.group(1))
    name = path.parent.name
    # Links and renders are named after the dir, but Claude Code shows the
    # frontmatter name: a mismatch would split one agent into two names.
    if fields.get("name") != name:
        raise SyncError(f"{path}: frontmatter name {fields.get('name')!r} must equal the directory name {name!r}")

    tools = fields.get("tools", [])
    if isinstance(tools, str):
        tools = _split_list(tools)
    description = fields.get("description", name)
    if not isinstance(description, str):
        raise SyncError(f"{path}: description must be a string")
    model = fields.get("model")
    if model not in MODEL_LEVELS:
        raise SyncError(f"{path}: model {model!r} must be one of {list(MODEL_LEVELS)}")
    effort = fields.get("effort")
    if effort is not None and effort not in EFFORTS:
        raise SyncError(f"{path}: effort {effort!r} must be one of {list(EFFORTS)}")
    return Agent(name, description.strip(), tools, match.group(2), path, model, effort)


def _parse_fields(frontmatter: str) -> _Fields:
    """Parse the YAML subset AGENT.md uses: `key: value`, `key: |` block scalars
    and `key: [a, b]` flow lists. Stdlib has no YAML parser."""
    fields: _Fields = {}
    lines = frontmatter.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            i += 1
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "|":
            block: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or lines[i] == ""):
                block.append(lines[i])
                i += 1
            # Dedent by the two-space indent, drop trailing blank lines.
            dedented = (row[2:] if row.startswith("  ") else row for row in block)
            fields[key] = "\n".join(dedented).rstrip()
            continue
        if value.startswith("[") and value.endswith("]"):
            fields[key] = _split_list(value[1:-1])
        else:
            fields[key] = value
        i += 1
    return fields


def _split_list(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


class Permission(NamedTuple):
    """One OpenCode v2 `permissions` rule: the action on a resource gets the
    effect."""

    action: str
    resource: str
    effect: str


def _opencode_permissions(tools: list[str]) -> list[Permission]:
    """The agent's `permissions` rules, each on the "*" resource. Listed tools
    are allowed, except the shell: an allow there would outrank the global
    ask/deny rules, which must stay the last word on the shell. Without an
    editing tool editing is denied, without Bash the shell."""
    actions = []
    for tool in tools:
        action = _TOOL_TO_PERMISSION.get(tool)
        if action and action not in actions:
            actions.append(action)
    rules = [Permission(action, "*", "allow") for action in actions if action != "shell"]
    rules.extend(Permission(action, "*", "deny") for action in ("edit", "shell") if action not in actions)
    return rules
