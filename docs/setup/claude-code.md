# Claude Code — подключение `ai-settings`

## После первого запуска `scripts/install.sh`

Проверь, что всё на месте:

```
ls -la ~/.claude/
# ожидаем:
# CLAUDE.md -> ~/.ai-settings/CLAUDE.md
# agents/  (реальный каталог, внутри ссылки <name>.md на агентов репы)
# skills/  (реальный каталог, внутри ссылки на скиллы репы)
# hooks/   (реальный каталог, внутри ссылки на скрипты из settings/hooks)
# settings.json  (твой файл, установщик мёрджит в него шаблон)
```

## Проверка загрузки

Запусти `claude` в любой папке. В начале сессии должен появиться hook-баннер:

```
[ai-settings] Loaded: N skill(s), M subagent(s).
```

Если не появился — либо выставлен `AI_SETTINGS_QUIET=1`, либо хуку не проставлен исполняемый бит.

## Обновление правил

```bash
cd ~/.ai-settings && git pull && ./scripts/install.sh
```

Симлинки не трогаются — новое содержимое подхватывается автоматически.

## settings.json

`~/.claude/settings.json` — твой файл: в него пишут сам Claude Code, плагины и agterm. `install.sh` мёрджит в него шаблон `settings/claude-settings.json` через `sync.py claude`, `jq` для этого не нужен. Правила мёржа:

- `$schema` и списки `permissions.allow`, `permissions.ask` и `permissions.deny` берутся из шаблона целиком. Своё правило в эти списки я добавляю в шаблон, иначе следующий прогон его сотрёт.
- Остальные ключи остаются как были: `model`, `env`, `enabledPlugins`, `permissions.defaultMode` и всё прочее.
- Хуки мёрджатся по событиям. Запись установщика — это хук из шаблона или хук, который запускает скрипт установщика из `~/.claude/hooks/`: тот, что запускает шаблон или линковал прошлый прогон. Такие записи заменяются шаблонными, и каждая остаётся ровно одна. Чужие записи, например хуки agterm, стоят где стояли. Запись на твой скрипт из `~/.claude/hooks/` тоже остаётся, даже если самого скрипта на этой машине ещё нет.
- Повторный прогон ничего не меняет. Если `settings.json` не читается как JSON или его `permissions` и `hooks` не той формы, установщик ничего не трогает и падает с ошибкой.

Какие строки `settings.json` меняются, установщик пишет в лог. Контекст вокруг них он не показывает, чтобы не светить твои значения, например токены из `env`. План видно до прогона:

```bash
~/.ai-settings/scripts/install.sh --dry-run
```

`~/.claude/hooks` — реальный каталог. На каждый скрипт, который запускает шаблон, в нём ссылка `<script>` → `settings/hooks/<script>`. Свои скрипты можно класть туда же: установщик их не трогает и их записи в `settings.json` оставляет. Ссылка на скрипт, который шаблон больше не запускает, уходит вместе со своей записью. Шаблон запускает скрипт только в виде `~/.claude/hooks/<script>` в начале команды: другую форму установщик отвергает. Старую раскладку, где `~/.claude/hooks` — симлинк на `settings/hooks/`, установщик переводит сам: всё, что git там не отслеживает, переезжает в новый каталог.

### Форматирование Python

Хука форматирования нет: линт, формат и тесты решает сам проект через pre-commit и свои конвенции. Глобальный хук переписывал бы файлы в чужих репах, где ruff не используют. Старый инлайн-хук с `uv run ruff` установщик при мёрдже удаляет сам, потому что `uv run` трогает кэш uv на каждом вызове и падает там, где он read-only. На любой другой хук с `uv run` он пишет предупреждение и оставляет его как есть.

### Поиск и permissions

`rtk hook claude` переписывает `find`, `grep`, `rg`, `cat`, `git …`, `pytest` и другие команды в `rtk …` и решает по правилам исходной команды. Если она в allow и не попадает под ask, хук одобряет переписанную сам. Под ask он её переписывает, но не одобряет, а команду под deny не трогает. Поэтому в allow лежат сами тулы (`find`, `grep`, `rg`, `git log` …), а rtk-форм там нет, кроме мета-команд `rtk gain` и `rtk discover`: их Claude зовёт напрямую. Прямой вызов вроде `rtk find …` спросит подтверждение. `fd` и `.venv/bin/*` rtk не переписывает, их решает сам Claude Code.

