# Records

This directory contains per-module task tracking for the Beyond Ralph project.

## Structure

```
records/
├── README.md           # This file
├── core/               # Core orchestration module
│   └── tasks.md
├── agents/             # Agent definitions
│   └── tasks.md
├── skills/             # Claude Code skills
│   └── tasks.md
├── hooks/              # Claude Code hooks
│   └── tasks.md
└── utils/              # Utilities
    └── tasks.md
```

## Task Checkbox Requirements

Every task MUST have all five checkboxes checked before it is considered complete:

- [ ] **Planned** - Design documented, approach decided
- [ ] **Implemented** - Code written
- [ ] **Mock tested** - Unit tests pass with mocks
- [ ] **Integration tested** - Integration tests pass
- [ ] **Live tested** - Works in real Claude Code environment

## Task Format

```markdown
### Task: [Task Name]
- [ ] Planned - [date]
- [ ] Implemented - [date]
- [ ] Mock tested - [date]
- [ ] Integration tested - [date]
- [ ] Live tested - [date]

**Description**: [What this task accomplishes]

**Implementation Agent**: [UUID]
**Validation Agent**: [UUID]
**Evidence**: records/[module]/evidence/[task-slug]/
```

## Evidence Requirements

Each completed task must have:
1. Test output logs
2. Coverage reports
3. Screenshots (if applicable)
4. Validator agent confirmation
