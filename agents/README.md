# Agents

Агент — субагент: отдельный контекст, свой промпт и свой набор инструментов. Главный агент отдаёт ему задачу целиком и получает назад только результат. Агент нужен, когда задачу лучше увести из основного контекста (широкий поиск, ревью большого диффа) или урезать инструменты, как у `code-reviewer`, который только читает. Если модели нужна повторяемая процедура прямо в текущем диалоге, нужен не агент, а [скилл](../skills/README.md).

Формат — Claude Code: `agents/<name>/AGENT.md`. `scripts/install.sh` линкует каждый в `~/.claude/agents/<name>.md`, для OpenCode, Codex, Gemini CLI и Cursor рендерит файл в их формат. Раскладка по харнессам — в [ARCHITECTURE.md](../ARCHITECTURE.md#агенты).

Деплоятся только агенты, которые отслеживает git, как и скиллы: так на каждой машине стоит один и тот же набор. Каталог с `AGENT.md`, который git не отслеживает и не игнорирует, `install.sh` не ставит, предупреждает и называет команду `git add`.

## Новый агент

Команды запускаю из корня репы. Линту нужен `.venv`: если его нет, сначала `uv sync --frozen`.

1. Заготовка:

   ```bash
   scripts/new.py agent <name>
   ```

   Скрипт создаёт `agents/<name>/AGENT.md`, имя проверяет по regex `^[a-z0-9]+(-[a-z0-9]+)*$`, существующий каталог не перезаписывает.
2. Заполняю `AGENT.md`, поля описаны [ниже](#формат-agentmd). Начинаю с `description`: по нему модель решает, звать ли агента.
3. `git add agents/<name>`: без этого агент не задеплоится.
4. Линт: `.venv/bin/python -m pytest tests/agent_lint -v`. Пока в `description` остаются `<заготовки>`, он красный, так и задумано.
5. `./scripts/install.sh --dry-run`, затем `./scripts/install.sh`, и перезапуск харнесса.

Агента удаляю через `git rm -r agents/<name>` и прогоняю `install.sh`: он уберёт ссылку и рендеры во всех харнессах.

## Формат `AGENT.md`

Пример — [code-reviewer](code-reviewer/AGENT.md):

```markdown
---
name: code-reviewer
description: |
  Use after completing a major implementation step, or when the user asks
  "review this / check the code / look at the diff", or before any commit.
  SKIP: trivial doc-only changes, cosmetic refactors, pure design discussions.
model: opus
tools: [Read, Grep, Glob, Bash]
---

# Role

You are a senior engineer conducting a rigorous code review.
```

- `name` равен имени каталога. Claude Code показывает `name`, а ссылки и рендеры называются по каталогу. При расхождении `sync.py` падает и называет файл, иначе один агент жил бы под двумя именами.
- `description` говорит, когда звать агента: `Use ...` (или `TRIGGER`) и `SKIP` (или `Do NOT use`), от 100 символов.
- `model` — модель агента в Claude Code, например `sonnet` или `opus`. В остальных харнессах агент работает на модели того, кто его вызвал.
- `tools` — инструменты в именах Claude Code: `Read`, `Grep`, `Glob`, `List`, `Bash`, `Edit`, `Write`, `Task`, `WebFetch`, `WebSearch`. Источник списка — `KNOWN_TOOLS` в `scripts/aisettings/agents.py`. Рендеры переводят эти имена в права других харнессов, а незнакомое молча выбросили бы, и агент остался бы без инструмента. Поэтому линт незнакомые имена не пускает.
- Агент без `Edit` и `Write` становится read-only: в OpenCode `edit: deny`, в Codex `sandbox_mode = "read-only"`, в Cursor `readonly: true`.
- Тело после frontmatter — системный промпт агента. `'''` в нём нельзя: Codex кладёт промпт в литеральную строку TOML.

Frontmatter пишу в подмножестве YAML, которое читает парсер `sync.py`: `key: value`, `key: |` и `key: [a, b]`. `description: >-` он прочтёт неверно, линт это ловит.

## Agent-lint

```bash
.venv/bin/python -m pytest tests/agent_lint -v
```

Без линта ошибку в агенте я видел только на `install.sh` или когда агент не вызывался. Линт проверяет до коммита всё, что описано в разделе про формат, и входит в общий `.venv/bin/python -m pytest -q`. Хука нет, гоняю руками. Список проверок — в [tests/agent_lint/README.md](../tests/agent_lint/README.md).
