# Git Workflow

## Commit and PR text

Commit format: skill `en-commit-message`. PR title and description: skill `ru-pr-description`.

## Branch naming

Format: `task-<PROJECT-KEY>-<issue-number>-<short-description-kebab-case>`.

The issue number comes from the tracker (Jira/GitLab). No `feat/`, `fix/`, etc. type prefixes — the tracker issue is the source of truth for what kind of change it is.

Examples:
- `task-BOTICS-123-github-oauth-login`
- `task-BOTICS-456-fix-expired-jwt`
- `task-BOTICS-789-upgrade-fastapi`

## Pull Requests

- **Prefer small PRs.** Split aggressively. No hard limit, but if the diff is >800 lines — pause and justify.
- **One PR = one logical change.** Don't mix refactoring with feature work.

## Pre-commit discipline

Before `git commit`:
1. Lint clean (`ruff check` / `npm run lint`).
2. Format applied (`ruff format` / `npm run format` / prettier).
3. Tests green (at minimum, the tests touching changed code).
4. **Read the full staged diff yourself** (`git diff --staged`). No blind commits.

## Merge strategy

- **Squash-merge by default** for feature branches into `main`.
- Preserve the PR title + description as the squash commit message.
- Use regular merge only when preserving individual commits has real value (major refactor series, coordinated multi-step change).
