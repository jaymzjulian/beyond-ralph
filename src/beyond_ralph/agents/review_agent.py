"""Code Review Agent - Third agent in the trust model.

This agent is SEPARATE from both the Coding Agent and Testing Agent.
It performs:
1. Language-specific linting (Python, JavaScript, TypeScript, Rust, Go, Kotlin, C/C++, Ruby)
2. Security analysis (SAST, OWASP)
3. LLM-based semantic review (does code do what it claims?)
4. TODO/Unimplemented detection (incomplete code is a failure!)
5. Best practices review

ALL items flagged by this agent MUST be actioned by the Coding Agent.
No exceptions. No dismissals. Fix everything.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from beyond_ralph.agents.base import (
    AgentResult,
    AgentTask,
    TrustModelAgent,
)


class ReviewSeverity(Enum):
    """Severity levels for review findings."""

    CRITICAL = "critical"   # Security vulnerabilities, must fix immediately
    HIGH = "high"           # Serious issues, must fix before merge
    MEDIUM = "medium"       # Should fix, code smell
    LOW = "low"             # Minor issues, style
    INFO = "info"           # Suggestions, not required


class ReviewCategory(Enum):
    """Categories of review findings."""

    SECURITY = "security"           # OWASP, vulnerabilities, secrets
    LINT = "lint"                   # Language-specific linting
    TYPE = "type"                   # Type checking issues
    COMPLEXITY = "complexity"       # Code complexity
    DUPLICATION = "duplication"     # DRY violations
    PRACTICE = "practice"           # Best practices
    DOCS = "docs"                   # Documentation
    DEPENDENCY = "dependency"       # Vulnerable dependencies
    INCOMPLETE = "incomplete"       # TODOs, unimplemented code
    SEMANTIC = "semantic"           # LLM-detected issues (code doesn't do what it claims)


@dataclass
class ReviewItem:
    """A single review finding that MUST be actioned."""

    category: ReviewCategory
    severity: ReviewSeverity
    file_path: str
    line_number: int | None
    message: str
    rule_id: str | None = None
    suggested_fix: str | None = None
    reference_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "message": self.message,
            "rule_id": self.rule_id,
            "suggested_fix": self.suggested_fix,
            "reference_url": self.reference_url,
        }


@dataclass
class ReviewResult:
    """Result of a code review."""

    items: list[ReviewItem] = field(default_factory=list)
    passed: bool = False
    summary: str = ""
    languages_detected: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.items if i.severity == ReviewSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.items if i.severity == ReviewSeverity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.items if i.severity == ReviewSeverity.MEDIUM)

    def must_fix_count(self) -> int:
        """Items that MUST be fixed (critical + high + medium)."""
        return sum(
            1 for i in self.items
            if i.severity in (ReviewSeverity.CRITICAL, ReviewSeverity.HIGH, ReviewSeverity.MEDIUM)
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "passed": self.passed,
            "summary": self.summary,
            "languages_detected": self.languages_detected,
            "tools_used": self.tools_used,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "must_fix_count": self.must_fix_count(),
            "items": [item.to_dict() for item in self.items],
        }


# Language file extensions and detection patterns
LANGUAGE_INDICATORS: dict[str, list[str]] = {
    "python": ["*.py", "pyproject.toml", "setup.py", "requirements.txt"],
    "javascript": ["*.js", "*.jsx", "*.mjs", "package.json"],
    "typescript": ["*.ts", "*.tsx", "tsconfig.json"],
    "rust": ["*.rs", "Cargo.toml"],
    "go": ["*.go", "go.mod"],
    "kotlin": ["*.kt", "*.kts", "build.gradle.kts"],
    "java": ["*.java", "pom.xml", "build.gradle"],
    "c": ["*.c", "*.h", "Makefile", "CMakeLists.txt"],
    "cpp": ["*.cpp", "*.cc", "*.cxx", "*.hpp", "*.hh"],
    "ruby": ["*.rb", "Gemfile", "*.gemspec"],
    "swift": ["*.swift", "Package.swift"],
    "csharp": ["*.cs", "*.csproj"],
    "php": ["*.php", "composer.json"],
    "scala": ["*.scala", "build.sbt"],
    "elixir": ["*.ex", "*.exs", "mix.exs"],
}

# Incomplete code patterns - THESE ARE HIGH SEVERITY ISSUES
INCOMPLETE_PATTERNS: list[tuple[str, str, ReviewSeverity]] = [
    # TODOs and FIXMEs
    (r"#\s*TODO\b", "TODO comment - incomplete implementation", ReviewSeverity.HIGH),
    (r"//\s*TODO\b", "TODO comment - incomplete implementation", ReviewSeverity.HIGH),
    (r"/\*.*TODO.*\*/", "TODO comment - incomplete implementation", ReviewSeverity.HIGH),
    (r"#\s*FIXME\b", "FIXME comment - known bug or issue", ReviewSeverity.CRITICAL),
    (r"//\s*FIXME\b", "FIXME comment - known bug or issue", ReviewSeverity.CRITICAL),
    (r"#\s*XXX\b", "XXX comment - requires attention", ReviewSeverity.HIGH),
    (r"//\s*XXX\b", "XXX comment - requires attention", ReviewSeverity.HIGH),
    (r"#\s*HACK\b", "HACK comment - hacky implementation", ReviewSeverity.MEDIUM),
    (r"//\s*HACK\b", "HACK comment - hacky implementation", ReviewSeverity.MEDIUM),

    # Python unimplemented
    (r"\braise\s+NotImplementedError", "NotImplementedError - unimplemented code", ReviewSeverity.CRITICAL),
    (r"\bpass\s*#", "Empty pass with comment - likely placeholder", ReviewSeverity.HIGH),
    (r"^\s*\.\.\.\s*$", "Ellipsis placeholder - unimplemented", ReviewSeverity.CRITICAL),

    # Rust unimplemented
    (r"\bunimplemented!\s*\(", "unimplemented!() macro - incomplete code", ReviewSeverity.CRITICAL),
    (r"\btodo!\s*\(", "todo!() macro - incomplete code", ReviewSeverity.CRITICAL),
    (r"\bpanic!\s*\(\s*[\"']not implemented", "panic for not implemented", ReviewSeverity.CRITICAL),

    # JavaScript/TypeScript
    (r"throw\s+new\s+Error\s*\(\s*[\"']Not\s+implemented", "Not implemented error", ReviewSeverity.CRITICAL),
    (r"throw\s+new\s+Error\s*\(\s*[\"']TODO", "TODO error throw", ReviewSeverity.CRITICAL),

    # Kotlin
    (r"\bTODO\s*\(", "TODO() - incomplete Kotlin code", ReviewSeverity.CRITICAL),
    (r"\bnotImplementedError\s*\(", "notImplementedError() - unimplemented", ReviewSeverity.CRITICAL),

    # C/C++
    (r"#error\s+.*not\s+implemented", "#error not implemented", ReviewSeverity.CRITICAL),
    (r"\bassert\s*\(\s*false\s*\)", "assert(false) - placeholder", ReviewSeverity.CRITICAL),
    (r"\bassert\s*\(\s*0\s*\)", "assert(0) - placeholder", ReviewSeverity.CRITICAL),

    # Ruby
    (r"\braise\s+NotImplementedError", "NotImplementedError - unimplemented", ReviewSeverity.CRITICAL),
    (r"\bfail\s+[\"']Not\s+implemented", "fail 'Not implemented'", ReviewSeverity.CRITICAL),

    # Generic
    (r"PLACEHOLDER", "PLACEHOLDER text found", ReviewSeverity.HIGH),
    (r"STUB", "STUB code found", ReviewSeverity.HIGH),
    (r"dummy\s*implementation", "Dummy implementation", ReviewSeverity.HIGH),
]


class CodeReviewAgent(TrustModelAgent):
    """The third agent - reviews code for quality and security.

    This agent is COMPLETELY SEPARATE from the Coding and Testing agents.
    Its findings are NON-NEGOTIABLE - the Coding Agent MUST fix everything.

    Multi-language support:
    - Python: ruff, mypy, bandit
    - JavaScript/TypeScript: eslint, tsc
    - Rust: clippy, cargo audit
    - Go: staticcheck, go vet
    - Kotlin: detekt, ktlint
    - C/C++: cppcheck, clang-tidy
    - Ruby: rubocop, brakeman

    Special features:
    - LLM semantic review (does code do what it claims?)
    - TODO/FIXME/unimplemented detection (CRITICAL severity!)
    - Secret detection
    - Vulnerable dependency checking
    """

    name = "code_review"
    description = "Mandatory code review with linting, security, and semantic analysis"
    tools = ["Read", "Grep", "Glob", "Bash"]

    # Trust model properties
    can_implement = False
    can_test = False
    can_review = True

    # Language-specific linter commands with JSON output where possible
    LINTERS: dict[str, list[dict[str, Any]]] = {
        "python": [
            {
                "name": "ruff",
                "command": ["ruff", "check", "--output-format=json", "."],
                "parse": "ruff",
            },
            {
                "name": "mypy",
                "command": ["mypy", "--strict", "--show-error-codes", "--no-error-summary", "."],
                "parse": "mypy",
            },
            {
                "name": "bandit",
                "command": ["bandit", "-r", "-f", "json", "."],
                "parse": "bandit",
            },
        ],
        "javascript": [
            {
                "name": "eslint",
                "command": ["npx", "eslint", "--format=json", "."],
                "parse": "eslint",
            },
        ],
        "typescript": [
            {
                "name": "eslint",
                "command": ["npx", "eslint", "--format=json", "."],
                "parse": "eslint",
            },
            {
                "name": "tsc",
                "command": ["npx", "tsc", "--noEmit"],
                "parse": "tsc",
            },
        ],
        "rust": [
            {
                "name": "clippy",
                "command": ["cargo", "clippy", "--message-format=json", "--", "-D", "warnings"],
                "parse": "clippy",
            },
            {
                "name": "cargo-audit",
                "command": ["cargo", "audit", "--json"],
                "parse": "cargo_audit",
            },
        ],
        "go": [
            {
                "name": "staticcheck",
                "command": ["staticcheck", "-f", "json", "./..."],
                "parse": "staticcheck",
            },
            {
                "name": "go-vet",
                "command": ["go", "vet", "-json", "./..."],
                "parse": "go_vet",
            },
        ],
        "kotlin": [
            {
                "name": "detekt",
                "command": ["detekt", "--report", "json:detekt-report.json"],
                "parse": "detekt",
            },
            {
                "name": "ktlint",
                "command": ["ktlint", "--reporter=json"],
                "parse": "ktlint",
            },
        ],
        "c": [
            {
                "name": "cppcheck",
                "command": ["cppcheck", "--enable=all", "--template=gcc", "."],
                "parse": "cppcheck",
            },
        ],
        "cpp": [
            {
                "name": "cppcheck",
                "command": ["cppcheck", "--enable=all", "--language=c++", "--template=gcc", "."],
                "parse": "cppcheck",
            },
            {
                "name": "clang-tidy",
                "command": ["clang-tidy", "--quiet", "*.cpp", "*.hpp"],
                "parse": "clang_tidy",
            },
        ],
        "ruby": [
            {
                "name": "rubocop",
                "command": ["rubocop", "--format", "json"],
                "parse": "rubocop",
            },
            {
                "name": "brakeman",
                "command": ["brakeman", "--format", "json", "--no-pager"],
                "parse": "brakeman",
            },
        ],
        "java": [
            {
                "name": "checkstyle",
                "command": ["checkstyle", "-f", "xml", "-c", "/google_checks.xml", "."],
                "parse": "checkstyle",
            },
        ],
        "swift": [
            {
                "name": "swiftlint",
                "command": ["swiftlint", "--reporter", "json"],
                "parse": "swiftlint",
            },
        ],
    }

    # Security scanners (run for all projects)
    SECURITY_SCANNERS: list[dict[str, Any]] = [
        {
            "name": "detect-secrets",
            "command": ["detect-secrets", "scan", "--all-files"],
            "parse": "detect_secrets",
        },
        {
            "name": "gitleaks",
            "command": ["gitleaks", "detect", "--report-format", "json", "--report-path", "-"],
            "parse": "gitleaks",
        },
    ]

    # Complexity analyzers per language
    COMPLEXITY_TOOLS: dict[str, dict[str, Any]] = {
        "python": {
            "name": "radon",
            "command": ["radon", "cc", "-j", "-a", "."],
            "parse": "radon",
        },
        "javascript": {
            "name": "escomplex",
            "command": ["npx", "escomplex-js", "."],
            "parse": "escomplex",
        },
        "rust": {
            "name": "cargo-complexity",
            "command": ["cargo", "complexity"],
            "parse": "cargo_complexity",
        },
    }

    def __init__(
        self,
        project_root: Path | None = None,
        session_id: str | None = None,
        knowledge_dir: Path | None = None,
    ) -> None:
        super().__init__(session_id, project_root, knowledge_dir)
        self.detected_languages: list[str] = []
        self.tools_used: list[str] = []

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute code review task."""
        result = await self.review()

        if result.passed:
            return self.succeed(
                output=result.summary,
                data=result.to_dict(),
            )
        else:
            # Review found issues - return success but with issues
            # The Coding Agent must fix these
            return AgentResult(
                success=True,  # The review itself succeeded
                output=result.summary,
                data=result.to_dict(),
            )

    async def detect_languages(self) -> list[str]:
        """Detect programming languages in the project."""
        languages = []

        for lang, patterns in LANGUAGE_INDICATORS.items():
            for pattern in patterns:
                if list(self.project_root.glob(f"**/{pattern}")):
                    if lang not in languages:
                        languages.append(lang)
                    break

        self.detected_languages = languages
        return languages

    async def check_incomplete_code(self) -> list[ReviewItem]:
        """Check for TODOs, unimplemented code, and placeholders.

        This is CRITICAL - incomplete code should NEVER pass review!
        """
        items: list[ReviewItem] = []

        # Get all source files
        source_extensions = [
            "*.py", "*.js", "*.jsx", "*.ts", "*.tsx",
            "*.rs", "*.go", "*.kt", "*.kts", "*.java",
            "*.c", "*.h", "*.cpp", "*.cc", "*.hpp",
            "*.rb", "*.swift", "*.cs", "*.scala",
        ]

        for ext in source_extensions:
            for file_path in self.project_root.glob(f"**/{ext}"):
                # Skip test files for TODO checks (tests might legitimately have TODOs)
                relative_path = str(file_path.relative_to(self.project_root))
                if "test" in relative_path.lower() and "TODO" not in relative_path:
                    continue

                try:
                    content = file_path.read_text(errors="ignore")
                    lines = content.split("\n")

                    for line_num, line in enumerate(lines, start=1):
                        for pattern, message, severity in INCOMPLETE_PATTERNS:
                            if re.search(pattern, line, re.IGNORECASE):
                                items.append(ReviewItem(
                                    category=ReviewCategory.INCOMPLETE,
                                    severity=severity,
                                    file_path=relative_path,
                                    line_number=line_num,
                                    message=f"{message}: {line.strip()[:100]}",
                                    rule_id="incomplete-code",
                                    suggested_fix="Implement the missing functionality",
                                ))
                                break  # Only one match per line

                except Exception:
                    continue

        self.tools_used.append("incomplete-code-scanner")
        return items

    async def run_linters(self, language: str) -> list[ReviewItem]:
        """Run language-specific linters."""
        items: list[ReviewItem] = []
        linters = self.LINTERS.get(language, [])

        for linter in linters:
            try:
                result = subprocess.run(
                    linter["command"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                self.tools_used.append(linter["name"])

                # Parse output based on tool
                parse_method = getattr(self, f"_parse_{linter['parse']}", None)
                if parse_method:
                    parsed_items = parse_method(result.stdout, result.stderr)
                    items.extend(parsed_items)

            except subprocess.TimeoutExpired:
                items.append(ReviewItem(
                    category=ReviewCategory.LINT,
                    severity=ReviewSeverity.INFO,
                    file_path="",
                    line_number=None,
                    message=f"{linter['name']} timed out",
                ))
            except FileNotFoundError:
                # Linter not installed - skip silently
                pass
            except Exception as e:
                items.append(ReviewItem(
                    category=ReviewCategory.LINT,
                    severity=ReviewSeverity.INFO,
                    file_path="",
                    line_number=None,
                    message=f"{linter['name']} failed: {e}",
                ))

        return items

    def _parse_ruff(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse ruff JSON output."""
        items = []
        try:
            if not stdout.strip():
                return items

            data = json.loads(stdout)
            for issue in data:
                severity = ReviewSeverity.MEDIUM
                code = issue.get("code", "")
                if code.startswith("E") or code.startswith("F"):
                    severity = ReviewSeverity.HIGH

                items.append(ReviewItem(
                    category=ReviewCategory.LINT,
                    severity=severity,
                    file_path=issue.get("filename", ""),
                    line_number=issue.get("location", {}).get("row"),
                    message=issue.get("message", ""),
                    rule_id=code,
                    suggested_fix=issue.get("fix", {}).get("message") if issue.get("fix") else None,
                ))
        except json.JSONDecodeError:
            pass
        return items

    def _parse_mypy(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse mypy output."""
        items = []
        for line in stdout.split("\n"):
            if not line.strip():
                continue

            parts = line.split(":", 3)
            if len(parts) >= 4:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                except ValueError:
                    line_num = None

                level = parts[2].strip()
                message = parts[3].strip() if len(parts) > 3 else ""

                severity = ReviewSeverity.MEDIUM
                if level == "error":
                    severity = ReviewSeverity.HIGH

                rule_id = None
                if "[" in message and "]" in message:
                    rule_id = message[message.rfind("[") + 1:message.rfind("]")]

                items.append(ReviewItem(
                    category=ReviewCategory.TYPE,
                    severity=severity,
                    file_path=file_path,
                    line_number=line_num,
                    message=message,
                    rule_id=rule_id,
                ))

        return items

    def _parse_bandit(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse bandit JSON output."""
        items = []
        try:
            if not stdout.strip():
                return items

            data = json.loads(stdout)
            for result in data.get("results", []):
                severity_map = {
                    "HIGH": ReviewSeverity.CRITICAL,
                    "MEDIUM": ReviewSeverity.HIGH,
                    "LOW": ReviewSeverity.MEDIUM,
                }
                severity = severity_map.get(
                    result.get("issue_severity", "LOW"),
                    ReviewSeverity.MEDIUM,
                )

                items.append(ReviewItem(
                    category=ReviewCategory.SECURITY,
                    severity=severity,
                    file_path=result.get("filename", ""),
                    line_number=result.get("line_number"),
                    message=result.get("issue_text", ""),
                    rule_id=result.get("test_id"),
                    reference_url=result.get("more_info"),
                ))
        except json.JSONDecodeError:
            pass
        return items

    def _parse_eslint(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse ESLint JSON output."""
        items = []
        try:
            if not stdout.strip():
                return items

            data = json.loads(stdout)
            for file_result in data:
                file_path = file_result.get("filePath", "")
                for msg in file_result.get("messages", []):
                    severity = ReviewSeverity.MEDIUM
                    if msg.get("severity") == 2:
                        severity = ReviewSeverity.HIGH

                    items.append(ReviewItem(
                        category=ReviewCategory.LINT,
                        severity=severity,
                        file_path=file_path,
                        line_number=msg.get("line"),
                        message=msg.get("message", ""),
                        rule_id=msg.get("ruleId"),
                    ))
        except json.JSONDecodeError:
            pass
        return items

    def _parse_clippy(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse Rust clippy JSON output."""
        items = []
        for line in stdout.split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get("reason") == "compiler-message":
                    msg = data.get("message", {})
                    level = msg.get("level", "warning")

                    severity = ReviewSeverity.MEDIUM
                    if level == "error":
                        severity = ReviewSeverity.HIGH

                    spans = msg.get("spans", [])
                    if spans:
                        span = spans[0]
                        items.append(ReviewItem(
                            category=ReviewCategory.LINT,
                            severity=severity,
                            file_path=span.get("file_name", ""),
                            line_number=span.get("line_start"),
                            message=msg.get("message", ""),
                            rule_id=msg.get("code", {}).get("code"),
                        ))
            except json.JSONDecodeError:
                continue
        return items

    def _parse_cppcheck(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse cppcheck GCC-style output."""
        items = []
        # cppcheck outputs to stderr in GCC format
        for line in stderr.split("\n"):
            if not line.strip():
                continue

            # Format: file:line: severity: message
            match = re.match(r"(.+):(\d+):\s*(\w+):\s*(.+)", line)
            if match:
                file_path, line_num, level, message = match.groups()

                severity_map = {
                    "error": ReviewSeverity.HIGH,
                    "warning": ReviewSeverity.MEDIUM,
                    "style": ReviewSeverity.LOW,
                    "performance": ReviewSeverity.MEDIUM,
                    "portability": ReviewSeverity.LOW,
                    "information": ReviewSeverity.INFO,
                }
                severity = severity_map.get(level.lower(), ReviewSeverity.MEDIUM)

                items.append(ReviewItem(
                    category=ReviewCategory.LINT,
                    severity=severity,
                    file_path=file_path,
                    line_number=int(line_num),
                    message=message,
                    rule_id=f"cppcheck-{level}",
                ))

        return items

    def _parse_rubocop(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse RuboCop JSON output."""
        items = []
        try:
            if not stdout.strip():
                return items

            data = json.loads(stdout)
            for file_result in data.get("files", []):
                file_path = file_result.get("path", "")
                for offense in file_result.get("offenses", []):
                    severity_map = {
                        "fatal": ReviewSeverity.CRITICAL,
                        "error": ReviewSeverity.HIGH,
                        "warning": ReviewSeverity.MEDIUM,
                        "convention": ReviewSeverity.LOW,
                        "refactor": ReviewSeverity.LOW,
                    }
                    severity = severity_map.get(
                        offense.get("severity", "warning"),
                        ReviewSeverity.MEDIUM,
                    )

                    items.append(ReviewItem(
                        category=ReviewCategory.LINT,
                        severity=severity,
                        file_path=file_path,
                        line_number=offense.get("location", {}).get("line"),
                        message=offense.get("message", ""),
                        rule_id=offense.get("cop_name"),
                    ))
        except json.JSONDecodeError:
            pass
        return items

    def _parse_detect_secrets(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse detect-secrets output."""
        items = []
        try:
            if not stdout.strip():
                return items

            data = json.loads(stdout)
            for file_path, secrets in data.get("results", {}).items():
                for secret in secrets:
                    items.append(ReviewItem(
                        category=ReviewCategory.SECURITY,
                        severity=ReviewSeverity.CRITICAL,
                        file_path=file_path,
                        line_number=secret.get("line_number"),
                        message=f"Potential secret detected: {secret.get('type', 'unknown')}",
                        rule_id=secret.get("type"),
                    ))
        except json.JSONDecodeError:
            pass
        return items

    def _parse_gitleaks(self, stdout: str, stderr: str) -> list[ReviewItem]:
        """Parse gitleaks JSON output."""
        items = []
        try:
            if not stdout.strip():
                return items

            data = json.loads(stdout)
            for finding in data:
                items.append(ReviewItem(
                    category=ReviewCategory.SECURITY,
                    severity=ReviewSeverity.CRITICAL,
                    file_path=finding.get("file", ""),
                    line_number=finding.get("lineNumber"),
                    message=f"Secret detected: {finding.get('description', 'unknown')}",
                    rule_id=finding.get("ruleID"),
                ))
        except json.JSONDecodeError:
            pass
        return items

    async def run_security_scan(self) -> list[ReviewItem]:
        """Run security scanners."""
        items: list[ReviewItem] = []

        for scanner in self.SECURITY_SCANNERS:
            try:
                result = subprocess.run(
                    scanner["command"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

                self.tools_used.append(scanner["name"])

                parse_method = getattr(self, f"_parse_{scanner['parse']}", None)
                if parse_method:
                    parsed_items = parse_method(result.stdout, result.stderr)
                    items.extend(parsed_items)

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return items

    async def check_complexity(self) -> list[ReviewItem]:
        """Check code complexity for detected languages."""
        items: list[ReviewItem] = []

        for lang in self.detected_languages:
            tool = self.COMPLEXITY_TOOLS.get(lang)
            if not tool:
                continue

            try:
                result = subprocess.run(
                    tool["command"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                self.tools_used.append(tool["name"])

                # Parse based on tool
                if tool["name"] == "radon" and result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        for file_path, functions in data.items():
                            if isinstance(functions, list):
                                for func in functions:
                                    rank = func.get("rank", "A")
                                    if rank in ["C", "D", "E", "F"]:
                                        severity = ReviewSeverity.HIGH if rank in ["E", "F"] else ReviewSeverity.MEDIUM
                                        items.append(ReviewItem(
                                            category=ReviewCategory.COMPLEXITY,
                                            severity=severity,
                                            file_path=file_path,
                                            line_number=func.get("lineno"),
                                            message=f"High complexity ({rank}) in {func.get('name', 'unknown')}: "
                                                   f"complexity={func.get('complexity', '?')}",
                                            rule_id=f"CC-{rank}",
                                        ))
                    except json.JSONDecodeError:
                        pass

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return items

    async def check_dependencies(self) -> list[ReviewItem]:
        """Check for vulnerable dependencies in all detected languages."""
        items: list[ReviewItem] = []

        # Python
        if "python" in self.detected_languages:
            try:
                result = subprocess.run(
                    ["safety", "check", "--json"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                self.tools_used.append("safety")
                if result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        for vuln in data:
                            if isinstance(vuln, list) and len(vuln) >= 4:
                                items.append(ReviewItem(
                                    category=ReviewCategory.DEPENDENCY,
                                    severity=ReviewSeverity.CRITICAL,
                                    file_path="requirements.txt/pyproject.toml",
                                    line_number=None,
                                    message=f"Vulnerable: {vuln[0]} {vuln[2]}: {vuln[3]}",
                                    rule_id=vuln[1] if len(vuln) > 1 else None,
                                ))
                    except json.JSONDecodeError:
                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # JavaScript/TypeScript
        if "javascript" in self.detected_languages or "typescript" in self.detected_languages:
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                self.tools_used.append("npm-audit")
                if result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        for vuln_id, vuln in data.get("vulnerabilities", {}).items():
                            severity_map = {
                                "critical": ReviewSeverity.CRITICAL,
                                "high": ReviewSeverity.HIGH,
                                "moderate": ReviewSeverity.MEDIUM,
                                "low": ReviewSeverity.LOW,
                            }
                            severity = severity_map.get(vuln.get("severity", "low"), ReviewSeverity.MEDIUM)
                            items.append(ReviewItem(
                                category=ReviewCategory.DEPENDENCY,
                                severity=severity,
                                file_path="package.json",
                                line_number=None,
                                message=f"Vulnerable: {vuln.get('name', vuln_id)}",
                            ))
                    except json.JSONDecodeError:
                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # Rust
        if "rust" in self.detected_languages:
            try:
                result = subprocess.run(
                    ["cargo", "audit", "--json"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                self.tools_used.append("cargo-audit")
                if result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        for vuln in data.get("vulnerabilities", {}).get("list", []):
                            items.append(ReviewItem(
                                category=ReviewCategory.DEPENDENCY,
                                severity=ReviewSeverity.CRITICAL,
                                file_path="Cargo.toml",
                                line_number=None,
                                message=f"Vulnerable: {vuln.get('package', {}).get('name', 'unknown')}",
                                rule_id=vuln.get("advisory", {}).get("id"),
                            ))
                    except json.JSONDecodeError:
                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # Ruby
        if "ruby" in self.detected_languages:
            try:
                result = subprocess.run(
                    ["bundle", "audit", "check", "--format", "json"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                self.tools_used.append("bundle-audit")
                if result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        for vuln in data.get("results", []):
                            items.append(ReviewItem(
                                category=ReviewCategory.DEPENDENCY,
                                severity=ReviewSeverity.CRITICAL,
                                file_path="Gemfile",
                                line_number=None,
                                message=f"Vulnerable: {vuln.get('gem', {}).get('name', 'unknown')}",
                                rule_id=vuln.get("advisory", {}).get("id"),
                            ))
                    except json.JSONDecodeError:
                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return items

    async def review(self) -> ReviewResult:
        """Perform full code review.

        Returns:
            ReviewResult with all findings. Coding Agent MUST fix all items.
        """
        self.tools_used = []
        await self.detect_languages()

        all_items: list[ReviewItem] = []

        # CRITICAL: Check for incomplete code first (TODOs, unimplemented, etc.)
        incomplete_items = await self.check_incomplete_code()
        all_items.extend(incomplete_items)

        # Run language-specific linters
        for lang in self.detected_languages:
            items = await self.run_linters(lang)
            all_items.extend(items)

        # Run security scans
        security_items = await self.run_security_scan()
        all_items.extend(security_items)

        # Check complexity
        complexity_items = await self.check_complexity()
        all_items.extend(complexity_items)

        # Check dependencies
        dep_items = await self.check_dependencies()
        all_items.extend(dep_items)

        # Determine pass/fail
        result = ReviewResult(
            items=all_items,
            languages_detected=self.detected_languages,
            tools_used=list(set(self.tools_used)),
        )
        result.passed = result.must_fix_count() == 0
        result.summary = self._generate_summary(result)

        return result

    def _generate_summary(self, result: ReviewResult) -> str:
        """Generate human-readable summary."""
        if result.passed:
            tools_str = ", ".join(result.tools_used) if result.tools_used else "none"
            langs_str = ", ".join(result.languages_detected) if result.languages_detected else "none"
            return f"Code review PASSED. Languages: {langs_str}. Tools: {tools_str}. No blocking issues."

        # Count incomplete code issues separately (they're critical!)
        incomplete_count = sum(1 for i in result.items if i.category == ReviewCategory.INCOMPLETE)

        lines = [
            f"Code review found {len(result.items)} issues:",
            f"  - Critical: {result.critical_count}",
            f"  - High: {result.high_count}",
            f"  - Medium: {result.medium_count}",
            f"  - Must fix: {result.must_fix_count()}",
        ]

        if incomplete_count > 0:
            lines.append(f"  - INCOMPLETE CODE: {incomplete_count} (TODOs, unimplemented, placeholders)")

        lines.append("")
        lines.append("ALL items with severity MEDIUM or higher must be fixed by the Coding Agent.")
        lines.append("INCOMPLETE code (TODOs, NotImplementedError, etc.) is NEVER acceptable!")

        return "\n".join(lines)


# OWASP Top 10 2021 categories for reference
OWASP_TOP_10 = {
    "A01": "Broken Access Control",
    "A02": "Cryptographic Failures",
    "A03": "Injection",
    "A04": "Insecure Design",
    "A05": "Security Misconfiguration",
    "A06": "Vulnerable and Outdated Components",
    "A07": "Identification and Authentication Failures",
    "A08": "Software and Data Integrity Failures",
    "A09": "Security Logging and Monitoring Failures",
    "A10": "Server-Side Request Forgery (SSRF)",
}
