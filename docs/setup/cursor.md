# Cursor — подключение `ai-settings`

У Cursor нет стабильного user-global механизма правил (зависит от версии). Используем гибрид: глобальная попытка + per-project как надёжный fallback.

## Глобальная попытка

`scripts/install.sh` запускает `sync.py all`, который среди прочего пишет `~/.cursor/rules/ai-settings.mdc`. Если твоя версия Cursor это подхватывает, правила применяются везде.

## Скиллы

Cursor читает скиллы из `~/.agents/skills/<skill>` (и из `~/.claude/skills`). `install.sh` кладёт туда по симлинку на каждый скилл репы, имена плоские, как в других харнессах.

## Per-project (надёжнее)

В корне проекта:

```bash
~/.ai-settings/scripts/init-project.sh
```

Скрипт положит `.cursor/rules/ai-settings.mdc` прямо в проект. Cursor подхватит при следующем открытии.

## Что внутри `.mdc`

Это **плоская** версия `AGENTS.md` со всеми резолвнутыми `@imports` + Cursor-frontmatter:

```
---
alwaysApply: true
---

# AGENTS.md
<резолвнутое содержимое всех модулей>
```

Размер — около 18–20 КБ (стартовый набор правил).

## Обновление

После `git pull` в `~/.ai-settings` вручную прогони:

```bash
# глобально (заодно правила Codex, OpenCode и ссылки Claude Code, Gemini):
~/.ai-settings/scripts/sync.py rules

# для конкретного проекта:
~/.ai-settings/scripts/sync.py rules --cursor-project /path/to/project
```

Cursor подхватит новые правила при следующем открытии окна.

## Валидация без записи

```bash
~/.ai-settings/scripts/sync.py rules --check
```

Проверяет, что все `@imports` резолвятся, и падает на битом; ничего не пишет. Удобно прогонять локально перед коммитом.

## Windows

`sync.py` рассчитан на macOS и Linux: нужен `python3` 3.9+, сторонних зависимостей нет.

**WSL (рекомендуется):** запустить `./scripts/install.sh` или `./scripts/sync.py rules` из WSL-терминала.

**Без WSL (вручную):** скопировать `.cursor/rules/ai-settings.mdc` в директорию правил Cursor вручную.
