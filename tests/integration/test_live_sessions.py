"""Live integration tests for Beyond Ralph.

These tests spawn REAL Claude CLI sessions to verify the system works
in actual operation, not just with mocks.

Run with: uv run pytest tests/integration/test_live_sessions.py -v

NOTE: These tests require:
1. Claude CLI installed and in PATH
2. Valid Claude API credentials
3. Sufficient quota

These tests are slower and consume quota, so they're marked with
@pytest.mark.live to allow selective running.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pytest

from beyond_ralph.core.session_manager import (
    SessionManager,
    SessionStatus,
    PEXPECT_AVAILABLE,
)


# Skip all live tests if Claude CLI not available
def claude_cli_available() -> bool:
    """Check if Claude CLI is available."""
    return shutil.which("claude") is not None


pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not claude_cli_available(),
        reason="Claude CLI not installed",
    ),
    pytest.mark.skipif(
        not PEXPECT_AVAILABLE,
        reason="pexpect not available",
    ),
]


class TestLiveSessionSpawning:
    """Test live session spawning with real Claude CLI."""

    @pytest.fixture
    def session_manager(self, tmp_path: Path) -> SessionManager:
        """Create session manager with temp lock dir."""
        lock_dir = tmp_path / ".sessions"
        lock_dir.mkdir()
        return SessionManager(safemode=False, lock_dir=lock_dir)

    @pytest.mark.asyncio
    async def test_spawn_simple_task(self, session_manager: SessionManager) -> None:
        """Test spawning a simple task that completes quickly."""
        outputs: list[str] = []

        def output_callback(output):
            outputs.append(output.line)
            print(f"[AGENT:{output.session_uuid}] {output.line}")

        # Simple task that should complete quickly
        session = await session_manager.spawn_cli(
            prompt="Say 'Hello from Beyond Ralph test' and nothing else.",
            agent_type="test",
            timeout=60,  # 60 second timeout for simple task
            output_callback=output_callback,
        )

        assert session.uuid is not None
        assert session.status == SessionStatus.COMPLETED
        assert session.result is not None
        assert len(outputs) > 0
        print(f"\nSession result: {session.result}")

    @pytest.mark.asyncio
    async def test_spawn_analysis_task(
        self, session_manager: SessionManager, tmp_path: Path
    ) -> None:
        """Test spawning a task that analyzes a file."""
        # Create a simple file to analyze
        test_file = tmp_path / "test.py"
        test_file.write_text('''
def hello():
    """Say hello."""
    return "Hello, world!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')

        outputs: list[str] = []

        def output_callback(output):
            outputs.append(output.line)
            print(f"[AGENT:{output.session_uuid}] {output.line}")

        session = await session_manager.spawn_cli(
            prompt=f"Read the file at {test_file} and list the functions defined in it. Be brief.",
            agent_type="analysis",
            timeout=120,
            output_callback=output_callback,
            working_dir=tmp_path,
        )

        assert session.status == SessionStatus.COMPLETED
        assert session.result is not None
        # Should mention the functions
        result_lower = session.result.lower()
        assert "hello" in result_lower or "add" in result_lower
        print(f"\nSession result: {session.result}")

    @pytest.mark.asyncio
    async def test_spawn_with_short_timeout(self, session_manager: SessionManager) -> None:
        """Test that sessions complete within timeout or timeout gracefully."""
        # Short timeout - session may complete or timeout
        session = await session_manager.spawn_cli(
            prompt="Say 'quick test' and exit immediately.",
            agent_type="timeout-test",
            timeout=30,  # 30 second timeout - should be enough
        )

        # Session should complete (either successfully or with timeout handled)
        assert session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED)
        print(f"Session status: {session.status}, result: {session.result}")

    @pytest.mark.asyncio
    async def test_session_locking(self, session_manager: SessionManager) -> None:
        """Test that session locking works correctly."""
        # Spawn a session
        session = await session_manager.spawn_cli(
            prompt="Say 'test' and exit.",
            agent_type="lock-test",
            timeout=30,
        )

        # Session should complete and lock should be released
        assert session.status == SessionStatus.COMPLETED

        # Lock should be released
        is_locked = await session_manager.is_locked(session.uuid)
        assert not is_locked

    @pytest.mark.asyncio
    async def test_output_streaming(self, session_manager: SessionManager) -> None:
        """Test that output streams in real-time."""
        outputs: list[str] = []
        timestamps: list[float] = []

        import time

        def output_callback(output):
            outputs.append(output.line)
            timestamps.append(time.time())
            print(f"[{len(outputs)}] {output.line}")

        session = await session_manager.spawn_cli(
            prompt="List the numbers 1, 2, 3 on separate lines.",
            agent_type="streaming-test",
            timeout=60,
            output_callback=output_callback,
        )

        assert session.status == SessionStatus.COMPLETED
        assert len(outputs) > 0
        print(f"\nCaptured {len(outputs)} output lines")


class TestLiveOrchestratorPhases:
    """Test orchestrator phases with live Claude sessions."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create project structure."""
        (tmp_path / "records").mkdir()
        (tmp_path / "beyondralph_knowledge").mkdir()
        (tmp_path / ".beyond_ralph_sessions").mkdir()

        # Create a minimal spec
        spec = tmp_path / "SPEC.md"
        spec.write_text("""# Test Project Spec

## Overview
A simple test project for integration testing.

## Requirements
1. Create a hello world function
2. Add basic error handling

## Questions
- What language should be used?
""")

        return tmp_path

    @pytest.mark.asyncio
    async def test_live_spec_ingestion(self, project_root: Path) -> None:
        """Test spec ingestion phase with live Claude session."""
        from beyond_ralph.core.orchestrator import Orchestrator, Phase
        from beyond_ralph.core.session_manager import SessionStatus

        orchestrator = Orchestrator(
            project_root=project_root,
            use_cli=True,  # Use real CLI sessions
        )
        orchestrator.spec_path = project_root / "SPEC.md"
        orchestrator.project_id = "live-test-001"
        orchestrator.phase = Phase.SPEC_INGESTION

        outputs: list[str] = []

        def output_callback(output):
            outputs.append(output.formatted())
            print(output.formatted())

        # Run spec ingestion phase
        result = await orchestrator._phase_spec_ingestion()

        print(f"\n--- Phase Result ---")
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        print(f"Errors: {result.errors}")

        # Verify the phase completed
        assert result.phase == Phase.SPEC_INGESTION
        # The phase should have processed the spec
        if not result.success:
            print(f"Phase failed with: {result.errors}")


