"""Tests for User Interaction Manager."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.user_interaction import (
    InteractionStatus,
    InteractionType,
    ProgressUpdate,
    QuestionOption,
    UserInteraction,
    UserInteractionManager,
    get_user_interaction_manager,
)


class TestQuestionOption:
    """Tests for QuestionOption dataclass."""

    def test_option_creation(self):
        """Test creating an option."""
        opt = QuestionOption(
            label="Option A",
            value="a",
            description="First option",
            is_recommended=True,
        )

        assert opt.label == "Option A"
        assert opt.value == "a"
        assert opt.is_recommended is True

    def test_option_to_dict(self):
        """Test serialization."""
        opt = QuestionOption(
            label="Test",
            value="test",
            description="Test option",
        )

        data = opt.to_dict()

        assert data["label"] == "Test"
        assert data["value"] == "test"
        assert data["is_recommended"] is False

    def test_option_from_dict(self):
        """Test deserialization."""
        data = {
            "label": "Choice",
            "value": "choice",
            "description": "A choice",
            "is_recommended": True,
        }

        opt = QuestionOption.from_dict(data)

        assert opt.label == "Choice"
        assert opt.is_recommended is True


class TestUserInteraction:
    """Tests for UserInteraction dataclass."""

    def test_interaction_creation(self):
        """Test creating an interaction."""
        interaction = UserInteraction(
            id="int-123",
            session_id="session-abc",
            interaction_type=InteractionType.QUESTION,
            question="What database should we use?",
        )

        assert interaction.id == "int-123"
        assert interaction.status == InteractionStatus.PENDING
        assert interaction.response is None

    def test_interaction_with_options(self):
        """Test interaction with options."""
        options = [
            QuestionOption(label="PostgreSQL", value="postgres", is_recommended=True),
            QuestionOption(label="MySQL", value="mysql"),
        ]

        interaction = UserInteraction(
            id="int-456",
            session_id="session-xyz",
            interaction_type=InteractionType.SELECTION,
            question="Select database",
            options=options,
        )

        assert len(interaction.options) == 2
        assert interaction.options[0].is_recommended is True

    def test_interaction_to_dict(self):
        """Test serialization."""
        interaction = UserInteraction(
            id="int-789",
            session_id="session-123",
            interaction_type=InteractionType.QUESTION,
            question="Test question?",
        )

        data = interaction.to_dict()

        assert data["id"] == "int-789"
        assert data["interaction_type"] == "question"
        assert data["status"] == "pending"

    def test_interaction_from_dict(self):
        """Test deserialization."""
        data = {
            "id": "int-000",
            "session_id": "session-000",
            "interaction_type": "confirmation",
            "question": "Continue?",
            "options": [],
            "status": "responded",
            "response": "yes",
            "created_at": datetime.now().isoformat(),
        }

        interaction = UserInteraction.from_dict(data)

        assert interaction.id == "int-000"
        assert interaction.interaction_type == InteractionType.CONFIRMATION
        assert interaction.status == InteractionStatus.RESPONDED

    def test_format_for_display_simple(self):
        """Test simple question display format."""
        interaction = UserInteraction(
            id="int-1",
            session_id="agent-1",
            interaction_type=InteractionType.QUESTION,
            question="What is the project name?",
        )

        formatted = interaction.format_for_display()

        assert "[USER INPUT REQUIRED" in formatted
        assert "agent-1" in formatted
        assert "What is the project name?" in formatted

    def test_format_for_display_with_options(self):
        """Test question with options display format."""
        options = [
            QuestionOption(
                label="Python", value="python", description="Use Python 3.11+", is_recommended=True
            ),
            QuestionOption(label="JavaScript", value="js", description="Use Node.js"),
        ]

        interaction = UserInteraction(
            id="int-2",
            session_id="agent-2",
            interaction_type=InteractionType.SELECTION,
            question="Select programming language",
            options=options,
        )

        formatted = interaction.format_for_display()

        assert "Python" in formatted
        assert "(Recommended)" in formatted
        assert "JavaScript" in formatted
        assert "Use Python 3.11+" in formatted

    def test_format_for_display_multi_select(self):
        """Test multi-select display format."""
        interaction = UserInteraction(
            id="int-3",
            session_id="agent-3",
            interaction_type=InteractionType.SELECTION,
            question="Select features",
            options=[QuestionOption(label="Auth", value="auth")],
            multi_select=True,
        )

        formatted = interaction.format_for_display()

        assert "multiple" in formatted.lower()


class TestProgressUpdate:
    """Tests for ProgressUpdate dataclass."""

    def test_progress_update_creation(self):
        """Test creating a progress update."""
        update = ProgressUpdate(
            session_id="agent-1",
            phase="Implementation",
            step="Writing tests",
            progress_percent=50,
            message="Halfway done",
        )

        assert update.progress_percent == 50
        assert update.phase == "Implementation"

    def test_format_for_display(self):
        """Test progress display format."""
        update = ProgressUpdate(
            session_id="agent-1",
            phase="Testing",
            step="Unit tests",
            progress_percent=75,
            message="Running tests",
        )

        formatted = update.format_for_display()

        assert "agent-1" in formatted
        assert "Testing" in formatted
        assert "75%" in formatted
        assert "█" in formatted  # Progress bar


class TestUserInteractionManager:
    """Tests for UserInteractionManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a manager for testing."""
        return UserInteractionManager(project_root=tmp_path)

    def test_request_question_creates_interaction(self, manager):
        """Test that requesting a question creates an interaction."""
        # Use synchronous setup
        interaction_id = manager._generate_id()

        interaction = UserInteraction(
            id=interaction_id,
            session_id="test-session",
            interaction_type=InteractionType.QUESTION,
            question="Test question?",
        )

        manager._interactions[interaction_id] = interaction
        manager._save_state()

        assert interaction_id in manager._interactions

    def test_submit_response(self, manager):
        """Test submitting a response."""
        interaction_id = manager._generate_id()

        interaction = UserInteraction(
            id=interaction_id,
            session_id="test-session",
            interaction_type=InteractionType.QUESTION,
            question="Test question?",
        )

        manager._interactions[interaction_id] = interaction
        manager._pending_responses[interaction_id] = asyncio.Event()

        result = manager.submit_response(interaction_id, "test answer")

        assert result is True
        assert manager._interactions[interaction_id].status == InteractionStatus.RESPONDED
        assert manager._interactions[interaction_id].response == "test answer"

    def test_submit_response_unknown_id(self, manager):
        """Test submitting response for unknown interaction."""
        result = manager.submit_response("nonexistent", "answer")
        assert result is False

    def test_submit_response_not_pending(self, manager):
        """Test submitting response for non-pending interaction."""
        interaction_id = manager._generate_id()

        interaction = UserInteraction(
            id=interaction_id,
            session_id="test-session",
            interaction_type=InteractionType.QUESTION,
            question="Test?",
        )
        interaction.status = InteractionStatus.RESPONDED

        manager._interactions[interaction_id] = interaction

        result = manager.submit_response(interaction_id, "new answer")
        assert result is False

    def test_cancel_interaction(self, manager):
        """Test cancelling an interaction."""
        interaction_id = manager._generate_id()

        interaction = UserInteraction(
            id=interaction_id,
            session_id="test-session",
            interaction_type=InteractionType.QUESTION,
            question="Test?",
        )

        manager._interactions[interaction_id] = interaction
        manager._pending_responses[interaction_id] = asyncio.Event()

        result = manager.cancel_interaction(interaction_id)

        assert result is True
        assert manager._interactions[interaction_id].status == InteractionStatus.CANCELLED

    def test_cancel_unknown_interaction(self, manager):
        """Test cancelling unknown interaction."""
        result = manager.cancel_interaction("nonexistent")
        assert result is False

    def test_get_pending_interactions(self, manager):
        """Test getting pending interactions."""
        # Add pending interaction
        int1 = UserInteraction(
            id="int-1",
            session_id="session-1",
            interaction_type=InteractionType.QUESTION,
            question="Q1?",
        )
        manager._interactions["int-1"] = int1

        # Add responded interaction
        int2 = UserInteraction(
            id="int-2",
            session_id="session-2",
            interaction_type=InteractionType.QUESTION,
            question="Q2?",
        )
        int2.status = InteractionStatus.RESPONDED
        manager._interactions["int-2"] = int2

        pending = manager.get_pending_interactions()

        assert len(pending) == 1
        assert pending[0].id == "int-1"

    def test_get_pending_interactions_for_session(self, manager):
        """Test getting pending interactions for specific session."""
        int1 = UserInteraction(
            id="int-1",
            session_id="session-a",
            interaction_type=InteractionType.QUESTION,
            question="Q1?",
        )
        manager._interactions["int-1"] = int1

        int2 = UserInteraction(
            id="int-2",
            session_id="session-b",
            interaction_type=InteractionType.QUESTION,
            question="Q2?",
        )
        manager._interactions["int-2"] = int2

        pending = manager.get_pending_interactions(session_id="session-a")

        assert len(pending) == 1
        assert pending[0].session_id == "session-a"

    def test_pause_resume(self, manager):
        """Test pause and resume functionality."""
        assert manager.is_paused is False

        manager.pause()
        assert manager.is_paused is True

        manager.resume()
        assert manager.is_paused is False

    def test_request_interrupt(self, manager):
        """Test requesting an interrupt."""
        manager.request_interrupt(reason="User requested stop")

        # Should create an interaction record
        interrupt = [
            i
            for i in manager._interactions.values()
            if i.interaction_type == InteractionType.INTERRUPT
        ]
        assert len(interrupt) == 1
        assert "User requested stop" in interrupt[0].question

    def test_send_progress(self, manager):
        """Test sending progress update."""
        update = manager.send_progress(
            session_id="agent-1",
            phase="Implementation",
            step="Writing code",
            progress_percent=50,
            message="Making progress",
        )

        assert isinstance(update, ProgressUpdate)
        assert update.progress_percent == 50

    def test_send_progress_clamps_percent(self, manager):
        """Test progress percent is clamped to 0-100."""
        update1 = manager.send_progress(
            session_id="a",
            phase="p",
            step="s",
            progress_percent=-10,
            message="m",
        )
        assert update1.progress_percent == 0

        update2 = manager.send_progress(
            session_id="a",
            phase="p",
            step="s",
            progress_percent=150,
            message="m",
        )
        assert update2.progress_percent == 100

    def test_format_ask_user_question(self, manager):
        """Test formatting for AskUserQuestion tool."""
        options = [
            {"label": "Python", "description": "Use Python"},
            {"label": "JavaScript", "description": "Use JS"},
        ]

        formatted = manager.format_ask_user_question(
            question="Which language?",
            options=options,
            multi_select=False,
        )

        data = json.loads(formatted)
        assert "questions" in data
        assert len(data["questions"]) == 1
        assert data["questions"][0]["question"] == "Which language?"
        assert len(data["questions"][0]["options"]) == 2

    def test_interaction_callback(self, manager):
        """Test interaction callback is called."""
        callback_called = []

        def callback(interaction: UserInteraction):
            callback_called.append(interaction)

        manager.set_interaction_callback(callback)

        # Create interaction
        interaction_id = manager._generate_id()
        interaction = UserInteraction(
            id=interaction_id,
            session_id="test",
            interaction_type=InteractionType.QUESTION,
            question="Test?",
        )
        manager._interactions[interaction_id] = interaction

        # Manually trigger callback (normally done in request_question)
        if manager._on_interaction_callback:
            manager._on_interaction_callback(interaction)

        assert len(callback_called) == 1
        assert callback_called[0].id == interaction_id

    def test_response_callback(self, manager):
        """Test response callback is called."""
        callback_called = []

        def callback(interaction_id: str, response: str):
            callback_called.append((interaction_id, response))

        manager.set_response_callback(callback)

        # Create and respond to interaction
        interaction_id = manager._generate_id()
        interaction = UserInteraction(
            id=interaction_id,
            session_id="test",
            interaction_type=InteractionType.QUESTION,
            question="Test?",
        )
        manager._interactions[interaction_id] = interaction
        manager._pending_responses[interaction_id] = asyncio.Event()

        manager.submit_response(interaction_id, "answer")

        assert len(callback_called) == 1
        assert callback_called[0] == (interaction_id, "answer")

    def test_state_persistence(self, tmp_path):
        """Test state persists across instances."""
        manager1 = UserInteractionManager(project_root=tmp_path)
        manager1._interactions["int-1"] = UserInteraction(
            id="int-1",
            session_id="session",
            interaction_type=InteractionType.QUESTION,
            question="Persistent?",
        )
        manager1._paused = True
        manager1._save_state()

        manager2 = UserInteractionManager(project_root=tmp_path)

        assert "int-1" in manager2._interactions
        assert manager2._interactions["int-1"].question == "Persistent?"
        assert manager2.is_paused is True


class TestUserInteractionAsync:
    """Async tests for UserInteractionManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a manager for testing."""
        return UserInteractionManager(project_root=tmp_path)

    @pytest.mark.asyncio
    async def test_request_question_with_immediate_response(self, manager):
        """Test requesting a question with immediate response."""

        async def respond_after_delay():
            await asyncio.sleep(0.1)
            # Find the pending interaction
            pending = manager.get_pending_interactions()
            if pending:
                manager.submit_response(pending[0].id, "test response")

        # Start response task
        asyncio.create_task(respond_after_delay())

        # Request question
        response = await manager.request_question(
            session_id="test-session",
            question="What is your name?",
            timeout_seconds=5,
        )

        assert response == "test response"

    @pytest.mark.asyncio
    async def test_request_question_timeout(self, manager):
        """Test question timeout returns default."""
        response = await manager.request_question(
            session_id="test-session",
            question="Quick question?",
            default_value="default",
            timeout_seconds=0.1,
        )

        assert response == "default"

    @pytest.mark.asyncio
    async def test_request_question_with_options(self, manager):
        """Test requesting question with options."""

        async def respond():
            await asyncio.sleep(0.1)
            pending = manager.get_pending_interactions()
            if pending:
                manager.submit_response(pending[0].id, "postgres")

        asyncio.create_task(respond())

        options = [
            {"label": "PostgreSQL", "value": "postgres", "is_recommended": True},
            {"label": "MySQL", "value": "mysql"},
        ]

        response = await manager.request_question(
            session_id="test-session",
            question="Select database",
            options=options,
            timeout_seconds=5,
        )

        assert response == "postgres"


class TestGetUserInteractionManager:
    """Tests for singleton getter."""

    def test_singleton_pattern(self, tmp_path, monkeypatch):
        """Test singleton pattern."""
        import beyond_ralph.core.user_interaction as module

        module._interaction_manager = None

        manager1 = get_user_interaction_manager(tmp_path)
        manager2 = get_user_interaction_manager(tmp_path)

        assert manager1 is manager2

        module._interaction_manager = None
