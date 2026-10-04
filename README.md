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
- [Как устроен скилл](skills/README.md)
- [Ссылки по AI-кодингу](docs/links.md)

## Лицензия

MIT — см. [LICENSE](LICENSE).
