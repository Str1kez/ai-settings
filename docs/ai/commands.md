# Commands

READ THIS FIRST. These are the canonical commands for common tasks. Prefer these over ad-hoc invocations — they include the flags that matter.

**Project-specific overrides:** before touching an unfamiliar project, check for a `.ai/` directory in its root. If present, it documents project-specific test/lint/build commands and custom tooling that take precedence over the defaults below.

## Python (pytest + uv)

- Run all tests: `pytest -v`
- Run one file: `pytest -v path/to/test_file.py`
- Run one test: `pytest -v path/to/test_file.py::test_name`
- Run with coverage: `pytest -v --cov=src --cov-report=term-missing`
- Stop on first failure: `pytest -v -x`
- Sync existing deps from lockfile: `uv sync --frozen`
- Add a new runtime dependency: `uv add <pkg>`
- Add a new dependency to a custom group (e.g. `local`, `lint`, `dev`): `uv add --group <name> <pkg>`
- Add a new optional/extra dependency: `uv add <pkg> --optional <extra>`
- Create venv: `uv venv && source .venv/bin/activate`
- Run a script in venv: `.venv/bin/python script.py`
- Run a CLI in venv: `.venv/bin/<cli-command>`
- Lint: `ruff check .`
- Format: `ruff format .` (or `black .`)

**Do not run project code through `uv run`.** uv initializes its cache on every
invocation — including `--frozen` — and dies with `Permission denied` wherever
`~/.cache/uv` is read-only: agent sandboxes and cron. The failure surfaces as a
made-up problem with the task ("calendar unavailable", "monitoring failed")
instead of a tooling error. Call the venv interpreter directly; it never touches
the cache. uv stays the installer, run once outside the sandbox.

If `.venv/bin/python` is missing, create the environment (`uv sync --frozen` or
`uv venv`) — do not fall back to `uv run`, and do not ask to disable the sandbox.

## Rust (cargo)

- Run all tests: `cargo test`
- Run one test: `cargo test <test_name>`
- Run with output: `cargo test -- --nocapture`
- Lint: `cargo clippy --all-targets --all-features -- -D warnings`
- Format: `cargo fmt`
- Build (debug): `cargo build`
- Build (release): `cargo build --release`

## Go (go test)

- Run all tests: `go test ./...`
- Run one test: `go test ./path/to/pkg -run TestName`
- Verbose: `go test -v ./...`
- With coverage: `go test -cover ./...`
- Lint: `golangci-lint run` (falls back to `go vet ./...` if not installed)
- Format: `gofmt -l -w .` (or `goimports -l -w .` if imports need sorting)
- Build: `go build ./...`

## Git

- Status: `git status`
- Log (recent): `git log --oneline -20`
- Log with graph: `git log --oneline --graph --decorate -20`
- Diff unstaged: `git diff`
- Diff staged: `git diff --staged`
- Diff against base: `git diff main...HEAD`
- Update current branch from main: `git merge main` (merge, not rebase — see git-workflow.md)
- Stash: `git stash push -m "<msg>"`
- Push current branch: `git push -u origin $(git branch --show-current)`
