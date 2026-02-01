# Core Module Tasks

## Overview

The core module contains the orchestrator and session management for Beyond Ralph.

---

### Task: Implement Session Manager

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Create the session manager that spawns and controls Claude Code sessions via CLI.

**Key Requirements**:
- Spawn new claude code sessions with `--dangerously-skip-permissions` flag
- Return UUID of spawned session
- Send follow-up messages to sessions by UUID
- Detect when session completes
- Check for active processes before spawning

**Implementation Agent**: TBD
**Validation Agent**: TBD

---

### Task: Implement Quota Monitor

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Monitor Claude usage quotas and pause operations when nearing limits.

**Key Requirements**:
- Check quota via `claude /usage` command
- Parse session and weekly percentages
- Cache status (5min normal, 10min when limited)
- Trigger pause when >= 85%
- Resume when quota resets

**Implementation Agent**: TBD
**Validation Agent**: TBD

---

### Task: Implement Main Orchestrator

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Main orchestration loop implementing the ralph-loop pattern.

**Key Requirements**:
- Check quota before each agent interaction
- Verify no other process is using target session UUID
- Implement phase transitions (Spec → Interview → Plan → Implement → Test)
- Ask assessment agent if project is complete
- Continue until ALL tasks completed

**Implementation Agent**: TBD
**Validation Agent**: TBD

---

### Task: Implement Knowledge Base Integration

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Integration with beyondralph_knowledge/ for agent knowledge sharing.

**Key Requirements**:
- Write structured knowledge entries
- Track source session UUID
- Read and search knowledge base
- Enable follow-up questions to source sessions

**Implementation Agent**: TBD
**Validation Agent**: TBD
