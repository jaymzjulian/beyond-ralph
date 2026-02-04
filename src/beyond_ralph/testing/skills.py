"""Testing Skills - Bundled testing capabilities for Beyond Ralph.

Provides testing frameworks and tools for:
- API/Backend: httpx, pytest, responses/respx for mocking
- Web UI: playwright for browser automation
- CLI: pexpect, subprocess for process interaction
- Desktop GUI: pillow, pyautogui for screenshots and automation
- Graphics/Games: opencv-python for frame analysis
- Mobile: Android emulator support

The testing module also provides a mock API server generator
that creates mock endpoints from OpenAPI specifications.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

AppType = Literal[
    "api",      # REST/GraphQL APIs
    "web",      # Web applications (browser-based)
    "cli",      # Command-line applications
    "desktop",  # Desktop GUI applications
    "mobile",   # Mobile applications
    "game",     # Games and graphics applications
]


class TestStatus(Enum):
    """Status of a test run."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestEvidence:
    """Evidence from a test run."""

    type: str  # screenshot, log, video, trace, report
    path: Path
    description: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "path": str(self.path),
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TestResult:
    """Result of a test execution."""

    name: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    evidence: list[TestEvidence] = field(default_factory=list)
    coverage: float | None = None  # Test coverage percentage if available

    @property
    def passed(self) -> bool:
        return self.status == TestStatus.PASSED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "message": self.message,
            "evidence": [e.to_dict() for e in self.evidence],
            "coverage": self.coverage,
        }


