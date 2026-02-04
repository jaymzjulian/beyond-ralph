"""Unit tests for Records System."""

from pathlib import Path

import pytest

from beyond_ralph.core.records import (
    Checkbox,
    RecordsManager,
    Task,
)


@pytest.fixture
def temp_records_path(tmp_path: Path) -> Path:
    """Create a temporary records directory."""
    records_path = tmp_path / "records"
    records_path.mkdir()
    return records_path


@pytest.fixture
def records(temp_records_path: Path) -> RecordsManager:
    """Create a records manager with temp directory."""
    return RecordsManager(path=temp_records_path)


class TestTask:
    """Tests for Task dataclass."""

    def test_is_complete(self) -> None:
        """Test completion detection."""
        task = Task(
            id="test-1",
            module="test",
            name="Test Task",
            description="A test task",
            checkboxes={cb: True for cb in Checkbox},
        )
        assert task.is_complete

    def test_is_incomplete(self) -> None:
        """Test incomplete detection."""
        task = Task(
            id="test-1",
            module="test",
            name="Test Task",
            description="A test task",
            checkboxes={
                Checkbox.PLANNED: True,
                Checkbox.IMPLEMENTED: True,
                Checkbox.MOCK_TESTED: False,
                Checkbox.INTEGRATION_TESTED: False,
                Checkbox.LIVE_TESTED: False,
            },
        )
        assert not task.is_complete
        assert task.completion_count == 2
        assert task.completion_fraction == "2/6"

    def test_to_markdown(self) -> None:
        """Test markdown generation."""
        task = Task(
            id="test-1",
            module="test",
            name="Implement Feature",
            description="A new feature",
            checkboxes={
                Checkbox.PLANNED: True,
                Checkbox.IMPLEMENTED: False,
                Checkbox.MOCK_TESTED: False,
                Checkbox.INTEGRATION_TESTED: False,
                Checkbox.LIVE_TESTED: False,
            },
        )

        md = task.to_markdown()

        assert "### Task: Implement Feature" in md
        assert "[x] Planned" in md
        assert "[ ] Implemented" in md
        assert "**Description**: A new feature" in md


