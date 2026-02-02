"""Core Orchestrator for Beyond Ralph.

The main control loop that implements the Spec and Interview Coder methodology.
Manages phases, agent coordination, and project completion.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from beyond_ralph.core.knowledge import KnowledgeBase, create_knowledge_entry
from beyond_ralph.core.quota_manager import QuotaManager, get_quota_manager
from beyond_ralph.core.records import Checkbox, RecordsManager
from beyond_ralph.core.session_manager import SessionManager, SessionStatus, get_session_manager

logger = logging.getLogger(__name__)


class Phase(Enum):
    """Project phases in the Spec and Interview Coder methodology."""

    IDLE = "idle"
    SPEC_INGESTION = "spec_ingestion"  # Phase 1
    INTERVIEW = "interview"  # Phase 2
    SPEC_CREATION = "spec_creation"  # Phase 3
    PLANNING = "planning"  # Phase 4
    REVIEW = "review"  # Phase 5
    VALIDATION = "validation"  # Phase 6
    IMPLEMENTATION = "implementation"  # Phase 7
    TESTING = "testing"  # Phase 8
    COMPLETE = "complete"
    PAUSED = "paused"
    FAILED = "failed"


class OrchestratorState(Enum):
    """Orchestrator operational state."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_FOR_USER = "waiting_for_user"


@dataclass
class ProjectStatus:
    """Current project status."""

    project_id: str
    phase: Phase
    state: OrchestratorState
    progress_percent: float
    current_task: str | None
    active_agents: int
    tasks_complete: int
    tasks_total: int
    last_activity: datetime
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_id": self.project_id,
            "phase": self.phase.value,
            "state": self.state.value,
            "progress_percent": self.progress_percent,
            "current_task": self.current_task,
            "active_agents": self.active_agents,
            "tasks_complete": self.tasks_complete,
            "tasks_total": self.tasks_total,
            "last_activity": self.last_activity.isoformat(),
            "errors": self.errors,
        }


@dataclass
class PhaseResult:
    """Result from a phase execution."""

    success: bool
    phase: Phase
    message: str
    next_phase: Phase | None = None
    should_loop: bool = False
    loop_to_phase: Phase | None = None
    errors: list[str] = field(default_factory=list)
    knowledge_entries: list[str] = field(default_factory=list)


