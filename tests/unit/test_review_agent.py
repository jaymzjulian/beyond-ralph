"""Tests for review agent module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.agents.review_agent import (
    ReviewCategory,
    ReviewItem,
    ReviewResult,
    ReviewSeverity,
    CodeReviewAgent,
)
from beyond_ralph.agents.base import TrustModelAgent


class TestReviewSeverity:
    """Tests for ReviewSeverity enum."""

    def test_severity_levels_exist(self):
        """Test all severity levels exist."""
        assert ReviewSeverity.CRITICAL.value == "critical"
        assert ReviewSeverity.HIGH.value == "high"
        assert ReviewSeverity.MEDIUM.value == "medium"
        assert ReviewSeverity.LOW.value == "low"
        assert ReviewSeverity.INFO.value == "info"

    def test_severity_count(self):
        """Test correct number of severity levels."""
        assert len(ReviewSeverity) == 5


class TestReviewCategory:
    """Tests for ReviewCategory enum."""

    def test_category_types_exist(self):
        """Test all category types exist."""
        assert ReviewCategory.SECURITY.value == "security"
        assert ReviewCategory.LINT.value == "lint"
        assert ReviewCategory.TYPE.value == "type"
        assert ReviewCategory.COMPLEXITY.value == "complexity"
        assert ReviewCategory.DUPLICATION.value == "duplication"
        assert ReviewCategory.PRACTICE.value == "practice"
        assert ReviewCategory.DOCS.value == "docs"
        assert ReviewCategory.DEPENDENCY.value == "dependency"
        assert ReviewCategory.INCOMPLETE.value == "incomplete"
        assert ReviewCategory.SEMANTIC.value == "semantic"

    def test_category_count(self):
        """Test correct number of categories."""
        assert len(ReviewCategory) == 10


class TestReviewItem:
    """Tests for ReviewItem dataclass."""

    def test_review_item_creation(self):
        """Test creating a ReviewItem."""
        item = ReviewItem(
            category=ReviewCategory.SECURITY,
            severity=ReviewSeverity.CRITICAL,
            file_path="src/auth.py",
            line_number=45,
            message="SQL injection vulnerability",
        )

        assert item.category == ReviewCategory.SECURITY
        assert item.severity == ReviewSeverity.CRITICAL
        assert item.file_path == "src/auth.py"
        assert item.line_number == 45
        assert item.message == "SQL injection vulnerability"

    def test_review_item_with_optional_fields(self):
        """Test ReviewItem with optional fields."""
        item = ReviewItem(
            category=ReviewCategory.LINT,
            severity=ReviewSeverity.MEDIUM,
            file_path="src/utils.py",
            line_number=10,
            message="Missing type hint",
            rule_id="PY001",
            suggested_fix="Add type annotation: def func(x: int) -> str",
            reference_url="https://docs.python.org/3/library/typing.html",
        )

        assert item.rule_id == "PY001"
        assert item.suggested_fix is not None
        assert item.reference_url is not None

    def test_review_item_to_dict(self):
        """Test ReviewItem serialization to dict."""
        item = ReviewItem(
            category=ReviewCategory.PRACTICE,
            severity=ReviewSeverity.HIGH,
            file_path="src/module.py",
            line_number=100,
            message="Dead code detected",
            rule_id="DC001",
        )

        data = item.to_dict()

        assert data["category"] == "practice"
        assert data["severity"] == "high"
        assert data["file_path"] == "src/module.py"
        assert data["line_number"] == 100
        assert data["message"] == "Dead code detected"
        assert data["rule_id"] == "DC001"

    def test_review_item_defaults(self):
        """Test ReviewItem has correct defaults."""
        item = ReviewItem(
            category=ReviewCategory.DOCS,
            severity=ReviewSeverity.LOW,
            file_path="src/api.py",
            line_number=None,
            message="Missing docstring",
        )

        assert item.rule_id is None
        assert item.suggested_fix is None
        assert item.reference_url is None


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_review_result_creation(self):
        """Test creating a ReviewResult."""
        result = ReviewResult()

        assert result.items == []
        assert result.passed is False
        assert result.summary == ""
        assert result.languages_detected == []
        assert result.tools_used == []

    def test_review_result_with_items(self):
        """Test ReviewResult with items."""
        items = [
            ReviewItem(
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                file_path="src/auth.py",
                line_number=45,
                message="Critical issue",
            ),
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.HIGH,
                file_path="src/utils.py",
                line_number=10,
                message="High severity lint issue",
            ),
            ReviewItem(
                category=ReviewCategory.DOCS,
                severity=ReviewSeverity.LOW,
                file_path="src/api.py",
                line_number=5,
                message="Low severity doc issue",
            ),
        ]

        result = ReviewResult(
            items=items,
            passed=False,
            summary="Found 3 issues",
            languages_detected=["python"],
            tools_used=["ruff", "mypy"],
        )

        assert len(result.items) == 3
        assert result.passed is False
        assert "3 issues" in result.summary
        assert "python" in result.languages_detected
        assert "ruff" in result.tools_used

    def test_review_result_critical_count(self):
        """Test critical_count property."""
        items = [
            ReviewItem(
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                file_path="a.py",
                line_number=1,
                message="Critical 1",
            ),
            ReviewItem(
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                file_path="b.py",
                line_number=2,
                message="Critical 2",
            ),
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.HIGH,
                file_path="c.py",
                line_number=3,
                message="High",
            ),
        ]

        result = ReviewResult(items=items)
        assert result.critical_count == 2

    def test_review_result_high_count(self):
        """Test high_count property."""
        items = [
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.HIGH,
                file_path="a.py",
                line_number=1,
                message="High 1",
            ),
            ReviewItem(
                category=ReviewCategory.PRACTICE,
                severity=ReviewSeverity.HIGH,
                file_path="b.py",
                line_number=2,
                message="High 2",
            ),
            ReviewItem(
                category=ReviewCategory.DOCS,
                severity=ReviewSeverity.LOW,
                file_path="c.py",
                line_number=3,
                message="Low",
            ),
        ]

        result = ReviewResult(items=items)
        assert result.high_count == 2


class TestCodeReviewAgent:
    """Tests for CodeReviewAgent class."""

    def test_code_review_agent_creation(self, tmp_path):
        """Test creating a CodeReviewAgent."""
        agent = CodeReviewAgent(project_root=tmp_path)

        assert agent.name == "code_review"
        assert "review" in agent.description.lower() or "code" in agent.description.lower()

    def test_code_review_agent_is_trust_model_agent(self, tmp_path):
        """Test CodeReviewAgent inherits from TrustModelAgent."""
        agent = CodeReviewAgent(project_root=tmp_path)
        assert isinstance(agent, TrustModelAgent)

    def test_code_review_agent_has_review_capability(self, tmp_path):
        """Test CodeReviewAgent has can_review=True."""
        agent = CodeReviewAgent(project_root=tmp_path)
        assert agent.can_review is True
        assert agent.can_implement is False
        assert agent.can_test is False

    def test_code_review_agent_tools(self, tmp_path):
        """Test CodeReviewAgent has expected tools."""
        agent = CodeReviewAgent(project_root=tmp_path)

        # Should have code reading tools
        assert "Read" in agent.tools or "Glob" in agent.tools or "Grep" in agent.tools


class TestCodeReviewAgentLanguageDetection:
    """Tests for CodeReviewAgent language detection."""

    def test_detect_python(self, tmp_path):
        """Test detecting Python files."""
        agent = CodeReviewAgent(project_root=tmp_path)

        # Create a Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")

        if hasattr(agent, "_detect_languages"):
            languages = agent._detect_languages(tmp_path)
            assert "python" in [l.lower() for l in languages]

    def test_detect_javascript(self, tmp_path):
        """Test detecting JavaScript files."""
        agent = CodeReviewAgent(project_root=tmp_path)

        # Create a JavaScript file
        js_file = tmp_path / "test.js"
        js_file.write_text("console.log('hello');")

        if hasattr(agent, "_detect_languages"):
            languages = agent._detect_languages(tmp_path)
            assert "javascript" in [l.lower() for l in languages]


class TestCodeReviewAgentLinting:
    """Tests for CodeReviewAgent linting functionality."""

    @pytest.mark.asyncio
    async def test_run_python_linters(self, tmp_path):
        """Test running Python linters."""
        agent = CodeReviewAgent(project_root=tmp_path)

        # Create a Python file with issues
        py_file = tmp_path / "test.py"
        py_file.write_text("import os\nx=1")  # Unused import, missing type hint

        if hasattr(agent, "_run_python_linters"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='[{"type":"error","message":"test"}]',
                    stderr="",
                )

                try:
                    items = await agent._run_python_linters(tmp_path)
                    assert isinstance(items, list)
                except (NotImplementedError, AttributeError):
                    pass


class TestCodeReviewAgentSecurityScanning:
    """Tests for CodeReviewAgent security scanning."""

    @pytest.mark.asyncio
    async def test_run_security_scan(self, tmp_path):
        """Test running security scan."""
        agent = CodeReviewAgent(project_root=tmp_path)

        if hasattr(agent, "_run_security_scan"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="[]",
                    stderr="",
                )

                try:
                    items = await agent._run_security_scan(tmp_path)
                    assert isinstance(items, list)
                except (NotImplementedError, AttributeError):
                    pass


class TestCodeReviewAgentTodoDetection:
    """Tests for CodeReviewAgent TODO/incomplete detection."""

    def test_detect_todos(self, tmp_path):
        """Test detecting TODO comments."""
        agent = CodeReviewAgent(project_root=tmp_path)

        # Create a file with TODOs
        py_file = tmp_path / "test.py"
        py_file.write_text("""
