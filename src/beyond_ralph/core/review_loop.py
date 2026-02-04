"""Review-Fix Loop Manager.

Implements the MANDATORY review-fix loop where:
- Code Review Agent finds issues
- Coding Agent MUST fix ALL items (no dismissals)
- Re-review after fixes
- Loop until 0 must-fix items

This is NON-NEGOTIABLE: Coding Agent cannot argue or dismiss items.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ReviewItemSeverity(Enum):
    """Severity of a review item."""

    CRITICAL = "critical"  # Must fix - security/correctness
    ERROR = "error"  # Must fix - code quality
    WARNING = "warning"  # Should fix - best practice
    INFO = "info"  # Suggestion - optional


class ReviewItemStatus(Enum):
    """Status of a review item."""

    OPEN = "open"  # Not yet addressed
    FIXED = "fixed"  # Fixed by coding agent
    VERIFIED = "verified"  # Fix verified by reviewer
    REJECTED = "rejected"  # Fix rejected, needs rework


class ReviewItemCategory(Enum):
    """Category of review item."""

    SECURITY = "security"  # OWASP, secrets, injection
    LINT = "lint"  # Code style, type hints
    PRACTICE = "practice"  # Best practices, SOLID
    DOCS = "docs"  # Documentation issues
    TEST = "test"  # Test coverage, test quality
    PERFORMANCE = "performance"  # Performance issues
    COMPLEXITY = "complexity"  # Code complexity


@dataclass
class ReviewItem:
    """A single review item that must be addressed."""

    id: str
    category: ReviewItemCategory
    severity: ReviewItemSeverity
    file_path: str
    line_number: int | None
    description: str
    suggested_fix: str | None = None
    status: ReviewItemStatus = ReviewItemStatus.OPEN
    fix_commit: str | None = None
    fix_description: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    fixed_at: datetime | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "status": self.status.value,
            "fix_commit": self.fix_commit,
            "fix_description": self.fix_description,
            "created_at": self.created_at.isoformat(),
            "fixed_at": self.fixed_at.isoformat() if self.fixed_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "rejection_reason": self.rejection_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            category=ReviewItemCategory(data["category"]),
            severity=ReviewItemSeverity(data["severity"]),
            file_path=data["file_path"],
            line_number=data.get("line_number"),
            description=data["description"],
            suggested_fix=data.get("suggested_fix"),
            status=ReviewItemStatus(data.get("status", "open")),
            fix_commit=data.get("fix_commit"),
            fix_description=data.get("fix_description"),
            created_at=datetime.fromisoformat(data["created_at"]),
            fixed_at=(
                datetime.fromisoformat(data["fixed_at"]) if data.get("fixed_at") else None
            ),
            verified_at=(
                datetime.fromisoformat(data["verified_at"]) if data.get("verified_at") else None
            ),
            rejection_reason=data.get("rejection_reason"),
        )

    @property
    def must_fix(self) -> bool:
        """Check if this item must be fixed (not optional)."""
        return self.severity in (ReviewItemSeverity.CRITICAL, ReviewItemSeverity.ERROR)


@dataclass
class ReviewCycle:
    """A complete review cycle."""

    id: str
    module: str
    coding_agent_id: str
    review_agent_id: str | None = None
    items: list[ReviewItem] = field(default_factory=list)
    cycle_number: int = 1
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    is_approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "module": self.module,
            "coding_agent_id": self.coding_agent_id,
            "review_agent_id": self.review_agent_id,
            "items": [item.to_dict() for item in self.items],
            "cycle_number": self.cycle_number,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_approved": self.is_approved,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewCycle":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            module=data["module"],
            coding_agent_id=data["coding_agent_id"],
            review_agent_id=data.get("review_agent_id"),
            items=[ReviewItem.from_dict(i) for i in data.get("items", [])],
            cycle_number=data.get("cycle_number", 1),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            is_approved=data.get("is_approved", False),
        )

    @property
    def open_must_fix_items(self) -> list[ReviewItem]:
        """Get all open must-fix items."""
        return [
            item
            for item in self.items
            if item.must_fix and item.status == ReviewItemStatus.OPEN
        ]

    @property
    def pending_verification_items(self) -> list[ReviewItem]:
        """Get items waiting for verification."""
        return [item for item in self.items if item.status == ReviewItemStatus.FIXED]

    @property
    def rejected_items(self) -> list[ReviewItem]:
        """Get rejected items that need rework."""
        return [item for item in self.items if item.status == ReviewItemStatus.REJECTED]

    def has_open_items(self) -> bool:
        """Check if there are any open must-fix items."""
        return len(self.open_must_fix_items) > 0 or len(self.rejected_items) > 0


class ReviewLoopManager:
    """Manages the review-fix loop.

    This ensures:
    1. All review items are tracked
    2. Coding agent fixes ALL must-fix items
    3. Fixes are verified by review agent
    4. Loop continues until approval
    """

    def __init__(
        self,
        project_root: Path | None = None,
        state_file: str = ".beyond_ralph_review_loop.json",
    ):
        """Initialize the review loop manager.

        Args:
            project_root: Root directory of the project.
            state_file: File to store review state.
        """
        self.project_root = project_root or Path.cwd()
        self.state_file = self.project_root / state_file
        self._cycles: dict[str, ReviewCycle] = {}
        self._active_cycle: str | None = None
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._cycles = {
                    k: ReviewCycle.from_dict(v) for k, v in data.get("cycles", {}).items()
                }
                self._active_cycle = data.get("active_cycle")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load review loop state: {e}")
                self._cycles = {}
                self._active_cycle = None

    def _save_state(self) -> None:
        """Save state to file."""
        data = {
            "cycles": {k: v.to_dict() for k, v in self._cycles.items()},
            "active_cycle": self._active_cycle,
            "updated_at": datetime.now().isoformat(),
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        import uuid

        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def start_review_cycle(
        self,
        module: str,
        coding_agent_id: str,
    ) -> ReviewCycle:
        """Start a new review cycle for a module.

        Args:
            module: Module being reviewed.
            coding_agent_id: ID of the coding agent.

        Returns:
            The new ReviewCycle.
        """
        # Find the latest cycle number for this module
        existing_cycles = [c for c in self._cycles.values() if c.module == module]
        cycle_num = max((c.cycle_number for c in existing_cycles), default=0) + 1

        cycle_id = self._generate_id("review")
        cycle = ReviewCycle(
            id=cycle_id,
            module=module,
            coding_agent_id=coding_agent_id,
            cycle_number=cycle_num,
        )

        self._cycles[cycle_id] = cycle
        self._active_cycle = cycle_id
        self._save_state()

        logger.info(f"[REVIEW-LOOP] Started review cycle {cycle_num} for module {module}")
        return cycle

    def add_review_items(
        self,
        cycle_id: str,
        items: list[dict[str, Any]],
        review_agent_id: str,
    ) -> int:
        """Add review items from the code review agent.

        Args:
            cycle_id: ID of the review cycle.
            items: List of review item dicts with category, severity, etc.
            review_agent_id: ID of the review agent.

        Returns:
            Number of items added.
        """
        if cycle_id not in self._cycles:
            raise ValueError(f"Unknown review cycle: {cycle_id}")

        cycle = self._cycles[cycle_id]
        cycle.review_agent_id = review_agent_id

        for item_data in items:
            item_id = self._generate_id("item")
            item = ReviewItem(
                id=item_id,
                category=ReviewItemCategory(item_data["category"]),
                severity=ReviewItemSeverity(item_data["severity"]),
                file_path=item_data["file_path"],
                line_number=item_data.get("line_number"),
                description=item_data["description"],
                suggested_fix=item_data.get("suggested_fix"),
            )
            cycle.items.append(item)

        self._save_state()

        must_fix_count = len([i for i in cycle.items if i.must_fix])
        logger.info(
            f"[REVIEW-LOOP] Added {len(items)} review items to cycle {cycle_id} "
            f"({must_fix_count} must-fix)"
        )
        return len(items)

    def get_items_for_coding_agent(self, cycle_id: str) -> list[ReviewItem]:
        """Get items that the coding agent must fix.

        This returns:
        1. All open must-fix items
        2. All rejected items (need rework)

        Args:
            cycle_id: ID of the review cycle.

        Returns:
            List of items to fix.
        """
        if cycle_id not in self._cycles:
            return []

        cycle = self._cycles[cycle_id]
        items_to_fix = cycle.open_must_fix_items + cycle.rejected_items

        # Sort by severity (critical first)
        severity_order = {
            ReviewItemSeverity.CRITICAL: 0,
            ReviewItemSeverity.ERROR: 1,
            ReviewItemSeverity.WARNING: 2,
            ReviewItemSeverity.INFO: 3,
        }
        items_to_fix.sort(key=lambda i: severity_order[i.severity])

        return items_to_fix

    def mark_item_fixed(
        self,
        cycle_id: str,
        item_id: str,
        fix_description: str,
        fix_commit: str | None = None,
    ) -> bool:
        """Mark a review item as fixed by the coding agent.

        Args:
            cycle_id: ID of the review cycle.
            item_id: ID of the review item.
            fix_description: Description of the fix.
            fix_commit: Git commit with the fix.

        Returns:
            True if marked successfully.
        """
        if cycle_id not in self._cycles:
            return False

        cycle = self._cycles[cycle_id]
        for item in cycle.items:
            if item.id == item_id:
                item.status = ReviewItemStatus.FIXED
                item.fix_description = fix_description
                item.fix_commit = fix_commit
                item.fixed_at = datetime.now()
                self._save_state()
                logger.info(f"[REVIEW-LOOP] Item {item_id} marked as FIXED")
                return True

        return False

    def verify_fix(self, cycle_id: str, item_id: str, approved: bool, reason: str | None = None) -> bool:
        """Verify a fix (by review agent).

        Args:
            cycle_id: ID of the review cycle.
            item_id: ID of the review item.
            approved: Whether the fix is approved.
            reason: Rejection reason if not approved.

        Returns:
            True if updated successfully.
        """
        if cycle_id not in self._cycles:
            return False

        cycle = self._cycles[cycle_id]
        for item in cycle.items:
            if item.id == item_id:
                if approved:
                    item.status = ReviewItemStatus.VERIFIED
                    item.verified_at = datetime.now()
                    logger.info(f"[REVIEW-LOOP] Item {item_id} fix VERIFIED")
                else:
                    item.status = ReviewItemStatus.REJECTED
                    item.rejection_reason = reason
                    item.fixed_at = None  # Reset
                    logger.warning(f"[REVIEW-LOOP] Item {item_id} fix REJECTED: {reason}")
                self._save_state()
                return True

        return False

    def is_cycle_complete(self, cycle_id: str) -> bool:
        """Check if a review cycle is complete (all items resolved).

        A cycle is complete when:
        - All must-fix items are VERIFIED
        - No items are REJECTED

        Args:
            cycle_id: ID of the review cycle.

        Returns:
            True if cycle is complete.
        """
        if cycle_id not in self._cycles:
            return False

        cycle = self._cycles[cycle_id]

        # Check for any open or rejected must-fix items
        for item in cycle.items:
            if item.must_fix:
                if item.status in (ReviewItemStatus.OPEN, ReviewItemStatus.REJECTED):
                    return False
                if item.status == ReviewItemStatus.FIXED:
                    # Still waiting for verification
                    return False

        return True

    def approve_cycle(self, cycle_id: str) -> bool:
        """Mark a review cycle as approved.

        Only call this when is_cycle_complete returns True.

        Args:
            cycle_id: ID of the review cycle.

        Returns:
            True if approved successfully.
        """
        if cycle_id not in self._cycles:
            return False

        if not self.is_cycle_complete(cycle_id):
            logger.error(f"[REVIEW-LOOP] Cannot approve cycle {cycle_id}: incomplete")
            return False

        cycle = self._cycles[cycle_id]
        cycle.is_approved = True
        cycle.completed_at = datetime.now()
        self._save_state()

        logger.info(f"[REVIEW-LOOP] Review cycle {cycle_id} APPROVED")
        return True

    def generate_fix_prompt(self, cycle_id: str) -> str:
        """Generate a prompt for the coding agent to fix items.

        This creates a detailed prompt listing all items that
        MUST be fixed. The coding agent cannot dismiss any of these.

        Args:
            cycle_id: ID of the review cycle.

        Returns:
            Prompt string for the coding agent.
        """
        items = self.get_items_for_coding_agent(cycle_id)
        if not items:
            return ""

        lines = [
            "# MANDATORY CODE REVIEW FIXES",
            "",
            "You MUST fix ALL of the following items. You CANNOT dismiss or argue",
            "against any of these items. After fixing, describe what you did for each.",
            "",
        ]

        for i, item in enumerate(items, 1):
            status = "REJECTED - REWORK NEEDED" if item.status == ReviewItemStatus.REJECTED else "OPEN"
            lines.append(f"## Item {i}: [{item.severity.value.upper()}] [{item.category.value}]")
            lines.append(f"**File**: {item.file_path}")
            if item.line_number:
                lines.append(f"**Line**: {item.line_number}")
            lines.append(f"**Status**: {status}")
            lines.append(f"**Description**: {item.description}")
            if item.suggested_fix:
                lines.append(f"**Suggested Fix**: {item.suggested_fix}")
            if item.rejection_reason:
                lines.append(f"**Rejection Reason**: {item.rejection_reason}")
            lines.append(f"**Item ID**: {item.id}")
            lines.append("")

        lines.append("---")
        lines.append("After fixing ALL items, report back with:")
        lines.append("1. Item ID")
        lines.append("2. What you changed")
        lines.append("3. The git commit (if applicable)")
        lines.append("")
        lines.append("DO NOT skip any items. ALL must be addressed.")

        return "\n".join(lines)

    def get_cycle_status(self, cycle_id: str) -> dict[str, Any]:
        """Get detailed status of a review cycle.

        Args:
            cycle_id: ID of the review cycle.

        Returns:
            Status dictionary.
        """
        if cycle_id not in self._cycles:
            return {"error": "Unknown cycle"}

        cycle = self._cycles[cycle_id]

        return {
            "id": cycle.id,
            "module": cycle.module,
            "cycle_number": cycle.cycle_number,
            "is_approved": cycle.is_approved,
            "total_items": len(cycle.items),
            "must_fix_items": len([i for i in cycle.items if i.must_fix]),
            "open_items": len(cycle.open_must_fix_items),
            "fixed_pending_verification": len(cycle.pending_verification_items),
            "rejected_items": len(cycle.rejected_items),
            "verified_items": len(
                [i for i in cycle.items if i.status == ReviewItemStatus.VERIFIED]
            ),
            "is_complete": self.is_cycle_complete(cycle_id),
        }

    def get_active_cycle(self) -> ReviewCycle | None:
        """Get the currently active review cycle.

        Returns:
            Active ReviewCycle or None.
        """
        if self._active_cycle and self._active_cycle in self._cycles:
            return self._cycles[self._active_cycle]
        return None


# Singleton instance
_review_manager: ReviewLoopManager | None = None


def get_review_loop_manager(project_root: Path | None = None) -> ReviewLoopManager:
    """Get the review loop manager singleton.

    Args:
        project_root: Project root directory.

    Returns:
        The ReviewLoopManager instance.
    """
    global _review_manager
    if _review_manager is None:
        _review_manager = ReviewLoopManager(project_root=project_root)
    return _review_manager
