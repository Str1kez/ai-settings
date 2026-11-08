# CLAUDE.md

<!-- Claude Code entry point. Imports AGENTS.md — the source of truth for all AI platforms. -->

@./AGENTS.md

## Claude Code-specific notes

- Always use the `Skill` tool (never `Read` on skill files) when invoking a skill.
- Use the `Agent` tool with `subagent_type` to delegate heavy, isolated tasks. Check the available agent types first: a project's `.claude/agents/` overrides the global `~/.claude/agents/`, and only project agents carry a chosen model (global ones run on the session model). `./agents/` in the ai-settings repo holds templates, not ready agents.

## Claude Code controls

Model switches use `/model`. Effort switches use `/effort` with `low`, `medium`, `high`, `xhigh`, or `max`.