class MockAPIServer:
    """Generate and run mock API servers from OpenAPI specs.

    Uses respx for httpx mocking or can spawn an actual mock server process.
    """

    def __init__(self, spec_path: Path | None = None) -> None:
        self.spec_path = spec_path
        self.endpoints: dict[str, dict[str, Any]] = {}
        self.process: subprocess.Popen | None = None
        self.port: int = 8080

    async def from_openapi(self, spec_path: Path) -> None:
        """Parse OpenAPI specification and generate mock endpoints.

        Args:
            spec_path: Path to OpenAPI JSON/YAML file
        """
        self.spec_path = spec_path

        try:
            import yaml

            content = spec_path.read_text()
            if spec_path.suffix in [".yaml", ".yml"]:
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)

            # Extract paths and generate mock responses
            paths = spec.get("paths", {})
            for path, methods in paths.items():
                self.endpoints[path] = {}
                for method, details in methods.items():
                    if method in ["get", "post", "put", "patch", "delete"]:
                        # Get example response or generate default
                        responses = details.get("responses", {})
                        success_response = responses.get("200") or responses.get("201")

                        example_response = {}
                        if success_response:
                            content = success_response.get("content", {})
                            json_content = content.get("application/json", {})
                            example_response = json_content.get("example", {})

                        self.endpoints[path][method.upper()] = {
                            "response": example_response,
                            "status_code": 200,
                            "description": details.get("summary", ""),
                        }

        except Exception as e:
            raise ValueError(f"Failed to parse OpenAPI spec: {e}") from e

    async def start(self, port: int = 8080) -> str:
        """Start mock server.

        Args:
            port: Port to listen on

        Returns:
            Base URL of the mock server
        """
        self.port = port

        # Generate a simple Flask-based mock server
        server_code = self._generate_server_code()

        # Write to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
        ) as f:
            f.write(server_code)
            server_file = f.name

        # Start server process
        self.process = subprocess.Popen(
            ["python", server_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        await asyncio.sleep(1)

        return f"http://localhost:{port}"

    async def stop(self) -> None:
        """Stop mock server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def _generate_server_code(self) -> str:
        """Generate Flask server code for mock endpoints."""
        routes = []
        for path, methods in self.endpoints.items():
            for method, config in methods.items():
                response_json = json.dumps(config["response"])
                flask_path = path.replace("{", "<").replace("}", ">")
                routes.append(f'''
@app.route("{flask_path}", methods=["{method}"])
def mock_{path.replace("/", "_").replace("<", "").replace(">", "")}_{method.lower()}():
    return jsonify({response_json}), {config["status_code"]}
''')

        return f'''
from flask import Flask, jsonify
app = Flask(__name__)

{"".join(routes)}

if __name__ == "__main__":
    app.run(port={self.port}, debug=False)
'''

    def add_endpoint(
        self,
        path: str,
        method: str,
        response: dict[str, Any],
        status_code: int = 200,
    ) -> None:
        """Add a custom mock endpoint.

        Args:
            path: URL path (e.g., "/api/users")
            method: HTTP method (GET, POST, etc.)
            response: Response body as dict
            status_code: HTTP status code to return
        """
        if path not in self.endpoints:
            self.endpoints[path] = {}

        self.endpoints[path][method.upper()] = {
            "response": response,
            "status_code": status_code,
        }


class TestRunner:
    """Run tests and collect results with evidence."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.evidence_dir = project_root / "test_evidence"

    async def run_pytest(
        self,
        test_path: str | None = None,
        coverage: bool = True,
        markers: list[str] | None = None,
    ) -> list[TestResult]:
        """Run pytest and collect results.

        Args:
            test_path: Specific test file/directory, or None for all tests
            coverage: Whether to collect coverage data
            markers: Pytest markers to filter tests

        Returns:
            List of test results
        """
        cmd = ["pytest", "-v", "--tb=short"]

        if coverage:
            cmd.extend(["--cov=src", "--cov-report=json"])

        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        if test_path:
            cmd.append(test_path)

        # Create evidence directory
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        # Run pytest with JSON report
        json_report = self.evidence_dir / "pytest_report.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report}"])

        try:
            start_time = datetime.now(UTC)
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )
            end_time = datetime.now(UTC)

            results = []

            # Parse JSON report if available
            if json_report.exists():
                report = json.loads(json_report.read_text())

                for test in report.get("tests", []):
                    status = TestStatus.PASSED
                    if test.get("outcome") == "failed":
                        status = TestStatus.FAILED
                    elif test.get("outcome") == "skipped":
                        status = TestStatus.SKIPPED
                    elif test.get("outcome") == "error":
                        status = TestStatus.ERROR

                    results.append(TestResult(
                        name=test.get("nodeid", "unknown"),
                        status=status,
                        duration_ms=test.get("duration", 0) * 1000,
                        message=test.get("longrepr", ""),
                    ))

                # Get coverage if available
                cov_file = self.project_root / "coverage.json"
                if cov_file.exists():
                    cov_data = json.loads(cov_file.read_text())
                    total_coverage = cov_data.get("totals", {}).get("percent_covered", 0)
                    if results:
                        results[0].coverage = total_coverage

            else:
                # Fallback: parse stdout for basic info
                passed = "passed" in result.stdout.lower()
                results.append(TestResult(
                    name="pytest",
                    status=TestStatus.PASSED if passed else TestStatus.FAILED,
                    duration_ms=(end_time - start_time).total_seconds() * 1000,
                    message=result.stdout[:500] if not passed else "",
                ))

            return results

        except subprocess.TimeoutExpired:
            return [TestResult(
                name="pytest",
                status=TestStatus.ERROR,
                duration_ms=600000,
                message="Test execution timed out",
            )]
        except Exception as e:
            return [TestResult(
                name="pytest",
                status=TestStatus.ERROR,
                duration_ms=0,
                message=str(e),
            )]

    async def run_playwright(
        self,
        test_path: str | None = None,
        browser: str = "chromium",
        headless: bool = True,
    ) -> list[TestResult]:
        """Run Playwright tests for web UI testing.

        Args:
            test_path: Specific test file, or None for all
            browser: Browser to use (chromium, firefox, webkit)
            headless: Run in headless mode

        Returns:
            List of test results
        """
        cmd = ["pytest", "-v"]

        if test_path:
            cmd.append(test_path)
        else:
            cmd.append("tests/")

        cmd.extend([
            f"--browser={browser}",
            "--headed" if not headless else "",
            "--screenshot=on",
            "--video=on",
            f"--output={self.evidence_dir}",
        ])

        # Filter out empty strings
        cmd = [c for c in cmd if c]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            # Collect evidence from playwright output directory
            evidence = []
            if self.evidence_dir.exists():
                for screenshot in self.evidence_dir.glob("*.png"):
                    evidence.append(TestEvidence(
                        type="screenshot",
                        path=screenshot,
                        description=f"Playwright screenshot: {screenshot.name}",
                    ))
                for video in self.evidence_dir.glob("*.webm"):
                    evidence.append(TestEvidence(
                        type="video",
                        path=video,
                        description=f"Playwright video: {video.name}",
                    ))

            passed = result.returncode == 0
            return [TestResult(
                name="playwright",
                status=TestStatus.PASSED if passed else TestStatus.FAILED,
                duration_ms=0,
                message="" if passed else result.stdout[:500],
                evidence=evidence,
            )]

        except Exception as e:
            return [TestResult(
                name="playwright",
                status=TestStatus.ERROR,
                duration_ms=0,
                message=str(e),
            )]

    async def capture_screenshot(
        self,
        name: str,
        description: str = "",
    ) -> TestEvidence | None:
        """Capture a screenshot for evidence.

        Args:
            name: Name for the screenshot file
            description: Description of what the screenshot shows

        Returns:
            TestEvidence if successful, None otherwise
        """
        try:
            from PIL import ImageGrab

            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = self.evidence_dir / f"{name}.png"

            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)

            return TestEvidence(
                type="screenshot",
                path=screenshot_path,
                description=description or f"Screenshot: {name}",
            )
        except Exception:
            return None


