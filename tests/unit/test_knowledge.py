"""Unit tests for Knowledge Base."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.knowledge import (
    KnowledgeBase,
    KnowledgeEntry,
    create_knowledge_entry,
)


@pytest.fixture
def temp_kb_path(tmp_path: Path) -> Path:
    """Create a temporary knowledge base directory."""
    kb_path = tmp_path / "knowledge"
    kb_path.mkdir()
    return kb_path


@pytest.fixture
def kb(temp_kb_path: Path) -> KnowledgeBase:
    """Create a knowledge base with temp directory."""
    return KnowledgeBase(path=temp_kb_path)


class TestKnowledgeEntry:
    """Tests for KnowledgeEntry."""

    def test_to_markdown(self) -> None:
        """Test converting entry to markdown."""
        entry = KnowledgeEntry(
            uuid="abc123",
            created_by_session="session-xyz",
            created_at=datetime(2024, 2, 1, 10, 30),
            category="testing",
            tags=["auth", "jwt"],
            title="Test Entry",
            content="# Test Entry\n\nThis is test content.",
        )

        md = entry.to_markdown()

        assert "uuid: abc123" in md
        assert "created_by_session: session-xyz" in md
        assert "category: testing" in md
        assert "- auth" in md
        assert "- jwt" in md
        assert "# Test Entry" in md
        assert "This is test content." in md

    def test_from_file(self, tmp_path: Path) -> None:
        """Test parsing entry from file."""
        content = """---
uuid: test123
created_by_session: session-abc
date: 2024-02-01T10:30:00
category: implementation
tags:
  - python
  - testing
---

# My Test Entry

This is the content.
"""
        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        entry = KnowledgeEntry.from_file(file_path)

        assert entry.uuid == "test123"
        assert entry.created_by_session == "session-abc"
        assert entry.category == "implementation"
        assert "python" in entry.tags
        assert entry.title == "My Test Entry"
        assert "This is the content." in entry.content


class TestKnowledgeBase:
    """Tests for KnowledgeBase."""

    def test_write_and_read(self, kb: KnowledgeBase) -> None:
        """Test writing and reading an entry."""
        entry = create_knowledge_entry(
            title="Test Knowledge",
            content="Some important information.",
            session_id="session-123",
            category="design",
            tags=["architecture"],
        )

        uuid = kb.write(entry)
        assert uuid

        # Read back
        retrieved = kb.read(uuid)
        assert retrieved is not None
        assert retrieved.title == "Test Knowledge"
        assert "Some important information" in retrieved.content

    def test_search(self, kb: KnowledgeBase) -> None:
        """Test searching the knowledge base."""
        # Write some entries
        entry1 = create_knowledge_entry(
            title="Python Testing",
            content="How to test Python code.",
            session_id="s1",
            tags=["python", "testing"],
        )
        entry2 = create_knowledge_entry(
            title="JavaScript Testing",
            content="How to test JavaScript code.",
            session_id="s2",
            tags=["javascript", "testing"],
        )

        kb.write(entry1)
        kb.write(entry2)

        # Search
        results = kb.search("python")
        assert len(results) == 1
        assert results[0].title == "Python Testing"

        # Search by content
        results = kb.search("JavaScript")
        assert len(results) == 1
        assert results[0].title == "JavaScript Testing"

        # Search by tag
        results = kb.search("testing")
        assert len(results) == 2

    def test_get_by_session(self, kb: KnowledgeBase) -> None:
        """Test getting entries by session."""
        entry1 = create_knowledge_entry(
            title="Entry 1",
            content="Content 1",
            session_id="session-aaa",
        )
        entry2 = create_knowledge_entry(
            title="Entry 2",
            content="Content 2",
            session_id="session-bbb",
        )

        kb.write(entry1)
        kb.write(entry2)

        results = kb.get_by_session("session-aaa")
        assert len(results) == 1
        assert results[0].title == "Entry 1"

    def test_categories_and_tags(self, kb: KnowledgeBase) -> None:
        """Test getting all categories and tags."""
        entry1 = create_knowledge_entry(
            title="Entry 1",
            content="Content",
            session_id="s1",
            category="design",
            tags=["arch", "patterns"],
        )
        entry2 = create_knowledge_entry(
            title="Entry 2",
            content="Content",
            session_id="s2",
            category="implementation",
            tags=["code", "patterns"],
        )

        kb.write(entry1)
        kb.write(entry2)

        categories = kb.get_all_categories()
        assert "design" in categories
        assert "implementation" in categories

        tags = kb.get_all_tags()
        assert "arch" in tags
        assert "code" in tags
        assert "patterns" in tags


class TestCreateKnowledgeEntry:
    """Tests for create_knowledge_entry helper."""

    def test_creates_valid_entry(self) -> None:
        """Test helper creates valid entry."""
        entry = create_knowledge_entry(
            title="My Entry",
            content="The content here.",
            session_id="sess-123",
            category="notes",
            tags=["important"],
            questions=["What about X?"],
        )

        assert entry.uuid
        assert entry.title == "My Entry"
        assert entry.created_by_session == "sess-123"
        assert entry.category == "notes"
        assert "important" in entry.tags
        assert "What about X?" in entry.questions
        assert "# My Entry" in entry.content
