# Skills

Библиотека кастомных скиллов для AI-платформ (Claude Code, Codex, OpenCode, Cursor, Gemini CLI).

Все кастомные скиллы лежат как `skills/<namespace>/<skill>/`, сейчас это `strikez/`.
Неймспейс нужен только для группировки в репе. В харнессы скиллы раскладываются плоско,
под одним именем: `scripts/install.sh` линкует каждый в `~/.claude/skills/<skill>` (Claude Code)
и `~/.agents/skills/<skill>` (Codex, OpenCode, Gemini CLI, Cursor).
Claude Code сам отдаёт скилл как `/<skill>`, шимы в `~/.claude/commands` не генерируются.

Поэтому имя скилла уникально по всей репе, а не внутри неймспейса. Установщик падает на дубле.
Деплоятся только скиллы, которые отслеживает git: новый скилл надо сначала `git add`.
Остальное в `skills/` (симлинки `npx skills`, `synced/`, `.trash/`) установщик не трогает.

## Правила

1. Каждый скилл — отдельная папка `skills/<namespace>/<skill>/` с именем в `kebab-case`
   по regex Agent Skills `^[a-z0-9]+(-[a-z0-9]+)*$`.
2. Имя папки совпадает с полем `name` в YAML frontmatter `SKILL.md`.
3. Обязательные файлы в папке скилла:
   - `SKILL.md` — основной файл на английском с YAML frontmatter.
   - `CHANGELOG.md` — история изменений скилла, на русском, формат Keep a Changelog.
   - `README.md` — человеко-читаемое описание на русском (что делает, как вызывается, примеры).
4. Опциональные файлы:
   - `references/` — справочные материалы (шаблоны, примеры вывода, выжимки из документации).
   - `tests/fixtures.md` — тестовые кейсы для skill-lint.

## Шаблон `SKILL.md`

```markdown
---
name: <kebab-case, совпадает с именем папки>
version: 1.0.0
description: |
  Use when <явный триггер: когда пользователь прямо просит>.
  Also trigger automatically when <автоматический триггер: паттерн в контексте>.
  SKIP: <явный анти-триггер: когда НЕ вызывать>.
category: code | work
tags: [git, markdown, russian, ...]
---

# Purpose
<Одно предложение: что делает скилл и зачем.>

# Process
1. ...
2. ...

# Output format
<Формат вывода — в идеале с коротким примером.>
```

## Требования к полю `description`

- **Минимум 100 символов** — модель должна понимать, когда вызывать скилл.
- Явно содержит фразу `Use when` или `Trigger`.
- Явно содержит фразу `SKIP` или `Do NOT use`.
- **Не больше 1024 символов** — лимит OpenCode.
- Даёт модели достаточно сигналов, чтобы самой решить — вызывать или нет.

Плохой description (не пройдёт skill-lint):
> `description: generates commits`

Хороший description:
> `description: "Use when the user asks 'напиши коммит' or before git commit with no message. SKIP: if the user already wrote a message, or for merge commits."`

## Версионирование

- Semver (`major.minor.patch`) в поле `version` frontmatter.
- `CHANGELOG.md` внутри папки скилла — запись для каждой версии.
- Помощник: `scripts/bump-skill-version.sh <skill-path> <major|minor|patch>` автоматизирует бамп + запись в CHANGELOG + commit.

## Skill-lint

Все скиллы автоматически проверяются через `pytest tests/skill_lint/`. Линт прогоняется локально перед коммитом — вручную или через pre-commit hook. Список проверок см. в `tests/skill_lint/README.md`.
Отдельно линт проверяет, что имена скиллов уникальны по всей репе.

## Стартовый набор

- `strikez/en-commit-message` — conventional commit на английском из staged diff.
- `strikez/ru-pr-description` — PR-описание на русском по шаблону.
- `strikez/en-pr-description` — PR-описание на английском по шаблону.
- `strikez/changelog-entry` — запись в корневой `CHANGELOG.md` проекта (на английском).
- `strikez/feature-architecture` — одна рекомендованная архитектура новой фичи поверх существующей кодовой базы.
- `strikez/boilerplate` — развернуть новый проект: шаблон + GitHub репо + AI-правила + инструкция деплоя.
