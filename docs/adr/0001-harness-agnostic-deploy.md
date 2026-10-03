# ADR 0001: harness-agnostic раскладка

Статус: принято.

## Контекст

Репа — источник глобального конфига для Claude Code, Codex, OpenCode, Gemini CLI, Cursor и Claude Desktop. Она обросла чужим и сломанным.

- `~/.claude/skills` — симлинк на весь `skills/` репы. Всё, что пишет в `~/.claude/skills`, оседает в репе: `npx skills` (25 matt-скиллов и `find-skills`), agterm, личный `bmw-g20`, синк аккаунтных скиллов Claude Code (`synced/`, `.trash/`). Отсюда 62 красных теста skill-lint, все на `synced/` и `.trash/`.
- Claude Code ищет скиллы только как `~/.claude/skills/<name>/SKILL.md`. Вложенные `strikez/<skill>` и `superpowers/<skill>` он не видит. Видимые сейчас `strikez:*` и `superpowers:*` — шимы из `~/.claude/commands/` с телом «Invoke the `strikez:x` skill», то есть ссылка на самих себя. Собственные скиллы в Claude Code фактически не работали.
- Раскладка несимметрична. Codex и OpenCode берут скиллы из `~/.agents/skills`, Gemini получает только скиллы Superpowers, `feature-architecture` лежит вне неймспейса и уезжает только в Claude. Агентов получают Claude Code и OpenCode, причём OpenCode мёрджем в `opencode.jsonc`, а это файл из дотфайлов с секретом. Codex, Gemini и Cursor умеют сабагентов, но ничего не получают.
- jq-мёрдж `settings.json` в `install.sh` заменяет массивы целиком. Повторный прогон сносит живые allow и чужие хуки (agterm).
- В репе лежат битые симлинки в чужие хоумы.

Я решил строить рабочий процесс на matt-скиллах (`github.com/mattpocock/skills`) и снести форк Superpowers целиком.

## Решение

1. Репа не симлинкается целым каталогом в хоум харнесса. В `~/.claude/{skills,agents,hooks}`, `~/.agents/skills` и аналогичные места кладутся только поштучные ссылки или файлы. Целиком линкуются лишь файлы инструкций (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md` у Gemini): их `@imports` резолвятся от реального пути.
2. Скиллы раскладываются плоско, под одним именем везде: в `~/.claude/skills` для Claude Code и в `~/.agents/skills` для Codex, OpenCode, Gemini и Cursor. `skills/<ns>/<skill>/` в репе — только группировка, имя уникально по всей репе.
3. У агентов один источник: `agents/<name>/AGENT.md` в формате Claude. Под каждый харнесс он рендерится в родной формат. Рендеренные файлы помечены `managed-by: ai-settings`: устаревшие свои установщик удаляет, чужие не удаляет. Чужой файл под именем агента уезжает в `backups/`, под другим именем остаётся на месте.
4. Внешние скиллы ставит `npx skills`, в репу они не попадают.
5. Форк Superpowers снесён в пользу matt-скиллов.
6. Единая точка входа: `install.sh` → `python3 scripts/sync.py all`. Python установщика — только stdlib и совместим с системным `/usr/bin/python3` 3.9, потому что это bootstrap и на чистом маке другого интерпретатора нет. Поэтому без `match/case`. Это осознанное исключение из `docs/ai/python.md`.

### Матрица харнессов

| Харнесс | Правила | Скиллы | Агенты |
|---|---|---|---|
| Claude Code | симлинк `~/.claude/CLAUDE.md` | `~/.claude/skills/<name>` → репа | `~/.claude/agents/<name>.md` → `agents/<name>/AGENT.md` |
| Codex CLI | плоский `~/.codex/AGENTS.md` | `~/.agents/skills/<name>` | `~/.codex/agents/<name>.toml`: `developer_instructions`, без Edit/Write → `sandbox_mode = "read-only"` |
| OpenCode | плоский `~/.config/opencode/AGENTS.md` | `~/.agents/skills` (видит и `~/.claude/skills`) | `~/.config/opencode/agents/<name>.md`: `mode: subagent`, `permission` |
| Gemini CLI | симлинки `~/.gemini/{GEMINI,AGENTS}.md` | `~/.agents/skills` (алиас `~/.gemini/skills`) | `~/.gemini/agents/<name>.md`: `tools` → `read_file`, `read_many_files`, `grep_search`, `glob`, `list_directory`, `run_shell_command`, `replace`, `write_file`, `web_fetch`, `google_web_search` |
| Cursor | `~/.cursor/rules/ai-settings.mdc` | `~/.agents/skills` (видит и `~/.claude/skills`) | `~/.cursor/agents/<name>.md`: `model: inherit`, `readonly`; приоритетнее совместимого `~/.claude/agents` |
| Claude Desktop | — | `deploy-skills.sh` (zip + rsync), без изменений | — |

Модель агентам задаю только в Claude (`opus`/`sonnet`). Остальные харнессы наследуют модель родителя.

## Последствия

- Имена скиллов уникальны по всей репе. Дубль имени в разных неймспейсах — ошибка skill-lint и `sync.py`.
- OpenCode и Cursor читают и `~/.claude/skills`, и `~/.agents/skills`. Есть риск, что скиллы там задвоятся. Проверяю после раскатки, пока это хвост в `TODO.md`.
- Код миграций (`scripts/aisettings/legacy.py`) временный. Я удаляю его, когда обе машины мигрированы.
- Репа больше не получает чужие скиллы через симлинк каталога. Скиллы agterm и `bmw-g20` живут вне репы.
- Установщик не пишет в `opencode.jsonc`, `jq` ему не нужен. Исключение одно — разовая чистка следов старого мёрджа в `legacy.py`. Пользовательские поля агентов OpenCode (`model` и т.п.) она оставляет на месте.
- Python в `scripts/` привязан к 3.9: `match/case` и более новый синтаксис там запрещены, пока системный интерпретатор чистого мака старый.

## Отклонённые варианты

- **Вендорить matt-скиллы в репу.** Копии расходятся с апстримом, обновление превращается в ручной мёрдж, а репа снова владеет чужим. `npx skills update -g` решает это без моего кода.
- **Оставить keep-list Superpowers.** Часть скиллов форка пересекается с matt-скиллами по назначению. Два процесса в одной репе — это два набора триггеров и вечная путаница, какой сработает. Держать форк ради пары скиллов дороже, чем их потерять.
- **Мёрджить агентов в `opencode.jsonc`.** Это файл из дотфайлов с секретом, и установщик в него писать не должен. Markdown-агенты в `~/.config/opencode/agents/` дают тот же результат без правки чужого конфига.
