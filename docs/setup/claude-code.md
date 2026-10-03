# Claude Code — подключение `ai-settings`

## После первого запуска `scripts/install.sh`

Проверь, что всё на месте:

```
ls -la ~/.claude/
# ожидаем:
# CLAUDE.md -> ~/.ai-settings/CLAUDE.md
# agents   -> ~/.ai-settings/agents
# skills/  (реальный каталог, внутри ссылки на скиллы репы)
# hooks    -> ~/.ai-settings/settings/hooks
# settings.json  (копия, не симлинк)
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
`~/.claude/settings.json` обновляется автоматически: `install.sh` мержит
секции `permissions`, `hooks` и `$schema` из шаблона через jq, сохраняя
твои `enabledPlugins`, `extraKnownMarketplaces` и другие кастомные ключи.
Требует `jq` (устанавливается через `brew install jq`).

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

`install.sh` линкует каждый скилл репы в `~/.claude/skills/<skill>`. Неймспейс `strikez/` в репе только группирует, в Claude Code скилл виден как `/<skill>`:

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
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\agents" -Target "$PWD\agents"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"
# Скиллы по одному: Junction на каждый skills\<namespace>\<skill> в .claude\skills\<skill>
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\hooks" -Target "$PWD\settings\hooks"

# 2. Скопировать настройки
Copy-Item "settings\claude-settings.json" "$env:USERPROFILE\.claude\settings.json"
```

**RTK на Windows:**
Скачать бинарник из [releases](https://github.com/rtk-ai/rtk/releases), добавить в PATH.
