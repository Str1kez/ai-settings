# Skills

Скилл — инструкция для модели под повторяемую задачу: как писать коммит, как оформлять PR, как вести спецификацию. Модель видит только `name` и `description` каждого скилла и по ним решает, подгружать ли его в диалог. Целиком `SKILL.md` она читает, только когда скилл подошёл. Если задачу лучше увести в отдельный контекст или урезать инструменты, нужен не скилл, а [агент](../agents/README.md).

Скиллы работают в Claude Code и OpenCode. Ссылки ставятся и для Codex, Gemini CLI и Cursor, но эти харнессы я не поддерживаю.

## Как скилл попадает в харнесс

Каждый скилл лежит в своей папке `skills/<skill>/`. `scripts/install.sh` линкует его под тем же
именем в `~/.claude/skills/<skill>` (Claude Code) и `~/.agents/skills/<skill>` (Codex, OpenCode,
Gemini CLI, Cursor). Claude Code сам отдаёт скилл как `/<skill>`, шимы в `~/.claude/commands`
не генерируются. Раз это ссылки, для правки существующего скилла `install.sh` не нужен, только для
нового или переименованного.

Деплоятся только скиллы, которые отслеживает git: так на каждой машине стоит один и тот же набор.
Настоящий каталог с `SKILL.md`, который git не отслеживает и не игнорирует, `install.sh` не ставит
и предупреждает:

    [warn] skills/my-skill/SKILL.md is not tracked by git, so skills/my-skill isn't deployed: git add skills/my-skill

Остальное неотслеживаемое в `skills/` осталось от старой раскладки, где `~/.claude/skills` был
симлинком на этот каталог: ссылки `npx skills`, `synced/`, `.trash/`. `install.sh` переносит такие
записи в `~/.claude/skills` и не предупреждает о них.

## Новый скилл

Команды запускаю из корня репы. Линту нужен `.venv`: если его нет, сначала `uv sync --frozen`.

1. Заготовка:

   ```bash
   scripts/new.py skill <name>
   ```

   Скрипт создаёт `skills/<name>/` с `SKILL.md`, `README.md` и `CHANGELOG.md`. Имя он проверяет
   по regex из [правил](#правила), существующий каталог не перезаписывает.
2. `description` в `SKILL.md` заполняю первым: только по нему модель решает, звать ли скилл.
   Требования — [ниже](#требования-к-полю-description). Потом разделы `Purpose`, `Process` и
   `Output format`, `README.md` на русском и запись в `CHANGELOG.md`.
3. `git add skills/<name>`: без этого скилл не задеплоится.
4. Линт: `.venv/bin/python -m pytest tests/skill_lint -v`. Пока в `description` остаются
   `<заготовки>` из шага 1, он красный, так и задумано.
5. `./scripts/install.sh --dry-run`, затем `./scripts/install.sh`, и перезапуск харнесса: список
   скиллов он читает на старте. В Claude Code скилл появится как `/<name>`.

## Правка скилла

`install.sh` для правки не нужен: скилл стоит ссылкой, харнесс читает файл из репы. Чтобы харнесс
перечитал скиллы, перезапусти его. Версия нужна для истории изменений:

- Версия — semver (`major.minor.patch`) в поле `version` frontmatter, у каждой версии есть запись
  в `CHANGELOG.md` скилла. Без записи линт падает.
- `scripts/bump-skill-version.sh <skill-path> <major|minor|patch> [--note "..."]` поднимает версию
  во frontmatter и добавляет заготовку записи в `CHANGELOG.md` скилла, например
  `scripts/bump-skill-version.sh skills/en-commit-message patch --note "..."`. Коммит — руками.
- Переименовываю через `git mv skills/<old> skills/<new>`, меняю `name` во frontmatter и прогоняю
  `install.sh`: он поставит ссылку под новым именем и уберёт старую. После простого `mv` новый
  каталог останется неотслеживаемым и не задеплоится.

## Правила

1. Каждый скилл — отдельная папка `skills/<skill>/` с именем в `kebab-case`
   по regex Agent Skills `^[a-z0-9]+(-[a-z0-9]+)*$`.
2. Имя папки совпадает с полем `name` в YAML frontmatter `SKILL.md`.
3. Обязательные файлы в папке скилла:
   - `SKILL.md` — основной файл на английском с YAML frontmatter.
   - `CHANGELOG.md` — история изменений скилла, на русском, формат Keep a Changelog.
   - `README.md` — человеко-читаемое описание на русском (что делает, как вызывается, примеры).
4. Опционально `references/` — справочные материалы: шаблоны, примеры вывода, выжимки из
   документации. Ссылки на них из `SKILL.md` проверяет линт.

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
- Без `<заготовок>` из `scripts/new.py`: незаполненный черновик проходит все остальные правила.
- Даёт модели достаточно сигналов, чтобы самой решить — вызывать или нет.

Плохой description (не пройдёт skill-lint):
> `description: generates commits`

Хороший description:
> `description: "Use when the user asks 'напиши коммит' or before git commit with no message. SKIP: if the user already wrote a message, or for merge commits."`

## Skill-lint

Без линта ошибку в скилле я вижу, только когда модель на ней спотыкается: скилл не вызвался, потому
что `description` расплывчатый, или повёл не туда по битой ссылке. Линт ловит это до коммита:

```bash
.venv/bin/python -m pytest tests/skill_lint -v
```

Хука нет, линт я гоняю руками перед коммитом. Общий `.venv/bin/python -m pytest -q` включает и его.

Что он ловит:

- frontmatter: обязательные поля, `name` по regex и равен имени папки, `version` в semver и
  запись о ней в `CHANGELOG.md`;
- `description`: требования [выше](#требования-к-полю-description);
- ссылки: относительные markdown-ссылки и пути `references/...`, `assets/...`, `scripts/...` в
  бэктиках из любого `*.md` скилла ведут на существующий файл внутри репы. Внешние URL не
  загружаются, якоря не проверяются;
- дубли: один `name` у двух скиллов, скилл с именем агента из `agents/`, одинаковый `description`
  у двух скиллов с точностью до регистра и пробелов. Похожесть по порогу не проверяется;
- секреты: ключи и токены по шаблонам.

Упавший тест называет скилл и правило. Чиню скилл. Если ошиблось само правило, правлю его вместе с
тестом на этот случай. Полный список проверок и как добавить новую — в
[tests/skill_lint/README.md](../tests/skill_lint/README.md).

## Стартовый набор

- `en-commit-message` — conventional commit на английском из staged diff.
- `ru-pr-description` — PR-описание на русском по шаблону.
- `en-pr-description` — PR-описание на английском по шаблону.
- `changelog-entry` — запись в корневой `CHANGELOG.md` проекта (на русском).
- `feature-architecture` — одна рекомендованная архитектура новой фичи поверх существующей кодовой базы.
- `product-spec-pipeline` — продуктовая спецификация из идеи: анализ проекта, выбор направления, исследования, grilling и независимые ревью.
- `spec` — короткий алиас `product-spec-pipeline`.
