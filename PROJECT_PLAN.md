# Beyond Ralph - Project Plan

## Project Vision

Create a fully autonomous multi-agent development system for Claude Code that implements the Spec and Interview Coder methodology.

## Phases

### Phase 1: Foundation (Current)
**Goal**: Core infrastructure and session management

#### Milestone 1.1: Project Setup ✓
- [x] Create project structure
- [x] Set up pyproject.toml with uv
- [x] Create CLAUDE.md guidelines
- [x] Set up records system
- [x] Initialize knowledge base

#### Milestone 1.2: Session Management
- [ ] Implement session spawning via CLI
- [ ] Implement session communication (send/receive)
- [ ] Implement session status monitoring
- [ ] Implement UUID-based session locking

#### Milestone 1.3: Quota Management
- [ ] Implement quota checking script
- [ ] Parse `claude /usage` output
- [ ] Implement caching mechanism
- [ ] Implement pause/resume logic

### Phase 2: Agent Framework
**Goal**: Define and implement all agent types

#### Milestone 2.1: Base Agent
- [ ] Design agent interface
- [ ] Implement base agent class
- [ ] Implement knowledge base integration
- [ ] Implement evidence generation

#### Milestone 2.2: Phase Agents
- [ ] Implement Spec Agent (Phase 1)
- [ ] Implement Interview Agent (Phase 2)
- [ ] Implement Planning Agent (Phases 3-4)
- [ ] Implement Validation Agent (Phase 6)
- [ ] Implement Implementation Agent (Phase 7)
- [ ] Implement Testing Agent (Phase 8)

### Phase 3: Orchestrator
**Goal**: Main control loop and phase management

#### Milestone 3.1: Core Orchestrator
- [ ] Implement phase state machine
- [ ] Implement agent spawning logic
- [ ] Implement quota-aware pausing
- [ ] Implement completion assessment

#### Milestone 3.2: Trust Validation
- [ ] Implement dual-agent validation
- [ ] Implement evidence verification
- [ ] Implement checkbox management

### Phase 4: Claude Code Integration (CRITICAL - USER EXPERIENCE)
**Goal**: Native Claude Code experience with streaming subagent output

#### Milestone 4.0: Research Claude Code Internals
- [ ] Investigate Task tool capabilities for subagent spawning
- [ ] Research how native agents stream output to UI
- [ ] Determine best approach (Task tool vs CLI subprocess)
- [ ] Document findings in knowledge base

#### Milestone 4.1: Skills
- [ ] Create beyond-ralph skill with `/beyond-ralph` commands
- [ ] Implement `start --spec` for new projects
- [ ] Implement `resume` for continuing work
- [ ] Implement `status` for progress display
- [ ] Implement `pause` for manual pause
- [ ] Skill registration in pyproject.toml entry points

#### Milestone 4.2: Subagent Output Streaming
- [ ] Implement output capture from subagents
- [ ] Format output with agent identifiers `[AGENT:xyz]`
- [ ] Stream to main Claude Code session UI
- [ ] Handle multi-line output properly
- [ ] Show phase transitions clearly `[BEYOND-RALPH]`

#### Milestone 4.3: User Interaction Integration
- [ ] Route AskUserQuestion from subagents to main session
- [ ] Capture user responses and return to subagent
- [ ] Handle interrupts and manual pauses
- [ ] Progress indicators and status updates

#### Milestone 4.4: Hooks
- [ ] Implement stop hooks for ralph-loop persistence
- [ ] Implement pre-operation quota hooks
- [ ] Implement progress hooks for streaming
- [ ] Hook registration in pyproject.toml entry points

### Phase 5: Testing Skills & Capabilities
**Goal**: Bundled testing tools AND autonomous discovery

#### Milestone 5.1: Bundled Testing Skills
- [ ] API/Backend testing (httpx, pytest, responses)
- [ ] Web UI testing (playwright)
- [ ] CLI testing (pexpect, subprocess)
- [ ] Desktop GUI testing (pillow, pyautogui)
- [ ] Screenshot/video analysis (opencv-python, pillow)
- [ ] Mock API server for development testing

#### Milestone 5.2: Research Agent for Tool Discovery
- [ ] Web search integration (find testing frameworks)
- [ ] GitHub API integration (check stars, maintenance)
- [ ] Documentation fetching and parsing
- [ ] Platform compatibility checking
- [ ] Alternative comparison logic
- [ ] Recommendation presentation to user
- [ ] Autonomous installation (with user approval)
- [ ] Knowledge base storage of discoveries

#### Milestone 5.3: Self-Testing
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests for each agent type
- [ ] End-to-end test with sample project

### Phase 6: Documentation
**Goal**: Complete docs for users and developers

#### Milestone 6.1: Documentation
- [ ] User documentation
- [ ] Developer documentation
- [ ] API reference
- [ ] Example projects
- [ ] Testing guide (how to test different app types)

### Phase 6: Self-Containment Verification
**Goal**: Ensure project ships everything it needs

#### Milestone 6.1: Dependency Audit
- [ ] Verify all deps in pyproject.toml
- [ ] Remove external tool references
- [ ] Test clean install

#### Milestone 6.2: Packaging
- [ ] Create installable package
- [ ] Test pip install
- [ ] Create release process

## Timeline

This is a large project expected to run over multiple sessions. Key dependencies:

```
Phase 1 (Foundation)
    └── Phase 2 (Agents)
        └── Phase 3 (Orchestrator)
            └── Phase 4 (Integration)
                └── Phase 5 (Testing)
                    └── Phase 6 (Verification)
```

## Success Criteria

1. **Autonomous Operation**: Can run for extended periods without human intervention
2. **Quota Awareness**: Properly pauses when nearing limits
3. **Trust Model**: Every implementation validated by separate agent
4. **Record Keeping**: All tasks have 5/5 checkboxes
5. **Self-Contained**: Installs and runs on clean system
6. **Documentation**: Complete user and developer docs

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Claude CLI interface changes | Abstract CLI interaction layer |
| Quota detection unreliable | Conservative pause thresholds |
| Session spawning fails | Retry logic with exponential backoff |
| Knowledge base conflicts | UUID-based locking mechanism |
| Long-running tests fail | Checkpoint/resume capability |

## Notes

- Iterate on project plan as implementation progresses
- Each phase requires validation before proceeding
- Document all design decisions in knowledge base
- Commit frequently with descriptive messages
