"""Core Orchestrator for Beyond Ralph.

The main control loop that implements the Spec and Interview Coder methodology.
Manages phases, agent coordination, and project completion.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from beyond_ralph.core.knowledge import KnowledgeBase, create_knowledge_entry
from beyond_ralph.core.quota_manager import get_quota_manager
from beyond_ralph.core.records import Checkbox, RecordsManager
from beyond_ralph.core.session_manager import SessionOutput, SessionStatus, get_session_manager

logger = logging.getLogger(__name__)

# Boilerplate appended to every agent prompt to prevent context exhaustion
CONTEXT_BUDGET_RULES = """

CONTEXT BUDGET RULES (MANDATORY):
- Use Grep/Glob to find specific code - do NOT read entire files unless small (<200 lines)
- Read only the functions/sections you need to modify
- Do NOT explore the whole codebase - focus ONLY on your specific task
- If a file is large, read only the relevant section using offset/limit
- Write targeted changes, not full file rewrites
- Limit yourself to the files directly related to your task
"""


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
    IMPLEMENTATION_AUDIT = "implementation_audit"  # Phase 9
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
    data: dict[str, Any] = field(default_factory=dict)  # Additional data from agents


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
        use_cli: bool = True,
    ):
        """Initialize orchestrator.

        Args:
            project_root: Root directory for the project.
            safemode: If True, require permissions for dangerous operations.
            max_parallel_agents: Maximum concurrent agents (Claude Code limit is 7).
            use_cli: If True, spawn real Claude CLI sessions (for standalone use).
                     If False, use Task tool mode (for running inside Claude Code).
        """
        self.project_root = project_root or Path.cwd()
        self.safemode = safemode
        self.max_parallel_agents = max_parallel_agents
        self.use_cli = use_cli  # Whether to spawn real CLI sessions

        # Core components - use project-specific paths
        self.session_manager = get_session_manager(safemode=safemode)
        self.quota_manager = get_quota_manager()
        self.knowledge_base = KnowledgeBase(self.project_root / "beyondralph_knowledge")
        self.records_manager = RecordsManager(self.project_root / "records")

        # State
        self.project_id: str | None = None
        self.phase = Phase.IDLE
        self.state = OrchestratorState.STOPPED
        self.spec_path: Path | None = None
        self._last_activity = datetime.now()
        self._errors: list[str] = []
        self._enable_streaming: bool = True  # Stream subagent output to console

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
            Phase.IMPLEMENTATION_AUDIT,
            Phase.COMPLETE,
        ]

    def _stream_output(self, output: SessionOutput) -> None:
        """Callback for streaming subagent output to console.

        Formats output with [AGENT:id] or [BEYOND-RALPH] prefixes.

        Args:
            output: Session output to stream.
        """
        if not self._enable_streaming:
            return

        # Print formatted output to console
        formatted = output.formatted()
        print(formatted)

        # Also log at debug level
        logger.debug("Agent output: %s", formatted)

    def _log_phase_transition(self, from_phase: Phase, to_phase: Phase) -> None:
        """Log phase transitions with [BEYOND-RALPH] prefix.

        Args:
            from_phase: Previous phase.
            to_phase: New phase.
        """
        if self._enable_streaming:
            print(f"[BEYOND-RALPH] Phase transition: {from_phase.value} → {to_phase.value}")
        logger.info("Phase transition: %s → %s", from_phase.value, to_phase.value)

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
        return f"br-{uuid.uuid4().hex[:8]}"

    async def _run_loop(self) -> None:
        """Main orchestration loop."""
        max_iterations = 100  # Prevent infinite loops
        iteration = 0
        loop_back_count = 0
        max_loop_backs = 3  # Maximum times to loop back before forcing completion

        while self.state == OrchestratorState.RUNNING:
            iteration += 1
            if iteration > max_iterations:
                logger.error("Maximum iterations reached - stopping")
                self._errors.append("Maximum iterations reached")
                break

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
                loop_back_count += 1
                if loop_back_count >= max_loop_backs:
                    logger.warning("Maximum loop backs reached - forcing completion")
                    self.phase = Phase.COMPLETE
                else:
                    logger.info("Looping back to phase: %s (attempt %d/%d)",
                               result.loop_to_phase, loop_back_count, max_loop_backs)
                    self.phase = result.loop_to_phase
            elif result.next_phase:
                logger.info("Transitioning to phase: %s", result.next_phase)
                self.phase = result.next_phase
                loop_back_count = 0  # Reset on forward progress
            else:
                # Move to next phase in order
                self.phase = self._get_next_phase()
                loop_back_count = 0

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
            Phase.IMPLEMENTATION_AUDIT: self._phase_implementation_audit,
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

        # Read and parse the spec
        spec_content = self.spec_path.read_text()

        # Extract project name from the spec (first heading)
        project_name = "main"
        for line in spec_content.split("\n"):
            if line.startswith("# "):
                project_name = line[2:].strip().lower().replace(" ", "_")
                break

        # Create a task from the spec requirements
        task_name = f"Implement {project_name.replace('_', ' ').title()}"
        task_description = spec_content[:500] + "..." if len(spec_content) > 500 else spec_content

        task = self.records_manager.add_task(
            module=project_name,
            name=task_name,
            description=task_description,
        )

        # Spawn spec agent to analyze the spec
        self._log_phase_transition(Phase.IDLE, Phase.SPEC_INGESTION)
        session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=15,
            prompt=f"""Analyze the specification at {self.spec_path} and identify:
