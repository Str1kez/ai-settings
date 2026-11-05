---
name: ship
version: 1.0.0
description: |
  Use when work on a branch is finished and has to reach main: "доведи ветку",
  "оформи PR", "смёрджи", "закрой задачу", "ship it".
  Runs checks, CHANGELOG, commit, PR, merge, local branch cleanup.
  SKIP: when asked only for a commit message or a PR text, when there is no git
  repository, when the user is still mid-implementation.
category: code
tags: [git, pr, merge, workflow]
---

# Purpose

Carry a finished branch to main through one fixed sequence. Tags and versions
belong to repos that have them: step 8 handles those and is skipped everywhere else.

# Process

How far to go is set by the request: "оформи PR" stops after step 5, "смёрджи" or
"доведи ветку" runs through step 7.

1. **State.** Run `git status`, `git branch --show-current`, `git log --oneline -5`.
   Done when you know the base branch, the current branch and whether the tree is dirty.
   On the base branch with changes, create a branch named per `git-workflow.md`
   (`task-<KEY>-<N>-<description>`). Take the key and number from the user or the
   tracker; ask once when neither is known.
2. **Checks.** Run the lint and test commands from the repo's `AGENTS.md`, `CLAUDE.md`
   or `Makefile`. Done when every check that ran is green. A red check ends the run:
   report the output and stop.
3. **CHANGELOG.** When the repo has a root `CHANGELOG.md` and the change is
   user-visible, invoke `changelog-entry`. Done when the entry sits in `[Unreleased]`
   or you can name why none is needed.
4. **Commit.** Stage the change, read the whole `git diff --staged`, invoke
   `en-commit-message`. Done when `git status` is clean. Files that may hold secrets
   (`.env`, `*.pem`, `*.key`, `credentials.json`) stay out of the stage.
5. **Push and PR.** `git push -u origin <branch>`, invoke `ru-pr-description`,
   `gh pr create`. Done when you have the PR URL.
6. **Merge.** `gh pr checks` is green, then `gh pr merge --squash`. Done when the PR
   state is `MERGED`. Pending checks mean wait; failed checks mean stop and report.
7. **Cleanup.** `git checkout <base>`, `git pull`, `git branch -d <branch>`. The
   remote branch stays on origin as history; delete it only on a separate request.
8. **Release, only for versioned repos.** `git tag` is non-empty and `CHANGELOG.md`
   has version headers: follow the repo's release doc (`docs/agents/release.md` or
   the section in `AGENTS.md`). Done when the repo's own release checklist is closed.
   No tags and no version headers: finish at step 7.

# Output

One short report: PR URL, merge state, checks that ran, steps skipped and why.
