# Module 3: Testing Skills - Specification

**Module**: testing
**Location**: `src/beyond_ralph/testing/`
**Dependencies**: research (for tool discovery), system-capabilities (for display setup)

## Purpose

Provide bundled testing capabilities for all application types, plus automatic discovery and installation of additional testing tools.

## Requirements

### R1: API/Backend Testing
- Mock API testing first (develop against mocks)
- Real endpoint testing when mocks pass
- Request/response validation
- Error scenario testing
- Support for OpenAPI/Swagger spec ingestion

**Bundled Tools**: httpx, pytest, responses, respx

### R2: Web UI Testing
- Browser automation with cross-browser support
- Screenshot capture for evidence
- Element interaction and form testing
- Navigation and routing testing
- Responsive layout testing
- Prefer Playwright (our preferred tool)

**Bundled Tools**: playwright

### R3: CLI Testing
- Process spawning and control
- Input/output verification
- Exit code checking
- Interactive CLI support (expect-style)
- Timeout handling for hung processes

**Bundled Tools**: pexpect, subprocess

### R4: Desktop GUI Testing
- Screenshot capture and analysis
- Image comparison (before/after)
- GUI automation where possible
- VNC/RDP integration for headless environments
- Window detection and interaction

**Bundled Tools**: pillow, pyautogui

### R5: Graphics/Game Testing
- Frame capture from video output
- Image analysis and comparison
- Motion detection
- Color/pattern recognition
- FPS measurement if available

**Bundled Tools**: opencv-python, pillow

### R6: Mock API Server
- Generate mock server from OpenAPI spec
- Record and replay capability
- Programmable responses
- Latency/error simulation
- Automatic transition: mock passes → test against real

### R7: Mobile Testing
- Android emulator support
- Screenshot capture from emulator
- App installation and interaction
- Discovered via Research Agent when needed

### R8: Test Workflow
```
1. All tests start against MOCKS
2. Mock tests must achieve 100% coverage
3. Automatic transition to real APIs when mocks pass
4. Real API tests run non-destructively
5. Gaps documented in UNTESTABLE.md with justification
```

## Interface

```python
class TestingSkill:
    """Base class for testing skills."""

    async def setup(self) -> None:
        """Set up testing environment."""

    async def teardown(self) -> None:
        """Clean up testing environment."""

    async def run_tests(self, target: Path) -> TestResult:
        """Run tests and return results with evidence."""

    async def generate_evidence(self) -> Evidence:
        """Generate evidence of test run."""

class MockAPIServer:
    """Local mock API server."""

    async def from_openapi(self, spec_path: Path) -> None:
        """Load endpoints from OpenAPI spec."""

    async def start(self, port: int = 8080) -> None:
        """Start mock server."""

    async def stop(self) -> None:
        """Stop mock server."""

    def record(self) -> None:
        """Start recording requests."""

    def replay(self) -> None:
        """Replay recorded requests."""

@dataclass
class TestResult:
    passed: bool
    tests_run: int
    tests_passed: int
    tests_failed: int
    coverage_percent: float
    evidence: Evidence
    failures: list[TestFailure]
```

## Display Server Integration

For headless testing:
```python
async def setup_display() -> VirtualDisplay:
    """Set up virtual display for GUI testing.

    Priority order:
    1. Wayland (native, best performance)
    2. xvnc (VNC accessible, good for debugging)
    3. Xvfb (fallback, reliable)
    """
```

## Testing Requirements

- Test each skill with mock applications
- Test mock server with sample OpenAPI specs
- Test display server setup on available platforms
- Test evidence generation format
- 100% coverage required for testing infrastructure itself
