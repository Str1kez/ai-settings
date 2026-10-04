# TODO

## В работе

- [ ] Удалить `scripts/aisettings/legacy.py`, когда обе машины мигрированы
  (личная — 2026-10-04, рабочая — ещё нет):
  вместе с ним уходят вызовы `legacy.*` в `sync.py`, помеченный блок
  миграционных методов в `fs.py`, ветка `seeing_src` в `Fs.link` и
  `tests/test_migrate_*.py`, раздел «Временное» в `ARCHITECTURE.md`.
  `agents.collect` и `agents.opencode_permission` после этого можно снова
  сделать приватными.
- [ ] Закрыть опасные формы под широкими allow шаблона
  `settings/claude-settings.json`: `Bash(git branch:*)` молча пропускает
  `git branch -D`, `Bash(git remote:*)` — `git remote set-url`, после
  которого `git push` уходит не туда, `Bash(git diff:*)` —
  `git diff --output=<file>`. Сами правила нужны: rtk одобряет переписанную
  команду только по allow-правилу исходной, встроенный read-only набор
  Claude Code ему неизвестен. Вариант — ask-гарды на такие флаги, как для
  `-exec`. Заодно убрать `Read(**)` и `Grep(**)`: allow-правило с
  относительным путём действует только в текущем каталоге, а там чтение и
  поиск и так идут без вопроса.

## Следующее

- [ ] Расширенные правила `skill-lint` (анти-дубли, проверка ссылок).
- [ ] Упростить добавление скилла и агента. Сейчас скилл — три файла руками
  по шаблону из `skills/README.md`, `git add`, skill-lint и `install.sh`;
  агент — `agents/<name>/AGENT.md` и `install.sh`. Острые углы: нет
  заготовки нового скилла; неотслеживаемый скилл молча не деплоится, а
  агент деплоится и без git; у агентов нет линта, имя берётся из каталога,
  а Claude Code показывает `name` из frontmatter.
- [ ] Перед 1.0.0 вычистить `[Unreleased]` в `CHANGELOG.md`: там остались
  записи о том, что добавлено и убрано в этом же цикле — `brainstorming`,
  мёрдж агентов в `opencode.jsonc`, Superpowers через `~/.gemini/skills`,
  `sync-cursor.sh`.

## Идеи / бэклог

- [ ] Интеграция с Yandex Cloud SDK (скилл/субагент).
- [ ] Автогенерация CHANGELOG из коммитов по conventional-commit типам.
- [ ] TUI / веб-UI для управления настройками (low priority, YAGNI пока).
- [ ] Per-skill README auto-generation из SKILL.md frontmatter.
- [ ] Харнессы без поддержки (Codex, Gemini, Cursor, Claude Desktop) — для
  мейнтейнера, если появится: проверить рендеры агентов вживую; дубли
  скиллов в Cursor, который читает и `~/.claude/skills`, и
  `~/.agents/skills`; убрать из `rules.sync` запись
  `~/.cursor/rules/ai-settings.mdc`, которую Cursor не читает;
  `context.fileName` у Gemini для проектного `AGENTS.md`.

## Сделано

- [x] Доки под текущую раскладку: `ARCHITECTURE.md`, гайды в `docs/setup/`,
  граница поддержки — Claude Code и OpenCode. `init-project.sh` кладёт в
  проект только то, что читают харнессы; `changelog-entry` снова пишет на
  русском (2026-10-04).
- [x] Harness-agnostic раскладка по [ADR 0001](docs/adr/0001-harness-agnostic-deploy.md):
  единый вход `scripts/sync.py`, плоские скиллы и агенты во всех пяти
  харнессах, мёрдж `~/.claude/settings.json` без потерь, README с матрицей
  и разделом про внешние скиллы (2026-10-04).
- [x] Поддержка OpenCode: плоские глобальные правила, общие personal skills,
  установка и setup-гайд (2026-08-08).
- [x] Риск-ориентированная политика тестов и ревью: критические контракты
  защищаются тестами, обычные правки не обрастают тестами и субагентскими
  циклами по умолчанию; fork Superpowers хранится в репозитории и не
  дублируется в Codex поверх plugin (2026-07-31).
- [x] Глобальная установка оригинального `brainstorming` из Superpowers v6.1.1 (2026-07-20).
- [x] Глобальный `$spec`: анализ проекта, brainstorming, выбранные исследования отдельными агентами, grilling, межмодельная проверка и 2 независимых ревью (2026-07-20).
- [x] Token-savings план (2026-04-19) — RTK-интеграция, Compression в style.md, Compact Instructions в AGENTS.md, Windows-инструкции в setup-доках, сокращение writing-voice.md.
- [x] Скилл `strikez:boilerplate` и публичный репо шаблонов `tsergeytovarov/strikez-boilerplate` (2026-04-19).
- [x] Имплементация по плану `docs/superpowers/plans/2026-04-18-ai-settings-implementation.md`, план остался в истории git — релиз v0.1.0 (2026-04-18).
