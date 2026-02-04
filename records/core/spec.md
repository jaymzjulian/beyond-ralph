# Module 1: Core - Specification

> Orchestrator Hub: Main control loop, session management, quota handling, and dynamic planning.

---

## Overview

The Core module is the central nervous system of Beyond Ralph. It coordinates all other modules, manages the development workflow phases, spawns and monitors agents, and handles quota-aware pausing.

**Key Principle**: The orchestrator ONLY orchestrates. It never implements, tests, or reviews code directly.

---

## Components

### 1.1 Orchestrator (`orchestrator.py`)

**Purpose**: Main control loop implementing the ralph-loop pattern with phase management.

**State Machine**:
```
IDLE → RUNNING → PAUSED → RUNNING → COMPLETE
                    ↓
              WAITING_FOR_USER
```

**Interfaces**:
```python
class Orchestrator:
    def __init__(self, config: OrchestratorConfig):
        """Initialize orchestrator with configuration."""

    async def start(self, spec_path: str) -> None:
        """Start new project from specification.

        Args:
            spec_path: Path to the project specification file.

        Flow:
            1. Validate spec exists
            2. Initialize session state
            3. Begin Phase 1 (spec ingestion)
            4. Continue through phases until complete
        """

    async def resume(self) -> None:
        """Resume paused project.

        Flow:
            1. Load saved state from .beyond_ralph_sessions/
            2. Check quota before resuming
            3. Continue from last checkpoint
        """

    def status(self) -> OrchestratorStatus:
        """Return current orchestrator status.

        Returns:
            OrchestratorStatus with phase, progress, active agents.
        """

    async def pause(self) -> None:
        """Manually pause orchestration.

        Saves state and stops agent spawning.
        """

    def on_compaction(self) -> None:
        """CRITICAL: Recovery protocol after context compaction.

        MUST:
            1. Re-read PROJECT_PLAN.md
            2. Re-read current module specs in records/
            3. Re-read task status from records/*/tasks.md
            4. Check beyondralph_knowledge/ for recent entries
            5. Resume from last known good state
        """
```

**Phase Handlers**:
```python
async def _phase_spec_ingestion(self) -> PhaseResult
async def _phase_interview(self) -> PhaseResult
async def _phase_spec_creation(self) -> PhaseResult
async def _phase_planning(self) -> PhaseResult
async def _phase_review(self) -> PhaseResult
async def _phase_validation(self) -> PhaseResult
async def _phase_implementation(self) -> PhaseResult
async def _phase_testing(self) -> PhaseResult
```

**Data Classes**:
```python
@dataclass
class OrchestratorConfig:
    safemode: bool = False
    quota_threshold: int = 85
    max_parallel_agents: int = 7
    knowledge_base_path: str = "beyondralph_knowledge/"
    records_path: str = "records/"
    sessions_path: str = ".beyond_ralph_sessions/"

@dataclass
class OrchestratorStatus:
    state: Literal["IDLE", "RUNNING", "PAUSED", "WAITING_FOR_USER", "COMPLETE"]
    current_phase: int
    phase_name: str
    progress_percent: float
    active_agents: list[str]
    last_activity: datetime

@dataclass
class PhaseResult:
    success: bool
    output: str
    should_loop: bool = False  # Return to earlier phase?
    loop_to_phase: Optional[int] = None
    evidence_path: Optional[str] = None
```

---

### 1.2 Session Manager (`session_manager.py`)

**Purpose**: Spawn and communicate with Claude Code sessions.

**Interfaces**:
```python
class SessionManager:
    def __init__(self, safemode: bool = False):
        """Initialize session manager.

        Args:
            safemode: If False, use --dangerously-skip-permissions.
        """

    def spawn(
        self,
        prompt: str,
        use_cli: bool = False,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> Session:
        """Spawn a new Claude Code session.

        Args:
            prompt: Initial prompt for the session.
            use_cli: If True, spawn via CLI. If False, use Task tool.
            output_callback: Callback for streaming output.

        Returns:
            Session object for further interaction.

        Raises:
            SessionError: If spawning fails.
            QuotaError: If quota is exceeded.
        """

    def is_locked(self, session_id: str) -> bool:
        """Check if session is locked by another process.

        Uses lock files with PID to prevent concurrent access.
        """

class Session:
    session_id: str
    created_at: datetime
    status: Literal["running", "complete", "failed"]

    async def send(self, message: str) -> SessionOutput:
        """Send message to session.

        Args:
            message: Message to send.

        Returns:
            SessionOutput with response and metadata.
        """

    async def complete(self) -> AgentResult:
        """Wait for session to complete and get result."""

    async def get_result(self) -> AgentResult:
        """Get result without waiting (for completed sessions)."""

    async def cleanup(self) -> None:
        """Clean up session resources and release lock."""

@dataclass
class SessionOutput:
    text: str
    session_id: str
    timestamp: datetime

    def formatted(self) -> str:
        """Return output with [AGENT:session_id] prefix."""
        return f"[AGENT:{self.session_id}] {self.text}"
```

