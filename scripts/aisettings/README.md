# aisettings

Пакет за `scripts/sync.py`. Раскладывает артефакты репы по хоумам харнессов: Claude Code, Codex, OpenCode, Gemini CLI, Cursor. `install.sh` зовёт `sync.py all`, `init-project.sh` — `sync.py rules --cursor-project`.

## Запуск

```bash
scripts/sync.py all [--dry-run]
scripts/sync.py rules [--dry-run] [--check | --cursor-project PATH]
scripts/sync.py agents [--dry-run]
```

`--dry-run` печатает план и ничего не меняет. `rules --check` разворачивает `@imports` и падает на битом.

## Модули

- `fs.py` — через `Fs` идёт каждое изменение в хоуме:
  - `link` ставит симлинк. Чужую ссылку заменяет, настоящий файл или каталог уносит в `backups/<ts>/`.
  - `write` пишет сгенерированный файл. Симлинк на его месте заменяет и сквозь него не пишет.
  - `update_in_place` правит файл пользователя там, где он лежит, в том числе сквозь симлинк в дотфайлы.
  - Гард: `Fs` отказывается что-либо создавать в каталоге, который на деле лежит внутри репы. Так старый симлинк каталога в репу не превратит раскладку в запись в репу.
- `rules.py` — ссылки на `CLAUDE.md` и `GEMINI.md`, плоский `AGENTS.md` для Codex, OpenCode и Cursor.
- `agents.py` — парсер `agents/<name>/AGENT.md` и агенты OpenCode.
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
