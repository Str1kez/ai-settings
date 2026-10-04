# ai-settings

Централизованная библиотека настроек для AI coding-ассистентов: **Claude Code**, **Codex CLI**, **OpenCode**, **Cursor** и **Gemini CLI**. Единое место, где живут персона агента, стандарты кода, стилистика общения, специализированные субагенты и переиспользуемые скиллы.

Подробный дизайн: [`docs/superpowers/specs/2026-04-18-ai-settings-design.md`](docs/superpowers/specs/2026-04-18-ai-settings-design.md).

## Установка

> ⚠️ **СТОП. Прочитай это перед `install.sh`.**
>
> Это мой личный пресет: персона «Афина», русский язык, мой стек (Python/Vue/FastAPI/LiteStar, локально в Docker), мои скиллы (русские коммиты, PR-описания).
>
> **Сначала** клонируй репо и пройди [docs/setup/customization.md](docs/setup/customization.md) — там чеклист, что править (persona, style, стек) и готовые промпты под каждую секцию (LLM задаст 4–6 вопросов и вернёт готовый файл).
>
> **Потом** запускай `install.sh`. Иначе ассистент будет вести себя как я, а не как ты.

```bash
git clone https://github.com/Str1kez/ai-settings.git ~/.ai-settings
cd ~/.ai-settings

# 1. Кастомизируй под себя — см. docs/setup/customization.md
# 2. Установи:
./scripts/install.sh
```

Установщик идемпотентный — безопасно запускать повторно. Существующие файлы бэкапятся в `backups/<timestamp>/`.

## Структура

```
ai-settings/
├── AGENTS.md                    # source of truth (читают все платформы)
├── CLAUDE.md / GEMINI.md        # тонкие обёртки с импортом AGENTS.md
├── docs/ai/                     # модули, подключаемые через @imports
├── docs/setup/                  # гайды по подключению (на русском)
├── docs/adr/                    # архитектурные решения
├── agents/<name>/AGENT.md       # субагенты в формате Claude, рендерятся под каждый харнесс
├── skills/<name>/               # свои скиллы, каждый линкуется в харнессы под своим именем
├── settings/                    # шаблон settings.json для Claude Code и его хуки
├── scripts/                     # install.sh → sync.py (пакет aisettings/), init-project.sh, deploy-skills.sh
├── examples/                    # курируемые ссылки и промпты
└── tests/                       # pytest: установщик, миграции, skill-lint в tests/skill_lint/
```

## Что куда раскладывается

Репа не линкуется в хоум харнесса целым каталогом: в `~/.claude/{skills,agents,hooks}` и `~/.agents/skills` кладутся только поштучные ссылки. Целиком линкуются лишь файлы инструкций, потому что их `@imports` резолвятся от реального пути.

| Харнесс | Правила | Скиллы | Агенты |
|---|---|---|---|
| Claude Code | симлинк `~/.claude/CLAUDE.md` | `~/.claude/skills/<name>` → репа | `~/.claude/agents/<name>.md` → `agents/<name>/AGENT.md` |
| Codex CLI | плоский `~/.codex/AGENTS.md` | `~/.agents/skills/<name>` | `~/.codex/agents/<name>.toml` |
| OpenCode | плоский `~/.config/opencode/AGENTS.md` | `~/.agents/skills` (видит и `~/.claude/skills`) | `~/.config/opencode/agents/<name>.md` |
| Gemini CLI | симлинки `~/.gemini/{GEMINI,AGENTS}.md` | `~/.agents/skills` | `~/.gemini/agents/<name>.md` |
| Cursor | `~/.cursor/rules/ai-settings.mdc` | `~/.agents/skills` (видит и `~/.claude/skills`) | `~/.cursor/agents/<name>.md` |
| Claude Desktop | — | `deploy-skills.sh` (zip + rsync) | — |