---

### 1.3 Quota Manager (`quota_manager.py`)

**Purpose**: Detect and handle Claude usage quotas.

**Interfaces**:
```python
class QuotaManager:
    def __init__(self, cache_file: str = ".beyond_ralph_quota"):
        """Initialize quota manager.

        Args:
            cache_file: Path to quota cache file.
        """

    def check(self, force_refresh: bool = False) -> QuotaStatus:
        """Check current quota status.

        Args:
            force_refresh: If True, bypass cache.

        Returns:
            QuotaStatus with session and weekly percentages.

        Note:
            Uses pexpect to run 'claude /usage' and parse output.
            Caches result to avoid excessive API calls.
        """

    def is_limited(self) -> bool:
        """Check if quota is at or above threshold.

        Returns True if either:
            - session_percent >= 85
            - weekly_percent >= 85
        """

    async def wait_for_reset(self) -> None:
        """Wait until quota resets.

        Checks every 10 minutes until quota is below threshold.
        """

    def pre_spawn_check(self) -> None:
        """Check quota before spawning agent.

        Raises:
            QuotaError: If quota is limited or unknown.
        """

@dataclass
class QuotaStatus:
    session_percent: int
    weekly_percent: int
    is_limited: bool
    is_unknown: bool  # CRITICAL: blocks operations when True
    last_checked: datetime
    reset_time: Optional[datetime]
```

---

### 1.4 Dynamic Plan Manager (`dynamic_plan.py`)

**Purpose**: Track inter-module requirements and discrepancies.

**Interfaces**:
```python
class DynamicPlanManager:
    def __init__(self, plan_path: str = "PROJECT_PLAN.md"):
        """Initialize dynamic plan manager."""

    def add_requirement(
        self,
        from_module: str,
        to_module: str,
        technical_spec: str
    ) -> None:
        """Add requirement from one module to another.

        Args:
            from_module: Module requesting the requirement.
            to_module: Module that must deliver.
            technical_spec: What is needed (e.g., "get_user() function").

        Note:
            No user input needed - only technical requirements.
            Updates PROJECT_PLAN.md automatically.
        """

    def mark_failed(
        self,
        module: str,
        requirement: str,
        reason: str
    ) -> None:
        """Mark a requirement as failed to deliver.

        Aggressively records the failure for orchestrator to address.
        """

    def mark_delivered(
        self,
        module: str,
        requirement: str
    ) -> None:
        """Mark a requirement as successfully delivered."""

    def get_pending_requirements(self, module: str) -> list[ModuleRequirement]:
        """Get all pending requirements for a module."""

    def get_work_for_module(self, module: str) -> list[ModuleRequirement]:
        """Get requirements this module needs to deliver."""

    def report_discrepancy(
        self,
        module: str,
        expected: str,
        actual: str,
        severity: Literal["critical", "high", "medium"]
    ) -> None:
        """Report discrepancy between promised and delivered.

        MUST NOT work around - demands fix.
        """

    def get_discrepancies(self) -> list[Discrepancy]:
        """Get all unresolved discrepancies."""

@dataclass
class ModuleRequirement:
    id: str
    from_module: str
    to_module: str
    technical_spec: str
    status: Literal["pending", "delivered", "failed"]
    created_at: datetime
    delivered_at: Optional[datetime]

@dataclass
class Discrepancy:
    module: str
    expected: str
    actual: str
    severity: Literal["critical", "high", "medium"]
    reported_at: datetime
    resolved: bool
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 2 (Agents) | Spawning phase and trust model agents |
| Module 3 (Knowledge) | Storing session state, reading recovery info |
| Module 4 (Records) | Tracking phase completion, updating checkboxes |
| Module 5 (Skills/Hooks) | Responding to skill invocations |
| Module 8 (System) | Tool availability checks |
| Module 9 (Notifications) | Alerting when blocked |
| Module 10 (User Interaction) | Routing AskUserQuestion |

---

## Error Handling

```python
class OrchestratorError(BeyondRalphError):
    """Orchestrator-specific errors."""

class PhaseError(OrchestratorError):
    """Phase execution failed."""

class CompactionRecoveryError(OrchestratorError):
    """Failed to recover from compaction."""
```

---

## State Persistence

State is saved to `.beyond_ralph_sessions/[session_id]/`:
- `state.json` - Current orchestrator state
- `phases/` - Phase-specific data
- `agents/` - Agent session info

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Orchestrator state machine, phase handlers |
| Integration tests | Full phase flow, agent coordination |
| Live tests | Real Claude Code sessions |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested (93% coverage for orchestrator, 91% for session manager, 96% for quota manager)
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant

**Note**: This is a composite module. See individual specs for detailed status:
- `records/orchestrator/spec.md` - Core Orchestrator (93% mock tested)
- `records/session/spec.md` - Session Manager (91% mock tested)
- `records/quota/spec.md` - Quota Manager (96% mock tested)
- `records/dynamic-plan/spec.md` - Dynamic Plan Manager
