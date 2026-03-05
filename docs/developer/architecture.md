# Beyond Ralph - Architecture Overview

## System Architecture

Beyond Ralph is a multi-agent orchestration system that runs within Claude Code. It implements the "Spec and Interview Coder" methodology through dedicated agents for each development phase.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Claude Code                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Beyond Ralph                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │    │
│  │  │ Orchestrator│  │ Knowledge   │  │   Records   │      │    │
│  │  │             │  │    Base     │  │   Manager   │      │    │
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘      │    │
│  │         │                                                │    │
│  │  ┌──────┴──────────────────────────────────┐            │    │
│  │  │              Session Manager             │            │    │
│  │  └──────┬──────────────┬──────────────┬────┘            │    │
│  │         │              │              │                  │    │
│  │  ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐         │    │
│  │  │ Coding Agent│ │Test Agent │ │Review Agent │         │    │
│  │  └─────────────┘ └───────────┘ └─────────────┘         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### Orchestrator

**Location**: `src/beyond_ralph/core/orchestrator.py`

The central coordinator that manages:
- Phase transitions (10 phases (including 8.5 and 9))
- Agent spawning and coordination
- State persistence and recovery
- Quota management
- Error handling and recovery

**Key Classes**:
- `Orchestrator`: Main control loop
- `Phase`: Enum of development phases
- `PhaseResult`: Result of phase execution
- `OrchestratorState`: Running, paused, stopped

### Session Manager

**Location**: `src/beyond_ralph/core/session_manager.py`

Manages Claude Code sessions:
- Spawns CLI sessions with pexpect
- Sends commands to sessions by UUID
- Tracks session state and output
- Implements locking (UUID-based)
- Supports both CLI and Task tool modes

**Key Classes**:
- `SessionManager`: Main session coordinator
- `SessionInfo`: Session metadata
- `SessionStatus`: Running, complete, failed
- `SessionOutput`: Captured output with prefixes

### Knowledge Base

**Location**: `src/beyond_ralph/core/knowledge.py`

Shared knowledge storage:
- YAML frontmatter format
- Session UUID tracking
- Category-based organization
- Full-text search
- Recent entries listing

**Key Classes**:
- `KnowledgeBase`: Storage manager
- `KnowledgeEntry`: Individual entry with metadata

### Records Manager

**Location**: `src/beyond_ralph/core/records.py`

Task tracking system:
- 7-checkbox tracking per task
- Module-based organization
- Markdown format for human readability
- Task completion detection

**Key Classes**:
- `RecordsManager`: Records coordinator
- `Task`: Task with checkboxes
- `Checkbox`: The 7 checkbox types

### Quota Manager

**Location**: `src/beyond_ralph/core/quota_manager.py`

Claude usage monitoring:
- Session and weekly quota tracking
- 85% threshold detection
- Pause/resume behavior
- File-based caching
- "Never fake results" principle

**Key Classes**:
- `QuotaManager`: Quota coordinator
- `QuotaStatus`: Current quota state

## Agent Framework

### Base Agent

**Location**: `src/beyond_ralph/agents/base.py`

Base classes for all agents:
- `AgentModel`: Agent configuration
- `AgentTask`: Task description
- `AgentResult`: Execution result with evidence

### Phase Agents

**Location**: `src/beyond_ralph/agents/phase_agents.py`

One agent per development phase:

| Agent | Phase | Purpose |
|-------|-------|---------|
| `SpecAgent` | 1 | Ingest specification |
| `InterviewAgent` | 2 | User interview |
| `SpecCreationAgent` | 3 | Create modular spec |
| `PlanningAgent` | 4 | Project planning |
| `UncertaintyReviewAgent` | 5 | Review for uncertainties |
| `ValidationAgent` | 6 | Validate plan |
| `ImplementationAgent` | 7 | TDD implementation |
| `TestingValidationAgent` | 8 | Final testing |

### Trust Model Agents

**Location**: `src/beyond_ralph/agents/review_agent.py`

Three-agent validation:
- `CodeReviewAgent`: Linting, security, best practices
- `SpecComplianceAgent`: Verify implementation matches spec
- `TrustModelAgent`: Base for trust-based validation

### Research Agent

**Location**: `src/beyond_ralph/agents/research_agent.py`

