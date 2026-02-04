"""Dynamic Project Plan Manager.

Implements the CRITICAL dynamic project plan functionality where:
- Modules CAN add requirements to other modules
- Requirements are technical (no user input needed)
- Modules MUST update PROJECT_PLAN.md with new requirements
- Orchestrator detects updates and schedules work
- Modules MUST aggressively call out when others fail to deliver
- Discrepancies between promised and delivered must be recorded
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RequirementStatus(Enum):
    """Status of a dynamic requirement."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    FAILED = "failed"
    BLOCKED = "blocked"


class RequirementPriority(Enum):
    """Priority of a requirement."""

    CRITICAL = "critical"  # Blocks other work
    HIGH = "high"  # Should be done soon
    NORMAL = "normal"  # Normal priority
    LOW = "low"  # Nice to have


@dataclass
class ModuleRequirement:
    """A requirement from one module to another.

    This is how modules communicate what they need from each other
    WITHOUT requiring user input.
    """

    id: str
    requesting_module: str
    providing_module: str
    description: str
    technical_spec: str
    priority: RequirementPriority = RequirementPriority.NORMAL
    status: RequirementStatus = RequirementStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    delivered_at: datetime | None = None
    failure_reason: str | None = None
    evidence_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "requesting_module": self.requesting_module,
            "providing_module": self.providing_module,
            "description": self.description,
            "technical_spec": self.technical_spec,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "failure_reason": self.failure_reason,
            "evidence_path": self.evidence_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModuleRequirement":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            requesting_module=data["requesting_module"],
            providing_module=data["providing_module"],
            description=data["description"],
            technical_spec=data["technical_spec"],
            priority=RequirementPriority(data.get("priority", "normal")),
            status=RequirementStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            delivered_at=(
                datetime.fromisoformat(data["delivered_at"])
                if data.get("delivered_at")
                else None
            ),
            failure_reason=data.get("failure_reason"),
            evidence_path=data.get("evidence_path"),
        )


@dataclass
class Discrepancy:
    """A discrepancy between what was promised and what was delivered."""

    id: str
    module: str
    requirement_id: str
    expected: str
    actual: str
    severity: str  # "critical", "major", "minor"
    reported_by: str
    reported_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "module": self.module,
            "requirement_id": self.requirement_id,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity,
            "reported_by": self.reported_by,
            "reported_at": self.reported_at.isoformat(),
            "resolved": self.resolved,
            "resolution": self.resolution,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Discrepancy":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            module=data["module"],
            requirement_id=data["requirement_id"],
            expected=data["expected"],
            actual=data["actual"],
            severity=data["severity"],
            reported_by=data["reported_by"],
            reported_at=datetime.fromisoformat(data["reported_at"]),
            resolved=data.get("resolved", False),
            resolution=data.get("resolution"),
        )


