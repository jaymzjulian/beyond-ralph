# Quick Start

## 1. Install

```bash
cd ~/your-project
mkdir -p .claude/commands .claude/hooks

cp /path/to/beyond-ralph/.claude/commands/beyond-ralph*.md .claude/commands/
cp /path/to/beyond-ralph/.claude/hooks/stop_hook.py .claude/hooks/
```

## 2. Write a Spec

Create a `SPEC.md` in your project describing what you want built:

```markdown
# My Project

## Overview
A CLI tool that converts CSV files to JSON.

## Requirements
- Accept input file path as argument
- Support multiple CSV dialects (comma, tab, pipe)
- Output valid JSON to stdout or file
- Handle malformed input gracefully with clear error messages
- Support streaming for large files (>1GB)
```

The more detailed the spec, the better the result. Include requirements, constraints, edge cases, and technology preferences.

## 3. Run

```bash
claude
```

Then type:

```
/beyond-ralph SPEC.md
```

## 4. Answer Interview Questions

Beyond Ralph will ask you clarifying questions about your requirements. Answer them — this is the **only time** it needs your input. After the interview, everything is fully autonomous.

## 5. Watch It Work

Beyond Ralph will:
- Create a project plan
- Spawn agents to implement each task
- Test everything (unit, integration, and live)
- Run an adversarial audit to verify nothing was faked
- Keep going until all 7 checkboxes pass on every task

If it hits a quota limit, it pauses automatically. Resume with:

```
/beyond-ralph-resume
```

## That's It

Check progress anytime with `/beyond-ralph-status`. The `records/` directory has detailed task tracking. The `beyondralph_knowledge/` directory has decisions and learnings from the build process.
