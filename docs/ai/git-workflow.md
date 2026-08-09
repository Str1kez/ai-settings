# Git Workflow

## Commit messages — Conventional Commits

Format: `<type>(<scope>): <description>`

**Types** (English, lowercase): `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `style`, `perf`, `ci`, `build`.

**Scope** (optional, English, lowercase): module or component name, derived from changed file paths. Examples: `auth`, `api`, `db`, `skills/ru-commit-message`.

**Description** (**English**, imperative, lowercase first letter, no trailing period, ≤72 chars): what the commit does from the user's perspective.

Example:
```
feat(auth): add github oauth login

Closes BOTICS-42. Regular login/password stays as a fallback.
```

**Body** (optional, **English**): explains WHY, not WHAT. Separated from subject by a blank line. Lines wrap at ~72 chars.

## Branch naming

Format: `task-<PROJECT-KEY>-<issue-number>-<short-description-kebab-case>`.

The issue number comes from the tracker (Jira/GitLab). No `feat/`, `fix/`, etc. type prefixes — the tracker issue is the source of truth for what kind of change it is.

Examples:
- `task-BOTICS-123-github-oauth-login`
- `task-BOTICS-456-fix-expired-jwt`
- `task-BOTICS-789-upgrade-fastapi`

## Pull Requests

- **Title** — **Russian**, one line, under 70 chars.
- **Description** — Russian, uses the template below:

```markdown
## TL;DR
<1–2 предложения: что и зачем>

## Что изменилось
- <пункт 1>
- <пункт 2>

## Как тестировал
- pytest / npm test / ручные шаги
- результат

## Чек-лист
- [x] Тесты проходят
- [x] Линтер чист
- [ ] Changelog обновлён (если есть user-visible изменения)
- [ ] Документация обновлена (если изменился публичный API)
```

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

## Never

- `git push --force` on `main` or shared branches without explicit user confirmation in the current conversation.
- `--no-verify` to skip hooks.
- `git reset --hard` without confirming what would be lost.
- Committing `.env`, `*.pem`, `*.key`, credentials files.
