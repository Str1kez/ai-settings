# Codex CLI — подключение `ai-settings`

## После `scripts/install.sh`

Проверь, что на месте плоский AGENTS.md с развёрнутыми импортами:

```bash
ls -la ~/.codex/AGENTS.md
# -> обычный файл, ~20 КБ (не симлинк)
```

Почему не симлинк: Codex **не резолвит `@imports`** в стиле Claude/Gemini. Если положить туда симлинк на исходный `AGENTS.md` с `@docs/ai/persona.md`, Codex увидит только строку `@docs/ai/persona.md` как текст и не загрузит содержимое. Поэтому `install.sh` запускает `sync.py all`, а тот разворачивает все `@imports` прямо в тело файла.

## Обновление после `git pull`

```bash
cd ~/.ai-settings && git pull
~/.ai-settings/scripts/install.sh
```

`install.sh` перегенерирует плоский `~/.codex/AGENTS.md`. Вручную прогонять ничего не надо.

Если хочется обновить только правила без остального — напрямую:

```bash
~/.ai-settings/scripts/sync.py rules
```

Команда перегенерирует плоские правила сразу для Codex, OpenCode и Cursor и
заодно проверяет ссылки `~/.claude/CLAUDE.md` и `~/.gemini/{GEMINI,AGENTS}.md`.
Если на месте ссылки лежит обычный файл, он уезжает в `backups/<ts>/` в репе.

## `config.toml`

`~/.codex/config.toml` **не трогается** установщиком — там твои настройки модели, плагинов, trusted projects. В репе эталона больше нет — было фиктивное содержимое, удалено в v0.1.1.

## Скиллы

`install.sh` создаёт симлинк на каждый скилл репы в `~/.agents/skills/<skill>/`.
Имя то же, что в Claude Code.
Codex читает их как personal skills после перезапуска приложения.
Симлинки в `~/.agents/skills`, которые смотрят в `skills/` репы и больше не нужны, установщик удаляет. Остальное в этом каталоге он не трогает.

Проверка:

```bash
find -L ~/.agents/skills -maxdepth 2 -name SKILL.md -print
```

Если добавил или переименовал скилл в `skills/` (новый скилл сначала `git add`), запусти:

```bash
~/.ai-settings/scripts/install.sh
```

Потом перезапусти Codex. Без перезапуска список скиллов может остаться старым.

## Субагенты

`install.sh` кладёт по файлу на каждого агента репы в `~/.codex/agents/<name>.toml`: `name`, `description` и `developer_instructions` (промпт агента). Агентам без Edit/Write (`code-reviewer`, `pr-writer`) добавляется `sandbox_mode = "read-only"`. Модель не задаётся, агент берёт модель родителя.

Первая строка файла — `# managed-by: ai-settings`. По ней установщик отличает свои файлы: устаревшие удаляет, а чужой файл под именем нашего агента уносит в `backups/<ts>/` репы. Файлы без метки под другими именами не трогает.

```bash
ls ~/.codex/agents
```

## Что глобально применено к Codex

После `install.sh` Codex получает:

- плоский `~/.codex/AGENTS.md` со всеми правилами общения, персоной Афины, hard gates, git workflow и platform-wide notes;
- personal skills из `~/.agents/skills/`;
- текущий `~/.codex/config.toml` остаётся пользовательским: модель, плагины и trusted projects не перезаписываются.

## Проверка

Запусти Codex в произвольной папке, задай:

> «напиши коммит»

Если модель предлагает Conventional Commits с русским описанием (`feat(scope): ...`) и не ломает персону Афины — правила подхвачены. Если выдаёт generic английский — значит плоский файл не прогрузился; проверь `head ~/.codex/AGENTS.md` и перегенерируй через `sync.py rules`.

## Windows

`install.sh` требует bash (macOS/Linux или WSL).

**WSL (рекомендуется):** запустить `./scripts/install.sh` из WSL-терминала.

**Без WSL (вручную):**
```powershell
# В PowerShell:
Copy-Item "AGENTS.md" "$env:USERPROFILE\.codex\AGENTS.md"
```

> Путь на Windows: `%USERPROFILE%\.codex\AGENTS.md`
