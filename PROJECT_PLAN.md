# Beyond Ralph - Complete Project Plan

## Project Vision

Create a fully autonomous multi-agent development system for Claude Code that implements the Spec and Interview Coder methodology, running for DAYS if needed to deliver complete projects.

---

## SPEC REQUIREMENTS CHECKLIST

Every item from SPEC.md must be implemented. Use this checklist:

### Agentic Model (SPEC lines 12-32)
- [ ] Start new Claude Code sessions via CLI, return UUID
- [ ] Send requests to sessions by UUID
- [ ] Return final human-readable message (the RESULT, not the work being done)
- [ ] Follow up conversations for more information
- [ ] Loop until work is done
- [ ] Default: --dangerously-skip-permissions
- [ ] Config switch: `safemode` to toggle permissions
- [ ] Use sessions (not just agents) for separation and parallel development
- [ ] Don't over-reuse agents (preserve context windows)
- [ ] Check no other Claude process using same UUID before interaction
- [ ] Main orchestrator implements ralph-loop persistence
- [ ] Child agents do NOT have ralph-loop (orchestrator's responsibility)
- [ ] Smart completion check: ask agent to assess if project complete

### Agent Knowledge (SPEC lines 34-37)
- [ ] beyondralph_knowledge/ folder for shared knowledge
- [ ] Structured information format
- [ ] Include UUID of session that created each knowledge entry
- [ ] Enable follow-up questions to source sessions
- [ ] Agents check knowledge base BEFORE asking orchestrator
- [ ] OK for agents to return with questions (caller can follow up)

### Basic Principles (SPEC lines 39-42)
- [ ] Git used judiciously (proper commits, branching)
- [ ] ALL agents keep on-disk TODOs updated
- [ ] ALL agents keep Project Plans updated
- [ ] Use TodoWrite tool
- [ ] Use Memory capabilities
- [ ] Use project planning features
- [ ] Search web for additional skills/tools as needed

### Phases - Each in Dedicated Agent (SPEC lines 44-57)
- [ ] Phase 1: Ingest full specification from user
- [ ] Phase 2: Interview user with AskUserQuestion (be in-depth, persistent, insist on info)
- [ ] Phase 3: Create complete spec, split into independent modules
- [ ] Phase 4: Create project plan with milestones and testing plans
- [ ] Phase 5: Examine all, interview again if uncertainties, loop phases 2-3-4
- [ ] Phase 6: Separate agent validates project plan
- [ ] Phase 7: Implement (TDD approach)
- [ ] Phase 8: Test implementation, return to phase 6 if incomplete

### Implementation Multi-Agent (SPEC lines 60-69)
- [ ] Orchestrator ONLY orchestrates during implementation
- [ ] Test-driven development
- [ ] Coding agent tests its own work during development
- [ ] SECOND agent (didn't code it) validates implementation
- [ ] Live testing validated by agent that didn't code
- [ ] Validation agent provides EVIDENCE
- [ ] Orchestrator validates evidence (NOT the coding agent)
- [ ] Expect DAYS of running for large projects

### Record Keeping (SPEC lines 71-82)
- [ ] Strong records and task lists (formal project management)
- [ ] 5 checkboxes per task: Planned, Implemented, Mock tested, Integration tested, Live tested
- [ ] ALL 5 must be checked for 100% completion
- [ ] Testing agent CAN and SHOULD remove checkboxes if tests fail
- [ ] Each module has its own specs
- [ ] records/[modulename]/ folder structure

### User Requirements (SPEC lines 84-101)
- [ ] Way to autonomously test the code
- [ ] API apps: access working endpoints non-destructively
- [ ] API apps: develop against mock APIs FIRST
- [ ] API apps: then debug against real APIs
- [ ] Ingest API documentation as part of development
- [ ] Ingest structured API definitions (OpenAPI, etc.)
- [ ] GUI apps: run and take screenshots to analyze
- [ ] GUI apps: prefer PNG/video output if available
- [ ] GUI apps: use Xvnc/RDP for functional GUIs
- [ ] Other resources: user must provide up front
- [ ] Check everything needed is available (during interview)
- [ ] User can allow autonomous system installation

### Documentation (SPEC lines 103-105)
- [ ] User documentation delivered
- [ ] Developer documentation delivered
- [ ] Evidence of how process worked

### Claude Quotas (SPEC lines 107-112)
- [ ] Detect when at 85% limit (session OR weekly)
- [ ] PAUSE (not stop) new agent requests when limit hit
- [ ] Check quota every 10 minutes when paused
- [ ] Check quota BEFORE each agent interaction
- [ ] Cache quota status in file (everyone can read)
- [ ] Python script to check "claude /usage"
- [ ] Remain autonomous, just PAUSE

### Implementation Details (SPEC lines 114-117)
- [ ] Use Claude Code plugins
- [ ] Use stop hooks for persistence
- [ ] Run WITHIN Claude Code (not external bash loop)
- [ ] Create skills for workflow
- [ ] Create agents for phases
- [ ] Agent management as a skill

### User Additions (from conversation)
- [ ] Native Claude Code experience (user runs /beyond-ralph in Claude Code)
- [ ] Stream ALL subagent output to main session with [AGENT:id] prefixes
- [ ] Testing skills for various app types (API, web, CLI, desktop, games)
- [ ] Research agent to discover and install testing tools
- [ ] Autonomous tool installation (no approval after interview)
- [ ] Preferred tools philosophy (Beyond Ralph has opinions)
- [ ] MANDATORY fallback: when tools fail, search for alternatives
- [ ] Use passwordless sudo liberally if available
- [ ] THREE agents per implementation: Coding, Testing, Review
- [ ] Code Review Agent is mandatory (linting, security, best practices)
- [ ] Coding Agent MUST action ALL review items (no dismissals)

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation
**Goal**: Core infrastructure

#### Milestone 1.1: Project Setup ✓
- [x] Create project structure
- [x] Set up pyproject.toml with uv
- [x] Create CLAUDE.md guidelines
- [x] Set up records system (per-module folders)
- [x] Initialize knowledge base

#### Milestone 1.2: Claude Code Plugin Structure
- [ ] Create .claude-plugin/plugin.json manifest
- [ ] Set up skills/ directory with SKILL.md files
- [ ] Set up agents/ directory for subagent definitions
- [ ] Set up hooks/hooks.json for event handlers
- [ ] Test plugin loading with --plugin-dir

#### Milestone 1.3: Session Management
- [ ] Implement session spawning via CLI (return UUID)
- [ ] Implement sending requests to sessions by UUID
- [ ] Implement getting final result (not work, the RESULT)
- [ ] Implement follow-up messaging
- [ ] Implement UUID locking (check no other process using it)
- [ ] Implement session cleanup

#### Milestone 1.4: Quota Management
- [ ] Create Python script to check "claude /usage"
- [ ] Parse session percentage
- [ ] Parse weekly percentage
- [ ] Implement file-based caching
- [ ] Implement 85% threshold detection
- [ ] Implement PAUSE behavior (not stop)
- [ ] Implement 10-minute check interval when paused
- [ ] Implement pre-interaction quota check

### Phase 2: Agent Framework
**Goal**: Define and implement all agent types

#### Milestone 2.1: Base Agent Infrastructure
- [ ] Design agent interface (subagent markdown format)
- [ ] Implement base agent configuration
- [ ] Implement knowledge base read/write
- [ ] Implement evidence generation
- [ ] Implement question-return capability

#### Milestone 2.2: Phase Agents
- [ ] Spec Agent (Phase 1): Ingest specification
- [ ] Interview Agent (Phase 2): Deep user interview with AskUserQuestion
- [ ] Spec Creation Agent (Phase 3): Create modular spec
- [ ] Planning Agent (Phase 4): Create project plan with milestones
- [ ] Review Agent (Phase 5): Examine and identify uncertainties
- [ ] Validation Agent (Phase 6): Validate project plan
- [ ] Implementation Agent (Phase 7): TDD implementation
- [ ] Testing Agent (Phase 8): Test and validate

#### Milestone 2.3: Trust Model Agents
- [ ] Coding Agent: Implements, fixes review items
- [ ] Testing Agent: Validates, provides evidence
- [ ] Code Review Agent: Linting, security, best practices
- [ ] Evidence validation in orchestrator

### Phase 3: Orchestrator
**Goal**: Main control loop and phase management

#### Milestone 3.1: Ralph-Loop Implementation
- [ ] Implement persistent loop (stop hook)
- [ ] Implement "is work to do?" check
- [ ] Implement "assess if project complete" agent call
- [ ] Implement task list parsing
- [ ] Implement phase transitions
- [ ] Implement return-to-phase-6 logic for failures

#### Milestone 3.2: Agent Coordination
- [ ] Implement parallel agent spawning (where appropriate)
- [ ] Implement sequential agent chaining
- [ ] Implement agent result handling
- [ ] Implement question routing back to user
- [ ] Implement quota-aware pausing

#### Milestone 3.3: Trust Validation
- [ ] Implement dual-agent validation (coder + tester)
- [ ] Implement triple-agent validation (coder + tester + reviewer)
- [ ] Implement evidence verification
- [ ] Implement checkbox management
- [ ] Implement checkbox removal on test failure

### Phase 4: Claude Code Integration
**Goal**: Native Claude Code experience

#### Milestone 4.1: Skills
- [ ] /beyond-ralph:start skill
- [ ] /beyond-ralph:resume skill
- [ ] /beyond-ralph:status skill
- [ ] /beyond-ralph:pause skill
- [ ] Agent management skill
- [ ] Skill registration in pyproject.toml

#### Milestone 4.2: Subagent Output Streaming
- [ ] Capture output from subagents
- [ ] Format with [AGENT:xyz] prefixes
- [ ] Stream to main Claude Code session
- [ ] Show phase transitions [BEYOND-RALPH]
- [ ] Handle multi-line output

#### Milestone 4.3: User Interaction
- [ ] Route AskUserQuestion from subagents to main session
- [ ] Capture user responses
- [ ] Handle interrupts and manual pauses
- [ ] Progress indicators

#### Milestone 4.4: Hooks
- [ ] Stop hook for ralph-loop persistence
- [ ] PreToolUse hook for quota checking
- [ ] SubagentStop hook for result handling
- [ ] Hook registration

### Phase 5: Testing Capabilities
**Goal**: Bundled testing tools AND autonomous discovery

#### Milestone 5.1: Bundled Testing Skills
- [ ] API/Backend testing (httpx, pytest, responses)
- [ ] Web UI testing (playwright)
- [ ] CLI testing (pexpect, subprocess)
- [ ] Desktop GUI testing (pillow, pyautogui)
- [ ] Screenshot/video analysis (opencv-python, pillow)
- [ ] Mock API server for development

#### Milestone 5.2: Research Agent
- [ ] Web search for testing frameworks
- [ ] GitHub API for repo evaluation
- [ ] Platform compatibility checking
- [ ] Recommendation logic
- [ ] Autonomous installation (no approval after interview)
- [ ] MANDATORY fallback when tools fail
- [ ] Preferred tools selection when user doesn't specify
- [ ] Knowledge base storage of discoveries

#### Milestone 5.3: System Capabilities
- [ ] Passwordless sudo detection
- [ ] Package manager detection
- [ ] Tool inventory
- [ ] System package installation
- [ ] Browser installation (Chrome, Firefox)
- [ ] Compiler installation (gcc, clang)

### Phase 6: Code Review Agent
**Goal**: Mandatory code quality enforcement

#### Milestone 6.1: Linting Integration
- [ ] Python: ruff, mypy
- [ ] JavaScript/TypeScript: eslint, tsc
- [ ] Go: golint, go vet, staticcheck
- [ ] Rust: cargo clippy
- [ ] Auto-detect language and run appropriate linter

#### Milestone 6.2: Security Scanning
- [ ] Semgrep with OWASP rulesets
- [ ] Bandit for Python
- [ ] detect-secrets for hardcoded secrets
- [ ] Safety for dependency vulnerabilities
- [ ] npm audit, cargo audit, etc.

#### Milestone 6.3: Best Practices
- [ ] Cyclomatic complexity (radon)
- [ ] Dead code detection (vulture)
- [ ] DRY violation detection
- [ ] Error handling patterns
- [ ] Input validation checks

#### Milestone 6.4: Review-Fix Loop
- [ ] Pass findings to Coding Agent
- [ ] Coding Agent MUST fix ALL items
- [ ] Re-review after fixes
- [ ] Loop until 0 must-fix items

### Phase 7: Self-Testing
**Goal**: Verify Beyond Ralph works

#### Milestone 7.1: Unit Tests
- [ ] Session manager tests
- [ ] Quota checker tests
- [ ] Agent framework tests
- [ ] Knowledge base tests
- [ ] Records system tests
- [ ] 80%+ coverage

#### Milestone 7.2: Integration Tests
- [ ] Plugin loading tests
- [ ] Skill invocation tests
- [ ] Subagent spawning tests
- [ ] Hook execution tests

#### Milestone 7.3: End-to-End Tests
- [ ] Complete project flow test
- [ ] Phase transition tests
- [ ] Quota pause/resume tests
- [ ] Multi-agent coordination tests

### Phase 8: Documentation
**Goal**: Complete user and developer docs

#### Milestone 8.1: User Documentation
- [ ] Installation guide
- [ ] Quick start guide
- [ ] Configuration options
- [ ] Testing guide (app types)
- [ ] Troubleshooting

#### Milestone 8.2: Developer Documentation
- [ ] Architecture overview
- [ ] Agent development guide
- [ ] Plugin structure
- [ ] Contributing guide

#### Milestone 8.3: Process Evidence
- [ ] Document how development went
- [ ] Record decisions made
- [ ] Store evidence of testing

### Phase 9: Self-Containment Verification
**Goal**: Ensure project ships everything

#### Milestone 9.1: Dependency Audit
- [ ] All deps in pyproject.toml
- [ ] No external tool references (SuperClaude, ralph-loop, etc.)
- [ ] Test clean install

#### Milestone 9.2: Packaging
- [ ] Create installable package
- [ ] Test uv pip install
- [ ] Create release process

---

## Timeline

Large project expected to run over multiple sessions (potentially DAYS).

```
Phase 1 (Foundation)
    └── Phase 2 (Agent Framework)
        └── Phase 3 (Orchestrator)
            └── Phase 4 (Integration)
                └── Phase 5 (Testing)
                    └── Phase 6 (Code Review)
                        └── Phase 7 (Self-Testing)
                            └── Phase 8 (Documentation)
                                └── Phase 9 (Verification)
```

## Success Criteria

1. **Autonomous Operation**: Runs for DAYS without human intervention (except interviews)
2. **Quota Awareness**: PAUSES at 85% (doesn't stop)
3. **Three-Agent Trust**: Coding + Testing + Review for every implementation
4. **5/5 Checkboxes**: All tasks have all 5 checkboxes checked
5. **Self-Contained**: Installs and runs on clean system
6. **Documentation**: Complete user and developer docs with process evidence

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Claude CLI interface changes | Abstract CLI interaction layer |
| Quota detection unreliable | Conservative pause thresholds |
| Session spawning fails | Retry logic with exponential backoff |
| Knowledge base conflicts | UUID-based locking mechanism |
| Long-running tests fail | Checkpoint/resume capability |
| Subagents can't spawn subagents | Orchestrator coordinates all agents |

---

*This plan covers EVERY item from SPEC.md plus user additions. Nothing is thrown away.*