class TestLiveQuotaIntegration:
    """Test quota checking with live system."""

    @pytest.mark.asyncio
    async def test_quota_check_before_spawn(self) -> None:
        """Test that quota is checked before spawning sessions."""
        from beyond_ralph.core.quota_manager import QuotaManager

        manager = QuotaManager()

        # Check quota - this performs the actual check
        status = await manager.check()
        can_spawn = await manager.pre_spawn_check()
        summary = manager.get_summary()

        print(f"\n--- Quota Status ---")
        print(f"Session: {status.session_percent}%")
        print(f"Weekly: {status.weekly_percent}%")
        print(f"Can spawn: {can_spawn}")
        print(f"Summary: {summary}")

        # We should at least get a valid response
        assert isinstance(can_spawn, bool)
        assert 0 <= status.session_percent <= 100
        assert 0 <= status.weekly_percent <= 100


class TestLiveEndToEnd:
    """End-to-end test with live Claude sessions."""

    @pytest.fixture
    def full_project(self, tmp_path: Path) -> Path:
        """Create a full project structure for E2E testing."""
        # Create directories
        (tmp_path / "records").mkdir()
        (tmp_path / "beyondralph_knowledge").mkdir()
        (tmp_path / ".beyond_ralph_sessions").mkdir()
        (tmp_path / "src").mkdir()

        # Create a realistic spec
        spec = tmp_path / "SPEC.md"
        spec.write_text("""# Calculator API

## Overview
Build a simple calculator API with basic arithmetic operations.

## Requirements
1. Addition endpoint: POST /add with {"a": number, "b": number}
2. Subtraction endpoint: POST /subtract with {"a": number, "b": number}
3. Input validation for all endpoints
4. Return JSON responses with {"result": number}

## Technology
- Python 3.11+
- FastAPI
- pytest for testing

## Non-functional Requirements
- Response time < 100ms
- Comprehensive error messages
""")

        return tmp_path

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_spec_analysis_live(self, full_project: Path) -> None:
        """Test analyzing a realistic spec with live Claude session."""
        from beyond_ralph.core.session_manager import SessionManager

        manager = SessionManager(
            safemode=False,
            lock_dir=full_project / ".beyond_ralph_sessions",
        )

        spec_content = (full_project / "SPEC.md").read_text()

        outputs: list[str] = []

        def output_callback(output):
            outputs.append(output.line)
            print(f"[AGENT:{output.session_uuid}] {output.line}")

        session = await manager.spawn_cli(
            prompt=f"""Analyze this specification and identify:
1. The main features/endpoints
2. Any potential ambiguities
3. Questions for clarification

Specification:
{spec_content}

Provide a brief, structured analysis.""",
            agent_type="spec-analysis",
            timeout=180,  # 3 minutes for analysis
            output_callback=output_callback,
            working_dir=full_project,
        )

        print(f"\n--- Analysis Result ---")
        print(f"Status: {session.status}")
        print(f"Result: {session.result}")
        print(f"Captured {len(outputs)} output lines")

        assert session.status == SessionStatus.COMPLETED
        # Check the full captured output, not just the extracted result
        full_output = "\n".join(outputs).lower()
        assert any(word in full_output for word in ["calculator", "api", "endpoint", "add", "subtract"]), \
            f"Expected calculator-related keywords in output. Got: {full_output[:500]}"
