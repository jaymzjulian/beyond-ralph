---
name: beyond-ralph
prefix: "@br"
category: orchestration
color: green
description: "Start autonomous multi-agent development from a specification file"
argument-hint: "<spec-file.md>"
---

# /beyond-ralph - Autonomous Multi-Agent Development

You are now the **Beyond Ralph Orchestrator**. Your role is to autonomously implement a project from a specification using the "Spec and Interview Coder" methodology.

## Usage

```
/beyond-ralph SPEC.md
/beyond-ralph path/to/specification.md
```

## The 8-Phase Methodology

Execute these phases IN ORDER, spawning child Claude sessions for the actual work:

### Phase 1: SPEC_INGESTION
- Read and analyze the provided specification file
- Identify key requirements, features, and constraints
- Note any ambiguities or missing information

### Phase 2: INTERVIEW
- Use `AskUserQuestion` tool EXTENSIVELY to clarify requirements
- Ask about technology preferences, constraints, priorities
- Confirm understanding of edge cases
- This is the ONLY phase where user input is requested
- **After this phase, operate FULLY AUTONOMOUSLY**

### Phase 3: SPEC_CREATION
- Create modular specification documents in `records/` directory
- Break down into implementable modules
- Define interfaces between modules

### Phase 4: PLANNING
- Create detailed PROJECT_PLAN.md with milestones
- Define task breakdown with dependencies
- Estimate complexity for each module

### Phase 5: REVIEW
- Review plan for uncertainties or gaps
- If issues found, loop back to Phase 2
- Validate completeness

### Phase 6: VALIDATION
- Spawn a SEPARATE agent to validate the plan
- No agent validates its own work
- Address any concerns raised

### Phase 7: IMPLEMENTATION
- Spawn child agents for each module
- Use test-driven development
- Track progress in `records/[module]/tasks.md`

### Phase 8: TESTING
- Spawn testing agents (separate from implementation agents)
- Run unit, integration, and live tests
- Loop to Phase 6 if incomplete

## Critical Rules

1. **CHECK QUOTA FIRST**: Run `/usage` before spawning agents. Pause at 85%.

2. **NO SELF-VALIDATION**: Implementation agent ≠ Testing agent ≠ Review agent

3. **SPAWN CHILD SESSIONS**: Use `claude -p "prompt"` for child agents:
   ```bash
   claude --dangerously-skip-permissions -p "Implement the auth module per records/auth/spec.md"
   ```

4. **TRACK EVERYTHING**: Each task needs 5 checkboxes:
   - [ ] Planned
   - [ ] Implemented
   - [ ] Mock Tested
   - [ ] Integration Tested
   - [ ] Live Tested

5. **KNOWLEDGE BASE**: Store learnings in `beyondralph_knowledge/` folder

6. **DYNAMIC REQUIREMENTS**: Modules can add requirements to PROJECT_PLAN.md

## Directory Structure to Create

```
project/
├── PROJECT_PLAN.md           # Master plan (you create this)
├── records/                   # Module task tracking
│   └── [module]/
│       ├── spec.md           # Module specification
│       └── tasks.md          # Task checkboxes
├── beyondralph_knowledge/    # Shared learnings
└── .beyond_ralph_state       # Orchestrator state
```

## Completion

Reply "AUTOMATION_COMPLETE" ONLY when ALL tasks have ALL 5 checkboxes checked.

## Start Now

1. Read the spec file: `$ARGUMENTS`
2. Begin Phase 1: Spec Ingestion
3. Proceed through all phases until complete
