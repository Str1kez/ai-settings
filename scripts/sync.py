#!/usr/bin/env python3
"""Deploy ai-settings artifacts into harness homes. install.sh runs `sync.py all`.

Runs on the system python3 of a clean Mac (3.9): stdlib only, no match/case.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aisettings import agents, claude, log, rules, skills
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
            skills.sync(fs, REPO, home)
        elif args.artifact == "agents":
            agents.sync(fs, REPO, home)
        elif args.artifact == "claude":
            claude.sync(fs, REPO, home)
        elif args.artifact == "project-agents":
            _sync_project_agents(fs, args)
        else:
            # Skills first: a skills dir linked into the repo stops the run
            # before anything is written.
            skills.sync(fs, REPO, home)
            rules.sync(fs, REPO, home)
            agents.sync(fs, REPO, home)
            claude.sync(fs, REPO, home)
    except SyncError as exc:
        log.error(str(exc))
        return 1
    return 0


def _sync_project_agents(fs: Fs, args: argparse.Namespace) -> None:
    """stdout carries the project agents, one path relative to the project
    per line: init-project.sh keeps them out of git. Logs go to stderr."""
    claude_models = agents.parse_models(args.claude_models, "claude") if args.claude_models is not None else None
    opencode_models = (
        agents.parse_models(args.opencode_models, "opencode") if args.opencode_models is not None else None
    )
    ours = agents.sync_project(fs, REPO, args.project, claude_models, opencode_models)
    if not args.dry_run:
        for path in ours:
            print(path)


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true", help="print the changes, make none")

    parser = argparse.ArgumentParser(description=__doc__)
    artifacts = parser.add_subparsers(dest="artifact", required=True)
    artifacts.add_parser("all", parents=[common], help="every artifact below")
    rules_parser = artifacts.add_parser(
        "rules",
        parents=[common],
        help="links to CLAUDE.md and GEMINI.md, flat AGENTS.md for Codex, OpenCode and Cursor",
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
        help="agents/<name>/AGENT.md linked into ~/.claude/agents, rendered into ~/.config/opencode/agents",
    )
    artifacts.add_parser(
        "claude",
        parents=[common],
        help="settings/claude-settings.json merged into ~/.claude/settings.json, "
        "the hook scripts it runs linked into ~/.claude/hooks",
    )
    project_agents = artifacts.add_parser(
        "project-agents",
        parents=[common],
        help="agents/<name>/AGENT.md rendered with concrete models into PROJECT/.claude/agents "
        "and PROJECT/.opencode/agents; prints the written files, relative to PROJECT",
    )
    project_agents.add_argument("project", type=_existing_dir, metavar="PROJECT")
    project_agents.add_argument(
        "--claude-models",
        metavar="LEVEL=MODEL,...",
        help="e.g. frontier=opus,standard=sonnet; writes the Claude Code agents",
    )
    project_agents.add_argument(
        "--opencode-models",
        metavar="LEVEL=PROVIDER/MODEL,...",
        help="e.g. frontier=anthropic/opus,standard=openai/gpt; writes the OpenCode agents",
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
