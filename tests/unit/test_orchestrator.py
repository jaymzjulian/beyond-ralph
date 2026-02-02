"""Unit tests for Core Orchestrator."""

from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.orchestrator import (
    Orchestrator,
    OrchestratorState,
    Phase,
    PhaseResult,
    ProjectStatus,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create required directories
    (project / "records").mkdir()
    (project / "beyondralph_knowledge").mkdir()

    # Create a spec file
    spec_file = project / "SPEC.md"
    spec_file.write_text("# Test Specification\n\nThis is a test spec.")

    return project


@pytest.fixture
def orchestrator(temp_project: Path) -> Orchestrator:
    """Create an orchestrator with temp project."""
    return Orchestrator(project_root=temp_project)


class TestPhase:
    """Tests for Phase enum."""

    def test_phase_values(self) -> None:
        """Test all phases are defined."""
        assert Phase.IDLE.value == "idle"
        assert Phase.SPEC_INGESTION.value == "spec_ingestion"
        assert Phase.INTERVIEW.value == "interview"
        assert Phase.IMPLEMENTATION.value == "implementation"
        assert Phase.COMPLETE.value == "complete"


class TestOrchestratorState:
    """Tests for OrchestratorState enum."""

    def test_state_values(self) -> None:
        """Test all states are defined."""
        assert OrchestratorState.STOPPED.value == "stopped"
        assert OrchestratorState.RUNNING.value == "running"
        assert OrchestratorState.PAUSED.value == "paused"
        assert OrchestratorState.WAITING_FOR_USER.value == "waiting_for_user"


class TestProjectStatus:
    """Tests for ProjectStatus dataclass."""

    def test_to_dict(self) -> None:
        """Test converting status to dict."""
        status = ProjectStatus(
            project_id="test-123",
            phase=Phase.IMPLEMENTATION,
            state=OrchestratorState.RUNNING,
            progress_percent=50.0,
            current_task="Implement feature X",
            active_agents=2,
            tasks_complete=5,
            tasks_total=10,
            last_activity=datetime(2024, 2, 1, 10, 0),
        )

        data = status.to_dict()

        assert data["project_id"] == "test-123"
        assert data["phase"] == "implementation"
        assert data["state"] == "running"
        assert data["progress_percent"] == 50.0
        assert data["active_agents"] == 2


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_successful_result(self) -> None:
        """Test successful phase result."""
        result = PhaseResult(
            success=True,
            phase=Phase.SPEC_INGESTION,
            message="Spec ingested",
            next_phase=Phase.INTERVIEW,
        )

        assert result.success
        assert result.next_phase == Phase.INTERVIEW
        assert not result.should_loop

    def test_loop_result(self) -> None:
        """Test result that loops back."""
        result = PhaseResult(
            success=True,
            phase=Phase.REVIEW,
            message="Uncertainties found",
            should_loop=True,
            loop_to_phase=Phase.INTERVIEW,
        )

        assert result.success
        assert result.should_loop
        assert result.loop_to_phase == Phase.INTERVIEW


class TestOrchestrator:
    """Tests for Orchestrator class."""

    def test_initialization(self, orchestrator: Orchestrator) -> None:
        """Test orchestrator initializes correctly."""
        assert orchestrator.phase == Phase.IDLE
        assert orchestrator.state == OrchestratorState.STOPPED
        assert orchestrator.project_id is None
        assert orchestrator.max_parallel_agents == 7

    def test_generate_project_id(self, orchestrator: Orchestrator) -> None:
        """Test project ID generation."""
        project_id = orchestrator._generate_project_id()

        assert project_id.startswith("br-")
        assert len(project_id) == 11  # br- + 8 hex chars

    def test_get_next_phase(self, orchestrator: Orchestrator) -> None:
        """Test phase progression."""
        orchestrator.phase = Phase.SPEC_INGESTION
        assert orchestrator._get_next_phase() == Phase.INTERVIEW

        orchestrator.phase = Phase.INTERVIEW
        assert orchestrator._get_next_phase() == Phase.SPEC_CREATION

        orchestrator.phase = Phase.TESTING
        assert orchestrator._get_next_phase() == Phase.COMPLETE

    @pytest.mark.asyncio
    async def test_status(self, orchestrator: Orchestrator) -> None:
        """Test getting status."""
        orchestrator.project_id = "test-project"
        orchestrator.phase = Phase.IMPLEMENTATION

        status = await orchestrator.status()

        assert status.project_id == "test-project"
        assert status.phase == Phase.IMPLEMENTATION
        assert status.state == OrchestratorState.STOPPED

    @pytest.mark.asyncio
    async def test_save_and_restore_state(
        self, orchestrator: Orchestrator, temp_project: Path
    ) -> None:
        """Test state persistence."""
        orchestrator.project_id = "test-123"
        orchestrator.phase = Phase.PLANNING
        orchestrator.state = OrchestratorState.PAUSED

        await orchestrator._save_state()

        # Create new orchestrator and restore
        new_orch = Orchestrator(project_root=temp_project)
        await new_orch._restore_state("test-123")

        assert new_orch.project_id == "test-123"
        assert new_orch.phase == Phase.PLANNING
        assert new_orch.state == OrchestratorState.PAUSED

    @pytest.mark.asyncio
    async def test_pause(self, orchestrator: Orchestrator) -> None:
        """Test pausing the orchestrator."""
        orchestrator.state = OrchestratorState.RUNNING

        await orchestrator.pause()

        assert orchestrator.state == OrchestratorState.PAUSED

    @pytest.mark.asyncio
    async def test_phase_spec_ingestion(
        self, orchestrator: Orchestrator, temp_project: Path
    ) -> None:
        """Test spec ingestion phase."""
        orchestrator.spec_path = temp_project / "SPEC.md"
        orchestrator.project_id = "test-123"

        result = await orchestrator._phase_spec_ingestion()

        assert result.success
        assert result.phase == Phase.SPEC_INGESTION
        assert result.next_phase == Phase.INTERVIEW

    @pytest.mark.asyncio
    async def test_phase_spec_ingestion_missing_file(
        self, orchestrator: Orchestrator
    ) -> None:
        """Test spec ingestion with missing file."""
        orchestrator.spec_path = Path("/nonexistent/file.md")

        result = await orchestrator._phase_spec_ingestion()

        assert not result.success
        assert "not found" in result.message


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator."""

    @pytest.mark.asyncio
    async def test_on_compaction(
        self, orchestrator: Orchestrator, temp_project: Path
    ) -> None:
        """Test compaction recovery protocol."""
        orchestrator.project_id = "test-123"

        # Create some project structure
        (temp_project / "PROJECT_PLAN.md").write_text("# Project Plan\n\nTest plan.")
        module_dir = temp_project / "records" / "test-module"
        module_dir.mkdir()
        (module_dir / "spec.md").write_text("# Test Module Spec")

        # Should not raise
        await orchestrator.on_compaction()
