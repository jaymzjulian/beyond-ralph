"""Tests for phase agents module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.agents.phase_agents import (
    SpecAgent,
    InterviewAgent,
    SpecCreationAgent,
    PlanningAgent,
    UncertaintyReviewAgent,
    ValidationAgent,
    ImplementationAgent,
    TestingValidationAgent,
    SpecComplianceAgent,
    PHASE_AGENTS,
    SPECIALIZED_AGENTS,
    get_phase_agent,
    get_specialized_agent,
)
from beyond_ralph.agents.base import AgentTask, AgentModel, AgentStatus


class TestSpecAgent:
    """Tests for SpecAgent (Phase 1)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = SpecAgent(project_root=tmp_path)
        assert agent.name == "spec_agent"
        assert agent.phase == 1
        assert agent.model == AgentModel.SONNET
        assert "Read" in agent.tools
        assert "Glob" in agent.tools

    def test_analyze_spec(self, tmp_path):
        """Test spec analysis."""
        import asyncio

        agent = SpecAgent(project_root=tmp_path)
        content = """
# Requirements
- Must handle authentication
- Must support REST API
* Must include logging

# Open Questions
What authentication method?
"""

        result = asyncio.run(agent._analyze_spec(content))

        assert "requirements" in result
        assert len(result["requirements"]) >= 3
        assert "ambiguities" in result
        assert len(result["ambiguities"]) >= 1


class TestInterviewAgent:
    """Tests for InterviewAgent (Phase 2)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = InterviewAgent(project_root=tmp_path)
        assert agent.name == "interview_agent"
        assert agent.phase == 2
        assert agent.model == AgentModel.OPUS  # Most capable for interviews
        assert "AskUserQuestion" in agent.tools


class TestSpecCreationAgent:
    """Tests for SpecCreationAgent (Phase 3)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = SpecCreationAgent(project_root=tmp_path)
        assert agent.name == "spec_creation_agent"
        assert agent.phase == 3
        assert "Write" in agent.tools

    def test_generate_modular_spec(self, tmp_path):
        """Test modular spec generation."""
        agent = SpecCreationAgent(project_root=tmp_path)
        requirements = ["Build REST API", "Add authentication"]
        decisions = ["Use FastAPI", "Use OAuth2"]

        content = agent._generate_modular_spec(requirements, decisions)

        assert "# Modular Specification" in content
        assert "## Modules" in content
        assert "## Decisions" in content
        assert "FastAPI" in content


class TestPlanningAgent:
    """Tests for PlanningAgent (Phase 4)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = PlanningAgent(project_root=tmp_path)
        assert agent.name == "planning_agent"
        assert agent.phase == 4

    def test_generate_plan(self, tmp_path):
        """Test plan generation."""
        agent = PlanningAgent(project_root=tmp_path)

        spec_content = """
# Modular Specification

## Modules

### Module 1
Authentication

### Module 2
API endpoints
"""

        plan = agent._generate_plan(spec_content)

        assert "# Project Plan" in plan
        assert "## Tasks" in plan
        assert "Task 1" in plan
        assert "Task 2" in plan


class TestUncertaintyReviewAgent:
    """Tests for UncertaintyReviewAgent (Phase 5)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = UncertaintyReviewAgent(project_root=tmp_path)
        assert agent.name == "review_agent"
        assert agent.phase == 5

    def test_find_uncertainties(self, tmp_path):
        """Test finding uncertainties."""
        agent = UncertaintyReviewAgent(project_root=tmp_path)

        content = """
# Project Plan

## Task 1
TBD - need to decide on framework

## Task 2
- [ ] Implementation complete
- TODO: Add error handling
"""

        uncertainties = agent._find_uncertainties(content)

        assert len(uncertainties) >= 2
        assert any("TBD" in u for u in uncertainties)
        assert any("TODO" in u for u in uncertainties)

    def test_find_no_uncertainties(self, tmp_path):
        """Test finding no uncertainties."""
        agent = UncertaintyReviewAgent(project_root=tmp_path)

        content = """
# Project Plan

## Tasks
- [ ] Task 1: Implementation
- [ ] Task 2: Testing
"""

        uncertainties = agent._find_uncertainties(content)

        assert len(uncertainties) == 0


