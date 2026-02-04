# Beyond Ralph - Configuration Guide

## Overview

Beyond Ralph can be configured through environment variables, command-line arguments, and project-specific settings.

## Command-Line Options

### Start Command

```bash
/beyond-ralph start --spec SPEC.md [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--spec` | Path to specification file | Required |
| `--safemode` | Enable permission prompts | `false` |
| `--max-agents` | Maximum parallel agents | `7` |
| `--project-root` | Project root directory | Current directory |

### Examples

```bash
# Basic usage
/beyond-ralph start --spec SPEC.md

# With safe mode (asks for permissions)
/beyond-ralph start --spec SPEC.md --safemode

# Custom project root
/beyond-ralph start --spec SPEC.md --project-root ./my-project
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BEYOND_RALPH_SAFEMODE` | Enable permission prompts | `false` |
| `BEYOND_RALPH_QUOTA_CACHE` | Quota cache file path | `.beyond_ralph_quota` |
| `BEYOND_RALPH_MAX_AGENTS` | Maximum parallel agents | `7` |
| `BEYOND_RALPH_KNOWLEDGE_DIR` | Knowledge base directory | `beyondralph_knowledge` |
| `BEYOND_RALPH_RECORDS_DIR` | Records directory | `records` |

## Project Structure

Beyond Ralph creates the following structure in your project:

```
your-project/
├── SPEC.md                    # Your specification
├── .beyond_ralph_state        # Orchestrator state (for resume)
├── .beyond_ralph_quota        # Quota cache
├── .beyond_ralph_sessions/    # Session tracking
├── beyondralph_knowledge/     # Shared knowledge base
│   ├── spec-ingestion.md
│   ├── interview-decisions.md
│   └── ...
└── records/                   # Task records
    └── [module-name]/
        └── tasks.md
```

## Quota Settings

### Thresholds

| Threshold | Action |
|-----------|--------|
| < 85% | Normal operation |
| 85-95% | Slow down, essential operations only |
| >= 95% | PAUSE, wait for reset |

### Check Interval

When paused, Beyond Ralph checks quota every 10 minutes.

### Manual Quota Check

```bash
uv run br-quota
```

Output:
```
Beyond Ralph Quota Status
Session: 45%
Weekly: 23%
Status: GREEN
```

## Safe Mode

When `safemode=true`:
- Every file operation requires permission
- System package installation requires permission
- External API calls require permission

When `safemode=false` (default):
- Operations run without prompts
- Designed for contained environments (containers, VMs)
- Allows full autonomous operation

## Agent Configuration

### Maximum Parallel Agents

Claude Code limits concurrent agents to 7. Beyond Ralph respects this:

```bash
/beyond-ralph start --spec SPEC.md --max-agents 5
```

### Agent Types

| Agent | Purpose |
|-------|---------|
| `spec` | Specification ingestion |
| `interview` | User interview |
| `planning` | Project planning |
| `validation` | Plan validation |
| `implementation` | Code implementation |
| `testing` | Test execution |
| `review` | Code review |

## Knowledge Base

### Storage Format

Knowledge entries use YAML frontmatter:

```markdown
---
title: Interview Decisions
session_id: abc123
created: 2024-01-15T10:30:00
category: decisions
---

## Authentication Method
User chose OAuth2 for authentication.

## Database
PostgreSQL selected for production database.
```

### Categories

- `phase-1` through `phase-8`: Phase-specific knowledge
- `decisions`: User decisions from interviews
- `discoveries`: Research agent findings
- `failures`: What didn't work (for future reference)

## Records System

### Task Format

```markdown
### Task: Implement User Authentication

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Implement OAuth2 authentication flow...

**Notes**: Using authlib library per interview decision.
```

### Checkbox Meanings

| Checkbox | Meaning |
|----------|---------|
| Planned | Task has been designed |
| Implemented | Code has been written |
| Mock tested | Unit tests pass |
| Integration tested | Integration tests pass |
| Live tested | Works in real environment |
| Spec compliant | Verified by compliance agent |

## Testing Configuration

### API Testing

```python
# Mock server configuration
mock_server = MockAPIServer(
    port=8080,
    spec="openapi.yaml"
)
```

### Web Testing

```python
# Playwright configuration
test_config = {
    "browser": "chromium",
    "headless": True,
    "timeout": 30000
}
```

### CLI Testing

```python
# CLI test configuration
test_config = {
    "timeout": 60,
    "interactive": True
}
```

## Hooks

### Stop Hook

The stop hook ensures Beyond Ralph persists across sessions:

```yaml
# .claude/hooks/stop.yaml
event: stop
command: beyond_ralph.hooks:stop_handler
```

### Quota Check Hook

Pre-operation quota check:

```yaml
# .claude/hooks/quota-check.yaml
event: pre_tool_use
command: beyond_ralph.hooks:quota_check
```

## Troubleshooting Configuration

### Reset State

If Beyond Ralph gets stuck, you can reset:

```bash
rm -rf .beyond_ralph_state .beyond_ralph_sessions
```

### Clear Knowledge Base

To start fresh:

```bash
rm -rf beyondralph_knowledge
```

### Clear Records

To reset task tracking:

```bash
rm -rf records
```

## Next Steps

- [Testing Guide](testing.md) - Learn about testing capabilities
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
