"""Tests for the Beyond Ralph Agent Framework.

Tests the base agent class, research agent, and code review agent.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import json

from beyond_ralph.agents.base import (
    AgentModel,
    AgentResult,
    AgentStatus,
    AgentTask,
    BaseAgent,
    PhaseAgent,
    TrustModelAgent,
)
from beyond_ralph.agents.research_agent import (
    DiscoveredTool,
    PackageManager,
    ResearchAgent,
    ToolCategory,
)
from beyond_ralph.agents.review_agent import (
    CodeReviewAgent,
    ReviewCategory,
    ReviewItem,
    ReviewResult,
    ReviewSeverity,
)


# ============================================================================
# BaseAgent Tests
# ============================================================================


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""

    name = "test_agent"
    description = "Test agent for unit tests"
    tools = ["Read", "Write"]
    model = AgentModel.SONNET

    async def execute(self, task: AgentTask) -> AgentResult:
        """Simple execution that returns success."""
        return self.succeed(
            output=f"Executed: {task.description}",
            data={"task_id": task.id},
        )


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_agent_initialization(self, tmp_path: Path) -> None:
        """Test agent initializes with correct defaults."""
        agent = ConcreteAgent(project_root=tmp_path)

        assert agent.name == "test_agent"
        assert agent.description == "Test agent for unit tests"
        assert agent.tools == ["Read", "Write"]
        assert agent.model == AgentModel.SONNET
        assert agent.project_root == tmp_path
        assert agent.status == AgentStatus.PENDING

    def test_agent_task_creation(self) -> None:
        """Test AgentTask creation with auto-generated ID."""
        task = AgentTask.create(
            description="Test task",
            instructions="Do something",
            context={"key": "value"},
        )

        assert task.id is not None
        assert len(task.id) == 36  # UUID format
        assert task.description == "Test task"
        assert task.instructions == "Do something"
        assert task.context == {"key": "value"}

    def test_agent_result_success(self) -> None:
        """Test creating a success result."""
        result = AgentResult(
            success=True,
            output="Task completed",
            data={"result": 42},
        )

        assert result.success is True
        assert result.output == "Task completed"
        assert result.data == {"result": 42}
        assert result.has_question is False

    def test_agent_result_with_question(self) -> None:
        """Test creating a result with a question."""
        result = AgentResult(
            success=False,
            output="Need clarification",
            question="What should I do?",
        )

        assert result.success is False
        assert result.has_question is True
        assert result.question == "What should I do?"

    @pytest.mark.asyncio
    async def test_agent_execute(self, tmp_path: Path) -> None:
        """Test agent execution lifecycle."""
        agent = ConcreteAgent(project_root=tmp_path)
        task = AgentTask.create(
            description="Test execution",
            instructions="Execute test",
        )

        result = await agent.run(task)

        assert result.success is True
        assert "Test execution" in result.output
        assert agent.status == AgentStatus.COMPLETED

    def test_agent_succeed(self, tmp_path: Path) -> None:
        """Test succeed helper method."""
        agent = ConcreteAgent(project_root=tmp_path)
        result = agent.succeed(
            output="Success!",
            data={"key": "value"},
            artifacts=[tmp_path / "file.txt"],
        )

        assert result.success is True
        assert result.output == "Success!"
        assert result.data == {"key": "value"}
        assert agent.status == AgentStatus.COMPLETED

    def test_agent_fail(self, tmp_path: Path) -> None:
        """Test fail helper method."""
        agent = ConcreteAgent(project_root=tmp_path)
        result = agent.fail(
            reason="Something went wrong",
            errors=["Error 1", "Error 2"],
        )

        assert result.success is False
        assert result.output == "Something went wrong"
        assert result.errors == ["Error 1", "Error 2"]
        assert agent.status == AgentStatus.FAILED

    def test_agent_return_with_question(self, tmp_path: Path) -> None:
        """Test return_with_question helper."""
        agent = ConcreteAgent(project_root=tmp_path)
        result = agent.return_with_question(
            question="Need input?",
            output="Partial work done",
        )

        assert result.success is False
        assert result.has_question is True
        assert result.question == "Need input?"
        assert agent.status == AgentStatus.WAITING_FOR_INPUT

    def test_agent_prompt_context(self, tmp_path: Path) -> None:
        """Test getting prompt context."""
        agent = ConcreteAgent(project_root=tmp_path)
        context = agent.get_prompt_context()

        assert context["agent_name"] == "test_agent"
        assert context["agent_description"] == "Test agent for unit tests"
        assert context["available_tools"] == ["Read", "Write"]
        assert context["model"] == "sonnet"


# ============================================================================
# PhaseAgent Tests
# ============================================================================


class ConcretePhaseAgent(PhaseAgent):
    """Concrete phase agent for testing."""

    name = "spec_agent"
    phase = 1

    async def execute(self, task: AgentTask) -> AgentResult:
        return self.succeed(output="Phase 1 complete")


class TestPhaseAgent:
    """Tests for PhaseAgent class."""

    def test_phase_agent_initialization(self, tmp_path: Path) -> None:
        """Test phase agent has correct phase."""
        agent = ConcretePhaseAgent(project_root=tmp_path)
        assert agent.phase == 1

    @pytest.mark.asyncio
    async def test_phase_context(self, tmp_path: Path) -> None:
        """Test getting phase context."""
        agent = ConcretePhaseAgent(project_root=tmp_path)
        context = await agent.get_phase_context()

        assert context["phase"] == 1
        assert context["phase_name"] == "Spec Ingestion"


# ============================================================================
# TrustModelAgent Tests
# ============================================================================


class CodingAgent(TrustModelAgent):
    """Test coding agent."""

    name = "coding"
    can_implement = True

    async def execute(self, task: AgentTask) -> AgentResult:
        return self.succeed(output="Code written")


class TestingAgent(TrustModelAgent):
    """Test testing agent."""

    name = "testing"
    can_test = True

    async def execute(self, task: AgentTask) -> AgentResult:
        return self.succeed(output="Tests run")


class TestTrustModelAgent:
    """Tests for TrustModelAgent class."""

    def test_trust_model_separation(self, tmp_path: Path) -> None:
        """Test trust model enforces separation."""
        coding = CodingAgent(project_root=tmp_path)
        testing = TestingAgent(project_root=tmp_path)

        # Different capabilities = valid separation
        assert coding.validate_separation(testing) is True

    def test_trust_model_violation(self, tmp_path: Path) -> None:
        """Test trust model detects violation."""
        coding1 = CodingAgent(project_root=tmp_path)
        coding2 = CodingAgent(project_root=tmp_path)

        # Same capability = violation
        assert coding1.validate_separation(coding2) is False


# ============================================================================
# ResearchAgent Tests
# ============================================================================


class TestResearchAgent:
    """Tests for ResearchAgent class."""

    def test_research_agent_initialization(self, tmp_path: Path) -> None:
        """Test research agent initializes correctly."""
        agent = ResearchAgent(project_root=tmp_path)

        assert agent.name == "research"
        assert agent.failed_tools == []
        assert agent.installed_tools == []

    def test_preferred_tools_exist(self) -> None:
        """Test preferred tools are defined for key categories."""
        assert ToolCategory.TESTING_FRAMEWORK in ResearchAgent.PREFERRED_TOOLS
        assert ToolCategory.BROWSER_AUTOMATION in ResearchAgent.PREFERRED_TOOLS
        assert ToolCategory.LINTING in ResearchAgent.PREFERRED_TOOLS
        assert ToolCategory.SECURITY_SCANNING in ResearchAgent.PREFERRED_TOOLS

    def test_get_preferred_tool(self, tmp_path: Path) -> None:
        """Test getting preferred tool for category."""
        agent = ResearchAgent(project_root=tmp_path)

        pytest_tool = agent.get_preferred_tool(ToolCategory.TESTING_FRAMEWORK)
        assert pytest_tool is not None
        assert pytest_tool.name == "pytest"
        assert pytest_tool.recommended is True

    def test_get_alternatives(self, tmp_path: Path) -> None:
        """Test getting alternative tools."""
        agent = ResearchAgent(project_root=tmp_path)

        alternatives = agent.get_alternatives(ToolCategory.BROWSER_AUTOMATION)
        assert len(alternatives) >= 2
        assert any(t.name == "selenium" for t in alternatives)

    def test_discovered_tool_serialization(self) -> None:
        """Test DiscoveredTool can be serialized."""
        tool = DiscoveredTool(
            name="pytest",
            category=ToolCategory.TESTING_FRAMEWORK,
            package_manager=PackageManager.PIP,
            package_name="pytest",
            description="Testing framework",
            install_command="pip install pytest",
            platform_support=["linux", "macos", "windows"],
        )

        data = tool.to_dict()
        assert data["name"] == "pytest"
        assert data["category"] == "testing_framework"
        assert data["package_manager"] == "pip"

    @pytest.mark.asyncio
    async def test_install_builtin_tool(self, tmp_path: Path) -> None:
        """Test installing a built-in tool (no actual install)."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="unittest",
            category=ToolCategory.TESTING_FRAMEWORK,
            package_manager=PackageManager.PIP,
            package_name="",
            description="Built-in testing",
            install_command="# Built-in, no install needed",
            platform_support=["linux", "macos", "windows"],
        )

        success = await agent.install_tool(tool)
        assert success is True
        assert "unittest" in agent.installed_tools

    @pytest.mark.asyncio
    async def test_handle_tool_failure_tracks_failed(self, tmp_path: Path) -> None:
        """Test that failed tools are tracked."""
        agent = ResearchAgent(project_root=tmp_path)

        # Mock install to always fail
        agent.install_tool = AsyncMock(return_value=False)

        result = await agent.handle_tool_failure(
            failed_tool="broken_tool",
            error_message="Doesn't work",
            category=ToolCategory.LINTING,
            platform="linux",
        )

        assert "broken_tool" in agent.failed_tools

    @pytest.mark.asyncio
    async def test_execute_find_tool_task(self, tmp_path: Path) -> None:
        """Test executing a find_tool task."""
        agent = ResearchAgent(project_root=tmp_path)

        # Mock install to succeed for built-in tools
        async def mock_install(tool: DiscoveredTool) -> bool:
            agent.installed_tools.append(tool.name)
            return True

        agent.install_tool = mock_install

        task = AgentTask.create(
            description="Find testing framework",
            instructions="Install pytest",
            context={
                "type": "find_tool",
                "category": "testing_framework",
                "platform": "linux",
            },
        )

        result = await agent.execute(task)
        assert result.success is True
        assert "pytest" in result.data.get("tool", {}).get("name", "")


