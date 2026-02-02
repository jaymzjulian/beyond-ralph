---
name: resume
description: Resume a paused or interrupted project
args:
  - name: project
    description: Project ID to resume (optional, defaults to most recent)
    required: false
    type: string
---

# Resume Command

Resumes a previously paused or interrupted Beyond Ralph project.

## Usage

```
/beyond-ralph:resume [project-id]
```

## Arguments

- `project-id` (optional): Specific project UUID to resume. If not provided, resumes the most recent project.

## Behavior

1. Loads saved state from `.beyond_ralph_state`
2. Restores phase, progress, and active tasks
3. Continues from the last checkpoint
4. Maintains all previous decisions from interview

## Example

```
/beyond-ralph:resume
```

Or with specific project:

```
/beyond-ralph:resume br-a1b2c3d4
```

## State Recovery

On resume, Beyond Ralph will:
- Re-read PROJECT_PLAN.md
- Re-read current module specifications
- Check recent knowledge base entries
- Continue from last known good state
