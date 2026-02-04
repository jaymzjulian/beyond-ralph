# Code Review Module Tasks

## Overview

The code-review module provides the CodeReviewAgent for multi-language linting and security scanning. **THIS MODULE HAS BLOCKING ITEMS FOR v1.0.**

**Dependencies**: agents/base
**Required By**: orchestrator, review-loop
**Location**: `src/beyond_ralph/agents/review_agent.py`
**Tests**: `tests/unit/test_review_agent.py`
**Status**: **PARTIAL - BLOCKING RELEASE**

---

## Task: Implement CodeReviewAgent Base Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Base CodeReviewAgent class extending TrustModelAgent.

**Acceptance Criteria**:
1. Extends `TrustModelAgent` with `can_review=True`
2. `review(files)` method for code review
3. Return `ReviewResult` with findings
4. Language detection (14+ languages)
5. Finding severity levels (CRITICAL, HIGH, MEDIUM, LOW, INFO)
6. Finding categories (LINT, SECURITY, STYLE, TYPE, PRACTICE)

**Tests**: tests/unit/test_review_agent.py::TestCodeReviewAgentBase
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/base-class/

---

## Task: Implement Language Detection

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Detect programming languages in files.

**Acceptance Criteria**:
1. `detect_language(file)` returns language
2. Support 14+ languages:
   - Python, JavaScript, TypeScript
   - Go, Rust, Java, C, C++
   - Ruby, PHP, Swift, Kotlin
   - Shell, SQL
3. Handle mixed-language projects
4. Return list of detected languages
5. File extension-based detection
6. Shebang-based detection for scripts

**Tests**: tests/unit/test_review_agent.py::TestLanguageDetection
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/language-detection/

---

## Task: Implement Python Linting

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Python linting with ruff and mypy.

**Acceptance Criteria**:
1. Run ruff for style/lint checks
2. Run mypy for type checking (strict mode)
3. Parse output into ReviewItems
4. Aggregate findings
5. Handle missing tools gracefully
6. Research agent finds alternatives if tools missing

**Tests**: tests/unit/test_review_agent.py::TestPythonLinting
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/python-linting/

---

## Task: Implement Multi-Language Linting **BLOCKING**

- [x] Planned - 2024-02-01
- [ ] Implemented - **IN PROGRESS**
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: **BLOCKING ITEM** - Linting for JS/TS, Go, Rust, Java, C/C++.

**Priority**: P0 - BLOCKS v1.0 RELEASE

**Acceptance Criteria**:
1. JavaScript/TypeScript: eslint, tsc
2. Go: golint/staticcheck, go vet
3. Rust: cargo clippy
4. Java: checkstyle, spotbugs
5. C/C++: clang-tidy, cppcheck
6. Unified finding format across all languages
7. Install missing tools automatically via research agent
8. Graceful fallback when tools unavailable
9. Each language has 2+ fallback linters

**Implementation Requirements**:
```python
class LanguageLinter:
    """Base class for language-specific linters."""

    @abstractmethod
    async def run(self, files: list[Path]) -> list[ReviewItem]: ...

    @abstractmethod
    def get_fallback_tools(self) -> list[str]: ...

# Required implementations:
class JavaScriptLinter(LanguageLinter): ...  # eslint -> jshint -> standard
class TypeScriptLinter(LanguageLinter): ...  # tsc -> eslint+ts -> deno lint
class GoLinter(LanguageLinter): ...          # staticcheck -> golint -> go vet
class RustLinter(LanguageLinter): ...        # cargo clippy -> rustfmt --check
class JavaLinter(LanguageLinter): ...        # checkstyle -> pmd -> spotbugs
class CLinter(LanguageLinter): ...           # clang-tidy -> cppcheck -> gcc -Wall
```

**Detailed Subtasks** (each with own acceptance criteria):

### Subtask 4.1: Implement LanguageLinter Base Class
- [ ] Create abstract `LanguageLinter` base class
- [ ] Define `run()` abstract method returning `list[ReviewItem]`
- [ ] Define `get_fallback_tools()` abstract method
- [ ] Implement `try_fallback()` method for automatic fallback on tool failure
- [ ] Implement `parse_output()` abstract method for tool output parsing

### Subtask 4.2: JavaScriptLinter Implementation
- [ ] Primary: eslint with `--format json` output parsing
- [ ] Secondary: jshint with JSON reporter
- [ ] Tertiary: standard with `--verbose` output
- [ ] Map eslint rule IDs to ReviewItem severity
- [ ] Unit tests with mock eslint output (8+ tests)

### Subtask 4.3: TypeScriptLinter Implementation
- [ ] Primary: tsc with `--pretty false` diagnostic parsing
- [ ] Secondary: eslint with `@typescript-eslint/parser`
- [ ] Tertiary: deno lint with JSON output
- [ ] Map TS error codes to severity levels
- [ ] Unit tests with mock tsc output (8+ tests)

