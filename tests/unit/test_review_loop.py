"""Tests for Review-Fix Loop Manager."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.review_loop import (
    ReviewCycle,
    ReviewItem,
    ReviewItemCategory,
    ReviewItemSeverity,
    ReviewItemStatus,
    ReviewLoopManager,
    get_review_loop_manager,
)


class TestReviewItem:
    """Tests for ReviewItem dataclass."""

    def test_review_item_creation(self):
        """Test creating a review item."""
        item = ReviewItem(
            id="item-123",
            category=ReviewItemCategory.SECURITY,
            severity=ReviewItemSeverity.CRITICAL,
            file_path="src/main.py",
            line_number=42,
            description="SQL injection vulnerability",
        )

        assert item.id == "item-123"
        assert item.category == ReviewItemCategory.SECURITY
        assert item.severity == ReviewItemSeverity.CRITICAL
        assert item.status == ReviewItemStatus.OPEN

    def test_review_item_must_fix_critical(self):
        """Test critical items must be fixed."""
        item = ReviewItem(
            id="item-1",
            category=ReviewItemCategory.SECURITY,
            severity=ReviewItemSeverity.CRITICAL,
            file_path="test.py",
            line_number=1,
            description="Critical issue",
        )

        assert item.must_fix is True

    def test_review_item_must_fix_error(self):
        """Test error items must be fixed."""
        item = ReviewItem(
            id="item-2",
            category=ReviewItemCategory.LINT,
            severity=ReviewItemSeverity.ERROR,
            file_path="test.py",
            line_number=1,
            description="Lint error",
        )

        assert item.must_fix is True

    def test_review_item_optional_warning(self):
        """Test warning items are optional."""
        item = ReviewItem(
            id="item-3",
            category=ReviewItemCategory.PRACTICE,
            severity=ReviewItemSeverity.WARNING,
            file_path="test.py",
            line_number=1,
            description="Best practice suggestion",
        )

        assert item.must_fix is False

    def test_review_item_optional_info(self):
        """Test info items are optional."""
        item = ReviewItem(
            id="item-4",
            category=ReviewItemCategory.DOCS,
            severity=ReviewItemSeverity.INFO,
            file_path="test.py",
            line_number=1,
            description="Documentation suggestion",
        )

        assert item.must_fix is False

    def test_review_item_to_dict(self):
        """Test serialization."""
        item = ReviewItem(
            id="item-5",
            category=ReviewItemCategory.SECURITY,
            severity=ReviewItemSeverity.CRITICAL,
            file_path="src/auth.py",
            line_number=100,
            description="Hardcoded password",
            suggested_fix="Use environment variable",
        )

        data = item.to_dict()

        assert data["id"] == "item-5"
        assert data["category"] == "security"
        assert data["severity"] == "critical"
        assert data["status"] == "open"
        assert data["suggested_fix"] == "Use environment variable"

    def test_review_item_from_dict(self):
        """Test deserialization."""
        data = {
            "id": "item-6",
            "category": "lint",
            "severity": "error",
            "file_path": "src/utils.py",
            "line_number": 50,
            "description": "Missing type hint",
            "status": "fixed",
            "created_at": datetime.now().isoformat(),
        }

        item = ReviewItem.from_dict(data)

        assert item.id == "item-6"
        assert item.category == ReviewItemCategory.LINT
        assert item.severity == ReviewItemSeverity.ERROR
        assert item.status == ReviewItemStatus.FIXED


class TestReviewCycle:
    """Tests for ReviewCycle dataclass."""

    def test_review_cycle_creation(self):
        """Test creating a review cycle."""
        cycle = ReviewCycle(
            id="cycle-123",
            module="auth",
            coding_agent_id="agent-abc",
        )

        assert cycle.id == "cycle-123"
        assert cycle.cycle_number == 1
        assert cycle.is_approved is False

    def test_review_cycle_open_must_fix_items(self):
        """Test getting open must-fix items."""
        cycle = ReviewCycle(
            id="cycle-1",
            module="test",
            coding_agent_id="agent-1",
        )
        cycle.items = [
            ReviewItem(
                id="i1",
                category=ReviewItemCategory.SECURITY,
                severity=ReviewItemSeverity.CRITICAL,
                file_path="a.py",
                line_number=1,
                description="Critical",
            ),
            ReviewItem(
                id="i2",
                category=ReviewItemCategory.LINT,
                severity=ReviewItemSeverity.WARNING,
                file_path="b.py",
                line_number=1,
                description="Warning",
            ),
        ]

        assert len(cycle.open_must_fix_items) == 1
        assert cycle.open_must_fix_items[0].id == "i1"

    def test_review_cycle_has_open_items(self):
        """Test checking for open items."""
        cycle = ReviewCycle(
            id="cycle-2",
            module="test",
            coding_agent_id="agent-1",
        )
        cycle.items = [
            ReviewItem(
                id="i1",
                category=ReviewItemCategory.SECURITY,
                severity=ReviewItemSeverity.CRITICAL,
                file_path="a.py",
                line_number=1,
                description="Critical",
            ),
        ]

        assert cycle.has_open_items() is True

    def test_review_cycle_no_open_items(self):
        """Test no open items when all verified."""
        cycle = ReviewCycle(
            id="cycle-3",
            module="test",
            coding_agent_id="agent-1",
        )
        item = ReviewItem(
            id="i1",
            category=ReviewItemCategory.SECURITY,
            severity=ReviewItemSeverity.CRITICAL,
            file_path="a.py",
            line_number=1,
            description="Critical",
        )
        item.status = ReviewItemStatus.VERIFIED
        cycle.items = [item]

        assert cycle.has_open_items() is False

    def test_review_cycle_to_dict(self):
        """Test serialization."""
        cycle = ReviewCycle(
            id="cycle-4",
            module="auth",
            coding_agent_id="agent-1",
            review_agent_id="agent-2",
        )

        data = cycle.to_dict()

        assert data["id"] == "cycle-4"
        assert data["module"] == "auth"
        assert data["is_approved"] is False


class TestReviewLoopManager:
    """Tests for ReviewLoopManager."""

    @pytest.fixture
    def loop_manager(self, tmp_path):
        """Create a loop manager for testing."""
        return ReviewLoopManager(project_root=tmp_path)

    def test_start_review_cycle(self, loop_manager):
        """Test starting a review cycle."""
        cycle = loop_manager.start_review_cycle(
            module="auth",
            coding_agent_id="agent-123",
        )

        assert cycle.id.startswith("review-")
        assert cycle.module == "auth"
        assert cycle.cycle_number == 1

    def test_start_multiple_review_cycles(self, loop_manager):
        """Test cycle numbers increment."""
        cycle1 = loop_manager.start_review_cycle(module="auth", coding_agent_id="a1")
        cycle2 = loop_manager.start_review_cycle(module="auth", coding_agent_id="a2")

        assert cycle1.cycle_number == 1
        assert cycle2.cycle_number == 2

    def test_add_review_items(self, loop_manager):
        """Test adding review items."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")

        items = [
            {
                "category": "security",
                "severity": "critical",
                "file_path": "src/main.py",
                "line_number": 42,
                "description": "SQL injection",
            },
            {
                "category": "lint",
                "severity": "error",
                "file_path": "src/utils.py",
                "line_number": 10,
                "description": "Missing type hint",
            },
        ]

        count = loop_manager.add_review_items(cycle.id, items, "reviewer-1")

        assert count == 2
        assert len(loop_manager._cycles[cycle.id].items) == 2
        assert loop_manager._cycles[cycle.id].review_agent_id == "reviewer-1"

    def test_get_items_for_coding_agent(self, loop_manager):
        """Test getting items for coding agent to fix."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Critical issue",
                },
                {
                    "category": "lint",
                    "severity": "warning",
                    "file_path": "b.py",
                    "line_number": 1,
                    "description": "Warning",
                },
            ],
            "reviewer",
        )

        items = loop_manager.get_items_for_coding_agent(cycle.id)

        # Only critical (must-fix) item should be returned
        assert len(items) == 1
        assert items[0].severity == ReviewItemSeverity.CRITICAL

    def test_mark_item_fixed(self, loop_manager):
        """Test marking an item as fixed."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )
        item_id = loop_manager._cycles[cycle.id].items[0].id

        result = loop_manager.mark_item_fixed(
            cycle.id,
            item_id,
            fix_description="Used parameterized queries",
            fix_commit="abc123",
        )

        assert result is True
        item = loop_manager._cycles[cycle.id].items[0]
        assert item.status == ReviewItemStatus.FIXED
        assert item.fix_description == "Used parameterized queries"
        assert item.fix_commit == "abc123"

    def test_verify_fix_approved(self, loop_manager):
        """Test verifying a fix (approved)."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )
        item_id = loop_manager._cycles[cycle.id].items[0].id
        loop_manager.mark_item_fixed(cycle.id, item_id, "Fixed it")

        result = loop_manager.verify_fix(cycle.id, item_id, approved=True)

        assert result is True
        item = loop_manager._cycles[cycle.id].items[0]
        assert item.status == ReviewItemStatus.VERIFIED

    def test_verify_fix_rejected(self, loop_manager):
        """Test verifying a fix (rejected)."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )
        item_id = loop_manager._cycles[cycle.id].items[0].id
        loop_manager.mark_item_fixed(cycle.id, item_id, "Attempted fix")

        result = loop_manager.verify_fix(
            cycle.id, item_id, approved=False, reason="Fix incomplete"
        )

        assert result is True
        item = loop_manager._cycles[cycle.id].items[0]
        assert item.status == ReviewItemStatus.REJECTED
        assert item.rejection_reason == "Fix incomplete"

    def test_is_cycle_complete_all_verified(self, loop_manager):
        """Test cycle is complete when all must-fix verified."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )
        item_id = loop_manager._cycles[cycle.id].items[0].id
        loop_manager.mark_item_fixed(cycle.id, item_id, "Fixed")
        loop_manager.verify_fix(cycle.id, item_id, approved=True)

        assert loop_manager.is_cycle_complete(cycle.id) is True

    def test_is_cycle_not_complete_open_items(self, loop_manager):
        """Test cycle is not complete with open items."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )

        assert loop_manager.is_cycle_complete(cycle.id) is False

    def test_is_cycle_not_complete_pending_verification(self, loop_manager):
        """Test cycle is not complete with pending verification."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )
        item_id = loop_manager._cycles[cycle.id].items[0].id
        loop_manager.mark_item_fixed(cycle.id, item_id, "Fixed")

        assert loop_manager.is_cycle_complete(cycle.id) is False

    def test_approve_cycle(self, loop_manager):
        """Test approving a complete cycle."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )
        item_id = loop_manager._cycles[cycle.id].items[0].id
        loop_manager.mark_item_fixed(cycle.id, item_id, "Fixed")
        loop_manager.verify_fix(cycle.id, item_id, approved=True)

        result = loop_manager.approve_cycle(cycle.id)

        assert result is True
        assert loop_manager._cycles[cycle.id].is_approved is True

    def test_approve_cycle_fails_if_incomplete(self, loop_manager):
        """Test approving incomplete cycle fails."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )

        result = loop_manager.approve_cycle(cycle.id)

        assert result is False

    def test_generate_fix_prompt(self, loop_manager):
        """Test generating fix prompt for coding agent."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "src/auth.py",
                    "line_number": 42,
                    "description": "SQL injection vulnerability",
                    "suggested_fix": "Use parameterized queries",
                },
            ],
            "reviewer",
        )

        prompt = loop_manager.generate_fix_prompt(cycle.id)

        assert "MANDATORY CODE REVIEW FIXES" in prompt
        assert "src/auth.py" in prompt
        assert "SQL injection" in prompt
        assert "parameterized queries" in prompt
        assert "CANNOT dismiss" in prompt

    def test_generate_fix_prompt_includes_rejected(self, loop_manager):
        """Test fix prompt includes rejected items."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue",
                },
            ],
            "reviewer",
        )
        item_id = loop_manager._cycles[cycle.id].items[0].id
        loop_manager.mark_item_fixed(cycle.id, item_id, "Bad fix")
        loop_manager.verify_fix(cycle.id, item_id, approved=False, reason="Incomplete")

        prompt = loop_manager.generate_fix_prompt(cycle.id)

        assert "REJECTED" in prompt
        assert "REWORK" in prompt
        assert "Incomplete" in prompt

    def test_get_cycle_status(self, loop_manager):
        """Test getting cycle status."""
        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Issue 1",
                },
                {
                    "category": "lint",
                    "severity": "error",
                    "file_path": "b.py",
                    "line_number": 1,
                    "description": "Issue 2",
                },
            ],
            "reviewer",
        )

        status = loop_manager.get_cycle_status(cycle.id)

        assert status["total_items"] == 2
        assert status["must_fix_items"] == 2
        assert status["open_items"] == 2
        assert status["is_complete"] is False

    def test_get_active_cycle(self, loop_manager):
        """Test getting active cycle."""
        assert loop_manager.get_active_cycle() is None

        cycle = loop_manager.start_review_cycle(module="test", coding_agent_id="agent")

        active = loop_manager.get_active_cycle()
        assert active is not None
        assert active.id == cycle.id

    def test_state_persistence(self, tmp_path):
        """Test state persists across instances."""
        manager1 = ReviewLoopManager(project_root=tmp_path)
        cycle = manager1.start_review_cycle(module="test", coding_agent_id="agent")
        manager1.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "a.py",
                    "line_number": 1,
                    "description": "Persistent issue",
                },
            ],
            "reviewer",
        )

        manager2 = ReviewLoopManager(project_root=tmp_path)

        assert cycle.id in manager2._cycles
        assert len(manager2._cycles[cycle.id].items) == 1
        assert manager2._cycles[cycle.id].items[0].description == "Persistent issue"


class TestGetReviewLoopManager:
    """Tests for singleton getter."""

    def test_get_review_loop_manager_singleton(self, tmp_path, monkeypatch):
        """Test singleton pattern."""
        import beyond_ralph.core.review_loop as module

        module._review_manager = None

        manager1 = get_review_loop_manager(tmp_path)
        manager2 = get_review_loop_manager(tmp_path)

        assert manager1 is manager2

        module._review_manager = None


class TestReviewLoopFullWorkflow:
    """Integration tests for full review-fix workflow."""

    @pytest.fixture
    def loop_manager(self, tmp_path):
        """Create a loop manager for testing."""
        return ReviewLoopManager(project_root=tmp_path)

    def test_full_review_fix_verify_cycle(self, loop_manager):
        """Test complete review-fix-verify workflow."""
        # 1. Start cycle
        cycle = loop_manager.start_review_cycle(module="auth", coding_agent_id="coder-1")

        # 2. Review agent adds items
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "src/auth.py",
                    "line_number": 42,
                    "description": "SQL injection in login",
                },
                {
                    "category": "lint",
                    "severity": "error",
                    "file_path": "src/auth.py",
                    "line_number": 50,
                    "description": "Missing type hints",
                },
            ],
            "reviewer-1",
        )

        # Verify not complete
        assert loop_manager.is_cycle_complete(cycle.id) is False

        # 3. Coding agent gets items to fix
        items_to_fix = loop_manager.get_items_for_coding_agent(cycle.id)
        assert len(items_to_fix) == 2

        # 4. Coding agent fixes items
        for item in items_to_fix:
            loop_manager.mark_item_fixed(cycle.id, item.id, f"Fixed {item.description}")

        # Still not complete - pending verification
        assert loop_manager.is_cycle_complete(cycle.id) is False

        # 5. Review agent verifies fixes
        for item in loop_manager._cycles[cycle.id].items:
            loop_manager.verify_fix(cycle.id, item.id, approved=True)

        # Now complete
        assert loop_manager.is_cycle_complete(cycle.id) is True

        # 6. Approve cycle
        result = loop_manager.approve_cycle(cycle.id)
        assert result is True
        assert loop_manager._cycles[cycle.id].is_approved is True

    def test_review_fix_rejection_rework_cycle(self, loop_manager):
        """Test workflow with rejected fix requiring rework."""
        # 1. Start cycle
        cycle = loop_manager.start_review_cycle(module="api", coding_agent_id="coder-1")

        # 2. Add item
        loop_manager.add_review_items(
            cycle.id,
            [
                {
                    "category": "security",
                    "severity": "critical",
                    "file_path": "src/api.py",
                    "line_number": 100,
                    "description": "Hardcoded API key",
                },
            ],
            "reviewer-1",
        )

        item_id = loop_manager._cycles[cycle.id].items[0].id

        # 3. First fix attempt
        loop_manager.mark_item_fixed(cycle.id, item_id, "Moved to config file")

        # 4. Fix rejected
        loop_manager.verify_fix(
            cycle.id, item_id, approved=False, reason="Config file is still committed"
        )

        # Not complete - has rejected item
        assert loop_manager.is_cycle_complete(cycle.id) is False

        # Rejected item appears in coding agent's list
        items = loop_manager.get_items_for_coding_agent(cycle.id)
        assert len(items) == 1
        assert items[0].status == ReviewItemStatus.REJECTED

        # 5. Second fix attempt
        loop_manager.mark_item_fixed(cycle.id, item_id, "Using environment variable")

        # 6. Fix approved
        loop_manager.verify_fix(cycle.id, item_id, approved=True)

        # Now complete
        assert loop_manager.is_cycle_complete(cycle.id) is True
