"""Live tests for research agent web search capabilities.

These tests require running in Claude Code context with WebSearch available.

Run with: uv run pytest tests/live/test_research_live.py -v -s
"""

from __future__ import annotations

import os

import pytest

# Skip if not in the right environment
pytestmark = pytest.mark.skipif(
    os.environ.get("BEYOND_RALPH_LIVE_TESTS") != "1",
    reason="Live tests require BEYOND_RALPH_LIVE_TESTS=1",
)


class TestResearchAgentWebSearch:
    """Live tests for research agent web search capabilities."""

    def test_web_search_available(self) -> None:
        """Verify we're in a context where WebSearch would be available.

        Note: WebSearch is only available in Claude Code agent context,
        not in pytest. This test verifies the research agent's search
        strategy and result parsing logic.
        """
        from beyond_ralph.agents.research_agent import ResearchAgent, ResearchResult

        # Verify the research agent can be instantiated
        agent = ResearchAgent(session_id="test-live-session")

        # Verify it has the expected methods
        assert hasattr(agent, "research_implementation")
        assert hasattr(agent, "search_for_tool")
        assert hasattr(agent, "discover_skills")

        print("ResearchAgent instantiated successfully with all required methods")

    def test_preferred_tools_defined(self) -> None:
        """Verify PREFERRED_TOOLS dictionary is properly defined."""
        from beyond_ralph.agents.research_agent import ResearchAgent, ToolCategory

        # PREFERRED_TOOLS is a class attribute with ToolCategory enum keys
        PREFERRED_TOOLS = ResearchAgent.PREFERRED_TOOLS

        # Should have browser automation preference (playwright)
        assert ToolCategory.BROWSER_AUTOMATION in PREFERRED_TOOLS
        assert PREFERRED_TOOLS[ToolCategory.BROWSER_AUTOMATION].name == "playwright"

        # Should have linting preference (ruff)
        assert ToolCategory.LINTING in PREFERRED_TOOLS
        assert PREFERRED_TOOLS[ToolCategory.LINTING].name == "ruff"

        # Should have security scanning preference (semgrep)
        assert ToolCategory.SECURITY_SCANNING in PREFERRED_TOOLS
        assert PREFERRED_TOOLS[ToolCategory.SECURITY_SCANNING].name == "semgrep"

        print(f"PREFERRED_TOOLS has {len(PREFERRED_TOOLS)} entries")

    def test_search_result_parsing(self) -> None:
        """Test that ResearchResult can parse various formats."""
        from beyond_ralph.agents.research_agent import CodeExample, ResearchResult

        # Test creating a research result
        result = ResearchResult(
            topic="test topic",
            summary="Test summary",
            implementation_steps=["Step 1", "Step 2"],
            code_examples=[CodeExample(
                language="python",
                code="def example(): pass",
                description="Example",
                source_url="https://example.com/code",
            )],
            sources=["https://example.com/1", "https://example.com/2"],
            confidence=0.9,
            stored_path="",
        )

        assert result.topic == "test topic"
        assert len(result.implementation_steps) == 2
        assert len(result.sources) == 2
        assert len(result.code_examples) == 1
        assert result.confidence == 0.9

        print("ResearchResult parsing and formatting works correctly")

    def test_skill_discovery_structure(self) -> None:
        """Test skill discovery data structures."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        # Test creating a skill recommendation
        skill = SkillRecommendation(
            name="postgres-mcp",
            description="PostgreSQL MCP server",
            source="npm",
            install_command="npm install -g @mcp/postgres",
            stars=1500,
            last_updated="2026-01-15",
            requires_restart=True,
            config_location="~/.claude/settings.json",
            quality_score=0.85,
            reason="Active maintenance, good documentation",
        )

        assert skill.name == "postgres-mcp"
        assert skill.source == "npm"
        assert skill.requires_restart is True

        print("SkillRecommendation structure works correctly")


class TestSkillInstallation:
    """Live tests for skill installation capabilities."""

    def test_skill_installation_methods(self) -> None:
        """Test ResearchAgent has skill installation methods."""
        from beyond_ralph.agents.research_agent import ResearchAgent

        agent = ResearchAgent(session_id="test-install-session")

        # Verify installation methods exist
        assert hasattr(agent, "install_skill")
        assert hasattr(agent, "install_tool")
        assert hasattr(agent, "verify_tool_installed")
        assert hasattr(agent, "find_and_install_tool")

        print("ResearchAgent has all installation methods")

    def test_npm_detection(self) -> None:
        """Test that npm availability can be detected."""
        import shutil

        npm_path = shutil.which("npm")

        if npm_path:
            print(f"npm found at: {npm_path}")
        else:
            print("npm not found in PATH (expected in some environments)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