### Subtask 4.4: GoLinter Implementation
- [ ] Primary: staticcheck with JSON output
- [ ] Secondary: golint (deprecated but available)
- [ ] Tertiary: go vet with JSON output
- [ ] Map staticcheck codes (SA*, S*, ST*) to severity
- [ ] Unit tests with mock staticcheck output (8+ tests)

### Subtask 4.5: RustLinter Implementation
- [ ] Primary: cargo clippy with `--message-format=json`
- [ ] Secondary: rustfmt --check (style only)
- [ ] Map clippy lint levels (allow, warn, deny, forbid) to severity
- [ ] Unit tests with mock clippy output (6+ tests)

### Subtask 4.6: JavaLinter Implementation
- [ ] Primary: checkstyle with XML output parsing
- [ ] Secondary: pmd with CSV/XML output
- [ ] Tertiary: spotbugs with XML output
- [ ] Map checkstyle severity (error, warning, info) to ReviewItem
- [ ] Unit tests with mock checkstyle output (8+ tests)

### Subtask 4.7: CLinter Implementation
- [ ] Primary: clang-tidy with YAML/JSON output
- [ ] Secondary: cppcheck with XML output
- [ ] Tertiary: gcc -Wall -Werror (parse stderr)
- [ ] Map clang-tidy check names to categories
- [ ] Unit tests with mock clang-tidy output (8+ tests)

### Subtask 4.8: LinterRegistry Implementation
- [ ] `LinterRegistry.get_linter(language)` returns appropriate linter
- [ ] Auto-detect language from file extensions
- [ ] Support language override via config
- [ ] Fallback chain execution when primary tool fails
- [ ] Unit tests for registry behavior (5+ tests)

### Subtask 4.9: Tool Installation Integration
- [ ] Detect missing tools via `which` or `shutil.which()`
- [ ] Call research agent to find/install missing tools
- [ ] Cache tool availability for performance
- [ ] Log tool installation attempts
- [ ] Unit tests for installation flow (5+ tests)

**Fallback Chain per Language**:
| Language | Primary | Secondary | Tertiary |
|----------|---------|-----------|----------|
| JavaScript | eslint | jshint | standard |
| TypeScript | tsc | eslint+ts | deno lint |
| Go | staticcheck | golint | go vet |
| Rust | cargo clippy | rustfmt --check | - |
| Java | checkstyle | pmd | spotbugs |
| C/C++ | clang-tidy | cppcheck | gcc -Wall |

**Tests**: tests/unit/test_review_agent.py::TestMultiLanguageLinting
**Test Count Target**: 60+ unit tests for all linter implementations
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/multi-language-linting/

---

## Task: Implement Security Scanning **BLOCKING**

- [x] Planned - 2024-02-01
- [ ] Implemented - **IN PROGRESS**
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: **BLOCKING ITEM** - Security scanning with Semgrep and OWASP.

**Priority**: P0 - BLOCKS v1.0 RELEASE

**Acceptance Criteria**:
1. Semgrep with OWASP rulesets (p/owasp-top-ten)
2. Bandit for Python security
3. detect-secrets for hardcoded secrets
4. Safety for dependency vulnerabilities
5. Parse findings into ReviewItems
6. Mark security issues as CRITICAL severity

**Detailed Subtasks**:

### Subtask 5.1: Implement Semgrep OWASP Integration
- [ ] Download and cache OWASP ruleset (`p/owasp-top-ten`)
- [ ] Run semgrep with `--json` output
- [ ] Parse SARIF/JSON output into ReviewItems
- [ ] Map OWASP rule IDs to categories:
  - A01 (Broken Access Control) -> CRITICAL
  - A02 (Cryptographic Failures) -> CRITICAL
  - A03 (Injection) -> CRITICAL
  - A04 (Insecure Design) -> HIGH
  - A05 (Security Misconfiguration) -> HIGH
  - A06 (Vulnerable Components) -> HIGH
  - A07 (Auth Failures) -> CRITICAL
  - A08 (Data Integrity) -> HIGH
  - A09 (Logging Failures) -> MEDIUM
  - A10 (SSRF) -> HIGH
- [ ] Support custom rulesets via config
- [ ] Unit tests with mock Semgrep output (10+ tests)

