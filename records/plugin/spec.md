# Module 4: Plugin Integration - Specification

**Module**: plugin
**Location**: `.claude-plugin/`, `skills/`, `agents/`, `hooks/`, `commands/`
**Dependencies**: All other modules (this is the integration layer)

## Purpose

Provide native Claude Code integration as a plugin, enabling the `/beyond-ralph` command experience.

## Requirements

### R1: Plugin Structure
Standard Claude Code plugin layout:
```
beyond-ralph/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── skills/
│   └── beyond-ralph/
│       └── SKILL.md          # Main skill definition
├── agents/
│   ├── spec-agent.md
│   ├── interview-agent.md
│   ├── implementation-agent.md
│   ├── testing-agent.md
│   └── review-agent.md
├── hooks/
│   └── hooks.json            # Event handlers
└── commands/
    ├── start.md              # /beyond-ralph:start
    ├── resume.md             # /beyond-ralph:resume
    ├── status.md             # /beyond-ralph:status
    └── pause.md              # /beyond-ralph:pause
```

### R2: Plugin Manifest
```json
{
  "name": "beyond-ralph",
  "description": "True Autonomous Coding - Multi-agent orchestration implementing the Spec and Interview Coder methodology",
  "version": "1.0.0",
  "author": {
    "name": "jaymzjulian",
    "url": "https://github.com/jaymzjulian"
  },
  "repository": "https://github.com/jaymzjulian/beyond-ralph",
  "homepage": "https://github.com/jaymzjulian/beyond-ralph",
  "engines": {
    "claude-code": ">=1.0.0"
  }
}
```

### R3: Skills Definition
Main skill with subcommands:

```yaml
# skills/beyond-ralph/SKILL.md
---
name: beyond-ralph
description: Autonomous multi-agent development. Start, resume, or manage autonomous coding projects.
---

Beyond Ralph - True Autonomous Coding

Commands:
- /beyond-ralph:start --spec <path> - Start new project from specification
- /beyond-ralph:resume [project-id] - Resume an interrupted project
- /beyond-ralph:status - Show current project status and progress
- /beyond-ralph:pause - Pause operations (saves state)
```

### R4: Hooks Configuration
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "python -m beyond_ralph.hooks.stop_handler"
        }],
        "description": "Ralph-loop persistence"
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [{
          "type": "command",
          "command": "python -m beyond_ralph.hooks.quota_check"
        }],
        "description": "Check quota before spawning agents"
      }
    ],
    "SubagentStop": [
      {
        "hooks": [{
          "type": "command",
          "command": "python -m beyond_ralph.hooks.agent_complete"
        }],
        "description": "Handle agent completion"
      }
    ]
  }
}
```

### R5: Output Streaming
All subagent output must stream to main Claude Code session:
```
[BEYOND-RALPH] Phase 2: Interview Agent starting...
[AGENT:interview-abc123] I need to ask you some questions.
[AGENT:interview-abc123] 1. What authentication method do you prefer?
[USER INPUT REQUIRED]
... user answers via AskUserQuestion ...
[AGENT:interview-abc123] Great, using OAuth2.
[BEYOND-RALPH] Interview complete, transitioning to Phase 3...
```

### R6: User Interaction Flow
```
User: /beyond-ralph:start --spec myproject.md

[BEYOND-RALPH] Starting autonomous development...
[BEYOND-RALPH] Phase 1: Ingesting specification...
[AGENT:spec-001] Reading myproject.md...
[AGENT:spec-001] Identified 5 major features
[BEYOND-RALPH] Phase 2: Interview starting...
[AGENT:interview-002] I have questions about your requirements:

<AskUserQuestion appears in Claude Code UI>
Q: What database system should we use?
- PostgreSQL (Recommended)
- MySQL
- SQLite
- Other

User selects: PostgreSQL

[AGENT:interview-002] Noted. Next question...
```

### R7: Installation Methods
Support both:
1. **PyPI**: `pip install beyond-ralph` then `claude --plugin-dir ~/.local/lib/python3.11/site-packages/beyond_ralph/.claude-plugin`
2. **Plugin**: `/plugin install beyond-ralph` (downloads and installs from registry)

### R8: Configuration File
```yaml
# beyond-ralph.yaml (user config)
safemode: false
max_parallel_agents: 7
quota_threshold: 85
notification:
  channels:
    - type: slack
      webhook_url: ${SLACK_WEBHOOK}
logging:
  level: DEBUG
  full_transcripts: true
```

## Interface

```python
class PluginManager:
    """Manages plugin installation and loading."""

    async def install(self, target: Path) -> None:
        """Install plugin to target directory."""

    async def load_config(self) -> Config:
        """Load user configuration."""

    async def register_hooks(self) -> None:
        """Register all hooks with Claude Code."""

class SkillHandler:
    """Handles skill invocations."""

    async def handle_start(self, spec_path: Path) -> None:
        """Handle /beyond-ralph:start command."""

    async def handle_resume(self, project_id: str | None) -> None:
        """Handle /beyond-ralph:resume command."""

    async def handle_status(self) -> ProjectStatus:
        """Handle /beyond-ralph:status command."""

    async def handle_pause(self) -> None:
        """Handle /beyond-ralph:pause command."""
```

## Testing Requirements

- Test plugin manifest validation
- Test skill loading and invocation
- Test hook registration
- Test output streaming format
- Test configuration loading
- Test both installation methods