class TestRecordsManager:
    """Tests for RecordsManager."""

    def test_parse_tasks_file(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test parsing tasks from markdown file."""
        # Create a test tasks file
        module_dir = temp_records_path / "test-module"
        module_dir.mkdir()

        tasks_file = module_dir / "tasks.md"
        tasks_file.write_text("""# Test Module Tasks

### Task: First Task

- [x] Planned
- [x] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: The first task.

### Task: Second Task

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: The second task.
**Notes**: Some notes here.
""")

        tasks = records.parse_tasks_file("test-module")

        assert len(tasks) == 2
        assert tasks[0].name == "First Task"
        assert tasks[0].checkboxes[Checkbox.PLANNED] is True
        assert tasks[0].checkboxes[Checkbox.IMPLEMENTED] is True
        assert tasks[0].checkboxes[Checkbox.MOCK_TESTED] is False

        assert tasks[1].name == "Second Task"
        assert tasks[1].checkboxes[Checkbox.PLANNED] is True
        assert tasks[1].checkboxes[Checkbox.IMPLEMENTED] is False

    def test_update_checkbox(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test updating a checkbox."""
        module_dir = temp_records_path / "test-module"
        module_dir.mkdir()

        tasks_file = module_dir / "tasks.md"
        tasks_file.write_text("""# Test Module Tasks

### Task: My Task

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: A task.
""")

        # Update checkbox
        result = records.update_checkbox(
            "test-module",
            "My Task",
            Checkbox.IMPLEMENTED,
            True,
        )
        assert result

        # Verify update
        content = tasks_file.read_text()
        assert "[x] Implemented" in content

    def test_get_incomplete_tasks(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test getting incomplete tasks."""
        # Create two modules
        for module in ["module-a", "module-b"]:
            module_dir = temp_records_path / module
            module_dir.mkdir()

        # Module A has complete task
        (temp_records_path / "module-a" / "tasks.md").write_text("""
### Task: Complete Task

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [x] Integration tested
- [x] Live tested

**Description**: Done.
""")

        # Module B has incomplete task
        (temp_records_path / "module-b" / "tasks.md").write_text("""
### Task: Incomplete Task

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Not done.
""")

        incomplete = records.get_incomplete_tasks()
        assert len(incomplete) == 1
        assert incomplete[0].name == "Incomplete Task"

    def test_is_complete(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test project completion check."""
        module_dir = temp_records_path / "test-module"
        module_dir.mkdir()

        # All tasks complete
        (module_dir / "tasks.md").write_text("""
### Task: Only Task

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [x] Integration tested
- [x] Live tested

**Description**: Done.
""")

        assert records.is_complete()

        # Add incomplete task
        (module_dir / "tasks.md").write_text("""
### Task: Only Task

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Not done.
""")

        assert not records.is_complete()

    def test_progress_summary(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test progress summary generation."""
        module_dir = temp_records_path / "test-module"
        module_dir.mkdir()

        (module_dir / "tasks.md").write_text("""
### Task: Task 1

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [x] Integration tested
- [x] Live tested

**Description**: Done.

### Task: Task 2

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Not done.
""")

        summary = records.get_progress_summary()

        assert summary["total_tasks"] == 2
        assert summary["complete_tasks"] == 1
        assert summary["incomplete_tasks"] == 1
        assert summary["percent_complete"] == 50.0


class TestTaskEdgeCases:
    """Tests for Task dataclass edge cases."""

    def test_post_init_initializes_checkboxes_when_empty(self) -> None:
        """Test that __post_init__ initializes checkboxes when not provided."""
        task = Task(
            id="test-1",
            module="test",
            name="Test Task",
            description="A test task",
            # No checkboxes provided
        )
        # Should have all checkboxes initialized to False
        assert len(task.checkboxes) == 6
        for cb in Checkbox:
            assert cb in task.checkboxes
            assert task.checkboxes[cb] is False

    def test_to_markdown_with_notes(self) -> None:
        """Test markdown generation includes notes when present."""
        task = Task(
            id="test-1",
            module="test",
            name="Task With Notes",
            description="Description here",
            notes="Some important notes",
        )

        md = task.to_markdown()

        assert "**Notes**: Some important notes" in md

    def test_to_markdown_with_implementation_agent(self) -> None:
        """Test markdown generation includes implementation agent when present."""
        task = Task(
            id="test-1",
            module="test",
            name="Task With Agent",
            description="Description",
            implementation_agent="agent-uuid-123",
        )

        md = task.to_markdown()

        assert "**Implementation Agent**: agent-uuid-123" in md

    def test_to_markdown_with_validation_agent(self) -> None:
        """Test markdown generation includes validation agent when present."""
        task = Task(
            id="test-1",
            module="test",
            name="Task With Validation",
            description="Description",
            validation_agent="validator-uuid-456",
        )

        md = task.to_markdown()

        assert "**Validation Agent**: validator-uuid-456" in md

    def test_to_markdown_with_evidence_path(self) -> None:
        """Test markdown generation includes evidence path when present."""
        task = Task(
            id="test-1",
            module="test",
            name="Task With Evidence",
            description="Description",
            evidence_path="records/test-module/evidence/",
        )

        md = task.to_markdown()

        assert "**Evidence**: records/test-module/evidence/" in md

    def test_to_markdown_with_all_optional_fields(self) -> None:
        """Test markdown generation with all optional fields."""
        task = Task(
            id="test-1",
            module="test",
            name="Full Task",
            description="Full description",
            notes="Notes here",
            implementation_agent="impl-agent",
            validation_agent="val-agent",
            evidence_path="evidence/path",
            checkboxes={cb: True for cb in Checkbox},
        )

        md = task.to_markdown()

        assert "**Notes**: Notes here" in md
        assert "**Implementation Agent**: impl-agent" in md
        assert "**Validation Agent**: val-agent" in md
        assert "**Evidence**: evidence/path" in md


class TestRecordsManagerEdgeCases:
    """Tests for RecordsManager edge cases."""

    def test_update_checkbox_file_not_exists(self, records: RecordsManager) -> None:
        """Test update_checkbox returns False when file doesn't exist."""
        result = records.update_checkbox(
            "nonexistent-module",
            "Some Task",
            Checkbox.PLANNED,
            True,
        )
        assert result is False

    def test_update_checkbox_task_not_found(
        self, records: RecordsManager, temp_records_path: Path
    ) -> None:
        """Test update_checkbox returns False when task not found."""
        module_dir = temp_records_path / "test-module"
        module_dir.mkdir()

        (module_dir / "tasks.md").write_text("""# Test Module Tasks

### Task: Existing Task

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: An existing task.
""")

        result = records.update_checkbox(
            "test-module",
            "Nonexistent Task",  # This task doesn't exist
            Checkbox.PLANNED,
            True,
        )
        assert result is False

    def test_add_task(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test adding a new task to a module."""
        task = records.add_task(
            module="new-module",
            name="New Task",
            description="A newly added task",
            notes="Some notes",
        )

        assert task.id == "new-module-1"
        assert task.module == "new-module"
        assert task.name == "New Task"
        assert task.description == "A newly added task"
        assert task.notes == "Some notes"

        # Verify file was created
        tasks_file = temp_records_path / "new-module" / "tasks.md"
        assert tasks_file.exists()

        content = tasks_file.read_text()
        assert "### Task: New Task" in content
        assert "**Description**: A newly added task" in content
        assert "**Notes**: Some notes" in content

    def test_add_task_to_existing_module(
        self, records: RecordsManager, temp_records_path: Path
    ) -> None:
        """Test adding a task to a module that already has tasks."""
        module_dir = temp_records_path / "existing-module"
        module_dir.mkdir()

        # Create initial tasks file
        (module_dir / "tasks.md").write_text("""# Existing Module Tasks

### Task: First Task

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: The first task.
""")

        # Add a new task
        task = records.add_task(
            module="existing-module",
            name="Second Task",
            description="The second task",
        )

        # Should have ID based on existing count
        assert task.id == "existing-module-2"

        # Verify file was updated
        content = (module_dir / "tasks.md").read_text()
        assert "### Task: First Task" in content
        assert "### Task: Second Task" in content

    def test_get_modules(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test getting list of all modules."""
        # Create some module directories
        (temp_records_path / "module-a").mkdir()
        (temp_records_path / "module-b").mkdir()
        (temp_records_path / "module-c").mkdir()

        modules = records.get_modules()

        assert len(modules) == 3
        assert "module-a" in modules
        assert "module-b" in modules
        assert "module-c" in modules
        # Should be sorted
        assert modules == ["module-a", "module-b", "module-c"]

    def test_get_modules_empty(self, records: RecordsManager) -> None:
        """Test get_modules returns empty list when no modules exist."""
        modules = records.get_modules()
        assert modules == []

    def test_get_all_tasks(self, records: RecordsManager, temp_records_path: Path) -> None:
        """Test getting all tasks from all modules."""
        # Create two modules with tasks
        module_a = temp_records_path / "module-a"
        module_a.mkdir()
        (module_a / "tasks.md").write_text("""
### Task: Task A1

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Task in module A.
""")

        module_b = temp_records_path / "module-b"
        module_b.mkdir()
        (module_b / "tasks.md").write_text("""
### Task: Task B1

- [x] Planned
- [x] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Task in module B.
""")

        all_tasks = records.get_all_tasks()

        assert len(all_tasks) == 2
        names = [t.name for t in all_tasks]
        assert "Task A1" in names
        assert "Task B1" in names

    def test_parse_tasks_file_with_agents(
        self, records: RecordsManager, temp_records_path: Path
    ) -> None:
        """Test parsing tasks that include agent info."""
        module_dir = temp_records_path / "test-module"
        module_dir.mkdir()

        (module_dir / "tasks.md").write_text("""
### Task: Task With Agents

- [x] Planned
- [x] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: A task with agent info.
**Notes**: Important notes.
**Implementation Agent**: impl-agent-123
**Validation Agent**: val-agent-456
**Evidence**: evidence/path/here
""")

        tasks = records.parse_tasks_file("test-module")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.name == "Task With Agents"
        assert task.notes == "Important notes."
        assert task.implementation_agent == "impl-agent-123"
        assert task.validation_agent == "val-agent-456"
        assert task.evidence_path == "evidence/path/here"

    def test_parse_tasks_empty_module(self, records: RecordsManager) -> None:
        """Test parsing tasks from nonexistent module returns empty list."""
        tasks = records.parse_tasks_file("nonexistent-module")
        assert tasks == []

    def test_progress_summary_empty_module(
        self, records: RecordsManager, temp_records_path: Path
    ) -> None:
        """Test progress summary with no tasks."""
        # Create an empty module directory (no tasks.md)
        module_dir = temp_records_path / "empty-module"
        module_dir.mkdir()

        summary = records.get_progress_summary()

        assert summary["total_tasks"] == 0
        assert summary["complete_tasks"] == 0
        assert summary["percent_complete"] == 0
