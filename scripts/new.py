#!/usr/bin/env python3
"""Scaffold a new skill or agent in the repo: `new.py skill|agent <name>`.

Runs on the system python3 of a clean Mac (3.9): stdlib only, no match/case.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

from aisettings import log
from aisettings.fs import SyncError

REPO = Path(__file__).resolve().parent.parent
# The Agent Skills name rule; agents follow it too, their name is a file name
# in every harness.
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SKILL_MD = """\
---
name: {name}
version: 1.0.0
description: |
  Use when <explicit trigger: when the user directly asks>.
  Also trigger automatically when <automatic trigger: a pattern in the context>.
  SKIP: <explicit anti-trigger: when NOT to invoke>.
category: code
tags: []
---

# Purpose
<One sentence: what the skill does and why.>

# Process
1. ...
2. ...

# Output format
<The output format, ideally with a short example.>
"""

SKILL_README_MD = """\
# {name}

<Что делает скилл, как вызывается, примеры.>
"""

SKILL_CHANGELOG_MD = """\
# Changelog

## [1.0.0] — {today}

### Добавлено

- Первая версия скилла.
"""

AGENT_MD = """\
---
name: {name}
description: |
  Use when <explicit trigger: when to call this agent>.
  SKIP: <explicit anti-trigger: when NOT to call it>.
model: sonnet
tools: [Read, Grep, Glob]
---

# Role

<One or two sentences: who the agent is and what it answers for.>

# Process

1. ...
2. ...
"""


def main() -> int:
    args = _parser().parse_args()
    try:
        _check_name(args.name)
        if args.kind == "skill":
            _new_skill(args.name)
        else:
            _new_agent(args.name)
    except SyncError as exc:
        log.error(str(exc))
        return 1
    return 0


def _new_skill(name: str) -> None:
    today = datetime.date.today().isoformat()
    _create(
        REPO / "skills" / name,
        {
            "SKILL.md": SKILL_MD.format(name=name),
            "README.md": SKILL_README_MD.format(name=name),
            "CHANGELOG.md": SKILL_CHANGELOG_MD.format(today=today),
        },
    )
    log.info("Next:")
    log.info("  1. fill in SKILL.md (description first), README.md, CHANGELOG.md")
    log.info(f"  2. git add skills/{name}: untracked skills are not deployed")
    log.info("  3. .venv/bin/python -m pytest tests/skill_lint -v")
    log.info("  4. scripts/install.sh --dry-run, then scripts/install.sh")


def _new_agent(name: str) -> None:
    _create(REPO / "agents" / name, {"AGENT.md": AGENT_MD.format(name=name)})
    log.info("Next:")
    log.info("  1. fill in AGENT.md (description first, then tools and model)")
    log.info(f"  2. git add agents/{name}: untracked agents are not deployed")
    log.info("  3. .venv/bin/python -m pytest tests/agent_lint -v")
    log.info("  4. scripts/install.sh --dry-run, then scripts/install.sh")


def _check_name(name: str) -> None:
    if not NAME_RE.match(name):
        raise SyncError(
            f"bad name {name!r}: lowercase letters and digits in words joined by single hyphens, {NAME_RE.pattern}"
        )


def _create(target: Path, files: dict[str, str]) -> None:
    """Make target and its files. An existing target is never touched."""
    try:
        target.mkdir(parents=True)
    except FileExistsError:
        raise SyncError(f"{target} already exists, nothing was written") from None
    for file_name, text in files.items():
        (target / file_name).write_text(text, encoding="utf-8")
    log.ok(f"created {target.relative_to(REPO)}: {', '.join(files)}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    kinds = parser.add_subparsers(dest="kind", required=True)
    for kind, help_text in (
        ("skill", "skills/<name>/ with SKILL.md, README.md and CHANGELOG.md"),
        ("agent", "agents/<name>/AGENT.md"),
    ):
        kinds.add_parser(kind, help=help_text).add_argument("name")
    return parser


if __name__ == "__main__":
    sys.exit(main())
