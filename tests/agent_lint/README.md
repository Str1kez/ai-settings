# agent-lint

Проверки всех агентов в `agents/`. Раньше агента проверял только деплой: ошибку во frontmatter я видел на `install.sh`, а не до коммита.

## Запуск локально

    .venv/bin/python -m pytest tests/agent_lint -v

## Что проверяется

Каждый каталог в `agents/`, в котором git отслеживает файлы (`rules.py`):

- есть `AGENT.md` с frontmatter, который читается как YAML-словарь;
- `name` равен имени каталога. Claude Code показывает `name`, а ссылки и рендеры называются по каталогу;
- `description` от 100 символов, с `Use ...` (или `TRIGGER`) и `SKIP` (или `Do NOT use`), без незаполненных `<заготовок>` от `scripts/new.py`;
- `model` — уровень `frontier` или `standard`, конкретная модель вроде `opus` отклоняется. `effort` — `low`, `medium`, `high`, `xhigh` или `max`, можно не указывать. Списки читаются из `scripts/aisettings/agents.py`;
- `tools` — непустой список известных инструментов из `scripts/aisettings/agents.py`. Неизвестный рендер молча выбрасывает, и агент теряет права;
- тело не пустое: оно становится промптом;
- `sync.py` читает `description` и `tools` так же, как YAML. У него свой урезанный парсер, поэтому `description: >-` он прочтёт неверно.

Неотслеживаемые каталоги не проверяются, как и в skill-lint. `sync.py` про них предупреждает, пока их не добавили в git.

## Как добавить новую проверку

Допиши причину в `problems()` в `rules.py` и случай в `test_lint_catches_a_broken_agent` в `test_agents.py`.