### Subtask 5.2: Implement Bandit Integration (Python)
- [ ] Run bandit with `--format json` output
- [ ] Parse JSON findings into ReviewItems
- [ ] Map Bandit severity/confidence to ReviewItem severity:
  - HIGH/HIGH -> CRITICAL
  - HIGH/MEDIUM -> HIGH
  - MEDIUM/HIGH -> HIGH
  - MEDIUM/MEDIUM -> MEDIUM
  - LOW/* -> LOW
- [ ] Include Bandit test IDs (B101, B102, etc.)
- [ ] Unit tests with mock Bandit output (8+ tests)

### Subtask 5.3: Implement detect-secrets Integration
- [ ] Run detect-secrets with `--list-all-plugins`
- [ ] Scan for hardcoded secrets in all file types
- [ ] Parse JSON output into ReviewItems
- [ ] Secret types detected:
  - API keys (AWS, GCP, Azure, etc.)
  - Private keys (RSA, SSH)
  - Database credentials
  - Tokens (JWT, OAuth, etc.)
  - Passwords in code
- [ ] All secrets marked as CRITICAL severity
- [ ] Unit tests with mock detect-secrets output (8+ tests)

### Subtask 5.4: Implement Safety Integration (Dependencies)
- [ ] Run safety check on requirements.txt/pyproject.toml
- [ ] Parse JSON output into ReviewItems
- [ ] Include CVE IDs in findings
- [ ] Map vulnerability severity to ReviewItem:
  - CVSS >= 9.0 -> CRITICAL
  - CVSS >= 7.0 -> HIGH
  - CVSS >= 4.0 -> MEDIUM
  - CVSS < 4.0 -> LOW
- [ ] Unit tests with mock Safety output (6+ tests)

### Subtask 5.5: Implement SecurityScanner Orchestrator
- [ ] `SecurityScanner` class to orchestrate all security tools
- [ ] `scan(files, config)` runs all applicable scanners
- [ ] Language-specific scanner selection:
  - Python: bandit, safety, semgrep
  - JavaScript/TypeScript: semgrep, npm audit
  - Go: semgrep, govulncheck
  - All: detect-secrets
- [ ] Aggregate findings from all scanners
- [ ] Unit tests for orchestration (6+ tests)

**Tests**: tests/unit/test_review_agent.py::TestSecurityScanning
**Test Count Target**: 40+ unit tests for security scanning
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/security-scanning/

---

## Task: Implement Finding Aggregation **BLOCKING**

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: **BLOCKING ITEM** - Aggregate findings from all tools.

**Priority**: P0 - BLOCKS v1.0 RELEASE

**Acceptance Criteria**:
1. `ReviewResult` aggregates all findings
2. Deduplicate overlapping findings
3. Sort by severity (CRITICAL > HIGH > MEDIUM > LOW > INFO)
4. Group by file/category
5. Generate human-readable report
6. Export to JSON for processing

**Detailed Subtasks**:

### Subtask 6.1: Implement ReviewResult Dataclass
- [ ] `ReviewResult` dataclass with:
  - `findings: list[ReviewItem]`
  - `files_reviewed: int`
  - `total_findings: int`
  - `findings_by_severity: dict[ReviewSeverity, int]`
  - `findings_by_category: dict[ReviewCategory, int]`
  - `passed: bool` (no CRITICAL/HIGH findings)
  - `timestamp: datetime`
  - `duration_ms: int`
- [ ] Unit tests for dataclass (5+ tests)

### Subtask 6.2: Implement Deduplication Logic
- [ ] `FindingDeduplicator` class
- [ ] Detect duplicate findings from different tools:
  - Same file + same line + similar message -> dedupe
  - Same file + same rule_id -> dedupe
  - Keep finding with most detail
- [ ] Configurable deduplication threshold (similarity score)
- [ ] Track original source tools for merged findings
- [ ] Unit tests for deduplication (10+ tests)

### Subtask 6.3: Implement Severity Ranking
- [ ] `SEVERITY_ORDER = [CRITICAL, HIGH, MEDIUM, LOW, INFO]`
- [ ] `sort_by_severity(findings)` sorts highest first
- [ ] Secondary sort by file path, then line number
- [ ] Unit tests for sorting (5+ tests)

### Subtask 6.4: Implement File-Based Grouping
- [ ] `group_by_file(findings)` returns `dict[Path, list[ReviewItem]]`
- [ ] `group_by_category(findings)` returns `dict[ReviewCategory, list[ReviewItem]]`
- [ ] Support nested grouping (file -> category -> findings)
- [ ] Unit tests for grouping (5+ tests)

### Subtask 6.5: Implement Markdown Report Generation
- [ ] `generate_markdown_report(result)` creates human-readable report
- [ ] Report format:
  ```markdown
  # Code Review Report

  **Summary**: X files reviewed, Y findings (Z critical, W high)
  **Status**: PASS/FAIL

  ## Critical Findings
  ### file.py
  - Line 45: SQL Injection (A03-Injection) - Use parameterized queries

  ## High Findings
  ...
  ```
- [ ] Include code snippets where available
- [ ] Include fix suggestions
- [ ] Unit tests for report generation (5+ tests)

### Subtask 6.6: Implement JSON Export
- [ ] `to_json(result)` serializes to JSON
- [ ] JSON schema for machine processing:
  ```json
  {
    "summary": {...},
    "findings": [...],
    "metadata": {...}
  }
  ```
- [ ] `from_json(data)` deserializes from JSON
- [ ] Schema validation
- [ ] Unit tests for JSON export/import (5+ tests)

### Subtask 6.7: Implement FindingAggregator Class
- [ ] `FindingAggregator` orchestrates full aggregation pipeline:
  1. Collect findings from all tools
  2. Deduplicate
  3. Sort by severity
  4. Group as needed
  5. Generate statistics
  6. Create ReviewResult
- [ ] `aggregate(findings_lists: list[list[ReviewItem]])` main method
- [ ] Unit tests for full pipeline (8+ tests)

**Tests**: tests/unit/test_review_agent.py::TestFindingAggregation
**Test Count Target**: 45+ unit tests for finding aggregation
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/finding-aggregation/

---

## Task: Implement ReviewItem Dataclass

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Dataclass for individual review findings.

**Acceptance Criteria**:
1. `ReviewItem` dataclass with:
   - `file`: File path
   - `line`: Line number
   - `column`: Column number (optional)
   - `severity`: CRITICAL/HIGH/MEDIUM/LOW/INFO
   - `category`: LINT/SECURITY/STYLE/TYPE/PRACTICE
   - `message`: Description
   - `rule_id`: Rule identifier
   - `suggestion`: Fix suggestion (optional)
2. ALL items are NON-NEGOTIABLE
3. Coder agent MUST fix ALL items

**Tests**: tests/unit/test_review_agent.py::TestReviewItem
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/review-item/

---

## Task: Implement Best Practices Checks

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Best practices and code quality checks.

**Acceptance Criteria**:
1. Cyclomatic complexity (radon for Python)
2. Dead code detection (vulture for Python)
3. DRY violation detection
4. Error handling patterns
5. Input validation checks
6. Documentation coverage checks

**Tests**: tests/unit/test_review_agent.py::TestBestPractices
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/code-review/evidence/best-practices/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| CodeReviewAgent Base Class | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| Language Detection | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| Python Linting | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| **Multi-Language Linting** | [x] | **[ ]** | **[ ]** | [ ] | [ ] | [ ] |
| **Security Scanning** | [x] | **[ ]** | **[ ]** | [ ] | [ ] | [ ] |
| **Finding Aggregation** | [x] | **[ ]** | **[ ]** | [ ] | [ ] | [ ] |
| ReviewItem Dataclass | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| Best Practices Checks | [x] | [x] | [x] | [ ] | [ ] | [ ] |

**Overall Progress**: 5/8 implemented (3 blocking), 5/8 mock tested, 0/8 integration tested, 0/8 live tested, 0/8 spec compliant

---

## BLOCKING ITEMS FOR v1.0 RELEASE

1. **Multi-Language Linting** - Must orchestrate linters for JS/TS, Go, Rust, Java, C/C++
   - 9 subtasks, ~60 unit tests needed
   - Dependencies: None (foundation complete)

2. **Security Scanning** - Must integrate full Semgrep OWASP ruleset
   - 5 subtasks, ~40 unit tests needed
   - Dependencies: None

3. **Finding Aggregation** - Must deduplicate and aggregate findings
   - 7 subtasks, ~45 unit tests needed
   - Dependencies: Multi-Language Linting, Security Scanning

**Total Estimated Work**:
- 21 subtasks
- 145+ new unit tests
- 2-3 implementation days

**Priority**: P0 - These items BLOCK release
**Next Action**: Complete implementation of remaining tasks before any live testing

---

## Implementation Order for Blocking Items

```
Phase 1: Multi-Language Linting (Day 1-2)
├── Subtask 4.1: LanguageLinter Base Class
├── Subtask 4.2: JavaScriptLinter
├── Subtask 4.3: TypeScriptLinter
├── Subtask 4.4: GoLinter
├── Subtask 4.5: RustLinter
├── Subtask 4.6: JavaLinter
├── Subtask 4.7: CLinter
├── Subtask 4.8: LinterRegistry
└── Subtask 4.9: Tool Installation Integration

Phase 2: Security Scanning (Day 2)
├── Subtask 5.1: Semgrep OWASP Integration
├── Subtask 5.2: Bandit Integration
├── Subtask 5.3: detect-secrets Integration
├── Subtask 5.4: Safety Integration
└── Subtask 5.5: SecurityScanner Orchestrator

Phase 3: Finding Aggregation (Day 3)
├── Subtask 6.1: ReviewResult Dataclass
├── Subtask 6.2: Deduplication Logic
├── Subtask 6.3: Severity Ranking
├── Subtask 6.4: File-Based Grouping
├── Subtask 6.5: Markdown Report Generation
├── Subtask 6.6: JSON Export
└── Subtask 6.7: FindingAggregator Class
```
