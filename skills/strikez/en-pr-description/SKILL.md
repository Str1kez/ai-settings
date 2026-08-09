---
name: en-pr-description
version: 1.0.0
description: |
  Use when the user asks "write a PR / generate a PR description / describe what I did on this branch".
  Also trigger automatically before `gh pr create` when no `--body` argument was provided.
  SKIP: if the PR already has a description, or for draft PRs explicitly marked "wip".
category: code
tags: [git, github, pr, english]
---

# Purpose

Generate an English PR title + description from the branch diff and commit history.

# Process

1. Determine the base branch (`main` by default, or from a user-supplied argument).
2. `git log --oneline <base>..HEAD` — list commits in this branch.
3. `git diff <base>...HEAD --stat` — files changed.
4. `git diff <base>...HEAD` — full diff if under ~500 lines; otherwise summarize from stat + commit messages.
5. Write the **title** in English: one line, under 70 chars.
6. Write the **body** using the template below.

# Template (English)

```markdown
## TL;DR
<1–2 sentences: what and why>

## What changed
- <item>
- <item>

## How I tested it
- <commands or manual steps>
- <result>

## Checklist
- [x] Tests pass
- [x] Linter is clean
- [ ] Changelog updated (if there are user-visible changes)
- [ ] Documentation updated (if the public API changed)
```

# Output

Full title + body text, ready to paste into `gh pr create --title "..." --body "..."` or the GitHub UI.

# Anti-patterns

- Description in Russian.
- TL;DR that just lists commit types ("added feat, fix").
- Copying the full diff into the description.
- Skipping the checklist.
