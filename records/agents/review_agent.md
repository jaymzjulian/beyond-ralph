# Code Review Agent Tasks

## Overview

The Code Review Agent is the THIRD agent in the trust model, completely separate from Coding and Testing agents. Its findings are NON-NEGOTIABLE.

**All review items MUST be actioned by the Coding Agent.**

---

### Task: Implement Review Agent Core

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Core review agent with language detection and tool orchestration.

**Key Requirements**:
- Detect project languages
- Orchestrate appropriate linters
- Aggregate findings
- Generate actionable report

---

### Task: Implement Language-Specific Linting

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Run appropriate linters for each detected language.

**Tools by Language**:
- Python: ruff, mypy, pylint
- JavaScript/TypeScript: eslint, tsc
- Go: golint, go vet, staticcheck
- Rust: cargo clippy
- Java: checkstyle, spotbugs
- Ruby: rubocop
- PHP: phpstan, psalm

**Key Requirements**:
- Auto-detect language
- Install linter if missing (via Research Agent)
- Parse linter output
- Create ReviewItems

---

### Task: Implement Security Scanning (SAST)

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Multi-language security scanning.

**Tools**:
- Semgrep (multi-language, OWASP rules)
- Bandit (Python)
- detect-secrets (secrets in code)
- Safety (Python dependencies)
- npm audit (Node.js)
- cargo audit (Rust)

**Key Requirements**:
- OWASP Top 10 coverage
- Secrets detection
- Dependency vulnerability checks
- Clear remediation guidance

---

### Task: Implement Best Practices Checks

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Check for code quality and best practices.

**Checks**:
- Cyclomatic complexity (radon)
- Dead code (vulture)
- Code duplication
- Error handling patterns
- Input validation
- Output encoding

---

### Task: Implement Documentation Checks

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Ensure code is properly documented.

**Checks**:
- Public APIs have docstrings
- Complex logic has comments
- README is present and current
- API documentation complete

---

### Task: Implement Review-Fix Loop

- [ ] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested

**Description**: Integration with Coding Agent for fix loop.

**Key Requirements**:
- Pass findings to Coding Agent
- Coding Agent MUST fix ALL items
- Re-review after fixes
- Loop until all items resolved
- No exceptions or dismissals allowed
