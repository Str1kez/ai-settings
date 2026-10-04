#!/usr/bin/env python3
"""Deploy ai-settings artifacts into harness homes. install.sh runs `sync.py all`.

Runs on the system python3 of a clean Mac (3.9): stdlib only, no match/case.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aisettings import agents, claude, legacy, log, rules, skills
from aisettings.fs import Fs, SyncError

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    args = _parser().parse_args()
    fs = Fs(REPO, dry_run=args.dry_run)
    home = Path.home()
    try:
        if args.artifact == "rules":
            if args.check:
                rules.check(REPO)
            elif args.cursor_project:
                rules.sync_cursor_project(fs, REPO, args.cursor_project)
            else:
                rules.sync(fs, REPO, home)
        elif args.artifact == "skills":
            legacy.migrate_skills(fs, REPO, home)
            skills.sync(fs, REPO, home)
        elif args.artifact == "agents":
            legacy.migrate_agents(fs, REPO, home)
            agents.sync(fs, REPO, home)
        elif args.artifact == "claude":
            legacy.migrate_hooks(fs, REPO, home)
            claude.sync(fs, REPO, home)
        else:
            # Skills first: they migrate the old layout, and a layout they
            # can't handle aborts the run before rules and agents are written.
            legacy.migrate_skills(fs, REPO, home)
            skills.sync(fs, REPO, home)
            rules.sync(fs, REPO, home)
            legacy.migrate_agents(fs, REPO, home)
            agents.sync(fs, REPO, home)
            legacy.migrate_hooks(fs, REPO, home)
            claude.sync(fs, REPO, home)
    except SyncError as exc:
        log.error(str(exc))
        return 1
    return 0


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dry-run", action="store_true", help="print the changes, make none"
    )

    parser = argparse.ArgumentParser(description=__doc__)
    artifacts = parser.add_subparsers(dest="artifact", required=True)
    artifacts.add_parser("all", parents=[common], help="every artifact below")
    rules_parser = artifacts.add_parser(
        "rules",
        parents=[common],
        help="links to CLAUDE.md and GEMINI.md, flat AGENTS.md for Codex, "
        "OpenCode and Cursor",
    )
    mode = rules_parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="resolve @imports and fail on a missing one, write nothing",
    )
    mode.add_argument(
        "--cursor-project",
        type=_existing_dir,
        metavar="PATH",
        help="write only PATH/.cursor/rules/ai-settings.mdc",
    )
    artifacts.add_parser(
        "skills",
        parents=[common],
        help="skills/<skill> into ~/.claude/skills and ~/.agents/skills",
    )
    artifacts.add_parser(
        "agents",
        parents=[common],
        help="agents/<name>/AGENT.md linked into ~/.claude/agents, rendered "
        "into ~/.config/opencode/agents",
    )
    artifacts.add_parser(
        "claude",
        parents=[common],
        help="settings/claude-settings.json merged into ~/.claude/settings.json, "
        "the hook scripts it runs linked into ~/.claude/hooks",
    )
    return parser


def _existing_dir(value: str) -> Path:
    """A typo in the project path must not create a new directory tree."""
    path = Path(value).resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"not a directory: {value}")
    return path


if __name__ == "__main__":
    sys.exit(main())
