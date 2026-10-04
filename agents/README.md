# Agents

Субагенты в формате Claude Code: `agents/<name>/AGENT.md`. `scripts/install.sh` линкует каждый в `~/.claude/agents/<name>.md`, для OpenCode, Codex, Gemini CLI и Cursor рендерит файл в их формат. Раскладка по харнессам — в [ARCHITECTURE.md](../ARCHITECTURE.md#агенты).

Деплоятся только агенты, которые отслеживает git, как и скиллы: новый агент надо сначала `git add`. Если в `agents/` лежит каталог с `AGENT.md`, который git не отслеживает и не игнорирует, `sync.py` предупредит и назовёт команду `git add`.

## Новый агент

```bash
scripts/new.py agent <name>
```

Скрипт создаёт `agents/<name>/AGENT.md` из заготовки, проверяет имя по regex `^[a-z0-9]+(-[a-z0-9]+)*$`, существующий каталог не перезаписывает и печатает следующие шаги:

1. заполнить `AGENT.md`: `description` с триггером и `SKIP`, `tools`, `model`, тело — промпт;
2. `git add agents/<name>`;
3. `.venv/bin/python -m pytest tests/agent_lint -v`;
4. `scripts/install.sh --dry-run`, затем `scripts/install.sh`.

## Правила

- Имя каталога равно `name` во frontmatter. Claude Code показывает `name`, а ссылки и рендеры называются по каталогу. При расхождении `sync.py` падает и называет файл.
- `description` содержит `Use ...` (или `TRIGGER`) и `SKIP`: по нему модель решает, звать агента или нет.
- `tools` — список из инструментов, которые знают рендеры (`KNOWN_TOOLS` в `scripts/aisettings/agents.py`). Остальные рендеры молча выбрасывают.
- Frontmatter пишу в подмножестве YAML, которое читает парсер `sync.py`: `key: value`, `key: |` и `key: [a, b]`. Для `description: >-` он не годится.
- Агенты без Edit и Write считаются read-only: в OpenCode `edit: deny`, в Codex `sandbox_mode = "read-only"`, в Cursor `readonly: true`.

Все правила проверяет agent-lint: `.venv/bin/python -m pytest tests/agent_lint -v`, список проверок — в `tests/agent_lint/README.md`.
