# Beyond Ralph Architecture

## Overview

Beyond Ralph is a **native Claude Code plugin** that provides fully autonomous multi-agent development. This document describes the architecture and integration approach.

## Core Principle: Native Experience

The user interacts with Beyond Ralph **inside Claude Code**, not as an external tool:

```
User opens Claude Code → Types /beyond-ralph start → Watches agents work → Project complete
```

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                       Claude Code Session                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Beyond Ralph Skill                        ││
│  │  /beyond-ralph start | resume | status | pause               ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Orchestrator                             ││
│  │  - Phase management (1-8)                                    ││
│  │  - Quota monitoring                                          ││
│  │  - Agent spawning/coordination                               ││
│  │  - Output streaming                                          ││
│  └─────────────────────────────────────────────────────────────┘│
│         │              │              │              │           │
│         ▼              ▼              ▼              ▼           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │  Spec    │   │Interview │   │ Planning │   │Implement │     │
│  │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│         │              │              │              │           │
│         └──────────────┴──────────────┴──────────────┘           │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Claude Code UI                             ││
│  │  [BEYOND-RALPH] Phase 2: Interview starting...               ││
│  │  [AGENT:interview-001] What database should we use?          ││
│  │  <AskUserQuestion prompt appears>                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Spawning Strategy

### Preferred: Task Tool with Subagents

Claude Code's `Task` tool can spawn subagents that:
- Run within the same session context
- Have their output visible to the parent
- Can be monitored and controlled

```python
# Using Task tool to spawn agents
result = await task_tool.spawn(
    subagent_type="implementation",
    prompt=f"Implement {task.description}",
    description="Implementation agent working"
)
```

**Benefits**:
- Native Claude Code integration
- Automatic output streaming
- Built-in context management
- Familiar user experience (like existing agents)

### Fallback: CLI Subprocess

If Task tool doesn't meet needs, spawn `claude` CLI processes:

```python
# Fallback: CLI-based agent spawning
process = await asyncio.create_subprocess_exec(
    "claude",
    "--dangerously-skip-permissions",
    "--session-id", uuid,
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)

# Stream output with agent prefix
async for line in process.stdout:
    print(f"[AGENT:{agent_id}] {line.decode()}")
```

**Trade-offs**:
- More control over process lifecycle
- More complexity in output handling
- Requires careful stream management
- Need to handle interrupts/signals

## Output Streaming Protocol

All agent output follows this format:

```
[BEYOND-RALPH] {orchestrator messages}
[AGENT:{id}] {agent output lines}
[USER INPUT REQUIRED] {prompt for user}
[ERROR:{id}] {error messages}
[QUOTA] {quota status updates}
```

### Examples

```
[BEYOND-RALPH] Starting project: my-app
[BEYOND-RALPH] Phase 1: Spec Ingestion

[AGENT:spec-a1b2c3] Reading specification file...
[AGENT:spec-a1b2c3] Found 5 major features:
[AGENT:spec-a1b2c3]   1. User authentication
[AGENT:spec-a1b2c3]   2. Dashboard
[AGENT:spec-a1b2c3]   3. API integration
[AGENT:spec-a1b2c3]   4. Notifications
[AGENT:spec-a1b2c3]   5. Admin panel
[AGENT:spec-a1b2c3] Spec ingestion complete.

[BEYOND-RALPH] Phase 2: Interview

[AGENT:interview-d4e5f6] I need to clarify some requirements.
[USER INPUT REQUIRED]
```

## User Interaction Routing

When subagents need user input:

1. Subagent calls `AskUserQuestion`
2. Orchestrator intercepts the call
3. Orchestrator presents question in main session
4. User responds via Claude Code UI
5. Response routed back to waiting subagent
6. Subagent continues

```
Subagent                 Orchestrator              Claude Code UI
   │                          │                          │
   │──AskUserQuestion────────>│                          │
   │                          │──Present question───────>│
   │                          │                          │
   │                          │<───User response─────────│
   │<────Response─────────────│                          │
   │                          │                          │
   │  continues...            │                          │
```

## Phase Management

```
┌─────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐
│ Phase 1 │────>│  Phase 2  │────>│ Phase 3  │────>│ Phase 4  │
│  Spec   │     │ Interview │     │   Spec   │     │  Plan    │
└─────────┘     └───────────┘     │ Creation │     │ Creation │
                     ▲            └──────────┘     └──────────┘
                     │                                  │
                     └───── if uncertainties ───────────┘
                                                        │
                                                        ▼
┌─────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐
│ Phase 8 │<────│  Phase 7  │<────│ Phase 6  │<────│ Phase 5  │
│  Test   │     │Implement  │     │ Validate │     │  Review  │
└─────────┘     └───────────┘     └──────────┘     └──────────┘
     │                                  ▲
     │                                  │
     └───── if tests fail ──────────────┘
```

## Quota Management Integration

```
Before EVERY agent spawn:
  1. Check quota status
  2. If >= 85%: PAUSE
  3. Display [QUOTA] message
  4. Check every 10 minutes
  5. Resume when quota resets
```