1. Key features and requirements (list each one)
2. Technologies mentioned or implied
3. Questions that need clarification in the interview phase
4. Potential ambiguities or missing information

Read the spec file and provide a structured analysis.""",
            agent_type="spec",
            output_callback=self._stream_output,
        )

        # Use the actual session result (spawn_cli waits for completion)
        if session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.SPEC_INGESTION,
                message=f"Spec analysis failed: {session.result or 'Unknown error'}",
                errors=[session.result or "Spec agent failed"],
            )

        await self._log_to_knowledge(
            title="Spec Ingestion Complete",
            content=f"Ingested specification from {self.spec_path}\n\nAgent result:\n{session.result}",
            category="phase-1",
        )

        return PhaseResult(
            success=True,
            phase=Phase.SPEC_INGESTION,
            message=f"Specification ingested, created task: {task.name}",
            next_phase=Phase.INTERVIEW,
            data={"session_result": session.result},
        )

    async def _phase_interview(self) -> PhaseResult:
        """Phase 2: Interview the user."""
        logger.info("Phase 2: User interview")

        # Interview requires user input - this phase may take time
        self.state = OrchestratorState.WAITING_FOR_USER

        # Spawn interview agent
        session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=15,
            prompt="""Conduct a thorough interview with the user about the project requirements.

Use AskUserQuestion to gather information about:
1. Implementation preferences (language, frameworks, tools)
2. Testing requirements (what types of tests, coverage expectations)
3. Missing details from the specification
4. Technical constraints or requirements
5. Deployment environment

After gathering all necessary information, summarize the key decisions made.
This is the ONLY approval gate - after this phase, the system operates autonomously.""",
            agent_type="interview",
            output_callback=self._stream_output,
        )

        self.state = OrchestratorState.RUNNING

        if session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.INTERVIEW,
                message=f"Interview failed: {session.result or 'Unknown error'}",
                errors=[session.result or "Interview agent failed"],
            )

        await self._log_to_knowledge(
            title="Interview Complete",
            content=f"User interview phase completed.\n\nDecisions:\n{session.result}",
            category="phase-2",
        )

        return PhaseResult(
            success=True,
            phase=Phase.INTERVIEW,
            message="Interview completed",
            next_phase=Phase.SPEC_CREATION,
            data={"decisions": session.result},
        )

    async def _phase_spec_creation(self) -> PhaseResult:
        """Phase 3: Create complete modular specification."""
        logger.info("Phase 3: Creating modular specification")

        session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=20,
            prompt=f"""Create a complete modular specification based on:
1. The original specification at {self.spec_path}
2. The interview decisions recorded in the knowledge base

Split into independent modules with:
- Clear interfaces between modules
- Explicit dependencies
- Test requirements for each module
- 7-checkbox task tracking (Planned, Implemented, Mock tested, Integration tested, Live tested, Spec compliant, Audit verified)