Флаги, которые запускают команды, перехватывают ask-правила. По ним rtk не одобряет, а Claude Code спрашивает даже поверх allow и поверх одобрения хука. Порядок deny → ask → allow, `*` в любом месте правила и то, что решение PreToolUse-хука не обходит ask и deny, описаны в [документации Claude Code](https://code.claude.com/docs/en/permissions).

| Правило в `ask` | Что ловит |
|---|---|
| `Bash(*-exec*)` | `find -exec`, `find -execdir`, `fd --exec` |
| `Bash(*-delete*)` | `find -delete` |
| `Bash(*rg *--pre*)` | `rg --pre`, который запускает программу на каждый файл |
| `Bash(fd *-x*)`, `Bash(fd *-X*)` | `fd -x`, `fd -X` |

Это паттерны по тексту команды. Обычные формы они ловят, нарочно запутанные вроде `fd -Hx` — нет. Иногда спросят лишнее, например на `rg --pretty`.

## Проектные переопределения

В корне проекта:

```bash
~/.ai-settings/scripts/init-project.sh
```

Это создаст:
- локальный `AGENTS.md` (additive — поверх глобальных правил),
- `.claude/settings.json` с пустыми `allow/ask/deny` для project-специфичных permissions,
- обновит `.gitignore` AI-артефактами (`.claude/sessions/`, `.claude/cache/`).

## Нюансы

- Глобальный слой применяется автоматически ко всем проектам через `~/.claude/CLAUDE.md` — не надо импортировать его из проектного `AGENTS.md`.
- Если нужно временно «заглушить» хук в конкретной сессии: `AI_SETTINGS_QUIET=1 claude`.

## Скиллы

`install.sh` линкует каждый скилл репы `skills/<skill>/` в `~/.claude/skills/<skill>`, в Claude Code он виден как `/<skill>`:

```
/en-commit-message
/ru-pr-description
...
```

Шимы в `~/.claude/commands` больше не нужны и не создаются. `~/.claude/skills` — реальный каталог: сюда же пишут `npx skills` и синк аккаунтных скиллов, и ничего из этого не попадает в репу.

Старую раскладку, где `~/.claude/skills` — симлинк на `skills/` репы, `install.sh` переводит сам. Симлинк становится реальным каталогом, туда переезжает всё, что git в `skills/` не отслеживает: ссылки `npx skills`, agterm, `bmw-g20`, `synced/` и `.trash/`. Отслеживаемое остаётся в репе. Заодно уходят сгенерированные шимы из `~/.claude/commands/<ns>/` (посторонние файлы там остаются) и ссылка `~/.gemini/skills` в репу. На такой машине я сначала смотрю план:

```bash
~/.ai-settings/scripts/install.sh --dry-run
```

Проверка:

```bash
ls -la ~/.claude/skills/en-commit-message
```

## RTK (Rust Token Killer)

RTK — CLI-прокси, сжимает вывод bash-команд перед попаданием в контекст. Экономит 60-90% токенов на `git`, `npm test`, `pytest`, `grep` и других командах.

**Что настроено автоматически:**
- PreToolUse hook (`rtk hook claude` — нативная команда бинарника, без обёрточного скрипта) — прозрачно переписывает команды через rtk
- `install.sh` устанавливает бинарник автоматически (через Homebrew или curl)

**Проверить установку:**
```bash
rtk --version
rtk hook claude --help   # если команды нет — обновись: brew upgrade rtk
rtk gain                 # статистика экономии токенов за сессию
```

**Установить вручную (если install.sh не запускали):**
```bash
# macOS с Homebrew:
brew install rtk

# macOS без Homebrew / Linux:
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# Windows: скачать бинарник из releases и добавить в PATH
# https://github.com/rtk-ai/rtk/releases
```

> Примечание: существуют два разных проекта с именем `rtk` на crates.io. Правильный — [rtk-ai/rtk](https://github.com/rtk-ai/rtk). Проверить: `rtk gain` должно работать.

## Windows

**Рекомендуемый путь: WSL (Windows Subsystem for Linux)**

1. Установить WSL: `wsl --install` в PowerShell (с правами администратора)
2. Открыть WSL-терминал
3. Запустить `./scripts/install.sh` как обычно — всё работает без изменений

**Без WSL (ручная настройка):**

```powershell
# В PowerShell (с правами администратора):
# 1. Создать символические ссылки
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\CLAUDE.md" -Target "$PWD\CLAUDE.md"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\agents"
# Агенты по одному: SymbolicLink на каждый agents\<name>\AGENT.md в .claude\agents\<name>.md
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"
# Скиллы по одному: Junction на каждый skills\<skill> в .claude\skills\<skill>
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\hooks"
# Хуки по одному: SymbolicLink на каждый скрипт, который запускает шаблон, в .claude\hooks\<script>

# 2. Скопировать настройки, если settings.json ещё нет.
#    В существующий файл permissions и хуки из шаблона переносятся руками.
if (-not (Test-Path "$env:USERPROFILE\.claude\settings.json")) {
    Copy-Item "settings\claude-settings.json" "$env:USERPROFILE\.claude\settings.json"
}
```

**RTK на Windows:**
Скачать бинарник из [releases](https://github.com/rtk-ai/rtk/releases), добавить в PATH.
