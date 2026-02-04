"""Tests for Dynamic Project Plan Manager."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.dynamic_plan import (
    Discrepancy,
    DynamicPlanManager,
    ModuleRequirement,
    RequirementPriority,
    RequirementStatus,
    get_dynamic_plan_manager,
)


class TestModuleRequirement:
    """Tests for ModuleRequirement dataclass."""

    def test_requirement_creation(self):
        """Test creating a requirement."""
        req = ModuleRequirement(
            id="req-123",
            requesting_module="auth",
            providing_module="database",
            description="Need a connection pool",
            technical_spec="def get_pool() -> ConnectionPool",
        )

        assert req.id == "req-123"
        assert req.requesting_module == "auth"
        assert req.providing_module == "database"
        assert req.status == RequirementStatus.PENDING
        assert req.priority == RequirementPriority.NORMAL

    def test_requirement_to_dict(self):
        """Test serialization to dict."""
        req = ModuleRequirement(
            id="req-456",
            requesting_module="api",
            providing_module="cache",
            description="Need cache interface",
            technical_spec="class Cache: ...",
            priority=RequirementPriority.HIGH,
        )

        data = req.to_dict()

        assert data["id"] == "req-456"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        assert "created_at" in data

    def test_requirement_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "id": "req-789",
            "requesting_module": "ui",
            "providing_module": "api",
            "description": "Need user endpoint",
            "technical_spec": "GET /users/{id}",
            "priority": "critical",
            "status": "delivered",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        req = ModuleRequirement.from_dict(data)

        assert req.id == "req-789"
        assert req.priority == RequirementPriority.CRITICAL
        assert req.status == RequirementStatus.DELIVERED


class TestDiscrepancy:
    """Tests for Discrepancy dataclass."""

    def test_discrepancy_creation(self):
        """Test creating a discrepancy."""
        disc = Discrepancy(
            id="disc-123",
            module="auth",
            requirement_id="req-456",
            expected="Returns User object",
            actual="Returns dict",
            severity="major",
            reported_by="auth-agent",
        )

        assert disc.id == "disc-123"
        assert disc.severity == "major"
        assert disc.resolved is False

    def test_discrepancy_to_dict(self):
        """Test serialization."""
        disc = Discrepancy(
            id="disc-456",
            module="api",
            requirement_id="req-789",
            expected="Status 200",
            actual="Status 404",
            severity="critical",
            reported_by="testing-agent",
        )

        data = disc.to_dict()

        assert data["id"] == "disc-456"
        assert data["severity"] == "critical"
        assert data["resolved"] is False

    def test_discrepancy_from_dict(self):
        """Test deserialization."""
        data = {
            "id": "disc-789",
            "module": "cache",
            "requirement_id": "req-000",
            "expected": "TTL of 300s",
            "actual": "No TTL set",
            "severity": "minor",
            "reported_by": "cache-agent",
            "reported_at": datetime.now().isoformat(),
            "resolved": True,
            "resolution": "Added TTL parameter",
        }

        disc = Discrepancy.from_dict(data)

        assert disc.id == "disc-789"
        assert disc.resolved is True
        assert disc.resolution == "Added TTL parameter"


class TestDynamicPlanManager:
    """Tests for DynamicPlanManager."""

    @pytest.fixture
    def plan_manager(self, tmp_path):
        """Create a plan manager for testing."""
        return DynamicPlanManager(project_root=tmp_path)

    @pytest.fixture
    def plan_manager_with_project_plan(self, tmp_path):
        """Create a plan manager with a PROJECT_PLAN.md file."""
        project_plan = tmp_path / "PROJECT_PLAN.md"
        project_plan.write_text(
            "# Project Plan\n\n## Overview\n\nSome content\n\n## Timeline\n\nTimeline here\n"
        )
        return DynamicPlanManager(project_root=tmp_path)

    def test_add_requirement(self, plan_manager):
        """Test adding a requirement."""
        req = plan_manager.add_requirement(
            requesting_module="auth",
            providing_module="database",
            description="Need connection pool",
            technical_spec="get_connection_pool() -> Pool",
        )

        assert req.id.startswith("req-")
        assert req.status == RequirementStatus.PENDING
        assert req.requesting_module == "auth"

    def test_add_requirement_with_priority(self, plan_manager):
        """Test adding a critical requirement."""
        req = plan_manager.add_requirement(
            requesting_module="api",
            providing_module="auth",
            description="Need authentication check",
            technical_spec="is_authenticated(token: str) -> bool",
            priority=RequirementPriority.CRITICAL,
        )

        assert req.priority == RequirementPriority.CRITICAL

    def test_add_requirement_updates_project_plan(self, plan_manager_with_project_plan, tmp_path):
        """Test that adding a requirement updates PROJECT_PLAN.md."""
        plan_manager_with_project_plan.add_requirement(
            requesting_module="ui",
            providing_module="api",
            description="Need user list endpoint",
            technical_spec="GET /api/users",
        )

        plan_content = (tmp_path / "PROJECT_PLAN.md").read_text()
        assert "Dynamic Module Requirements" in plan_content
        assert "ui → api" in plan_content
        assert "Need user list endpoint" in plan_content

    def test_mark_delivered(self, plan_manager):
        """Test marking a requirement as delivered."""
        req = plan_manager.add_requirement(
            requesting_module="test",
            providing_module="impl",
            description="Test requirement",
            technical_spec="some_function()",
        )

        result = plan_manager.mark_delivered(req.id, evidence_path="/path/to/evidence")

        assert result is True
        assert plan_manager._requirements[req.id].status == RequirementStatus.DELIVERED
        assert plan_manager._requirements[req.id].evidence_path == "/path/to/evidence"

    def test_mark_delivered_unknown_id(self, plan_manager):
        """Test marking unknown requirement as delivered."""
        result = plan_manager.mark_delivered("nonexistent-id")
        assert result is False

    def test_mark_failed(self, plan_manager):
        """Test marking a requirement as failed."""
        req = plan_manager.add_requirement(
            requesting_module="test",
            providing_module="impl",
            description="Test requirement",
            technical_spec="some_function()",
        )

        result = plan_manager.mark_failed(req.id, reason="Not implemented")

        assert result is True
        assert plan_manager._requirements[req.id].status == RequirementStatus.FAILED
        assert plan_manager._requirements[req.id].failure_reason == "Not implemented"

    def test_report_discrepancy(self, plan_manager):
        """Test reporting a discrepancy."""
        req = plan_manager.add_requirement(
            requesting_module="test",
            providing_module="impl",
            description="Test requirement",
            technical_spec="some_function()",
        )

        disc = plan_manager.report_discrepancy(
            module="test",
            requirement_id=req.id,
            expected="Returns int",
            actual="Returns str",
            severity="major",
            reported_by="test-agent",
        )

        assert disc.id.startswith("disc-")
        assert disc.severity == "major"
        assert disc.resolved is False

    def test_resolve_discrepancy(self, plan_manager):
        """Test resolving a discrepancy."""
        disc = plan_manager.report_discrepancy(
            module="test",
            requirement_id="req-123",
            expected="A",
            actual="B",
            severity="minor",
            reported_by="agent",
        )

        result = plan_manager.resolve_discrepancy(disc.id, "Fixed the type")

        assert result is True
        assert plan_manager._discrepancies[disc.id].resolved is True
        assert plan_manager._discrepancies[disc.id].resolution == "Fixed the type"

    def test_get_pending_requirements(self, plan_manager):
        """Test getting pending requirements."""
        plan_manager.add_requirement(
            requesting_module="a",
            providing_module="b",
            description="Req 1",
            technical_spec="spec1",
        )
        plan_manager.add_requirement(
            requesting_module="a",
            providing_module="c",
            description="Req 2",
            technical_spec="spec2",
            priority=RequirementPriority.CRITICAL,
        )

        pending = plan_manager.get_pending_requirements()

        assert len(pending) == 2
        # Critical should be first
        assert pending[0].priority == RequirementPriority.CRITICAL

    def test_get_pending_requirements_for_module(self, plan_manager):
        """Test getting pending requirements for specific module."""
        plan_manager.add_requirement(
            requesting_module="a",
            providing_module="target",
            description="Req for target",
            technical_spec="spec",
        )
        plan_manager.add_requirement(
            requesting_module="a",
            providing_module="other",
            description="Req for other",
            technical_spec="spec",
        )

        pending = plan_manager.get_pending_requirements(for_module="target")

        assert len(pending) == 1
        assert pending[0].providing_module == "target"

    def test_get_unresolved_discrepancies(self, plan_manager):
        """Test getting unresolved discrepancies."""
        disc1 = plan_manager.report_discrepancy(
            module="a",
            requirement_id="req-1",
            expected="x",
            actual="y",
            severity="critical",
            reported_by="agent",
        )
        disc2 = plan_manager.report_discrepancy(
            module="b",
            requirement_id="req-2",
            expected="a",
            actual="b",
            severity="minor",
            reported_by="agent",
        )
        plan_manager.resolve_discrepancy(disc2.id, "Fixed")

        unresolved = plan_manager.get_unresolved_discrepancies()

        assert len(unresolved) == 1
        assert unresolved[0].id == disc1.id

    def test_has_blocking_issues_critical_requirement(self, plan_manager):
        """Test blocking issues with critical pending requirement."""
        plan_manager.add_requirement(
            requesting_module="a",
            providing_module="b",
            description="Critical req",
            technical_spec="spec",
            priority=RequirementPriority.CRITICAL,
        )

        assert plan_manager.has_blocking_issues() is True

    def test_has_blocking_issues_critical_discrepancy(self, plan_manager):
        """Test blocking issues with critical discrepancy."""
        plan_manager.report_discrepancy(
            module="test",
            requirement_id="req-1",
            expected="x",
            actual="y",
            severity="critical",
            reported_by="agent",
        )

        assert plan_manager.has_blocking_issues() is True

    def test_has_no_blocking_issues(self, plan_manager):
        """Test no blocking issues."""
        req = plan_manager.add_requirement(
            requesting_module="a",
            providing_module="b",
            description="Normal req",
            technical_spec="spec",
            priority=RequirementPriority.NORMAL,
        )
        plan_manager.mark_delivered(req.id)

        assert plan_manager.has_blocking_issues() is False

    def test_get_work_for_module(self, plan_manager):
        """Test getting work for a specific module."""
        plan_manager.add_requirement(
            requesting_module="a",
            providing_module="target",
            description="Work 1",
            technical_spec="spec1",
        )
        req2 = plan_manager.add_requirement(
            requesting_module="b",
            providing_module="target",
            description="Work 2",
            technical_spec="spec2",
        )
        plan_manager.mark_delivered(req2.id)

        work = plan_manager.get_work_for_module("target")

        assert len(work) == 1
        assert work[0].description == "Work 1"

    def test_generate_status_report(self, plan_manager):
        """Test generating status report."""
        plan_manager.add_requirement(
            requesting_module="a",
            providing_module="b",
            description="Pending req",
            technical_spec="spec",
        )
        plan_manager.report_discrepancy(
            module="c",
            requirement_id="req-1",
            expected="x",
            actual="y",
            severity="major",
            reported_by="agent",
        )

        report = plan_manager.generate_status_report()

        assert "Dynamic Plan Status Report" in report
        assert "Total Requirements" in report
        assert "Pending" in report
        assert "Unresolved Discrepancies" in report

    def test_state_persistence(self, tmp_path):
        """Test state is persisted across instances."""
        # Create first manager and add data
        manager1 = DynamicPlanManager(project_root=tmp_path)
        req = manager1.add_requirement(
            requesting_module="a",
            providing_module="b",
            description="Persistent req",
            technical_spec="spec",
        )
        req_id = req.id

        # Create second manager from same directory
        manager2 = DynamicPlanManager(project_root=tmp_path)

        assert req_id in manager2._requirements
        assert manager2._requirements[req_id].description == "Persistent req"


class TestGetDynamicPlanManager:
    """Tests for singleton getter."""

    def test_get_dynamic_plan_manager_singleton(self, tmp_path, monkeypatch):
        """Test singleton pattern."""
        # Reset singleton
        import beyond_ralph.core.dynamic_plan as module

        module._plan_manager = None

        manager1 = get_dynamic_plan_manager(tmp_path)
        manager2 = get_dynamic_plan_manager(tmp_path)

        # Same instance
        assert manager1 is manager2

        # Reset for other tests
        module._plan_manager = None
