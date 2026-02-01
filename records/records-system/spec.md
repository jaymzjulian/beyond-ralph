# Module 8: Records System - Specification

**Module**: records-system
**Location**: `src/beyond_ralph/core/records.py`
**Dependencies**: None (foundational)

## Purpose

Task tracking with 5 checkboxes, per-module organization, and evidence management.

## Requirements

### R1: Task Management
- Create tasks with 5 checkboxes
- Update checkboxes (including UNCHECKING on test failure)
- Track implementation and validation agent UUIDs

### R2: Checkbox States
- Planned: Design documented
- Implemented: Code written
- Mock tested: Unit tests pass
- Integration tested: Integration tests pass
- Live tested: Works in real environment

### R3: Evidence Management
- Store evidence in records/[module]/evidence/[task]/
- Link evidence to tasks
- Evidence validated by orchestrator (not coding agent)

### R4: Completion Tracking
- Check if ALL tasks have 5/5 checkboxes
- 100% required - nothing less acceptable

## Task Format

```markdown
### Task: [Name]

- [ ] Planned - [date]
- [ ] Implemented - [date]
- [ ] Mock tested - [date]
- [ ] Integration tested - [date]
- [ ] Live tested - [date]

**Description**: ...

**Implementation Agent**: [UUID]
**Validation Agent**: [UUID]
**Evidence**: records/[module]/evidence/[task]/
```

## Interface

```python
class RecordsManager:
    async def create_task(self, module: str, task: Task) -> str
    async def update_checkbox(
        self,
        module: str,
        task_id: str,
        checkbox: Checkbox,
        checked: bool,
    ) -> None
    async def get_module_tasks(self, module: str) -> list[Task]
    async def get_incomplete_tasks(self) -> list[Task]
    async def is_complete(self) -> bool
    async def store_evidence(
        self,
        module: str,
        task_id: str,
        evidence: Evidence,
    ) -> Path
```

## Testing Requirements

- Test task CRUD
- Test checkbox updates
- Test checkbox removal (unchecking)
- Test completion detection
- Test evidence storage
