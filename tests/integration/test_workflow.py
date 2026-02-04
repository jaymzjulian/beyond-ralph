"""Integration tests for Beyond Ralph workflow."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.core.orchestrator import Orchestrator, Phase, OrchestratorState
from beyond_ralph.core.knowledge import KnowledgeBase
from beyond_ralph.agents.phase_agents import (
    SpecAgent,
    PlanningAgent,
    UncertaintyReviewAgent,
    ValidationAgent,
    get_phase_agent,
)


class TestOrchestratorBasics:
    """Tests for basic orchestrator functionality."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create project root with required directories."""
        (tmp_path / ".beyond_ralph").mkdir()
        (tmp_path / "knowledge").mkdir()
        return tmp_path

    @pytest.fixture
    def orchestrator(self, project_root):
        """Create orchestrator instance."""
        return Orchestrator(project_root=project_root)

    def test_orchestrator_exists(self, orchestrator):
        """Test orchestrator can be created."""
        assert orchestrator is not None
        assert hasattr(orchestrator, "phase")
        assert hasattr(orchestrator, "state")

    def test_orchestrator_status_method(self, orchestrator):
        """Test orchestrator has status method."""
        assert hasattr(orchestrator, "status")
        status = orchestrator.status()
        assert status is not None


class TestKnowledgeBaseIntegration:
    """Tests for knowledge base integration."""

    @pytest.fixture
    def kb(self, tmp_path):
        """Create knowledge base instance."""
        kb_dir = tmp_path / "knowledge"
        kb_dir.mkdir()
        return KnowledgeBase(path=kb_dir)

    def test_write_and_search(self, kb):
        """Test writing and searching knowledge."""
        from datetime import datetime
        from beyond_ralph.core.knowledge import KnowledgeEntry

        # Create entry
        entry = KnowledgeEntry(
            uuid="test-123",
            created_by_session="test-session",
            created_at=datetime.now(),
            category="specification",
            tags=["test", "auth"],
            title="Test Entry",
            content="# Test Entry\n\nThis is test content about authentication.",
        )

        # Write entry
        entry_uuid = kb.write(entry)
        assert entry_uuid == "test-123"

        # Search for entry
        results = kb.search("authentication")
        assert len(results) >= 1
        assert "authentication" in results[0].content.lower()

    def test_category_filtering(self, kb):
        """Test filtering by category."""
        from datetime import datetime
        from beyond_ralph.core.knowledge import KnowledgeEntry

        # Write entries in different categories
        spec_entry = KnowledgeEntry(
            uuid="spec-123",
            created_by_session="test-session",
            created_at=datetime.now(),
            category="specification",
            tags=[],
            title="Spec Entry",
            content="# Spec Entry\n\nSpecification content.",
        )
        kb.write(spec_entry)

        decision_entry = KnowledgeEntry(
            uuid="decision-123",
            created_by_session="test-session",
            created_at=datetime.now(),
            category="decisions",
            tags=[],
            title="Decision Entry",
            content="# Decision Entry\n\nDecision content.",
        )
        kb.write(decision_entry)

        # Search with category filter
        specs = kb.search("", category="specification")
        decisions = kb.search("", category="decisions")

        assert len(specs) >= 1
        assert len(decisions) >= 1