Агенты рендерятся из одного `AGENT.md` и помечаются `managed-by: ai-settings`: устаревшие свои установщик удаляет, чужие не трогает. Модель задаётся только в Claude, остальные харнессы наследуют модель родителя. Детали и причины — в [ADR 0001](docs/adr/0001-harness-agnostic-deploy.md).

## Внешние скиллы

Скиллы Matt Pocock и `find-skills` в репе не лежат. Их ставит `npx skills`: канонически в `~/.agents/skills` плюс ссылки в `~/.claude/skills`. Репа ими не владеет, поэтому `install.sh` их не трогает.

```bash
# matt-скиллы; список берётся из ~/.agents/.skill-lock.json
npx skills add mattpocock/skills -g -a claude-code codex opencode gemini-cli cursor \
  -s ask-matt code-review codebase-design diagnosing-bugs domain-modeling grill-me \
  grill-with-docs grilling handoff implement improve-codebase-architecture prototype \
  research resolving-merge-conflicts setup-matt-pocock-skills tdd teach to-questionnaire \
  to-spec to-tickets triage wait-what wayfinder wizard writing-for-agents -y

npx skills add vercel-labs/skills -g -s find-skills -y

npx skills ls -g        # что стоит
npx skills update -g    # обновить
```

Что живёт вне репы и вне `npx skills`:

- `agterm` и `bmw-g20` живут вне репы, только в `~/.claude/skills`. `bmw-g20` — мой личный скилл.
- `product-spec-pipeline` требует matt `grilling` на Phase 5. Без него pipeline дойдёт до этой фазы и встанет.

## Использование

**В новом проекте** — ничего делать не надо. Глобальные правила уже применяются автоматически через `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.config/opencode/AGENTS.md`, `~/.gemini/GEMINI.md` (для Cursor — запусти `~/.ai-settings/scripts/sync.py rules --cursor-project .` один раз в проекте).

**Для проектной специфики** — в корне проекта:

```bash
~/.ai-settings/scripts/init-project.sh
```

Положит локальный `AGENTS.md` (additive-слой поверх глобального), `.claude/settings.json` и обновит `.gitignore`.

## Обновление

```bash
cd ~/.ai-settings
git pull
./scripts/install.sh
```

Симлинки не пересоздаются — новое содержимое подхватывается автоматически.

## Скиллы в Claude Desktop

Claude Desktop не читает `~/.claude/skills/` (это канал Claude Code CLI). Нативного watched-folder у него тоже нет — скиллы добавляются только через Upload в Settings. Но после первой загрузки Desktop разворачивает скилл в открытую папку в `Library/Application Support/Claude/...`, куда можно класть обновления напрямую. На этом построена схема `deploy-skills.sh`:

```bash
./scripts/deploy-skills.sh
```

Скрипт:
- прогоняет `install.sh` (Claude Code + Codex + OpenCode + Gemini + Cursor);
- пакует каждый скилл в zip в `dist/claude-desktop-skills/` — для **первой** загрузки через UI;
- для скиллов, которые **уже** загружены, делает rsync из репы прямо в папку Desktop (щадящий режим, без `--delete` — ничего чужого не удаляется).

Порядок работы:

1. Первый раз — Settings → Capabilities → Skills → Upload, перетащи zip'ы из открывшейся папки, включи тумблеры.
2. Дальше — просто `./scripts/deploy-skills.sh` после правок в репе, перезапусти Desktop, обновления подхватываются.

Если в репе появляется новый скилл, которого ещё нет в Desktop, — скрипт подсветит его в списке «требует первой загрузки».

## Документация

- [Кастомизация под себя](docs/setup/customization.md) ← **начни отсюда**
- [Подключение Claude Code](docs/setup/claude-code.md)
- [Подключение Codex CLI](docs/setup/codex.md)
- [Подключение Cursor](docs/setup/cursor.md)
- [Подключение Gemini CLI](docs/setup/gemini.md)
- [Подключение OpenCode](docs/setup/opencode.md)
- [Новый проект](docs/setup/new-project.md)

## Лицензия

MIT — см. [LICENSE](LICENSE).