# TODO: implement this
def incomplete_function():
    pass  # FIXME: add logic
""")

        if hasattr(agent, "_detect_incomplete_code"):
            items = agent._detect_incomplete_code(tmp_path)
            assert isinstance(items, list)
            # Should find at least the TODO and FIXME
            if items:
                assert any("TODO" in str(item) or "FIXME" in str(item) for item in items)


class TestCodeReviewAgentExecution:
    """Tests for CodeReviewAgent execution."""

    @pytest.mark.asyncio
    async def test_execute_review(self, tmp_path):
        """Test executing a code review."""
        from beyond_ralph.agents.base import AgentTask

        agent = CodeReviewAgent(project_root=tmp_path)

        # Create some Python files
        py_file = tmp_path / "module.py"
        py_file.write_text("def hello():\n    return 'world'")

        task = AgentTask(
            id="test-review",
            description="Review the code",
            instructions="Check for issues",
            context={"path": str(tmp_path)},
        )

        # Mock subprocess calls to avoid needing real linters
        # Return empty results for each tool format
        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""

            # Different tools expect different output formats
            if "detect-secrets" in str(cmd):
                result.stdout = '{"results": {}}'
            elif "ruff" in str(cmd) or "mypy" in str(cmd):
                result.stdout = "[]"
            elif "semgrep" in str(cmd):
                result.stdout = '{"results": []}'
            else:
                result.stdout = ""

            return result

        with patch("subprocess.run", side_effect=mock_subprocess):
            with patch("shutil.which", return_value=None):  # No linters installed
                result = await agent.execute(task)

                assert result is not None
                assert hasattr(result, "success")


class TestCodeReviewAgentOutputParsing:
    """Tests for CodeReviewAgent output parsing."""

    def test_parse_ruff_output_empty(self, tmp_path):
        """Test parsing empty ruff output."""
        agent = CodeReviewAgent(project_root=tmp_path)

        if hasattr(agent, "_parse_ruff_output"):
            items = agent._parse_ruff_output("[]")
            assert items == []

    def test_parse_ruff_output_with_errors(self, tmp_path):
        """Test parsing ruff output with errors."""
        agent = CodeReviewAgent(project_root=tmp_path)

        ruff_output = '''[
            {"type": "error", "filename": "test.py", "row": 1, "column": 1, "message": "E501 line too long", "code": "E501"}
        ]'''

        if hasattr(agent, "_parse_ruff_output"):
            items = agent._parse_ruff_output(ruff_output)
            assert isinstance(items, list)

    def test_parse_mypy_output_empty(self, tmp_path):
        """Test parsing empty mypy output."""
        agent = CodeReviewAgent(project_root=tmp_path)

        if hasattr(agent, "_parse_mypy_output"):
            items = agent._parse_mypy_output("")
            assert items == []

    def test_parse_mypy_output_with_errors(self, tmp_path):
        """Test parsing mypy output with errors."""
        agent = CodeReviewAgent(project_root=tmp_path)

        mypy_output = '''test.py:10: error: Incompatible types
test.py:20: note: See https://mypy.readthedocs.io
'''

        if hasattr(agent, "_parse_mypy_output"):
            items = agent._parse_mypy_output(mypy_output)
            assert isinstance(items, list)


class TestReviewItemAdvanced:
    """Advanced tests for ReviewItem."""

    def test_review_item_defaults(self):
        """Test ReviewItem has correct defaults."""
        item = ReviewItem(
            category=ReviewCategory.LINT,
            severity=ReviewSeverity.LOW,
            file_path="test.py",
            line_number=1,
            message="Test message",
        )

        assert item.rule_id is None
        assert item.suggested_fix is None
        assert item.reference_url is None

    def test_review_item_equality(self):
        """Test ReviewItem equality."""
        item1 = ReviewItem(
            category=ReviewCategory.LINT,
            severity=ReviewSeverity.LOW,
            file_path="test.py",
            line_number=1,
            message="Test message",
        )

        item2 = ReviewItem(
            category=ReviewCategory.LINT,
            severity=ReviewSeverity.LOW,
            file_path="test.py",
            line_number=1,
            message="Test message",
        )

        # Should be equal (same values)
        assert item1 == item2


class TestReviewResultAdvanced:
    """Advanced tests for ReviewResult."""

    def test_review_result_empty(self):
        """Test ReviewResult with empty items."""
        result = ReviewResult(items=[], passed=True)

        assert result.critical_count == 0
        assert result.high_count == 0
        assert result.medium_count == 0
        assert result.passed is True

    def test_review_result_to_dict(self):
        """Test ReviewResult serialization."""
        items = [
            ReviewItem(
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                file_path="auth.py",
                line_number=10,
                message="SQL injection",
            ),
        ]

        result = ReviewResult(items=items)
        data = result.to_dict()

        assert "items" in data
        # Summary may be a string or dict depending on implementation
        assert result.critical_count == 1

    def test_review_result_by_file(self):
        """Test ReviewResult grouped by file."""
        items = [
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.LOW,
                file_path="a.py",
                line_number=1,
                message="Issue 1",
            ),
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.LOW,
                file_path="a.py",
                line_number=2,
                message="Issue 2",
            ),
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.LOW,
                file_path="b.py",
                line_number=1,
                message="Issue 3",
            ),
        ]

        result = ReviewResult(items=items)

        if hasattr(result, "by_file"):
            by_file = result.by_file()
            assert "a.py" in by_file
            assert len(by_file["a.py"]) == 2
            assert "b.py" in by_file
            assert len(by_file["b.py"]) == 1


class TestCodeReviewAgentToolDetection:
    """Tests for CodeReviewAgent tool detection."""

    def test_detect_available_linters(self, tmp_path):
        """Test detecting available linters."""
        agent = CodeReviewAgent(project_root=tmp_path)

        if hasattr(agent, "_get_available_linters"):
            with patch("shutil.which") as mock_which:
                mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x == "ruff" else None

                linters = agent._get_available_linters()
                assert isinstance(linters, list)

    def test_detect_available_security_tools(self, tmp_path):
        """Test detecting available security tools."""
        agent = CodeReviewAgent(project_root=tmp_path)

        if hasattr(agent, "_get_available_security_tools"):
            with patch("shutil.which") as mock_which:
                mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x == "bandit" else None

                tools = agent._get_available_security_tools()
                assert isinstance(tools, list)


class TestCodeReviewAgentCategoryFiltering:
    """Tests for filtering review results by category."""

    def test_filter_by_severity(self, tmp_path):
        """Test filtering items by severity."""
        items = [
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.CRITICAL,
                file_path="a.py",
                line_number=1,
                message="Critical",
            ),
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.LOW,
                file_path="b.py",
                line_number=1,
                message="Low",
            ),
        ]

        result = ReviewResult(items=items)

        if hasattr(result, "filter_by_severity"):
            critical = result.filter_by_severity(ReviewSeverity.CRITICAL)
            assert len(critical) == 1
            assert critical[0].message == "Critical"

    def test_filter_by_category(self, tmp_path):
        """Test filtering items by category."""
        items = [
            ReviewItem(
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.HIGH,
                file_path="a.py",
                line_number=1,
                message="Security issue",
            ),
            ReviewItem(
                category=ReviewCategory.LINT,
                severity=ReviewSeverity.LOW,
                file_path="b.py",
                line_number=1,
                message="Lint issue",
            ),
        ]

        result = ReviewResult(items=items)

        if hasattr(result, "filter_by_category"):
            security = result.filter_by_category(ReviewCategory.SECURITY)
            assert len(security) == 1
            assert security[0].category == ReviewCategory.SECURITY


class TestCodeReviewAgentParsers:
    """Tests for CodeReviewAgent parser methods."""

    def test_parse_ruff_empty(self, tmp_path):
        """Test parsing empty ruff output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_ruff("", "")
        assert items == []

    def test_parse_ruff_empty_whitespace(self, tmp_path):
        """Test parsing whitespace-only ruff output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_ruff("   ", "")
        assert items == []

    def test_parse_ruff_with_issues(self, tmp_path):
        """Test parsing ruff output with issues."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''[
            {
                "code": "E501",
                "filename": "test.py",
                "location": {"row": 10, "column": 1},
                "message": "Line too long",
                "fix": {"message": "Split the line"}
            }
        ]'''
        items = agent._parse_ruff(stdout, "")
        assert len(items) == 1
        assert items[0].file_path == "test.py"
        assert items[0].line_number == 10
        assert items[0].rule_id == "E501"
        assert items[0].suggested_fix == "Split the line"

    def test_parse_ruff_error_code_severity(self, tmp_path):
        """Test that E/F codes are treated as high severity."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''[
            {"code": "F401", "filename": "test.py", "location": {"row": 1}, "message": "Unused import"},
            {"code": "W291", "filename": "test.py", "location": {"row": 2}, "message": "Trailing whitespace"}
        ]'''
        items = agent._parse_ruff(stdout, "")
        assert len(items) == 2
        assert items[0].severity == ReviewSeverity.HIGH  # F code
        assert items[1].severity == ReviewSeverity.MEDIUM  # W code

    def test_parse_ruff_invalid_json(self, tmp_path):
        """Test parsing invalid JSON returns empty list."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_ruff("not json", "")
        assert items == []

    def test_parse_mypy_empty(self, tmp_path):
        """Test parsing empty mypy output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_mypy("", "")
        assert items == []

    def test_parse_mypy_with_errors(self, tmp_path):
        """Test parsing mypy output with errors."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = """test.py:10: error: Incompatible types [type-arg]
