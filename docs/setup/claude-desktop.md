# Claude Desktop

> **Без поддержки.** Я не пользуюсь Claude Desktop и не проверяю `deploy-skills.sh`: работает ли он с текущей версией Desktop, не знаю. Гайд оставлен для мейнтейнера, если такой появится, см. [ARCHITECTURE.md](../../ARCHITECTURE.md#поддержка).

Claude Desktop не читает `~/.claude/skills`: это канал Claude Code. Папки, за которой он следит, у него тоже нет, скиллы добавляются только через Upload в настройках. Зато после первой загрузки Desktop разворачивает скилл в открытую папку в `~/Library/Application Support/Claude/`, и обновления можно класть туда напрямую. На этом построен `deploy-skills.sh`:

```bash
~/.ai-settings/scripts/deploy-skills.sh
```

Скрипт:

- прогоняет `install.sh` для остальных харнессов;
- пакует каждый скилл репы в zip в `dist/claude-desktop-skills/` — для первой загрузки через UI;
- в скиллы, которые Desktop уже загрузил, делает `rsync` из репы прямо в его папку. Без `--delete`: файлы, которых нет в репе, остаются.

## Порядок

1. Первый раз: Settings → Capabilities → Skills → Upload, перетащи zip из `dist/claude-desktop-skills/` и включи тумблеры.
2. Дальше: `deploy-skills.sh` после правок в репе и перезапуск Desktop.

Новый скилл, которого в Desktop ещё нет, скрипт покажет в списке тех, что требуют первой загрузки. Внешние скиллы из `npx skills` он не пакует, только `skills/` репы.
