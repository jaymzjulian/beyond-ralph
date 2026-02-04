# Module 14: User Interaction - Specification

> User Interaction: Route AskUserQuestion from subagents to main Claude Code session.

---

## Overview

The User Interaction module manages the routing of user questions and responses between subagents and the main Claude Code session. It provides a bridge for the interview agent and any other agent that needs user input.

**Key Principle**: All user interaction flows through the main Claude Code session. Subagents request questions, the orchestrator routes them to the user, and responses flow back.

---

## Location

`src/beyond_ralph/core/user_interaction.py`

---

## Components

### 14.1 User Interaction Manager

**Purpose**: Route questions and responses between agents and users.

**Interface**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

class QuestionStatus(Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class PendingQuestion:
    """A question pending user response."""
    question_id: str
    agent_session: str
    question_text: str
    options: list[str]
    asked_at: datetime
    timeout: Optional[int] = None  # seconds, None = no timeout
    status: QuestionStatus = QuestionStatus.PENDING
    response: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if question has timed out."""
        if self.timeout is None:
            return False
        elapsed = (datetime.now() - self.asked_at).total_seconds()
        return elapsed > self.timeout

@dataclass
class ProgressUpdate:
    """Progress update to show user."""
    phase: int
    phase_name: str
    message: str
    percent: float
    agent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

class UserInteractionManager:
    """Routes user interactions between agents and Claude Code UI."""

    def __init__(self) -> None:
        """Initialize interaction manager."""
        self.pending_questions: dict[str, PendingQuestion] = {}
        self.responses: dict[str, str] = {}
        self._paused: bool = False

    def request_question(
        self,
        agent_session: str,
        question: str,
        options: list[str],
        timeout: Optional[int] = None
    ) -> str:
        """Request a question be asked to user.

        Args:
            agent_session: UUID of the requesting agent session.
            question: The question text to ask.
            options: Available choices (empty for open-ended).
            timeout: Optional timeout in seconds.

        Returns:
            Question ID for tracking the response.

        Note:
            This creates a pending question that the orchestrator
            should route to Claude Code's AskUserQuestion tool.
        """
        question_id = f"q-{uuid.uuid4().hex[:8]}"
        self.pending_questions[question_id] = PendingQuestion(
            question_id=question_id,
            agent_session=agent_session,
            question_text=question,
            options=options,
            asked_at=datetime.now(),
            timeout=timeout
        )
        return question_id

    def submit_response(
        self,
        question_id: str,
        response: str
    ) -> None:
        """Submit user's response to pending question.

        Args:
            question_id: ID of the question being answered.
            response: User's response text.

        Updates the pending question status and stores response.
        """
        if question_id in self.pending_questions:
            q = self.pending_questions[question_id]
            q.status = QuestionStatus.ANSWERED
            q.response = response
            self.responses[question_id] = response

    def get_response(self, question_id: str) -> Optional[str]:
        """Get response for question (may be None if pending).

        Args:
            question_id: ID of the question.

        Returns:
            Response text if answered, None if still pending.
        """
        return self.responses.get(question_id)

    async def wait_for_response(
        self,
        question_id: str,
        poll_interval: float = 0.5
    ) -> str:
        """Wait for response to be submitted.

        Args:
            question_id: ID of the question.
            poll_interval: Seconds between checks.

        Returns:
            Response text when available.

        Raises:
            TimeoutError: If question expires before response.
        """
        import asyncio

        question = self.pending_questions.get(question_id)
        if not question:
            raise ValueError(f"Unknown question: {question_id}")

        while True:
            if question.is_expired():
                question.status = QuestionStatus.EXPIRED
                raise TimeoutError(f"Question {question_id} expired")

            response = self.get_response(question_id)
            if response is not None:
                return response

            await asyncio.sleep(poll_interval)

    def get_pending_questions(self) -> list[PendingQuestion]:
        """Get all pending questions awaiting user response."""
        return [
            q for q in self.pending_questions.values()
            if q.status == QuestionStatus.PENDING and not q.is_expired()
        ]

    def cancel_question(self, question_id: str) -> None:
        """Cancel a pending question."""
        if question_id in self.pending_questions:
            self.pending_questions[question_id].status = QuestionStatus.CANCELLED

    def request_interrupt(self) -> None:
        """Request user interrupt current operation.

        Sets a flag that the orchestrator checks periodically.
        """
        # This would integrate with Claude Code's interrupt mechanism
        pass

    def send_progress(self, update: ProgressUpdate) -> None:
        """Send progress update to user.

        Args:
            update: Progress information to display.

        Formats and outputs progress message.
        """
        prefix = f"[AGENT:{update.agent_id}]" if update.agent_id else "[BEYOND-RALPH]"
        print(f"{prefix} Phase {update.phase}: {update.phase_name} - {update.message} ({update.percent:.1f}%)")

    def pause(self) -> None:
        """Pause user interaction (for quota limits)."""
        self._paused = True

    def resume(self) -> None:
        """Resume user interaction."""
        self._paused = False

    def is_paused(self) -> bool:
        """Check if interaction is paused."""
        return self._paused

    def cleanup_expired(self) -> int:
        """Clean up expired questions.

        Returns:
            Number of questions cleaned up.
        """
        count = 0
        for q in list(self.pending_questions.values()):
            if q.is_expired() and q.status == QuestionStatus.PENDING:
                q.status = QuestionStatus.EXPIRED
                count += 1
        return count


def get_user_interaction_manager() -> UserInteractionManager:
    """Get singleton user interaction manager instance."""
    global _user_interaction_manager
    if '_user_interaction_manager' not in globals():
        _user_interaction_manager = UserInteractionManager()
    return _user_interaction_manager
```

---

## Integration with AskUserQuestion

When a subagent needs user input:

```python
# In agent execution
user_manager = get_user_interaction_manager()

# Request question from orchestrator
question_id = user_manager.request_question(
    agent_session=self.session_id,
    question="What authentication method should we use?",
    options=["OAuth2", "JWT", "API Keys", "Other"]
)

# Orchestrator routes to AskUserQuestion and waits
response = await user_manager.wait_for_response(question_id)

# Agent continues with response
auth_method = response
```

---

## Integration with Orchestrator

```python
# In orchestrator main loop
user_manager = get_user_interaction_manager()

# Check for pending questions from agents
pending = user_manager.get_pending_questions()
for question in pending:
    # Route to Claude Code AskUserQuestion
    response = await ask_user_question(
        question.question_text,
        options=question.options
    )
    user_manager.submit_response(question.question_id, response)
```

---

## Output Format

User interaction messages are prefixed for clarity:

```
[BEYOND-RALPH] Phase 2: Interview - Starting user interview
[AGENT:interview-abc123] I need to ask you some questions about requirements.
[USER INPUT REQUIRED]
<AskUserQuestion UI appears>
... user answers ...
[AGENT:interview-abc123] Thank you. Moving to next question...
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 15 (Notifications) | Alerting when blocked on user input |
| Module 16 (Utils) | UUID generation, logging |

---

## Error Handling

```python
class UserInteractionError(BeyondRalphError):
    """User interaction errors."""

class QuestionTimeoutError(UserInteractionError):
    """Question expired without response."""

class InvalidQuestionError(UserInteractionError):
    """Invalid question or question ID."""

class InteractionPausedError(UserInteractionError):
    """Cannot interact while paused."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Question creation, response handling |
| Integration tests | Full question/response flow |
| Mock tests | Mocked Claude Code AskUserQuestion |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
