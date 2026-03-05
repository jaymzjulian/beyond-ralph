# Beyond Ralph - Quick Start Guide

## Overview

Beyond Ralph is an autonomous multi-agent development system that implements the "Spec and Interview Coder" methodology. It takes your specification and delivers a complete, tested project.

## Your First Project

### Step 1: Create a Specification

Create a SPEC.md file describing your project:

```markdown
# My Project Specification

## Overview
Create a simple Python CLI tool that [describes what it does].

## Requirements

### Functional Requirements
1. The application MUST [requirement 1]
2. The application MUST [requirement 2]

### Non-Functional Requirements
1. Code MUST have type hints
2. Code MUST pass ruff linting
3. Code MUST have unit tests

### Project Structure
```
my_project/
├── main.py
├── tests/
│   └── test_main.py
└── pyproject.toml
```

## Success Criteria
- [Criterion 1]
- [Criterion 2]
```

### Step 2: Start Beyond Ralph

In Claude Code, run:

```
/beyond-ralph start --spec SPEC.md
```

### Step 3: Answer Interview Questions

Beyond Ralph will ask you clarifying questions during the interview phase:

```
[BEYOND-RALPH] Phase 2: Interview starting...
[AGENT:interview-001] I have questions about your requirements:

Q: What logging level should the application use by default?
- INFO (Recommended)
- DEBUG
- WARNING
- Other
```

Answer each question to help Beyond Ralph understand your requirements.

### Step 4: Watch It Work

After the interview, Beyond Ralph works autonomously:

```
[BEYOND-RALPH] Phase 3: Creating specification...
[BEYOND-RALPH] Phase 4: Planning...
[BEYOND-RALPH] Phase 5: Reviewing...
[BEYOND-RALPH] Phase 6: Validating...
[BEYOND-RALPH] Phase 7: Implementation...
[AGENT:code-001] Writing tests first (TDD)...
[AGENT:code-001] Implementing features...
[AGENT:test-002] Running tests...
[AGENT:review-003] Reviewing code quality...
[BEYOND-RALPH] Phase 8: Final testing...
[BEYOND-RALPH] Project complete!
```

### Step 5: Check Results

Your project is now complete with:
- Implemented code
- Unit tests
- Documentation
- All 7 checkboxes checked for each task

Check the task status:
```
/beyond-ralph status
```

## Commands

| Command | Description |
|---------|-------------|
| `/beyond-ralph start --spec FILE` | Start a new project |
| `/beyond-ralph status` | Show current progress |
| `/beyond-ralph resume` | Resume a paused project |
| `/beyond-ralph pause` | Pause the current project |

## Development Phases

Beyond Ralph follows 10 phases (including 8.5 and 9):

1. **Spec Ingestion**: Reads and analyzes your specification
2. **Interview**: Asks clarifying questions
3. **Spec Creation**: Creates detailed modular specifications
4. **Planning**: Creates project plan with milestones
5. **Review**: Identifies uncertainties (may loop to phase 2)
6. **Validation**: Validates the project plan
7. **Implementation**: TDD implementation with 3-agent trust model
8. **Testing**: Final testing and validation

## The Three-Agent Trust Model

During implementation, three agents work together:

1. **Coding Agent**: Writes the code using TDD
2. **Testing Agent**: Validates the implementation independently
3. **Review Agent**: Checks code quality, security, and best practices

No agent validates its own work - this ensures quality.

## Quota Management

Beyond Ralph automatically pauses when your Claude quota reaches 85%:

```
[BEYOND-RALPH] Quota at 87% - pausing...
[BEYOND-RALPH] Will resume when quota resets...
```

It checks every 10 minutes and resumes automatically.

## Example: Hello World

Here's a minimal spec for testing:

```markdown
# Hello World Project Specification

## Overview
Create a Python application that outputs "Hello, World!"

## Requirements
1. Output exactly "Hello, World!" when run
2. Exit with code 0 on success
3. Runnable via `python hello.py`

## Success Criteria
- Running `python hello.py` outputs "Hello, World!"
- All tests pass
```

Save this as `SPEC.md` and run:
```
/beyond-ralph start --spec SPEC.md
```

## Next Steps

- [Configuration](configuration.md) - Customize Beyond Ralph settings
- [Testing Guide](testing.md) - Learn about testing different app types
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