class TestValidationAgent:
    """Tests for ValidationAgent (Phase 6)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = ValidationAgent(project_root=tmp_path)
        assert agent.name == "validation_agent"
        assert agent.phase == 6
        assert "Bash" in agent.tools

    def test_validate_valid_plan(self, tmp_path):
        """Test validating valid plan."""
        agent = ValidationAgent(project_root=tmp_path)

        content = """
# Project Plan

## Tasks
- [ ] Task 1
- [ ] Task 2
"""

        issues = agent._validate_plan(content)

        assert len(issues) == 0

    def test_validate_invalid_plan(self, tmp_path):
        """Test validating invalid plan."""
        agent = ValidationAgent(project_root=tmp_path)

        content = """
# Project Plan

Some content without proper structure.
"""

        issues = agent._validate_plan(content)

        assert len(issues) >= 1


class TestImplementationAgent:
    """Tests for ImplementationAgent (Phase 7)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = ImplementationAgent(project_root=tmp_path)
        assert agent.name == "implementation_agent"
        assert agent.phase == 7
        assert agent.can_implement is True
        assert agent.can_test is False
        assert agent.can_review is False
        assert "Write" in agent.tools
        assert "Edit" in agent.tools


class TestTestingValidationAgent:
    """Tests for TestingValidationAgent (Phase 8)."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = TestingValidationAgent(project_root=tmp_path)
        assert agent.name == "testing_agent"
        assert agent.phase == 8
        assert agent.can_implement is False
        assert agent.can_test is True
        assert agent.can_review is False
        assert "Bash" in agent.tools


class TestPhaseAgentsRegistry:
    """Tests for PHASE_AGENTS registry and get_phase_agent."""

    def test_phase_agents_complete(self):
        """Test all 8 phases are registered."""
        assert len(PHASE_AGENTS) == 8
        for i in range(1, 9):
            assert i in PHASE_AGENTS

    def test_get_phase_agent_valid(self):
        """Test getting valid phase agent."""
        for i in range(1, 9):
            agent_class = get_phase_agent(i)
            assert agent_class.phase == i

    def test_get_phase_agent_invalid(self):
        """Test getting invalid phase raises error."""
        with pytest.raises(ValueError) as exc_info:
            get_phase_agent(0)
        assert "Invalid phase" in str(exc_info.value)

        with pytest.raises(ValueError):
            get_phase_agent(9)

    def test_phase_agent_inheritance(self):
        """Test all phase agents inherit properly."""
        from beyond_ralph.agents.base import PhaseAgent

        for agent_class in PHASE_AGENTS.values():
            assert issubclass(agent_class, PhaseAgent)

    def test_phase_agents_instantiate(self, tmp_path):
        """Test all phase agents can be instantiated."""
        for phase, agent_class in PHASE_AGENTS.items():
            agent = agent_class(project_root=tmp_path)
            assert agent.phase == phase
            assert hasattr(agent, "execute")


class TestSpecComplianceAgent:
    """Tests for SpecComplianceAgent - verifies implementation matches spec."""

    def test_agent_properties(self, tmp_path):
        """Test agent properties."""
        agent = SpecComplianceAgent(project_root=tmp_path)
        assert agent.name == "spec_compliance_agent"
        assert agent.description == "Verifies implementation matches specification"
        assert agent.model == AgentModel.OPUS
        assert agent.can_implement is False
        assert agent.can_test is False
        assert agent.can_review is True
        assert "Read" in agent.tools
        assert "Grep" in agent.tools
        assert "Glob" in agent.tools

    def test_agent_is_trust_model_agent(self, tmp_path):
        """Test agent is a TrustModelAgent."""
        from beyond_ralph.agents.base import TrustModelAgent

        agent = SpecComplianceAgent(project_root=tmp_path)
        assert isinstance(agent, TrustModelAgent)

    @pytest.mark.asyncio
    async def test_execute_compliant(self, tmp_path):
        """Test execution with compliant implementation."""
        # Create spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# Feature: User Login
- Must validate email format
- Must check password length >= 8
- Must return JWT token on success
""")

        # Create implementation file
        impl_file = tmp_path / "login.py"
        impl_file.write_text("""
import re

def login(email: str, password: str) -> str:
    '''Login and return JWT token.'''
    # Validate email format
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError("Invalid email format")

    # Check password length >= 8
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    # Return JWT token on success
    return "jwt_token_here"
""")

        agent = SpecComplianceAgent(project_root=tmp_path)
        task = AgentTask(
            id="test-compliance",
            description="Verify login implementation matches spec",
            instructions="Verify the implementation",
            context={
                "spec_path": str(spec_file),
                "implementation_path": str(impl_file),
            },
        )

        result = await agent.execute(task)
        assert result.success is True
        assert result.data.get("compliant") is True

    @pytest.mark.asyncio
    async def test_execute_empty_implementation(self, tmp_path):
        """Test execution with empty implementation (structural non-compliance)."""
        # Create spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# Feature: User Registration