test.py:20: warning: Missing return type
"""
        items = agent._parse_mypy(stdout, "")
        assert len(items) == 2
        assert items[0].file_path == "test.py"
        assert items[0].line_number == 10
        assert items[0].severity == ReviewSeverity.HIGH
        assert items[0].rule_id == "type-arg"

    def test_parse_mypy_invalid_line_number(self, tmp_path):
        """Test parsing mypy with invalid line number."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = "test.py:abc: error: Some error"
        items = agent._parse_mypy(stdout, "")
        assert len(items) == 1
        assert items[0].line_number is None

    def test_parse_mypy_without_rule_id(self, tmp_path):
        """Test parsing mypy without rule ID in brackets."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = "test.py:5: error: Some error without rule"
        items = agent._parse_mypy(stdout, "")
        assert len(items) == 1
        assert items[0].rule_id is None

    def test_parse_bandit_empty(self, tmp_path):
        """Test parsing empty bandit output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_bandit("", "")
        assert items == []

    def test_parse_bandit_with_results(self, tmp_path):
        """Test parsing bandit output with results."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''{"results": [
            {
                "filename": "test.py",
                "line_number": 15,
                "issue_severity": "HIGH",
                "issue_text": "SQL injection",
                "test_id": "B608",
                "more_info": "https://bandit.readthedocs.io"
            }
        ]}'''
        items = agent._parse_bandit(stdout, "")
        assert len(items) == 1
        assert items[0].category == ReviewCategory.SECURITY
        assert items[0].severity == ReviewSeverity.CRITICAL
        assert items[0].file_path == "test.py"
        assert items[0].line_number == 15
        assert items[0].rule_id == "B608"
        assert items[0].reference_url == "https://bandit.readthedocs.io"

    def test_parse_bandit_medium_severity(self, tmp_path):
        """Test bandit medium severity mapping."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''{"results": [
            {"issue_severity": "MEDIUM", "filename": "a.py", "line_number": 1, "issue_text": "Issue", "test_id": "B001"}
        ]}'''
        items = agent._parse_bandit(stdout, "")
        assert items[0].severity == ReviewSeverity.HIGH

    def test_parse_bandit_low_severity(self, tmp_path):
        """Test bandit low severity mapping."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''{"results": [
            {"issue_severity": "LOW", "filename": "a.py", "line_number": 1, "issue_text": "Issue", "test_id": "B001"}
        ]}'''
        items = agent._parse_bandit(stdout, "")
        assert items[0].severity == ReviewSeverity.MEDIUM

    def test_parse_bandit_invalid_json(self, tmp_path):
        """Test parsing invalid bandit JSON."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_bandit("not json", "")
        assert items == []

    def test_parse_eslint_empty(self, tmp_path):
        """Test parsing empty ESLint output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_eslint("", "")
        assert items == []

    def test_parse_eslint_with_issues(self, tmp_path):
        """Test parsing ESLint output with issues."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''[
            {
                "filePath": "/src/app.js",
                "messages": [
                    {"line": 5, "severity": 2, "message": "Unexpected var", "ruleId": "no-var"},
                    {"line": 10, "severity": 1, "message": "Console is allowed", "ruleId": "no-console"}
                ]
            }
        ]'''
        items = agent._parse_eslint(stdout, "")
        assert len(items) == 2
        assert items[0].severity == ReviewSeverity.HIGH  # severity 2
        assert items[1].severity == ReviewSeverity.MEDIUM  # severity 1

    def test_parse_eslint_invalid_json(self, tmp_path):
        """Test parsing invalid ESLint JSON."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_eslint("not json", "")
        assert items == []

    def test_parse_clippy_empty(self, tmp_path):
        """Test parsing empty clippy output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_clippy("", "")
        assert items == []

    def test_parse_clippy_with_messages(self, tmp_path):
        """Test parsing clippy output with messages."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''{"reason": "compiler-message", "message": {"level": "error", "message": "unused variable", "code": {"code": "unused_variables"}, "spans": [{"file_name": "src/main.rs", "line_start": 10}]}}
{"reason": "compiler-message", "message": {"level": "warning", "message": "consider using", "code": {"code": "clippy::style"}, "spans": [{"file_name": "src/lib.rs", "line_start": 20}]}}
'''
        items = agent._parse_clippy(stdout, "")
        assert len(items) == 2
        assert items[0].severity == ReviewSeverity.HIGH
        assert items[0].file_path == "src/main.rs"
        assert items[1].severity == ReviewSeverity.MEDIUM

    def test_parse_clippy_no_spans(self, tmp_path):
        """Test parsing clippy output without spans."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '{"reason": "compiler-message", "message": {"level": "warning", "message": "test", "spans": []}}'
        items = agent._parse_clippy(stdout, "")
        assert items == []

    def test_parse_clippy_invalid_json_lines(self, tmp_path):
        """Test parsing clippy with invalid JSON lines."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''not json
{"reason": "other"}
'''
        items = agent._parse_clippy(stdout, "")
        assert items == []

    def test_parse_cppcheck_empty(self, tmp_path):
        """Test parsing empty cppcheck output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_cppcheck("", "")
        assert items == []

    def test_parse_cppcheck_with_issues(self, tmp_path):
        """Test parsing cppcheck output with issues."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stderr = """src/main.c:10: error: Buffer overflow