# ============================================================================
# CodeReviewAgent Tests
# ============================================================================


class TestCodeReviewAgent:
    """Tests for CodeReviewAgent class."""

    def test_review_agent_initialization(self, tmp_path: Path) -> None:
        """Test review agent initializes correctly."""
        agent = CodeReviewAgent(project_root=tmp_path)

        assert agent.name == "code_review"
        assert agent.can_review is True
        assert agent.can_implement is False
        assert agent.can_test is False

    def test_review_severity_order(self) -> None:
        """Test review severities are properly defined."""
        assert ReviewSeverity.CRITICAL.value == "critical"
        assert ReviewSeverity.HIGH.value == "high"
        assert ReviewSeverity.MEDIUM.value == "medium"
        assert ReviewSeverity.LOW.value == "low"
        assert ReviewSeverity.INFO.value == "info"

    def test_review_item_serialization(self) -> None:
        """Test ReviewItem can be serialized."""
        item = ReviewItem(
            category=ReviewCategory.SECURITY,
            severity=ReviewSeverity.CRITICAL,
            file_path="test.py",
            line_number=10,
            message="SQL injection vulnerability",
            rule_id="B608",
        )

        data = item.to_dict()
        assert data["category"] == "security"
        assert data["severity"] == "critical"
        assert data["file_path"] == "test.py"
        assert data["line_number"] == 10

    def test_review_result_counts(self) -> None:
        """Test ReviewResult counting methods."""
        items = [
            ReviewItem(ReviewCategory.SECURITY, ReviewSeverity.CRITICAL, "a.py", 1, "Critical"),
            ReviewItem(ReviewCategory.SECURITY, ReviewSeverity.HIGH, "b.py", 2, "High"),
            ReviewItem(ReviewCategory.LINT, ReviewSeverity.MEDIUM, "c.py", 3, "Medium"),
            ReviewItem(ReviewCategory.LINT, ReviewSeverity.LOW, "d.py", 4, "Low"),
            ReviewItem(ReviewCategory.DOCS, ReviewSeverity.INFO, "e.py", 5, "Info"),
        ]

        result = ReviewResult(items=items)

        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.must_fix_count() == 3  # Critical + High + Medium

    def test_review_result_passed(self) -> None:
        """Test ReviewResult.passed property."""
        # Empty result should pass
        result = ReviewResult(items=[], passed=True)
        assert result.passed is True

        # Only low/info should pass
        low_items = [
            ReviewItem(ReviewCategory.LINT, ReviewSeverity.LOW, "a.py", 1, "Minor"),
            ReviewItem(ReviewCategory.DOCS, ReviewSeverity.INFO, "b.py", 2, "Suggestion"),
        ]
        result = ReviewResult(items=low_items)
        result.passed = result.must_fix_count() == 0
        assert result.passed is True

        # Medium or higher should fail
        medium_items = [
            ReviewItem(ReviewCategory.LINT, ReviewSeverity.MEDIUM, "a.py", 1, "Issue"),
        ]
        result = ReviewResult(items=medium_items)
        result.passed = result.must_fix_count() == 0
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_detect_languages(self, tmp_path: Path) -> None:
        """Test language detection."""
        # Create Python indicator
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").touch()

        agent = CodeReviewAgent(project_root=tmp_path)
        languages = await agent.detect_languages()

        assert "python" in languages

    @pytest.mark.asyncio
    async def test_detect_no_languages(self, tmp_path: Path) -> None:
        """Test language detection with no code."""
        agent = CodeReviewAgent(project_root=tmp_path)
        languages = await agent.detect_languages()

        assert languages == []

    def test_parse_ruff_output(self, tmp_path: Path) -> None:
        """Test parsing ruff JSON output."""
        agent = CodeReviewAgent(project_root=tmp_path)

        ruff_output = json.dumps([
            {
                "filename": "test.py",
                "location": {"row": 10, "column": 5},
                "code": "E501",
                "message": "Line too long",
            },
            {
                "filename": "test.py",
                "location": {"row": 20, "column": 1},
                "code": "F401",
                "message": "Unused import",
            },
        ])

        items = agent._parse_ruff(ruff_output, "")

        assert len(items) == 2
        assert items[0].file_path == "test.py"
        assert items[0].line_number == 10
        assert items[0].rule_id == "E501"
        assert items[0].severity == ReviewSeverity.HIGH  # E codes are high

    def test_parse_bandit_output(self, tmp_path: Path) -> None:
        """Test parsing bandit JSON output."""
        agent = CodeReviewAgent(project_root=tmp_path)

        bandit_output = json.dumps({
            "results": [
                {
                    "filename": "auth.py",
                    "line_number": 42,
                    "issue_severity": "HIGH",
                    "issue_text": "Possible hardcoded password",
                    "test_id": "B106",
                    "more_info": "https://example.com",
                },
            ],
        })

        items = agent._parse_bandit(bandit_output, "")

        assert len(items) == 1
        assert items[0].category == ReviewCategory.SECURITY
        assert items[0].severity == ReviewSeverity.CRITICAL
        assert items[0].rule_id == "B106"

    def test_parse_detect_secrets_output(self, tmp_path: Path) -> None:
        """Test parsing detect-secrets output."""
        agent = CodeReviewAgent(project_root=tmp_path)

        secrets_output = json.dumps({
            "results": {
                "config.py": [
                    {
                        "type": "Secret Keyword",
                        "line_number": 5,
                    },
                ],
            },
        })

        items = agent._parse_detect_secrets(secrets_output, "")

        assert len(items) == 1
        assert items[0].category == ReviewCategory.SECURITY
        assert items[0].severity == ReviewSeverity.CRITICAL
        assert items[0].file_path == "config.py"

    def test_generate_summary_passed(self, tmp_path: Path) -> None:
        """Test summary generation for passing review."""
        agent = CodeReviewAgent(project_root=tmp_path)
        result = ReviewResult(items=[], passed=True, tools_used=["ruff", "mypy"])

        summary = agent._generate_summary(result)

        assert "PASSED" in summary
        assert "ruff" in summary
        assert "mypy" in summary

    def test_generate_summary_failed(self, tmp_path: Path) -> None:
        """Test summary generation for failing review."""
        agent = CodeReviewAgent(project_root=tmp_path)
        result = ReviewResult(
            items=[
                ReviewItem(ReviewCategory.SECURITY, ReviewSeverity.CRITICAL, "a.py", 1, "Issue"),
            ],
            passed=False,
        )

        summary = agent._generate_summary(result)

        assert "found" in summary
        assert "Critical: 1" in summary
        assert "must be fixed" in summary

    @pytest.mark.asyncio
    async def test_review_empty_project(self, tmp_path: Path) -> None:
        """Test reviewing an empty project."""
        agent = CodeReviewAgent(project_root=tmp_path)
        result = await agent.review()

        # Empty project should pass (no issues found)
        assert result.passed is True
        assert result.languages_detected == []

    @pytest.mark.asyncio
    async def test_execute_review_task(self, tmp_path: Path) -> None:
        """Test executing a review task."""
        agent = CodeReviewAgent(project_root=tmp_path)

        task = AgentTask.create(
            description="Review code",
            instructions="Perform full code review",
        )

        result = await agent.execute(task)

        # Review task should succeed (even if issues found)
        assert result.success is True
        assert "passed" in result.data or "items" in result.data


