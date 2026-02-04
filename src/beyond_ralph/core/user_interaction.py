"""User Interaction Manager.

Handles routing of user interactions from subagents to the main session,
including:
- AskUserQuestion prompts from subagents
- User responses back to subagents
- Interrupts and manual pauses
- Progress indicators
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Type of user interaction."""

    QUESTION = "question"  # AskUserQuestion from subagent
    CONFIRMATION = "confirmation"  # Yes/No confirmation
    INPUT = "input"  # Free-form text input
    SELECTION = "selection"  # Select from options
    INTERRUPT = "interrupt"  # User interrupt
    PROGRESS = "progress"  # Progress update


class InteractionStatus(Enum):
    """Status of a user interaction."""

    PENDING = "pending"  # Waiting for user response
    RESPONDED = "responded"  # User has responded
    CANCELLED = "cancelled"  # Interaction cancelled
    TIMEOUT = "timeout"  # Timed out waiting for response


@dataclass
class QuestionOption:
    """An option for a selection question."""

    label: str
    value: str
    description: str | None = None
    is_recommended: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "label": self.label,
            "value": self.value,
            "description": self.description,
            "is_recommended": self.is_recommended,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuestionOption":
        """Create from dictionary."""
        return cls(
            label=data["label"],
            value=data["value"],
            description=data.get("description"),
            is_recommended=data.get("is_recommended", False),
        )


@dataclass
class UserInteraction:
    """A user interaction request from a subagent."""

    id: str
    session_id: str
    interaction_type: InteractionType
    question: str
    options: list[QuestionOption] = field(default_factory=list)
    multi_select: bool = False
    default_value: str | None = None
    status: InteractionStatus = InteractionStatus.PENDING
    response: str | list[str] | None = None
    created_at: datetime = field(default_factory=datetime.now)
    responded_at: datetime | None = None
    timeout_seconds: int = 300  # 5 minute default

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "interaction_type": self.interaction_type.value,
            "question": self.question,
            "options": [opt.to_dict() for opt in self.options],
            "multi_select": self.multi_select,
            "default_value": self.default_value,
            "status": self.status.value,
            "response": self.response,
            "created_at": self.created_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserInteraction":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            interaction_type=InteractionType(data["interaction_type"]),
            question=data["question"],
            options=[QuestionOption.from_dict(opt) for opt in data.get("options", [])],
            multi_select=data.get("multi_select", False),
            default_value=data.get("default_value"),
            status=InteractionStatus(data.get("status", "pending")),
            response=data.get("response"),
            created_at=datetime.fromisoformat(data["created_at"]),
            responded_at=(
                datetime.fromisoformat(data["responded_at"])
                if data.get("responded_at")
                else None
            ),
            timeout_seconds=data.get("timeout_seconds", 300),
        )

    def format_for_display(self) -> str:
        """Format the interaction for display to the user."""
        lines = [
            f"[USER INPUT REQUIRED - {self.session_id}]",
            "",
            self.question,
        ]

        if self.options:
            lines.append("")
            for i, opt in enumerate(self.options, 1):
                rec = " (Recommended)" if opt.is_recommended else ""
                lines.append(f"  {i}. {opt.label}{rec}")
                if opt.description:
                    lines.append(f"     {opt.description}")

        if self.multi_select:
            lines.append("")
            lines.append("(Select multiple options separated by comma)")

        if self.default_value:
            lines.append("")
            lines.append(f"Default: {self.default_value}")

        return "\n".join(lines)


