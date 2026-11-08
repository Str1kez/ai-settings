# aisettings

Пакет за `scripts/sync.py`. Раскладывает артефакты репы по хоумам харнессов: Claude Code, Codex, OpenCode, Gemini CLI, Cursor. `install.sh` зовёт `sync.py all`, `init-project.sh --cursor` — `sync.py rules --cursor-project`.

## Запуск

```bash
scripts/sync.py all [--dry-run]
scripts/sync.py rules [--dry-run] [--check | --cursor-project PATH]
scripts/sync.py skills [--dry-run]
scripts/sync.py agents [--dry-run]
scripts/sync.py claude [--dry-run]
scripts/sync.py opencode [--dry-run]
scripts/sync.py project-agents PROJECT [--dry-run] [--claude-models SPEC] [--opencode-models SPEC]
```

`project-agents` зовёт `init-project.sh`. SPEC — `frontier=opus,standard=sonnet`, для OpenCode модели вида `provider/model`. Подкоманда пишет агентов в `PROJECT/.claude/agents` и `PROJECT/.opencode/agents` (в файле строка `# model-level:` с уровнем), чужие одноимённые файлы пропускает, наших агентов без шаблона удаляет. Без флагов обновляет харнессы, где наши агенты уже лежат: модель уровня берёт из их строк `# model-level:`, флаги её перекрывают. Уровень без модели — выход 3 и строки `missing-model: HARNESS LEVEL` в stderr; две разные модели на уровень в файлах — выход 1 с именами файлов. В stdout печатает записанные файлы относительно `PROJECT`: по ним `init-project.sh` прячет их в `.git/info/exclude`. В терминале `init-project.sh` сам спрашивает модели: зовёт подкоманду с `--dry-run` и пустой привязкой харнесса (`--claude-models ""`), читает из stderr `missing-model` и передаёт ответы теми же флагами.

`--dry-run` печатает план и ничего не меняет. `rules --check` разворачивает `@imports` и падает на битом.

## Модули

- `fs.py` — через `Fs` идёт каждое изменение в хоуме:
  - `link` ставит симлинк. Чужую ссылку заменяет, настоящий файл или каталог уносит в `backups/<ts>/`.
  - `write` пишет сгенерированный файл. Симлинк на его месте заменяет и сквозь него не пишет.
  - `update_in_place` правит файл пользователя там, где он лежит, в том числе сквозь симлинк в дотфайлы.
  - `remove_file` удаляет файл, который сгенерировал установщик, например рендер агента, которого в репе больше нет.
  - Гард: `Fs` отказывается что-либо создавать в каталоге, который на деле лежит внутри репы. Так старый симлинк каталога в репу не превратит раскладку в запись в репу.
- `rules.py` — ссылки на `CLAUDE.md` и `GEMINI.md`, плоский `AGENTS.md` для Codex, OpenCode и Cursor.
- `skills.py` — каждый отслеживаемый скилл `skills/<skill>/` в `~/.claude/skills` и `~/.agents/skills`.
- `tracked.py` — какие каталоги `skills/<name>/` и `agents/<name>/` отслеживает git. Деплоятся только они. Каталог, удалённый без `git rm`, считается отсутствующим. Настоящий каталог с маркером (`SKILL.md`, `AGENT.md`), которого git не отслеживает и не игнорирует, — предупреждение о забытом `git add`.
- `agents.py` — парсер `agents/<name>/AGENT.md` (падает, если `name` во frontmatter не равен имени каталога): шаблон с уровнем модели становится глобальным агентом, помеченным рендером для Claude Code (`model: inherit`) и субагентом без `model` для OpenCode. Ссылки на репу, оставшиеся от прошлых версий, удаляются.
- `claude.py` — мёрдж шаблона `settings/claude-settings.json` в `~/.claude/settings.json` и ссылки на скрипты хуков в `~/.claude/hooks`. Шаблон владеет `$schema`, ключами `env` из шаблона, `permissions.{allow,ask,deny}` и своими хуками, остальное в файле пользовательское и не трогается. Ключ `env` шаблона, которого нет в файле, встаёт первым: так в логе рядом с изменением не оказывается строка пользователя с токеном. Шаблон же задаёт список скриптов: линкуется каждый `~/.claude/hooks/<script>`, который он запускает, и только в такой форме в начале команды. Оба файла читаются и проверяются до первого изменения в хоуме. Изменённые строки `settings.json` уходят в лог без контекста, чтобы не показать значения пользователя.
- `opencode.py` — ключ `shell` в `~/.config/opencode/opencode.jsonc`. Файл с комментариями не переписывается: сканер находит корневой объект и ключи верхнего уровня (вложенный `shell` не считается), ключ вставляется текстом после первой `{`. Файла нет — создаётся с одним ключом. Другое значение `shell` остаётся с предупреждением.
- `log.py` — строки логов в stderr.

## Ограничения

Пакет запускает системный `python3`, а на чистом маке это 3.9. Поэтому только stdlib, без `match/case` и без `X | Y` вне аннотаций, в каждом модуле `from __future__ import annotations`. Интеграционные тесты гоняют `sync.py` именно этим интерпретатором.

## Новый тип артефакта

Модуль с функцией `sync(fs, repo, home)`, подкоманда в `sync.py` и вызов в ветке `all`. В хоум пишу только через `Fs`, иначе dry-run, гард и бэкапы перестают работать.

## Проверки

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check scripts tests
.venv/bin/mypy
```
