# Beyond Ralph - Installation & Usage Guide

## Quick Start

### Option 1: Install Commands Globally (Recommended)

Copy the command files to your global Claude commands directory:

```bash
# Create commands directory if it doesn't exist
mkdir -p ~/.claude/commands

# Copy Beyond Ralph commands
cp /path/to/beyond-ralph/.claude/commands/*.md ~/.claude/commands/
```

Then in ANY project:
```bash
cd /path/to/your/project
claude
# Type: /beyond-ralph SPEC.md
```

### Option 2: Install Commands to Specific Project

Copy commands to a specific project's `.claude/commands/` directory:

```bash
cd /path/to/your/project
mkdir -p .claude/commands
cp /path/to/beyond-ralph/.claude/commands/*.md .claude/commands/
```

Then start Claude in that project:
```bash
claude
# Type: /beyond-ralph SPEC.md
```

### Option 3: One-Line Global Install

```bash
mkdir -p ~/.claude/commands && cp ~/beyond-ralph/.claude/commands/*.md ~/.claude/commands/
```

## Available Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `/beyond-ralph <spec>` | `@br` | Start autonomous development from a spec |
| `/beyond-ralph-status` | `@br-status` | Check current project status |
| `/beyond-ralph-resume` | `@br-resume` | Resume a paused project |

## Usage Example

### 1. Create Your Project

```bash
mkdir my-project
cd my-project
```

### 2. Create a Specification File

Create `SPEC.md` with your project requirements:

```markdown
# My Project

## Overview
A web application that does X, Y, Z.

## Requirements
1. User authentication
2. Dashboard with metrics
3. API for mobile app

## Technology
- Python/FastAPI backend
- React frontend
- PostgreSQL database
```

### 3. Start Claude and Run Beyond Ralph

```bash
claude
```

Then type:
```
/beyond-ralph SPEC.md
```

### 4. Respond to Interview Questions

During Phase 2 (Interview), Claude will ask clarifying questions using `AskUserQuestion`. Answer them to refine the requirements.

### 5. Watch It Work

After the interview phase completes, Beyond Ralph operates **fully autonomously**:
- Creates modular specifications
- Plans the implementation
- Spawns child agents for coding
- Runs tests with separate agents
- Tracks progress in `records/` directory

### 6. Check Status

At any time, you can check progress:
```
/beyond-ralph-status
```

### 7. Resume If Paused

If the session ends or quota is reached:
```
/beyond-ralph-resume
```

## Directory Structure Created

Beyond Ralph creates this structure in your project:

```
your-project/
├── SPEC.md                    # Your original spec
├── PROJECT_PLAN.md            # Generated master plan
├── records/                   # Module tracking
│   ├── auth/
│   │   ├── spec.md           # Module spec
│   │   └── tasks.md          # Task checkboxes
│   ├── api/
│   │   ├── spec.md
│   │   └── tasks.md
│   └── ...
├── beyondralph_knowledge/     # Learnings & decisions
│   ├── interview-decisions.md
│   └── ...
└── .beyond_ralph_state        # Orchestrator state
```

## Task Tracking

Each task in `records/*/tasks.md` has 5 checkboxes:

```markdown
### Task: Implement User Login
- [x] Planned
- [x] Implemented
- [x] Mock Tested
- [ ] Integration Tested
- [ ] Live Tested
```

A task is only complete when ALL 5 are checked.

## Quota Management

Beyond Ralph checks `/usage` before spawning agents:
- **Green** (<85%): Normal operation
- **Yellow** (85-95%): Essential operations only
- **Red** (≥95%): Paused, waits for reset

Use `/beyond-ralph-resume` after quota resets.

## Troubleshooting

### Commands Not Appearing

1. Verify files are in the right location:
   ```bash
   ls ~/.claude/commands/beyond-ralph*.md
   ```

2. Restart Claude Code:
   ```bash
   claude
   ```

3. Check file permissions:
   ```bash
   chmod 644 ~/.claude/commands/beyond-ralph*.md
   ```

### Project Not Resuming

Check `.beyond_ralph_state` exists and has valid JSON:
```bash
cat .beyond_ralph_state
```

### Quota Issues

Manually check quota:
```
/usage
```

Or use the standalone tool (if installed):
```bash
br-quota
```

## Advanced: Installing the Full Package

For additional features (quota checker CLI, hooks), install the Python package:

```bash
pip install /path/to/beyond-ralph
```

This provides:
- `br-quota` - Standalone quota checker
- Python API for programmatic access
- Hooks for Claude Code integration