# ============================================================================
# Integration Tests
# ============================================================================


class TestAgentIntegration:
    """Integration tests for agent framework."""

    @pytest.mark.asyncio
    async def test_agent_writes_knowledge(self, tmp_path: Path) -> None:
        """Test agent can write to knowledge base."""
        knowledge_dir = tmp_path / "beyondralph_knowledge"
        knowledge_dir.mkdir()

        agent = ConcreteAgent(
            project_root=tmp_path,
            knowledge_dir=knowledge_dir,
        )

        entry_uuid = await agent.write_knowledge(
            title="test-entry",
            content="# Test\nThis is a test entry.",
            category="test",
            tags=["unit-test"],
        )

        assert entry_uuid is not None

        # Verify file was created
        files = list(knowledge_dir.glob("*.md"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_agent_reads_knowledge(self, tmp_path: Path) -> None:
        """Test agent can read from knowledge base."""
        knowledge_dir = tmp_path / "beyondralph_knowledge"
        knowledge_dir.mkdir()

        # Create a knowledge entry
        entry_content = """---
uuid: test-123
category: test
tags:
  - example
---

# Test Entry
Some test content.
"""
        (knowledge_dir / "test-entry.md").write_text(entry_content)

        agent = ConcreteAgent(
            project_root=tmp_path,
            knowledge_dir=knowledge_dir,
        )

        entries = await agent.read_knowledge(topic="test")

        assert len(entries) >= 1
        assert any("test" in e.get("content", "").lower() for e in entries)