class TestingSkills:
    """Main class for testing skills orchestration.

    Provides methods to test various application types with appropriate
    tools and collect evidence.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.runner = TestRunner(project_root)
        self.mock_server: MockAPIServer | None = None

    def detect_app_type(self) -> AppType:
        """Detect the application type based on project structure.

        Returns:
            Detected AppType
        """
        # Check for indicators
        indicators: dict[str, list[str]] = {
            "api": [
                "openapi.yaml", "openapi.json", "swagger.yaml",
                "routes/", "controllers/", "endpoints/",
            ],
            "web": [
                "package.json", "index.html", "src/App.tsx",
                "src/App.jsx", "public/index.html",
            ],
            "cli": [
                "setup.py", "pyproject.toml",
                "__main__.py", "cli.py", "main.py",
            ],
            "desktop": [
                "*.ui", "*.qml", "tkinter", "pyqt", "wxpython",
            ],
            "mobile": [
                "android/", "ios/", "app.json", "AndroidManifest.xml",
            ],
            "game": [
                "pygame", "godot", "unity", "*.unity", "*.godot",
            ],
        }

        for app_type, patterns in indicators.items():
            for pattern in patterns:
                if "/" in pattern:
                    # Directory check
                    if (self.project_root / pattern.rstrip("/")).is_dir():
                        return app_type  # type: ignore
                elif "*" in pattern:
                    # Glob pattern
                    if list(self.project_root.glob(f"**/{pattern}")):
                        return app_type  # type: ignore
                else:
                    # File check
                    if (self.project_root / pattern).exists():
                        return app_type  # type: ignore

        return "cli"  # Default to CLI

    async def test_api(
        self,
        base_url: str | None = None,
        openapi_spec: Path | None = None,
    ) -> list[TestResult]:
        """Test API endpoints.

        Args:
            base_url: Base URL of the API, or None to use mock server
            openapi_spec: Path to OpenAPI spec for mock server

        Returns:
            List of test results
        """
        if base_url is None and openapi_spec:
            # Start mock server
            self.mock_server = MockAPIServer()
            await self.mock_server.from_openapi(openapi_spec)
            base_url = await self.mock_server.start()

        try:
            # Run API tests
            return await self.runner.run_pytest(
                test_path="tests/",
                markers=["api"],
            )
        finally:
            if self.mock_server:
                await self.mock_server.stop()

    async def test_web(
        self,
        url: str | None = None,
        browser: str = "chromium",
    ) -> list[TestResult]:
        """Test web application UI.

        Args:
            url: URL to test, or None to start dev server
            browser: Browser to use

        Returns:
            List of test results with screenshots/videos
        """
        return await self.runner.run_playwright(
            browser=browser,
            headless=True,
        )

    async def test_cli(
        self,
        command: str,
        expected_output: str | None = None,
        timeout: int = 60,
        interactive: bool = False,
    ) -> list[TestResult]:
        """Test CLI application.

        Uses pexpect for interactive testing or subprocess for simple commands.

        Args:
            command: Command to run
            expected_output: Expected output substring
            timeout: Timeout in seconds
            interactive: If True, use pexpect for interactive testing

        Returns:
            List of test results
        """
        start_time = datetime.now(UTC)
        evidence: list[TestEvidence] = []

        try:
            if interactive:
                # Use pexpect for interactive CLI testing
                try:
                    import pexpect

                    child = pexpect.spawn(command, timeout=timeout, encoding="utf-8")

                    output_lines = []
                    while True:
                        try:
                            index = child.expect(["\r\n", "\n", pexpect.EOF], timeout=5)
                            if index in (0, 1):
                                output_lines.append(child.before)
                            else:
                                if child.before:
                                    output_lines.append(child.before)
                                break
                        except pexpect.EOF:
                            break
                        except pexpect.TIMEOUT:
                            if not child.isalive():
                                break

                    child.close()
                    exit_code = child.exitstatus or 0
                    output = "\n".join(output_lines)

                except ImportError:
                    # Fall back to subprocess
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=self.project_root,
                    )
                    exit_code = result.returncode
                    output = result.stdout + result.stderr
            else:
                # Simple subprocess execution
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.project_root,
                )
                exit_code = result.returncode
                output = result.stdout + result.stderr

            # Save output as evidence
            self.runner.evidence_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.runner.evidence_dir / f"cli_output_{datetime.now().strftime('%H%M%S')}.txt"
            log_path.write_text(output)
            evidence.append(TestEvidence(
                type="log",
                path=log_path,
                description=f"CLI output for: {command[:50]}...",
            ))

            end_time = datetime.now(UTC)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Check expected output
            passed = exit_code == 0
            if expected_output and passed:
                passed = expected_output in output

            return [TestResult(
                name=f"cli: {command[:30]}",
                status=TestStatus.PASSED if passed else TestStatus.FAILED,
                duration_ms=duration_ms,
                message="" if passed else f"Exit code: {exit_code}\n{output[:500]}",
                evidence=evidence,
            )]

        except subprocess.TimeoutExpired:
            return [TestResult(
                name=f"cli: {command[:30]}",
                status=TestStatus.ERROR,
                duration_ms=timeout * 1000,
                message=f"Command timed out after {timeout}s",
            )]
        except Exception as e:
            return [TestResult(
                name=f"cli: {command[:30]}",
                status=TestStatus.ERROR,
                duration_ms=0,
                message=str(e),
            )]

    async def test_desktop_gui(
        self,
        window_title: str | None = None,
        screenshot_interval: float = 1.0,
        duration: float = 5.0,
    ) -> list[TestResult]:
        """Test desktop GUI application by capturing screenshots.

        Args:
            window_title: Title of window to capture (None for full screen)
            screenshot_interval: Seconds between screenshots
            duration: Total duration to capture

        Returns:
            List of test results with screenshot evidence
        """
        evidence: list[TestEvidence] = []
        start_time = datetime.now(UTC)

        try:
            from PIL import ImageGrab

            self.runner.evidence_dir.mkdir(parents=True, exist_ok=True)

            # Capture screenshots at intervals
            captured = 0
            elapsed = 0.0
            while elapsed < duration:
                screenshot = ImageGrab.grab()
                screenshot_path = self.runner.evidence_dir / f"desktop_{captured:03d}.png"
                screenshot.save(screenshot_path)

                evidence.append(TestEvidence(
                    type="screenshot",
                    path=screenshot_path,
                    description=f"Desktop screenshot at {elapsed:.1f}s",
                ))

                captured += 1
                await asyncio.sleep(screenshot_interval)
                elapsed += screenshot_interval

            end_time = datetime.now(UTC)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            return [TestResult(
                name="desktop_gui",
                status=TestStatus.PASSED,
                duration_ms=duration_ms,
                message=f"Captured {captured} screenshots",
                evidence=evidence,
            )]

        except ImportError:
            return [TestResult(
                name="desktop_gui",
                status=TestStatus.ERROR,
                duration_ms=0,
                message="Pillow not installed. Run: uv add pillow",
            )]
        except Exception as e:
            return [TestResult(
                name="desktop_gui",
                status=TestStatus.ERROR,
                duration_ms=0,
                message=str(e),
            )]

    async def analyze_screenshot(
        self,
        screenshot_path: Path,
        expected_elements: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze a screenshot for expected elements.

        Uses basic image analysis. For more advanced analysis,
        the orchestrator should spawn an LLM agent.

        Args:
            screenshot_path: Path to screenshot
            expected_elements: List of expected element descriptions

        Returns:
            Analysis results dict
        """
        try:
            from PIL import Image

            img = Image.open(screenshot_path)
            width, height = img.size
            mode = img.mode

            # Basic analysis
            analysis = {
                "path": str(screenshot_path),
                "width": width,
                "height": height,
                "mode": mode,
                "format": img.format,
                "has_content": width > 0 and height > 0,
            }

            # For detailed element detection, spawn an LLM agent
            # This is a placeholder for basic structural checks
            if expected_elements:
                analysis["expected_elements"] = expected_elements
                analysis["note"] = "Element detection requires LLM agent analysis"

            return analysis

        except Exception as e:
            return {"error": str(e)}

    async def run_all_tests(self) -> list[TestResult]:
        """Run all tests and collect results.

        Returns:
            Combined list of all test results
        """
        return await self.runner.run_pytest(coverage=True)

    def get_coverage_report(self) -> dict[str, Any]:
        """Get test coverage report.

        Returns:
            Coverage data dictionary
        """
        cov_file = self.project_root / "coverage.json"
        if cov_file.exists():
            return json.loads(cov_file.read_text())
        return {"error": "No coverage data available"}

    async def cleanup(self) -> None:
        """Clean up any running mock servers or resources."""
        if self.mock_server:
            await self.mock_server.stop()
