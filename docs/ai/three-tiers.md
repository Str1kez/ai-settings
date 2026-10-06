# Three-Tier Boundaries

Every tool use falls into one of three tiers. When in doubt — assume the more restrictive tier.

## Always Do (no permission needed)

| Category | Action |
|---|---|
| Filesystem | Read any file in the cwd subtree |
| Filesystem | Search (grep/glob) in the cwd subtree |
| Git | `git status`, `git log`, `git diff`, `git show` (read-only) |
| Runtime | Run existing tests (`pytest`) |
| Info | `--version`, `--help`, docs lookups |
| Checks | Linters, type-checkers, formatters (read-only mode) |

## Ask First (user confirmation needed)

| Category | Action |
|---|---|
| Filesystem | Create directories outside standard cwd subtree |
| Deps | Install new dependencies (`uv add`, `uv pip install`, `pip install`) |
| Git | Commit, push, create/switch branches, rebase, merge |
| Runtime | Run destructive or long-running commands (DB migrations, build, deploy) |
| Network | Any API call with side effects (POST/PUT/PATCH/DELETE) |
| System | Sudo anything |

## Never (hard denied — no confirmation can override a live deny)

| Category | Action |
|---|---|
| Filesystem | `rm -rf` on paths outside cwd |
| Identity | Modify `git config user.email` or `user.name` without explicit request |
