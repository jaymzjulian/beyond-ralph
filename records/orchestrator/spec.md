# Module 1: Core Orchestrator - Specification

**Module**: orchestrator
**Location**: `src/beyond_ralph/core/orchestrator.py`
**Dependencies**: session, quota, knowledge, records-system

## Purpose

Main control loop implementing ralph-loop persistence, phase management, agent coordination, and context recovery.

## Requirements

### R1: Ralph-Loop Persistence
- Continue until ALL tasks have 5/5 checkboxes
- Use Stop hook for persistence within Claude Code
- Only pause for: quota limits, fatal errors, user interrupt
- Very aggressive - do not stop for minor issues

### R2: Phase Management
- Implement state machine for phases 1-8
- Spawn appropriate agent for each phase
- Handle phase transitions
- Support looping back (Phase 5→2, Phase 8→6)

### R3: Context Management
- MINIMIZE orchestrator context usage
- Delegate ALL work to agents
- On compaction event:
  - Re-read PROJECT_PLAN.md
  - Re-read current module specs
  - Re-read task status
  - Check recent knowledge entries

### R4: Dynamic Plan Updates
- Detect when modules add requirements to PROJECT_PLAN.md
- Schedule work to fulfill inter-module requirements
- Track discrepancies between promised and delivered

### R5: Completion Assessment
- Spawn assessment agent to evaluate project completion
- Comprehensive audit, not just checkbox check
- Review ALL evidence from testing agents

### R6: Agent Coordination
- Spawn up to 7 agents in parallel where appropriate
- Sequential execution where dependencies exist
- Route questions from agents to user via AskUserQuestion
- Validate evidence from testing agents (not coding agents)

## Interface

```python
class Orchestrator:
    async def start(self, spec_path: Path) -> None
    async def resume(self, project_id: str | None = None) -> None
    async def pause(self) -> None
    async def status(self) -> ProjectStatus
    async def on_compaction(self) -> None
```

## Testing Requirements

- Unit test each method
- Integration test with mock agents
- Test compaction recovery
- Test phase transitions
- Test dynamic plan updates
