# Module 6: Testing - Specification

> Testing Capabilities: Bundled testing tools for various application types.

---

## Overview

The Testing module provides bundled testing capabilities for different application types (API, Web, CLI, Desktop GUI, Games). It includes skills for running tests, mock servers for development, and screenshot analysis.

**Key Principle**: Test autonomously, provide evidence, support various app types.

---

## Location

`src/beyond_ralph/testing/`

---

## Components

### 6.1 Testing Skills (`skills.py`)

**Purpose**: High-level testing capabilities for different app types.

**Interface**:
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TestEvidence:
    """Evidence from test execution."""
    test_type: str
    passed: bool
    output: str
    coverage: Optional[float] = None
    screenshots: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

class TestingSkills:
    """Bundled testing capabilities for various app types."""

    async def test_api(
        self,
        base_url: str,
        endpoints: list[dict],
        use_mock: bool = True
    ) -> TestEvidence:
        """Test API endpoints.

        Args:
            base_url: Base URL of API (or mock server).
            endpoints: List of endpoint specs:
                [
                    {"method": "GET", "path": "/users", "expected_status": 200},
                    {"method": "POST", "path": "/users", "body": {...}, "expected_status": 201}
                ]
            use_mock: If True, start mock server first.

        Uses: httpx, pytest, responses

        Flow:
            1. If use_mock, start MockAPIServer
            2. Run endpoint tests
            3. Collect evidence
            4. Return TestEvidence
        """

    async def test_web(
        self,
        url: str,
        scenarios: list[dict]
    ) -> TestEvidence:
        """Test web UI.

        Args:
            url: URL to test.
            scenarios: List of test scenarios:
                [
                    {"name": "Login", "steps": [
                        {"action": "fill", "selector": "#email", "value": "test@example.com"},
                        {"action": "click", "selector": "#submit"},
                        {"action": "assert", "selector": ".welcome", "text": "Welcome"}
                    ]}
                ]

        Uses: playwright

        Captures screenshots at each step.
        """

    async def test_cli(
        self,
        command: str,
        scenarios: list[dict],
        interactive: bool = False
    ) -> TestEvidence:
        """Test CLI application.

        Args:
            command: Command to test.
            scenarios: List of test scenarios:
                [
                    {"args": ["--help"], "expected_output": "Usage:"},
                    {"args": ["create", "foo"], "expected_exit_code": 0}
                ]
            interactive: If True, use pexpect for interactive testing.

        Uses: pexpect, subprocess
        """

    async def test_desktop_gui(
        self,
        app_command: str,
        scenarios: list[dict]
    ) -> TestEvidence:
        """Test desktop GUI application.

        Args:
            app_command: Command to launch app.
            scenarios: List of test scenarios:
                [
                    {"name": "Startup", "screenshot": True},
                    {"action": "click", "coords": [100, 200], "screenshot": True}
                ]

        Uses: pillow, pyautogui

        Requires display (Xvfb or real).
        """

    async def analyze_screenshot(
        self,
        image_path: str,
        expected: str
    ) -> bool:
        """Analyze screenshot for expected content.

        Uses image analysis to verify UI state.
        Returns True if expected content found.
        """

    async def test_game(
        self,
        game_command: str,
        scenarios: list[dict]
    ) -> TestEvidence:
        """Test game/graphics application.

        Args:
            game_command: Command to launch game.
            scenarios: Frame capture and analysis scenarios.

        Uses: pillow, opencv-python (if available)
        """
```

---

### 6.2 Mock API Server (`mock_server.py`)

**Purpose**: Provide mock APIs for development testing.

**Interface**:
```python
from typing import Optional

