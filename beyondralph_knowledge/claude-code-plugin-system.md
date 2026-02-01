# Knowledge: Claude Code Plugin System

**Created by**: Initial Session
**Date**: 2024-02-01
**Category**: design

## Summary

Complete understanding of how Claude Code plugins, skills, hooks, and subagents work for Beyond Ralph implementation.

## Plugin Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        # Plugin manifest (ONLY this goes here)
├── commands/              # Slash commands (optional)
├── agents/                # Custom subagents (optional)
├── skills/                # Agent Skills with SKILL.md (optional)
├── hooks/                 # hooks.json event handlers (optional)
├── .mcp.json              # MCP server config (optional)
└── README.md
```

**CRITICAL**: Don't put commands/, agents/, skills/, or hooks/ inside .claude-plugin/!

## Plugin Manifest

```json
{
  "name": "beyond-ralph",
  "description": "True Autonomous Coding - Multi-agent orchestration",
  "version": "1.0.0",
  "author": {"name": "Beyond Ralph Contributors"}
}
```

The `name` becomes the skill namespace: `/beyond-ralph:start`

## Skills vs Commands

- **Commands**: Explicit `/command` trigger
- **Skills**: Activate automatically based on task context

Skill file: `skills/my-skill/SKILL.md` with frontmatter:
```yaml
---
name: my-skill
description: What this skill does
---
Instructions for the skill...
```

## Subagents

Subagents are Markdown files with YAML frontmatter in `agents/`:

```yaml
---
name: code-reviewer
description: Reviews code for quality and security
tools: Read, Grep, Glob, Bash
model: sonnet
permissionMode: default
---

You are a code reviewer...
```

### Subagent Configuration

| Field | Description |
|-------|-------------|
| name | Unique identifier (lowercase, hyphens) |
| description | When Claude should delegate |
| tools | Allowed tools (inherits all if omitted) |
| disallowedTools | Tools to deny |
| model | sonnet, opus, haiku, or inherit |
| permissionMode | default, acceptEdits, dontAsk, bypassPermissions, plan |
| skills | Skills to preload |
| hooks | Lifecycle hooks for this subagent |

### Critical Limitation

**Subagents cannot spawn other subagents!** This prevents infinite nesting.

This is CRITICAL for Beyond Ralph - the orchestrator runs in main session, subagents do the work but can't spawn their own subagents.

## Hooks

Defined in `hooks/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...],
    "SubagentStart": [...],
    "SubagentStop": [...]
  }
}
```

### Hook Events

| Event | When |
|-------|------|
| PreToolUse | Before tool use |
| PostToolUse | After tool use |
| Stop | When session/subagent stops |
| SubagentStart | When subagent begins |
| SubagentStop | When subagent completes |
| SessionStart | When session starts |
| SessionEnd | When session ends |
| UserPromptSubmit | Before user prompt processed |

### Hook Types

**Command-based**:
```json
{"type": "command", "command": "./scripts/my-hook.sh"}
```

**Prompt-based**:
```json
{"type": "prompt", "prompt": "Evaluate if appropriate: $TOOL_INPUT"}
```

### Hook Exit Codes

- 0: Success, continue
- 2: Block the operation (for PreToolUse)
- Other: Error

## Task Tool

The Task tool spawns subagents:
- Up to 7 subagents can run in parallel
- Each has its own context window
- Results return to parent
- Can run in foreground (blocking) or background

## Built-in Subagents

- **Explore**: Read-only, uses Haiku, fast codebase search
- **Plan**: Research for plan mode
- **general-purpose**: All tools, complex multi-step tasks

## Testing Plugins

```bash
claude --plugin-dir ./my-plugin
```

Multiple plugins:
```bash
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
```

## Implications for Beyond Ralph

1. **Orchestrator runs in main session** - cannot be a subagent
2. **Phase agents are subagents** - spec, interview, planning, etc.
3. **Use Stop hook** for ralph-loop persistence
4. **Subagents can't nest** - orchestrator must coordinate all
5. **Use permissionMode: bypassPermissions** for autonomous operation
6. **Parallel execution** possible with multiple Task tool calls

## Sources

- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/sub-agents
- https://github.com/anthropics/claude-code
