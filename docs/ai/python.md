# Python Standards

Applies to all Python code. Builds on top of `coding-standards.md`.

## Language version

- **Python 3.14+** required. Use modern syntax (`match/case`, `|` unions, PEP 695 generics).
- **Prefer `match/case` over `if/elif` chains** whenever branching on the shape,
  type, or value of a single subject — enum/type dispatch, parsing tagged
  unions, handling command variants. Don't force it onto simple boolean
  conditions where `if/else` is clearer.
- Python 3.14 evaluates annotations lazily by default (PEP 649). Explicit
  `from __future__ import annotations` is no longer required for new code, but
  leaving it in existing modules is harmless.

## Package management

- **uv** is preferred over pip when possible. Faster, reproducible, handles lockfiles.
- `uv venv` to create, `uv pip install -e ".[dev]"` to install in editable mode.
- uv is the **installer**, not the runner. Execute project code with
  `.venv/bin/python`, never `uv run` — see the cache caveat in `commands.md`.
- Single source of truth for deps: `pyproject.toml`. Avoid `requirements.txt` unless required by external tooling.

## Type hints

- **Required in new code.** All public functions, methods, and class attributes are annotated.
- Prefer `list[int]` over `List[int]`; `dict[str, Any]` over `Dict[str, Any]` — PEP 585.
- Type hints are enforced by **mypy strict** (see Linting & formatting below), not just documentation — code must pass `mypy --strict` before merge.

## Testing (pytest)

- Arrange–Act–Assert structure; blank line between sections.
- Use fixtures for setup; scope them (`session`, `module`, `function`) to match lifetime.
- Avoid mocking the filesystem, network, or database unless the cost of real I/O is excessive. Prefer integration tests over mock-heavy unit tests.
- Use `pytest.mark.parametrize` for truth-table tests.
- Name tests after behavior, not implementation: `test_user_is_locked_after_three_failed_logins`, not `test_lock_user`.

## Web framework patterns (FastAPI & LiteStar)

Common to both:

- **Dependency injection only.** No global mutable state.
- **Pydantic v2** for request/response schemas. Never return raw DB models.
- **Async correctly**: no blocking calls (`requests.get`, `time.sleep`, sync SQLAlchemy) inside async handlers.
- Project layout: `app/routers/` (or `app/controllers/`), `app/schemas/`, `app/services/`, `app/db/`. One concern per file.
- Error handling: raise the framework's HTTP exception at the route boundary; internal/domain errors use custom exception types, translated to HTTP at the edge, not inside services.

FastAPI specifics:

- DI via `Depends`.
- Errors: `HTTPException` at the route boundary.

LiteStar specifics:

- DI via `Provide`, scoped per-request unless explicitly stated otherwise.
- Prefer LiteStar's built-in DTO layer over hand-rolled serialization when the schema maps 1:1 to a DB model.

## Database (SQLAlchemy + Alembic)

- **SQLAlchemy 2.0+ style** (`sqlalchemy.select(...)`, not legacy `Query`).
- Migrations via **Alembic**: autogenerate, then manually review before committing.
- Never edit an applied migration. Add a new migration to reverse or amend.

## Linting & formatting

- `ruff check .` for linting; `ruff format .` for formatting. No `black`.
- `mypy --strict .` for type checking, run in CI and required to pass before merge.
- Baseline `pyproject.toml` config:

  ```toml
  [tool.mypy]
  python_version = "3.14"
  strict = true
  warn_unused_ignores = true
  disallow_any_generics = true

  [tool.ruff]
  target-version = "py314"

  [tool.ruff.lint]
  select = ["E", "F", "I", "UP", "B"]
  ```

- Imports order: stdlib → third-party → local. Blank line between groups. `ruff` enforces this automatically.

## Imports

- Absolute imports by default. Relative imports only within a package when they improve readability.
- Never `from module import *`.