Autonomous tool discovery:
- Web search for testing frameworks
- GitHub API for evaluation
- Platform compatibility checking
- Knowledge base integration

## Data Flow

### Phase Execution Flow

```
1. Orchestrator starts phase
2. Phase handler spawns agent(s)
3. Agent executes task
4. Agent returns result with evidence
5. Orchestrator validates evidence
6. Orchestrator updates records
7. Orchestrator transitions to next phase
```

### Knowledge Flow

```
Agent discovers information
        │
        ▼
Writes to knowledge base
        │
        ▼
Other agents read knowledge
        │
        ▼
Orchestrator uses for recovery
```

### Trust Validation Flow

```
Coding Agent writes code
        │
        ▼
Testing Agent validates
        │
        ▼
Review Agent checks quality
        │
        ▼
Coding Agent fixes issues
        │
        ▼ (repeat until approved)
Orchestrator marks complete
```

## State Management

### Persistent State

```json
// .beyond_ralph_state
{
  "project_id": "br-abc12345",
  "phase": "implementation",
  "spec_path": "/path/to/SPEC.md"
}
```

### Session State

```
.beyond_ralph_sessions/
├── session-uuid-1/
│   ├── output.log
│   └── result.json
└── session-uuid-2/
    ├── output.log
    └── result.json
```

### Quota Cache

```json
// .beyond_ralph_quota
{
  "session_percent": 45,
  "weekly_percent": 23,
  "is_limited": false,
  "timestamp": "2024-01-15T10:30:00"
}
```

## Error Handling

### Phase Errors

- Logged to orchestrator
- Added to error list
- After 3 errors, phase fails
- Can loop back to earlier phase

### Agent Errors

- Returned in `AgentResult.errors`
- Logged to knowledge base
- Orchestrator decides recovery

### Quota Errors

- Triggers pause state
- 10-minute check interval
- Auto-resume when available

## Extension Points

### Adding a New Agent

1. Create agent class in `agents/`
2. Extend appropriate base class
3. Implement `execute()` method
4. Register in phase handler if needed

### Adding a New Phase

1. Add to `Phase` enum
2. Create phase handler method
3. Update `_phase_order` list
4. Create corresponding agent

### Adding Testing Capability

1. Add to `TestingSkills` class
2. Implement test method
3. Add evidence generation
4. Update documentation

## Security Considerations

### Safe Mode

When enabled:
- All operations require permission
- File writes are confirmed
- External calls are approved

### Never Fake Results

Core principle enforced by:
- `is_unknown` field in QuotaStatus
- Explicit error returns
- Evidence requirements
- Validation agents

### Session Isolation

- UUID-based locking
- Separate contexts per session
- No session data sharing

## Performance

### Parallel Agent Limit

Claude Code limits to 7 concurrent agents. Beyond Ralph respects this.

### Context Management

- Orchestrator stays lean
- Delegates to agents aggressively
- Compaction recovery protocol

### Quota Efficiency

- Pre-spawn checks
- Cached quota status
- Pause before limit hit

## File Structure

```
src/beyond_ralph/
├── __init__.py
├── cli.py                   # CLI entry points
├── agents/
│   ├── __init__.py
│   ├── base.py              # Base classes
│   ├── phase_agents.py      # Phase-specific agents
│   ├── research_agent.py    # Tool discovery
│   └── review_agent.py      # Code review
├── core/
│   ├── __init__.py
│   ├── orchestrator.py      # Main control
│   ├── session_manager.py   # Session handling
│   ├── knowledge.py         # Knowledge base
│   ├── records.py           # Task records
│   ├── quota_manager.py     # Quota tracking
│   ├── notifications.py     # User notifications
│   └── principles.py        # Core principles
├── hooks/
│   ├── __init__.py
│   ├── stop_handler.py      # Stop hook
│   └── quota_check.py       # Quota hook
├── skills/
│   └── __init__.py          # Skill registration
├── testing/
│   ├── __init__.py
│   └── skills.py            # Testing capabilities
└── utils/
    ├── __init__.py
    ├── quota_checker.py     # Quota CLI parser
    └── system.py            # System capabilities
```

## Next Steps

- [Agent Development Guide](agent-development.md)
- [Plugin Structure](plugin-structure.md)
- [Contributing Guide](contributing.md)