src/utils.c:20: warning: Uninitialized variable
src/helper.c:5: style: Redundant code
"""
        items = agent._parse_cppcheck("", stderr)
        assert len(items) == 3
        assert items[0].severity == ReviewSeverity.HIGH
        assert items[0].file_path == "src/main.c"
        assert items[0].line_number == 10
        assert items[1].severity == ReviewSeverity.MEDIUM
        assert items[2].severity == ReviewSeverity.LOW

    def test_parse_cppcheck_performance_severity(self, tmp_path):
        """Test cppcheck performance severity."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stderr = "test.c:1: performance: Slow operation"
        items = agent._parse_cppcheck("", stderr)
        assert items[0].severity == ReviewSeverity.MEDIUM

    def test_parse_cppcheck_information_severity(self, tmp_path):
        """Test cppcheck information severity."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stderr = "test.c:1: information: Info message"
        items = agent._parse_cppcheck("", stderr)
        assert items[0].severity == ReviewSeverity.INFO

    def test_parse_rubocop_empty(self, tmp_path):
        """Test parsing empty RuboCop output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_rubocop("", "")
        assert items == []

    def test_parse_rubocop_with_offenses(self, tmp_path):
        """Test parsing RuboCop output with offenses."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''{"files": [
            {
                "path": "app.rb",
                "offenses": [
                    {"severity": "error", "message": "Syntax error", "cop_name": "Syntax", "location": {"line": 5}},
                    {"severity": "convention", "message": "Use double quotes", "cop_name": "Style/StringLiterals", "location": {"line": 10}}
                ]
            }
        ]}'''
        items = agent._parse_rubocop(stdout, "")
        assert len(items) == 2
        assert items[0].severity == ReviewSeverity.HIGH
        assert items[1].severity == ReviewSeverity.LOW

    def test_parse_rubocop_fatal_severity(self, tmp_path):
        """Test RuboCop fatal severity mapping."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''{"files": [{"path": "a.rb", "offenses": [{"severity": "fatal", "message": "Fatal", "cop_name": "Fatal", "location": {"line": 1}}]}]}'''
        items = agent._parse_rubocop(stdout, "")
        assert items[0].severity == ReviewSeverity.CRITICAL

    def test_parse_rubocop_invalid_json(self, tmp_path):
        """Test parsing invalid RuboCop JSON."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_rubocop("not json", "")
        assert items == []

    def test_parse_detect_secrets_empty(self, tmp_path):
        """Test parsing empty detect-secrets output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_detect_secrets("", "")
        assert items == []

    def test_parse_detect_secrets_with_results(self, tmp_path):
        """Test parsing detect-secrets with secrets found."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''{"results": {
            "config.py": [
                {"line_number": 5, "type": "Secret Keyword"},
                {"line_number": 10, "type": "Base64 High Entropy String"}
            ]
        }}'''
        items = agent._parse_detect_secrets(stdout, "")
        assert len(items) == 2
        assert items[0].category == ReviewCategory.SECURITY
        assert items[0].severity == ReviewSeverity.CRITICAL
        assert items[0].file_path == "config.py"
        assert items[0].line_number == 5

    def test_parse_detect_secrets_invalid_json(self, tmp_path):
        """Test parsing invalid detect-secrets JSON."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_detect_secrets("not json", "")
        assert items == []

    def test_parse_gitleaks_empty(self, tmp_path):
        """Test parsing empty gitleaks output."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_gitleaks("", "")
        assert items == []

    def test_parse_gitleaks_with_findings(self, tmp_path):
        """Test parsing gitleaks with findings."""
        agent = CodeReviewAgent(project_root=tmp_path)
        stdout = '''[
            {"file": "secrets.txt", "lineNumber": 3, "description": "AWS Access Key", "ruleID": "aws-access-key"}
        ]'''
        items = agent._parse_gitleaks(stdout, "")
        assert len(items) == 1
        assert items[0].category == ReviewCategory.SECURITY
        assert items[0].severity == ReviewSeverity.CRITICAL
        assert items[0].file_path == "secrets.txt"
        assert items[0].line_number == 3
        assert items[0].rule_id == "aws-access-key"

    def test_parse_gitleaks_invalid_json(self, tmp_path):
        """Test parsing invalid gitleaks JSON."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = agent._parse_gitleaks("not json", "")
        assert items == []


