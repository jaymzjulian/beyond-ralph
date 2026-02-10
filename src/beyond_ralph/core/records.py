"""Records System for Beyond Ralph.

Handles task tracking with 7 checkboxes per task:
- Planned
- Implemented
- Mock tested
- Integration tested
- Live tested
- Spec Compliant (verified by separate agent that implementation matches spec)
- Audit Verified (verified by static analysis + LLM interrogation for stubs/fakes)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Default records location
DEFAULT_RECORDS_PATH = Path("records")


class Checkbox(Enum):
    """Task completion checkboxes."""

    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    MOCK_TESTED = "mock_tested"
    INTEGRATION_TESTED = "integration_tested"
    LIVE_TESTED = "live_tested"
    SPEC_COMPLIANT = "spec_compliant"  # Verified by separate agent
    AUDIT_VERIFIED = "audit_verified"  # Verified by static analysis + LLM interrogation


CHECKBOX_LABELS = {
    Checkbox.PLANNED: "Planned",
    Checkbox.IMPLEMENTED: "Implemented",
    Checkbox.MOCK_TESTED: "Mock tested",
    Checkbox.INTEGRATION_TESTED: "Integration tested",
    Checkbox.LIVE_TESTED: "Live tested",
    Checkbox.SPEC_COMPLIANT: "Spec compliant",
    Checkbox.AUDIT_VERIFIED: "Audit verified",
}


@dataclass
class Task:
    """A task with 7 checkboxes.

    The 6th checkbox (SPEC_COMPLIANT) is verified by a SEPARATE agent
    that confirms the implementation matches what the spec says.
    The 7th checkbox (AUDIT_VERIFIED) is verified by static analysis
    and LLM interrogation to catch stubs, fakes, and TODOs.
    """

    id: str
    module: str
    name: str
    description: str
    checkboxes: dict[Checkbox, bool] = field(default_factory=dict)
    notes: str = ""
    implementation_agent: str | None = None
    validation_agent: str | None = None
    spec_compliance_agent: str | None = None  # Agent that verified spec compliance
    evidence_path: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize checkboxes if not provided."""
        if not self.checkboxes:
            self.checkboxes = dict.fromkeys(Checkbox, False)

    @property
    def is_complete(self) -> bool:
        """Check if all 7 checkboxes are checked."""
        return all(self.checkboxes.values())

    @property
    def completion_count(self) -> int:
        """Count how many checkboxes are checked."""
        return sum(1 for v in self.checkboxes.values() if v)

    @property
    def completion_fraction(self) -> str:
        """Return completion as X/6 string."""
        return f"{self.completion_count}/7"

    def to_markdown(self) -> str:
        """Convert task to Markdown format."""
        lines = [f"### Task: {self.name}", ""]

        for cb in Checkbox:
            checked = "[x]" if self.checkboxes.get(cb, False) else "[ ]"
            lines.append(f"- {checked} {CHECKBOX_LABELS[cb]}")

        lines.append("")
        lines.append(f"**Description**: {self.description}")

        if self.notes:
            lines.append(f"**Notes**: {self.notes}")

        if self.implementation_agent:
            lines.append(f"**Implementation Agent**: {self.implementation_agent}")

        if self.validation_agent:
            lines.append(f"**Validation Agent**: {self.validation_agent}")

        if self.evidence_path:
            lines.append(f"**Evidence**: {self.evidence_path}")

        return "\n".join(lines)


