# TODO

## В работе

- [ ] Harness-agnostic раскладка по [ADR 0001](docs/adr/0001-harness-agnostic-deploy.md):
  готовы единый вход `scripts/sync.py`, плоская раскладка скиллов с миграцией
  старой, агенты во всех пяти харнессах и мёрдж `~/.claude/settings.json` без
  потерь. Дальше хук форматирования без uv, доки и раскатка на машины.
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
- [ ] Проверка Cursor-синка в реальной установке (разные версии Cursor).
- [ ] ML-helper: секция про versioning датасетов (DVC / lakeFS).

## Идеи / бэклог

- [ ] Интеграция с Yandex Cloud SDK (скилл/субагент).
- [ ] Автогенерация CHANGELOG из коммитов по conventional-commit типам.
- [ ] TUI / веб-UI для управления настройками (low priority, YAGNI пока).
- [ ] Per-skill README auto-generation из SKILL.md frontmatter.

## Сделано

- [x] Поддержка OpenCode: плоские глобальные правила, общие personal skills,
  установка и setup-гайд (2026-08-08).
- [x] Риск-ориентированная политика тестов и ревью: критические контракты
  защищаются тестами, обычные правки не обрастают тестами и субагентскими
  циклами по умолчанию; fork Superpowers хранится в репозитории и не
  дублируется в Codex поверх plugin (2026-07-31).
- [x] Глобальная установка оригинального `brainstorming` из Superpowers v6.1.1 (2026-07-20).
- [x] Глобальный `$spec`: анализ проекта, brainstorming, выбранные исследования отдельными агентами, grilling, межмодельная проверка и 2 независимых ревью (2026-07-20).
- [x] Token-savings план (2026-04-19) — RTK-интеграция, Compression в style.md, Compact Instructions в AGENTS.md, Windows-инструкции в setup-доках, сокращение writing-voice.md.
- [x] Скилл `strikez:boilerplate` и публичный репо шаблонов `tsergeytovarov/strikez-boilerplate` — план [`docs/superpowers/plans/2026-04-19-strikez-boilerplate.md`](docs/superpowers/plans/2026-04-19-strikez-boilerplate.md) (2026-04-19).
- [x] Имплементация по плану [`docs/superpowers/plans/2026-04-18-ai-settings-implementation.md`](docs/superpowers/plans/2026-04-18-ai-settings-implementation.md) — релиз v0.1.0 (2026-04-18).
