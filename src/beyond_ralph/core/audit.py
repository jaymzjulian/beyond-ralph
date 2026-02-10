"""Implementation Audit - Static analysis for stubs, fakes, and TODOs.

Prong 1 of the Implementation Audit system. Provides fast, deterministic
scanning of project source files for patterns that indicate fake/stub
implementations.

Used by:
- Phase 9 (IMPLEMENTATION_AUDIT) for thorough checking
- Stop hook as a safety gate before accepting AUTOMATION_COMPLETE
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class AuditSeverity(Enum):
    """Severity of an audit finding."""

    CRITICAL = "critical"  # Definitely a stub (NotImplementedError, bare pass)
    HIGH = "high"  # Very likely a stub (TODO, FIXME, placeholder strings)
    MEDIUM = "medium"  # Possibly a stub (empty except blocks, hardcoded test data)
    LOW = "low"  # Worth reviewing (bare return None, ellipsis)


@dataclass
class AuditFinding:
    """A single finding from static audit."""

    file: str
    line_number: int
    pattern_name: str
    severity: AuditSeverity
    line_text: str
    context: str = ""


@dataclass
class StaticAuditResult:
    """Result of static audit scan."""

    findings: list[AuditFinding] = field(default_factory=list)
    files_scanned: int = 0

    @property
    def passed(self) -> bool:
        """True if no CRITICAL or HIGH findings."""
        return self.critical_count == 0 and self.high_count == 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == AuditSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == AuditSeverity.HIGH)

    def summary(self) -> str:
        if not self.findings:
            return f"Static audit PASSED: {self.files_scanned} files scanned, 0 findings"
        return (
            f"Static audit {'PASSED' if self.passed else 'FAILED'}: "
            f"{len(self.findings)} findings "
            f"({self.critical_count} critical, {self.high_count} high) "
            f"in {self.files_scanned} files"
        )


# Patterns to search for, with severity classification
STUB_PATTERNS: list[tuple[str, str, AuditSeverity]] = [
    # CRITICAL - almost certainly stubs
    (r"raise\s+NotImplementedError", "NotImplementedError", AuditSeverity.CRITICAL),
    (r"raise\s+NotImplemented\b", "NotImplemented (wrong form)", AuditSeverity.CRITICAL),
    # HIGH - strong indicators of incomplete implementation
    (r"\bTODO\b", "TODO marker", AuditSeverity.HIGH),
    (r"\bFIXME\b", "FIXME marker", AuditSeverity.HIGH),
    (r"\bHACK\b", "HACK marker", AuditSeverity.HIGH),
    (r"\bXXX\b", "XXX marker", AuditSeverity.HIGH),
    (
        r"""['"](?:placeholder|stub|fake|dummy|implement\s*me|not\s*implemented)['"]""",
        "placeholder string literal",
        AuditSeverity.HIGH,
    ),
    # MEDIUM - contextual indicators
    (
        r"""['"](?:test_?data|sample_?data|example_?data|lorem\s*ipsum)['"]""",
        "hardcoded test/sample data",
        AuditSeverity.MEDIUM,
    ),
]

# File extensions to scan
CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".kt", ".java", ".go", ".rs", ".rb"}

# Directories to skip
SKIP_DIRS = {
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".gradle",
    "build",
    "dist",
}


def run_static_audit(
    project_root: Path,
    source_dirs: list[str] | None = None,
    skip_test_files: bool = True,
    min_severity: AuditSeverity = AuditSeverity.HIGH,
) -> StaticAuditResult:
    """Run static analysis audit on project source files.

    Args:
        project_root: Root directory of the project.
        source_dirs: Directories to scan (relative to root). If None, scans ["src", "app", "lib"].
        skip_test_files: Skip files matching test_* or *_test.*.
        min_severity: Minimum severity to include in results.

    Returns:
        StaticAuditResult with findings.
    """
    if source_dirs is None:
        source_dirs = ["src", "app", "lib"]

    severity_order = [AuditSeverity.CRITICAL, AuditSeverity.HIGH, AuditSeverity.MEDIUM, AuditSeverity.LOW]
    min_index = severity_order.index(min_severity)
    active_severities = set(severity_order[: min_index + 1])

    result = StaticAuditResult()

    for source_dir in source_dirs:
        scan_root = project_root / source_dir
        if not scan_root.exists():
            continue

        for file_path in scan_root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in CODE_EXTENSIONS:
                continue
            if any(skip in file_path.parts for skip in SKIP_DIRS):
                continue
            if skip_test_files and _is_test_file(file_path):
                continue

            result.files_scanned += 1
            _scan_file(file_path, project_root, result, active_severities)

    return result


def _is_test_file(file_path: Path) -> bool:
    """Check if a file is a test file."""
    name = file_path.name
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith("_test.js")
        or name.endswith("_test.ts")
        or name.endswith(".test.js")
        or name.endswith(".test.ts")
        or name.endswith(".test.tsx")
        or name.endswith(".test.jsx")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.js")
        or "conftest" in name
    )


def _scan_file(
    file_path: Path,
    project_root: Path,
    result: StaticAuditResult,
    active_severities: set[AuditSeverity],
) -> None:
    """Scan a single file for stub patterns."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    lines = content.split("\n")
    rel_path = str(file_path.relative_to(project_root))

    for pattern_str, pattern_name, severity in STUB_PATTERNS:
        if severity not in active_severities:
            continue
        for i, line in enumerate(lines, 1):
            if re.search(pattern_str, line, re.IGNORECASE):
                result.findings.append(
                    AuditFinding(
                        file=rel_path,
                        line_number=i,
                        pattern_name=pattern_name,
                        severity=severity,
                        line_text=line.strip(),
                    )
                )

    # Special check: functions/methods with only `pass` or `...` as body
    if AuditSeverity.CRITICAL in active_severities:
        _check_empty_function_bodies(lines, rel_path, result)


def _check_empty_function_bodies(
    lines: list[str],
    rel_path: str,
    result: StaticAuditResult,
) -> None:
    """Check for functions whose body is just pass or ellipsis (after docstring)."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(("def ", "async def ")):
            continue

        body_line = _get_first_body_line(lines, i)
        if body_line is not None and body_line.strip() in ("pass", "..."):
            result.findings.append(
                AuditFinding(
                    file=rel_path,
                    line_number=i + 1,
                    pattern_name="empty function body (pass/...)",
                    severity=AuditSeverity.CRITICAL,
                    line_text=stripped,
                    context=f"Body: {body_line.strip()}",
                )
            )


def _get_first_body_line(lines: list[str], def_index: int) -> str | None:
    """Get the first meaningful body line after a function definition."""
    in_docstring = False
    for i in range(def_index + 1, min(def_index + 30, len(lines))):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Handle docstrings
        if '"""' in stripped or "'''" in stripped:
            count = stripped.count('"""') + stripped.count("'''")
            if count >= 2:
                continue  # single-line docstring
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        return lines[i]
    return None


def quick_audit_for_hook(project_root: Path) -> tuple[bool, str]:
    """Fast audit check for the stop hook.

    Returns:
        Tuple of (passed: bool, summary: str)
    """
    result = run_static_audit(project_root, min_severity=AuditSeverity.HIGH)
    return result.passed, result.summary()
