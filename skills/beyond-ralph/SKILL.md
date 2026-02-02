---
name: beyond-ralph
description: |
  True Autonomous Coding - Multi-agent orchestration implementing the Spec and Interview Coder methodology.
  Use to start, resume, or manage autonomous coding projects that run for DAYS if needed.
---

# Beyond Ralph - Autonomous Development System

Beyond Ralph is a Claude Code plugin that enables fully autonomous multi-agent development.
It implements the Spec and Interview Coder methodology with eight phases from specification
to tested, documented code.

## Commands

### Start a New Project
```
/beyond-ralph:start --spec <path>
```
Start autonomous development from a specification file. Beyond Ralph will:
1. Ingest and analyze the specification
2. Interview you about requirements and preferences
3. Create a modular specification and project plan
4. Implement using TDD with three-agent trust model
5. Test and validate until all checkboxes are complete

### Resume a Project
```
/beyond-ralph:resume [project-id]
```
Resume an interrupted or paused project. If no project ID is given, resumes the most recent project.

### Check Status
```
/beyond-ralph:status
```
Show current project status including:
- Current phase
- Progress percentage
- Active agents
- Incomplete tasks

### Pause Operations
```
/beyond-ralph:pause
```
Manually pause autonomous operations. State is saved for later resumption.

## Key Features

- **8-Phase Methodology**: Spec → Interview → Planning → Review → Validation → Implementation → Testing → Complete
- **Three-Agent Trust**: Every implementation is validated by Coding + Testing + Review agents
- **Quota Aware**: Pauses at 85% usage, resumes when quota resets
- **5/5 Checkboxes**: Every task must be Planned, Implemented, Mock tested, Integration tested, Live tested
- **Dynamic Planning**: Modules can add requirements to other modules
- **Compaction Recovery**: Automatically recovers after context compaction

## Example Usage

```
/beyond-ralph:start --spec ./my-project-spec.md
```

Beyond Ralph will then autonomously:
- Ask clarifying questions during interview phase
- Create a complete specification and project plan
- Implement features using test-driven development
- Run code review with linting and security scanning
- Continue until ALL tasks have 5/5 checkboxes checked