- Must validate username is alphanumeric
- Must send confirmation email
- Must store password as hash
""")

        # Create empty/comment-only implementation (structurally non-compliant)
        impl_file = tmp_path / "register.py"
        impl_file.write_text("""
# This file is empty - TODO implement registration
# No actual code here, just comments
""")

        agent = SpecComplianceAgent(project_root=tmp_path)
        task = AgentTask(
            id="test-non-compliance",
            description="Verify registration implementation matches spec",
            instructions="Verify the implementation",
            context={
                "spec_path": str(spec_file),
                "implementation_path": str(impl_file),
            },
        )

        result = await agent.execute(task)
        # Empty implementations should fail the structural check
        assert result.success is False
        # Check there are issues in the output
        assert "NOT match" in result.output or "issues" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_with_valid_structure(self, tmp_path):
        """Test execution with structurally valid implementation passes.

        Note: The current implementation does structural checks, not semantic.
        Deep semantic analysis requires an LLM agent spawned by the orchestrator.
        """
        # Create spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# Feature: Calculator
- Must add two numbers
- Must validate inputs
""")

        # Create structurally valid implementation
        impl_file = tmp_path / "calc.py"
        impl_file.write_text('''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    if not isinstance(a, int) or not isinstance(b, int):
        raise ValueError("Inputs must be integers")
    return a + b
''')

        agent = SpecComplianceAgent(project_root=tmp_path)
        task = AgentTask(
            id="test-valid-structure",
            description="Verify calculator implementation",
            instructions="Verify the implementation",
            context={
                "spec_path": str(spec_file),
                "implementation_path": str(impl_file),
            },
        )

        result = await agent.execute(task)
        # Structurally valid implementations pass the check
        assert result.success is True
        assert result.data.get("compliant") is True
        # Evidence should include requirements found
        assert result.data.get("evidence") is not None
        assert len(result.data.get("evidence", [])) > 0

    @pytest.mark.asyncio
    async def test_execute_missing_paths(self, tmp_path):
        """Test execution with missing required paths."""
        agent = SpecComplianceAgent(project_root=tmp_path)
        task = AgentTask(
            id="test-missing",
            description="Verify without paths",
            instructions="Verify the implementation",
            context={},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "spec_path" in result.output.lower() or "implementation_path" in result.output.lower()


class TestSpecializedAgentsRegistry:
    """Tests for SPECIALIZED_AGENTS registry and get_specialized_agent."""

    def test_spec_compliance_in_registry(self):
        """Test SpecComplianceAgent is in registry."""
        assert "spec_compliance" in SPECIALIZED_AGENTS
        assert SPECIALIZED_AGENTS["spec_compliance"] is SpecComplianceAgent

    def test_get_specialized_agent_valid(self):
        """Test getting valid specialized agent."""
        agent_class = get_specialized_agent("spec_compliance")
        assert agent_class is SpecComplianceAgent

    def test_get_specialized_agent_invalid(self):
        """Test getting invalid specialized agent raises error."""
        with pytest.raises(ValueError) as exc_info:
            get_specialized_agent("nonexistent_agent")
        assert "Unknown specialized agent" in str(exc_info.value)

    def test_specialized_agents_are_trust_model_agents(self, tmp_path):
        """Test all specialized agents are TrustModelAgents."""
        from beyond_ralph.agents.base import TrustModelAgent

        for name, agent_class in SPECIALIZED_AGENTS.items():
            agent = agent_class(project_root=tmp_path)
            assert isinstance(agent, TrustModelAgent), f"{name} is not a TrustModelAgent"


class TestSpecAgentExecute:
    """Tests for SpecAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_no_spec_path(self, tmp_path):
        """Test execute fails without spec path."""
        agent = SpecAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "No specification path" in result.output

    @pytest.mark.asyncio
    async def test_execute_spec_not_found(self, tmp_path):
        """Test execute fails when spec file not found."""
        agent = SpecAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"spec_path": "nonexistent.md"},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_success(self, tmp_path):
        """Test execute succeeds with valid spec."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# My Project
- Feature 1: Authentication
- Feature 2: API endpoints
What authentication method?
""")

        agent = SpecAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"spec_path": str(spec_file)},
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock):
            result = await agent.execute(task)

        assert result.success is True
        assert "requirements" in result.data
        assert "ambiguities" in result.data

    @pytest.mark.asyncio
    async def test_execute_read_error(self, tmp_path):
        """Test execute handles read errors."""
        agent = SpecAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"spec_path": str(tmp_path)},  # directory, not file
        )

        result = await agent.execute(task)
        assert result.success is False
        # Either "not found" or "Failed to read" depending on path resolution
        assert "not found" in result.output.lower() or "failed" in result.output.lower()


class TestInterviewAgentExecute:
    """Tests for InterviewAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_no_questions(self, tmp_path):
        """Test execute with no questions."""
        agent = InterviewAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"questions": [], "ambiguities": []},
        )

        result = await agent.execute(task)
        assert result.success is True
        assert "No questions needed" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_questions(self, tmp_path):
        """Test execute returns questions."""
        agent = InterviewAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={
                "questions": ["What framework?"],
                "ambiguities": ["Authentication method?"],
            },
        )

        result = await agent.execute(task)
        # return_with_question returns a result with success=False but has question data
        assert result.success is False or "question" in str(result.data).lower() or "pending" in str(result.data).lower()
        assert "Interview in progress" in result.output


