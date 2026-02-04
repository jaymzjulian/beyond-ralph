"""Claude Code Terminal Driver.

A test automation framework for driving Claude Code CLI sessions,
similar to how Playwright/Selenium drive web browsers.

This enables end-to-end testing of Beyond Ralph skills and agents.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DriverState(Enum):
    """State of the Claude Code driver."""

    IDLE = "idle"
    WAITING_FOR_RESPONSE = "waiting_for_response"
    RESPONSE_COMPLETE = "response_complete"
    ASKING_USER = "asking_user"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class ClaudeResponse:
    """Response from Claude Code."""

    text: str
    duration_ms: float
    tool_calls: list[str] = field(default_factory=list)
    agent_outputs: list[tuple[str, str]] = field(default_factory=list)  # (agent_id, text)
    user_questions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    raw_output: str = ""


@dataclass
class DriverConfig:
    """Configuration for Claude Code driver."""

    timeout: float = 120.0  # Max wait time for response
    poll_interval: float = 0.1  # How often to check for output
    working_dir: Path | None = None  # Working directory for Claude
    env: dict[str, str] = field(default_factory=dict)  # Environment variables
    dangerously_skip_permissions: bool = True  # Skip permission prompts
    verbose: bool = False  # Enable verbose output
    use_print_mode: bool = True  # Use --print for non-interactive mode
    output_format: str = "text"  # Output format: text, json, stream-json


class ClaudeCodeDriver:
    """Driver for automating Claude Code CLI sessions.

    Similar to Playwright for browsers, this class provides methods to:
    - Start Claude Code sessions
    - Send prompts and commands
    - Wait for and parse responses
    - Handle interactive prompts
    - Capture agent outputs

    Example:
        async with ClaudeCodeDriver() as driver:
            response = await driver.send_prompt("Hello, Claude!")
            print(response.text)

            # Execute a skill
            response = await driver.execute_skill("/beyond-ralph status")
            print(response.text)
    """

    # ANSI escape code pattern for stripping terminal formatting
    ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b\[\?[0-9]+[hl]")

    # Patterns to detect various states
    PROMPT_PATTERN = r"^(>|claude>|\$|❯)\s*$"
    THINKING_PATTERN = r"(Thinking|Processing|Loading|\.\.\.)"
    AGENT_OUTPUT_PATTERN = r"\[AGENT:([a-zA-Z0-9-]+)\]\s*(.*)"
    USER_QUESTION_PATTERN = r"\[USER INPUT REQUIRED\]|AskUserQuestion|Select an option"
    ERROR_PATTERN = r"(Error:|ERROR:|Exception:|Traceback)"
    TOOL_CALL_PATTERN = r"(Using tool:|Calling:|Running:)\s*(.*)"

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        """Strip ANSI escape codes from text."""
        return cls.ANSI_PATTERN.sub("", text)

    def __init__(self, config: DriverConfig | None = None):
        """Initialize the driver.

        Args:
            config: Driver configuration. Uses defaults if not provided.
        """
        self.config = config or DriverConfig()
        self._process: Any = None
        self._state = DriverState.IDLE
        self._output_buffer: list[str] = []
        self._temp_dir: Path | None = None

    async def __aenter__(self) -> ClaudeCodeDriver:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start a new Claude Code session."""
        try:
            import pexpect
        except ImportError:
            raise RuntimeError("pexpect is required for ClaudeCodeDriver")

        # Create temp directory for isolation
        self._temp_dir = Path(tempfile.mkdtemp(prefix="claude_driver_"))

        # Build command
        cmd = "claude"
        args = []

        if self.config.dangerously_skip_permissions:
            args.append("--dangerously-skip-permissions")

        if self.config.verbose:
            args.append("--verbose")

        # Set up environment
        env = os.environ.copy()
        env.update(self.config.env)

        # Set working directory
        cwd = str(self.config.working_dir) if self.config.working_dir else str(self._temp_dir)

        logger.info("Starting Claude Code session in %s", cwd)

        # Spawn the process
        full_cmd = f"{cmd} {' '.join(args)}" if args else cmd
        self._process = pexpect.spawn(
            full_cmd,
            cwd=cwd,
            env=env,
            encoding="utf-8",
            timeout=self.config.timeout,
        )

        # Wait for initial prompt
        await self._wait_for_ready()
        self._state = DriverState.IDLE
        logger.info("Claude Code session started")

    async def close(self) -> None:
        """Close the Claude Code session."""
        if self._process is None:
            return

        try:
            # Send quit command
            self._process.sendline("/quit")
            await asyncio.sleep(0.5)

            # Force close if needed
            if self._process.isalive():
                self._process.close(force=True)

        except Exception as e:
            logger.warning("Error closing Claude session: %s", e)

        finally:
            self._process = None
            self._state = DriverState.CLOSED

            # Clean up temp directory
            if self._temp_dir and self._temp_dir.exists():
                import shutil

                try:
                    shutil.rmtree(self._temp_dir)
                except Exception:
                    pass

        logger.info("Claude Code session closed")

    async def send_prompt(self, prompt: str, timeout: float | None = None) -> ClaudeResponse:
        """Send a prompt to Claude and wait for response.

        Args:
            prompt: The prompt text to send.
            timeout: Custom timeout (uses config default if not specified).

        Returns:
            ClaudeResponse with the parsed response.
        """
        if self._process is None:
            raise RuntimeError("Driver not started. Call start() first.")

        timeout = timeout or self.config.timeout
        start_time = time.time()

        logger.debug("Sending prompt: %s", prompt[:100])
        self._state = DriverState.WAITING_FOR_RESPONSE
        self._output_buffer = []

        # Send the prompt
        self._process.sendline(prompt)

        # Wait for and collect response
        response = await self._collect_response(timeout)

        duration_ms = (time.time() - start_time) * 1000
        response.duration_ms = duration_ms

        self._state = DriverState.RESPONSE_COMPLETE
        logger.debug("Response received in %.0f ms", duration_ms)

        return response

    async def execute_skill(self, skill_command: str, timeout: float | None = None) -> ClaudeResponse:
        """Execute a Claude Code skill (slash command).

        Args:
            skill_command: The skill command (e.g., "/beyond-ralph status").
            timeout: Custom timeout.

        Returns:
            ClaudeResponse with the skill output.
        """
        if not skill_command.startswith("/"):
            skill_command = "/" + skill_command

        return await self.send_prompt(skill_command, timeout)

    async def answer_question(self, answer: str) -> ClaudeResponse:
        """Answer a user question prompt.

        Args:
            answer: The answer to provide.

        Returns:
            ClaudeResponse with the continuation.
        """
        if self._state != DriverState.ASKING_USER:
            logger.warning("No question pending, sending as regular prompt")

        return await self.send_prompt(answer)

    async def select_option(self, option_index: int) -> ClaudeResponse:
        """Select an option from a multiple choice prompt.

        Args:
            option_index: Zero-based index of the option to select.

        Returns:
            ClaudeResponse with the continuation.
        """
        # Options are typically 1-indexed in Claude's UI
        return await self.answer_question(str(option_index + 1))

    async def wait_for_completion(self, timeout: float | None = None) -> ClaudeResponse:
        """Wait for any ongoing operation to complete.

        Args:
            timeout: Maximum time to wait.

        Returns:
            ClaudeResponse with any collected output.
        """
        timeout = timeout or self.config.timeout
        return await self._collect_response(timeout)

    def get_state(self) -> DriverState:
        """Get current driver state."""
        return self._state

    def is_asking_user(self) -> bool:
        """Check if Claude is waiting for user input."""
        return self._state == DriverState.ASKING_USER

    async def _wait_for_ready(self) -> None:
        """Wait for Claude to be ready for input."""
        import pexpect

        try:
            # Wait for any initial output to settle
            await asyncio.sleep(1.0)

            # Read any startup messages
            while True:
                try:
                    self._process.expect(r".+", timeout=0.5)
                except pexpect.TIMEOUT:
                    break

        except pexpect.EOF:
            raise RuntimeError("Claude process ended unexpectedly")

    async def _collect_response(self, timeout: float) -> ClaudeResponse:
        """Collect response output until completion.

        Args:
            timeout: Maximum time to wait.

        Returns:
            Parsed ClaudeResponse.
        """
        import pexpect

        start_time = time.time()
        lines: list[str] = []
        agent_outputs: list[tuple[str, str]] = []
        tool_calls: list[str] = []
        user_questions: list[str] = []
        errors: list[str] = []

        # Patterns that indicate we should keep waiting
        thinking_indicators = ["...", "Thinking", "Processing"]

        # Track silence to detect completion
        last_output_time = time.time()
        silence_threshold = 3.0  # Seconds of silence before considering done
        min_response_time = 2.0  # Minimum time to wait for response

        # UI elements to filter out
        ui_patterns = [
            r"^─+$",  # Horizontal lines
            r"bypass permissions",
            r"ctrl\+",
            r"shift\+",
            r"⏵",
            r"to cycle",
            r"to edit in",
            r"^\s*$",  # Empty lines
        ]

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning("Timeout waiting for response after %.0f seconds", elapsed)
                break

            try:
                # Try to read a line
                self._process.expect(r"[^\r\n]+", timeout=self.config.poll_interval)
                raw_line = self._process.after.strip() if self._process.after else ""
                # Strip ANSI escape codes
                line = self.strip_ansi(raw_line)

                if line:
                    last_output_time = time.time()
                    lines.append(line)
                    logger.debug("Output: %s", line[:100])

                    # Parse agent output
                    agent_match = re.search(self.AGENT_OUTPUT_PATTERN, line)
                    if agent_match:
                        agent_id = agent_match.group(1)
                        agent_text = agent_match.group(2)
                        agent_outputs.append((agent_id, agent_text))

                    # Parse tool calls
                    tool_match = re.search(self.TOOL_CALL_PATTERN, line)
                    if tool_match:
                        tool_calls.append(tool_match.group(2))

                    # Check for user questions
                    if re.search(self.USER_QUESTION_PATTERN, line):
                        user_questions.append(line)
                        self._state = DriverState.ASKING_USER

                    # Check for errors
                    if re.search(self.ERROR_PATTERN, line):
                        errors.append(line)

            except pexpect.TIMEOUT:
                # Check if we've been silent long enough
                silence_duration = time.time() - last_output_time
                total_elapsed = time.time() - start_time

                if silence_duration > silence_threshold and total_elapsed > min_response_time:
                    # Check if still showing thinking indicators
                    if not lines or not any(ind in lines[-1] for ind in thinking_indicators):
                        logger.debug("Response complete (%.1f seconds of silence)", silence_duration)
                        break

            except pexpect.EOF:
                logger.warning("Process ended unexpectedly")
                self._state = DriverState.ERROR
                break

        raw_output = "\n".join(lines)

        # Extract main text (remove agent prefixes, tool calls, and UI elements)
        text_lines = []
        for line in lines:
            # Skip agent/tool output
            if re.match(self.AGENT_OUTPUT_PATTERN, line) or re.match(self.TOOL_CALL_PATTERN, line):
                continue
            # Skip UI elements
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in ui_patterns):
                continue
            text_lines.append(line)

        return ClaudeResponse(
            text="\n".join(text_lines),
            duration_ms=0,  # Will be set by caller
            tool_calls=tool_calls,
            agent_outputs=agent_outputs,
            user_questions=user_questions,
            errors=errors,
            raw_output=raw_output,
        )


