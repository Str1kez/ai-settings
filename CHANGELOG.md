# CHANGELOG

Все значимые изменения в этом репозитории фиксируются здесь.
Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версионирование по [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Добавлено
- Скилл `feature-architecture` — сводит разведку кодовой базы и продуктовое
  открытие в одну рекомендованную архитектуру фичи: диаграмма, точки
  интеграции, поток данных, честная оценка и явные допущения.
- Скилл `product-spec-pipeline` — превращает идеи и продуктовые задачи любого масштаба в адаптивную спецификацию через интерактивный grilling, межмодельную проверку и 2 независимых ревью в Orca.
- Оригинальный скилл `brainstorming` из Superpowers v6.1.1 — проводит идею через уточняющий диалог, сравнение подходов и согласование дизайна.
- Короткий alias `$spec` — запускает полный pipeline продуктовой спецификации из любого проекта.
- `install.sh` и `sync-cursor.sh --opencode` устанавливают плоский глобальный
  `~/.config/opencode/AGENTS.md`; OpenCode использует общие personal skills из
  `~/.agents/skills`, а пользовательский `opencode.json` остаётся нетронутым.
- Добавлен гайд `docs/setup/opencode.md` по установке, обновлению и проверке
  интеграции OpenCode.
- `sync-cursor.sh --opencode-agents` конвертирует `agents/*/AGENT.md` и мерджит
  managed-поля (`description`, `mode`, `permission`, `prompt`) в блок `agent`
  файла `~/.config/opencode/opencode.jsonc`. Промпты лежат отдельно в
  `~/.config/opencode/agent-prompts/`. Поле `model` не задаётся установщиком —
  оно пользовательское; project-level override через `agent.<name>.model` в
  `opencode.json` работает как field-level merge. Существующие пользовательские
  поля агентов при повторном `install.sh` сохраняются.
- `scripts/init-project.sh` создаёт в корне проекта пустой `opencode.jsonc`
  с `$schema` и подсказкой в комментарии — для project-level override модели,
  `agent`, `mcp` и других runtime-настроек OpenCode.

### Изменено
- `product-spec-pipeline` анализирует существующий проект до работы с идеей и предлагает выбрать глубокие исследования, запускаемые отдельными агентами.
- `product-spec-pipeline` начинает работу с оригинального `brainstorming`: пользователь выбирает направление из 2–3 вариантов, после чего `grilling` уточняет выбранный вариант.
- `docs/ai/python.md` адаптирован под команду: минимальная версия поднята до
  3.14+ с акцентом на `match/case` и упоминанием PEP 649 (ленивые аннотации);
  раздел `FastAPI patterns` расширен до `Web framework patterns` (FastAPI и
  LiteStar); линтинг зафиксирован как `ruff` (lint+format, без `black`) +
  обязательный `mypy --strict` с baseline-конфигом в `pyproject.toml`.
- RTK PreToolUse hook в `settings/claude-settings.json` переведён с
  обёрточного скрипта на нативную команду бинарника `rtk hook claude` —
  сам скрипт дублировал логику, которая уже целиком живёт в бинаре rtk.
- `install.sh` теперь ставит RTK-плагин для OpenCode автоматически
  (`rtk init -g --opencode --hook-only --no-patch`, идемпотентно, не трогает
  Claude Code) — раньше требовался ручной шаг.

### Исправлено
- `install.sh` теперь создаёт `~/.gemini/AGENTS.md` для относительного импорта
  из `GEMINI.md` и подключает risk-based Superpowers через
  `~/.gemini/skills`.
- skill-lint проверяет только `SKILL.md`, которые отслеживает git. Раньше он
  падал на чужих скиллах в `skills/synced/` и `skills/.trash/`.

### Удалено
- `tg-post-writer`, `ru-commit-message`
- Битые симлинки `presentation-builder`, `report-builder`, `sales-kit-writer`
  и `strikez/write-meridian-article` — смотрели в чужие домашние каталоги.
- `settings/hooks/rtk-rewrite.sh` — заменён на нативную команду `rtk hook claude`
  прямо в `settings/claude-settings.json`.

## [0.2.5] — 2026-07-31

### Изменено
- Тесты и проверки теперь масштабируются по риску изменения: обычные правки не
  требуют теста на каждую функцию, а критические контракты и регрессии
  сохраняют минимальный test-first сценарий.
- Субагентское ревью ограничено одной независимой проверкой для рискованных или
  межкомпонентных изменений; per-task review, повторные полные прогоны и
  открытые циклы re-review больше не являются глобальным дефолтом.
- Скиллы сначала сопоставляются со своими trigger-условиями, а не запускаются
  автоматически из-за формальной вероятности применимости.
- Risk-based fork Superpowers 6.2.0 перенесён в `skills/superpowers/`: короткие
  workflow заменяют обязательные церемонии, а `install.sh` не создаёт вторую
  копию skills в Codex, если plugin уже установлен.
- Общие правила из `CLAUDE.md` перенесены в `AGENTS.md`, чтобы Codex получал подсказки по модели, напоминание о новом чате и запрет на неявные внешние интеграции через глобальный плоский файл.
- Правила личности Афины уточняют, что мат допустим в чате с пользователем как рабочий инструмент, но не переносится в UI, клиентские документы и generated content.

## [0.2.4] — 2026-04-21

### Добавлено
- `CLAUDE.md` — инструкция модели не вызывать MCP-инструменты (Notion, Confluence, Claude_in_Chrome, scheduled-tasks) без явной просьбы пользователя.
- `CLAUDE.md` — правило давать подсказку по модели (Haiku / Sonnet / Opus) и уровню effort в конце ответов, где предлагается следующий шаг или запускается задача.
- `CLAUDE.md` — напоминание писать «Задача закрыта. Если следующая несвязанная — открой новый чат» при завершении задачи.
- `skills/strikez/boilerplate/SKILL.md` — Step 5 теперь генерирует `.claude/CLAUDE.md` в новом проекте с MCP-guard и маппингом моделей.

## [0.2.2] — 2026-04-20

### Добавлено
- Секция `## Codex Skills` в `AGENTS.md` — объясняет модели, что скиллы из `.claude/skills/` не видны Codex нативно; как использовать их вручную и как устанавливать в `~/.agents/skills/`; предупреждение про namespace (`strikez:write-meridian-article` → `write-meridian-article`).
- `scripts/install.sh` — новая секция: создаёт `~/.agents/skills/` и симлинкует каждый скилл из репо без namespace-префикса. Идемпотентно, работает с `--dry-run`.

## [0.2.1] — 2026-04-19

### Добавлено
- Раздел Compression в `docs/ai/style.md` — тёрсный стиль для ответов AI, не затрагивает генерируемый контент (коммиты, посты, docs).
- Интеграция RTK (Rust Token Killer): PreToolUse hook `settings/hooks/rtk-rewrite.sh` сжимает вывод bash-команд на 60–90%; awareness-документ `docs/ai/rtk-awareness.md` с мета-командами и предупреждением про коллизию пакетов; автоустановка в `scripts/install.sh`.
- Compact Instructions в `AGENTS.md` — директива для auto-compaction: что сохранять, что выбрасывать при сжатии контекста.
- Windows-инструкции во всех setup-доках `docs/setup/` — пути, команды, установка зависимостей.
- Проверка rtk-бинарника в `settings/hooks/session-start-reminder.sh` — предупреждение, если rtk не установлен.

### Изменено
- `docs/ai/writing-voice.md` — сокращён с 6.8KB до ~3KB: убрано дублирование с tg-post-writer style-guide.
- `AGENTS.md` — `ml.md` вынесен из постоянной цепочки (загружать вручную для ML-проектов через `@./docs/ai/ml.md`); добавлен импорт `rtk-awareness.md`; добавлена секция Compact Instructions.
- `settings/claude-settings.json` — добавлен PreToolUse hook для rtk-rewrite.
- `scripts/install.sh` — Windows-детекция; автоустановка rtk; авто-мерж `permissions` и `hooks` в существующий `~/.claude/settings.json` через jq.

### Исправлено
- `scripts/install.sh` — `_generate_skill_commands` больше не завершалась с exit 1 при `--dry-run`.

## [0.2.0] — 2026-04-19

### Добавлено
- Скилл `skills/strikez/boilerplate` — одна команда (`/strikez:boilerplate`) разворачивает новый проект: скачивает актуальный шаблон из публичного репо `tsergeytovarov/strikez-boilerplate`, подставляет плейсхолдеры, копирует снэпшот AI-правил, генерирует `docs/DEPLOY.md` с точными командами для VM, создаёт GitHub репо и делает начальный коммит. Поддерживает 4 стека: `nextjs-fastapi`, `fastapi-only`, `landing`, `docs`.
- Репо `tsergeytovarov/strikez-boilerplate` (публичный) — рабочие шаблоны для всех четырёх стеков. Каждый стек верифицирован: docker-compose up поднимается, `/health` отдаёт 200, mkdocs build проходит, HTML валиден.
- `scripts/deploy-skills.sh` — одна команда разворачивает скиллы на все платформы: прогоняет `install.sh` (Claude Code + Codex + Gemini + Cursor), пакует скиллы в zip для Claude Desktop и **авто-синкает обновления** в уже загруженные скиллы через rsync. Режим щадящий (без `--delete`) — чужие файлы не трогаются. Первая загрузка через UI (zip в `dist/claude-desktop-skills/`), последующие апдейты — автоматически.
- `docs/ai/writing-voice.md` — модуль голоса для всего **генерируемого контента**: коммиты, PR, CHANGELOG, TODO, документация, TG-посты, статьи. Явно прописано, где **не** применяется: UI-строки продукта, ошибки для конечных пользователей, формальная API-дока, чат-ответы (на них действует `style.md`). Содержит правила: присутствие автора, разделение факта и мнения, гипербола как приём, стоп-лист канцелярита/инфобиза, жёсткое правило про кавычки, руководство по тону коммитов.
- Скилл `skills/strikez/tg-post-writer` поднят до **1.1.0**: полный стайл-гайд канала, 10 эталонных постов по жанрам, блок required reading и вызов чек-листа перед возвратом в `SKILL.md`.

### Изменено
- `AGENTS.md` — добавлена секция **3. Writing Voice** с импортом `docs/ai/writing-voice.md`. Секции сдвинуты.
- README — предупреждение о кастомизации перенесено **перед** блоком установки.

## [0.1.2] — 2026-04-18

### Добавлено
- `docs/setup/customization.md` — гайд для тех, кто клонирует репо: что надо поправить под себя (персона, стиль, стек, скиллы) и чего не трогать (генерируемые файлы, симлинки). Ссылка добавлена в README со статусом «начни отсюда».
- В `docs/setup/customization.md` — готовые промпты под каждую редактируемую секцию (persona, style, стек, commands, git-workflow, язык-специфичные модули, скиллы, субагенты, safety-rules). Промпт задаёт 4–6 вопросов по одному и возвращает готовый markdown на английском.

## [0.1.1] — 2026-04-18

### Изменено
- `~/.codex/AGENTS.md` теперь не симлинк, а плоский файл с развёрнутыми `@imports`. Codex CLI не резолвит `@imports` в стиле Claude/Gemini и при симлинке видел только верхний уровень — модули `docs/ai/*.md` до модели не доходили. `install.sh` вызывает `sync-cursor.sh --codex` для генерации.
- `sync-cursor.sh` получил флаг `--codex` (плоский вывод без Cursor frontmatter в `~/.codex/AGENTS.md`). Путь к скрипту и семантика `--global` / `--project` не изменились.

### Удалено
- `.github/workflows/ci.yml` — GitHub Actions на аккаунте заблокирован биллингом, а для личной библиотеки CI не нужен. Локальный `pytest tests/` остаётся основным способом проверки.
- `settings/codex-config.toml` — содержал выдуманные `[agents]/[behavior]` поля, которых в реальной схеме Codex CLI нет. Codex читает `~/.codex/AGENTS.md` без доп. настроек, эталон не нужен.

### Исправлено
- `docs/setup/codex.md` — описание теперь соответствует фактической логике (flat-файл, а не симлинк).
- `docs/setup/cursor.md` — убрано упоминание удалённого CI в разделе про `--check`.

## [0.1.0] — 2026-04-18

### Первый релиз

- `AGENTS.md` с 13 секциями + 11 модулей `docs/ai/` (persona, style, commands, coding-standards, python, typescript, git-workflow, red-flags, three-tiers, hard-gates, ml).
- Персона «Афина» + 6 специализированных субагентов (`code-reviewer`, `debugger`, `fastapi-backend`, `next-frontend`, `ml-helper`, `pr-writer`).
- 4 скилла: `ru-commit-message`, `ru-pr-description`, `changelog-entry`, `tg-post-writer`.
- `skill-lint` (pytest, 9 проверок) с negative fixture — 37 тестов, все зелёные.
- Установщики: `install.sh`, `init-project.sh`, `sync-cursor.sh`, `bump-skill-version.sh`.
- GitHub Actions CI: `skill-lint`, `check-imports`, `markdown-lint` (warnings only).
- Setup-гайды для Claude Code / Codex / Cursor / Gemini CLI (русский, `docs/setup/`).
- `examples/` — курируемые ссылки (стандарты, практики, тулзы) и структура промптов.

### Известные нюансы

- CI на момент релиза не прогнан — GitHub Actions заблокирован верификацией биллинга владельца аккаунта. Локально `pytest` и `sync-cursor.sh --check` зелёные. Разблокировка отложена отдельной задачей.