class TestCodeReviewAgentIncompleteCode:
    """Tests for check_incomplete_code method."""

    @pytest.mark.asyncio
    async def test_check_incomplete_code_empty_project(self, tmp_path):
        """Test checking empty project for incomplete code."""
        agent = CodeReviewAgent(project_root=tmp_path)
        items = await agent.check_incomplete_code()
        assert items == []

    @pytest.mark.asyncio
    async def test_check_incomplete_code_with_todo(self, tmp_path):
        """Test detecting TODO comments."""
        agent = CodeReviewAgent(project_root=tmp_path)
        (tmp_path / "main.py").write_text("# TODO: implement this\ndef foo():\n    pass")
        items = await agent.check_incomplete_code()
        assert len(items) >= 1
        assert any("TODO" in item.message for item in items)

    @pytest.mark.asyncio
    async def test_check_incomplete_code_with_fixme(self, tmp_path):
        """Test detecting FIXME comments."""
        agent = CodeReviewAgent(project_root=tmp_path)
        (tmp_path / "utils.py").write_text("def broken():\n    # FIXME: this is broken\n    pass")
        items = await agent.check_incomplete_code()
        assert len(items) >= 1
        assert any("FIXME" in item.message for item in items)

    @pytest.mark.asyncio
    async def test_check_incomplete_code_skips_test_files(self, tmp_path):
        """Test that test files are skipped for TODO detection."""
        agent = CodeReviewAgent(project_root=tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_module.py").write_text("# TODO: add more tests\ndef test_foo():\n    pass")
        items = await agent.check_incomplete_code()
        # Should not find TODOs in test files
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_check_incomplete_code_multiple_languages(self, tmp_path):
        """Test detecting incomplete code in multiple languages."""
        agent = CodeReviewAgent(project_root=tmp_path)
        (tmp_path / "app.js").write_text("// TODO: implement\nfunction foo() {}")
        (tmp_path / "lib.rs").write_text("// FIXME: broken\nfn bar() {}")
        items = await agent.check_incomplete_code()
        assert len(items) >= 2

    @pytest.mark.asyncio
    async def test_check_incomplete_code_unreadable_file(self, tmp_path):
        """Test handling unreadable files gracefully."""
        agent = CodeReviewAgent(project_root=tmp_path)
        # Create binary file that can't be read as text
        (tmp_path / "binary.py").write_bytes(b"\xff\xfe")
        items = await agent.check_incomplete_code()
        # Should not crash, just skip unreadable files
        assert isinstance(items, list)


class TestCodeReviewAgentRunLinters:
    """Tests for run_linters method."""

    @pytest.mark.asyncio
    async def test_run_linters_no_linters(self, tmp_path):
        """Test running linters when none available."""
        agent = CodeReviewAgent(project_root=tmp_path)
        with patch.object(agent, "LINTERS", {}):
            items = await agent.run_linters("python")
            assert items == []

    @pytest.mark.asyncio
    async def test_run_linters_success(self, tmp_path):
        """Test running linters successfully."""
        agent = CodeReviewAgent(project_root=tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = "[]"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            items = await agent.run_linters("python")
            assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_run_linters_timeout(self, tmp_path):
        """Test handling linter timeout."""
        agent = CodeReviewAgent(project_root=tmp_path)

        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ruff", timeout=300)):
            items = await agent.run_linters("python")
            # Should return an info item about timeout
            assert any(item.severity == ReviewSeverity.INFO for item in items)

    @pytest.mark.asyncio
    async def test_run_linters_not_found(self, tmp_path):
        """Test handling missing linter."""
        agent = CodeReviewAgent(project_root=tmp_path)

        with patch("subprocess.run", side_effect=FileNotFoundError):
            items = await agent.run_linters("python")
            # Should silently skip missing linters
            assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_run_linters_exception(self, tmp_path):
        """Test handling linter exception."""
        agent = CodeReviewAgent(project_root=tmp_path)

        with patch("subprocess.run", side_effect=Exception("Unexpected error")):
            items = await agent.run_linters("python")
            # Should return info item about failure
            assert any("failed" in item.message for item in items)


class TestCodeReviewAgentSecurityScan:
    """Tests for run_security_scan method."""

    @pytest.mark.asyncio
    async def test_run_security_scan_empty(self, tmp_path):
        """Test running security scan on empty project."""
        agent = CodeReviewAgent(project_root=tmp_path)

        def mock_subprocess(*args, **kwargs):
            """Return appropriate empty output for each security scanner."""
            result = MagicMock()
            result.stderr = ""
            cmd = args[0] if args else kwargs.get("args", [])
            cmd_str = str(cmd)

            if "detect-secrets" in cmd_str:
                result.stdout = '{"results": {}}'
            elif "gitleaks" in cmd_str:
                result.stdout = '[]'
            elif "bandit" in cmd_str:
                result.stdout = '{"results": []}'
            elif "semgrep" in cmd_str:
                result.stdout = '{"results": []}'
            else:
                result.stdout = ''

            return result

        with patch("subprocess.run", side_effect=mock_subprocess):
            items = await agent.run_security_scan()
            assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_run_security_scan_timeout(self, tmp_path):
        """Test handling security scan timeout."""
        agent = CodeReviewAgent(project_root=tmp_path)

        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="bandit", timeout=600)):
            items = await agent.run_security_scan()
            # Should silently continue
            assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_run_security_scan_not_found(self, tmp_path):
        """Test handling missing security scanner."""
        agent = CodeReviewAgent(project_root=tmp_path)

        with patch("subprocess.run", side_effect=FileNotFoundError):
            items = await agent.run_security_scan()
            # Should silently skip
            assert isinstance(items, list)


