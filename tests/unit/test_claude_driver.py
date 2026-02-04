"""Tests for Claude Code Terminal Driver."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest

from beyond_ralph.testing.claude_driver import (
    DriverState,
    ClaudeResponse,
    DriverConfig,
    ClaudeCodeDriver,
    ClaudeCodeTestRunner,
    run_prompt_once,
    run_live_tests,
    main,
)


class TestDriverState:
    """Tests for DriverState enum."""

    def test_all_states_exist(self):
        """All driver states should be defined."""
        assert DriverState.IDLE.value == "idle"
        assert DriverState.WAITING_FOR_RESPONSE.value == "waiting_for_response"
        assert DriverState.RESPONSE_COMPLETE.value == "response_complete"
        assert DriverState.ASKING_USER.value == "asking_user"
        assert DriverState.ERROR.value == "error"
        assert DriverState.CLOSED.value == "closed"

    def test_state_count(self):
        """Should have exactly 6 states."""
        assert len(DriverState) == 6


class TestClaudeResponse:
    """Tests for ClaudeResponse dataclass."""

    def test_default_values(self):
        """Response should have sensible defaults."""
        response = ClaudeResponse(text="Hello", duration_ms=100.0)
        assert response.text == "Hello"
        assert response.duration_ms == 100.0
        assert response.tool_calls == []
        assert response.agent_outputs == []
        assert response.user_questions == []
        assert response.errors == []
        assert response.raw_output == ""

    def test_with_all_fields(self):
        """Response should accept all fields."""
        response = ClaudeResponse(
            text="Test response",
            duration_ms=500.0,
            tool_calls=["Read", "Write"],
            agent_outputs=[("agent-1", "Hello"), ("agent-2", "World")],
            user_questions=["What is your name?"],
            errors=["Error occurred"],
            raw_output="raw text here",
        )
        assert response.text == "Test response"
        assert response.duration_ms == 500.0
        assert len(response.tool_calls) == 2
        assert len(response.agent_outputs) == 2
        assert response.agent_outputs[0] == ("agent-1", "Hello")
        assert len(response.user_questions) == 1
        assert len(response.errors) == 1
        assert response.raw_output == "raw text here"


class TestDriverConfig:
    """Tests for DriverConfig dataclass."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = DriverConfig()
        assert config.timeout == 120.0
        assert config.poll_interval == 0.1
        assert config.working_dir is None
        assert config.env == {}
        assert config.dangerously_skip_permissions is True
        assert config.verbose is False
        assert config.use_print_mode is True
        assert config.output_format == "text"

    def test_custom_values(self):
        """Config should accept custom values."""
        config = DriverConfig(
            timeout=60.0,
            poll_interval=0.5,
            working_dir=Path("/tmp/test"),
            env={"TEST": "value"},
            dangerously_skip_permissions=False,
            verbose=True,
            use_print_mode=False,
            output_format="json",
        )
        assert config.timeout == 60.0
        assert config.poll_interval == 0.5
        assert config.working_dir == Path("/tmp/test")
        assert config.env == {"TEST": "value"}
        assert config.dangerously_skip_permissions is False
        assert config.verbose is True
        assert config.use_print_mode is False
        assert config.output_format == "json"


