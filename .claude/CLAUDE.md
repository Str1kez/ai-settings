## This repo

- Root `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` and `docs/ai/` are the user's global instructions: install symlinks or renders them into every harness home, so they load in every project. Guidance about working on this repo goes in this file.
- Python in `scripts/` runs under the system `python3` (3.9 on macOS): stdlib only, 3.9-compatible syntax. For `scripts/` this overrides the 3.14+ rule in `docs/ai/python.md`.
- `scripts/install.sh` writes into the real harness homes (`~/.claude`, `~/.agents`, `~/.codex`, ...). Run it with `--dry-run`, show the output, and do the real run only after the user approves.

## Agent skills

### Issue tracker

Issues и specs живут локально в `.scratch/<feature>/` (markdown). See `docs/agents/issue-tracker.md`.

### Triage labels

Дефолтный словарь: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: один `CONTEXT.md` и `docs/adr/` в корне. See `docs/agents/domain.md`.