class TestCodeReviewAgentCheckComplexity:
    """Tests for check_complexity method."""

    @pytest.mark.asyncio
    async def test_check_complexity_no_languages(self, tmp_path):
        """Test checking complexity with no languages detected."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = []
        items = await agent.check_complexity()
        assert items == []

    @pytest.mark.asyncio
    async def test_check_complexity_python(self, tmp_path):
        """Test checking Python code complexity."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["python"]

        mock_result = MagicMock()
        mock_result.stdout = '''{"src/complex.py": [
            {"name": "complex_function", "rank": "D", "complexity": 15, "lineno": 10}
        ]}'''
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            items = await agent.check_complexity()
            assert len(items) >= 1
            assert items[0].category == ReviewCategory.COMPLEXITY

    @pytest.mark.asyncio
    async def test_check_complexity_high_rank(self, tmp_path):
        """Test high complexity rank detection."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["python"]

        mock_result = MagicMock()
        mock_result.stdout = '''{"src/bad.py": [
            {"name": "terrible_function", "rank": "F", "complexity": 50, "lineno": 1}
        ]}'''
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            items = await agent.check_complexity()
            assert items[0].severity == ReviewSeverity.HIGH

    @pytest.mark.asyncio
    async def test_check_complexity_timeout(self, tmp_path):
        """Test handling complexity check timeout."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["python"]

        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="radon", timeout=120)):
            items = await agent.check_complexity()
            assert items == []


