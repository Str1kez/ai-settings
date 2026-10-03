# OpenCode — подключение `ai-settings`

## После `scripts/install.sh`

Проверь, что на месте плоский файл с глобальными правилами:

```bash
ls -la ~/.config/opencode/AGENTS.md
# -> обычный файл, не симлинк
```

OpenCode не разворачивает `@imports` из `AGENTS.md` автоматически. Поэтому
`install.sh` вызывает `sync-cursor.sh --opencode`, который подставляет содержимое
всех модулей из `docs/ai/` в глобальный файл OpenCode.

## Скиллы

OpenCode автоматически находит personal skills в `~/.agents/skills/`. Эти
симлинки создаёт тот же `install.sh`; отдельная копия в
`~/.config/opencode/skills/` не нужна.

Проверка:

```bash
find -L ~/.agents/skills -maxdepth 2 -name SKILL.md -print
```

## Агенты

`install.sh` конвертирует `agents/*/AGENT.md` (Claude Code формат) и мерджит
их в блок `agent` файла `~/.config/opencode/opencode.jsonc`. Промпты лежат
отдельно в `~/.config/opencode/agent-prompts/<name>.md` и подключаются через
`{file:./agent-prompts/<name>.md}`.

`install.sh` управляет полями `description`, `mode`, `permission`, `prompt`.
Поле `model` **не задаётся** установщиком — это пользовательское поле. Без него
primary-агент берёт глобально настроенный `model`, а subagent наследует модель
родителя.

Существующие пользовательские поля агентов (`model`, `temperature` и т.д.)
при повторном `install.sh` сохраняются: merge обновляет только managed-поля.

Проверка:

```bash
opencode debug config
```

### Указать модель агента глобально

Добавь в `~/.config/opencode/opencode.jsonc`:

```json
{
  "agent": {
    "code-reviewer": { "model": "anthropic/claude-opus-4-1" },
    "pr-writer":     { "model": "anthropic/claude-haiku-4-5" }
  }
}
```

### Переопределить модель агента в конкретном проекте

Конфиги OpenCode мерджатся field-level. Положи в корень проекта `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "code-reviewer": { "model": "anthropic/claude-opus-4-1" }
  }
}
```

Переопределяется только `model` для указанного агента. Остальные поля
(`description`, `prompt`, `permission`) берутся из глобального определения.

Список доступных моделей: `opencode models`.

### Зависимости

Конвертация агентов требует `jq` для merge в `opencode.jsonc`. Если `jq` нет
— выводится предупреждение, агент-блок не записывается. Установка: `brew install jq`.

## RTK (Rust Token Killer)

`install.sh` ставит плагин автоматически (если бинарник `rtk` уже есть в PATH):

```bash
rtk init -g --opencode --hook-only --no-patch
```

Флаги `--hook-only --no-patch` гарантируют, что команда трогает только
OpenCode: без `CLAUDE.md`/`RTK.md` и без патча `~/.claude/settings.json` —
Claude Code уже настроен отдельно через `settings/claude-settings.json`
(`rtk hook claude`).

Команда кладёт плагин `~/.config/opencode/plugins/rtk.ts` — он делегирует всю
логику переписывания команд бинарнику `rtk` (`rtk rewrite <cmd>`), сам плагин
не содержит никакой rewrite-логики. Проверка: `rtk init --show`.

Если бинарника `rtk` не было на момент установки — поставь его
(`brew install rtk`) и перезапусти `install.sh`, или прогони команду выше
вручную.

## Пользовательская конфигурация

`~/.config/opencode/opencode.jsonc` остаётся пользовательским: провайдеры,
модели, MCP-серверы и плагины (кроме RTK, см. выше) установщик не трогает.
Единственное исключение в самом `opencode.jsonc` — блок `agent`: `install.sh`
мерджит туда managed-поля (`description`, `mode`, `permission`, `prompt`) из
`agents/*/AGENT.md`. Поля `model`, `temperature` и другие пользовательские
настройки агентов сохраняются при повторных запусках.

## Обновление

```bash
cd ~/.ai-settings && git pull
./scripts/install.sh
```

После обновления полностью перезапусти OpenCode: конфигурационные файлы и
список скиллов читаются при старте.

Если нужно обновить только глобальные правила OpenCode:

```bash
~/.ai-settings/scripts/sync-cursor.sh --opencode
```

## Проектные правила и runtime-конфиг

Правила проекта покрывает `AGENTS.md`: OpenCode автоматически читает ближайший
такой файл от текущей директории до корня worktree, и `scripts/init-project.sh`
уже создаёт его — отдельного механизма для правил не нужно.

Runtime-конфиг (модель, `agent`, `mcp`, `permission`, плагины) — это другое:
`scripts/init-project.sh` создаёт в корне проекта пустой `opencode.jsonc` с
`$schema` и комментарием-подсказкой. Он мерджится field-level над глобальным
`~/.config/opencode/opencode.jsonc`, так что можно переопределить, например,
модель конкретного агента только для этого проекта (см. пример выше).

## Windows

`install.sh` требует bash: используй WSL или выполни ручную генерацию из WSL в
Windows-профиль. Глобальный путь OpenCode определяется через XDG config и по
умолчанию имеет вид `~/.config/opencode/AGENTS.md`.
