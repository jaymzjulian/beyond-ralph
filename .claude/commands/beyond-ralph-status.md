---
name: beyond-ralph-status
prefix: "@br-status"
category: orchestration
color: blue
description: "Check status of Beyond Ralph autonomous development"
---

# /beyond-ralph-status - Check Project Status

Check the current status of the Beyond Ralph autonomous development project.

## What to Report

1. **Read State**: Check `.beyond_ralph_state` for current phase and progress

2. **Task Progress**: Scan `records/*/tasks.md` for checkbox status:
   - Count tasks with all 6 checkboxes ✓
   - Count tasks in progress
   - Count tasks not started

3. **Quota Status**: Run `/usage` and report current levels

4. **Active State**: Report:
   - Current phase (1-8)
   - Active module being worked on
   - Any blocked or paused state
   - Recent knowledge entries

## Output Format

```
Beyond Ralph Status
═══════════════════
Phase: [current phase name]
Progress: [X/Y] modules complete

Task Summary:
  ✓ Complete: N tasks
  → In Progress: N tasks
  ○ Not Started: N tasks

Quota: Session X% | Weekly Y%

Recent Activity:
  - [timestamp] [activity]
```

## Start Now

Read the state files and present the status report.