class TestSpecCreationAgentExecute:
    """Tests for SpecCreationAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_creates_spec_file(self, tmp_path):
        """Test execute creates modular spec file."""
        agent = SpecCreationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={
                "requirements": ["Build API", "Add auth"],
                "decisions": ["Use FastAPI"],
            },
        )

        result = await agent.execute(task)

        assert result.success is True
        assert (tmp_path / "MODULAR_SPEC.md").exists()
        assert "spec_file" in result.data


class TestPlanningAgentExecute:
    """Tests for PlanningAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_no_spec_file(self, tmp_path):
        """Test execute fails without spec file path."""
        agent = PlanningAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "No specification file" in result.output

    @pytest.mark.asyncio
    async def test_execute_spec_not_found(self, tmp_path):
        """Test execute fails when spec not found."""
        agent = PlanningAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"spec_file": "nonexistent.md"},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_creates_plan(self, tmp_path):
        """Test execute creates project plan."""
        spec_file = tmp_path / "MODULAR_SPEC.md"
        spec_file.write_text("""
### Module 1
Auth

### Module 2
API
""")

        agent = PlanningAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"spec_file": str(spec_file)},
        )

        result = await agent.execute(task)

        assert result.success is True
        assert (tmp_path / "PROJECT_PLAN.md").exists()


