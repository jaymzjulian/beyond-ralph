"""Tests for the Implementation Audit module (static analysis)."""

from __future__ import annotations

from pathlib import Path

from beyond_ralph.core.audit import (
    AuditFinding,
    AuditSeverity,
    StaticAuditResult,
    _check_empty_function_bodies,
    _get_first_body_line,
    _is_test_file,
    quick_audit_for_hook,
    run_static_audit,
)


class TestAuditSeverity:
    """Tests for AuditSeverity enum."""

    def test_severity_values(self) -> None:
        assert AuditSeverity.CRITICAL.value == "critical"
        assert AuditSeverity.HIGH.value == "high"
        assert AuditSeverity.MEDIUM.value == "medium"
        assert AuditSeverity.LOW.value == "low"


class TestStaticAuditResult:
    """Tests for StaticAuditResult dataclass."""

    def test_empty_result_passes(self) -> None:
        result = StaticAuditResult(files_scanned=5)
        assert result.passed is True
        assert result.critical_count == 0
        assert result.high_count == 0

    def test_critical_finding_fails(self) -> None:
        result = StaticAuditResult(
            findings=[
                AuditFinding(
                    file="test.py",
                    line_number=1,
                    pattern_name="NotImplementedError",
                    severity=AuditSeverity.CRITICAL,
                    line_text="raise NotImplementedError",
                )
            ],
            files_scanned=1,
        )
        assert result.passed is False
        assert result.critical_count == 1

    def test_high_finding_fails(self) -> None:
        result = StaticAuditResult(
            findings=[
                AuditFinding(
                    file="test.py",
                    line_number=1,
                    pattern_name="TODO marker",
                    severity=AuditSeverity.HIGH,
                    line_text="# TODO: implement this",
                )
            ],
            files_scanned=1,
        )
        assert result.passed is False
        assert result.high_count == 1

    def test_medium_finding_passes(self) -> None:
        result = StaticAuditResult(
            findings=[
                AuditFinding(
                    file="test.py",
                    line_number=1,
                    pattern_name="test data",
                    severity=AuditSeverity.MEDIUM,
                    line_text="data = 'test_data'",
                )
            ],
            files_scanned=1,
        )
        assert result.passed is True

    def test_summary_no_findings(self) -> None:
        result = StaticAuditResult(files_scanned=10)
        assert "PASSED" in result.summary()
        assert "0 findings" in result.summary()

    def test_summary_with_findings(self) -> None:
        result = StaticAuditResult(
            findings=[
                AuditFinding(
                    file="test.py",
                    line_number=1,
                    pattern_name="TODO",
                    severity=AuditSeverity.HIGH,
                    line_text="# TODO",
                ),
                AuditFinding(
                    file="test.py",
                    line_number=2,
                    pattern_name="NotImplementedError",
                    severity=AuditSeverity.CRITICAL,
                    line_text="raise NotImplementedError",
                ),
            ],
            files_scanned=5,
        )
        summary = result.summary()
        assert "FAILED" in summary
        assert "1 critical" in summary
        assert "1 high" in summary


class TestIsTestFile:
    """Tests for _is_test_file."""

    def test_python_test_file(self) -> None:
        assert _is_test_file(Path("test_something.py")) is True

    def test_python_test_suffix(self) -> None:
        assert _is_test_file(Path("something_test.py")) is True

    def test_js_test_file(self) -> None:
        assert _is_test_file(Path("component.test.js")) is True

    def test_ts_spec_file(self) -> None:
        assert _is_test_file(Path("service.spec.ts")) is True

    def test_conftest(self) -> None:
        assert _is_test_file(Path("conftest.py")) is True

    def test_normal_file(self) -> None:
        assert _is_test_file(Path("main.py")) is False

    def test_tsx_test_file(self) -> None:
        assert _is_test_file(Path("App.test.tsx")) is True


class TestGetFirstBodyLine:
    """Tests for _get_first_body_line."""

    def test_simple_function(self) -> None:
        lines = [
            "def foo():",
            "    return 42",
        ]
        assert _get_first_body_line(lines, 0) is not None
        assert "return 42" in _get_first_body_line(lines, 0)  # type: ignore[operator]

    def test_function_with_docstring(self) -> None:
        lines = [
            "def foo():",
            '    """Do something."""',
            "    return 42",
        ]
        result = _get_first_body_line(lines, 0)
        assert result is not None
        assert "return 42" in result

    def test_function_with_multiline_docstring(self) -> None:
        lines = [
            "def foo():",
            '    """',
            "    Do something.",
            '    """',
            "    return 42",
        ]
        result = _get_first_body_line(lines, 0)
        assert result is not None
        assert "return 42" in result

    def test_stub_function_with_pass(self) -> None:
        lines = [
            "def foo():",
            '    """Stub."""',
            "    pass",
        ]
        result = _get_first_body_line(lines, 0)
        assert result is not None
        assert result.strip() == "pass"

    def test_stub_function_with_ellipsis(self) -> None:
        lines = [
            "def foo():",
            "    ...",
        ]
        result = _get_first_body_line(lines, 0)
        assert result is not None
        assert result.strip() == "..."


