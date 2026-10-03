# OpenCode — подключение `ai-settings`

## После `scripts/install.sh`

Проверь, что на месте плоский файл с глобальными правилами:

```bash
ls -la ~/.config/opencode/AGENTS.md
# -> обычный файл, не симлинк
```

OpenCode не разворачивает `@imports` из `AGENTS.md` автоматически. Поэтому
`install.sh` запускает `sync.py all`, который подставляет содержимое всех
модулей из `docs/ai/` в глобальный файл OpenCode.

## Скиллы

OpenCode автоматически находит personal skills в `~/.agents/skills/`. Эти
симлинки создаёт тот же `install.sh`, по одному на скилл репы под плоским именем.
Отдельная копия в `~/.config/opencode/skills/` не нужна. OpenCode режет
`description` на 1024 символах, это проверяет skill-lint.

Проверка:

```bash
find -L ~/.agents/skills -maxdepth 2 -name SKILL.md -print
```

## Агенты

`install.sh` рендерит каждый `agents/<name>/AGENT.md` (формат Claude Code) в
markdown-агента `~/.config/opencode/agents/<name>.md`:

- `description` берётся из `AGENT.md`;
- `mode: subagent`;
- `permission`: инструменты из `tools` разрешены, без `Edit` и `Write` стоит
  `edit: deny`, без `Bash` — `bash: deny`, остальные ключи по умолчанию
  OpenCode;
- тело `AGENT.md` становится промптом.

Модель установщик не задаёт: сабагент без `model` работает на модели агента,
который его вызвал.

Первая строка frontmatter — комментарий `# managed-by: ai-settings`. Файл с
этим маркером принадлежит установщику: повторный `install.sh` его
перезаписывает, а рендер агента, удалённого из репы, удаляет. Правки в таком
файле следующий прогон затрёт. Файл без маркера установщик не трогает, а если
его имя совпало с агентом репы, уносит его в `backups/<ts>/`.

Проверка:

```bash
ls ~/.config/opencode/agents
opencode debug config
```

### Модель агента

OpenCode сначала читает `opencode.jsonc`, глобальный и проектный, затем
накладывает поверх markdown-агентов. Так устроено в исходниках OpenCode,
документация порядок не описывает. Поэтому то, что задаёт рендер, из
`opencode.jsonc` не переопределить ни глобально, ни в проекте: `description`,
`mode`, промпт и ключи `permission` из рендера. Остальное работает: `model` или
ключ `permission`, которого в рендере нет.

Глобально — в `~/.config/opencode/opencode.jsonc`:

```json
{
  "agent": {
    "code-reviewer": { "model": "anthropic/claude-opus-4-1" },
    "pr-writer":     { "model": "anthropic/claude-haiku-4-5" }
  }
}
```

В конкретном проекте — в `opencode.json` или `opencode.jsonc` в его корне:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "code-reviewer": { "model": "anthropic/claude-opus-4-1" }
  }
}
```

Список доступных моделей: `opencode models`.

### Переход со старой схемы

Раньше `install.sh` мёрджил агентов в блок `agent` файла `opencode.jsonc`, а
промпты клал в `~/.config/opencode/agent-prompts/`. Первый прогон новой версии
убирает только то, что записал старый мёрдж. Запись агента он узнаёт по
`"prompt": "{file:./agent-prompts/<name>.md}"`, в том числе у агента, которого
в репе уже нет, и удаляет у неё `description`, `mode` и `prompt`. Из
`permission` уходят только ключи, которые рендер задаёт с тем же значением:
старый мёрдж был глубоким, и твои ключи в нём выживали. У агента, которого в
репе нет, `permission` уходит целиком. Опустевшая запись удаляется, `model` и
другие свои поля остаются. Промпт из `agent-prompts/` удаляется, когда
`opencode.jsonc` на него больше не ссылается.

Если в `opencode.jsonc` есть комментарии, установщик файл не трогает и пишет
предупреждение: при перезаписи комментарии пропали бы. Тогда убери эти поля
руками и запусти `install.sh` ещё раз, он дочистит `agent-prompts/`.

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
модели, MCP-серверы и плагины (кроме RTK, см. выше) установщик не трогает и в
сам файл не пишет. Единственное исключение — разовая чистка блока `agent` от
старого мёрджа, она описана в разделе про переход со старой схемы.

## Обновление

```bash
cd ~/.ai-settings && git pull
./scripts/install.sh
```

После обновления полностью перезапусти OpenCode: конфигурационные файлы и
список скиллов читаются при старте.

Если нужно обновить только правила (заодно у Codex и Cursor, плюс ссылки
Claude Code и Gemini):

```bash
~/.ai-settings/scripts/sync.py rules
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
