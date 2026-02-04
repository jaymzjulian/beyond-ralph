"""Tests for skills module."""

from __future__ import annotations

import pytest

from beyond_ralph.skills import (
    SKILLS,
    get_skill,
    list_skills,
    register_skills,
)


class TestSkillsConstants:
    """Tests for SKILLS constant."""

    def test_skills_dict_exists(self):
        """Test SKILLS dictionary exists."""
        assert SKILLS is not None
        assert isinstance(SKILLS, dict)

    def test_skills_has_expected_skills(self):
        """Test SKILLS contains expected skill names."""
        assert "beyond-ralph" in SKILLS
        assert "beyond-ralph-status" in SKILLS
        assert "beyond-ralph-resume" in SKILLS

    def test_skill_count(self):
        """Test correct number of skills."""
        assert len(SKILLS) == 3


class TestBeyondRalphSkill:
    """Tests for beyond-ralph skill definition."""

    def test_skill_has_name(self):
        """Test skill has name field."""
        skill = SKILLS["beyond-ralph"]
        assert skill["name"] == "beyond-ralph"

    def test_skill_has_description(self):
        """Test skill has description."""
        skill = SKILLS["beyond-ralph"]
        assert "description" in skill
        assert "autonomous" in skill["description"].lower()

    def test_skill_has_instructions(self):
        """Test skill has instructions."""
        skill = SKILLS["beyond-ralph"]
        assert "instructions" in skill
        assert len(skill["instructions"]) > 100  # Should be substantial

    def test_skill_instructions_contain_key_concepts(self):
        """Test instructions contain key methodology concepts."""
        skill = SKILLS["beyond-ralph"]
        instructions = skill["instructions"]

        assert "ORCHESTRATOR" in instructions
        assert "SPEC_INGESTION" in instructions or "Phase 1" in instructions
        assert "INTERVIEW" in instructions
        assert "quota" in instructions.lower()
        assert "checkbox" in instructions.lower()

    def test_skill_has_arguments(self):
        """Test skill has arguments defined."""
        skill = SKILLS["beyond-ralph"]
        assert "arguments" in skill
        assert isinstance(skill["arguments"], list)

    def test_skill_spec_argument(self):
        """Test skill has spec argument."""
        skill = SKILLS["beyond-ralph"]
        args = skill["arguments"]

        # Find spec argument
        spec_arg = next((a for a in args if a["name"] == "spec"), None)
        assert spec_arg is not None
        assert spec_arg["required"] is False
        assert "description" in spec_arg


class TestBeyondRalphStatusSkill:
    """Tests for beyond-ralph-status skill definition."""

    def test_skill_has_name(self):
        """Test skill has name field."""
        skill = SKILLS["beyond-ralph-status"]
        assert skill["name"] == "beyond-ralph-status"

    def test_skill_has_description(self):
        """Test skill has description."""
        skill = SKILLS["beyond-ralph-status"]
        assert "description" in skill
        assert "status" in skill["description"].lower()

    def test_skill_has_instructions(self):
        """Test skill has instructions."""
        skill = SKILLS["beyond-ralph-status"]
        assert "instructions" in skill

    def test_skill_instructions_reference_state_file(self):
        """Test instructions reference state file."""
        skill = SKILLS["beyond-ralph-status"]
        instructions = skill["instructions"]
        assert "state" in instructions.lower()


class TestBeyondRalphResumeSkill:
    """Tests for beyond-ralph-resume skill definition."""

    def test_skill_has_name(self):
        """Test skill has name field."""
        skill = SKILLS["beyond-ralph-resume"]
        assert skill["name"] == "beyond-ralph-resume"

    def test_skill_has_description(self):
        """Test skill has description."""
        skill = SKILLS["beyond-ralph-resume"]
        assert "description" in skill
        assert "resume" in skill["description"].lower()

    def test_skill_has_instructions(self):
        """Test skill has instructions."""
        skill = SKILLS["beyond-ralph-resume"]
        assert "instructions" in skill

    def test_skill_instructions_reference_quota(self):
        """Test instructions reference quota checking."""
        skill = SKILLS["beyond-ralph-resume"]
        instructions = skill["instructions"]
        assert "quota" in instructions.lower()


class TestRegisterSkills:
    """Tests for register_skills function."""

    def test_register_skills_returns_dict(self):
        """Test register_skills returns dictionary."""
        result = register_skills()
        assert isinstance(result, dict)

    def test_register_skills_returns_skills(self):
        """Test register_skills returns the SKILLS dictionary."""
        result = register_skills()
        assert result == SKILLS

    def test_register_skills_contains_all_skills(self):
        """Test registered skills contain all expected skills."""
        result = register_skills()
        assert "beyond-ralph" in result
        assert "beyond-ralph-status" in result
        assert "beyond-ralph-resume" in result


class TestGetSkill:
    """Tests for get_skill function."""

    def test_get_skill_returns_skill(self):
        """Test get_skill returns correct skill."""
        skill = get_skill("beyond-ralph")
        assert skill is not None
        assert skill["name"] == "beyond-ralph"

    def test_get_skill_returns_none_for_unknown(self):
        """Test get_skill returns None for unknown skill."""
        skill = get_skill("nonexistent-skill")
        assert skill is None

    def test_get_skill_status(self):
        """Test get_skill for status skill."""
        skill = get_skill("beyond-ralph-status")
        assert skill is not None
        assert skill["name"] == "beyond-ralph-status"

    def test_get_skill_resume(self):
        """Test get_skill for resume skill."""
        skill = get_skill("beyond-ralph-resume")
        assert skill is not None
        assert skill["name"] == "beyond-ralph-resume"


class TestListSkills:
    """Tests for list_skills function."""

    def test_list_skills_returns_list(self):
        """Test list_skills returns list."""
        result = list_skills()
        assert isinstance(result, list)

    def test_list_skills_contains_all_skills(self):
        """Test list_skills contains all skill names."""
        result = list_skills()
        assert "beyond-ralph" in result
        assert "beyond-ralph-status" in result
        assert "beyond-ralph-resume" in result

    def test_list_skills_count(self):
        """Test list_skills returns correct count."""
        result = list_skills()
        assert len(result) == 3
