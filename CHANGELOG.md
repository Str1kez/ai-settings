# CHANGELOG

Все значимые изменения в этом репозитории фиксируются здесь.
Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версионирование по [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

## [1.0.2] — 2026-10-07

Разбираю ретро рефакторинга: всё, на чём агенты спотыкались по нескольку раз, записываю в доки, а дубли и мёртвые строки из глобальных правил выкидываю.

### Добавлено
- `docs/agents/release.md` — чеклист релиза по шагам 1.0.0 и 1.0.1: ветка, `CHANGELOG.md`, версия в `pyproject.toml` и `uv.lock`, `TODO.md`, проверки, PR, тег после мёрджа. Указатель на него лежит в `.claude/CLAUDE.md`.
- `docs/agents/issue-tracker.md`: в каждом файле тикета рядом со `Status:` стоит строка `**Model:** <модель>, effort <уровень>`. Её выставляет тот, кто режет тикеты, а агент, закрывший тикет, называет модель следующего по ней, а не по догадке.
- `.claude/CLAUDE.md`: правки `permissions` в `settings/claude-settings.json` классификатор auto mode блокирует как самомодификацию, поэтому агент сразу показывает diff, а применяю его я.
- `docs/ai/commands.md`: раздел про macOS. `sed` там из BSD: `sed -i` требует `''`, а GNU-синтаксис вроде `{p}` без `;` падает. Файлы правлю через Edit, не через `sed`.
- `docs/ai/red-flags.md`: для экспериментов и проверок агент заводит свежий каталог через `mktemp -d` в scratchpad и старые не чистит.

### Изменено
- Запреты `git push --force`, `git reset --hard`, `--no-verify`, `--dangerously-skip-permissions` и коммита секретных файлов живут только в `docs/ai/hard-gates.md`. Дубли убраны из таблицы Never в `three-tiers.md`, из `red-flags.md` и из раздела «Never» в `git-workflow.md`. В `three-tiers.md` остались `rm -rf` вне cwd и смена git identity.

### Исправлено
- Хвосты 1.0.1: в `docs/ai/three-tiers.md` оставались `npm test` и `npm install`, а в `docs/setup/customization.md` — Python 3.12+.

### Удалено
- Разделы Rust (cargo) и Go (go test) из `docs/ai/commands.md`: эти команды модель знает и без них. В `docs/setup/customization.md` убрал упоминания npm, cargo и go в описании `commands.md`.
- Строка «Write or edit any file» из Ask First в `docs/ai/three-tiers.md`: что агент правит без вопроса, решает режим разрешений харнесса.
- Раздел «Never» из `docs/ai/git-workflow.md`: он целиком дублировал `hard-gates.md`.

## [1.0.1] — 2026-10-06

Чищу противоречия в глобальных правилах и выкидываю TypeScript: я на нём не пишу, а модуль жрал контекст в каждой сессии.

### Исправлено
- `AGENTS.md` требовал Python 3.12+, а `docs/ai/python.md` — 3.14+. Теперь везде 3.14+.
- `docs/ai/commands.md` предлагал `black` как запасной форматтер, `python.md` его запрещает. Остался только `ruff format .`.

### Добавлено
- `docs/ai/rtk-awareness.md`: `rtk ls` и `rtk find` прячут dotfiles и фильтруют записи («… (N filtered)»). Dot-каталоги и секретные файлы проверяю через `rtk proxy ls -A` и `rtk proxy find`.

### Удалено
- TypeScript и JavaScript целиком: `docs/ai/typescript.md`, его `@import` в `AGENTS.md`, раздел npm в `docs/ai/commands.md`, три TS/React-строки в `docs/ai/red-flags.md`. Ссылки на модуль убраны из `code-reviewer`, `docs/ai/coding-standards.md` и `docs/setup/customization.md`. Vue 3 в стеке остался: он к TS не привязан.

## [1.0.0] — 2026-10-05

Раскладка переписана по [ADR 0001](docs/adr/0001-harness-agnostic-deploy.md) и не совместима со старой. Машину, где `~/.claude/skills`, `~/.claude/agents` или `~/.claude/hooks` — симлинк в репу, установщик не мигрирует, а останавливает: что делать, написано в «Изменено».

### Добавлено
- `scripts/sync.py` — единый вход раскладки. Подкоманды `all`, `rules`, `skills`, `agents`, `claude` и общий `--dry-run`, который показывает реальный план, а не список команд. За ним stdlib-пакет `scripts/aisettings/`, совместимый с системным `python3` 3.9. `install.sh` стал тонкой обёрткой: проверка на Windows, `sync.py all` и RTK. `sync-cursor.sh` и `jq` больше не нужны.
- `sync.py` не создаёт файлы и ссылки в каталоге, который на деле лежит внутри репы, например через симлинк каталога. Файл или каталог на месте ссылки уезжает в `backups/<ts>/`, а не удаляется.
- Агенты ставятся во все харнессы. Claude Code получает ссылку `~/.claude/agents/<name>.md`, OpenCode, Gemini CLI и Cursor — markdown-рендер, Codex — `~/.codex/agents/<name>.toml`. `code-reviewer` и `pr-writer` остаются read-only везде: `sandbox_mode = "read-only"` у Codex, `readonly: true` у Cursor, у Gemini нет `replace` и `write_file`, у OpenCode `edit: deny`. Модель задаётся только в Claude Code. Рендер помечен `# managed-by: ai-settings`: помеченный файл установщик перезаписывает, рендер удалённого агента удаляет, файл без метки под именем агента уезжает в `backups/<ts>/`, под другим именем остаётся.
- OpenCode получает плоский `~/.config/opencode/AGENTS.md`, общие скиллы из `~/.agents/skills` и RTK-плагин: `install.sh` ставит его через `rtk init -g --opencode --hook-only --no-patch`. Установщик в `opencode.jsonc` не пишет. Гайд — `docs/setup/opencode.md`.
- `scripts/new.py skill <name>` и `scripts/new.py agent <name>` создают заготовку скилла (`SKILL.md`, `README.md`, `CHANGELOG.md`) или агента (`AGENT.md`). Имя проверяется по regex Agent Skills, существующий каталог не перезаписывается, в конце печатаются следующие шаги.
- agent-lint в `tests/agent_lint/`: `name` равен имени каталога, `description` с триггером и `SKIP` и без заготовок, `tools` из тех, что знают рендеры, тело без `'''`. Отдельно он ловит frontmatter, который урезанный парсер `sync.py` читает не так, как YAML, например `description: >-`.
- skill-lint проверяет относительные markdown-ссылки и пути `references/…`, `assets/…`, `scripts/…` в бэктиках из любого `*.md` скилла: они должны вести на существующий файл внутри репы. Ловит дубли: один `name` у двух скиллов, скилл с именем агента, одинаковый `description`. Не пропускает `description` с незаполненными заготовками из `scripts/new.py`. Сравнение точное, без порога похожести: парные `en-pr-description` и `ru-pr-description` честно делят большую часть формулировок.
- `sync.py` предупреждает о каталоге в `skills/` или `agents/` с `SKILL.md` или `AGENT.md`, который git не отслеживает и не игнорирует, и называет команду `git add`. Раньше такой скилл молча не деплоился.
- Установщик предупреждает о хуках в `settings.json`, которые запускают `uv run`: он падает там, где кэш uv доступен только на чтение. Хука форматирования Python в шаблоне нет, линт и формат решает проект.
- Скилл `feature-architecture` — сводит разведку кодовой базы и продуктовое открытие в одну рекомендованную архитектуру фичи: диаграмма, точки интеграции, поток данных, честная оценка и явные допущения.
- Скилл `product-spec-pipeline` и короткий alias `$spec` — превращают идею или продуктовую задачу любого масштаба в адаптивную спецификацию. Пайплайн анализирует существующий проект, предлагает выбрать 1 из 2–3 направлений, по выбору запускает глубокие исследования отдельными агентами, уточняет выбранный вариант через `grilling`, проверяет результат разными моделями и отдаёт его на 2 независимых ревью в Orca.
- `ARCHITECTURE.md` — карта репы: принципы раскладки, как правила, скиллы, агенты и настройки попадают в харнессы, матрица харнессов, код установщика и известные ограничения. Поддерживаются Claude Code и OpenCode. Codex, Gemini CLI, Cursor и Claude Desktop установщик обслуживает, но без поддержки: я ими не пользуюсь и не проверяю.
- README: раздел «Внешние скиллы» с командами `npx skills` для matt-скиллов и `find-skills`, раздел про свой скилл или агента: чем они отличаются, как завести через `scripts/new.py`, зачем `git add` и линт.
- `ruff` и `mypy` в dev-зависимостях. По конфигу в `pyproject.toml` ruff проверяет `scripts/` как код под Python 3.9, а `mypy --strict` — как код под 3.10: ниже mypy не целится.

### Изменено
- Скиллы лежат плоско в `skills/<skill>/`, неймспейса `strikez/` нет: каталог не линкуется в харнессы целиком, и группировка потеряла смысл. `sync.py skills` линкует каждый отслеживаемый git скилл в `~/.claude/skills/<skill>` и `~/.agents/skills/<skill>`, одно имя во всех харнессах. Раньше Claude Code не видел вложенные `strikez/<skill>`, а Gemini получал только Superpowers. Ссылки на старые пути `skills/strikez/<skill>` и устаревшие ссылки на `skills/` репы `sync.py` перелинковывает и удаляет сам, чужие остаются.
- `~/.claude/skills`, `~/.claude/agents` и `~/.claude/hooks` — реальные каталоги, а не симлинки в репу. Если один из них всё ещё симлинк в репу, `sync.py` останавливается с ошибкой и ничего не пишет. Заменить симлинк реальным каталогом надо руками и перенести в него всё, что git в репе не отслеживает: ссылки `npx skills`, agterm, `bmw-g20`, `synced/` и `.trash/` синка Claude Code. Шимы `~/.claude/commands/<ns>/`, ссылку `~/.gemini/skills` и следы старого мёрджа агентов в `opencode.jsonc` вместе с `~/.config/opencode/agent-prompts/` установщик тоже не убирает.
- Скиллы и агенты деплоятся, только если их отслеживает git. Агент без `git add` раньше попадал в харнессы только на той машине, где лежал. Скилл, удалённый с диска без `git rm`, не оставляет битую ссылку: `sync.py` считает его удалённым и убирает ссылку. `sync.py` падает и называет файл, если `name` во frontmatter `AGENT.md` не равен имени каталога: Claude Code показывал `name`, ссылки и рендеры назывались по каталогу, и один агент жил под двумя именами.
- `~/.claude/settings.json` мёрджит `sync.py claude`. Из шаблона `settings/claude-settings.json` берутся `$schema`, списки `permissions.allow`, `.ask`, `.deny` и хуки шаблона, остальные ключи (`model`, `env`, `enabledPlugins`, `permissions.defaultMode` и прочие) остаются как были. Хуки мёрджатся по событиям: записи установщика заменяются шаблонными в одном экземпляре, чужие, например хуки agterm, не трогаются. Раньше jq заменял массивы целиком: повторный прогон стирал живые allow, а любой `PostToolUse` в шаблоне снёс бы хуки agterm. Если файл не читается как JSON или его `permissions` и `hooks` не той формы, установщик ничего не меняет и падает с ошибкой. Изменённые строки уходят в лог без строк контекста: в них могли бы попасть значения пользователя, например токены из `env`.
- Скрипты хуков линкуются поштучно: в `~/.claude/hooks` на каждый скрипт, который запускает шаблон, ссылка на `settings/hooks/<script>`. Свои скрипты можно держать там же. Ссылка на скрипт, который шаблон больше не запускает, уходит вместе с его записью в `settings.json`.
- Permissions шаблона собраны из живых настроек, раньше шаблон от них отставал. В allow нет `Bash(uv run:*)` и rtk-форм вроде `rtk find` и `rtk git status`: `rtk hook claude` решает по правилам исходной команды, достаточно разрешить сам тул. Остались мета-команды `rtk gain` и `rtk discover`. Добавлены `Bash(grep:*)`, `.venv/bin/pytest`, `.venv/bin/python -m pytest`, `.venv/bin/ruff check` и `.venv/bin/mypy`. Из ask ушли `Write(**)` и `Edit(**)`: ask-правило не автоодобряется ни в одном режиме, и `acceptEdits` с ними не работал. Новые ask-правила спрашивают на `-exec`, `-delete`, `rg --pre` и `fd -x`/`-X`: раньше `find -exec rm` и `rg --pre` проходили молча.
- RTK PreToolUse hook в шаблоне переведён с обёрточного скрипта на нативную команду бинарника `rtk hook claude`: скрипт дублировал логику, которая уже целиком живёт в `rtk`.
- `init-project.sh` кладёт в проект только то, что читают харнессы: `AGENTS.md`, `CHANGELOG.md` и `TODO.md`. Пустые `.claude/settings.json` и `opencode.jsonc` больше не создаются, строки `.claude/sessions/`, `.claude/cache/` и `.cursor/sessions/` в `.gitignore` тоже. Копия правил для Cursor пишется только с `--cursor` и сразу прячется от git через `.git/info/exclude`, раньше она уезжала в историю проекта. Рядом с одиноким `CLAUDE.md` скрипт не создаёт второй файл правил, а предупреждает.
- Гайды в `docs/setup/` переписаны под текущую раскладку: что ставит `install.sh`, проверка, проект, обновление. Агенты OpenCode описаны как markdown, JSON только задаёт им `model`. Claude Desktop переехал из README в `docs/setup/claude-desktop.md`. `skills/README.md` и `agents/README.md` написаны как инструкция: что это такое, шаги нового скилла или агента, правка и переименование, поля `AGENT.md`.
- skill-lint проверяет `description` до 1024 символов (лимит OpenCode) и имя по regex Agent Skills.
- Раздел Codex Skills в `AGENTS.md` стал харнесс-нейтральным разделом Skills.
- `docs/ai/python.md`: минимальная версия поднята до 3.14+ с акцентом на `match/case` и PEP 649 (ленивые аннотации); раздел `FastAPI patterns` расширен до `Web framework patterns` (FastAPI и LiteStar); линтинг зафиксирован как `ruff` (lint и format, без `black`) плюс обязательный `mypy --strict` с baseline-конфигом в `pyproject.toml`.

### Исправлено
- Хук `session-start-reminder.sh` показывает строку со счётчиками скиллов и агентов мне, а не только модели. Раньше обычный stdout `SessionStart` уходил в контекст, и на старте я ничего не видел. Теперь строка идёт в `systemMessage`, напоминание для модели — в `additionalContext`.
- Баннер SessionStart считает скиллы и агентов по ссылкам, которые ставит `install.sh`. Раньше `find` не шёл по симлинкам, и баннер писал `0 skill(s), 0 subagent(s)`.
- Шаблон `settings/claude-settings.json` больше не пропускает без вопроса мутирующие формы git. `git branch` и `git remote` разрешены только read-only формами: раньше префикс пропускал `git branch -D`, создание ветки и `git remote set-url`, после которого `git push` уходит не туда. `git diff`, `git log` и `git show` с `--output=<file>` спрашивают подтверждение. Правила `Read(**)` и `Grep(**)` убраны: в рабочем каталоге чтение и поиск идут без вопроса и так.
- Шаблон разрешает `echo` без вопроса, а `echo` с перенаправлением (`echo … > файл`) по-прежнему спрашивает. Хук rtk переводит составную команду целиком в запрос подтверждения, если у одного из сегментов нет своего allow-правила: связка `head …; echo ----; cat … | head` спрашивала, хотя `head` и `cat` разрешены. Это воркараунд открытого бага [rtk-ai/rtk#1347](https://github.com/rtk-ai/rtk/issues/1347); когда его закроют, правило `echo` можно убрать.
- `changelog-entry` снова пишет записи на русском, как требуют глобальные правила. В `CHANGELOG.md`, который ведётся на другом языке, он продолжает на нём.
- `sync.py rules --check` падает на битом `@import`. `sync-cursor.sh --check` завершался успехом при любых импортах.
- `sync.py rules --cursor-project` отказывается работать с несуществующим каталогом. Раньше опечатка в пути молча создавала новый каталог.
- Gemini CLI получает `~/.gemini/AGENTS.md` ссылкой: относительный импорт из `GEMINI.md` он резолвит от каталога ссылки.
- Глобальный `CLAUDE.md`: убраны `@RTK.md` (дублировал `docs/ai/rtk-awareness.md`, файл лежит вне репы) и правило про несуществующий тул `TodoWrite`; в `/effort` добавлено значение `max`. В `rtk-awareness.md` добавлено предупреждение про `rtk init -g` без `--hook-only --no-patch`.
- skill-lint проверяет только `SKILL.md`, которые отслеживает git. Раньше он падал на чужих скиллах в `skills/synced/` и `skills/.trash/`.
- `bump-skill-version.sh` добавляет запись в `CHANGELOG.md` скилла и при заголовке `# Changelog`, не только `# CHANGELOG`. Раньше он поднимал `version`, записи не писал и печатал `[ok]`. Теперь без места для записи он завершается с ошибкой и ничего не меняет.

### Удалено
- Форк Superpowers (`skills/superpowers/`) и тест на пропуск Codex-плагина. Из `install.sh` ушли проверка SP-плагина Claude, пропуск Codex-плагина и симлинк `~/.gemini/skills`. Процесс ведут внешние matt-скиллы.
- `docs/superpowers/` — планы и спеки процесса Superpowers. Они описывали старую раскладку, история осталась в git.
- Генерация шимов `~/.claude/commands/<ns>/*.md` в `install.sh`: Claude Code отдаёт скиллы как `/<skill>` сам.
- `scripts/sync-cursor.sh` — Python-скрипт с расширением `.sh`. Его заменили `sync.py rules` и `sync.py agents`.
- `settings/hooks/rtk-rewrite.sh` — заменён на нативную команду `rtk hook claude` прямо в `settings/claude-settings.json`.
- Агенты `ml-helper` и `next-frontend`. Стандарты `docs/ai/ml.md` остались и подключаются вручную.
- Скилл `boilerplate`: разворачивал проекты из публичного репо шаблонов с деплоем на мою VM, а копия AI-правил в новый проект грузилась вторым экземпляром поверх глобальных. Проектный слой даёт `init-project.sh`.
- Скиллы `tg-post-writer` и `ru-commit-message`.
- Битые симлинки `presentation-builder`, `report-builder`, `sales-kit-writer` и `strikez/write-meridian-article` — смотрели в чужие домашние каталоги.
- Ручные Windows-инструкции из гайдов `docs/setup/`: часть не работала, например Codex получал `AGENTS.md` без развёрнутых импортов. На Windows — WSL.
- Каталог `examples/`: каркас под промпты и референсы с апреля так и остался пустыми `.gitkeep`. Подборка ссылок переехала в `docs/links.md`.

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
