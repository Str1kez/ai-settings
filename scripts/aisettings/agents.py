"""Agents: agents/<name>/AGENT.md in Claude Code format is the only source.

Claude Code reads it as is, through a link per agent. OpenCode, Gemini and
Cursor get a markdown agent rendered from it, Codex a TOML one.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import NamedTuple, Union

from aisettings import tracked
from aisettings.fs import Fs, SyncError, link_target

# Claude Code tool -> OpenCode permission key. In OpenCode, edit covers write,
# edit and apply_patch.
_TOOL_TO_PERMISSION = {
    "Read": "read",
    "Grep": "grep",
    "Glob": "glob",
    "List": "list",
    "Bash": "bash",
    "Edit": "edit",
    "Write": "edit",
    "Task": "task",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
}
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_CLAUDE_AGENTS = Path(".claude/agents")
_OPENCODE_AGENTS = Path(".config/opencode/agents")
_GEMINI_AGENTS = Path(".gemini/agents")
_CURSOR_AGENTS = Path(".cursor/agents")
_CODEX_AGENTS = Path(".codex/agents")
# The first lines of a render: the mark tells our files from the user's.
_MARKER = "# managed-by: ai-settings"
_MARKDOWN_HEADER = f"---\n{_MARKER}\n"
_TOML_HEADER = f"{_MARKER}\n"
_TOML_LITERAL_QUOTES = "'''"

# Claude Code tool -> Gemini CLI tools. Tools with no entry have no Gemini
# counterpart and are left out.
_TOOL_TO_GEMINI = {
    "Read": ["read_file", "read_many_files"],
    "Grep": ["grep_search"],
    "Glob": ["glob", "list_directory"],
    "Bash": ["run_shell_command"],
    "Edit": ["replace"],
    "Write": ["write_file"],
    "WebFetch": ["web_fetch"],
    "WebSearch": ["google_web_search"],
}
_EDITING_TOOLS = {"Edit", "Write"}
# A tool outside this set is dropped silently by the renders, so a typo would
# quietly cost an agent its permission. The agent lint holds tools to it.
KNOWN_TOOLS = frozenset(_TOOL_TO_PERMISSION) | frozenset(_TOOL_TO_GEMINI)

# Runtime alias: no `X | Y` here, it must evaluate on Python 3.9.
_Fields = dict[str, Union[str, list[str]]]


class Agent(NamedTuple):
    name: str
    description: str
    tools: list[str]
    body: str
    path: Path


def sync(fs: Fs, repo: Path, home: Path) -> None:
    agents = _collect(repo)
    tracked.warn_untracked(repo, "agents", "AGENT.md")
    _sync_claude(fs, repo, home / _CLAUDE_AGENTS, agents)
    for agents_home, render in (
        (_OPENCODE_AGENTS, _render_opencode),
        (_GEMINI_AGENTS, _render_gemini),
        (_CURSOR_AGENTS, _render_cursor),
    ):
        renders = {f"{agent.name}.md": render(agent) for agent in agents}
        _sync_renders(fs, home / agents_home, renders, _MARKDOWN_HEADER)
    codex = {f"{agent.name}.toml": _render_codex(agent) for agent in agents}
    _sync_renders(fs, home / _CODEX_AGENTS, codex, _TOML_HEADER)


def _collect(repo: Path) -> list[Agent]:
    agents_dir = repo / "agents"
    if not agents_dir.is_dir():
        raise SyncError(f"agents dir not found: {agents_dir}")
    return [
        load(agent_dir / "AGENT.md")
        for agent_dir in tracked.tracked_dirs(repo, "agents", "AGENT.md")
    ]


def _sync_claude(fs: Fs, repo: Path, claude_agents: Path, agents: list[Agent]) -> None:
    """Link every agent. A link into repo/agents/ that matches no agent goes:
    its agent was renamed or deleted. Links elsewhere aren't ours."""
    linked = {f"{agent.name}.md" for agent in agents}
    for agent in agents:
        fs.link(agent.path, claude_agents / f"{agent.name}.md")
    if not claude_agents.is_dir():
        return
    for entry in sorted(claude_agents.iterdir()):
        if not entry.is_symlink() or entry.name in linked:
            continue
        if link_target(entry).is_relative_to(repo / "agents"):
            fs.unlink(entry)


