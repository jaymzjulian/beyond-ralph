# Module 7: Code Review - Specification

> Code Quality: Multi-language linting, security scanning, and mandatory fix loops.

---

## Overview

The Code Review module enforces code quality through automated linting, security scanning, and best practices checks. Every implementation MUST pass code review before being considered complete. The Coding Agent MUST action ALL review items - no dismissals allowed.

**Key Principle**: ALL findings are blocking. Coding Agent MUST fix EVERY item.

---

## Components

### 7.1 Code Review Agent (`review_agent.py`)

**Location**: `src/beyond_ralph/agents/review_agent.py`

### 7.2 Review Loop Manager (`review_loop.py`)

**Location**: `src/beyond_ralph/core/review_loop.py`

---

## Review Categories

### 1. Linting (Language-Specific)

| Language | Tools | Flags |
|----------|-------|-------|
| Python | ruff, mypy | --strict (mypy) |
| JavaScript | eslint | --max-warnings 0 |
| TypeScript | eslint, tsc | --noEmit --strict (tsc) |
| Go | golint, go vet, staticcheck | - |
| Rust | cargo clippy | -D warnings |
| C/C++ | clang-tidy, cppcheck | - |
| Java | checkstyle, spotbugs | - |
| Ruby | rubocop | - |

### 2. Security Scanning (OWASP/SAST)

| Tool | Purpose |
|------|---------|
| semgrep | General SAST with security rulesets |
| bandit | Python security |
| detect-secrets | Hardcoded credentials |
| safety | Python dependency vulnerabilities |
| npm audit | Node.js vulnerabilities |
| cargo audit | Rust vulnerabilities |
| bundle audit | Ruby vulnerabilities |

### 3. Best Practices

| Check | Tool/Method |
|-------|-------------|
| Cyclomatic complexity | radon (Python) |
| Dead code | vulture (Python) |
| DRY violations | Pattern analysis |
| Error handling | AST analysis |
| Input validation | Security scanning |
| Output encoding | Security scanning |

---

## Interfaces

### CodeReviewAgent

```python
class CodeReviewAgent:
    """Multi-language code review agent."""

    def __init__(self, project_path: str):
        """Initialize code review agent.

        Args:
            project_path: Root of project to review.
        """

    def review(
        self,
        files: list[str],
        languages: Optional[list[str]] = None
    ) -> ReviewResult:
        """Review specified files.

        Args:
            files: List of file paths to review.
            languages: Languages to check (auto-detect if None).

        Returns:
            ReviewResult with all findings.

        Flow:
            1. Detect languages from file extensions
            2. Run appropriate linters
            3. Run security scanners
            4. Run best practices checks
            5. Collect and categorize findings
        """

    def get_linters_for_language(self, lang: str) -> list[LinterConfig]:
        """Get linters configured for a language.

        Args:
            lang: Language name (python, javascript, etc.)

        Returns:
            List of LinterConfig for that language.
        """

    def run_linter(
        self,
        linter: LinterConfig,
        files: list[str]
    ) -> list[ReviewItem]:
        """Run a specific linter.

        Args:
            linter: Linter configuration.
            files: Files to lint.

        Returns:
            List of findings.
        """

    def run_security_scan(
        self,
        files: list[str]
    ) -> list[ReviewItem]:
        """Run security scanning tools.

        Args:
            files: Files to scan.

        Returns:
            Security findings (ALL are blocking).
        """

    def check_dependencies(
        self,
        project_path: str
    ) -> list[ReviewItem]:
        """Check for vulnerable dependencies.

        Args:
            project_path: Project root.

        Returns:
            Dependency vulnerability findings.
        """

    def check_best_practices(
        self,
        files: list[str]
    ) -> list[ReviewItem]:
        """Check best practices.

        Args:
            files: Files to check.

        Returns:
            Best practice findings.
        """

@dataclass
class LinterConfig:
    """Configuration for a linter."""
    name: str
    command: str
    args: list[str]
    languages: list[str]
    severity_mapping: dict[str, str]  # Tool output -> severity

@dataclass
class ReviewItem:
    """A single review finding."""
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal["security", "lint", "practice", "docs"]
    file: str
    line: int
    column: Optional[int] = None
    message: str = ""
    tool: str = ""  # Which tool found this
    rule: Optional[str] = None  # Rule ID (e.g., "E501", "SEC001")
    fix_suggestion: Optional[str] = None

    def is_blocking(self) -> bool:
        """Check if this finding blocks approval."""
        # ALL findings are blocking per interview decision
        return True

@dataclass
class ReviewResult:
    """Complete review result."""
    items: list[ReviewItem]
    passed: bool  # True only if 0 findings
    summary: str
    tools_run: list[str]
    duration_ms: int

    @property
    def critical_count(self) -> int:
        return len([i for i in self.items if i.severity == "critical"])

    @property
    def high_count(self) -> int:
        return len([i for i in self.items if i.severity == "high"])

    def to_markdown(self) -> str:
        """Generate markdown report."""
```

