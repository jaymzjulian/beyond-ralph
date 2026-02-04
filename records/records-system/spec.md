# Module 4: Records System - Specification

> Task Tracking: 6-checkbox system for tracking implementation status across modules.

---

## Overview

The Records System module provides formal project management through structured task tracking. Every task has 6 checkboxes that MUST all be checked for the project to be complete. Agents can update checkboxes, and testing/compliance agents can REMOVE checkboxes when failures are found.

**Key Principle**: Anything less than 6/6 checkboxes is unacceptable. Testing agents CAN and SHOULD remove checkboxes.

---

## Components

### 4.1 Records Manager (`records.py`)

**Location**: `src/beyond_ralph/core/records.py`

**Storage Location**: `records/[module_name]/`

---

## Data Format

### Directory Structure
```
records/
├── README.md
├── core/
│   ├── spec.md              # Module specification
│   ├── tasks.md             # Task tracking
│   └── evidence/            # Test evidence
│       └── [task-uuid]/
│           ├── test-output.txt
│           ├── coverage.html
│           └── screenshots/
├── agents/
│   ├── spec.md
│   ├── tasks.md
│   └── evidence/
├── knowledge/
│   └── ...
└── [other-modules]/
```

### Task File Format
```markdown
# [Module Name] Tasks

## Task: [Task Name]
**Task ID**: [uuid]
**Description**: [Brief description]

### Status
- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant

### Evidence
- Test output: records/[module]/evidence/[task-uuid]/test-output.txt
- Coverage: records/[module]/evidence/[task-uuid]/coverage.html

### History
- 2024-02-01 10:00: Planned by planning-agent-abc123
- 2024-02-01 14:00: Implemented by impl-agent-xyz789
- 2024-02-01 15:00: Implemented REMOVED by testing-agent-def456 (tests failed)
- 2024-02-01 16:00: Implemented by impl-agent-xyz789 (fixed)
- 2024-02-01 17:00: Mock tested by testing-agent-def456

---

## Task: [Another Task]
...
```

---

## Interfaces

```python
@dataclass
class TaskRecord:
    """A tracked task with 6 checkboxes."""
    task_id: str
    name: str
    module: str
    description: str
    planned: bool = False
    implemented: bool = False
    mock_tested: bool = False
    integration_tested: bool = False
    live_tested: bool = False
    spec_compliant: bool = False
    evidence_path: Optional[str] = None
    history: list[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Check if all 6 checkboxes are checked."""
        return all([
            self.planned,
            self.implemented,
            self.mock_tested,
            self.integration_tested,
            self.live_tested,
            self.spec_compliant
        ])

    def completion_count(self) -> tuple[int, int]:
        """Return (checked, total) checkbox count."""
        checked = sum([
            self.planned,
            self.implemented,
            self.mock_tested,
            self.integration_tested,
            self.live_tested,
            self.spec_compliant
        ])
        return (checked, 6)

class RecordsManager:
    """Manager for task records across all modules."""

    def __init__(self, base_path: str = "records/"):
        """Initialize records manager.

        Args:
            base_path: Path to records directory.
        """

    def get_task(self, module: str, task_name: str) -> Optional[TaskRecord]:
        """Get a specific task record.

        Args:
            module: Module name (e.g., "core", "agents")
            task_name: Task name

        Returns:
            TaskRecord if found, None otherwise.
        """

    def get_task_by_id(self, task_id: str) -> Optional[TaskRecord]:
        """Get task by its UUID."""

    def add_task(self, module: str, task: TaskRecord) -> str:
        """Add a new task to a module.

        Args:
            module: Module to add task to.
            task: Task record to add.

        Returns:
            Task ID.
        """

    def update_checkbox(
        self,
        module: str,
        task_name: str,
        checkbox: str,
        value: bool,
        agent_id: str,
        reason: Optional[str] = None
    ) -> None:
        """Update a checkbox on a task.

        Args:
            module: Module name.
            task_name: Task name.
            checkbox: One of: planned, implemented, mock_tested,
                      integration_tested, live_tested, spec_compliant
            value: True to check, False to uncheck.
            agent_id: ID of agent making the change.
            reason: Required when unchecking (why it was removed).

        Note:
            Testing agents CAN and SHOULD remove checkboxes when tests fail.
            Spec Compliance agent CAN remove Implemented checkbox.
        """

    def get_incomplete_tasks(self) -> list[TaskRecord]:
        """Get all tasks without all 6 checkboxes checked.

        Used by orchestrator to determine if more work needed.
        """

    def get_module_tasks(self, module: str) -> list[TaskRecord]:
        """Get all tasks for a specific module."""

    def get_all_tasks(self) -> list[TaskRecord]:
        """Get all tasks across all modules."""

    def get_completion_summary(self) -> dict[str, tuple[int, int]]:
        """Get completion summary per module.

        Returns:
            Dict of module -> (complete_tasks, total_tasks)
        """

    def store_evidence(
        self,
        module: str,
        task_name: str,
        evidence_type: str,
        content: Union[str, bytes]
    ) -> str:
        """Store evidence for a task.

        Args:
            module: Module name.
            task_name: Task name.
            evidence_type: Type (test-output, coverage, screenshot).
            content: Evidence content.

        Returns:
            Path to stored evidence.
        """

    def get_evidence(
        self,
        module: str,
        task_name: str,
        evidence_type: str
    ) -> Optional[str]:
        """Retrieve stored evidence."""

@dataclass
class CheckboxChange:
    """Record of a checkbox change."""
    timestamp: datetime
    agent_id: str
    checkbox: str
    old_value: bool
    new_value: bool
    reason: Optional[str]
```

