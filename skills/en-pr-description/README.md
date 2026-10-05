# en-pr-description

Generates a PR title and description in English from the branch diff.

## When it's invoked

- Explicitly: "write a PR", "generate a PR description", "describe what I did on this branch".
- Automatically: before `gh pr create` without `--body`.

## When it's skipped

- The PR already has a description.
- Draft explicitly marked "wip".

## Usage

After `git push` (or when ready to open a PR):

1. Tell Claude: "write a PR".
2. It gathers context (`git log`, `git diff` against `main`) and produces a ready-to-use title + body.
3. Paste it into `gh pr create --title "..." --body "..."` or the GitHub UI.

## PR body template

```markdown
## TL;DR
<1–2 sentences>

## What changed
- item

## How I tested it
- pytest / npm test / manual steps

## Checklist
- [x] Tests pass
- [x] Linter is clean
- [ ] Changelog updated
- [ ] Documentation updated
```