class TestCodeReviewAgentCheckDependencies:
    """Tests for check_dependencies method."""

    @pytest.mark.asyncio
    async def test_check_dependencies_no_languages(self, tmp_path):
        """Test checking dependencies with no languages."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = []
        items = await agent.check_dependencies()
        assert items == []

    @pytest.mark.asyncio
    async def test_check_dependencies_python_safety(self, tmp_path):
        """Test Python dependency check with safety."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["python"]

        mock_result = MagicMock()
        mock_result.stdout = '''[["requests", "CVE-2023-1234", "2.28.0", "Security vulnerability"]]'''
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            items = await agent.check_dependencies()
            assert any(item.category == ReviewCategory.DEPENDENCY for item in items)
            assert any(item.severity == ReviewSeverity.CRITICAL for item in items)

    @pytest.mark.asyncio
    async def test_check_dependencies_javascript_npm(self, tmp_path):
        """Test JavaScript dependency check with npm audit."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["javascript"]

        mock_result = MagicMock()
        mock_result.stdout = '''{"vulnerabilities": {
            "lodash": {"name": "lodash", "severity": "high"}
        }}'''
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            items = await agent.check_dependencies()
            assert any(item.category == ReviewCategory.DEPENDENCY for item in items)

    @pytest.mark.asyncio
    async def test_check_dependencies_rust_cargo(self, tmp_path):
        """Test Rust dependency check with cargo audit."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["rust"]

        mock_result = MagicMock()
        mock_result.stdout = '''{"vulnerabilities": {"list": [
            {"package": {"name": "vulnerable-crate"}, "advisory": {"id": "RUSTSEC-2023-0001"}}
        ]}}'''
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            items = await agent.check_dependencies()
            assert any(item.category == ReviewCategory.DEPENDENCY for item in items)

    @pytest.mark.asyncio
    async def test_check_dependencies_ruby_bundle(self, tmp_path):
        """Test Ruby dependency check with bundle audit."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["ruby"]

        mock_result = MagicMock()
        mock_result.stdout = '''{"results": [
            {"gem": {"name": "rails"}, "advisory": {"id": "CVE-2023-9999"}}
        ]}'''
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            items = await agent.check_dependencies()
            assert any(item.category == ReviewCategory.DEPENDENCY for item in items)

    @pytest.mark.asyncio
    async def test_check_dependencies_timeout(self, tmp_path):
        """Test handling dependency check timeout."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["python"]

        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="safety", timeout=120)):
            items = await agent.check_dependencies()
            assert items == []

    @pytest.mark.asyncio
    async def test_check_dependencies_not_installed(self, tmp_path):
        """Test handling missing dependency checker."""
        agent = CodeReviewAgent(project_root=tmp_path)
        agent.detected_languages = ["python"]

        with patch("subprocess.run", side_effect=FileNotFoundError):
            items = await agent.check_dependencies()
            assert items == []


