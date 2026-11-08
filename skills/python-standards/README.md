# python-standards

Скилл держит мои правила для Python: какую версию брать, как работать с uv, типы, интерфейсы через `abc.ABC`, паттерны FastAPI и LiteStar, SQLAlchemy с Alembic и baseline-конфиг ruff и mypy для `pyproject.toml`. Раньше всё это лежало в общих правилах и грузилось в каждую сессию, даже если Python в ней не было.

## Когда вызывается

- Агент пишет или ревьюит Python-код.
- Агент настраивает Python-проект: `pyproject.toml`, ruff, mypy, uv, pytest.
- `coder` и `code-reviewer` вызывают его сами, если в задаче или диффе есть Python.

## Когда пропускается

Код на других языках, скрипты установщика в этой репе (там stdlib и 3.9), вопросы, которые не касаются кода и настройки проекта.

## Пример

Запрос: «заведи pyproject для нового сервиса на FastAPI».

Без скилла агент выберет версию Python и набор правил ruff на глаз.

Со скиллом он возьмёт нижнюю границу `requires-python` или `.python-version`, поставит baseline из скилла (`strict = true` у mypy, `select = ["E", "F", "I", "UP", "B"]` у ruff) и будет запускать код через `.venv/bin/python`, а не через `uv run`.
