# Module 10: Code Review - Specification

**Module**: code-review
**Location**: `src/beyond_ralph/agents/review_agent.py`
**Dependencies**: research (for linter discovery)

## Purpose

Mandatory code review with linting, security scanning, and best practices enforcement.

## Requirements

### R1: Language Detection
- Auto-detect project languages
- Support: Python, JavaScript, TypeScript, Go, Rust, Java, etc.

### R2: Linting (ALL BLOCKING)
- Python: ruff, mypy (strict)
- JavaScript/TypeScript: eslint, tsc
- Go: golint, go vet, staticcheck
- Rust: cargo clippy
- Install linters via Research Agent if missing

### R3: Security Scanning (ALL BLOCKING)
- Semgrep with OWASP rulesets
- Bandit for Python
- detect-secrets for hardcoded secrets
- Safety for dependency vulnerabilities
- npm audit, cargo audit as applicable

### R4: Best Practices (HIGH/MEDIUM BLOCKING)
- Cyclomatic complexity (radon)
- Dead code detection (vulture)
- DRY violations
- Error handling patterns
- Input validation

### R5: Review-Fix Loop
- ALL findings must be fixed (zero tolerance)
- Pass findings to Coding Agent
- Coding Agent fixes ALL items
- Re-review until 0 must-fix items

## Interface

```python
class CodeReviewAgent:
    async def review(self, project_root: Path) -> ReviewResult
    async def detect_languages(self) -> list[str]
    async def run_linters(self, language: str) -> list[ReviewItem]
    async def run_security_scan(self) -> list[ReviewItem]
    async def check_complexity(self) -> list[ReviewItem]
    async def check_dead_code(self) -> list[ReviewItem]
```

## ReviewItem

```python
@dataclass
class ReviewItem:
    category: ReviewCategory  # SECURITY, LINT, TYPE, COMPLEXITY, etc.
    severity: ReviewSeverity  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    file_path: str
    line_number: int | None
    message: str
    rule_id: str | None
    suggested_fix: str | None
```

## Testing Requirements

- Test each linter integration
- Test security scanner integration
- Test review-fix loop
- Mock linter outputs for unit tests