Write the modular specification to records/[module_name]/spec.md for each module.
Also create a MODULAR_SPEC.md in the project root summarizing all modules.""",
            agent_type="planning",
            output_callback=self._stream_output,
        )

        if session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.SPEC_CREATION,
                message=f"Spec creation failed: {session.result or 'Unknown error'}",
                errors=[session.result or "Spec creation agent failed"],
            )

        return PhaseResult(
            success=True,
            phase=Phase.SPEC_CREATION,
            message="Modular specification created",
            next_phase=Phase.PLANNING,
            data={"spec_result": session.result},
        )

    async def _phase_planning(self) -> PhaseResult:
        """Phase 4: Create project plan with milestones."""
        logger.info("Phase 4: Creating project plan")

        session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=20,
            prompt="""Create a detailed project plan with:
1. Implementation order based on module dependencies
2. Milestones for each phase
3. Testing plans (unit, integration, live)
4. Risk mitigation strategies

For each module, create records/[module]/tasks.md with:
- Task checkboxes (7 checkboxes per task)
- Clear acceptance criteria
- Dependencies on other modules

Update the PROJECT_PLAN.md with the overall timeline and milestones.""",
            agent_type="planning",
            output_callback=self._stream_output,
        )

        if session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.PLANNING,
                message=f"Planning failed: {session.result or 'Unknown error'}",
                errors=[session.result or "Planning agent failed"],
            )

        return PhaseResult(
            success=True,
            phase=Phase.PLANNING,
            message="Project plan created",
            next_phase=Phase.REVIEW,
            data={"plan_result": session.result},
        )

    async def _phase_review(self) -> PhaseResult:
        """Phase 5: Review for uncertainties, may loop back."""
        logger.info("Phase 5: Reviewing for uncertainties")

        session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=15,
            prompt="""Review the specification and project plan for any uncertainties, ambiguities, or missing information.

Check:
1. All requirements have corresponding tasks
2. No conflicting requirements
3. Dependencies are correctly identified
4. Testing plans are complete
5. No TBD, TODO, or unclear items remain

If you find uncertainties that REQUIRE user input, clearly state them.
If you find issues that can be resolved without user input, resolve them.

Output format:
- NEEDS_INTERVIEW: true/false
- UNCERTAINTIES: (list if any)
- RESOLVED: (list of auto-resolved issues)""",
            agent_type="review",
            output_callback=self._stream_output,
        )

        if session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.REVIEW,
                message=f"Review failed: {session.result or 'Unknown error'}",
                errors=[session.result or "Review agent failed"],
            )

        # Check if we need to loop back to interview based on agent output
        result_text = session.result or ""
        has_uncertainties = "NEEDS_INTERVIEW: true" in result_text.lower() or \
                           "needs_interview: true" in result_text.lower()

        if has_uncertainties:
            return PhaseResult(
                success=True,
                phase=Phase.REVIEW,
                message="Uncertainties found - returning to interview",
                should_loop=True,
                loop_to_phase=Phase.INTERVIEW,
                data={"review_result": session.result},
            )

        return PhaseResult(
            success=True,
            phase=Phase.REVIEW,
            message="Review complete - no uncertainties",
            next_phase=Phase.VALIDATION,
            data={"review_result": session.result},
        )

    async def _phase_validation(self) -> PhaseResult:
        """Phase 6: Validate project plan with separate agent."""
        logger.info("Phase 6: Validating project plan")

        session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=15,
            prompt="""Validate the project plan as a SEPARATE agent (you did not create it).

Check:
1. All requirements from the original spec have corresponding tasks
2. Dependencies between modules are correct and complete
3. Testing plans cover all acceptance criteria
4. Implementation order respects dependencies
5. No circular dependencies exist
6. Each task has all 7 checkboxes defined

Output:
- VALID: true/false
- ISSUES: (list of any problems found)
- SUGGESTIONS: (improvements that could be made)

If VALID is false, the plan needs to be revised.""",
            agent_type="validation",
            output_callback=self._stream_output,
        )

        if session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.VALIDATION,
                message=f"Validation failed: {session.result or 'Unknown error'}",
                errors=[session.result or "Validation agent failed"],
            )

        # Check if validation passed
        result_text = session.result or ""
        is_valid = "VALID: true" in result_text.lower() or "valid: true" in result_text.lower()

        if not is_valid and "VALID: false" in result_text.lower():
            return PhaseResult(
                success=True,
                phase=Phase.VALIDATION,
                message="Validation found issues - returning to planning",
                should_loop=True,
                loop_to_phase=Phase.PLANNING,
                data={"validation_result": session.result},
            )

        return PhaseResult(
            success=True,
            phase=Phase.VALIDATION,
            message="Project plan validated",
            next_phase=Phase.IMPLEMENTATION,
            data={"validation_result": session.result},
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

        # THREE-AGENT TRUST MODEL:
        # Each agent operates independently and validates the others

        # 1. CODING AGENT - Implements with TDD
        if self._enable_streaming:
            print(f"[BEYOND-RALPH] Spawning Coding Agent for: {task.name}")
        coding_session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=25,
            prompt=f"""CODING AGENT: Implement the following task using TDD.

