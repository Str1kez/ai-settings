# Gemini CLI — подключение `ai-settings`

## После `scripts/install.sh`

```bash
ls -la ~/.gemini/GEMINI.md ~/.gemini/AGENTS.md
# -> ai-settings/GEMINI.md и ai-settings/AGENTS.md
```

## Проверка

Запусти Gemini CLI и задай любой вопрос, требующий правил, например:

> «напиши коммит»

Если модель отвечает в стиле персоны Афины на русском и предлагает conventional-commit сообщение — всё работает.

## @imports

Gemini CLI нативно поддерживает `@imports`, поэтому модули из `docs/ai/*.md` подтягиваются автоматически при загрузке `GEMINI.md` (через транзит `GEMINI.md → @./AGENTS.md → @docs/ai/*.md`). Отдельный симлинк `~/.gemini/AGENTS.md` нужен, потому что относительный импорт разрешается из глобальной папки Gemini, а не из директории исходного симлинка.

Скиллы Gemini берёт из `~/.agents/skills/<skill>`: по симлинку на каждый скилл репы, имена те же, что в остальных харнессах. Отдельный `~/.gemini/skills` не нужен.

## Субагенты

`install.sh` кладёт по файлу на каждого агента репы в `~/.gemini/agents/<name>.md`: `name`, `description` и `tools`. Инструменты Claude Code переводятся так: Read → `read_file`, `read_many_files`; Grep → `grep_search`; Glob → `glob`, `list_directory`; Bash → `run_shell_command`; Edit → `replace`; Write → `write_file`; WebFetch → `web_fetch`; WebSearch → `google_web_search`. У агентов без Edit/Write (`code-reviewer`, `pr-writer`) нет `replace` и `write_file`. Модель не задаётся, агент берёт модель родителя.

Файлы с меткой `# managed-by: ai-settings` под frontmatter установщик считает своими: устаревшие удаляет. Чужой файл под именем нашего агента уходит в `backups/<ts>/` репы, остальные не трогаются.

## Обновление

```bash
cd ~/.ai-settings && git pull
```

Симлинк остаётся валидным. Перезапусти Gemini-сессию, чтобы подтянулись новые правила.

## Windows

**WSL (рекомендуется):** запустить `./scripts/install.sh` — GEMINI.md симлинкуется автоматически.

**Без WSL (вручную):**
```powershell
# В PowerShell:
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.gemini\GEMINI.md" -Target "$PWD\GEMINI.md"
```

> Путь на Windows: `%USERPROFILE%\.gemini\GEMINI.md`
