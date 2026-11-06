# Release checklist

Version `X.Y.Z`, date `YYYY-MM-DD`. Past releases: `git show c94d971` (1.0.0), `git show eeee8ab` (1.0.1), `gh pr view 2`.

1. Branch `release-X.Y.Z` from a fresh `main`.
2. `CHANGELOG.md`: move the content of `[Unreleased]` under `## [X.Y.Z] — YYYY-MM-DD` with a short intro line. Leave an empty `[Unreleased]` above it.
3. Bump the version in `pyproject.toml` and in `uv.lock` (the `ai-settings` package entry).
4. `TODO.md`: close the items this release closes, move them to "Сделано", drop stale entries from "Следующее".
5. `make check` must pass: ruff check and format, both mypy runs, pytest, `sync.py rules --check`.
6. PR in Russian via skill `ru-pr-description`. Title: `Релиз X.Y.Z: …`.
7. After the merge: annotated tag `vX.Y.Z` on the merge commit in `origin/main`, then `git push origin vX.Y.Z`. Delete only the local branch; the remote one stays in history. Then pull `main`.
