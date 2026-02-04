"""Tests for principles module."""

from __future__ import annotations

import pytest

from beyond_ralph.core.principles import (
    CORE_PRINCIPLES,
    PRINCIPLES_SUMMARY,
    AGENT_PRINCIPLES_PROMPT,
    CODE_REVIEW_PRINCIPLES_CHECKLIST,
    get_principles_for_prompt,
    get_full_principles,
    get_principles_summary,
    get_code_review_checklist,
)


class TestCorePrinciples:
    """Tests for core principles constants."""

    def test_core_principles_exists(self):
        """Test CORE_PRINCIPLES constant exists and is non-empty."""
        assert CORE_PRINCIPLES
        assert len(CORE_PRINCIPLES) > 100  # Should be substantial

    def test_core_principles_contains_key_sections(self):
        """Test CORE_PRINCIPLES contains key sections."""
        assert "NEVER FAKE RESULTS" in CORE_PRINCIPLES
        assert "HONEST ERROR HANDLING" in CORE_PRINCIPLES
        assert "TRANSPARENT OPERATIONS" in CORE_PRINCIPLES
        assert "SEPARATION OF CONCERNS" in CORE_PRINCIPLES
        assert "FAIL-SAFE DEFAULTS" in CORE_PRINCIPLES

    def test_core_principles_contains_code_examples(self):
        """Test CORE_PRINCIPLES contains code examples."""
        assert "Example of WRONG code" in CORE_PRINCIPLES
        assert "Example of CORRECT code" in CORE_PRINCIPLES

    def test_core_principles_contains_enforcement(self):
        """Test CORE_PRINCIPLES contains enforcement section."""
        assert "ENFORCEMENT" in CORE_PRINCIPLES


class TestPrinciplesSummary:
    """Tests for principles summary."""

    def test_principles_summary_exists(self):
        """Test PRINCIPLES_SUMMARY exists and is non-empty."""
        assert PRINCIPLES_SUMMARY
        assert len(PRINCIPLES_SUMMARY) > 50

    def test_principles_summary_is_short(self):
        """Test PRINCIPLES_SUMMARY is shorter than full principles."""
        assert len(PRINCIPLES_SUMMARY) < len(CORE_PRINCIPLES)

    def test_principles_summary_contains_key_points(self):
        """Test PRINCIPLES_SUMMARY contains key points."""
        assert "NEVER fake results" in PRINCIPLES_SUMMARY
        assert "NEVER silent fallbacks" in PRINCIPLES_SUMMARY
        assert "NEVER hide errors" in PRINCIPLES_SUMMARY
        assert "NEVER skip verification" in PRINCIPLES_SUMMARY
        assert "NEVER generate dishonest code" in PRINCIPLES_SUMMARY


class TestAgentPrinciplesPrompt:
    """Tests for agent principles prompt."""

    def test_agent_principles_prompt_exists(self):
        """Test AGENT_PRINCIPLES_PROMPT exists and is non-empty."""
        assert AGENT_PRINCIPLES_PROMPT
        assert len(AGENT_PRINCIPLES_PROMPT) > 100

    def test_agent_principles_prompt_format(self):
        """Test AGENT_PRINCIPLES_PROMPT is formatted for prompts."""
        # Should start with a header
        assert "##" in AGENT_PRINCIPLES_PROMPT or "#" in AGENT_PRINCIPLES_PROMPT
        # Should contain numbered points
        assert "1." in AGENT_PRINCIPLES_PROMPT
        assert "2." in AGENT_PRINCIPLES_PROMPT

    def test_agent_principles_prompt_contains_critical_instruction(self):
        """Test AGENT_PRINCIPLES_PROMPT contains critical instruction."""
        assert "CRITICAL" in AGENT_PRINCIPLES_PROMPT
        assert "MUST" in AGENT_PRINCIPLES_PROMPT


class TestCodeReviewChecklist:
    """Tests for code review checklist."""

    def test_code_review_checklist_exists(self):
        """Test CODE_REVIEW_PRINCIPLES_CHECKLIST exists and is non-empty."""
        assert CODE_REVIEW_PRINCIPLES_CHECKLIST
        assert len(CODE_REVIEW_PRINCIPLES_CHECKLIST) > 50

    def test_code_review_checklist_has_checkboxes(self):
        """Test checklist has checkbox format."""
        assert "[ ]" in CODE_REVIEW_PRINCIPLES_CHECKLIST

    def test_code_review_checklist_covers_key_areas(self):
        """Test checklist covers key compliance areas."""
        assert "fake data" in CODE_REVIEW_PRINCIPLES_CHECKLIST.lower()
        assert "exception" in CODE_REVIEW_PRINCIPLES_CHECKLIST.lower()
        assert "fallback" in CODE_REVIEW_PRINCIPLES_CHECKLIST.lower()
        assert "error" in CODE_REVIEW_PRINCIPLES_CHECKLIST.lower()


class TestPrinciplesFunctions:
    """Tests for principles getter functions."""

    def test_get_principles_for_prompt(self):
        """Test get_principles_for_prompt returns correct content."""
        result = get_principles_for_prompt()
        assert result == AGENT_PRINCIPLES_PROMPT

    def test_get_full_principles(self):
        """Test get_full_principles returns correct content."""
        result = get_full_principles()
        assert result == CORE_PRINCIPLES

    def test_get_principles_summary(self):
        """Test get_principles_summary returns correct content."""
        result = get_principles_summary()
        assert result == PRINCIPLES_SUMMARY

    def test_get_code_review_checklist(self):
        """Test get_code_review_checklist returns correct content."""
        result = get_code_review_checklist()
        assert result == CODE_REVIEW_PRINCIPLES_CHECKLIST

    def test_all_getters_return_strings(self):
        """Test all getter functions return strings."""
        assert isinstance(get_principles_for_prompt(), str)
        assert isinstance(get_full_principles(), str)
        assert isinstance(get_principles_summary(), str)
        assert isinstance(get_code_review_checklist(), str)


class TestPrinciplesIntegration:
    """Integration tests for principles usage."""

    def test_principles_can_be_concatenated(self):
        """Test principles can be added to prompts."""
        base_prompt = "You are an implementation agent."
        full_prompt = base_prompt + "\n\n" + get_principles_for_prompt()

        assert base_prompt in full_prompt
        assert "NEVER FAKE RESULTS" in full_prompt

    def test_principles_checklist_can_be_parsed(self):
        """Test checklist can be parsed for items."""
        checklist = get_code_review_checklist()
        items = [line for line in checklist.split("\n") if "[ ]" in line]

        assert len(items) >= 5  # Should have multiple items
