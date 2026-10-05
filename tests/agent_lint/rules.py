"""Agent-lint rules: what an agents/<name>/AGENT.md must satisfy so that Claude
Code reads it and sync.py renders it for the other harnesses."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from aisettings import agents
from aisettings.fs import SyncError

REPO_ROOT = Path(__file__).resolve().parents[2]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MIN_DESCRIPTION_LENGTH = 100
# "Use when/after/for ...", "TRIGGER when ...": the agents state it either way.
TRIGGER_RE = re.compile(r"\b(Use|Trigger|TRIGGER)\b")
SKIP_RE = re.compile(r"\b(SKIP|Do NOT use)\b")
# What scripts/new.py leaves in a draft: <explicit trigger: ...>.
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
TOML_LITERAL_QUOTES = "'''"


def discover_agent_dirs(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Every dir under agents/ that holds a file git tracks, with or without
    an AGENT.md: a dir without one is a forgotten file, not a non-agent."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "agents"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    files = (Path(rel) for rel in result.stdout.split("\0") if rel)
    return sorted({repo_root / f.parent for f in files if len(f.parts) > 2})


def problems(agent_dir: Path) -> list[str]:
    """What is wrong with the agent in agent_dir; empty if nothing."""
    path = agent_dir / "AGENT.md"
    if not path.is_file():
        return [f"{path} is missing"]
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        return ["no frontmatter between --- lines"]
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return [f"frontmatter is not valid YAML: {exc}"]
    if not isinstance(frontmatter, dict):
        return ["frontmatter must be a YAML mapping"]

    found = _name_problems(frontmatter, agent_dir.name)
    found += _description_problems(frontmatter.get("description"))
    tools = _tools(frontmatter.get("tools"))
    found += _tools_problems(tools)
    if not match.group(2).strip():
        found.append("body is empty: it is the agent's prompt")
    if TOML_LITERAL_QUOTES in match.group(2):
        found.append(
            f"body holds {TOML_LITERAL_QUOTES}: the Codex render can't carry it"
        )
    return found or _renderer_problems(path, frontmatter, tools)


def _name_problems(frontmatter: dict[str, Any], dir_name: str) -> list[str]:
    name = frontmatter.get("name")
    found = []
    if name != dir_name:
        found.append(
            f"name {name!r} must equal the directory name {dir_name!r}: "
            "Claude Code shows the name, links and renders use the directory"
        )
    if not NAME_RE.match(dir_name):
        found.append(f"directory name {dir_name!r} doesn't match {NAME_RE.pattern}")
    return found


def _description_problems(description: Any) -> list[str]:
    if not isinstance(description, str) or not description.strip():
        return ["description must be a non-empty string"]
    found = []
    if len(description) < MIN_DESCRIPTION_LENGTH:
        found.append(
            f"description too short ({len(description)} chars, "
            f"need >={MIN_DESCRIPTION_LENGTH})"
        )
    if not TRIGGER_RE.search(description):
        found.append("description must say when to use the agent: 'Use ...'")
    if not SKIP_RE.search(description):
        found.append("description must contain 'SKIP' or 'Do NOT use'")
    if PLACEHOLDER_RE.search(description):
        found.append("description still holds a <placeholder> from the scaffold")
    return found


def _tools(raw: Any) -> list[str] | None:
    """tools as the renderers need it: a YAML list or a comma-separated string."""
    if isinstance(raw, str):
        return [tool.strip() for tool in raw.split(",") if tool.strip()]
    if isinstance(raw, list) and all(isinstance(tool, str) for tool in raw):
        return raw
    return None


def _tools_problems(tools: list[str] | None) -> list[str]:
    if not tools:
        return ["tools must be a non-empty list of tool names"]
    unknown = sorted(set(tools) - agents.KNOWN_TOOLS)
    if unknown:
        return [
            f"unknown tools {unknown}: the renders would drop them silently; "
            f"known: {sorted(agents.KNOWN_TOOLS)}"
        ]
    return []


def _renderer_problems(
    path: Path, frontmatter: dict[str, Any], tools: list[str] | None
) -> list[str]:
    """sync.py parses frontmatter with its own small YAML subset. The agent must
    come out of it as YAML reads it."""
    try:
        agent = agents.load(path)
    except SyncError as exc:
        return [str(exc)]
    found = []
    if agent.description != frontmatter["description"].strip():
        found.append(
            "sync.py reads description differently from YAML: "
            "use `description: |` or a one-line value"
        )
    if agent.tools != tools:
        found.append("sync.py reads tools differently from YAML: use `[A, B]`")
    return found