Task: {task.name}
Description: {task.description}

REQUIREMENTS:
1. Write tests FIRST (Test-Driven Development)
2. Implement the minimal code to pass tests
3. Refactor while keeping tests green
4. Follow the project's code style (check CLAUDE.md)
5. Add type hints and docstrings to public functions
6. Commit your changes with descriptive messages

ZERO DEFERRAL POLICY (MANDATORY):
- You MUST fully implement everything described in the spec for this task
- Do NOT defer anything to 'v2', 'future work', or 'next version'
- Do NOT implement a 'simplified version' - implement the SPECIFIED version
- Do NOT leave placeholders, stubs, or partial implementations
- There are NO time constraints - take as long as needed to implement fully
- If the spec says it, you MUST implement it. No exceptions.

After implementation, update records/{task.module}/tasks.md:
- Mark [x] Planned
- Mark [x] Implemented

Output what files you created/modified.
{CONTEXT_BUDGET_RULES}""",
            agent_type="implementation",
            output_callback=self._stream_output,
        )

        if coding_session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.IMPLEMENTATION,
                message=f"Coding failed for {task.name}: {coding_session.result}",
                errors=[coding_session.result or "Coding agent failed"],
            )

        # 2. TESTING AGENT - Validates independently (did NOT write the code)
        if self._enable_streaming:
            print(f"[BEYOND-RALPH] Spawning Testing Agent for: {task.name}")
        testing_session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=20,
            prompt=f"""TESTING AGENT: Validate the implementation of: {task.name}

You are a SEPARATE agent - you did NOT write this code.
Your job is to verify it works correctly.

REQUIREMENTS:
1. Run the unit tests: pytest tests/
2. Check test coverage is adequate
3. Run integration tests if applicable
4. Verify the implementation matches the task description
5. Provide EVIDENCE of test results (paste output)

If tests FAIL:
- Output TESTS_PASSED: false
- List specific failures

If tests PASS:
- Output TESTS_PASSED: true
- Update records/{task.module}/tasks.md:
  - Mark [x] Mock tested
  - Mark [x] Integration tested (if applicable)
{CONTEXT_BUDGET_RULES}""",
            agent_type="testing",
            output_callback=self._stream_output,
        )

        if testing_session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.IMPLEMENTATION,
                message=f"Testing failed for {task.name}: {testing_session.result}",
                errors=[testing_session.result or "Testing agent failed"],
            )

        # Check if tests passed
        tests_passed = "TESTS_PASSED: true" in (testing_session.result or "").lower()

        # 3. CODE REVIEW AGENT - Reviews for quality (did NOT write or test)
        if self._enable_streaming:
            print(f"[BEYOND-RALPH] Spawning Review Agent for: {task.name}")
        review_session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=20,
            prompt=f"""CODE REVIEW AGENT: Review the implementation of: {task.name}

You are a SEPARATE agent - you did NOT write or test this code.
Your job is to ensure code quality.

RUN THESE CHECKS:
1. Linting: ruff check src/
2. Type checking: mypy src/
3. Security: Check for OWASP top 10 vulnerabilities
4. Best practices: Check for code smells, complexity

Output format:
REVIEW_PASSED: true/false
MUST_FIX: (list of items that MUST be fixed)
SUGGESTIONS: (optional improvements)

The Coding Agent MUST fix all MUST_FIX items before proceeding.
If REVIEW_PASSED is false, this task cannot be marked complete.
{CONTEXT_BUDGET_RULES}""",
            agent_type="review",
            output_callback=self._stream_output,
        )

        if review_session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.IMPLEMENTATION,
                message=f"Review failed for {task.name}: {review_session.result}",
                errors=[review_session.result or "Review agent failed"],
            )

        # Check if review passed
        review_result = review_session.result or ""
        review_passed = "REVIEW_PASSED: true" in review_result.lower()
        has_must_fix = "MUST_FIX:" in review_result and review_result.split("MUST_FIX:")[1].strip()

        # If review found issues, coding agent must fix them
        if has_must_fix and not review_passed:
            if self._enable_streaming:
                print(f"[BEYOND-RALPH] Review found issues - Coding Agent must fix")
            # Spawn coding agent again to fix issues
            fix_session = await self.session_manager.spawn(
                use_cli=self.use_cli,
                max_turns=20,
                prompt=f"""CODING AGENT: Fix the following review issues for {task.name}

