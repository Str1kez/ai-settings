# CHANGELOG — en-commit-message

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), semantic versioning.

## [1.1.0] — 2026-11-06

### Changed
- Tone rules: describe the change from the user's perspective, keep the body dry, no hyperbole or sarcasm. The commit format now lives only here; `git-workflow.md` no longer repeats it. The `Closes BOTICS-42` example moved to `references/examples.md`.

## [1.0.0] — 2026-08-09

### Initial release
- Generate a conventional-commit message in English from `git diff --staged`.
- Support types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `style`, `perf`, `ci`, `build`.
- Optional scope derived from changed file paths.
- Message body in English, explaining WHY.