@dataclass
class ProgressUpdate:
    """A progress update from a subagent."""

    session_id: str
    phase: str
    step: str
    progress_percent: int
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def format_for_display(self) -> str:
        """Format for display."""
        bar_length = 20
        filled = int(bar_length * self.progress_percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"[{self.session_id}] {self.phase} [{bar}] {self.progress_percent}% - {self.step}: {self.message}"


# Callback types
InteractionCallback = Callable[[UserInteraction], None]
ResponseCallback = Callable[[str, str | list[str]], None]


class UserInteractionManager:
    """Manages user interactions from subagents.

    This handles:
    1. Receiving AskUserQuestion requests from subagents
    2. Routing them to the main Claude Code session
    3. Capturing user responses
    4. Returning responses to the requesting subagent
    """

    def __init__(
        self,
        project_root: Path | None = None,
        state_file: str = ".beyond_ralph_interactions.json",
    ):
        """Initialize the user interaction manager.

        Args:
            project_root: Root directory of the project.
            state_file: File to store interaction state.
        """
        self.project_root = project_root or Path.cwd()
        self.state_file = self.project_root / state_file
        self._interactions: dict[str, UserInteraction] = {}
        self._pending_responses: dict[str, asyncio.Event] = {}
        self._on_interaction_callback: InteractionCallback | None = None
        self._on_response_callback: ResponseCallback | None = None
        self._paused = False
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._interactions = {
                    k: UserInteraction.from_dict(v)
                    for k, v in data.get("interactions", {}).items()
                }
                self._paused = data.get("paused", False)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load interaction state: {e}")
                self._interactions = {}
                self._paused = False

    def _save_state(self) -> None:
        """Save state to file."""
        data = {
            "interactions": {k: v.to_dict() for k, v in self._interactions.items()},
            "paused": self._paused,
            "updated_at": datetime.now().isoformat(),
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def _generate_id(self) -> str:
        """Generate a unique interaction ID."""
        import uuid

        return f"int-{uuid.uuid4().hex[:8]}"

    def set_interaction_callback(self, callback: InteractionCallback) -> None:
        """Set callback for when interactions are received.

        The callback should display the interaction to the user.

        Args:
            callback: Function to call with the interaction.
        """
        self._on_interaction_callback = callback

    def set_response_callback(self, callback: ResponseCallback) -> None:
        """Set callback for when responses are ready.

        The callback should send the response to the subagent.

        Args:
            callback: Function to call with (interaction_id, response).
        """
        self._on_response_callback = callback

    async def request_question(
        self,
        session_id: str,
        question: str,
        options: list[dict[str, Any]] | None = None,
        multi_select: bool = False,
        default_value: str | None = None,
        timeout_seconds: int = 300,
    ) -> str | list[str] | None:
        """Request a question from the user on behalf of a subagent.

        This method blocks until the user responds or timeout.

        Args:
            session_id: ID of the requesting session/agent.
            question: The question to ask.
            options: List of option dicts with label, value, description.
            multi_select: Whether multiple selections are allowed.
            default_value: Default value if user doesn't respond.
            timeout_seconds: Timeout in seconds.

        Returns:
            The user's response or None if timeout/cancelled.
        """
        interaction_id = self._generate_id()

        # Create options
        option_list = []
        if options:
            for opt in options:
                option_list.append(
                    QuestionOption(
                        label=opt.get("label", ""),
                        value=opt.get("value", opt.get("label", "")),
                        description=opt.get("description"),
                        is_recommended=opt.get("is_recommended", False),
                    )
                )

        interaction = UserInteraction(
            id=interaction_id,
            session_id=session_id,
            interaction_type=InteractionType.QUESTION,
            question=question,
            options=option_list,
            multi_select=multi_select,
            default_value=default_value,
            timeout_seconds=timeout_seconds,
        )

        self._interactions[interaction_id] = interaction
        self._save_state()

        # Create event to wait for response
        response_event = asyncio.Event()
        self._pending_responses[interaction_id] = response_event

        # Notify callback
        if self._on_interaction_callback:
            self._on_interaction_callback(interaction)

        logger.info(
            f"[USER-INTERACTION] Requesting user input for session {session_id}: {question}"
        )

        # Wait for response
        try:
            await asyncio.wait_for(response_event.wait(), timeout=timeout_seconds)
            return self._interactions[interaction_id].response
        except asyncio.TimeoutError:
            interaction.status = InteractionStatus.TIMEOUT
            self._save_state()
            logger.warning(
                f"[USER-INTERACTION] Timeout waiting for response to {interaction_id}"
            )
            return default_value

    def submit_response(
        self,
        interaction_id: str,
        response: str | list[str],
    ) -> bool:
        """Submit a user response for an interaction.

        Args:
            interaction_id: ID of the interaction.
            response: The user's response.

        Returns:
            True if response was accepted.
        """
        if interaction_id not in self._interactions:
            logger.warning(f"[USER-INTERACTION] Unknown interaction: {interaction_id}")
            return False

        interaction = self._interactions[interaction_id]
        if interaction.status != InteractionStatus.PENDING:
            logger.warning(
                f"[USER-INTERACTION] Interaction {interaction_id} is not pending"
            )
            return False

        interaction.response = response
        interaction.status = InteractionStatus.RESPONDED
        interaction.responded_at = datetime.now()
        self._save_state()

        # Notify waiting coroutine
        if interaction_id in self._pending_responses:
            self._pending_responses[interaction_id].set()
            del self._pending_responses[interaction_id]

        # Notify callback
        if self._on_response_callback:
            self._on_response_callback(interaction_id, response)

        logger.info(f"[USER-INTERACTION] Response received for {interaction_id}")
        return True

    def cancel_interaction(self, interaction_id: str) -> bool:
        """Cancel a pending interaction.

        Args:
            interaction_id: ID of the interaction.

        Returns:
            True if cancelled successfully.
        """
        if interaction_id not in self._interactions:
            return False

        interaction = self._interactions[interaction_id]
        interaction.status = InteractionStatus.CANCELLED
        self._save_state()

        # Release waiting coroutine
        if interaction_id in self._pending_responses:
            self._pending_responses[interaction_id].set()
            del self._pending_responses[interaction_id]

        logger.info(f"[USER-INTERACTION] Interaction {interaction_id} cancelled")
        return True

    def get_pending_interactions(self, session_id: str | None = None) -> list[UserInteraction]:
        """Get all pending interactions.

        Args:
            session_id: If specified, only for this session.

        Returns:
            List of pending interactions.
        """
        pending = [
            i for i in self._interactions.values() if i.status == InteractionStatus.PENDING
        ]

        if session_id:
            pending = [i for i in pending if i.session_id == session_id]

        return pending

    def pause(self) -> None:
        """Pause all interaction processing (manual pause)."""
        self._paused = True
        self._save_state()
        logger.info("[USER-INTERACTION] Paused")

    def resume(self) -> None:
        """Resume interaction processing."""
        self._paused = False
        self._save_state()
        logger.info("[USER-INTERACTION] Resumed")

    @property
    def is_paused(self) -> bool:
        """Check if paused."""
        return self._paused

    def request_interrupt(self, reason: str = "") -> None:
        """Request an interrupt (user wants to pause/stop).

        Args:
            reason: Optional reason for the interrupt.
        """
        interrupt_id = self._generate_id()
        interaction = UserInteraction(
            id=interrupt_id,
            session_id="orchestrator",
            interaction_type=InteractionType.INTERRUPT,
            question=f"Interrupt requested: {reason}" if reason else "Interrupt requested",
        )
        interaction.status = InteractionStatus.RESPONDED
        interaction.responded_at = datetime.now()

        self._interactions[interrupt_id] = interaction
        self._save_state()

        logger.info(f"[USER-INTERACTION] Interrupt requested: {reason}")

    def send_progress(
        self,
        session_id: str,
        phase: str,
        step: str,
        progress_percent: int,
        message: str,
    ) -> ProgressUpdate:
        """Send a progress update.

        Args:
            session_id: ID of the session.
            phase: Current phase name.
            step: Current step name.
            progress_percent: Progress percentage (0-100).
            message: Progress message.

        Returns:
            The ProgressUpdate object.
        """
        update = ProgressUpdate(
            session_id=session_id,
            phase=phase,
            step=step,
            progress_percent=min(100, max(0, progress_percent)),
            message=message,
        )

        logger.debug(f"[USER-INTERACTION] Progress: {update.format_for_display()}")
        return update

    def format_ask_user_question(
        self,
        question: str,
        options: list[dict[str, Any]],
        multi_select: bool = False,
    ) -> str:
        """Format a question for use with Claude's AskUserQuestion tool.

        This generates the parameters for the AskUserQuestion tool call.

        Args:
            question: The question to ask.
            options: List of option dicts.
            multi_select: Whether multiple selections allowed.

        Returns:
            JSON string for AskUserQuestion parameters.
        """
        formatted = {
            "questions": [
                {
                    "question": question,
                    "header": question[:12] if len(question) > 12 else question,
                    "options": [
                        {
                            "label": opt.get("label", ""),
                            "description": opt.get("description", ""),
                        }
                        for opt in options[:4]  # Max 4 options
                    ],
                    "multiSelect": multi_select,
                }
            ]
        }
        return json.dumps(formatted, indent=2)


# Singleton instance
_interaction_manager: UserInteractionManager | None = None


def get_user_interaction_manager(project_root: Path | None = None) -> UserInteractionManager:
    """Get the user interaction manager singleton.

    Args:
        project_root: Project root directory.

    Returns:
        The UserInteractionManager instance.
    """
    global _interaction_manager
    if _interaction_manager is None:
        _interaction_manager = UserInteractionManager(project_root=project_root)
    return _interaction_manager