def _sync_renders(
    fs: Fs, agents_home: Path, renders: dict[str, str], header: str
) -> None:
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
    return _MARKDOWN_HEADER + "\n".join(
        [*frontmatter, "---", "", agent.body.strip(), ""]
    )


def _is_read_only(agent: Agent) -> bool:
    return not _EDITING_TOOLS.intersection(agent.tools)


def _render_opencode(agent: Agent) -> str:
    """A markdown agent, its body is the prompt. No model: a subagent without
    one runs on the model of the agent that called it."""
    frontmatter = [
        f"description: {_yaml_string(agent.description)}",
        "mode: subagent",
        "permission:",
        *(
            f"  {key}: {value}"
            for key, value in _opencode_permission(agent.tools).items()
        ),
    ]
    return _markdown_agent(frontmatter, agent)


def _render_gemini(agent: Agent) -> str:
    """A markdown agent, its body is the prompt. No model: it inherits the
    parent's. Tools are what the agent is allowed to call."""
    tools = [
        gemini_tool
        for tool in agent.tools
        for gemini_tool in _TOOL_TO_GEMINI.get(tool, [])
    ]
    frontmatter = [
        f"name: {_yaml_string(agent.name)}",
        f"description: {_yaml_string(agent.description)}",
        "tools:",
        *(f"  - {tool}" for tool in tools),
    ]
    return _markdown_agent(frontmatter, agent)


def _render_cursor(agent: Agent) -> str:
    """A markdown agent, its body is the prompt. It runs on the parent's model;
    without Edit/Write it is read-only."""
    frontmatter = [
        f"name: {_yaml_string(agent.name)}",
        f"description: {_yaml_string(agent.description)}",
        "model: inherit",
    ]
    if _is_read_only(agent):
        frontmatter.append("readonly: true")
    return _markdown_agent(frontmatter, agent)


def _render_codex(agent: Agent) -> str:
    """A TOML agent. The prompt is a literal string, so it can't hold the
    literal quotes. Without Edit/Write the sandbox is read-only."""
    prompt = agent.body.strip()
    if _TOML_LITERAL_QUOTES in prompt:
        raise SyncError(f"{agent.path}: body holds {_TOML_LITERAL_QUOTES}")
    lines = [
        f"name = {_toml_string(agent.name)}",
        f"description = {_toml_string(agent.description)}",
    ]
    if _is_read_only(agent):
        lines.append('sandbox_mode = "read-only"')
    quotes = _TOML_LITERAL_QUOTES
    lines.append(f"developer_instructions = {quotes}\n{prompt}\n{quotes}")
    return _TOML_HEADER + "\n".join(lines) + "\n"


def _toml_string(text: str) -> str:
    """A JSON string is a valid TOML basic string: same escapes."""
    return json.dumps(text, ensure_ascii=False)


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
        raise SyncError(
            f"{path}: frontmatter name {fields.get('name')!r} must equal the "
            f"directory name {name!r}"
        )

    tools = fields.get("tools", [])
    if isinstance(tools, str):
        tools = _split_list(tools)
    description = fields.get("description", name)
    if not isinstance(description, str):
        raise SyncError(f"{path}: description must be a string")
    return Agent(name, description.strip(), tools, match.group(2), path)


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


def _opencode_permission(tools: list[str]) -> dict[str, str]:
    """Listed tools are allowed. Without Edit/Write editing is denied, without
    Bash the shell; other keys keep OpenCode defaults."""
    keys = [_TOOL_TO_PERMISSION[tool] for tool in tools if tool in _TOOL_TO_PERMISSION]
    permission = dict.fromkeys(keys, "allow")
    permission.setdefault("edit", "deny")
    permission.setdefault("bash", "deny")
    return permission