class ClaudeCodeTestRunner:
    """Test runner for Claude Code integration tests.

    Provides high-level methods for testing Beyond Ralph functionality.
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize test runner.

        Args:
            project_root: Root directory for test projects.
        """
        self.project_root = project_root or Path.cwd()
        self.driver: ClaudeCodeDriver | None = None
        self.results: list[dict[str, Any]] = []

    async def setup(self) -> None:
        """Set up the test environment."""
        config = DriverConfig(
            working_dir=self.project_root,
            dangerously_skip_permissions=True,
            timeout=180.0,  # 3 minutes for complex operations
        )
        self.driver = ClaudeCodeDriver(config)
        await self.driver.start()

    async def teardown(self) -> None:
        """Clean up test environment."""
        if self.driver:
            await self.driver.close()
            self.driver = None

    async def test_skill_available(self, skill_name: str) -> bool:
        """Test if a skill is available.

        Args:
            skill_name: Name of the skill (e.g., "beyond-ralph").

        Returns:
            True if skill is available.
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")

        # Use /help to check available skills
        response = await self.driver.send_prompt("/help", timeout=30)
        return skill_name in response.text

    async def test_beyond_ralph_status(self) -> dict[str, Any]:
        """Test /beyond-ralph status command.

        Returns:
            Dict with test results.
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")

        result = {
            "test": "beyond_ralph_status",
            "passed": False,
            "response": None,
            "error": None,
        }

        try:
            response = await self.driver.execute_skill("/beyond-ralph status", timeout=60)
            result["response"] = response.text
            result["passed"] = "error" not in response.text.lower() or len(response.errors) == 0
        except Exception as e:
            result["error"] = str(e)

        self.results.append(result)
        return result

    async def test_beyond_ralph_start(self, spec_path: Path) -> dict[str, Any]:
        """Test /beyond-ralph start command.

        Args:
            spec_path: Path to specification file.

        Returns:
            Dict with test results.
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")

        result = {
            "test": "beyond_ralph_start",
            "passed": False,
            "response": None,
            "phases_completed": [],
            "error": None,
        }

        try:
            response = await self.driver.execute_skill(
                f"/beyond-ralph start --spec {spec_path}",
                timeout=300,  # 5 minutes for full run
            )

            result["response"] = response.text
            result["agent_outputs"] = response.agent_outputs

            # Check for phase completions
            phase_pattern = r"Phase (\d+):"
            phases = re.findall(phase_pattern, response.raw_output)
            result["phases_completed"] = list(set(phases))

            # Check for completion
            result["passed"] = (
                "complete" in response.text.lower()
                or "Project complete" in response.raw_output
                or len(phases) >= 8
            )

        except Exception as e:
            result["error"] = str(e)

        self.results.append(result)
        return result

    async def test_subagent_streaming(self) -> dict[str, Any]:
        """Test that subagent output is properly streamed.

        Returns:
            Dict with test results.
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")

        result = {
            "test": "subagent_streaming",
            "passed": False,
            "agent_outputs": [],
            "error": None,
        }

        try:
            # Run a command that spawns subagents
            response = await self.driver.send_prompt(
                "Use the Task tool to spawn an agent that says hello",
                timeout=120,
            )

            result["agent_outputs"] = response.agent_outputs
            result["passed"] = len(response.agent_outputs) > 0

        except Exception as e:
            result["error"] = str(e)

        self.results.append(result)
        return result

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all test results.

        Returns:
            Summary dict with pass/fail counts.
        """
        passed = sum(1 for r in self.results if r.get("passed", False))
        failed = len(self.results) - passed

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.results) if self.results else 0,
            "results": self.results,
        }


async def run_prompt_once(
    prompt: str,
    working_dir: Path | None = None,
    timeout: float = 120.0,
    dangerously_skip_permissions: bool = True,
) -> ClaudeResponse:
    """Run a single prompt using Claude's --print mode.

    This is simpler and more reliable than interactive mode for testing.

    Args:
        prompt: The prompt to send.
        working_dir: Working directory for Claude.
        timeout: Maximum time to wait.
        dangerously_skip_permissions: Skip permission prompts.

    Returns:
        ClaudeResponse with the result.
    """
    import subprocess

    start_time = time.time()

    # Build command
    cmd = ["claude", "--print"]
    if dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    # Add prompt
    cmd.append(prompt)

    logger.info("Running: %s", " ".join(cmd[:4]) + "...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(working_dir) if working_dir else None,
        )

        duration_ms = (time.time() - start_time) * 1000

        # Parse output
        text = result.stdout.strip()
        errors = [result.stderr.strip()] if result.stderr.strip() else []

        if result.returncode != 0:
            errors.append(f"Exit code: {result.returncode}")

        return ClaudeResponse(
            text=text,
            duration_ms=duration_ms,
            errors=errors,
            raw_output=result.stdout,
        )

    except subprocess.TimeoutExpired:
        return ClaudeResponse(
            text="",
            duration_ms=(time.time() - start_time) * 1000,
            errors=["Timeout expired"],
        )
    except Exception as e:
        return ClaudeResponse(
            text="",
            duration_ms=(time.time() - start_time) * 1000,
            errors=[str(e)],
        )


async def run_live_tests(project_root: Path | None = None) -> dict[str, Any]:
    """Run live Claude Code integration tests.

    Args:
        project_root: Root directory for tests.

    Returns:
        Test results summary.
    """
    runner = ClaudeCodeTestRunner(project_root)

    try:
        print("Setting up Claude Code test environment...")
        await runner.setup()

        print("\nRunning tests...")

        # Test 1: Check skill availability
        print("  [1/3] Testing skill availability...")
        skill_available = await runner.test_skill_available("beyond-ralph")
        print(f"        Skill available: {skill_available}")

        # Test 2: Test status command
        print("  [2/3] Testing /beyond-ralph status...")
        status_result = await runner.test_beyond_ralph_status()
        print(f"        Passed: {status_result['passed']}")

        # Test 3: Test with a simple spec (if available)
        test_spec = project_root / "test_projects" / "hello_world" / "SPEC.md" if project_root else None
        if test_spec and test_spec.exists():
            print("  [3/3] Testing /beyond-ralph start...")
            start_result = await runner.test_beyond_ralph_start(test_spec)
            print(f"        Passed: {start_result['passed']}")
            print(f"        Phases completed: {start_result.get('phases_completed', [])}")
        else:
            print("  [3/3] Skipping start test (no test spec found)")

        # Get summary
        summary = runner.get_summary()
        print(f"\nTest Summary: {summary['passed']}/{summary['total']} passed")

        return summary

    finally:
        print("\nCleaning up...")
        await runner.teardown()


def main() -> None:
    """CLI entry point for running live tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Run live Claude Code tests")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    summary = asyncio.run(run_live_tests(args.project_root))

    # Exit with error code if tests failed
    if summary["failed"] > 0:
        exit(1)


if __name__ == "__main__":
    main()
