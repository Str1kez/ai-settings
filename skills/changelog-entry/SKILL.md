---
name: changelog-entry
version: 1.2.0
description: |
  Use when the user asks "обнови changelog / добавь запись в changelog", or after a
  user-visible change is committed.
  Also trigger automatically after a `feat:` or `fix:` commit.
  SKIP: for `chore:`, `docs:`, `test:`, `refactor:`, `style:`, `ci:`, `build:` commits
  unless the change is user-facing.
category: code
tags: [changelog, keep-a-changelog, russian]
---

# Purpose

Add an entry to the repo's root `CHANGELOG.md` following Keep a Changelog format, in Russian.

# Process

1. Read the root `CHANGELOG.md`.
2. Pick the language. Russian by default. If the existing entries are in another
   language, keep writing in that language.
3. Find or create the `## [Unreleased]` section.
4. Determine the sub-section from the commit type. If the file already uses its own
   headings, reuse them:

   | Change | Russian | English |
   |---|---|---|
   | `feat:` | `### Добавлено` | `### Added` |
   | `fix:` | `### Исправлено` | `### Fixed` |
   | breaking / removal | `### Удалено` | `### Removed` |
   | behavior change that isn't add/fix/remove | `### Изменено` | `### Changed` |

5. Add one entry in active voice, describing what the **user** sees change.
6. Preserve all other entries and sections exactly.

# Anti-patterns

- Mentioning implementation details (file names, function renames) unless user-visible.
- Duplicating an entry that already exists.
- Writing "добавлена новая функция" without specifics.
- Mixing languages within one `CHANGELOG.md`.
- Editing entries under a released version (only `[Unreleased]` is mutable).

# Output

Updated `CHANGELOG.md` content (full file) or a unified diff.
Ask the user to confirm before writing.