Display format:
```
[QUOTA] Session: 45%, Weekly: 72% - OK
[QUOTA] Session: 86%, Weekly: 72% - PAUSING (session limit)
[QUOTA] Waiting for quota reset... checking in 10 minutes
[QUOTA] Quota reset! Resuming operations.
```

## Knowledge Base Integration

All agents read from and write to `beyondralph_knowledge/`:

```
beyondralph_knowledge/
├── design/
│   └── {topic}-{uuid}.md
├── implementation/
│   └── {topic}-{uuid}.md
├── issues/
│   └── {issue}-{uuid}.md
└── resolutions/
    └── {resolution}-{uuid}.md
```

Agents MUST:
1. Check knowledge base before asking orchestrator
2. Write learnings for future agents
3. Include source session UUID
4. Enable follow-up queries

## Record Keeping Integration

Task status tracked in `records/{module}/tasks.md`:

```markdown
### Task: Implement Session Manager
- [x] Planned - 2024-01-15
- [x] Implemented - 2024-01-16
- [x] Mock tested - 2024-01-16
- [ ] Integration tested
- [ ] Live tested

**Implementation Agent**: abc-123
**Validation Agent**: def-456
```

Orchestrator updates checkboxes as phases complete.

## Error Handling

```
[ERROR:agent-id] Description of error
[BEYOND-RALPH] Agent failed, attempting recovery...
[BEYOND-RALPH] Spawning new agent for retry...
```

Or for fatal errors:
```
[ERROR:orchestrator] Critical failure: {description}
[BEYOND-RALPH] Project paused. Resume with /beyond-ralph resume
```

## Autonomous Operation Model

### Interview Phase = Only Approval Gate

```
Phase 1-2: INTERVIEW (User Interaction)
  └── User approves spec and plan
  └── All decisions are made here
  └── User confirms testing approach
  └── User approves dependencies

Phase 3-8: AUTONOMOUS (No User Approval)
  └── Beyond Ralph operates independently
  └── Installs packages without asking
  └── Makes implementation decisions
  └── Only interrupts for:
      - Clarifying questions (returns to interview)
      - Fatal errors
      - Quota limits
```

### Contained Environment Assumption

Beyond Ralph assumes it runs in a **contained environment**:
- Docker container
- Virtual machine
- Dedicated development machine
- Disposable environment

This means:
- ✅ Install any packages freely
- ✅ Modify any files
- ✅ Run any commands
- ✅ Download dependencies
- ✅ Make system changes if needed

The user opts into this by running Beyond Ralph. The interview phase is where they confirm what will be built. After that, it's fully autonomous.

### No Mid-Flight Approval

```
WRONG (interrupts flow):
[AGENT:impl] Need to install pytest-asyncio
[USER INPUT REQUIRED] Install pytest-asyncio? (y/n)

CORRECT (autonomous):
[AGENT:impl] Installing pytest-asyncio...
[AGENT:impl] Running: uv add pytest-asyncio
[AGENT:impl] Installation complete, continuing...
```

### Preferred Tools & Automatic Fallback

Beyond Ralph has **opinions about its tools**. When the user hasn't specified:

| Need | Preferred Tool | Why |
|------|----------------|-----|
| Web testing | Playwright | Modern, cross-browser, well-maintained |
| API testing | httpx + pytest | Async, clean API |
| CLI testing | pexpect | Interactive CLI support |
| Screenshot analysis | Pillow + OpenCV | Powerful, widely supported |
| Package management | uv | Fast, reliable |

**MANDATORY FALLBACK BEHAVIOR**:

When a tool fails, Beyond Ralph MUST:
1. Detect the failure
2. Understand why it failed (parse error, check platform, etc.)
3. Search for alternatives
4. Install and try the alternative
5. Only give up after exhausting reasonable alternatives

```
[AGENT:testing] ERROR: playwright install failed (ARM64 + Wayland not supported)
[AGENT:testing] Analyzing failure...
[AGENT:testing] Searching for ARM64-compatible browser automation...
[AGENT:testing] Found: Selenium + Firefox works on ARM64 Linux
[AGENT:testing] Installing selenium...
[AGENT:testing] Installing geckodriver...
[AGENT:testing] Retrying tests...
[AGENT:testing] Tests passing with Selenium fallback
[KNOWLEDGE] arm64-wayland-browser-testing.md: Use Selenium, not Playwright
```

**Never ask the user what alternative to try. Just find one and use it.**

### safemode Override

If `safemode=true` in config:
- Prompts before dangerous operations
- For users who DON'T have contained environments
- Default is `safemode=false`

## Security Considerations

1. **Contained environment assumed**: User runs in isolated environment
2. **Interview is approval**: Spec approval = blanket approval for implementation
3. **safemode config**: Optional prompts for non-contained environments
4. **Agent isolation**: Agents can't access each other's sessions directly
5. **Knowledge base validation**: Prevent injection via knowledge entries
6. **Quota enforcement**: Prevent runaway resource usage

## Implementation Priorities

1. **First**: Get basic skill registration working
2. **Second**: Implement output streaming (even if basic)
3. **Third**: Add agent spawning (Task tool first, CLI fallback)
4. **Fourth**: Add quota checking
5. **Fifth**: Complete phase management
6. **Sixth**: Polish UI experience
