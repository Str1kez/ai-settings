"""Reusable skill-lint rules: link resolution and duplicate detection.

Pure functions over paths so that the negative tests can run them on fixtures
with a fixture-local repo root.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import yaml

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
FENCE_RE = re.compile(r"^(```|~~~).*?^\1[ \t]*$", re.DOTALL | re.MULTILINE)
CODE_SPAN_RE = re.compile(r"`[^`\n]+`")
INLINE_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
LINK_DEFINITION_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*<?(\S+?)>?\s*$", re.MULTILINE)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
# Directories the Agent Skills spec reserves inside a skill folder. A code span
# starting with one of them is a reference to a bundled file, not prose.
BUNDLED_PATH_RE = re.compile(r"^(?:references|assets|scripts)/[^\s<>*{}]*$")


@dataclass(frozen=True)
class Declaration:
    """One name declared by a skill or an agent."""

    name: str
    description: str
    path: Path


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    parsed = yaml.safe_load(match.group(1))
    return parsed if isinstance(parsed, dict) else {}


def _strip_fences(text: str) -> str:
    return FENCE_RE.sub("", text)


def _link_targets(text: str) -> list[str]:
    prose = CODE_SPAN_RE.sub("", _strip_fences(text))
    return INLINE_LINK_RE.findall(prose) + LINK_DEFINITION_RE.findall(prose)


def _bundled_paths(text: str) -> list[str]:
    spans = (span.strip("`") for span in CODE_SPAN_RE.findall(_strip_fences(text)))
    return [span for span in spans if BUNDLED_PATH_RE.match(span)]


def _link_problem(target: str, base: Path, repo_root: Path) -> str | None:
    if SCHEME_RE.match(target) or target.startswith("#"):
        return None
    path_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path_part:
        return None
    if path_part.startswith("/"):
        return f"{target}: absolute path, use a relative one"
    resolved = (base / path_part).resolve()
    if not resolved.is_relative_to(repo_root.resolve()):
        return f"{target}: points outside the repo"
    if not resolved.exists():
        return f"{target}: not found"
    return None


def find_broken_links(md_file: Path, skill_dir: Path, repo_root: Path) -> list[str]:
    """Return one message per unresolved reference in md_file.

    Markdown links resolve against the file's own directory. Code spans that
    start with references/, assets/ or scripts/ resolve against the skill
    folder, because that is how SKILL.md points at its bundled files.
    External URLs are skipped, anchors are ignored.
    """
    text = md_file.read_text(encoding="utf-8")
    problems = [
        problem
        for target in _link_targets(text)
        if (problem := _link_problem(target, md_file.parent, repo_root))
    ]
    problems += [
        problem
        for target in _bundled_paths(text)
        if (problem := _link_problem(target, skill_dir, repo_root))
    ]
    return problems


def _normalize(description: str) -> str:
    return " ".join(description.lower().split())


def find_duplicates(skills: list[Declaration], agents: list[Declaration]) -> list[str]:
    """Report identical names, name collisions with agents, identical descriptions.

    Descriptions are compared exactly after case and whitespace folding. A
    similarity threshold would flag sibling skills such as en-pr-description
    and ru-pr-description, which legitimately share most of their wording.
    """
    problems: list[str] = []

    by_name: dict[str, list[Path]] = defaultdict(list)
    for skill in skills:
        by_name[skill.name].append(skill.path)
    for name, paths in sorted(by_name.items()):
        if len(paths) > 1:
            where = sorted(map(str, paths))
            problems.append(f"skill name '{name}' declared in {where}")

    agent_names = {agent.name: agent.path for agent in agents}
    for skill in skills:
        if skill.name in agent_names:
            problems.append(
                f"skill '{skill.name}' ({skill.path}) collides with agent "
                f"{agent_names[skill.name]}"
            )

    by_description: dict[str, list[str]] = defaultdict(list)
    for skill in skills:
        if skill.description:
            by_description[_normalize(skill.description)].append(skill.name)
    for names in by_description.values():
        if len(names) > 1:
            problems.append(f"identical description in skills {sorted(names)}")

    return problems
