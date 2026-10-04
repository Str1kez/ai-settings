# ai-settings

Мои настройки AI-ассистентов для кода в одной репе: персона агента, стандарты кода, стиль общения, скиллы и субагенты. `install.sh` раскладывает их по харнессам, и правка в репе доходит до каждого.

Поддерживаю я **Claude Code** и **OpenCode**: ими пользуюсь и их проверяю. Установщик раскладывает настройки ещё в Codex CLI, Gemini CLI, Cursor и Claude Desktop, но эти харнессы я не использую и не поддерживаю, работает ли там раскладка — не знаю. Их код и гайды оставлены для мейнтейнеров, если такие появятся.

Как это устроено — в [ARCHITECTURE.md](ARCHITECTURE.md).

## Установка

> **Стоп. Это мой личный пресет:** персона Афина, русский язык, мой стек (Python, FastAPI, LiteStar, Vue, локально в Docker) и мои скиллы. Сначала пройди [кастомизацию](docs/setup/customization.md): там чеклист, что править, и промпты, с которыми LLM соберёт файлы под тебя. Иначе ассистент будет вести себя как я.

Нужны macOS или Linux, на Windows — WSL.

```bash
git clone https://github.com/Str1kez/ai-settings.git ~/.ai-settings
cd ~/.ai-settings
./scripts/install.sh --dry-run   # план, ничего не меняет
./scripts/install.sh
```

Повторный прогон ничего не меняет. Файл, который стоит на месте ссылки, установщик уносит в `backups/<ts>/`.

### Внешние скиллы

Скиллы Matt Pocock и `find-skills` в репе не лежат. Их ставит `npx skills`: канонично в `~/.agents/skills`, плюс ссылки в `~/.claude/skills`. Репа ими не владеет, поэтому `install.sh` их не трогает.

```bash
npx skills add mattpocock/skills -g    # интерактивно: скиллы, харнессы, ссылки или копии
npx skills add vercel-labs/skills -g -s find-skills

npx skills ls -g        # что стоит
npx skills update -g    # обновить
```

Из matt-скиллов выбери минимум `grilling` и `setup-matt-pocock-skills`: первый нужен `product-spec-pipeline` на Phase 5, без него pipeline встанет на этой фазе, второй настраивает проект после `init-project.sh`. Остальные по вкусу. Харнессы отмечай Claude Code и OpenCode, способ установки — ссылки. Скиллы `agterm` и мой личный `bmw-g20` живут вне репы и вне `npx skills`.

## В проекте

После `install.sh` правила, скиллы и агенты работают в любом проекте. Проектный слой добавляет `init-project.sh`:

```bash
cd my-project
~/.ai-settings/scripts/init-project.sh            # AGENTS.md, CHANGELOG.md, TODO.md
~/.ai-settings/scripts/init-project.sh --cursor   # плюс мои правила для Cursor, без поддержки
```

Что он создаёт и как это сочетается с matt-скиллами — в [гайде по новому проекту](docs/setup/new-project.md).

## Свой скилл или агент

Скилл — инструкция под повторяемую задачу: как писать коммит, как оформлять PR. Модель видит только его `name` и `description` и по ним решает, подгружать ли скилл в текущий диалог. Агент — субагент со своим контекстом, промптом и набором инструментов: главный агент отдаёт ему задачу целиком и получает назад результат. Агент нужен, когда задачу лучше увести из основного контекста или урезать инструменты, как у `code-reviewer`, который только читает.

Заготовку для обоих делает `scripts/new.py`:

```bash
cd ~/.ai-settings
scripts/new.py skill my-skill   # skills/my-skill/: SKILL.md, README.md, CHANGELOG.md
scripts/new.py agent my-agent   # agents/my-agent/AGENT.md
```

Заполняю заготовку, начиная с `description`: только по нему модель решает, звать скилл или агента. Дальше:

```bash
git add skills/my-skill
.venv/bin/python -m pytest tests/skill_lint tests/agent_lint   # нет .venv — сначала uv sync --frozen
./scripts/install.sh
```

- `git add` обязателен. `install.sh` ставит только то, что отслеживает git, так на каждой машине оказывается один и тот же набор. Забытый каталог он не ставит и пишет `[warn] skills/my-skill/SKILL.md is not tracked by git, …`.
- Линт ловит до коммита то, что иначе всплыло бы в работе: расплывчатый `description`, по которому модель не поймёт, когда звать, битые ссылки, дубли имён. Свежая заготовка его не проходит, пока в `description` остаются `<заготовки>`: так и задумано.
- После `install.sh` перезапусти харнесс: список скиллов и агентов он читает на старте.

Подробности — в [skills/README.md](skills/README.md) и [agents/README.md](agents/README.md).

## Обновление

```bash
cd ~/.ai-settings && git pull && ./scripts/install.sh
```

Ссылки видят правки сразу, плоские копии правил и рендеры агентов обновляет `install.sh`. Харнесс после обновления я перезапускаю: правила и список скиллов он читает на старте.

## Документация

- [Кастомизация под себя](docs/setup/customization.md) — начни отсюда
- [Архитектура](ARCHITECTURE.md) и [ADR](docs/adr/)
- Харнессы: [Claude Code](docs/setup/claude-code.md), [OpenCode](docs/setup/opencode.md)
- Без поддержки: [Codex CLI](docs/setup/codex.md), [Gemini CLI](docs/setup/gemini.md), [Cursor](docs/setup/cursor.md), [Claude Desktop](docs/setup/claude-desktop.md)
- [Новый проект](docs/setup/new-project.md)
- Свои [скиллы](skills/README.md) и [агенты](agents/README.md)
- [Ссылки по AI-кодингу](docs/links.md)

## Лицензия

MIT — см. [LICENSE](LICENSE).