class TestCheckEmptyFunctionBodies:
    """Tests for _check_empty_function_bodies."""

    def test_detects_pass_body(self) -> None:
        lines = [
            "def foo():",
            "    pass",
        ]
        result = StaticAuditResult()
        _check_empty_function_bodies(lines, "test.py", result)
        assert len(result.findings) == 1
        assert result.findings[0].severity == AuditSeverity.CRITICAL
        assert result.findings[0].pattern_name == "empty function body (pass/...)"

    def test_detects_ellipsis_body(self) -> None:
        lines = [
            "def foo():",
            "    ...",
        ]
        result = StaticAuditResult()
        _check_empty_function_bodies(lines, "test.py", result)
        assert len(result.findings) == 1

    def test_detects_pass_after_docstring(self) -> None:
        lines = [
            "def foo():",
            '    """Do something."""',
            "    pass",
        ]
        result = StaticAuditResult()
        _check_empty_function_bodies(lines, "test.py", result)
        assert len(result.findings) == 1

    def test_real_function_no_finding(self) -> None:
        lines = [
            "def foo():",
            '    """Do something."""',
            "    return 42",
        ]
        result = StaticAuditResult()
        _check_empty_function_bodies(lines, "test.py", result)
        assert len(result.findings) == 0

    def test_async_def_detected(self) -> None:
        lines = [
            "async def bar():",
            "    pass",
        ]
        result = StaticAuditResult()
        _check_empty_function_bodies(lines, "test.py", result)
        assert len(result.findings) == 1


class TestRunStaticAudit:
    """Tests for run_static_audit using tmp_path."""

    def test_clean_project_passes(self, tmp_path: Path) -> None:
        """A project with real implementations should pass."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text(
            "def greet(name: str) -> str:\n"
            '    return f"Hello, {name}!"\n'
        )
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.passed is True
        assert result.files_scanned == 1

    def test_detects_not_implemented_error(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "stub.py").write_text(
            "def do_something():\n"
            "    raise NotImplementedError\n"
        )
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.passed is False
        assert result.critical_count >= 1

    def test_detects_todo(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "wip.py").write_text(
            "def process():\n"
            "    # TODO: implement this\n"
            "    return None\n"
        )
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.passed is False
        assert result.high_count >= 1

    def test_detects_fixme(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "wip.py").write_text(
            "def process():\n"
            "    # FIXME: broken\n"
            "    return None\n"
        )
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.passed is False

    def test_detects_placeholder_string(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "fake.py").write_text(
            "def get_result():\n"
            "    return 'placeholder'\n"
        )
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.passed is False
        assert any(f.pattern_name == "placeholder string literal" for f in result.findings)

    def test_detects_empty_pass_body(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "empty.py").write_text(
            "def important_function():\n"
            '    """This should do something important."""\n'
            "    pass\n"
        )
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.passed is False
        assert any("empty function body" in f.pattern_name for f in result.findings)

    def test_skips_test_files(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "test_something.py").write_text(
            "def test_foo():\n"
            "    # TODO: write real test\n"
            "    pass\n"
        )
        result = run_static_audit(tmp_path, source_dirs=["src"], skip_test_files=True)
        assert result.passed is True
        assert result.files_scanned == 0

    def test_includes_test_files_when_requested(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "test_something.py").write_text(
            "def test_foo():\n"
            "    # TODO: write real test\n"
            "    pass\n"
        )
        result = run_static_audit(tmp_path, source_dirs=["src"], skip_test_files=False)
        assert result.files_scanned == 1

    def test_skips_pycache(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        pycache = src / "__pycache__"
        pycache.mkdir(parents=True)
        (pycache / "cached.py").write_text("raise NotImplementedError\n")
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.files_scanned == 0

    def test_nonexistent_source_dir(self, tmp_path: Path) -> None:
        result = run_static_audit(tmp_path, source_dirs=["nonexistent"])
        assert result.passed is True
        assert result.files_scanned == 0

    def test_min_severity_medium(self, tmp_path: Path) -> None:
        """With medium severity, should also find medium-level patterns."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "data.py").write_text(
            "config = 'test_data'\n"
        )
        result = run_static_audit(
            tmp_path, source_dirs=["src"], min_severity=AuditSeverity.MEDIUM
        )
        assert any(f.severity == AuditSeverity.MEDIUM for f in result.findings)

    def test_non_code_files_skipped(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "readme.md").write_text("# TODO: write docs\n")
        (src / "config.yaml").write_text("# TODO: configure\n")
        result = run_static_audit(tmp_path, source_dirs=["src"])
        assert result.files_scanned == 0


class TestQuickAuditForHook:
    """Tests for quick_audit_for_hook interface."""

    def test_clean_project(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "clean.py").write_text(
            "def hello() -> str:\n"
            '    return "world"\n'
        )
        passed, summary = quick_audit_for_hook(tmp_path)
        assert passed is True
        assert "PASSED" in summary

    def test_stubbed_project(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "stub.py").write_text(
            "def hello():\n"
            "    raise NotImplementedError\n"
        )
        passed, summary = quick_audit_for_hook(tmp_path)
        assert passed is False
        assert "FAILED" in summary

    def test_returns_tuple(self, tmp_path: Path) -> None:
        passed, summary = quick_audit_for_hook(tmp_path)
        assert isinstance(passed, bool)
        assert isinstance(summary, str)
