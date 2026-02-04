# Beyond Ralph - Plugin Structure

## Overview

Beyond Ralph integrates with Claude Code through skills and hooks, making it a native plugin that runs within the Claude Code environment.

## Directory Structure

```
.claude/
├── skills/                    # Skill definitions
│   ├── beyond-ralph.yaml      # Main start skill
│   ├── beyond-ralph-resume.yaml
│   ├── beyond-ralph-status.yaml
│   └── beyond-ralph-pause.yaml
└── hooks/                     # Hook definitions
    ├── stop.yaml              # Stop hook for persistence
    └── quota-check.yaml       # Pre-operation quota check
```

## Skills

Skills are YAML files that define commands available in Claude Code.

### Skill Format

```yaml
name: skill-name
description: Short description shown in help
trigger: /skill-name  # How users invoke it
instructions: |
  Detailed instructions for Claude Code to execute.

  ## Steps
  1. Do this
  2. Then this

  ## Example
  Show usage example here.
```

### Main Skill: beyond-ralph.yaml

```yaml
name: beyond-ralph
description: Start autonomous multi-agent development
trigger: /beyond-ralph start
instructions: |
  Start Beyond Ralph autonomous development.

  ## Usage
  /beyond-ralph start --spec SPEC.md

  ## Procedure
  1. Read the specification file
  2. Initialize orchestrator
  3. Begin 8-phase development process
  4. Stream output to user

  ## Arguments
  - --spec: Path to specification file (required)
  - --safemode: Enable permission prompts
  - --project-root: Project root directory
```

### Status Skill

```yaml
name: beyond-ralph-status
description: Show current Beyond Ralph status
trigger: /beyond-ralph status
instructions: |
  Display current project status.

  ## Procedure
  1. Read .beyond_ralph_state
  2. Show current phase
  3. Show task progress
  4. Show any errors
```

### Resume Skill

```yaml
name: beyond-ralph-resume
description: Resume paused project
trigger: /beyond-ralph resume
instructions: |
  Resume a previously paused project.

  ## Procedure
  1. Read .beyond_ralph_state
  2. Restore orchestrator state
  3. Continue from last phase
```

### Pause Skill

```yaml
name: beyond-ralph-pause
description: Pause current project
trigger: /beyond-ralph pause
instructions: |
  Pause the current project.

  ## Procedure
  1. Read current state
  2. Save checkpoint
  3. Stop orchestrator loop
  4. Report paused status
```

## Hooks

Hooks are triggered by Claude Code events.

### Hook Format

```yaml
event: event-type  # stop, pre_tool_use, etc.
command: module.function  # Python function to call
```

### Stop Hook

```yaml
# .claude/hooks/stop.yaml
event: stop
command: beyond_ralph.hooks:stop_handler
description: Handle Claude Code session stop
```

Implementation:

```python
# src/beyond_ralph/hooks/stop_handler.py
def stop_handler(context: dict) -> dict:
    """Handle stop event for ralph-loop persistence."""
    state_file = Path(".beyond_ralph_state")

    if state_file.exists():
        state = json.loads(state_file.read_text())

        if state.get("state") == "running":
            return {
                "prevent_stop": True,
                "message": "Beyond Ralph is running. Use /beyond-ralph pause first.",
            }

    return {"prevent_stop": False}
```

### Quota Check Hook

```yaml
# .claude/hooks/quota-check.yaml
event: pre_tool_use
command: beyond_ralph.hooks:quota_check
description: Check quota before operations
```

Implementation:

```python
# src/beyond_ralph/hooks/quota_check.py
def quota_check(context: dict) -> dict:
    """Pre-operation quota check."""
    from beyond_ralph.core.quota_manager import get_quota_manager

    manager = get_quota_manager()
    status = manager.check()

    if status.is_limited:
        return {
            "allow": False,
            "message": f"Quota at {status.session_percent}% - pausing",
        }

    return {"allow": True}
```

## Entry Points

Entry points register CLI commands via pyproject.toml:

```toml
[project.scripts]
br-quota = "beyond_ralph.utils.quota_checker:main"
br-session = "beyond_ralph.core.session_manager:cli_main"
br-orchestrate = "beyond_ralph.core.orchestrator:cli_main"
```

Usage:
```bash
uv run br-quota        # Check quota status
uv run br-session      # Session management
uv run br-orchestrate  # Run orchestrator
```

## Installation

### User Installation

```bash
# Copy skills to user's Claude config
mkdir -p ~/.claude/skills
cp .claude/skills/*.yaml ~/.claude/skills/

# Copy hooks
mkdir -p ~/.claude/hooks
cp .claude/hooks/*.yaml ~/.claude/hooks/
```

### Project-Local Installation

Skills and hooks can also be project-local:

```
my-project/
├── .claude/
│   ├── skills/
│   │   └── beyond-ralph.yaml
│   └── hooks/
│       └── stop.yaml
└── ...
```

## Creating New Skills

### Step 1: Define YAML

```yaml
# .claude/skills/my-skill.yaml
name: my-skill
description: What it does
trigger: /my-skill
instructions: |
  How to execute the skill.
```

### Step 2: Add Python Support (Optional)

```python
# src/beyond_ralph/skills/my_skill.py
def execute(args: dict) -> str:
    """Execute the skill."""
    return "Result"
```

### Step 3: Test

```bash
# In Claude Code
/my-skill
```

## Creating New Hooks

### Step 1: Define YAML

```yaml
# .claude/hooks/my-hook.yaml
event: event_name
command: beyond_ralph.hooks:my_handler
```

### Step 2: Implement Handler

```python
# src/beyond_ralph/hooks/my_handler.py
def my_handler(context: dict) -> dict:
    """Handle the event."""
    # Process context
    return {"key": "value"}
```

### Step 3: Register

Hooks are automatically loaded from `.claude/hooks/`.

## Best Practices

### Skills

1. Keep instructions clear and actionable
2. Include usage examples
3. Document all arguments
4. Handle errors gracefully

### Hooks

1. Be fast - hooks block execution
2. Return early if not applicable
3. Log important decisions
4. Don't throw exceptions

### General

1. Follow Claude Code conventions
2. Test with actual Claude Code
3. Document behavior
4. Handle edge cases

## Debugging

### Skill Issues

```bash
# Check skill is loaded
claude --help | grep beyond-ralph

# Verbose execution
claude --verbose /beyond-ralph status
```

### Hook Issues

```bash
# Check hook is registered
cat ~/.claude/hooks/*.yaml

# Test hook function
python -c "from beyond_ralph.hooks import stop_handler; print(stop_handler({}))"
```

## Next Steps

- [Architecture](architecture.md)
- [Agent Development](agent-development.md)
- [Contributing](contributing.md)
