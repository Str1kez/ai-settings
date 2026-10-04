# OpenCode

Что ставит `install.sh`:

| Что | Куда |
|---|---|
| Правила | плоский `~/.config/opencode/AGENTS.md` |
| Скиллы | ссылка `~/.agents/skills/<name>` на каждый скилл репы |
| Агенты | markdown-агент `~/.config/opencode/agents/<name>.md` |
| RTK | плагин `~/.config/opencode/plugins/rtk.ts` |

Агенты живут в markdown-файлах, а `opencode.jsonc` установщик не трогает: провайдеры, модели, MCP и плагины в нём твои. Проверено на OpenCode 1.18.34.

## Правила

OpenCode не разворачивает `@imports`, поэтому `sync.py rules` пишет плоский `AGENTS.md`, в котором все модули уже внутри. Править его руками бесполезно: следующий прогон перезапишет.

## Скиллы

OpenCode читает скиллы и из `~/.agents/skills`, и из `~/.claude/skills`. Скилл репы лежит в обоих под одним именем. OpenCode оставляет копию из `~/.agents/skills` и на каждый дубль пишет в лог `WARN duplicate skill name`. Обе ссылки ведут в один каталог репы, так что разницы нет.

`description` скилла OpenCode режет на 1024 символах, это проверяет skill-lint.

## Агенты

Каждый `agents/<name>/AGENT.md` становится `~/.config/opencode/agents/<name>.md`:

- `description` из `AGENT.md` и `mode: subagent`;
- `permission` из `tools`: без Edit и Write — `edit: deny`, без Bash — `bash: deny`, остальные ключи по умолчанию OpenCode;
- тело `AGENT.md` становится промптом.

Модель установщик не задаёт: субагент работает на модели агента, который его вызвал.

Первая строка frontmatter — комментарий `# managed-by: ai-settings`. Такой файл принадлежит установщику: следующий прогон его перезапишет, а рендер агента, удалённого из репы, удалит. Правки в нём пропадут. Файл без метки установщик не трогает, а если его имя совпало с агентом репы, уносит в `backups/<ts>/`.

### Своя модель для агента

Поверх markdown-агента модель задаётся в JSON-конфиге. Глобально — в `~/.config/opencode/opencode.jsonc`, для одного проекта — в `opencode.json` или `opencode.jsonc` в его корне:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "code-reviewer": { "model": "opencode/claude-opus-5-5" },
    "pr-writer": { "model": "opencode/claude-haiku-4-5" }
  }
}
```

Список моделей — `opencode models`. Так можно задать `model` и ключ `permission`, которого нет в рендере. То, что задаёт рендер, из JSON не переопределить: `description`, `mode`, промпт и его ключи `permission`. OpenCode читает JSON-конфиги раньше markdown-агентов, и markdown ложится сверху. Так устроено в исходниках OpenCode, документация порядок не описывает.

## RTK

`install.sh` ставит плагин сам, если бинарник `rtk` уже есть в PATH:

```bash
rtk init -g --opencode --hook-only --no-patch
```

Флаги `--hook-only --no-patch` ограничивают команду OpenCode: она не пишет `CLAUDE.md` и `RTK.md` и не патчит `~/.claude/settings.json`, Claude Code настроен отдельно. Плагин `~/.config/opencode/plugins/rtk.ts` своей логики не содержит и отдаёт каждую команду бинарнику (`rtk rewrite <cmd>`). Проверка: `rtk init --show`.

Если `rtk` поставлен после `install.sh`, прогони его ещё раз или выполни команду выше руками.

## Проверка

```bash
ls ~/.config/opencode/agents
opencode debug config   # агенты, их модели и права
opencode debug skill    # скиллы
```

## Проект

Проектный `AGENTS.md` OpenCode читает сам, его создаёт [`init-project.sh`](new-project.md). Модель агента для одного проекта — в `opencode.json` в корне проекта, пример выше. Скрипт этот файл не создаёт: пустой конфиг ничего не настраивает.

## Обновление

```bash
cd ~/.ai-settings && git pull && ./scripts/install.sh
```

После обновления перезапусти OpenCode полностью: конфиг и список скиллов он читает на старте. Только правила: `~/.ai-settings/scripts/sync.py rules`.