Review findings:
{review_result}

You MUST fix ALL items listed under MUST_FIX.
Do not skip any items. Do not argue with the reviewer.
Fix each issue and run tests to verify the fix doesn't break anything.
{CONTEXT_BUDGET_RULES}""",
                agent_type="implementation",
                output_callback=self._stream_output,
            )

        # Update checkboxes based on actual results
        if tests_passed:
            self.records_manager.update_checkbox(task.module, task.name, Checkbox.MOCK_TESTED, True)
            self.records_manager.update_checkbox(task.module, task.name, Checkbox.INTEGRATION_TESTED, True)

        # Check if more tasks remain
        remaining = self.records_manager.get_incomplete_tasks()
        if remaining:
            return PhaseResult(
                success=True,
                phase=Phase.IMPLEMENTATION,
                message=f"Completed: {task.name}. {len(remaining)} tasks remaining.",
                data={
                    "coding_result": coding_session.result,
                    "testing_result": testing_session.result,
                    "review_result": review_session.result,
                },
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

        if self._enable_streaming:
            print("[BEYOND-RALPH] Phase 8: Running final integration and live tests")

        # Run full integration tests
        session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=25,
            prompt=f"""FINAL TESTING: Three distinct stages. Do NOT conflate them.

STAGE 1 - MOCK + INTEGRATION TESTS:
Run the project's test suite (pytest / cargo test / npm test as appropriate).
Mark [x] Mock tested and [x] Integration tested for tasks whose tests pass.

STAGE 2 - LIVE TESTING (CRITICAL - THIS IS NOT MORE UNIT TESTS):
You must ACTUALLY BUILD AND RUN the real artifact:
1. Build the project (cargo build / python -m build / npm run build)
2. Run the ACTUAL BUILT ARTIFACT with real inputs (not test harnesses)
3. Verify the output is correct
4. Record the exact command and output as evidence in records/*/tasks.md

Examples of what qualifies as Live Testing:
- Compiler: compile a real source file, run the output binary, verify results
- API: start the server, curl an endpoint, check response body
- CLI: run the binary with real args, verify stdout/stderr

DO NOT mark [x] Live tested just because unit/integration tests pass.
Live tested means the ACTUAL ARTIFACT was executed outside of test harnesses.

STAGE 3 - RESULTS:
For each task in records/*/tasks.md, update checkboxes based on what ACTUALLY passed.

Output:
ALL_TESTS_PASSED: true/false
LIVE_TESTS_PASSED: true/false (did you actually build and run the artifact?)
COVERAGE: percentage
FAILED_TESTS: (list if any)
INCOMPLETE_TASKS: (list of tasks missing checkboxes)
{CONTEXT_BUDGET_RULES}""",
            agent_type="testing",
            output_callback=self._stream_output,
        )

        if session.status == SessionStatus.FAILED:
            return PhaseResult(
                success=False,
                phase=Phase.TESTING,
                message=f"Final testing failed: {session.result or 'Unknown error'}",
                errors=[session.result or "Testing agent failed"],
            )

        # Check results
        result_text = session.result or ""
        all_passed = "ALL_TESTS_PASSED: true" in result_text.lower()

        # Check if all tasks are complete (7/7 checkboxes)
        if self.records_manager.is_complete():
            return PhaseResult(
                success=True,
                phase=Phase.TESTING,
                message="All tests passed - project complete",
                next_phase=Phase.COMPLETE,
                data={"testing_result": session.result},
            )

        # If not complete, check if tests failed or just missing checkboxes
        if not all_passed:
            return PhaseResult(
                success=True,
                phase=Phase.TESTING,
                message="Some tests failed - returning to implementation",
                should_loop=True,
                loop_to_phase=Phase.IMPLEMENTATION,
                data={"testing_result": session.result},
            )

        # Tests passed but checkboxes incomplete - run adversarial spec compliance

        # PASS 1: Extract requirements from spec
        if self._enable_streaming:
            print("[BEYOND-RALPH] Phase 8.5: Requirement extraction from spec")

        extraction_session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=15,
            prompt=f"""REQUIREMENT EXTRACTOR: Read the specification at: {self.spec_path}
