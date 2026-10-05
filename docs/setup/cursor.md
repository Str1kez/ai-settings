# Cursor

> **Без поддержки.** Я не пользуюсь Cursor и не проверяю его. Раскладка сделана по документации, работает ли она — не знаю. Гайд оставлен для мейнтейнера, если такой появится, см. [ARCHITECTURE.md](../../ARCHITECTURE.md#поддержка).

Что ставит `install.sh`:

| Что | Куда |
|---|---|
| Скиллы | ссылка `~/.agents/skills/<name>` на каждый скилл репы |
| Агенты | рендер `~/.cursor/agents/<name>.md` |
| Правила | плоский `~/.cursor/rules/ai-settings.mdc`, который Cursor не читает, см. ниже |

## Правила

Пользовательские правила Cursor берёт только из своего UI: Customize → Rules. Из файлов он читает правила проекта: `AGENTS.md` в корне и подкаталогах и `.mdc` в `.cursor/rules/`. Так написано в [документации](https://cursor.com/docs/rules). Поэтому `~/.cursor/rules/ai-settings.mdc`, который пишет `install.sh`, Cursor не видит. Убрать эту запись из установщика — задача для мейнтейнера Cursor, она записана в [TODO.md](../../TODO.md).

Мои правила попадают в Cursor через проект:

```bash
cd my-project
~/.ai-settings/scripts/init-project.sh --cursor
```

Скрипт кладёт `.cursor/rules/ai-settings.mdc` — плоскую копию глобальных правил с frontmatter `alwaysApply: true` — и прячет её от git через `.git/info/exclude`. Это копия моих личных правил, в истории проекта ей не место. Если файл уже закоммичен, скрипт предупредит, и его надо вынуть из индекса: `git rm --cached .cursor/rules/ai-settings.mdc`.

Сама копия не обновляется. После правок в репе перезапусти в проекте `init-project.sh --cursor`, Cursor подхватит новые правила при следующем открытии окна.

## Скиллы

Cursor читает скиллы из `~/.agents/skills` и из `~/.claude/skills`. Скилл репы лежит в обоих под одним именем. Схлопывает ли Cursor такие дубли, как OpenCode, я не проверял.

## Агенты

Каждый `agents/<name>/AGENT.md` становится `~/.cursor/agents/<name>.md`: `name`, `description`, `model: inherit`. Агентам без Edit и Write (`code-reviewer`, `pr-writer`) добавляется `readonly: true`. Каталог `~/.cursor/agents` приоритетнее совместимого `~/.claude/agents`, так что Cursor берёт эти файлы, а не ссылки Claude Code.

Файл с меткой `# managed-by: ai-settings` под frontmatter установщик считает своим: перезаписывает, а рендер удалённого агента удаляет. Чужой файл под именем агента репы уезжает в `backups/<ts>/`, остальные не трогаются.

## Проверка импортов

```bash
~/.ai-settings/scripts/sync.py rules --check
```

Разворачивает все `@imports`, падает на битом и ничего не пишет. Удобно прогнать перед коммитом.