class TestUncertaintyReviewAgentExecute:
    """Tests for UncertaintyReviewAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_no_plan_file(self, tmp_path):
        """Test execute fails without plan file path."""
        agent = UncertaintyReviewAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "No plan file" in result.output

    @pytest.mark.asyncio
    async def test_execute_plan_not_found(self, tmp_path):
        """Test execute fails when plan not found."""
        agent = UncertaintyReviewAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"plan_file": "nonexistent.md"},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_with_uncertainties(self, tmp_path):
        """Test execute finds uncertainties."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("TBD need to decide")

        agent = UncertaintyReviewAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"plan_file": str(plan_file)},
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data.get("needs_interview") is True

    @pytest.mark.asyncio
    async def test_execute_no_uncertainties(self, tmp_path):
        """Test execute with no uncertainties."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("- [ ] Task 1\n- [ ] Task 2")

        agent = UncertaintyReviewAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"plan_file": str(plan_file)},
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data.get("needs_interview") is False


class TestValidationAgentExecute:
    """Tests for ValidationAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_no_plan_file(self, tmp_path):
        """Test execute fails without plan file path."""
        agent = ValidationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "No plan file" in result.output

    @pytest.mark.asyncio
    async def test_execute_plan_not_found(self, tmp_path):
        """Test execute fails when plan not found."""
        agent = ValidationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"plan_file": "nonexistent.md"},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_valid_plan(self, tmp_path):
        """Test execute validates valid plan."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("## Tasks\n- [ ] Task 1")

        agent = ValidationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"plan_file": str(plan_file)},
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data.get("valid") is True

    @pytest.mark.asyncio
    async def test_execute_invalid_plan(self, tmp_path):
        """Test execute finds issues in invalid plan."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Some content without structure")

        agent = ValidationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"plan_file": str(plan_file)},
        )

        result = await agent.execute(task)

        assert result.success is True
        assert result.data.get("valid") is False


class TestImplementationAgentExecute:
    """Tests for ImplementationAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_returns_success(self, tmp_path):
        """Test execute returns success."""
        agent = ImplementationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"feature": "User login"},
        )

        result = await agent.execute(task)

        assert result.success is True
        assert "User login" in result.output
        assert result.data.get("feature") == "User login"

    @pytest.mark.asyncio
    async def test_execute_default_feature(self, tmp_path):
        """Test execute with default feature name."""
        agent = ImplementationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={},  # No feature specified
        )

        result = await agent.execute(task)

        assert result.success is True
        assert "Unknown feature" in result.output


class TestTestingValidationAgentExecute:
    """Tests for TestingValidationAgent.execute method."""

    @pytest.mark.asyncio
    async def test_execute_runs_tests(self, tmp_path):
        """Test execute runs tests."""
        agent = TestingValidationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"test_path": "tests/", "feature": "login"},
        )

        # Mock TestRunner - patch at the import location
        mock_results = []

        with patch("beyond_ralph.testing.TestRunner") as MockRunner:
            mock_runner = MagicMock()
            mock_runner.run_pytest = AsyncMock(return_value=mock_results)
            MockRunner.return_value = mock_runner

            result = await agent.execute(task)

        assert result.success is True
        assert "passed" in result.output.lower() or "failed" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_with_failing_tests(self, tmp_path):
        """Test execute handles failing tests."""
        agent = TestingValidationAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={"test_path": "tests/", "feature": "login"},
        )

        # Create mock failed test result
        mock_result = MagicMock()
        mock_result.passed = False
        mock_result.to_dict.return_value = {"passed": False}

        with patch("beyond_ralph.testing.TestRunner") as MockRunner:
            mock_runner = MagicMock()
            mock_runner.run_pytest = AsyncMock(return_value=[mock_result])
            MockRunner.return_value = mock_runner

            result = await agent.execute(task)

        assert result.success is True
        assert result.data.get("passed") is False


class TestSpecComplianceAgentExecuteMissingFiles:
    """Additional tests for SpecComplianceAgent missing file handling."""

    @pytest.mark.asyncio
    async def test_execute_spec_not_found(self, tmp_path):
        """Test execute fails when spec file not found."""
        impl_file = tmp_path / "impl.py"
        impl_file.write_text("def foo(): pass")

        agent = SpecComplianceAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={
                "spec_path": "nonexistent.md",
                "implementation_path": str(impl_file),
            },
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "Specification file not found" in result.output

    @pytest.mark.asyncio
    async def test_execute_impl_not_found(self, tmp_path):
        """Test execute fails when implementation file not found."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("- Must do something")

        agent = SpecComplianceAgent(project_root=tmp_path)
        task = AgentTask(
            id="test",
            description="Test",
            instructions="Test",
            context={
                "spec_path": str(spec_file),
                "implementation_path": "nonexistent.py",
            },
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "Implementation file not found" in result.output
