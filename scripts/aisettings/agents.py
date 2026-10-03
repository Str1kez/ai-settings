"""Agents: agents/<name>/AGENT.md in Claude Code format is the only source.

OpenCode gets them the legacy way: prompts in agent-prompts/ plus a managed
`agent` block merged into opencode.jsonc with jq. ADR 0001 moves OpenCode to
markdown agents.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple, Union

from aisettings.fs import Fs, SyncError

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
_OPENCODE_SKELETON = '{\n  "$schema": "https://opencode.ai/config.json"\n}\n'

# Runtime alias: no `X | Y` here, it must evaluate on Python 3.9.
_Fields = dict[str, Union[str, list[str]]]


class _Agent(NamedTuple):
    name: str
    description: str
    tools: list[str]
    body: str


def sync(fs: Fs, repo: Path, home: Path) -> None:
    """Write OpenCode prompts and merge the managed agent block into opencode.jsonc.

    model is never set: it belongs to the user, and the merge keeps it.
    """
    agents_dir = repo / "agents"
    if not agents_dir.is_dir():
        raise SyncError(f"agents dir not found: {agents_dir}")

    opencode = home / ".config/opencode"
    managed: dict[str, object] = {}
    for path in sorted(agents_dir.glob("*/AGENT.md")):
        agent = _load(path)
        managed[agent.name] = {
            "description": agent.description,
            "mode": "subagent",
            "permission": _permission(agent.tools),
            "prompt": f"{{file:./agent-prompts/{agent.name}.md}}",
        }
        prompt = opencode / "agent-prompts" / f"{agent.name}.md"
        fs.write(prompt, agent.body.lstrip() + "\n")

    config = opencode / "opencode.jsonc"
    current = (
        config.read_text(encoding="utf-8") if config.exists() else _OPENCODE_SKELETON
    )
    fs.update_in_place(config, _jq_merge(current, {"agent": managed}))


def _load(path: Path) -> _Agent:
    match = _FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise SyncError(f"{path}: no frontmatter found")
    fields = _parse_fields(match.group(1))
    name = path.parent.name

    tools = fields.get("tools", [])
    if isinstance(tools, str):
        tools = _split_list(tools)
    description = fields.get("description", name)
    if not isinstance(description, str):
        raise SyncError(f"{path}: description must be a string")
    return _Agent(name, description.strip(), tools, match.group(2))


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


def _permission(tools: list[str]) -> dict[str, str]:
    """Listed tools are allowed. Without Edit/Write editing is denied, without
    Bash the shell; other keys keep OpenCode defaults."""
    keys = [_TOOL_TO_PERMISSION[tool] for tool in tools if tool in _TOOL_TO_PERMISSION]
    permission = dict.fromkeys(keys, "allow")
    permission.setdefault("edit", "deny")
    permission.setdefault("bash", "deny")
    return permission


def _jq_merge(config: str, managed: dict[str, object]) -> str:
    """Deep-merge managed into config: our fields win, the user's fields stay."""
    if shutil.which("jq") is None:
        raise SyncError("jq not found, agents not merged into opencode.jsonc")
    managed_json = json.dumps(managed, ensure_ascii=False)
    result = subprocess.run(
        ["jq", "--argjson", "managed", managed_json, ". * $managed"],
        input=config,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise SyncError(f"jq merge into opencode.jsonc: {result.stderr.strip()}")
    return result.stdout
