# skill-lint

Автоматические проверки качества всех скиллов в `skills/`.

## Запуск локально

    pytest tests/skill_lint/ -v

## Что проверяется

Каждый `skills/**/SKILL.md`, который отслеживает git, валидируется набором правил — см. `test_skills.py`: frontmatter, обязательные поля, триггер и SKIP в `description`, длина `description` от 100 до 1024 символов, имя по regex Agent Skills, semver, `CHANGELOG.md`, секреты.
Неотслеживаемые и игнорируемые записи в `skills/` (npx-симлинки, `synced/`, `.trash/`) не проверяются.

## Как добавить новую проверку

Добавь функцию `test_<что>(skill_path, skill_frontmatter)` в `test_skills.py`. Она автоматически применится ко всем скиллам через pytest-фикстуру `skill_path`.
