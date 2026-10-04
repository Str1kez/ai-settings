# Skills

Библиотека кастомных скиллов для Claude Code и OpenCode. Ссылки ставятся и для Codex, Gemini CLI и Cursor, но эти харнессы я не поддерживаю.

Каждый скилл лежит в своей папке `skills/<skill>/`. `scripts/install.sh` линкует его под тем же
именем в `~/.claude/skills/<skill>` (Claude Code) и `~/.agents/skills/<skill>` (Codex, OpenCode,
Gemini CLI, Cursor). Claude Code сам отдаёт скилл как `/<skill>`, шимы в `~/.claude/commands`
не генерируются.

Деплоятся только скиллы, которые отслеживает git: новый скилл надо сначала `git add`.
Если в `skills/` лежит настоящий каталог с `SKILL.md`, который git не отслеживает и не
игнорирует, `sync.py` предупредит, что скилл не задеплоен, и назовёт команду `git add`.
Остальное неотслеживаемое в `skills/` остаётся от старой раскладки, где `~/.claude/skills` был
симлинком на этот каталог: `install.sh` переносит такие записи в `~/.claude/skills`, предупреждений
на них нет.

## Новый скилл

```bash
scripts/new.py skill <name>
```

Скрипт создаёт `skills/<name>/` с `SKILL.md`, `README.md` и `CHANGELOG.md`. Имя он проверяет по
regex из правил ниже, существующий каталог не перезаписывает и в конце печатает следующие шаги:

1. заполнить `SKILL.md` (сначала `description`), `README.md` и запись в `CHANGELOG.md`;
2. `git add skills/<name>`: без этого скилл не задеплоится;
3. `.venv/bin/python -m pytest tests/skill_lint -v`;
4. `scripts/install.sh --dry-run`, затем `scripts/install.sh`.

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

Шаблон лежит в `scripts/new.py` (`SKILL_MD`), второй копии в доке нет. Во frontmatter заготовки:
`name` равен имени папки, `version: 1.0.0`, `description` с заготовками триггера и `SKIP`,
`category: code` и пустой `tags`. `category` — например `code` или `work`, `tags` — свободный список
(`git`, `markdown`, `russian`). Дальше три раздела на английском: `Purpose`, `Process`,
`Output format`.

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

Кроме правил на frontmatter линт проверяет ссылки и дубли:

- Относительные markdown-ссылки и пути `references/...`, `assets/...`, `scripts/...` в бэктиках из любого `*.md` скилла должны указывать на существующий файл внутри репозитория. Внешние URL не загружаются, якоря игнорируются.
- `name` скилла уникален среди скиллов и не совпадает с именем агента из `agents/`. `description` у двух скиллов не может совпадать дословно (после приведения регистра и пробелов). Похожесть по порогу не проверяется.

## Стартовый набор

- `en-commit-message` — conventional commit на английском из staged diff.
- `ru-pr-description` — PR-описание на русском по шаблону.
- `en-pr-description` — PR-описание на английском по шаблону.
- `changelog-entry` — запись в корневой `CHANGELOG.md` проекта (на русском).
- `feature-architecture` — одна рекомендованная архитектура новой фичи поверх существующей кодовой базы.
- `product-spec-pipeline` — продуктовая спецификация из идеи: анализ проекта, выбор направления, исследования, grilling и независимые ревью.
- `spec` — короткий алиас `product-spec-pipeline`.