Also read the module specs in records/*/spec.md.

Extract EVERY requirement, feature, behavior, constraint, and interface.
Number them sequentially: REQ-001, REQ-002, etc.

Include ALL of these:
- Explicit requirements (MUST, SHALL, SHOULD, REQUIRED)
- Implicit requirements (described behaviors, documented interfaces)
- Edge cases mentioned in the spec
- Error handling requirements
- Performance/quality constraints
- Integration points and interfaces

Output a numbered list. Do NOT skip anything. Do NOT summarize or combine.
If in doubt whether something is a requirement, INCLUDE IT.
{CONTEXT_BUDGET_RULES}""",
            agent_type="validation",
            output_callback=self._stream_output,
        )

        requirements_list = extraction_session.result or ""

        # PASS 2: Adversarial compliance check
        if self._enable_streaming:
            print("[BEYOND-RALPH] Phase 8.5: Adversarial spec compliance check")

        compliance_session = await self.session_manager.spawn(
            use_cli=self.use_cli,
            max_turns=25,
            prompt=f"""ADVERSARIAL SPEC COMPLIANCE AGENT: Your job is to FIND FAILURES.

You are an ADVERSARIAL reviewer. You are NOT here to confirm the code works.
You are here to find every way it FAILS to meet the specification.

ZERO DEFERRAL POLICY:
- 'Deferred to v2' = FAIL (there is no v2)
- 'Partial implementation' = FAIL
- 'Simplified version' = FAIL (implement the SPECIFIED version)
- 'Good enough' = FAIL
- 'Placeholder' = FAIL
- There are NO time constraints. Everything in the spec MUST be implemented.

Here are the extracted requirements:
{requirements_list}

For EACH requirement:
1. Find the EXACT code that implements it (file:line)
2. Verify the code ACTUALLY does what the spec says (not just something similar)
3. Check edge cases mentioned in the spec are handled
4. Mark PASS only if you can point to complete, working code

Output format (MANDATORY):
SPEC_COMPLIANCE_RESULT: PASS/FAIL
TOTAL_REQUIREMENTS: N
PASSED: N
FAILED: N

CHECKLIST:
REQ-001: [spec text] -> PASS/FAIL | [evidence: file:line or reason for failure]
REQ-002: ...

ANY single FAIL = SPEC_COMPLIANCE_RESULT: FAIL
Do NOT mark [x] Spec compliant on ANY tasks if there are failures.
Only mark [x] Spec compliant on ALL tasks if SPEC_COMPLIANCE_RESULT: PASS.
{CONTEXT_BUDGET_RULES}""",
            agent_type="validation",
            output_callback=self._stream_output,
        )

        result_text = compliance_session.result or ""
        spec_compliant = "SPEC_COMPLIANCE_RESULT: PASS" in result_text.upper()

        if spec_compliant:
            return PhaseResult(
                success=True,
                phase=Phase.TESTING,
                message="All tests and spec compliance passed",
                next_phase=Phase.COMPLETE,
                data={
                    "testing_result": session.result,
                    "requirements_list": requirements_list,
                    "compliance_result": result_text,
                },
            )

        # Spec compliance failed - extract failed requirements for targeted fixes
        return PhaseResult(
            success=True,
            phase=Phase.TESTING,
            message="Spec compliance FAILED - returning to implementation",
            should_loop=True,
            loop_to_phase=Phase.IMPLEMENTATION,
            data={
                "testing_result": session.result,
                "requirements_list": requirements_list,
                "compliance_result": result_text,
            },
        )

    async def _phase_implementation_audit(self) -> PhaseResult:
        """Phase 9: Implementation Audit - catch stubs, fakes, and TODOs.

        Two-pronged approach:
        1. Static analysis: grep for NotImplementedError, TODO, pass, placeholder strings
        2. LLM interrogation: ask a separate agent "is this implementation real?"

        If stubs are found, loops back to Phase 7 (IMPLEMENTATION) for fixes.
        """
        logger.info("Phase 9: Implementation Audit")

        if self._enable_streaming:
            print("[BEYOND-RALPH] Phase 9: Running implementation audit...")

        # Prong 1: Static analysis (fast, deterministic)
        from beyond_ralph.core.audit import AuditSeverity, run_static_audit

        if self._enable_streaming:
            print("[BEYOND-RALPH] Prong 1: Static analysis for stubs/fakes...")

        audit_result = run_static_audit(
            project_root=self.project_root,
            min_severity=AuditSeverity.HIGH,
        )

        if not audit_result.passed:
            findings_text = "\n".join(
                f"  - {f.file}:{f.line_number} [{f.severity.value}] "
                f"{f.pattern_name}: {f.line_text}"
                for f in audit_result.findings
            )
            if self._enable_streaming:
                print(f"[BEYOND-RALPH] Static audit FAILED: {audit_result.critical_count} critical, "
                      f"{audit_result.high_count} high findings")
                print(findings_text)

            return PhaseResult(
                success=True,
                phase=Phase.IMPLEMENTATION_AUDIT,
                message=f"Static audit failed: {audit_result.critical_count} critical, "
                        f"{audit_result.high_count} high findings - returning to implementation",
                should_loop=True,
                loop_to_phase=Phase.IMPLEMENTATION,
                data={
                    "audit_passed": False,
                    "findings": findings_text,
                    "critical_count": audit_result.critical_count,
                    "high_count": audit_result.high_count,
                },
            )

        if self._enable_streaming:
            print(f"[BEYOND-RALPH] Static audit passed: {audit_result.files_scanned} files clean")

        # Prong 2: LLM interrogation (ask a separate agent if implementations are real)
        if self._enable_streaming:
            print("[BEYOND-RALPH] Prong 2: LLM interrogation - checking each module...")

        modules = self.records_manager.get_modules()

        for module in modules:
            if self._enable_streaming:
                print(f"[BEYOND-RALPH] Interrogating module: {module}")

            interrogation_session = await self.session_manager.spawn(
                use_cli=self.use_cli,
                max_turns=20,
                prompt=f"""IMPLEMENTATION AUDIT AGENT: You are a SEPARATE agent auditing module '{module}'.

Your job is to determine if the implementation is REAL or FAKED.

Read the source code in the project and answer these questions for EACH function/class:
1. Is this a real implementation or a stub/placeholder?
2. Does the code actually DO what it claims to do?
3. Are there any TODOs, FIXMEs, or "implement me" comments?
4. Are there any functions that just return hardcoded values or raise NotImplementedError?
5. Are there any empty except blocks or pass-only function bodies?

Be BRUTALLY HONEST. If something looks fake, say so.

Output format:
AUDIT_PASSED: true/false
FAKED_ITEMS: (list of faked/stub implementations with file:line)
REAL_ITEMS: (count of verified real implementations)
CONCERNS: (any other concerns)

If AUDIT_PASSED is false, list EVERY faked item so it can be fixed.
{CONTEXT_BUDGET_RULES}""",
                agent_type="validation",
                output_callback=self._stream_output,
            )

            result_text = interrogation_session.result or ""
            audit_passed = "AUDIT_PASSED: true" in result_text.lower()

            if not audit_passed:
                if self._enable_streaming:
                    print(f"[BEYOND-RALPH] LLM audit FAILED for module: {module}")

                return PhaseResult(
                    success=True,
                    phase=Phase.IMPLEMENTATION_AUDIT,
                    message=f"LLM audit failed for module '{module}' - "
                            f"returning to implementation",
                    should_loop=True,
                    loop_to_phase=Phase.IMPLEMENTATION,
                    data={
                        "audit_passed": False,
                        "module": module,
                        "interrogation_result": result_text,
                    },
                )

        # Both prongs passed - mark audit verified on all tasks
        if self._enable_streaming:
            print("[BEYOND-RALPH] Implementation audit PASSED - all modules verified")

        for module in modules:
            tasks = self.records_manager.get_module_tasks(module)
            for task in tasks:
                self.records_manager.update_checkbox(
                    module, task.name, Checkbox.AUDIT_VERIFIED, True
                )

        return PhaseResult(
            success=True,
            phase=Phase.IMPLEMENTATION_AUDIT,
            message="Implementation audit passed - all modules verified as real implementations",
            next_phase=Phase.COMPLETE,
            data={"audit_passed": True, "modules_audited": modules},
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
