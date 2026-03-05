# Beyond Ralph - Testing Guide

## Overview

Beyond Ralph includes comprehensive testing capabilities for various application types. It uses a three-agent trust model where no agent validates its own work.

## Testing Philosophy

### Test-Driven Development (TDD)

Beyond Ralph follows TDD:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Repeat

### Three-Agent Trust Model

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CODING AGENT   │     │ TESTING AGENT   │     │ REVIEW AGENT    │
│  (Implements)   │     │ (Validates)     │     │ (Reviews)       │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ writes code           │                       │
         │──────────────────────>│ runs tests            │
         │                       │──────────────────────>│ reviews
         │<──────────────────────────────────────────────│
         │        fixes any issues                       │
         └───────── REPEAT UNTIL APPROVED ─────────────┘
```

## Application Types

### API/Backend Testing

Beyond Ralph can test REST APIs:

```python
# Automatic API testing
- Mock server development first
- Real endpoint testing second
- Non-destructive operations only
```

**Features**:
- OpenAPI/Swagger spec ingestion
- Mock server for development
- Request/response validation
- Authentication handling

**Example Spec**:
```markdown
## API Requirements
1. GET /users returns list of users
2. POST /users creates new user
3. All endpoints require Bearer token
```

### Web UI Testing

Browser automation with Playwright:

```python
# Web testing capabilities
- Cross-browser testing (Chrome, Firefox, WebKit)
- Headless mode for CI/CD
- Screenshot capture
- Visual regression
```

**Example Spec**:
```markdown
## Web UI Requirements
1. Login page at /login
2. Form validates email format
3. Success redirects to /dashboard
```

### CLI Testing

Command-line application testing:

```python
# CLI testing with pexpect
- Interactive prompts
- Exit code verification
- Output pattern matching
- Timeout handling
```

**Example Spec**:
```markdown
## CLI Requirements
1. `myapp --help` shows usage
2. `myapp process file.txt` outputs results
3. Exit code 0 on success, 1 on error
```

### Desktop GUI Testing

GUI application testing:

```python
# Desktop GUI testing
- Screenshot analysis
- Element detection
- Mouse/keyboard simulation
- Cross-platform support
```

**Example Spec**:
```markdown
## Desktop GUI Requirements
1. Main window shows toolbar
2. File menu contains Open, Save, Exit
3. Status bar shows current state
```

## Mock Server

### Creating a Mock Server

Beyond Ralph creates mock servers for API development:

```python
# From OpenAPI spec
mock_server = MockAPIServer.from_openapi("api-spec.yaml")
mock_server.start()

# Manual routes
mock_server = MockAPIServer(port=8080)
mock_server.add_route("GET", "/users", [{"id": 1, "name": "Test"}])
```

### Benefits of Mock-First Development

1. **Isolation**: Test without external dependencies
2. **Speed**: No network latency
3. **Control**: Simulate edge cases and errors
4. **Reliability**: No external service outages

## Code Review

### What the Review Agent Checks

**Linting** (language-specific):
- Python: ruff, mypy
- JavaScript/TypeScript: eslint, tsc
- Go: golint, go vet
- Rust: cargo clippy

**Security** (OWASP/SAST):
- SQL injection
- XSS vulnerabilities
- Hardcoded secrets
- Insecure dependencies

**Best Practices**:
- Cyclomatic complexity
- Code duplication (DRY)
- Error handling patterns
- Input validation

### Review Items Must Be Fixed

When the Review Agent finds issues, the Coding Agent **must** fix them:

```
[AGENT:review-001] 5 items found:
  1. SECURITY: SQL injection at db.py:45
  2. LINT: Missing type hints
  3. PRACTICE: Duplicate code
  ...

[AGENT:code-001] Fixing all items...
[AGENT:code-001] Resubmitting for review...

[AGENT:review-001] 0 items. APPROVED.
```

## Evidence Requirements

Every task requires evidence:

```markdown
## Evidence: User Authentication

### Tests Executed
- Unit tests: 15 passed, 0 failed
- Integration tests: 3 passed
- Coverage: 95%

### Artifacts Verified
- [x] Code compiles
- [x] No linting errors
- [x] Type checks pass
- [x] Documentation updated

### Evidence Files
- test-output.txt
- coverage.html
- screenshots/
```

## Testing Tools

### Bundled Tools

| Tool | Purpose |
|------|---------|
| pytest | Python testing |
| httpx | HTTP client |
| pexpect | CLI interaction |
| pillow | Image analysis |
| responses | HTTP mocking |

### Auto-Discovered Tools

Beyond Ralph's Research Agent can discover and install:

| Category | Tools |
|----------|-------|
| Web | playwright, selenium, puppeteer |
| Mobile | appium |
| Desktop | pyautogui, sikuli |
| API | postman, insomnia |
| Load | locust, k6 |

## Test Coverage

### Checkboxes

Each task has 7 checkboxes:

| Checkbox | Description | Agent Responsible |
|----------|-------------|-------------------|
| Planned | Task designed | Planning Agent |
| Implemented | Code written | Coding Agent |
| Mock tested | Unit tests pass | Testing Agent |
| Integration tested | Integration tests pass | Testing Agent |
| Live tested | Works in real environment | Testing Agent |
| Spec compliant | Matches specification | Compliance Agent |

### Coverage Requirements

Beyond Ralph targets:
- **Unit test coverage**: 80%+ line coverage
- **Branch coverage**: All major branches tested
- **Integration coverage**: All API endpoints tested
- **Spec compliance**: 100% requirements covered

## Autonomous Tool Installation

If Beyond Ralph needs a testing tool:

1. Research Agent searches for options
2. Evaluates platform compatibility
3. Checks if actively maintained
4. Installs automatically (no approval needed post-interview)
5. Documents in knowledge base

Example:
```
[AGENT:research-001] Need: Electron testing
[AGENT:research-001] Found: playwright (recommended)
[AGENT:research-001] Installing...
[AGENT:research-001] Added to project dependencies
[KNOWLEDGE] Stored: electron-testing-playwright.md
```

## System Package Installation

With passwordless sudo, Beyond Ralph can install:

- Browsers (Chrome, Firefox, Chromium)
- Compilers (gcc, make)
- Databases (PostgreSQL, Redis)
- Runtime libraries

```bash
# Detected passwordless sudo
sudo apt install -y chromium-browser
sudo apt install -y postgresql
```

## Troubleshooting Tests

### Tests Failing

1. Check the evidence files
2. Review test output in records/
3. Check if dependencies are installed
4. Verify mock server is running

### Flaky Tests

Beyond Ralph retries flaky tests and:
- Increases timeouts
- Adds explicit waits
- Documents flakiness in knowledge base

### Missing Test Tools

If a tool is missing, Beyond Ralph:
1. Searches for alternatives
2. Installs the best option
3. Updates project dependencies
4. Does NOT ask for permission (post-interview)

## Next Steps

- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Developer Guide](../developer/architecture.md) - Architecture details
