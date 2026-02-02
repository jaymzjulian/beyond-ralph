---
name: start
description: Start a new autonomous development project from a specification file
args:
  - name: spec
    description: Path to the specification file
    required: true
    type: string
  - name: safemode
    description: Require permissions for dangerous operations
    required: false
    type: boolean
    default: false
---

# Start Command

Starts a new Beyond Ralph autonomous development project.

## Usage

```
/beyond-ralph:start --spec <path> [--safemode]
```

## Arguments

- `--spec` (required): Path to the specification file (Markdown)
- `--safemode` (optional): If set, requires permissions for dangerous operations

## Behavior

1. Validates the specification file exists
2. Initializes the orchestrator
3. Begins Phase 1: Spec Ingestion
4. Proceeds through all 8 phases automatically
5. Pauses only for:
   - User interview questions (Phase 2)
   - Quota limits (85%+)
   - Fatal errors

## Example

```
/beyond-ralph:start --spec ./PROJECT_SPEC.md
```

The orchestrator will then:
- Stream all agent output to this session with [AGENT:id] prefixes
- Ask questions via AskUserQuestion during interview
- Continue autonomously after interview phase
- Complete when ALL tasks have 5/5 checkboxes
