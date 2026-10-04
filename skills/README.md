# Skills

Библиотека кастомных скиллов для Claude Code и OpenCode. Ссылки ставятся и для Codex, Gemini CLI и Cursor, но эти харнессы я не поддерживаю.

Каждый скилл лежит в своей папке `skills/<skill>/`. `scripts/install.sh` линкует его под тем же
именем в `~/.claude/skills/<skill>` (Claude Code) и `~/.agents/skills/<skill>` (Codex, OpenCode,
Gemini CLI, Cursor). Claude Code сам отдаёт скилл как `/<skill>`, шимы в `~/.claude/commands`
не генерируются.

Деплоятся только скиллы, которые отслеживает git: новый скилл надо сначала `git add`.
Неотслеживаемое в `skills/` остаётся от старой раскладки, где `~/.claude/skills` был симлинком
на этот каталог: `install.sh` переносит такие записи в `~/.claude/skills`.

## Правила

1. Каждый скилл — отдельная папка `skills/<skill>/` с именем в `kebab-case`
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
- Помощник: `scripts/bump-skill-version.sh <skill-path> <major|minor|patch> [--note "..."]` поднимает версию во frontmatter и добавляет заготовку записи в CHANGELOG скилла. Коммит — руками.

## Skill-lint

Все скиллы проверяются через `.venv/bin/python -m pytest tests/skill_lint`. Линт прогоняется локально перед коммитом — вручную или через pre-commit hook. Список проверок см. в `tests/skill_lint/README.md`.

## Стартовый набор

- `en-commit-message` — conventional commit на английском из staged diff.
- `ru-pr-description` — PR-описание на русском по шаблону.
- `en-pr-description` — PR-описание на английском по шаблону.
- `changelog-entry` — запись в корневой `CHANGELOG.md` проекта (на русском).
- `feature-architecture` — одна рекомендованная архитектура новой фичи поверх существующей кодовой базы.
- `product-spec-pipeline` — продуктовая спецификация из идеи: анализ проекта, выбор направления, исследования, grilling и независимые ревью.
- `spec` — короткий алиас `product-spec-pipeline`.