class Orchestrator:
    """Main orchestrator for Beyond Ralph.

    Implements the Spec and Interview Coder methodology with:
    - Phase management (8 phases)
    - Agent coordination (spawn, monitor, collect results)
    - Quota-aware pausing
    - Context-efficient delegation
    - Compaction recovery
    """

    def __init__(
        self,
        project_root: Path | None = None,
        safemode: bool = False,
        max_parallel_agents: int = 7,
    ):
        """Initialize orchestrator.

        Args:
            project_root: Root directory for the project.
            safemode: If True, require permissions for dangerous operations.
            max_parallel_agents: Maximum concurrent agents (Claude Code limit is 7).
        """
        self.project_root = project_root or Path.cwd()
        self.safemode = safemode
        self.max_parallel_agents = max_parallel_agents

        # Core components
        self.session_manager = get_session_manager(safemode=safemode)
        self.quota_manager = get_quota_manager()
        self.knowledge_base = KnowledgeBase()
        self.records_manager = RecordsManager()

        # State
        self.project_id: str | None = None
        self.phase = Phase.IDLE
        self.state = OrchestratorState.STOPPED
        self.spec_path: Path | None = None
        self._last_activity = datetime.now()
        self._errors: list[str] = []

        # Phase transition map
        self._phase_order = [
            Phase.SPEC_INGESTION,
            Phase.INTERVIEW,
            Phase.SPEC_CREATION,
            Phase.PLANNING,
            Phase.REVIEW,
            Phase.VALIDATION,
            Phase.IMPLEMENTATION,
            Phase.TESTING,
            Phase.COMPLETE,
        ]

    async def start(self, spec_path: Path) -> None:
        """Start autonomous development from specification.

        Args:
            spec_path: Path to the specification file.
        """
        logger.info("Starting Beyond Ralph with spec: %s", spec_path)

        if not spec_path.exists():
            raise FileNotFoundError(f"Specification not found: {spec_path}")

        self.spec_path = spec_path
        self.project_id = self._generate_project_id()
        self.state = OrchestratorState.RUNNING
        self.phase = Phase.SPEC_INGESTION

        # Log start to knowledge base
        await self._log_to_knowledge(
            title="Project Started",
            content=f"Started autonomous development from {spec_path}",
            category="orchestrator",
        )

        # Main loop
        await self._run_loop()

    async def resume(self, project_id: str | None = None) -> None:
        """Resume an interrupted project.

        Args:
            project_id: Optional specific project to resume.
        """
        logger.info("Resuming Beyond Ralph project: %s", project_id or "most recent")

        # Restore state from records
        await self._restore_state(project_id)

        if self.state == OrchestratorState.PAUSED:
            self.state = OrchestratorState.RUNNING
            await self._run_loop()

    async def pause(self) -> None:
        """Manually pause operations."""
        logger.info("Pausing Beyond Ralph")
        self.state = OrchestratorState.PAUSED
        await self._save_state()

    async def status(self) -> ProjectStatus:
        """Get current project status."""
        progress = self.records_manager.get_progress_summary()

        return ProjectStatus(
            project_id=self.project_id or "none",
            phase=self.phase,
            state=self.state,
            progress_percent=progress.get("percent_complete", 0),
            current_task=self._get_current_task(),
            active_agents=self.session_manager.count_active(),
            tasks_complete=progress.get("complete_tasks", 0),
            tasks_total=progress.get("total_tasks", 0),
            last_activity=self._last_activity,
            errors=self._errors[-5:],  # Last 5 errors
        )

    async def on_compaction(self) -> None:
        """Recovery protocol after context compaction.

        CRITICAL: Must re-read all state after compaction.
        """
        logger.warning("Compaction detected - executing recovery protocol")

        # Re-read PROJECT_PLAN.md
        plan_path = self.project_root / "PROJECT_PLAN.md"
        if plan_path.exists():
            logger.info("Re-reading PROJECT_PLAN.md")
            # The content is available for the orchestrator's context

        # Re-read current module specs
        for module_dir in (self.project_root / "records").iterdir():
            if module_dir.is_dir():
                spec_file = module_dir / "spec.md"
                if spec_file.exists():
                    logger.info("Re-reading spec for module: %s", module_dir.name)

        # Re-read task status
        incomplete = self.records_manager.get_incomplete_tasks()
        logger.info("Found %d incomplete tasks after compaction", len(incomplete))

        # Check recent knowledge
        recent = self.knowledge_base.list_recent(hours=24)
        logger.info("Found %d recent knowledge entries", len(recent))

        await self._log_to_knowledge(
            title="Compaction Recovery",
            content=f"Recovered after compaction. Found {len(incomplete)} incomplete tasks.",
            category="orchestrator",
        )

    # === Private Methods ===

    def _generate_project_id(self) -> str:
        """Generate a unique project ID."""
        import uuid
        return f"br-{uuid.uuid4().hex[:8]}"

    async def _run_loop(self) -> None:
        """Main orchestration loop."""
        while self.state == OrchestratorState.RUNNING:
            # Check quota before any work
            if not await self.quota_manager.pre_spawn_check():
                logger.warning("Quota limit reached - pausing")
                self.state = OrchestratorState.PAUSED
                await self.quota_manager.wait_for_reset()
                self.state = OrchestratorState.RUNNING
                continue

            # Execute current phase
            result = await self._execute_phase()

            if not result.success:
                self._errors.append(result.message)
                if len(result.errors) > 3:
                    logger.error("Too many errors in phase %s - failing", self.phase)
                    self.phase = Phase.FAILED
                    break

            # Handle phase transition
            if result.should_loop and result.loop_to_phase:
                logger.info("Looping back to phase: %s", result.loop_to_phase)
                self.phase = result.loop_to_phase
            elif result.next_phase:
                logger.info("Transitioning to phase: %s", result.next_phase)
                self.phase = result.next_phase
            else:
                # Move to next phase in order
                self.phase = self._get_next_phase()

            self._last_activity = datetime.now()

            # Check if complete
            if self.phase == Phase.COMPLETE:
                logger.info("Project complete!")
                break

            # Save state periodically
            await self._save_state()

    async def _execute_phase(self) -> PhaseResult:
        """Execute the current phase.

        Returns:
            PhaseResult with outcome and next steps.
        """
        logger.info("Executing phase: %s", self.phase)

        handlers = {
            Phase.SPEC_INGESTION: self._phase_spec_ingestion,
            Phase.INTERVIEW: self._phase_interview,
            Phase.SPEC_CREATION: self._phase_spec_creation,
            Phase.PLANNING: self._phase_planning,
            Phase.REVIEW: self._phase_review,
            Phase.VALIDATION: self._phase_validation,
            Phase.IMPLEMENTATION: self._phase_implementation,
            Phase.TESTING: self._phase_testing,
        }

        handler = handlers.get(self.phase)
        if not handler:
            return PhaseResult(
                success=False,
                phase=self.phase,
                message=f"No handler for phase: {self.phase}",
            )

        try:
            return await handler()
        except Exception as e:
            logger.exception("Error in phase %s: %s", self.phase, e)
            return PhaseResult(
                success=False,
                phase=self.phase,
                message=str(e),
                errors=[str(e)],
            )

    def _get_next_phase(self) -> Phase:
        """Get the next phase in order."""
        try:
            idx = self._phase_order.index(self.phase)
            if idx < len(self._phase_order) - 1:
                return self._phase_order[idx + 1]
        except ValueError:
            pass
        return Phase.COMPLETE

    def _get_current_task(self) -> str | None:
        """Get description of current task."""
        incomplete = self.records_manager.get_incomplete_tasks()
        if incomplete:
            return incomplete[0].name
        return None

    async def _save_state(self) -> None:
        """Save orchestrator state to disk."""
        state_file = self.project_root / ".beyond_ralph_state"
        import json
        state = {
            "project_id": self.project_id,
            "phase": self.phase.value,
            "state": self.state.value,
            "spec_path": str(self.spec_path) if self.spec_path else None,
            "last_activity": self._last_activity.isoformat(),
        }
        state_file.write_text(json.dumps(state, indent=2))

    async def _restore_state(self, project_id: str | None) -> None:
        """Restore orchestrator state from disk."""
        state_file = self.project_root / ".beyond_ralph_state"
        if state_file.exists():
            import json
            state = json.loads(state_file.read_text())
            if project_id is None or state.get("project_id") == project_id:
                self.project_id = state.get("project_id")
                self.phase = Phase(state.get("phase", "idle"))
                self.state = OrchestratorState(state.get("state", "stopped"))
                if state.get("spec_path"):
                    self.spec_path = Path(state["spec_path"])

    async def _log_to_knowledge(
        self,
        title: str,
        content: str,
        category: str = "orchestrator",
    ) -> str:
        """Log an entry to the knowledge base."""
        entry = create_knowledge_entry(
            title=title,
            content=content,
            session_id=self.project_id or "orchestrator",
            category=category,
        )
        return self.knowledge_base.write(entry)

    # === Phase Handlers ===

    async def _phase_spec_ingestion(self) -> PhaseResult:
        """Phase 1: Ingest the specification."""
        logger.info("Phase 1: Ingesting specification")

        if not self.spec_path or not self.spec_path.exists():
            return PhaseResult(
                success=False,
                phase=Phase.SPEC_INGESTION,
                message="Specification file not found",
            )

        # Spawn spec agent to analyze the spec
        session = await self.session_manager.spawn(
            prompt=f"Analyze the specification at {self.spec_path} and identify key features, requirements, and questions for the interview phase.",
            agent_type="spec",
        )

        # For now, mark as complete (actual agent execution TBD)
        await self.session_manager.complete(
            session.uuid,
            "Specification ingested successfully",
        )

        await self._log_to_knowledge(
            title="Spec Ingestion Complete",
            content=f"Ingested specification from {self.spec_path}",
            category="phase-1",
        )

        return PhaseResult(
            success=True,
            phase=Phase.SPEC_INGESTION,
            message="Specification ingested",
            next_phase=Phase.INTERVIEW,
        )

    async def _phase_interview(self) -> PhaseResult:
        """Phase 2: Interview the user."""
        logger.info("Phase 2: User interview")

        # Spawn interview agent
        session = await self.session_manager.spawn(
            prompt="Conduct a thorough interview with the user about the project requirements. Use AskUserQuestion to gather information about implementation preferences, testing requirements, and any missing details.",
            agent_type="interview",
        )

        # Interview requires user input - this phase may take time
        self.state = OrchestratorState.WAITING_FOR_USER

        # For now, mark as complete
        await self.session_manager.complete(
            session.uuid,
            "Interview completed",
        )

        self.state = OrchestratorState.RUNNING

        await self._log_to_knowledge(
            title="Interview Complete",
            content="User interview phase completed. Decisions recorded in knowledge base.",
            category="phase-2",
        )

        return PhaseResult(
            success=True,
            phase=Phase.INTERVIEW,
            message="Interview completed",
            next_phase=Phase.SPEC_CREATION,
        )

    async def _phase_spec_creation(self) -> PhaseResult:
        """Phase 3: Create complete modular specification."""
        logger.info("Phase 3: Creating modular specification")

        session = await self.session_manager.spawn(
            prompt="Create a complete modular specification based on the ingested spec and interview decisions. Split into independent modules with clear interfaces.",
            agent_type="planning",
        )

        await self.session_manager.complete(session.uuid, "Specification created")

        return PhaseResult(
            success=True,
            phase=Phase.SPEC_CREATION,
            message="Modular specification created",
            next_phase=Phase.PLANNING,
        )

    async def _phase_planning(self) -> PhaseResult:
        """Phase 4: Create project plan with milestones."""
        logger.info("Phase 4: Creating project plan")

        session = await self.session_manager.spawn(
            prompt="Create a detailed project plan with milestones, testing plans, and implementation order based on module dependencies.",
            agent_type="planning",
        )

        await self.session_manager.complete(session.uuid, "Project plan created")

        return PhaseResult(
            success=True,
            phase=Phase.PLANNING,
            message="Project plan created",
            next_phase=Phase.REVIEW,
        )

    async def _phase_review(self) -> PhaseResult:
        """Phase 5: Review for uncertainties, may loop back."""
        logger.info("Phase 5: Reviewing for uncertainties")

        session = await self.session_manager.spawn(
            prompt="Review the specification and project plan for any uncertainties, ambiguities, or missing information. Identify items that need clarification.",
            agent_type="review",
        )

        await self.session_manager.complete(session.uuid, "Review completed")

        # Check if we need to loop back to interview
        # This would be determined by the review agent's findings
        has_uncertainties = False  # Placeholder - would come from agent result

        if has_uncertainties:
            return PhaseResult(
                success=True,
                phase=Phase.REVIEW,
                message="Uncertainties found - returning to interview",
                should_loop=True,
                loop_to_phase=Phase.INTERVIEW,
            )

        return PhaseResult(
            success=True,
            phase=Phase.REVIEW,
            message="Review complete - no uncertainties",
            next_phase=Phase.VALIDATION,
        )

    async def _phase_validation(self) -> PhaseResult:
        """Phase 6: Validate project plan with separate agent."""
        logger.info("Phase 6: Validating project plan")

        session = await self.session_manager.spawn(
            prompt="Validate the project plan. Check that all requirements are covered, dependencies are correct, and the plan is implementable.",
            agent_type="validation",
        )

        await self.session_manager.complete(session.uuid, "Validation completed")

        return PhaseResult(
            success=True,
            phase=Phase.VALIDATION,
            message="Project plan validated",
            next_phase=Phase.IMPLEMENTATION,
        )

    async def _phase_implementation(self) -> PhaseResult:
        """Phase 7: TDD Implementation with three-agent trust model."""
        logger.info("Phase 7: Implementation")

        # Get incomplete tasks
        incomplete = self.records_manager.get_incomplete_tasks()

        if not incomplete:
            return PhaseResult(
                success=True,
                phase=Phase.IMPLEMENTATION,
                message="All implementation complete",
                next_phase=Phase.TESTING,
            )

        # Take the next task
        task = incomplete[0]
        logger.info("Implementing task: %s", task.name)

        # Three-agent trust model:
        # 1. Coding Agent implements
        coding_session = await self.session_manager.spawn(
            prompt=f"Implement: {task.name}\nDescription: {task.description}\nUse TDD - write tests first, then implement.",
            agent_type="implementation",
        )

        # 2. Testing Agent validates
        testing_session = await self.session_manager.spawn(
            prompt=f"Validate the implementation of: {task.name}\nRun tests and provide evidence of functionality.",
            agent_type="testing",
        )

        # 3. Code Review Agent reviews
        review_session = await self.session_manager.spawn(
            prompt=f"Review the implementation of: {task.name}\nCheck linting, security, and best practices. ALL findings must be fixed.",
            agent_type="review",
        )

        # Wait for all to complete
        await self.session_manager.complete(coding_session.uuid, "Implementation done")
        await self.session_manager.complete(testing_session.uuid, "Testing done")
        await self.session_manager.complete(review_session.uuid, "Review done")

        # Update checkboxes
        self.records_manager.update_checkbox(
            task.module, task.name, Checkbox.IMPLEMENTED, True
        )
        self.records_manager.update_checkbox(
            task.module, task.name, Checkbox.MOCK_TESTED, True
        )

        # Check if more tasks remain
        remaining = self.records_manager.get_incomplete_tasks()
        if remaining:
            return PhaseResult(
                success=True,
                phase=Phase.IMPLEMENTATION,
                message=f"Completed: {task.name}. {len(remaining)} tasks remaining.",
            )

        return PhaseResult(
            success=True,
            phase=Phase.IMPLEMENTATION,
            message="All implementation tasks complete",
            next_phase=Phase.TESTING,
        )

    async def _phase_testing(self) -> PhaseResult:
        """Phase 8: Final testing and validation."""
        logger.info("Phase 8: Final testing")

        session = await self.session_manager.spawn(
            prompt="Run all integration and live tests. Verify the complete system works as specified. Mark remaining checkboxes.",
            agent_type="testing",
        )

        await self.session_manager.complete(session.uuid, "Final testing complete")

        # Check if all tasks are 5/5
        if self.records_manager.is_complete():
            return PhaseResult(
                success=True,
                phase=Phase.TESTING,
                message="All tests passed - project complete",
                next_phase=Phase.COMPLETE,
            )

        # If not complete, loop back to validation
        return PhaseResult(
            success=True,
            phase=Phase.TESTING,
            message="Some tests failed - returning to validation",
            should_loop=True,
            loop_to_phase=Phase.VALIDATION,
        )


# Singleton instance
_orchestrator: Orchestrator | None = None


def get_orchestrator(
    project_root: Path | None = None,
    safemode: bool = False,
) -> Orchestrator:
    """Get the orchestrator singleton.

    Args:
        project_root: Project root directory.
        safemode: Whether to use safe mode.

    Returns:
        The Orchestrator instance.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(
            project_root=project_root,
            safemode=safemode,
        )
    return _orchestrator
