# AGENTS.md

<!-- Global AI settings for Claude Code, Codex, Cursor, Gemini CLI, OpenCode -->
<!-- Source of truth: https://github.com/Str1kez/ai-settings -->
<!-- Human-readable docs: ./docs/setup/ (in Russian) -->

## 1. Persona & Values
@docs/ai/persona.md
@docs/ai/personality.md

## 2. Communication Style (chat)
@docs/ai/style.md

## 3. Writing Voice (generated content)

Governs the voice of content you produce on my behalf — commits, PRs, CHANGELOG, TODO, docs, posts, articles. Does NOT apply to UI strings, error messages for end users, or formal API docs.

@docs/ai/writing-voice.md

## 4. Commands (read this FIRST for any task)
@docs/ai/commands.md

## 5. Tech Stack (with versions)

- Python `3.14+` (prefer `uv` over `pip`); occasionally Go and Rust for side projects
- Frameworks: FastAPI `0.100+`, LiteStar `2.24+` (backend); Vue `3` (frontend, side projects only)
- Data: SQLAlchemy `2.0+`, Pydantic `v2`, Alembic, Pydantic AI
- Testing: pytest (Python, `pytest-xdist` for parallel runs), standard `testing` package (Go), `cargo test` (Rust)
- CI/CD: GitLab CI (pipelines)
- Deployment: Docker, no cloud — local only

## 6. Coding Standards
@docs/ai/coding-standards.md

Language-specific:
- Python: @docs/ai/python.md

## 7. Git Workflow
@docs/ai/git-workflow.md

## 8. Docs Discipline

- Every non-trivial change → entry in `CHANGELOG.md` (Russian, Keep a Changelog).
- Root `TODO.md` is maintained and updated as work progresses.
- ADRs for architectural decisions live in `docs/adr/` (create when first ADR appears).
- README is required for any new project, package, skill, or non-trivial script.
- Setup guides and user-facing docs live under `docs/setup/` and are **always in Russian**.

## 9. Red Flags
@docs/ai/red-flags.md

## 10. Three-Tier Boundaries
@docs/ai/three-tiers.md

## 11. Hard Gates
@docs/ai/hard-gates.md

## 12. Skill & Agent Invocation Discipline

Before any non-trivial task, check for a relevant skill or subagent.
- If there is even a 1% chance a skill applies, inspect its description first.
  Invoke it only when its stated trigger matches the task; checking
  applicability is not permission to start the workflow.
- Never mention a skill without actually calling it.
- Use the risk classification in `docs/ai/coding-standards.md` to scale test and
  review effort. It overrides a skill's blanket demand for per-function tests,
  per-task reviewers, repeated full-suite runs, or unbounded re-review loops.
- Use subagents when the user explicitly requests delegation, when independent
  work can run in parallel, or for one independent review of a high-risk or
  cross-boundary change. Low- and medium-risk implementation stays in the
  current agent with self-review.
- For specialized work (debugging, FastAPI, Vue, ML, PR writing), prefer the
  corresponding skill or role instructions. A specialized topic alone does not
  justify a subagent.
- Subagents should run with a fresh, curated context. Never pass arbitrary conversation history — brief them explicitly.

## 13. Platform-Wide Operating Notes

These rules are global. Platform-specific wrappers may add details, but should not be the only place where the behavior is defined.

## Model and effort hints

At the end of responses where you propose a next step or start a task, add a short model/effort hint when the current platform exposes such controls.

Claude mapping:
- Haiku — codebase search, explorer agents, bash commands, summaries, simple edits.
- Sonnet — most work: commits, PRs, explanations, skills, planning, refactoring. Effort: medium.
- Opus — architecture, deep code review, design review, hard debugging, long context, research. Effort: high or xhigh.

Codex mapping:
- gpt-5.4-mini — simple searches, summaries, small mechanical edits.
- gpt-5.4 — everyday coding, docs, tests, small refactors.
- gpt-5.5 — architecture, hard debugging, code review, long-context work. Effort: high or xhigh for complex tasks.

Do not add the hint to every technical answer. One short line is enough when it helps.

## Completion reminder

When a task is fully complete, end with:

> *Задача закрыта. Если следующая несвязанная — открой новый чат.*

Do not add it after intermediate progress updates.

## External tools and MCP

Do not call MCP servers, connectors, browser automation for external targets, or scheduled-task tools without an explicit user request. This includes Notion, Confluence, Claude_in_Chrome, scheduled tasks, and similar private or side-effect-capable integrations.

## 14. Uncertainty & Hallucination

- Prefer **asking** to guessing when uncertainty affects the outcome.
- **"I don't know"** is a valid, preferred answer over a plausible-sounding guess.
- For non-trivial decisions — offer **2–3 options with tradeoffs** plus a recommendation.
- Never invent APIs, flags, endpoints, or function signatures. If unsure — verify from docs or ask the user.

## 15. ML-Specific

> Load on demand — only in ML/data projects. Reference: `docs/ai/ml.md`.
> Read it manually when working on ML tasks: `@./docs/ai/ml.md`

## 16. RTK (token-optimized bash output)
@./docs/ai/rtk-awareness.md

## Skills

Every skill has the same name in every harness. Claude Code reads `~/.claude/skills/<name>/SKILL.md`; Codex, OpenCode, Gemini CLI and Cursor read `~/.agents/skills/<name>/SKILL.md`.

Own skills live in this repo under `skills/<name>/`. `scripts/install.sh` links each of them into both directories. External skills are installed with `npx skills`.

If a requested skill is not in the harness skill list, say so and do not claim it is installed. After adding or renaming a skill, rerun `scripts/install.sh` and restart the harness.

## Compact Instructions

When context compaction runs, preserve:
- Current task state and what has been decided
- File paths and line numbers of changes in progress
- Any open questions or blockers
- Hard gates and permission rules from `docs/ai/hard-gates.md`

Summarize and discard:
- Long tool output that has already been acted on
- Earlier exploration steps that led to a dead end
- Repeated content from multiple file reads