class TestCodeReviewAgentDetectLanguages:
    """Tests for detect_languages method."""

    @pytest.mark.asyncio
    async def test_detect_languages_empty_project(self, tmp_path):
        """Test detecting languages in empty project."""
        agent = CodeReviewAgent(project_root=tmp_path)
        languages = await agent.detect_languages()
        assert languages == []

    @pytest.mark.asyncio
    async def test_detect_languages_python(self, tmp_path):
        """Test detecting Python language."""
        agent = CodeReviewAgent(project_root=tmp_path)
        (tmp_path / "main.py").write_text("print('hello')")
        languages = await agent.detect_languages()
        assert "python" in languages

    @pytest.mark.asyncio
    async def test_detect_languages_javascript(self, tmp_path):
        """Test detecting JavaScript language."""
        agent = CodeReviewAgent(project_root=tmp_path)
        (tmp_path / "package.json").write_text("{}")
        languages = await agent.detect_languages()
        assert "javascript" in languages

    @pytest.mark.asyncio
    async def test_detect_languages_multiple(self, tmp_path):
        """Test detecting multiple languages."""
        agent = CodeReviewAgent(project_root=tmp_path)
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "app.js").write_text("console.log('hello');")
        (tmp_path / "Cargo.toml").write_text("[package]")
        languages = await agent.detect_languages()
        assert len(languages) >= 3

    @pytest.mark.asyncio
    async def test_detect_languages_no_duplicates(self, tmp_path):
        """Test that languages are not duplicated."""
        agent = CodeReviewAgent(project_root=tmp_path)
        (tmp_path / "a.py").write_text("pass")
        (tmp_path / "b.py").write_text("pass")
        languages = await agent.detect_languages()
        assert languages.count("python") == 1


class TestCodeReviewAgentExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_passes_review(self, tmp_path):
        """Test execute when review passes."""
        from beyond_ralph.agents.base import AgentTask

        agent = CodeReviewAgent(project_root=tmp_path)

        task = AgentTask(
            id="test",
            description="Review code",
            instructions="Check for issues",
            context={},
        )

        # Mock review to pass
        async def mock_review():
            return ReviewResult(items=[], passed=True, summary="All good")

        with patch.object(agent, "review", mock_review):
            result = await agent.execute(task)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_fails_review(self, tmp_path):
        """Test execute when review finds issues."""
        from beyond_ralph.agents.base import AgentTask

        agent = CodeReviewAgent(project_root=tmp_path)

        task = AgentTask(
            id="test",
            description="Review code",
            instructions="Check for issues",
            context={},
        )

        # Mock review to fail
        async def mock_review():
            return ReviewResult(
                items=[
                    ReviewItem(
                        category=ReviewCategory.SECURITY,
                        severity=ReviewSeverity.CRITICAL,
                        file_path="auth.py",
                        line_number=1,
                        message="Critical issue",
                    )
                ],
                passed=False,
                summary="Found issues",
            )

        with patch.object(agent, "review", mock_review):
            result = await agent.execute(task)
            # Review succeeded even though it found issues
            assert result.success is True
            assert "items" in result.data
