# Gemini CLI

> **Без поддержки.** Я не пользуюсь Gemini CLI и не проверяю его. Раскладка сделана по документации, работает ли она — не знаю. Гайд оставлен для мейнтейнера, если такой появится, см. [ARCHITECTURE.md](../../ARCHITECTURE.md#поддержка).

Что ставит `install.sh`:

| Что | Куда |
|---|---|
| Правила | ссылки `~/.gemini/GEMINI.md` и `~/.gemini/AGENTS.md` на файлы репы |
| Скиллы | ссылка `~/.agents/skills/<name>` на каждый скилл репы |
| Агенты | рендер `~/.gemini/agents/<name>.md` |

## Правила

Gemini разворачивает `@imports` сам: `GEMINI.md` → `@./AGENTS.md` → `@docs/ai/*.md`. Отдельная ссылка `~/.gemini/AGENTS.md` нужна, потому что импорт из `GEMINI.md` резолвится от каталога ссылки, то есть от `~/.gemini`, а не от репы.

## Скиллы

Скиллы Gemini берёт из `~/.agents/skills`: по ссылке на каждый скилл репы, имена те же, что в остальных харнессах. Отдельный `~/.gemini/skills` не нужен.

## Агенты

Каждый `agents/<name>/AGENT.md` становится `~/.gemini/agents/<name>.md`: `name`, `description` и `tools`. Инструменты Claude Code переводятся так: Read → `read_file`, `read_many_files`; Grep → `grep_search`; Glob → `glob`, `list_directory`; Bash → `run_shell_command`; Edit → `replace`; Write → `write_file`; WebFetch → `web_fetch`; WebSearch → `google_web_search`. У агентов без Edit и Write (`code-reviewer`, `pr-writer`) нет `replace` и `write_file`. Модель не задаётся, агент берёт модель родителя.

Файл с меткой `# managed-by: ai-settings` под frontmatter установщик считает своим: перезаписывает, а рендер удалённого агента удаляет. Чужой файл под именем агента репы уезжает в `backups/<ts>/`, остальные не трогаются.

## Проверка

```bash
ls -la ~/.gemini/GEMINI.md ~/.gemini/AGENTS.md ~/.gemini/agents
```

Smoke-тест: попроси «напиши коммит». Персона Афины и Conventional Commits на английском значат, что правила подхвачены.

## Проект

По умолчанию Gemini читает только `GEMINI.md`: глобальный, в проекте и в его родителях. Проектный `AGENTS.md` он увидит, только если тот есть в `context.fileName` в `~/.gemini/settings.json`:

```json
{ "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }
```

Эту настройку я не включал. Есть вероятность, что с ней Gemini загрузит глобальные правила дважды: через `~/.gemini/GEMINI.md` и через ссылку `~/.gemini/AGENTS.md`. Перед включением это надо проверить.

## Обновление

```bash
cd ~/.ai-settings && git pull
```

Ссылки остаются валидными, перезапусти сессию Gemini. Если поменялись агенты, нужен ещё `./scripts/install.sh`.
