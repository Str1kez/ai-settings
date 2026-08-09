# CHANGELOG — en-commit-message

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), semantic versioning.

## [1.0.0] — 2026-08-09

### Initial release
- Generate a conventional-commit message in English from `git diff --staged`.
- Support types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `style`, `perf`, `ci`, `build`.
- Optional scope derived from changed file paths.
- Message body in English, explaining WHY.