class TestClaudeCodeDriver:
    """Tests for ClaudeCodeDriver class."""

    def test_strip_ansi(self):
        """ANSI escape codes should be stripped."""
        # Basic color codes
        assert ClaudeCodeDriver.strip_ansi("\x1b[31mRed text\x1b[0m") == "Red text"
        # Multiple codes
        assert ClaudeCodeDriver.strip_ansi("\x1b[1m\x1b[32mBold green\x1b[0m") == "Bold green"
        # No codes
        assert ClaudeCodeDriver.strip_ansi("Plain text") == "Plain text"
        # Empty string
        assert ClaudeCodeDriver.strip_ansi("") == ""
        # Complex sequences
        assert ClaudeCodeDriver.strip_ansi("\x1b[?25l\x1b[?25h") == ""

    def test_init_default_config(self):
        """Driver should use default config if none provided."""
        driver = ClaudeCodeDriver()
        assert driver.config.timeout == 120.0
        assert driver._process is None
        assert driver._state == DriverState.IDLE
        assert driver._output_buffer == []

    def test_init_custom_config(self):
        """Driver should use provided config."""
        config = DriverConfig(timeout=60.0)
        driver = ClaudeCodeDriver(config)
        assert driver.config.timeout == 60.0

    def test_get_state(self):
        """Should return current state."""
        driver = ClaudeCodeDriver()
        assert driver.get_state() == DriverState.IDLE

    def test_is_asking_user(self):
        """Should correctly detect asking user state."""
        driver = ClaudeCodeDriver()
        assert driver.is_asking_user() is False
        driver._state = DriverState.ASKING_USER
        assert driver.is_asking_user() is True

    @pytest.mark.asyncio
    async def test_start_without_pexpect(self):
        """Should raise error if pexpect not available."""
        driver = ClaudeCodeDriver()

        with patch.dict("sys.modules", {"pexpect": None}):
            with patch("builtins.__import__", side_effect=ImportError("No pexpect")):
                with pytest.raises(RuntimeError, match="pexpect is required"):
                    await driver.start()

    @pytest.mark.asyncio
    async def test_start_success(self):
        """Should start a Claude session successfully."""
        mock_pexpect = MagicMock()
        mock_process = MagicMock()
        mock_pexpect.spawn.return_value = mock_process
        mock_pexpect.TIMEOUT = Exception
        mock_pexpect.EOF = Exception

        # Configure expect to raise TIMEOUT (meaning startup is complete)
        mock_process.expect.side_effect = mock_pexpect.TIMEOUT

        with patch.dict("sys.modules", {"pexpect": mock_pexpect}):
            driver = ClaudeCodeDriver()
            await driver.start()

            assert driver._process is not None
            assert driver._state == DriverState.IDLE
            mock_pexpect.spawn.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_start(self):
        """Closing without starting should be safe."""
        driver = ClaudeCodeDriver()
        await driver.close()  # Should not raise
        # State remains IDLE because close() returns early if no process
        assert driver._state == DriverState.IDLE

    @pytest.mark.asyncio
    async def test_close_with_process(self):
        """Should close process and clean up."""
        mock_process = MagicMock()
        mock_process.isalive.return_value = True

        driver = ClaudeCodeDriver()
        driver._process = mock_process
        driver._temp_dir = Path("/tmp/test_dir")

        with patch("shutil.rmtree"):
            await driver.close()

        mock_process.sendline.assert_called_with("/quit")
        mock_process.close.assert_called_with(force=True)
        assert driver._process is None
        assert driver._state == DriverState.CLOSED

    @pytest.mark.asyncio
    async def test_close_handles_errors(self):
        """Should handle errors during close gracefully."""
        mock_process = MagicMock()
        mock_process.sendline.side_effect = Exception("Error")

        driver = ClaudeCodeDriver()
        driver._process = mock_process

        # Should not raise
        await driver.close()
        assert driver._process is None
        assert driver._state == DriverState.CLOSED

    @pytest.mark.asyncio
    async def test_send_prompt_without_start(self):
        """Should raise error if not started."""
        driver = ClaudeCodeDriver()
        with pytest.raises(RuntimeError, match="Driver not started"):
            await driver.send_prompt("Hello")

    @pytest.mark.asyncio
    async def test_send_prompt_success(self):
        """Should send prompt and collect response."""
        mock_pexpect = MagicMock()
        mock_process = MagicMock()
        mock_pexpect.TIMEOUT = type("TIMEOUT", (Exception,), {})
        mock_pexpect.EOF = type("EOF", (Exception,), {})

        # Simulate output then timeout (response complete)
        expect_call_count = [0]
        def expect_side_effect(*args, **kwargs):
            expect_call_count[0] += 1
            if expect_call_count[0] <= 2:
                mock_process.after = "Test output line"
                return 0
            raise mock_pexpect.TIMEOUT()

        mock_process.expect.side_effect = expect_side_effect

        driver = ClaudeCodeDriver()
        driver._process = mock_process

        # Create a counter-based time mock that always returns incrementing values
        time_counter = [0]
        def mock_time():
            time_counter[0] += 1
            return float(time_counter[0])

        # Mock sleep to speed up test
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with patch("time.time", side_effect=mock_time):
                with patch.dict("sys.modules", {"pexpect": mock_pexpect}):
                    response = await driver.send_prompt("Test prompt")

        mock_process.sendline.assert_called_with("Test prompt")
        assert response.duration_ms > 0
        assert driver._state == DriverState.RESPONSE_COMPLETE

    @pytest.mark.asyncio
    async def test_execute_skill_adds_slash(self):
        """Should add slash prefix if missing."""
        driver = ClaudeCodeDriver()
        driver._process = MagicMock()

        with patch.object(driver, "send_prompt", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = ClaudeResponse(text="", duration_ms=0)
            await driver.execute_skill("beyond-ralph status")
            mock_send.assert_called_with("/beyond-ralph status", None)

    @pytest.mark.asyncio
    async def test_execute_skill_preserves_slash(self):
        """Should preserve slash if already present."""
        driver = ClaudeCodeDriver()
        driver._process = MagicMock()

        with patch.object(driver, "send_prompt", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = ClaudeResponse(text="", duration_ms=0)
            await driver.execute_skill("/beyond-ralph status")
            mock_send.assert_called_with("/beyond-ralph status", None)

    @pytest.mark.asyncio
    async def test_answer_question(self):
        """Should send answer as prompt."""
        driver = ClaudeCodeDriver()
        driver._process = MagicMock()
        driver._state = DriverState.ASKING_USER

        with patch.object(driver, "send_prompt", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = ClaudeResponse(text="", duration_ms=0)
            await driver.answer_question("Yes")
            mock_send.assert_called_with("Yes")

    @pytest.mark.asyncio
    async def test_select_option(self):
        """Should convert 0-indexed to 1-indexed selection."""
        driver = ClaudeCodeDriver()
        driver._process = MagicMock()

        with patch.object(driver, "answer_question", new_callable=AsyncMock) as mock_answer:
            mock_answer.return_value = ClaudeResponse(text="", duration_ms=0)
            await driver.select_option(0)
            mock_answer.assert_called_with("1")

            await driver.select_option(2)
            mock_answer.assert_called_with("3")

    @pytest.mark.asyncio
    async def test_wait_for_completion(self):
        """Should collect response with default timeout."""
        driver = ClaudeCodeDriver()
        driver._process = MagicMock()

        with patch.object(driver, "_collect_response", new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = ClaudeResponse(text="Done", duration_ms=100)
            response = await driver.wait_for_completion()
            assert response.text == "Done"
            mock_collect.assert_called_with(120.0)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Should work as async context manager."""
        with patch.object(ClaudeCodeDriver, "start", new_callable=AsyncMock) as mock_start:
            with patch.object(ClaudeCodeDriver, "close", new_callable=AsyncMock) as mock_close:
                async with ClaudeCodeDriver() as driver:
                    pass
                mock_start.assert_called_once()
                mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_response_detects_agent_output(self):
        """Should detect and parse agent output."""
        mock_pexpect = MagicMock()
        mock_process = MagicMock()
        mock_pexpect.TIMEOUT = type("TIMEOUT", (Exception,), {})
        mock_pexpect.EOF = type("EOF", (Exception,), {})

        expect_call_count = [0]
        def expect_side_effect(*args, **kwargs):
            expect_call_count[0] += 1
            if expect_call_count[0] == 1:
                mock_process.after = "[AGENT:test-123] Hello from agent"
                return 0
            raise mock_pexpect.TIMEOUT()

        mock_process.expect.side_effect = expect_side_effect

        driver = ClaudeCodeDriver()
        driver._process = mock_process

        # Create incrementing time mock
        time_counter = [0]
        def mock_time():
            time_counter[0] += 1
            return float(time_counter[0])

        with patch("time.time", side_effect=mock_time):
            with patch.dict("sys.modules", {"pexpect": mock_pexpect}):
                response = await driver._collect_response(10.0)

        assert len(response.agent_outputs) == 1
        assert response.agent_outputs[0] == ("test-123", "Hello from agent")

    @pytest.mark.asyncio
    async def test_collect_response_detects_user_questions(self):
        """Should detect user question prompts."""
        mock_pexpect = MagicMock()
        mock_process = MagicMock()
        mock_pexpect.TIMEOUT = type("TIMEOUT", (Exception,), {})
        mock_pexpect.EOF = type("EOF", (Exception,), {})

        expect_call_count = [0]
        def expect_side_effect(*args, **kwargs):
            expect_call_count[0] += 1
            if expect_call_count[0] == 1:
                mock_process.after = "[USER INPUT REQUIRED]"
                return 0
            raise mock_pexpect.TIMEOUT()

        mock_process.expect.side_effect = expect_side_effect

        driver = ClaudeCodeDriver()
        driver._process = mock_process

        # Create incrementing time mock
        time_counter = [0]
        def mock_time():
            time_counter[0] += 1
            return float(time_counter[0])

        with patch("time.time", side_effect=mock_time):
            with patch.dict("sys.modules", {"pexpect": mock_pexpect}):
                response = await driver._collect_response(10.0)

        assert len(response.user_questions) == 1
        assert driver._state == DriverState.ASKING_USER

    @pytest.mark.asyncio
    async def test_collect_response_detects_errors(self):
        """Should detect error messages."""
        mock_pexpect = MagicMock()
        mock_process = MagicMock()
        mock_pexpect.TIMEOUT = type("TIMEOUT", (Exception,), {})
        mock_pexpect.EOF = type("EOF", (Exception,), {})

        expect_call_count = [0]
        def expect_side_effect(*args, **kwargs):
            expect_call_count[0] += 1
            if expect_call_count[0] == 1:
                mock_process.after = "Error: Something went wrong"
                return 0
            raise mock_pexpect.TIMEOUT()

        mock_process.expect.side_effect = expect_side_effect

        driver = ClaudeCodeDriver()
        driver._process = mock_process

        # Create incrementing time mock
        time_counter = [0]
        def mock_time():
            time_counter[0] += 1
            return float(time_counter[0])

        with patch("time.time", side_effect=mock_time):
            with patch.dict("sys.modules", {"pexpect": mock_pexpect}):
                response = await driver._collect_response(10.0)

        assert len(response.errors) == 1
        assert "Error" in response.errors[0]

    @pytest.mark.asyncio
    async def test_collect_response_handles_eof(self):
        """Should handle EOF (process ended)."""
        mock_pexpect = MagicMock()
        mock_process = MagicMock()
        mock_pexpect.TIMEOUT = type("TIMEOUT", (Exception,), {})
        mock_pexpect.EOF = type("EOF", (Exception,), {})

        mock_process.expect.side_effect = mock_pexpect.EOF()

        driver = ClaudeCodeDriver()
        driver._process = mock_process

        # Create incrementing time mock
        time_counter = [0]
        def mock_time():
            time_counter[0] += 1
            return float(time_counter[0])

        with patch("time.time", side_effect=mock_time):
            with patch.dict("sys.modules", {"pexpect": mock_pexpect}):
                response = await driver._collect_response(10.0)

        assert driver._state == DriverState.ERROR

    @pytest.mark.asyncio
    async def test_wait_for_ready_handles_startup(self):
        """Should drain startup messages."""
        mock_pexpect = MagicMock()
        mock_process = MagicMock()
        mock_pexpect.TIMEOUT = type("TIMEOUT", (Exception,), {})
        mock_pexpect.EOF = type("EOF", (Exception,), {})

        # First call returns data, second raises timeout
        expect_call_count = [0]
        def expect_side_effect(*args, **kwargs):
            expect_call_count[0] += 1
            if expect_call_count[0] == 1:
                return 0
            raise mock_pexpect.TIMEOUT()

        mock_process.expect.side_effect = expect_side_effect

        driver = ClaudeCodeDriver()
        driver._process = mock_process

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with patch.dict("sys.modules", {"pexpect": mock_pexpect}):
                await driver._wait_for_ready()

        # Should have called expect at least once
        assert mock_process.expect.called


class TestClaudeCodeTestRunner:
    """Tests for ClaudeCodeTestRunner class."""

    def test_init_default(self):
        """Should use cwd as default project root."""
        runner = ClaudeCodeTestRunner()
        assert runner.project_root == Path.cwd()
        assert runner.driver is None
        assert runner.results == []

    def test_init_custom_root(self):
        """Should accept custom project root."""
        runner = ClaudeCodeTestRunner(Path("/test/project"))
        assert runner.project_root == Path("/test/project")

    @pytest.mark.asyncio
    async def test_setup(self):
        """Should create and start driver."""
        runner = ClaudeCodeTestRunner()

        with patch.object(ClaudeCodeDriver, "start", new_callable=AsyncMock):
            await runner.setup()

        assert runner.driver is not None
        assert runner.driver.config.timeout == 180.0

    @pytest.mark.asyncio
    async def test_teardown(self):
        """Should close driver."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.close = AsyncMock()
        runner.driver = mock_driver

        await runner.teardown()

        mock_driver.close.assert_called_once()
        assert runner.driver is None

    @pytest.mark.asyncio
    async def test_teardown_no_driver(self):
        """Should handle teardown without driver."""
        runner = ClaudeCodeTestRunner()
        await runner.teardown()  # Should not raise

    @pytest.mark.asyncio
    async def test_test_skill_available_not_initialized(self):
        """Should raise if driver not initialized."""
        runner = ClaudeCodeTestRunner()
        with pytest.raises(RuntimeError, match="Driver not initialized"):
            await runner.test_skill_available("test")

    @pytest.mark.asyncio
    async def test_test_skill_available_found(self):
        """Should return True if skill found."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.send_prompt = AsyncMock(
            return_value=ClaudeResponse(text="Available skills: beyond-ralph, other", duration_ms=0)
        )
        runner.driver = mock_driver

        result = await runner.test_skill_available("beyond-ralph")
        assert result is True

    @pytest.mark.asyncio
    async def test_test_skill_available_not_found(self):
        """Should return False if skill not found."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.send_prompt = AsyncMock(
            return_value=ClaudeResponse(text="Available skills: other", duration_ms=0)
        )
        runner.driver = mock_driver

        result = await runner.test_skill_available("beyond-ralph")
        assert result is False

    @pytest.mark.asyncio
    async def test_test_beyond_ralph_status_not_initialized(self):
        """Should raise if driver not initialized."""
        runner = ClaudeCodeTestRunner()
        with pytest.raises(RuntimeError, match="Driver not initialized"):
            await runner.test_beyond_ralph_status()

    @pytest.mark.asyncio
    async def test_test_beyond_ralph_status_success(self):
        """Should test status command successfully."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.execute_skill = AsyncMock(
            return_value=ClaudeResponse(text="Project status: idle", duration_ms=100, errors=[])
        )
        runner.driver = mock_driver

        result = await runner.test_beyond_ralph_status()

        assert result["test"] == "beyond_ralph_status"
        assert result["passed"] is True
        assert result["response"] == "Project status: idle"
        assert len(runner.results) == 1

    @pytest.mark.asyncio
    async def test_test_beyond_ralph_status_error(self):
        """Should handle status command errors."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.execute_skill = AsyncMock(side_effect=Exception("Connection failed"))
        runner.driver = mock_driver

        result = await runner.test_beyond_ralph_status()

        assert result["passed"] is False
        assert result["error"] == "Connection failed"

    @pytest.mark.asyncio
    async def test_test_beyond_ralph_start_not_initialized(self):
        """Should raise if driver not initialized."""
        runner = ClaudeCodeTestRunner()
        with pytest.raises(RuntimeError, match="Driver not initialized"):
            await runner.test_beyond_ralph_start(Path("/test/spec.md"))

    @pytest.mark.asyncio
    async def test_test_beyond_ralph_start_success(self):
        """Should test start command successfully."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.execute_skill = AsyncMock(
            return_value=ClaudeResponse(
                text="Project complete",
                duration_ms=1000,
                agent_outputs=[("impl-1", "Done")],
                errors=[],
                raw_output="Phase 1: spec\nPhase 2: interview\nPhase 8: done",
            )
        )
        runner.driver = mock_driver

        result = await runner.test_beyond_ralph_start(Path("/test/spec.md"))

        assert result["test"] == "beyond_ralph_start"
        assert result["passed"] is True
        assert "1" in result["phases_completed"]
        assert "2" in result["phases_completed"]
        assert "8" in result["phases_completed"]

    @pytest.mark.asyncio
    async def test_test_beyond_ralph_start_error(self):
        """Should handle start command errors."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.execute_skill = AsyncMock(side_effect=Exception("Timeout"))
        runner.driver = mock_driver

        result = await runner.test_beyond_ralph_start(Path("/test/spec.md"))

        assert result["passed"] is False
        assert result["error"] == "Timeout"

    @pytest.mark.asyncio
    async def test_test_subagent_streaming_not_initialized(self):
        """Should raise if driver not initialized."""
        runner = ClaudeCodeTestRunner()
        with pytest.raises(RuntimeError, match="Driver not initialized"):
            await runner.test_subagent_streaming()

    @pytest.mark.asyncio
    async def test_test_subagent_streaming_success(self):
        """Should detect subagent outputs."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.send_prompt = AsyncMock(
            return_value=ClaudeResponse(
                text="Done",
                duration_ms=100,
                agent_outputs=[("agent-1", "Hello")],
            )
        )
        runner.driver = mock_driver

        result = await runner.test_subagent_streaming()

        assert result["passed"] is True
        assert len(result["agent_outputs"]) == 1

    @pytest.mark.asyncio
    async def test_test_subagent_streaming_no_outputs(self):
        """Should fail if no subagent outputs detected."""
        runner = ClaudeCodeTestRunner()
        mock_driver = MagicMock()
        mock_driver.send_prompt = AsyncMock(
            return_value=ClaudeResponse(text="Done", duration_ms=100, agent_outputs=[])
        )
        runner.driver = mock_driver

        result = await runner.test_subagent_streaming()

        assert result["passed"] is False

    def test_get_summary_empty(self):
        """Should handle empty results."""
        runner = ClaudeCodeTestRunner()
        summary = runner.get_summary()

        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["pass_rate"] == 0

    def test_get_summary_with_results(self):
        """Should calculate summary correctly."""
        runner = ClaudeCodeTestRunner()
        runner.results = [
            {"passed": True},
            {"passed": True},
            {"passed": False},
        ]

        summary = runner.get_summary()

        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["pass_rate"] == 2/3


class TestRunPromptOnce:
    """Tests for run_prompt_once function."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Should run prompt successfully."""
        mock_result = MagicMock()
        mock_result.stdout = "Hello, world!"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            response = await run_prompt_once("Say hello")

        assert response.text == "Hello, world!"
        assert response.duration_ms > 0
        assert len(response.errors) == 0

    @pytest.mark.asyncio
    async def test_with_working_dir(self):
        """Should pass working directory."""
        mock_result = MagicMock()
        mock_result.stdout = "OK"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            await run_prompt_once("Test", working_dir=Path("/test"))

        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == "/test"

    @pytest.mark.asyncio
    async def test_without_skip_permissions(self):
        """Should omit skip-permissions flag when disabled."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            await run_prompt_once("Test", dangerously_skip_permissions=False)

        cmd = mock_run.call_args[0][0]
        assert "--dangerously-skip-permissions" not in cmd

    @pytest.mark.asyncio
    async def test_with_errors(self):
        """Should capture stderr and non-zero exit code."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "Error occurred"
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            response = await run_prompt_once("Fail")

        assert len(response.errors) == 2
        assert "Error occurred" in response.errors
        assert "Exit code: 1" in response.errors

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Should handle timeout."""
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 60)):
            response = await run_prompt_once("Slow command", timeout=60)

        assert "Timeout expired" in response.errors

    @pytest.mark.asyncio
    async def test_exception(self):
        """Should handle other exceptions."""
        with patch("subprocess.run", side_effect=Exception("Unknown error")):
            response = await run_prompt_once("Bad command")

        assert "Unknown error" in response.errors


class TestRunLiveTests:
    """Tests for run_live_tests function."""

    @pytest.mark.asyncio
    async def test_success_with_spec(self):
        """Should run all tests successfully."""
        mock_runner = MagicMock()
        mock_runner.setup = AsyncMock()
        mock_runner.teardown = AsyncMock()
        mock_runner.test_skill_available = AsyncMock(return_value=True)
        mock_runner.test_beyond_ralph_status = AsyncMock(
            return_value={"passed": True}
        )
        mock_runner.test_beyond_ralph_start = AsyncMock(
            return_value={"passed": True, "phases_completed": ["1", "8"]}
        )
        mock_runner.get_summary = MagicMock(
            return_value={"total": 2, "passed": 2, "failed": 0}
        )

        with patch("beyond_ralph.testing.claude_driver.ClaudeCodeTestRunner", return_value=mock_runner):
            with patch("builtins.print"):
                # Create a temp spec file
                with patch.object(Path, "exists", return_value=True):
                    summary = await run_live_tests(Path("/test/project"))

        assert summary["passed"] == 2
        mock_runner.teardown.assert_called_once()

    @pytest.mark.asyncio
    async def test_without_spec(self):
        """Should skip start test if no spec found."""
        mock_runner = MagicMock()
        mock_runner.setup = AsyncMock()
        mock_runner.teardown = AsyncMock()
        mock_runner.test_skill_available = AsyncMock(return_value=True)
        mock_runner.test_beyond_ralph_status = AsyncMock(
            return_value={"passed": True}
        )
        mock_runner.get_summary = MagicMock(
            return_value={"total": 1, "passed": 1, "failed": 0}
        )

        with patch("beyond_ralph.testing.claude_driver.ClaudeCodeTestRunner", return_value=mock_runner):
            with patch("builtins.print"):
                summary = await run_live_tests(None)

        mock_runner.test_beyond_ralph_start.assert_not_called()

    @pytest.mark.asyncio
    async def test_teardown_on_error(self):
        """Should teardown even on error."""
        mock_runner = MagicMock()
        mock_runner.setup = AsyncMock(side_effect=Exception("Setup failed"))
        mock_runner.teardown = AsyncMock()

        with patch("beyond_ralph.testing.claude_driver.ClaudeCodeTestRunner", return_value=mock_runner):
            with patch("builtins.print"):
                with pytest.raises(Exception, match="Setup failed"):
                    await run_live_tests(Path("/test"))

        mock_runner.teardown.assert_called_once()


class TestMain:
    """Tests for main CLI function."""

    def test_default_arguments(self):
        """Should use default arguments."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = MagicMock(
                project_root=Path.cwd(),
                verbose=False,
            )
            with patch("asyncio.run") as mock_run:
                mock_run.return_value = {"total": 1, "passed": 1, "failed": 0}
                with patch("logging.basicConfig"):
                    main()

                mock_run.assert_called_once()

    def test_verbose_mode(self):
        """Should enable debug logging in verbose mode."""
        import logging

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = MagicMock(
                project_root=Path.cwd(),
                verbose=True,
            )
            with patch("asyncio.run") as mock_run:
                mock_run.return_value = {"total": 1, "passed": 1, "failed": 0}
                with patch("logging.basicConfig") as mock_logging:
                    main()

                mock_logging.assert_called_with(level=logging.DEBUG)

    def test_exit_on_failure(self):
        """Should exit with code 1 on test failure."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = MagicMock(
                project_root=Path.cwd(),
                verbose=False,
            )
            with patch("asyncio.run") as mock_run:
                mock_run.return_value = {"total": 2, "passed": 1, "failed": 1}
                with patch("logging.basicConfig"):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1


class TestPatterns:
    """Tests for regex patterns used in the driver."""

    def test_ansi_pattern(self):
        """ANSI pattern should match various escape codes."""
        import re
        pattern = ClaudeCodeDriver.ANSI_PATTERN

        # Color codes
        assert pattern.search("\x1b[31m")
        assert pattern.search("\x1b[0m")
        assert pattern.search("\x1b[1;32m")

        # Cursor codes
        assert pattern.search("\x1b[?25l")
        assert pattern.search("\x1b[?25h")

        # OSC sequences
        assert pattern.search("\x1b]0;title\x07")

    def test_agent_output_pattern(self):
        """Agent output pattern should match [AGENT:id] format."""
        import re
        pattern = ClaudeCodeDriver.AGENT_OUTPUT_PATTERN

        match = re.search(pattern, "[AGENT:test-123] Hello world")
        assert match
        assert match.group(1) == "test-123"
        assert match.group(2) == "Hello world"

        # Should match alphanumeric and hyphens
        match = re.search(pattern, "[AGENT:ABC-xyz-123] Message")
        assert match
        assert match.group(1) == "ABC-xyz-123"

    def test_user_question_pattern(self):
        """User question pattern should match various prompts."""
        import re
        pattern = ClaudeCodeDriver.USER_QUESTION_PATTERN

        assert re.search(pattern, "[USER INPUT REQUIRED]")
        assert re.search(pattern, "Using AskUserQuestion tool")
        assert re.search(pattern, "Select an option:")

    def test_error_pattern(self):
        """Error pattern should match error messages."""
        import re
        pattern = ClaudeCodeDriver.ERROR_PATTERN

        assert re.search(pattern, "Error: Something went wrong")
        assert re.search(pattern, "ERROR: Critical failure")
        assert re.search(pattern, "Exception: ValueError")
        assert re.search(pattern, "Traceback (most recent call last):")
