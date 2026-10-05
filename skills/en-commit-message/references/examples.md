# Examples

## feat — new functionality

```
feat(api): add /users/me/preferences endpoint
```

```
feat(auth): support magic-link login

Alternative to a password — a link sent via email. Password stays
the default; magic-link is enabled via the `magic_link_auth` feature flag.
```

## fix — bug fix

```
fix(auth): revoke stale JWT on password change
```

```
fix(billing): compute prorated refund correctly on cancellation

Before: full-rate refund. Now: prorated to the remaining subscription
days. Regression test added.
```

## refactor — refactoring without behavior change

```
refactor(db): extract session into a dependency instead of a global
```

## docs — documentation only

```
docs(readme): update the uv installation section
```

## test — tests only

```
test(auth): add regression test for expired token
```

## chore — maintenance, dependencies, configs

```
chore(deps): bump FastAPI to 0.110
```

```
chore: set up pre-commit hooks for ruff and mypy
```

## style — formatting, no logic change

```
style: apply ruff format across the whole repo
```

## perf — performance

```
perf(api): cache list_users result for 60 seconds
```

## ci / build

```
ci(github): add skill-lint run on every PR
```

```
build: update lockfile after dependency bump
```