---

## Checkbox Rules

### Who Can Check What

| Checkbox | Can Check | Can Uncheck |
|----------|-----------|-------------|
| Planned | Planning Agent | Uncertainty Review Agent |
| Implemented | Implementation Agent | Testing Agent, Spec Compliance Agent |
| Mock tested | Testing Agent | Testing Agent (on regression) |
| Integration tested | Testing Agent | Testing Agent (on regression) |
| Live tested | Testing Agent | Testing Agent (on regression) |
| Spec Compliant | Spec Compliance Agent | Spec Compliance Agent |

### Critical Rules

1. **Testing Agent CAN remove Implemented checkbox** when tests fail
2. **Spec Compliance Agent CAN remove Implemented checkbox** when spec doesn't match
3. **EVERY uncheck MUST have a reason** documented in history
4. **Orchestrator tracks history** for accountability

---

## Usage Patterns

### Planning Agent Marks Task Planned
```python
records_manager.update_checkbox(
    module="core",
    task_name="Implement Session Manager",
    checkbox="planned",
    value=True,
    agent_id="planning-agent-abc123"
)
```

### Testing Agent Removes Implemented on Failure
```python
# Tests failed - remove the implemented checkbox
records_manager.update_checkbox(
    module="core",
    task_name="Implement Session Manager",
    checkbox="implemented",
    value=False,
    agent_id="testing-agent-xyz789",
    reason="Unit tests failed: test_spawn_session_returns_uuid assertion error"
)
```

### Checking Project Completion
```python
incomplete = records_manager.get_incomplete_tasks()
if incomplete:
    # More work needed
    for task in incomplete:
        checked, total = task.completion_count()
        logger.info(f"Task {task.name}: {checked}/{total}")
else:
    # Project complete!
    logger.info("All tasks have 6/6 checkboxes!")
```

---

## Dependencies

None - this is a leaf module with no external dependencies.

---

## Error Handling

```python
class RecordsError(BeyondRalphError):
    """Records system errors."""

class TaskNotFoundError(RecordsError):
    """Task not found in records."""

class InvalidCheckboxError(RecordsError):
    """Invalid checkbox name."""

class MissingReasonError(RecordsError):
    """Reason required when unchecking checkbox."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Add, update, query tasks |
| Integration tests | Filesystem operations |
| Mock tests | Checkbox state transitions |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested (99% coverage)
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
