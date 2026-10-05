# Новый проект

После `install.sh` глобальные правила, скиллы и агенты работают в любом проекте, делать ничего не надо. `init-project.sh` добавляет только то, что принадлежит самому проекту.

## Запуск

В корне проекта:

```bash
~/.ai-settings/scripts/init-project.sh            # AGENTS.md, CHANGELOG.md, TODO.md
~/.ai-settings/scripts/init-project.sh --cursor   # плюс мои правила для Cursor
```

Вместо `cd` можно передать путь: `init-project.sh path/to/project`. Существующие файлы скрипт не трогает, повторный запуск безопасен.

## Что создаётся

| Файл | Зачем |
|---|---|
| `AGENTS.md` | Факты проекта для агентов: что это, стек, команды, локальные договорённости. Читают Claude Code, Codex, OpenCode и Cursor. |
| `CHANGELOG.md` | Мои правила требуют запись в CHANGELOG на каждое заметное изменение: на русском, по Keep a Changelog. Пишет её скилл `changelog-entry`. |
| `TODO.md` | Мои правила ведут `TODO.md` в корне по ходу работы. |
| `.cursor/rules/ai-settings.mdc` | Только с `--cursor`. Копия глобальных правил: пользовательские правила Cursor берёт только из UI. Скрипт прячет её от git через `.git/info/exclude`, подробности в [гайде Cursor](cursor.md). |

`AGENTS.md` создаётся, только если в корне нет ни `AGENTS.md`, ни `CLAUDE.md`. На одинокий `CLAUDE.md` скрипт предупреждает: Codex и Cursor его не читают, а второй файл рядом разделил бы правила проекта надвое. Его лучше переименовать в `AGENTS.md`.

Обёртка `CLAUDE.md` с `@AGENTS.md` не нужна: Claude Code читает проектный `AGENTS.md` сам, я проверил это на 2.1.289. Gemini CLI читает только `GEMINI.md`, см. [гайд Gemini](gemini.md#проект).

## Matt-скиллы

Инженерным matt-скиллам нужна настройка под репу: где трекер задач, какие метки триажа, где лежат `CONTEXT.md` и ADR. После `init-project.sh` запусти в проекте `/setup-matt-pocock-skills`: он допишет блок `## Agent skills` в `AGENTS.md` и создаст `docs/agents/`. Пока `docs/agents/` нет, `init-project.sh` в конце об этом напоминает.

С `init-project.sh` они не пересекаются. Matt-скиллы не трогают `CHANGELOG.md` и `TODO.md`, а `CONTEXT.md` и `docs/adr/` создают сами, когда появляется что записать. Задачи, если трекер локальный, живут в `.scratch/<feature>/`, а `TODO.md` остаётся списком верхнего уровня.

Одно правило: не заводи `CLAUDE.md` рядом с `AGENTS.md`. Если в корне есть `CLAUDE.md`, `/setup-matt-pocock-skills` пишет свой блок в него, и Codex, OpenCode и Cursor этот блок не увидят.

## Что класть в проектный AGENTS.md

- Фреймворки и их версии.
- Команды сборки, запуска и тестов, которые отличаются от глобальных.
- Договорённости проекта, которые расходятся с глобальными правилами, и почему.
- Ссылки на ADR и архитектурные решения проекта.

Чего туда не класть:

- Глобальные правила: они уже применяются.
- Секреты и приватные конфиги.
- То, что нужно людям, а не агентам: инструкции по запуску и описание архитектуры — в `README.md`.

## Проекты, заведённые старым скриптом

Старый `init-project.sh` клал ещё пустые `.claude/settings.json` и `opencode.jsonc` и строки `.claude/sessions/`, `.claude/cache/` и `.cursor/sessions/` в `.gitignore`. Пустые конфиги ничего не настраивали, а таких каталогов в проектах не бывает: сессии и кэш Claude Code держит в `~/.claude`. Всё это можно удалить.

Ещё он клал `.cursor/rules/ai-settings.mdc`, не пряча его от git. Если файл попал в историю проекта, вынь его из индекса и перезапусти скрипт:

```bash
git rm --cached .cursor/rules/ai-settings.mdc
~/.ai-settings/scripts/init-project.sh --cursor
```
