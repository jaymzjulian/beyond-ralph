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
        assert task.completion_fraction == "2/5"

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
