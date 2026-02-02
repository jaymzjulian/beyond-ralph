---
name: pause
description: Pause autonomous operations
---

# Pause Command

Manually pauses Beyond Ralph autonomous operations.

## Usage

```
/beyond-ralph:pause
```

## Behavior

1. Completes any in-progress agent work
2. Saves current state to disk
3. Stops spawning new agents
4. Can be resumed with `/beyond-ralph:resume`

## When to Use

- Need to stop development temporarily
- Want to review progress before continuing
- Need to make manual changes
- Before a long break

## Automatic Pausing

Beyond Ralph also pauses automatically when:
- Quota reaches 85% (resumes when reset)
- Fatal errors occur
- User input is required

## Example

```
/beyond-ralph:pause
```

Output:
```
Beyond Ralph paused.
State saved to .beyond_ralph_state
Resume with: /beyond-ralph:resume
```
