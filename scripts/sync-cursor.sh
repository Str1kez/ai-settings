#!/usr/bin/env python3
"""Generate a flat rules file by resolving @imports in AGENTS.md.

Назначения:
- `--global` / `--project PATH` — для Cursor (`.cursor/rules/ai-settings.mdc`, с frontmatter `alwaysApply: true`).
- `--codex` — для Codex CLI (`~/.codex/AGENTS.md`, без frontmatter).
- `--opencode` — для OpenCode (`~/.config/opencode/AGENTS.md`, без frontmatter).

Codex и OpenCode не резолвят @imports автоматически, поэтому им нужен плоский файл.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


IMPORT_RE = re.compile(r"^@([./\w\-/]+\.md)\s*$", re.MULTILINE)


def resolve_imports(text: str, base_dir: Path, seen: set[Path] | None = None) -> str:
    seen = seen or set()

    def replace(match: re.Match) -> str:
        rel = match.group(1)
        target = (base_dir / rel).resolve()
        if target in seen:
            return f"<!-- skipped cyclic import: {rel} -->"
        if not target.is_file():
            return f"<!-- missing import: {rel} -->"
        seen.add(target)
        inner = target.read_text(encoding="utf-8")
        return resolve_imports(inner, target.parent, seen)

    return IMPORT_RE.sub(replace, text)


def write_safely(dst: Path, content: str) -> None:
    """Пишем в dst так, чтобы не испортить исходный файл через симлинк.

    Если dst — симлинк (как после старого install.sh, когда ~/.codex/AGENTS.md
    был симлинком в репо), Path.write_text() пошёл бы по симлинку и перезаписал
    бы исходный AGENTS.md в репозитории. Поэтому сначала unlink, потом write.
    """
    if dst.is_symlink() or dst.exists():
        if dst.is_symlink():
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")


AGENT_DIR = Path(__file__).resolve().parent.parent / "agents"

# Mapping Claude Code tool names → OpenCode permission keys.
# Edit covers write/edit/apply_patch in OpenCode.
TOOL_TO_PERMISSION = {
    "Read": "read",
    "Grep": "grep",
    "Glob": "glob",
    "List": "list",
    "Bash": "bash",
    "Edit": "edit",
    "Write": "edit",
    "Task": "task",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def parse_agent_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from an AGENT.md file. Returns (fields, body).
    Minimal hand-rolled parser: handles `key: value`, `key: |` block scalars,
    and `key: [a, b, c]` flow sequences. No external yaml dependency.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("no frontmatter found")
    fm, body = m.group(1), m.group(2)

    fields: dict = {}
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "|":
            # Block scalar: collect indented lines.
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or lines[i] == ""):
                block.append(lines[i])
                i += 1
            # Dedent by 2 spaces, strip trailing empties.
            block_text = "\n".join(b[2:] if b.startswith("  ") else b for b in block).rstrip()
            fields[key] = block_text
            continue
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fields[key] = [x.strip() for x in inner.split(",") if x.strip()] if inner else []
            i += 1
            continue
        fields[key] = val
        i += 1
    return fields, body


def tools_to_permission(tools: list[str]) -> dict:
    """Convert Claude Code `tools: [...]` list into OpenCode permission dict.
    Explicitly listed tools → "allow". If edit/write is absent → edit: deny.
    If bash is absent → bash: deny. Other unspecified keys are left unset
    (OpenCode defaults apply).
    """
    perm: dict = {}
    allowed_keys = set()
    for t in tools:
        key = TOOL_TO_PERMISSION.get(t)
        if key:
            allowed_keys.add(key)
    for key in allowed_keys:
        perm[key] = "allow"
    if "edit" not in allowed_keys:
        perm["edit"] = "deny"
    if "bash" not in allowed_keys:
        perm["bash"] = "deny"
    return perm


def convert_agents_to_opencode(agents_dir: Path, dry_run: bool = False) -> int:
    """Convert agents/*/AGENT.md into OpenCode agent definitions.
    Writes prompt bodies to ~/.config/opencode/agent-prompts/<name>.md and
    merges a managed `agent` block into ~/.config/opencode/opencode.jsonc.
    `model` is intentionally NOT set by this function — it is a user-owned
    field. The merge preserves any existing per-agent keys (model, temperature,
    etc.) that the user configured in opencode.jsonc.
    """
    import json
    import subprocess

    if not agents_dir.is_dir():
        print(f"[error] agents dir not found: {agents_dir}", file=sys.stderr)
        return 1

    prompts_dir = Path.home() / ".config" / "opencode" / "agent-prompts"
    config_path = Path.home() / ".config" / "opencode" / "opencode.jsonc"

    if not dry_run:
        prompts_dir.mkdir(parents=True, exist_ok=True)

    managed: dict = {}
    count = 0
    for agent_md in sorted(agents_dir.glob("*/AGENT.md")):
        name = agent_md.parent.name
        fields, body = parse_agent_frontmatter(agent_md.read_text(encoding="utf-8"))

        tools = fields.get("tools", [])
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",") if t.strip()]
        permission = tools_to_permission(tools)

        description = fields.get("description", name).strip()
        prompt_rel = f"{{file:./agent-prompts/{name}.md}}"

        managed[name] = {
            "description": description,
            "mode": "subagent",
            "permission": permission,
            "prompt": prompt_rel,
        }

        prompt_dst = prompts_dir / f"{name}.md"
        if dry_run:
            print(f"[dry-run] would write prompt {prompt_dst}")
        else:
            write_safely(prompt_dst, body.lstrip() + "\n")
            print(f"[ok] wrote prompt {prompt_dst}")
        count += 1

    managed_block = json.dumps({"agent": managed}, ensure_ascii=False)

    if dry_run:
        print(f"[dry-run] would merge agent block into {config_path}")
        print(f"[ok] converted {count} agent(s) (dry-run)")
        return 0

    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            '{\n  "$schema": "https://opencode.ai/config.json"\n}\n',
            encoding="utf-8",
        )
        print(f"[ok] created {config_path}")

    if not shutil.which("jq"):
        print("[warn] jq not found — agent block not merged into opencode.jsonc",
              file=sys.stderr)
        print(f"       managed block:\n{managed_block}", file=sys.stderr)
        return 1

    cmd = [
        "jq", "--argjson", "managed", managed_block,
        # recursive merge: existing user fields (model, temperature) preserved,
        # managed fields (description, mode, permission, prompt) updated.
        ". * $managed",
        str(config_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[error] jq merge failed: {result.stderr}", file=sys.stderr)
        return 1
    config_path.write_text(result.stdout, encoding="utf-8")
    print(f"[ok] merged agent block into {config_path} ({count} agent(s))")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--global", dest="is_global", action="store_true",
                        help="Cursor: write to ~/.cursor/rules/ai-settings.mdc")
    parser.add_argument("--project", type=Path, default=None,
                        help="Cursor: write to <project>/.cursor/rules/ai-settings.mdc")
    parser.add_argument("--codex", action="store_true",
                        help="Codex: write flat AGENTS.md to ~/.codex/AGENTS.md (no frontmatter)")
    parser.add_argument("--opencode", action="store_true",
                        help="OpenCode: write flat AGENTS.md to ~/.config/opencode/AGENTS.md")
    parser.add_argument("--opencode-agents", action="store_true",
                        help="OpenCode: merge agents/*/AGENT.md into ~/.config/opencode/opencode.jsonc (model is user-owned)")
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().parent.parent / "AGENTS.md")
    parser.add_argument("--check", action="store_true",
                        help="Resolve imports but don't write; exit 0 if OK")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show actions without writing files")
    args = parser.parse_args()

    if args.opencode_agents:
        return convert_agents_to_opencode(AGENT_DIR, dry_run=args.dry_run)

    source: Path = args.source.resolve()
    if not source.is_file():
        print(f"[error] source not found: {source}", file=sys.stderr)
        return 1

    flat = resolve_imports(source.read_text(encoding="utf-8"), source.parent)

    if args.codex or args.opencode:
        # Codex и OpenCode не поддерживают Cursor frontmatter.
        output = flat
    else:
        frontmatter = "---\nalwaysApply: true\n---\n\n"
        output = frontmatter + flat

    if args.check:
        print(f"[ok] resolved {source} ({len(output)} chars)")
        return 0

    targets = [
        bool(args.is_global),
        bool(args.project),
        bool(args.codex),
        bool(args.opencode),
    ]
    if sum(targets) != 1:
        print("[error] exactly one of --global / --project PATH / --codex / --opencode required",
              file=sys.stderr)
        return 2

    if args.is_global:
        dst = Path.home() / ".cursor" / "rules" / "ai-settings.mdc"
    elif args.project:
        dst = args.project.resolve() / ".cursor" / "rules" / "ai-settings.mdc"
    elif args.codex:
        dst = Path.home() / ".codex" / "AGENTS.md"
    else:  # args.opencode
        dst = Path.home() / ".config" / "opencode" / "AGENTS.md"

    if args.dry_run:
        print(f"[dry-run] would write {dst}")
        return 0
    write_safely(dst, output)
    print(f"[ok] wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