### ReviewLoopManager

```python
class ReviewLoopManager:
    """Manages the review-fix-revalidate loop."""

    def __init__(self, code_review_agent: CodeReviewAgent):
        """Initialize review loop manager."""

    def generate_fix_prompt(
        self,
        items: list[ReviewItem]
    ) -> str:
        """Generate prompt for Coding Agent to fix items.

        Args:
            items: Review items to fix.

        Returns:
            Prompt instructing agent to fix ALL items.

        Note:
            Agent MUST fix ALL items. No dismissals allowed.
        """

    def verify_fix(
        self,
        item: ReviewItem,
        new_content: str
    ) -> bool:
        """Verify a specific fix was applied.

        Args:
            item: Original finding.
            new_content: Updated file content.

        Returns:
            True if fix verified.
        """

    def is_cycle_complete(self, result: ReviewResult) -> bool:
        """Check if review loop can be approved.

        Args:
            result: Latest review result.

        Returns:
            True only if 0 findings.
        """

    def approve_cycle(self) -> None:
        """Approve completed review cycle."""

    def get_fix_attempts(self, item: ReviewItem) -> int:
        """Get number of fix attempts for an item."""

    def record_fix_attempt(
        self,
        item: ReviewItem,
        fixed: bool,
        agent_id: str
    ) -> None:
        """Record a fix attempt."""
```

---

## Review Loop Flow

```
┌─────────────────┐
│  Coding Agent   │
│  (Implements)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Code Review    │
│  Agent runs     │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Items?  │
    └────┬────┘
         │
    Yes  │  No
    ▼    └────────────────────────────────►┌──────────────┐
┌─────────────────┐                        │   APPROVED   │
│ Generate Fix    │                        │              │
│ Prompt          │                        └──────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Coding Agent    │
│ FIXES ALL items │◄───────────────┐
└────────┬────────┘                │
         │                         │
         ▼                         │
┌─────────────────┐                │
│ Re-run Review   │                │
└────────┬────────┘                │
         │                         │
    ┌────┴────┐                    │
    │ Items?  │────────────────────┘
    └────┬────┘  Yes
         │
         │ No
         ▼
┌─────────────────┐
│    APPROVED     │
└─────────────────┘
```

---

## Severity Levels

| Severity | Examples | Action |
|----------|----------|--------|
| **Critical** | SQL injection, command injection, hardcoded secrets | IMMEDIATE fix required |
| **High** | XSS, insecure deserialization, missing auth checks | Fix before merge |
| **Medium** | Missing input validation, weak crypto, info disclosure | Fix before merge |
| **Low** | Style issues, missing docs, complexity warnings | Fix before merge |

**Note**: Per interview decision, ALL findings are blocking. Zero tolerance.

---

## Usage Example

```python
# In orchestrator._phase_implementation()
review_agent = CodeReviewAgent(project_path)
review_loop = ReviewLoopManager(review_agent)

# Initial review
result = review_agent.review(changed_files)

while not review_loop.is_cycle_complete(result):
    # Generate fix prompt
    fix_prompt = review_loop.generate_fix_prompt(result.items)

    # Send to coding agent
    fix_result = await coding_session.send(fix_prompt)

    # Re-review
    result = review_agent.review(changed_files)

# All items fixed
review_loop.approve_cycle()
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 8 (System) | Installing linters, security tools |
| Module 4 (Records) | Storing findings |

---

## Tool Installation

Tools are installed automatically when needed:

```python
# In review agent
if not self._is_tool_available("semgrep"):
    SystemCapabilities.install_system_package("semgrep")

if not self._is_tool_available("bandit"):
    subprocess.run(["uv", "add", "bandit"])
```

---

## Error Handling

```python
class ReviewError(BeyondRalphError):
    """Review-specific errors."""

class LinterNotAvailableError(ReviewError):
    """Required linter not installed."""

class SecurityScanError(ReviewError):
    """Security scan failed."""

class ReviewNotPassedError(ReviewError):
    """Review has unresolved findings."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Individual checks, parsing |
| Integration tests | Full review runs |
| Mock tests | Mocked tool outputs |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested (94% coverage)
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
