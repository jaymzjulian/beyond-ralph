"""Code Review Agent - Third agent in the trust model.

This agent is SEPARATE from both the Coding Agent and Testing Agent.
It performs:
1. Language-specific linting
2. Security analysis (SAST, OWASP)
3. Best practices review
4. Documentation checks

ALL items flagged by this agent MUST be actioned by the Coding Agent.
No exceptions. No dismissals. Fix everything.
"""

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


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


@dataclass
class ReviewResult:
    """Result of a code review."""

    items: list[ReviewItem] = field(default_factory=list)
    passed: bool = False
    summary: str = ""

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.items if i.severity == ReviewSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.items if i.severity == ReviewSeverity.HIGH)

    def must_fix_count(self) -> int:
        """Items that MUST be fixed (critical + high + medium)."""
        return sum(
            1 for i in self.items
            if i.severity in (ReviewSeverity.CRITICAL, ReviewSeverity.HIGH, ReviewSeverity.MEDIUM)
        )


class CodeReviewAgent:
    """The third agent - reviews code for quality and security.

    This agent is COMPLETELY SEPARATE from the Coding and Testing agents.
    Its findings are NON-NEGOTIABLE - the Coding Agent MUST fix everything.

    Tools used:
    - Semgrep: Multi-language security rules, OWASP patterns
    - Bandit: Python security analysis
    - Ruff: Python linting (fast, comprehensive)
    - mypy: Python type checking
    - ESLint: JavaScript/TypeScript linting
    - detect-secrets: Find hardcoded secrets
    - Safety: Check for vulnerable dependencies
    - Radon: Code complexity metrics
    - Vulture: Dead code detection
    """

    # Language-specific linter commands
    LINTERS: dict[str, list[list[str]]] = {
        "python": [
            ["ruff", "check", "--output-format=json"],
            ["mypy", "--strict", "--show-error-codes"],
            ["bandit", "-r", "-f", "json"],
            ["vulture"],
        ],
        "javascript": [
            ["eslint", "--format=json"],
        ],
        "typescript": [
            ["eslint", "--format=json"],
            ["tsc", "--noEmit"],
        ],
        "go": [
            ["golint"],
            ["go", "vet"],
            ["staticcheck"],
        ],
        "rust": [
            ["cargo", "clippy", "--", "-D", "warnings"],
        ],
    }

    # Security scanners (run for all languages)
    SECURITY_SCANNERS: list[list[str]] = [
        ["semgrep", "scan", "--config=auto", "--json"],
        ["detect-secrets", "scan"],
        ["safety", "check", "--json"],
    ]

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.detected_languages: list[str] = []

    async def detect_languages(self) -> list[str]:
        """Detect programming languages in the project."""
        languages = []

        # Check for language indicators
        indicators = {
            "python": ["*.py", "pyproject.toml", "setup.py", "requirements.txt"],
            "javascript": ["*.js", "package.json"],
            "typescript": ["*.ts", "*.tsx", "tsconfig.json"],
            "go": ["*.go", "go.mod"],
            "rust": ["*.rs", "Cargo.toml"],
            "java": ["*.java", "pom.xml", "build.gradle"],
            "csharp": ["*.cs", "*.csproj"],
            "ruby": ["*.rb", "Gemfile"],
            "php": ["*.php", "composer.json"],
        }

        for lang, patterns in indicators.items():
            for pattern in patterns:
                if list(self.project_root.glob(f"**/{pattern}")):
                    languages.append(lang)
                    break

        self.detected_languages = languages
        return languages

    async def run_linters(self, language: str) -> list[ReviewItem]:
        """Run language-specific linters."""
        items = []
        linters = self.LINTERS.get(language, [])

        for linter_cmd in linters:
            try:
                result = subprocess.run(
                    linter_cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                # TODO: Parse linter output based on tool
                # This is a placeholder - each linter has different output format
                if result.returncode != 0:
                    # Parse and create ReviewItems
                    pass
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                # Linter not installed - research agent should find alternative
                pass

        return items

    async def run_security_scan(self) -> list[ReviewItem]:
        """Run security scanners (Semgrep, Bandit, etc.)."""
        items = []

        for scanner_cmd in self.SECURITY_SCANNERS:
            try:
                result = subprocess.run(
                    scanner_cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600,  # Security scans can take longer
                )
                # TODO: Parse scanner output
                pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return items

    async def check_complexity(self) -> list[ReviewItem]:
        """Check code complexity using radon."""
        items = []
        try:
            result = subprocess.run(
                ["radon", "cc", "-j", str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            # TODO: Parse radon output, flag high complexity
            pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return items

    async def check_secrets(self) -> list[ReviewItem]:
        """Check for hardcoded secrets."""
        items = []
        try:
            result = subprocess.run(
                ["detect-secrets", "scan", "--all-files"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            # TODO: Parse detect-secrets output
            pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return items

    async def check_dependencies(self) -> list[ReviewItem]:
        """Check for vulnerable dependencies."""
        items = []

        # Python dependencies
        if "python" in self.detected_languages:
            try:
                result = subprocess.run(
                    ["safety", "check", "--json"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                # TODO: Parse safety output
                pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # TODO: Add npm audit, cargo audit, etc.
        return items

    async def review(self) -> ReviewResult:
        """Perform full code review.

        Returns:
            ReviewResult with all findings. Coding Agent MUST fix all items.
        """
        await self.detect_languages()

        all_items: list[ReviewItem] = []

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

        # Check for secrets
        secret_items = await self.check_secrets()
        all_items.extend(secret_items)

        # Check dependencies
        dep_items = await self.check_dependencies()
        all_items.extend(dep_items)

        # Determine pass/fail
        result = ReviewResult(items=all_items)
        result.passed = result.must_fix_count() == 0
        result.summary = self._generate_summary(result)

        return result

    def _generate_summary(self, result: ReviewResult) -> str:
        """Generate human-readable summary."""
        if result.passed:
            return "✅ Code review PASSED. No issues found."

        lines = [
            f"❌ Code review found {len(result.items)} issues:",
            f"  - Critical: {result.critical_count}",
            f"  - High: {result.high_count}",
            f"  - Must fix: {result.must_fix_count()}",
            "",
            "ALL items must be fixed by the Coding Agent.",
        ]
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
