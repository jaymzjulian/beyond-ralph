"""Base Agent - Foundation for all Beyond Ralph agents.

All phase-specific and trust model agents inherit from this base class.
Provides common functionality for knowledge access, tool usage, and
inter-agent communication.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
import uuid


class AgentModel(Enum):
    """Model options for agent execution."""

    SONNET = "sonnet"      # Fast, capable - default for most work
    OPUS = "opus"          # Most capable - for complex reasoning
    HAIKU = "haiku"        # Fastest, cheapest - for simple tasks
    INHERIT = "inherit"    # Use parent's model


class AgentStatus(Enum):
    """Status of agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_INPUT = "waiting_for_input"
    PAUSED = "paused"


@dataclass
class AgentResult:
    """Result of agent execution."""

    success: bool
    output: str
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    question: str | None = None  # Set if agent needs to ask something
    artifacts: list[Path] = field(default_factory=list)
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_question(self) -> bool:
        """Check if agent is returning with a question."""
        return self.question is not None


@dataclass
class AgentTask:
    """Task assigned to an agent."""

    id: str
    description: str
    instructions: str
    context: dict[str, Any] = field(default_factory=dict)
    parent_task_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        description: str,
        instructions: str,
        context: dict[str, Any] | None = None,
        parent_task_id: str | None = None,
    ) -> "AgentTask":
        """Create a new task with auto-generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            description=description,
            instructions=instructions,
            context=context or {},
            parent_task_id=parent_task_id,
        )


class BaseAgent(ABC):
    """Base class for all Beyond Ralph agents.

    Provides:
    - Knowledge base access (read before asking, write discoveries)
    - Tool usage patterns
    - Inter-agent communication (return with question)
    - Execution lifecycle management

    All agents operate autonomously after the interview phase.
    They should make decisions without asking users.
    """

    # Class-level defaults - override in subclasses
    name: str = "base"
    description: str = "Base agent class"
    tools: list[str] = []
    model: AgentModel = AgentModel.SONNET

    def __init__(
        self,
        session_id: str | None = None,
        project_root: Path | None = None,
        knowledge_dir: Path | None = None,
    ) -> None:
        """Initialize agent.

        Args:
            session_id: UUID of the spawning session (for tracking)
            project_root: Root directory of the project
            knowledge_dir: Directory for knowledge base (default: beyondralph_knowledge/)
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.project_root = project_root or Path.cwd()
        self.knowledge_dir = knowledge_dir or self.project_root / "beyondralph_knowledge"

        # Runtime state
        self._status = AgentStatus.PENDING
        self._current_task: AgentTask | None = None
        self._result: AgentResult | None = None

    @property
    def status(self) -> AgentStatus:
        """Get current agent status."""
        return self._status

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute the agent's task.

        This is the main entry point for agent work. Subclasses must implement
        this method to define their behavior.

        Args:
            task: The task to execute

        Returns:
            AgentResult with success status and output
        """
        ...

    async def read_knowledge(
        self,
        topic: str,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Read from knowledge base before asking orchestrator.

        Agents should ALWAYS check knowledge first for:
        - Previous decisions made
        - Tool preferences discovered
        - Error resolutions found
        - Implementation patterns

        Args:
            topic: Search topic/keywords
            category: Optional category filter
            tags: Optional tag filters

        Returns:
            List of matching knowledge entries
        """
        from beyond_ralph.core.knowledge import KnowledgeBase

        kb = KnowledgeBase(self.knowledge_dir)
        entries = kb.search(topic)  # sync method

        # Filter by category if specified
        if category:
            entries = [e for e in entries if e.category == category]

        # Filter by tags if specified
        if tags:
            entries = [
                e for e in entries
                if any(tag in e.tags for tag in tags)
            ]

        return [
            {
                "uuid": e.uuid,
                "title": e.title,
                "category": e.category,
                "tags": e.tags,
                "content": e.content,
                "date": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]

    async def write_knowledge(
        self,
        title: str,
        content: str,
        category: str,
        tags: list[str] | None = None,
    ) -> str:
        """Write to knowledge base for future reference.

        Agents should document:
        - Decisions made and rationale
        - Tools discovered and installed
        - Error resolutions
        - Implementation patterns

        Args:
            title: Entry title (used for filename)
            content: Markdown content
            category: Category (e.g., "implementation", "research", "decision")
            tags: Optional tags for searchability

        Returns:
            UUID of created entry
        """
        from beyond_ralph.core.knowledge import KnowledgeBase, create_knowledge_entry

        kb = KnowledgeBase(self.knowledge_dir)

        entry = create_knowledge_entry(
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            session_id=self.session_id,
        )

        entry_uuid = kb.write(entry)  # sync method
        return entry_uuid

    def return_with_question(
        self,
        question: str,
        output: str = "",
        data: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Return to caller with a question.

        Use when the agent needs information it cannot determine itself.
        This is an allowed behavior - agents can ask questions.

        Args:
            question: The question to ask
            output: Any partial output to include
            data: Any data collected so far

        Returns:
            AgentResult with question set
        """
        self._status = AgentStatus.WAITING_FOR_INPUT
        return AgentResult(
            success=False,  # Not complete yet
            output=output,
            data=data or {},
            question=question,
        )

    def fail(
        self,
        reason: str,
        errors: list[str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Mark execution as failed.

        Args:
            reason: Human-readable failure reason
            errors: List of specific errors
            data: Any data collected before failure

        Returns:
            AgentResult with failure status
        """
        self._status = AgentStatus.FAILED
        return AgentResult(
            success=False,
            output=reason,
            errors=errors or [reason],
            data=data or {},
        )

    def succeed(
        self,
        output: str,
        data: dict[str, Any] | None = None,
        artifacts: list[Path] | None = None,
    ) -> AgentResult:
        """Mark execution as successful.

        Args:
            output: Human-readable output
            data: Structured data produced
            artifacts: Files created

        Returns:
            AgentResult with success status
        """
        self._status = AgentStatus.COMPLETED
        return AgentResult(
            success=True,
            output=output,
            data=data or {},
            artifacts=artifacts or [],
        )

    async def run(self, task: AgentTask) -> AgentResult:
        """Run the agent with lifecycle management.

        This wraps execute() with status tracking and error handling.

        Args:
            task: The task to execute

        Returns:
            AgentResult from execution
        """
        self._current_task = task
        self._status = AgentStatus.RUNNING

        try:
            result = await self.execute(task)
            self._result = result
            return result
        except Exception as e:
            self._status = AgentStatus.FAILED
            error_result = self.fail(
                reason=f"Agent execution failed: {e}",
                errors=[str(e)],
            )
            self._result = error_result
            return error_result

    def get_prompt_context(self) -> dict[str, Any]:
        """Get context for prompt construction.

        Returns:
            Dict with agent metadata for prompts
        """
        return {
            "agent_name": self.name,
            "agent_description": self.description,
            "available_tools": self.tools,
            "model": self.model.value,
            "session_id": self.session_id,
            "project_root": str(self.project_root),
        }


class PhaseAgent(BaseAgent):
    """Base class for phase-specific agents.

    Phase agents execute work for specific phases of the Beyond Ralph
    methodology (Spec Ingestion, Interview, Planning, etc.).
    """

    phase: int = 0  # Override in subclass

    async def get_phase_context(self) -> dict[str, Any]:
        """Get phase-specific context.

        Returns:
            Dict with phase information
        """
        return {
            "phase": self.phase,
            "phase_name": self._get_phase_name(),
        }

    def _get_phase_name(self) -> str:
        """Get human-readable phase name."""
        phase_names = {
            1: "Spec Ingestion",
            2: "Interview",
            3: "Spec Creation",
            4: "Planning",
            5: "Review",
            6: "Validation",
            7: "Implementation",
            8: "Testing",
        }
        return phase_names.get(self.phase, f"Phase {self.phase}")


class TrustModelAgent(BaseAgent):
    """Base class for trust model agents.

    Trust model agents (Coding, Testing, Review) have specific separation
    of concerns. Each validates the work of others.
    """

    # What this agent CAN do
    can_implement: bool = False
    can_test: bool = False
    can_review: bool = False

    # What this agent CANNOT validate
    cannot_validate_own_work: bool = True

    def validate_separation(self, other_agent: "TrustModelAgent") -> bool:
        """Validate that separation of concerns is maintained.

        Args:
            other_agent: Another trust model agent

        Returns:
            True if agents have different responsibilities
        """
        if self.can_implement and other_agent.can_implement:
            return False  # Both implement - violation
        if self.can_test and other_agent.can_test:
            return False  # Both test - violation
        return True