class MockAPIServer:
    """Mock API server for development testing."""

    def __init__(self, port: int = 8000) -> None:
        """Initialize mock server."""

    @classmethod
    def from_openapi(cls, spec_path: str, port: int = 8000) -> "MockAPIServer":
        """Create mock server from OpenAPI/Swagger spec.

        Automatically generates mock endpoints from spec.
        """

    def add_endpoint(
        self,
        method: str,
        path: str,
        response: dict,
        status_code: int = 200
    ) -> None:
        """Add mock endpoint.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: URL path (supports path params like /users/{id}).
            response: JSON response body.
            status_code: HTTP status code.
        """

    def add_error_endpoint(
        self,
        method: str,
        path: str,
        error_code: int,
        error_message: str
    ) -> None:
        """Add mock error endpoint."""

    def add_delay(self, path: str, delay_ms: int) -> None:
        """Add delay to endpoint for timeout testing."""

    async def start(self) -> None:
        """Start mock server in background."""

    async def stop(self) -> None:
        """Stop mock server."""

    def get_url(self) -> str:
        """Get base URL of mock server."""

    def get_request_log(self) -> list[dict]:
        """Get log of all requests made to mock server."""
```

---

### 6.3 Test Runner (`runner.py`)

**Purpose**: Unified test runner for all test types.

**Interface**:
```python
from typing import Callable

class TestRunner:
    """Unified test runner for all test types."""

    async def run_pytest(
        self,
        path: str,
        coverage: bool = True,
        markers: Optional[list[str]] = None
    ) -> TestEvidence:
        """Run pytest with coverage.

        Args:
            path: Path to tests (file or directory).
            coverage: If True, collect coverage data.
            markers: Optional pytest markers to filter tests.

        Returns:
            TestEvidence with output and coverage.
        """

    async def run_playwright(
        self,
        test_file: str
    ) -> TestEvidence:
        """Run playwright tests.

        Args:
            test_file: Path to playwright test file.

        Automatically captures screenshots and videos.
        """

    async def run_custom(
        self,
        command: str,
        parse_output: Callable[[str], TestEvidence]
    ) -> TestEvidence:
        """Run custom test command.

        Args:
            command: Command to run.
            parse_output: Function to parse output into TestEvidence.
        """

    async def run_all(
        self,
        test_paths: list[str]
    ) -> list[TestEvidence]:
        """Run all tests and collect evidence."""
```

---

### 6.4 API Doc Ingester (`api_docs.py`)

**Purpose**: Ingest and store API documentation.

**Interface**:
```python
@dataclass
class APIEndpoint:
    method: str
    path: str
    description: str
    parameters: list[dict]
    request_body: Optional[dict]
    responses: dict[int, dict]

@dataclass
class APIDocumentation:
    title: str
    version: str
    base_url: str
    endpoints: list[APIEndpoint]

class APIDocIngester:
    """Ingest API documentation for testing."""

    def ingest_openapi(self, spec_path: str) -> APIDocumentation:
        """Ingest OpenAPI/Swagger specification."""

    def ingest_postman(self, collection_path: str) -> APIDocumentation:
        """Ingest Postman collection."""

    def ingest_markdown(self, doc_path: str) -> APIDocumentation:
        """Ingest markdown API documentation."""

    def store_to_knowledge(
        self,
        docs: APIDocumentation,
        session_id: str
    ) -> None:
        """Store API docs in knowledge base for agents."""
```

---

## Bundled Dependencies

| App Type | Tools | PyPI Packages |
|----------|-------|---------------|
| API | HTTP client, mocking | httpx, pytest, responses |
| Web | Browser automation | playwright |
| CLI | Process interaction | pexpect, subprocess (stdlib) |
| Desktop GUI | Screen capture | pillow, pyautogui |
| Games | Frame capture | pillow, opencv-python |

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 8 (System) | Tool availability checks |
| Module 12 (Utils) | Logging, file operations |

---

## Error Handling

```python
class TestingError(BeyondRalphError):
    """Testing-related errors."""

class TestRunError(TestingError):
    """Test execution failed."""

class MockServerError(TestingError):
    """Mock server error."""

class ScreenshotError(TestingError):
    """Screenshot capture failed."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Test parsing, evidence collection |
| Integration tests | Full test execution |
| Live tests | Real browser/CLI tests |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