class DynamicPlanManager:
    """Manages the dynamic project plan.

    Key responsibilities:
    1. Track requirements between modules
    2. Detect when new requirements are added
    3. Schedule work for unmet requirements
    4. Track and report discrepancies
    5. Update PROJECT_PLAN.md with changes
    """

    def __init__(
        self,
        project_root: Path | None = None,
        requirements_file: str = ".beyond_ralph_requirements.json",
        discrepancies_file: str = ".beyond_ralph_discrepancies.json",
    ):
        """Initialize the dynamic plan manager.

        Args:
            project_root: Root directory of the project.
            requirements_file: File to store requirements.
            discrepancies_file: File to store discrepancies.
        """
        self.project_root = project_root or Path.cwd()
        self.requirements_file = self.project_root / requirements_file
        self.discrepancies_file = self.project_root / discrepancies_file
        self._requirements: dict[str, ModuleRequirement] = {}
        self._discrepancies: dict[str, Discrepancy] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load state from files."""
        # Load requirements
        if self.requirements_file.exists():
            try:
                data = json.loads(self.requirements_file.read_text())
                self._requirements = {
                    k: ModuleRequirement.from_dict(v)
                    for k, v in data.get("requirements", {}).items()
                }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load requirements: {e}")
                self._requirements = {}

        # Load discrepancies
        if self.discrepancies_file.exists():
            try:
                data = json.loads(self.discrepancies_file.read_text())
                self._discrepancies = {
                    k: Discrepancy.from_dict(v)
                    for k, v in data.get("discrepancies", {}).items()
                }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load discrepancies: {e}")
                self._discrepancies = {}

    def _save_state(self) -> None:
        """Save state to files."""
        # Save requirements
        req_data = {
            "requirements": {k: v.to_dict() for k, v in self._requirements.items()},
            "updated_at": datetime.now().isoformat(),
        }
        self.requirements_file.write_text(json.dumps(req_data, indent=2))

        # Save discrepancies
        disc_data = {
            "discrepancies": {k: v.to_dict() for k, v in self._discrepancies.items()},
            "updated_at": datetime.now().isoformat(),
        }
        self.discrepancies_file.write_text(json.dumps(disc_data, indent=2))

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        import uuid

        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def add_requirement(
        self,
        requesting_module: str,
        providing_module: str,
        description: str,
        technical_spec: str,
        priority: RequirementPriority = RequirementPriority.NORMAL,
    ) -> ModuleRequirement:
        """Add a new requirement from one module to another.

        This is how modules communicate dependencies WITHOUT user input.

        Args:
            requesting_module: Module that needs something.
            providing_module: Module that should provide it.
            description: Human-readable description.
            technical_spec: Technical specification (e.g., function signature).
            priority: Priority of the requirement.

        Returns:
            The created ModuleRequirement.
        """
        req_id = self._generate_id("req")
        requirement = ModuleRequirement(
            id=req_id,
            requesting_module=requesting_module,
            providing_module=providing_module,
            description=description,
            technical_spec=technical_spec,
            priority=priority,
        )

        self._requirements[req_id] = requirement
        self._save_state()

        # Update PROJECT_PLAN.md
        self._update_project_plan(requirement)

        logger.info(
            f"[DYNAMIC-PLAN] New requirement: {requesting_module} -> {providing_module}: "
            f"{description}"
        )

        return requirement

    def _update_project_plan(self, requirement: ModuleRequirement) -> None:
        """Update PROJECT_PLAN.md with the new requirement.

        Args:
            requirement: The requirement to add.
        """
        plan_path = self.project_root / "PROJECT_PLAN.md"
        if not plan_path.exists():
            return

        content = plan_path.read_text()

        # Find or create the Dynamic Requirements section
        section_header = "## Dynamic Module Requirements"
        if section_header not in content:
            # Add section before the Timeline section
            timeline_marker = "## Timeline"
            if timeline_marker in content:
                content = content.replace(
                    timeline_marker,
                    f"{section_header}\n\n"
                    f"*Auto-generated requirements between modules.*\n\n"
                    f"---\n\n{timeline_marker}",
                )
            else:
                content += f"\n\n{section_header}\n\n*Auto-generated requirements between modules.*\n\n"

        # Add the requirement entry
        req_entry = (
            f"### [{requirement.id}] {requirement.requesting_module} → "
            f"{requirement.providing_module}\n"
            f"- **Description**: {requirement.description}\n"
            f"- **Technical Spec**: `{requirement.technical_spec}`\n"
            f"- **Priority**: {requirement.priority.value}\n"
            f"- **Status**: {requirement.status.value}\n"
            f"- **Created**: {requirement.created_at.isoformat()}\n\n"
        )

        # Insert after section header
        section_idx = content.find(section_header)
        if section_idx != -1:
            # Find the next section or end
            insert_pos = content.find("\n---\n", section_idx)
            if insert_pos == -1:
                insert_pos = len(content)

            content = content[:insert_pos] + req_entry + content[insert_pos:]

        plan_path.write_text(content)
        logger.debug(f"[DYNAMIC-PLAN] Updated PROJECT_PLAN.md with requirement {requirement.id}")

    def mark_delivered(
        self,
        requirement_id: str,
        evidence_path: str | None = None,
    ) -> bool:
        """Mark a requirement as delivered.

        Args:
            requirement_id: ID of the requirement.
            evidence_path: Path to evidence of delivery.

        Returns:
            True if marked successfully.
        """
        if requirement_id not in self._requirements:
            logger.warning(f"[DYNAMIC-PLAN] Unknown requirement: {requirement_id}")
            return False

        req = self._requirements[requirement_id]
        req.status = RequirementStatus.DELIVERED
        req.delivered_at = datetime.now()
        req.updated_at = datetime.now()
        req.evidence_path = evidence_path

        self._save_state()
        logger.info(f"[DYNAMIC-PLAN] Requirement {requirement_id} marked as DELIVERED")
        return True

    def mark_failed(
        self,
        requirement_id: str,
        reason: str,
    ) -> bool:
        """Mark a requirement as failed.

        This is how modules AGGRESSIVELY call out failures.

        Args:
            requirement_id: ID of the requirement.
            reason: Why it failed.

        Returns:
            True if marked successfully.
        """
        if requirement_id not in self._requirements:
            logger.warning(f"[DYNAMIC-PLAN] Unknown requirement: {requirement_id}")
            return False

        req = self._requirements[requirement_id]
        req.status = RequirementStatus.FAILED
        req.failure_reason = reason
        req.updated_at = datetime.now()

        self._save_state()
        logger.error(
            f"[DYNAMIC-PLAN] REQUIREMENT FAILED: {requirement_id} - "
            f"{req.providing_module} failed to deliver: {reason}"
        )
        return True

    def report_discrepancy(
        self,
        module: str,
        requirement_id: str,
        expected: str,
        actual: str,
        severity: str,
        reported_by: str,
    ) -> Discrepancy:
        """Report a discrepancy between promised and delivered.

        Modules MUST call this when what they receive doesn't match
        what was promised.

        Args:
            module: Module that has the discrepancy.
            requirement_id: Related requirement ID.
            expected: What was expected.
            actual: What was actually delivered.
            severity: "critical", "major", or "minor".
            reported_by: Who is reporting (module/agent name).

        Returns:
            The created Discrepancy.
        """
        disc_id = self._generate_id("disc")
        discrepancy = Discrepancy(
            id=disc_id,
            module=module,
            requirement_id=requirement_id,
            expected=expected,
            actual=actual,
            severity=severity,
            reported_by=reported_by,
        )

        self._discrepancies[disc_id] = discrepancy
        self._save_state()

        logger.error(
            f"[DYNAMIC-PLAN] DISCREPANCY REPORTED [{severity.upper()}]: "
            f"{module} - Expected: {expected}, Got: {actual}"
        )

        return discrepancy

    def resolve_discrepancy(
        self,
        discrepancy_id: str,
        resolution: str,
    ) -> bool:
        """Mark a discrepancy as resolved.

        Args:
            discrepancy_id: ID of the discrepancy.
            resolution: How it was resolved.

        Returns:
            True if resolved successfully.
        """
        if discrepancy_id not in self._discrepancies:
            return False

        disc = self._discrepancies[discrepancy_id]
        disc.resolved = True
        disc.resolution = resolution

        self._save_state()
        logger.info(f"[DYNAMIC-PLAN] Discrepancy {discrepancy_id} resolved: {resolution}")
        return True

    def get_pending_requirements(
        self,
        for_module: str | None = None,
    ) -> list[ModuleRequirement]:
        """Get all pending requirements.

        Args:
            for_module: If specified, only get requirements for this module.

        Returns:
            List of pending requirements.
        """
        pending = [
            req
            for req in self._requirements.values()
            if req.status in (RequirementStatus.PENDING, RequirementStatus.FAILED)
        ]

        if for_module:
            pending = [req for req in pending if req.providing_module == for_module]

        # Sort by priority (critical first)
        priority_order = {
            RequirementPriority.CRITICAL: 0,
            RequirementPriority.HIGH: 1,
            RequirementPriority.NORMAL: 2,
            RequirementPriority.LOW: 3,
        }
        pending.sort(key=lambda r: priority_order[r.priority])

        return pending

    def get_unresolved_discrepancies(
        self,
        for_module: str | None = None,
    ) -> list[Discrepancy]:
        """Get all unresolved discrepancies.

        Args:
            for_module: If specified, only for this module.

        Returns:
            List of unresolved discrepancies.
        """
        unresolved = [
            disc for disc in self._discrepancies.values() if not disc.resolved
        ]

        if for_module:
            unresolved = [disc for disc in unresolved if disc.module == for_module]

        # Sort by severity
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        unresolved.sort(key=lambda d: severity_order.get(d.severity, 99))

        return unresolved

    def has_blocking_issues(self) -> bool:
        """Check if there are any blocking issues.

        Blocking issues are:
        - Critical priority requirements that are PENDING or FAILED
        - Critical severity discrepancies

        Returns:
            True if there are blocking issues.
        """
        # Check critical requirements
        for req in self._requirements.values():
            if req.priority == RequirementPriority.CRITICAL and req.status in (
                RequirementStatus.PENDING,
                RequirementStatus.FAILED,
            ):
                return True

        # Check critical discrepancies
        for disc in self._discrepancies.values():
            if disc.severity == "critical" and not disc.resolved:
                return True

        return False

    def get_work_for_module(self, module: str) -> list[ModuleRequirement]:
        """Get work that needs to be done by a module.

        This is called by the orchestrator to find what a module
        needs to deliver.

        Args:
            module: The module name.

        Returns:
            List of requirements this module needs to fulfill.
        """
        return [
            req
            for req in self._requirements.values()
            if req.providing_module == module
            and req.status in (RequirementStatus.PENDING, RequirementStatus.FAILED)
        ]

    def generate_status_report(self) -> str:
        """Generate a status report of all dynamic requirements.

        Returns:
            Markdown-formatted status report.
        """
        lines = ["# Dynamic Plan Status Report", ""]

        # Summary
        total_reqs = len(self._requirements)
        pending = sum(1 for r in self._requirements.values() if r.status == RequirementStatus.PENDING)
        delivered = sum(
            1 for r in self._requirements.values() if r.status == RequirementStatus.DELIVERED
        )
        failed = sum(1 for r in self._requirements.values() if r.status == RequirementStatus.FAILED)

        lines.append("## Summary")
        lines.append(f"- **Total Requirements**: {total_reqs}")
        lines.append(f"- **Pending**: {pending}")
        lines.append(f"- **Delivered**: {delivered}")
        lines.append(f"- **Failed**: {failed}")
        lines.append("")

        # Unresolved discrepancies
        unresolved = self.get_unresolved_discrepancies()
        if unresolved:
            lines.append("## Unresolved Discrepancies")
            for disc in unresolved:
                lines.append(f"- [{disc.severity.upper()}] {disc.module}: {disc.expected} vs {disc.actual}")
            lines.append("")

        # Pending work by module
        pending_reqs = self.get_pending_requirements()
        if pending_reqs:
            lines.append("## Pending Work by Module")
            by_module: dict[str, list[ModuleRequirement]] = {}
            for req in pending_reqs:
                if req.providing_module not in by_module:
                    by_module[req.providing_module] = []
                by_module[req.providing_module].append(req)

            for module, reqs in sorted(by_module.items()):
                lines.append(f"\n### {module}")
                for req in reqs:
                    status_icon = "!" if req.status == RequirementStatus.FAILED else "?"
                    lines.append(
                        f"- [{status_icon}] {req.description} "
                        f"(requested by {req.requesting_module})"
                    )
            lines.append("")

        # Blocking issues warning
        if self.has_blocking_issues():
            lines.append("## WARNING: BLOCKING ISSUES PRESENT")
            lines.append("Critical requirements or discrepancies are blocking progress.")
            lines.append("")

        return "\n".join(lines)


# Singleton instance
_plan_manager: DynamicPlanManager | None = None


def get_dynamic_plan_manager(project_root: Path | None = None) -> DynamicPlanManager:
    """Get the dynamic plan manager singleton.

    Args:
        project_root: Project root directory.

    Returns:
        The DynamicPlanManager instance.
    """
    global _plan_manager
    if _plan_manager is None:
        _plan_manager = DynamicPlanManager(project_root=project_root)
    return _plan_manager