class TestPhaseAgentsIntegration:
    """Tests for phase agent integration."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create project root with knowledge dir."""
        (tmp_path / "knowledge").mkdir()
        return tmp_path

    def test_spec_agent_workflow(self, project_root):
        """Test spec agent can analyze a specification."""
        # Create spec file
        spec_file = project_root / "SPEC.md"
        spec_file.write_text("""
# Test Spec

## Requirements
- Feature A
- Feature B
- Feature C

## Questions
What about edge cases?
""")

        agent = SpecAgent(project_root=project_root)

        # Test analysis method directly
        import asyncio
        result = asyncio.run(agent._analyze_spec(spec_file.read_text()))

        assert "requirements" in result
        assert len(result["requirements"]) >= 3
        assert "ambiguities" in result

    def test_planning_agent_workflow(self, project_root):
        """Test planning agent can generate a plan."""
        agent = PlanningAgent(project_root=project_root)

        spec_content = """
# Modular Specification

## Modules

### Module 1
User authentication

### Module 2
API endpoints

### Module 3
Database layer
"""

        plan = agent._generate_plan(spec_content)

        assert "# Project Plan" in plan
        assert "Task 1" in plan
        assert "Task 2" in plan
        assert "Task 3" in plan

    def test_uncertainty_review_workflow(self, project_root):
        """Test uncertainty review agent."""
        agent = UncertaintyReviewAgent(project_root=project_root)

        plan_with_issues = """
# Project Plan

## Task 1
TBD - need to decide

## Task 2
TODO: finish this
"""

        plan_clean = """
# Project Plan

## Tasks
- [ ] Task 1
- [ ] Task 2
"""

        issues = agent._find_uncertainties(plan_with_issues)
        no_issues = agent._find_uncertainties(plan_clean)

        assert len(issues) >= 2
        assert len(no_issues) == 0

    def test_validation_agent_workflow(self, project_root):
        """Test validation agent can validate a plan."""
        agent = ValidationAgent(project_root=project_root)

        valid_plan = """
# Project Plan

## Tasks
- [ ] Task 1
- [ ] Task 2
"""

        invalid_plan = """
# Project Plan

Some content without structure.
"""

        valid_issues = agent._validate_plan(valid_plan)
        invalid_issues = agent._validate_plan(invalid_plan)

        assert len(valid_issues) == 0
        assert len(invalid_issues) >= 1


class TestCompleteWorkflow:
    """Tests for complete workflow from spec to validation."""

    @pytest.fixture
    def setup(self, tmp_path):
        """Set up complete project structure."""
        (tmp_path / ".beyond_ralph").mkdir()
        (tmp_path / "knowledge").mkdir()

        # Create spec
        spec = tmp_path / "SPEC.md"
        spec.write_text("""
# Complete Test Project

## Requirements
- Authentication system
- User management
- API endpoints

## Technologies
- Python
- FastAPI
""")

        return {
            "root": tmp_path,
            "spec": spec,
        }

    def test_spec_to_plan_workflow(self, setup):
        """Test workflow from spec ingestion to planning."""
        root = setup["root"]
        spec = setup["spec"]

        # Phase 1: Spec ingestion
        spec_agent = SpecAgent(project_root=root)
        import asyncio
        analysis = asyncio.run(spec_agent._analyze_spec(spec.read_text()))

        assert len(analysis["requirements"]) >= 3

        # Phase 4: Planning
        planning_agent = PlanningAgent(project_root=root)

        modular_spec = f"""
# Modular Specification

## Modules
{chr(10).join(f'### Module {i+1}{chr(10)}{req}' for i, req in enumerate(analysis['requirements']))}
"""

        plan = planning_agent._generate_plan(modular_spec)

        assert "# Project Plan" in plan
        assert "Task" in plan

        # Phase 5: Uncertainty Review
        review_agent = UncertaintyReviewAgent(project_root=root)
        uncertainties = review_agent._find_uncertainties(plan)

        # Plan generated from clean spec should have no uncertainties
        assert len(uncertainties) == 0

        # Phase 6: Validation
        validation_agent = ValidationAgent(project_root=root)
        issues = validation_agent._validate_plan(plan)

        # Plan should be valid
        assert len(issues) == 0


class TestPhaseAgentRegistry:
    """Tests for phase agent registry."""

    def test_all_phases_have_agents(self):
        """Test all 8 phases have registered agents."""
        for phase in range(1, 9):
            agent_class = get_phase_agent(phase)
            assert agent_class is not None
            assert agent_class.phase == phase

    def test_agents_instantiate(self, tmp_path):
        """Test all agents can be instantiated."""
        (tmp_path / "knowledge").mkdir()

        for phase in range(1, 9):
            agent_class = get_phase_agent(phase)
            agent = agent_class(project_root=tmp_path)
            assert hasattr(agent, "execute")
