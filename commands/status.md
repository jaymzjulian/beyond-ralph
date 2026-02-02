---
name: status
description: Show current project status and progress
---

# Status Command

Displays the current status of a Beyond Ralph project.

## Usage

```
/beyond-ralph:status
```

## Output

Shows:
- **Project ID**: Unique identifier
- **Phase**: Current phase (1-8 or complete)
- **State**: Running, Paused, Waiting, Stopped
- **Progress**: Percentage complete
- **Active Agents**: Number of running subagents
- **Tasks**: Complete/Total with details
- **Recent Errors**: Last 5 errors if any

## Example Output

```
Beyond Ralph Status
===================
Project:  br-a1b2c3d4
Phase:    Implementation (7/8)
State:    Running
Progress: 65%

Active Agents: 2
Tasks: 13/20 complete

Current Task: Implement API endpoint validation

Recent Activity:
- [10:30] Completed: Database schema migration
- [10:25] Review passed: Auth middleware
- [10:20] Tests passed: User model (87% coverage)
```
