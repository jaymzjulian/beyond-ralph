---
name: beyond-ralph-resume
prefix: "@br-resume"
category: orchestration
color: yellow
description: "Resume a paused Beyond Ralph project"
---

# /beyond-ralph-resume - Resume Paused Project

Resume a Beyond Ralph project that was paused (due to quota limits, user interrupt, or session end).

## Resume Process

1. **Check Quota**: Run `/usage` first - don't resume if still limited

2. **Read State**: Load `.beyond_ralph_state` for:
   - Last active phase
   - Current module
   - Pending tasks

3. **Read Knowledge**: Check `beyondralph_knowledge/` for context

4. **Read Task Status**: Scan `records/*/tasks.md` to find:
   - In-progress tasks
   - Next tasks to start

5. **Resume Orchestration**: Continue from the paused phase

## Quota Check

If quota is still limited (≥85%), report:
```
Cannot resume - quota still limited
Session: X% | Weekly: Y%
Will auto-retry when quota resets.
```

## Start Now

1. Check quota with `/usage`
2. If OK, read state and resume
3. If limited, report and wait