class RecordsManager:
    """Manages task records for all modules."""

    def __init__(self, path: Path | None = None):
        """Initialize records manager.

        Args:
            path: Path to records directory. Defaults to records/
        """
        self.path = path or DEFAULT_RECORDS_PATH
        self.path.mkdir(parents=True, exist_ok=True)

    def _get_module_path(self, module: str) -> Path:
        """Get path to module's records directory."""
        module_path = self.path / module
        module_path.mkdir(parents=True, exist_ok=True)
        return module_path

    def _get_tasks_file(self, module: str) -> Path:
        """Get path to module's tasks.md file."""
        return self._get_module_path(module) / "tasks.md"

    def parse_tasks_file(self, module: str) -> list[Task]:
        """Parse tasks from a module's tasks.md file.

        Args:
            module: Module name.

        Returns:
            List of Task objects.
        """
        tasks_file = self._get_tasks_file(module)
        if not tasks_file.exists():
            return []

        content = tasks_file.read_text()
        tasks = []

        # Parse tasks using regex
        task_pattern = r"### Task: (.+?)(?=### Task:|$)"
        task_blocks = re.findall(task_pattern, content, re.DOTALL)

        for i, block in enumerate(task_blocks):
            lines = block.strip().split("\n")
            name = lines[0].strip() if lines else f"Task {i+1}"

            # Parse checkboxes
            checkboxes = {}
            for cb in Checkbox:
                label = CHECKBOX_LABELS[cb]
                checked_pattern = rf"\[x\]\s*{re.escape(label)}"
                unchecked_pattern = rf"\[\s*\]\s*{re.escape(label)}"

                if re.search(checked_pattern, block, re.IGNORECASE):
                    checkboxes[cb] = True
                elif re.search(unchecked_pattern, block, re.IGNORECASE):
                    checkboxes[cb] = False

            # Parse description
            desc_match = re.search(r"\*\*Description\*\*:\s*(.+?)(?=\n\*\*|\n---|\n###|$)", block, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""

            # Parse notes
            notes_match = re.search(r"\*\*Notes\*\*:\s*(.+?)(?=\n\*\*|\n---|\n###|$)", block, re.DOTALL)
            notes = notes_match.group(1).strip() if notes_match else ""

            # Parse agent info
            impl_match = re.search(r"\*\*Implementation Agent\*\*:\s*(.+)", block)
            impl_agent = impl_match.group(1).strip() if impl_match else None

            val_match = re.search(r"\*\*Validation Agent\*\*:\s*(.+)", block)
            val_agent = val_match.group(1).strip() if val_match else None

            evidence_match = re.search(r"\*\*Evidence\*\*:\s*(.+)", block)
            evidence = evidence_match.group(1).strip() if evidence_match else None

            task = Task(
                id=f"{module}-{i+1}",
                module=module,
                name=name,
                description=description,
                checkboxes=checkboxes,
                notes=notes,
                implementation_agent=impl_agent,
                validation_agent=val_agent,
                evidence_path=evidence,
            )
            tasks.append(task)

        return tasks

    def update_checkbox(
        self,
        module: str,
        task_name: str,
        checkbox: Checkbox,
        checked: bool,
    ) -> bool:
        """Update a specific checkbox for a task.

        Args:
            module: Module name.
            task_name: Name of the task.
            checkbox: Which checkbox to update.
            checked: New checked state.

        Returns:
            True if update succeeded.
        """
        tasks_file = self._get_tasks_file(module)
        if not tasks_file.exists():
            return False

        content = tasks_file.read_text()
        label = CHECKBOX_LABELS[checkbox]

        # Find the task section
        task_pattern = rf"(### Task: {re.escape(task_name)}.+?)(?=### Task:|$)"
        task_match = re.search(task_pattern, content, re.DOTALL)

        if not task_match:
            return False

        task_block = task_match.group(1)

        # Update the checkbox
        new_marker = "[x]" if checked else "[ ]"
        old_marker = "[ ]" if checked else "[x]"

        checkbox_pattern = rf"\[[ x]\]\s*{re.escape(label)}"
        new_checkbox = f"{new_marker} {label}"

        new_task_block = re.sub(checkbox_pattern, new_checkbox, task_block, flags=re.IGNORECASE)

        # Replace in content
        new_content = content.replace(task_block, new_task_block)
        tasks_file.write_text(new_content)

        return True

    def get_module_tasks(self, module: str) -> list[Task]:
        """Get all tasks for a module.

        Args:
            module: Module name.

        Returns:
            List of Task objects.
        """
        return self.parse_tasks_file(module)

    def get_incomplete_tasks(self) -> list[Task]:
        """Get all incomplete tasks (not all 7 checkboxes checked).

        Returns:
            List of incomplete Task objects.
        """
        incomplete = []

        for module_dir in self.path.iterdir():
            if module_dir.is_dir():
                tasks = self.get_module_tasks(module_dir.name)
                incomplete.extend(t for t in tasks if not t.is_complete)

        return incomplete

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks from all modules.

        Returns:
            List of all Task objects.
        """
        all_tasks = []

        for module_dir in self.path.iterdir():
            if module_dir.is_dir():
                tasks = self.get_module_tasks(module_dir.name)
                all_tasks.extend(tasks)

        return all_tasks

    def is_complete(self) -> bool:
        """Check if ALL tasks have 7/7 checkboxes.

        Returns:
            True if all tasks complete.
        """
        for module_dir in self.path.iterdir():
            if module_dir.is_dir():
                tasks = self.get_module_tasks(module_dir.name)
                if any(not t.is_complete for t in tasks):
                    return False

        return True

    def get_progress_summary(self) -> dict[str, Any]:
        """Get overall progress summary.

        Returns:
            Dict with progress statistics.
        """
        all_tasks = self.get_all_tasks()
        total = len(all_tasks)
        complete = sum(1 for t in all_tasks if t.is_complete)

        by_module: dict[str, dict[str, int]] = {}
        for task in all_tasks:
            if task.module not in by_module:
                by_module[task.module] = {"total": 0, "complete": 0}
            by_module[task.module]["total"] += 1
            if task.is_complete:
                by_module[task.module]["complete"] += 1

        return {
            "total_tasks": total,
            "complete_tasks": complete,
            "incomplete_tasks": total - complete,
            "percent_complete": (complete / total * 100) if total > 0 else 0,
            "by_module": by_module,
        }

    def add_task(
        self,
        module: str,
        name: str,
        description: str,
        notes: str = "",
    ) -> Task:
        """Add a new task to a module.

        Args:
            module: Module name.
            name: Task name.
            description: Task description.
            notes: Optional notes.

        Returns:
            The created Task.
        """
        tasks = self.get_module_tasks(module)
        task_id = f"{module}-{len(tasks) + 1}"

        task = Task(
            id=task_id,
            module=module,
            name=name,
            description=description,
            notes=notes,
        )

        # Append to tasks file
        tasks_file = self._get_tasks_file(module)
        content = tasks_file.read_text() if tasks_file.exists() else f"# {module.title()} Module Tasks\n\n"

        content += "\n---\n\n" + task.to_markdown() + "\n"
        tasks_file.write_text(content)

        return task

    def get_modules(self) -> list[str]:
        """Get list of all module names.

        Returns:
            List of module names.
        """
        modules = []
        for module_dir in self.path.iterdir():
            if module_dir.is_dir():
                modules.append(module_dir.name)
        return sorted(modules)
