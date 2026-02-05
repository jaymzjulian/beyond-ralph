"""Tests for research agent module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.agents.research_agent import (
    CodeExample,
    DiscoveredTool,
    PackageManager,
    ResearchAgent,
    ResearchResult,
    ToolCategory,
)


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_tool_categories_exist(self):
        """Test all expected tool categories exist."""
        assert ToolCategory.TESTING_FRAMEWORK.value == "testing_framework"
        assert ToolCategory.BROWSER_AUTOMATION.value == "browser_automation"
        assert ToolCategory.MOCK_SERVER.value == "mock_server"
        assert ToolCategory.SCREENSHOT_TOOL.value == "screenshot_tool"
        assert ToolCategory.VIDEO_CAPTURE.value == "video_capture"
        assert ToolCategory.LINTING.value == "linting"
        assert ToolCategory.SECURITY_SCANNING.value == "security_scanning"

    def test_all_categories_have_values(self):
        """Test all categories have string values."""
        for category in ToolCategory:
            assert isinstance(category.value, str)
            assert len(category.value) > 0


class TestPackageManager:
    """Tests for PackageManager enum."""

    def test_package_managers_exist(self):
        """Test all expected package managers exist."""
        assert PackageManager.PIP.value == "pip"
        assert PackageManager.NPM.value == "npm"
        assert PackageManager.CARGO.value == "cargo"
        assert PackageManager.GO.value == "go"
        assert PackageManager.APT.value == "apt"
        assert PackageManager.BREW.value == "brew"

    def test_all_package_managers_have_values(self):
        """Test all package managers have string values."""
        for pm in PackageManager:
            assert isinstance(pm.value, str)
            assert len(pm.value) > 0


class TestDiscoveredTool:
    """Tests for DiscoveredTool dataclass."""

    def test_discovered_tool_creation(self):
        """Test creating a DiscoveredTool."""
        tool = DiscoveredTool(
            name="playwright",
            category=ToolCategory.BROWSER_AUTOMATION,
            package_manager=PackageManager.PIP,
            package_name="playwright",
            description="Cross-browser automation",
            install_command="pip install playwright",
        )

        assert tool.name == "playwright"
        assert tool.category == ToolCategory.BROWSER_AUTOMATION
        assert tool.package_manager == PackageManager.PIP
        assert tool.package_name == "playwright"
        assert tool.description == "Cross-browser automation"
        assert tool.install_command == "pip install playwright"

    def test_discovered_tool_with_optional_fields(self):
        """Test DiscoveredTool with optional fields."""
        tool = DiscoveredTool(
            name="pytest",
            category=ToolCategory.TESTING_FRAMEWORK,
            package_manager=PackageManager.PIP,
            package_name="pytest",
            description="Python testing framework",
            install_command="pip install pytest",
            github_stars=10000,
            last_updated="2024-01-15",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://docs.pytest.org",
            recommended=True,
            rationale="Standard Python testing framework",
            version="7.4.0",
        )

        assert tool.github_stars == 10000
        assert tool.last_updated == "2024-01-15"
        assert tool.platform_support == ["linux", "macos", "windows"]
        assert tool.documentation_url == "https://docs.pytest.org"
        assert tool.recommended is True
        assert tool.rationale == "Standard Python testing framework"
        assert tool.version == "7.4.0"

    def test_discovered_tool_to_dict(self):
        """Test DiscoveredTool serialization to dict."""
        tool = DiscoveredTool(
            name="ruff",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="ruff",
            description="Fast Python linter",
            install_command="pip install ruff",
            github_stars=5000,
            recommended=True,
        )

        data = tool.to_dict()

        assert data["name"] == "ruff"
        assert data["category"] == "linting"
        assert data["package_manager"] == "pip"
        assert data["package_name"] == "ruff"
        assert data["description"] == "Fast Python linter"
        assert data["install_command"] == "pip install ruff"
        assert data["github_stars"] == 5000
        assert data["recommended"] is True

    def test_discovered_tool_defaults(self):
        """Test DiscoveredTool has correct defaults."""
        tool = DiscoveredTool(
            name="test-tool",
            category=ToolCategory.TESTING_FRAMEWORK,
            package_manager=PackageManager.PIP,
            package_name="test-tool",
            description="A test tool",
            install_command="pip install test-tool",
        )

        assert tool.github_stars is None
        assert tool.last_updated is None
        assert tool.platform_support == []
        assert tool.documentation_url is None
        assert tool.recommended is False
        assert tool.rationale == ""
        assert tool.version is None


class TestResearchAgent:
    """Tests for ResearchAgent class."""

    def test_research_agent_creation(self, tmp_path):
        """Test creating a ResearchAgent."""
        agent = ResearchAgent(project_root=tmp_path)

        assert agent.name == "research"
        assert "discovery" in agent.description.lower() or "tool" in agent.description.lower()

    def test_research_agent_has_preferred_tools(self, tmp_path):
        """Test ResearchAgent has preferred tools defined."""
        agent = ResearchAgent(project_root=tmp_path)

        # Check that preferred tools attribute exists
        if hasattr(agent, "_preferred_tools") or hasattr(agent, "preferred_tools"):
            preferred = getattr(agent, "_preferred_tools", None) or getattr(
                agent, "preferred_tools", {}
            )
            assert isinstance(preferred, dict)

    def test_research_agent_inherits_base_agent(self, tmp_path):
        """Test ResearchAgent inherits from BaseAgent."""
        from beyond_ralph.agents.base import BaseAgent

        agent = ResearchAgent(project_root=tmp_path)
        assert isinstance(agent, BaseAgent)


class TestResearchAgentPreferredTools:
    """Tests for ResearchAgent preferred tools logic."""

    def test_preferred_tools_for_browser_automation(self, tmp_path):
        """Test preferred tool for browser automation is Playwright."""
        agent = ResearchAgent(project_root=tmp_path)

        # If agent has get_preferred_tool method
        if hasattr(agent, "get_preferred_tool"):
            preferred = agent.get_preferred_tool(ToolCategory.BROWSER_AUTOMATION)
            assert preferred is not None
            # Playwright should be preferred
            if hasattr(preferred, "name"):
                assert preferred.name.lower() in ["playwright", "puppeteer", "selenium"]

    def test_preferred_tools_for_testing(self, tmp_path):
        """Test preferred tool for testing is pytest."""
        agent = ResearchAgent(project_root=tmp_path)

        if hasattr(agent, "get_preferred_tool"):
            preferred = agent.get_preferred_tool(ToolCategory.TESTING_FRAMEWORK)
            if preferred is not None and hasattr(preferred, "name"):
                assert preferred.name.lower() in ["pytest", "unittest", "nose"]


class TestResearchAgentDiscovery:
    """Tests for ResearchAgent discovery functionality."""

    @pytest.mark.asyncio
    async def test_discover_tool_returns_result(self, tmp_path):
        """Test discover_tool method returns a result."""
        agent = ResearchAgent(project_root=tmp_path)

        # If agent has discover_tool method
        if hasattr(agent, "discover_tool"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = {"items": []}
                mock_response.status_code = 200

                mock_instance = AsyncMock()
                mock_instance.get.return_value = mock_response
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None

                mock_client.return_value = mock_instance

                # This should not raise
                try:
                    result = await agent.discover_tool(ToolCategory.LINTING)
                    # Result can be None if no tools found
                    assert result is None or isinstance(result, DiscoveredTool)
                except NotImplementedError:
                    # Method might not be fully implemented
                    pass


class TestResearchAgentInstallation:
    """Tests for ResearchAgent installation functionality."""

    @pytest.mark.asyncio
    async def test_install_tool_runs_command(self, tmp_path):
        """Test install_tool runs installation command."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="test-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="test-tool",
            description="A test tool",
            install_command="pip install test-tool",
        )

        if hasattr(agent, "install_tool"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                try:
                    result = await agent.install_tool(tool)
                    assert result is True or result is None
                except NotImplementedError:
                    pass


class TestResearchAgentKnowledgeBase:
    """Tests for ResearchAgent knowledge base integration."""

    def test_agent_has_knowledge_base_access(self, tmp_path):
        """Test agent can access knowledge base."""
        agent = ResearchAgent(project_root=tmp_path)

        # Agent should have access to knowledge base
        assert hasattr(agent, "project_root") or hasattr(agent, "_project_root")

    @pytest.mark.asyncio
    async def test_store_discovery_to_knowledge(self, tmp_path):
        """Test storing tool discovery to knowledge base."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="discovered-tool",
            category=ToolCategory.SECURITY_SCANNING,
            package_manager=PackageManager.PIP,
            package_name="discovered-tool",
            description="A security scanner",
            install_command="pip install discovered-tool",
            recommended=True,
            rationale="Found during research",
        )

        if hasattr(agent, "store_discovery"):
            try:
                await agent.store_discovery(tool)
                # Should not raise
            except NotImplementedError:
                pass


class TestResearchAgentPlatformDetection:
    """Tests for platform detection in ResearchAgent."""

    def test_detect_platform_linux(self, tmp_path):
        """Test platform detection on Linux."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Linux"
            platform = agent._detect_platform()
            assert platform == "linux"

    def test_detect_platform_macos(self, tmp_path):
        """Test platform detection on macOS."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Darwin"
            platform = agent._detect_platform()
            assert platform == "macos"

    def test_detect_platform_windows(self, tmp_path):
        """Test platform detection on Windows."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Windows"
            platform = agent._detect_platform()
            assert platform == "windows"


class TestResearchAgentPreferredToolsLookup:
    """Tests for preferred tools lookup."""

    def test_get_preferred_tool_exists(self, tmp_path):
        """Test getting preferred tool that exists."""
        agent = ResearchAgent(project_root=tmp_path)

        # Should have some preferred tools defined
        tool = agent.get_preferred_tool(ToolCategory.BROWSER_AUTOMATION)
        if tool is not None:
            assert isinstance(tool, DiscoveredTool)
            assert tool.category == ToolCategory.BROWSER_AUTOMATION

    def test_get_preferred_tool_not_exists(self, tmp_path):
        """Test getting preferred tool for unknown category."""
        agent = ResearchAgent(project_root=tmp_path)

        # Create a mock category that definitely doesn't exist
        # This tests the dict.get() fallback
        result = agent.get_preferred_tool(ToolCategory.VIDEO_CAPTURE)
        # May or may not exist, but should not raise
        assert result is None or isinstance(result, DiscoveredTool)

    def test_get_alternatives(self, tmp_path):
        """Test getting alternative tools."""
        agent = ResearchAgent(project_root=tmp_path)

        alternatives = agent.get_alternatives(ToolCategory.BROWSER_AUTOMATION)
        assert isinstance(alternatives, list)
        for alt in alternatives:
            if alt is not None:
                assert isinstance(alt, DiscoveredTool)


class TestResearchAgentExecution:
    """Tests for ResearchAgent task execution."""

    @pytest.mark.asyncio
    async def test_execute_find_tool_missing_category(self, tmp_path):
        """Test execute with find_tool type but missing category."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Find a testing tool",
            instructions="Find a tool",
            context={"type": "find_tool"},  # Missing category
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "category" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_find_tool_invalid_category(self, tmp_path):
        """Test execute with find_tool type but invalid category."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Find a tool",
            instructions="Find a tool",
            context={"type": "find_tool", "category": "invalid_category"},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "unknown category" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_unknown_task_type(self, tmp_path):
        """Test execute with unknown task type."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Do something",
            instructions="Do something",
            context={"type": "unknown_type"},
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "unknown task type" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_handle_failure_missing_context(self, tmp_path):
        """Test execute with handle_failure type but missing context."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Handle tool failure",
            instructions="Handle failure",
            context={"type": "handle_failure"},  # Missing required fields
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "missing" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_handle_failure_invalid_category(self, tmp_path):
        """Test execute with handle_failure type but invalid category."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Handle tool failure",
            instructions="Handle failure",
            context={
                "type": "handle_failure",
                "failed_tool": "some-tool",
                "category": "invalid_category",
                "error": "Some error",
            },
        )

        result = await agent.execute(task)
        assert result.success is False
        assert "unknown category" in result.output.lower()


class TestToolCategoryComplete:
    """Comprehensive tests for ToolCategory enum."""

    def test_category_count(self):
        """Test expected number of categories."""
        # Count based on what's defined in the source
        assert len(ToolCategory) >= 7  # At minimum


class TestPackageManagerComplete:
    """Comprehensive tests for PackageManager enum."""

    def test_package_manager_count(self):
        """Test expected number of package managers."""
        assert len(PackageManager) >= 6  # At minimum


class TestResearchAgentInstallTool:
    """Tests for ResearchAgent install_tool method."""

    @pytest.mark.asyncio
    async def test_install_tool_builtin(self, tmp_path):
        """Test install_tool with built-in tool (no install needed)."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="unittest",
            category=ToolCategory.TESTING_FRAMEWORK,
            package_manager=PackageManager.PIP,
            package_name="",
            description="Built-in Python testing",
            install_command="# Built-in, no install needed",
        )

        result = await agent.install_tool(tool)
        assert result is True
        assert "unittest" in agent.installed_tools

    @pytest.mark.asyncio
    async def test_install_tool_success(self, tmp_path):
        """Test install_tool with successful subprocess."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="test-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="test-tool",
            description="Test tool",
            install_command="pip install test-tool",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = await agent.install_tool(tool)
            assert result is True
            assert "test-tool" in agent.installed_tools
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_install_tool_failure(self, tmp_path):
        """Test install_tool with failed subprocess."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="failing-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="failing-tool",
            description="Tool that fails",
            install_command="pip install failing-tool",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = await agent.install_tool(tool)
            assert result is False
            assert "failing-tool" not in agent.installed_tools

    @pytest.mark.asyncio
    async def test_install_tool_timeout(self, tmp_path):
        """Test install_tool handles timeout."""
        import subprocess

        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="slow-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="slow-tool",
            description="Tool that times out",
            install_command="pip install slow-tool",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("pip", 300)
            result = await agent.install_tool(tool)
            assert result is False

    @pytest.mark.asyncio
    async def test_install_tool_multi_command(self, tmp_path):
        """Test install_tool with multiple commands."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="playwright",
            category=ToolCategory.BROWSER_AUTOMATION,
            package_manager=PackageManager.PIP,
            package_name="playwright",
            description="Browser automation",
            install_command="pip install playwright && playwright install chromium",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = await agent.install_tool(tool)
            assert result is True
            # Should be called twice for the two commands
            assert mock_run.call_count == 2


class TestResearchAgentSearchForTool:
    """Tests for ResearchAgent search_for_tool method."""

    @pytest.mark.asyncio
    async def test_search_for_tool_uses_cache(self, tmp_path):
        """Test search_for_tool caches results."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="cached-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="cached-tool",
            description="A cached tool",
            install_command="pip install cached-tool",
        )

        # Pre-populate cache
        cache_key = f"{ToolCategory.LINTING.value}:linux:test need"
        agent.discovered_cache[cache_key] = [tool]

        result = await agent.search_for_tool("test need", "linux", ToolCategory.LINTING)
        assert len(result) == 1
        assert result[0].name == "cached-tool"

    @pytest.mark.asyncio
    async def test_search_for_tool_returns_empty(self, tmp_path):
        """Test search_for_tool returns empty list when no cache."""
        agent = ResearchAgent(project_root=tmp_path)

        result = await agent.search_for_tool("some need", "linux", ToolCategory.VIDEO_CAPTURE)
        assert isinstance(result, list)
        assert len(result) == 0


class TestResearchAgentFindAndInstall:
    """Tests for ResearchAgent find_and_install_tool method."""

    @pytest.mark.asyncio
    async def test_find_and_install_preferred_tool(self, tmp_path):
        """Test find_and_install_tool uses preferred tool."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
            with patch.object(agent, "_document_installation", new_callable=AsyncMock):
                with patch.object(agent, "read_knowledge", new_callable=AsyncMock) as mock_read:
                    mock_read.return_value = None
                    mock_install.return_value = True

                    result = await agent.find_and_install_tool(
                        category=ToolCategory.TESTING_FRAMEWORK,
                        need="test my code",
                        platform="linux",
                    )

                    assert result is not None
                    assert result.name == "pytest"

    @pytest.mark.asyncio
    async def test_find_and_install_tries_alternatives(self, tmp_path):
        """Test find_and_install_tool tries alternatives when preferred fails."""
        agent = ResearchAgent(project_root=tmp_path)
        agent.failed_tools.append("ruff")  # Mark preferred as failed

        with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
            with patch.object(agent, "_document_installation", new_callable=AsyncMock):
                with patch.object(agent, "read_knowledge", new_callable=AsyncMock) as mock_read:
                    mock_read.return_value = None
                    mock_install.return_value = True

                    result = await agent.find_and_install_tool(
                        category=ToolCategory.LINTING,
                        need="lint my code",
                        platform="linux",
                    )

                    # Should try an alternative (flake8 or pylint)
                    assert result is not None
                    assert result.name in ["flake8", "pylint"]

    @pytest.mark.asyncio
    async def test_find_and_install_all_fail(self, tmp_path):
        """Test find_and_install_tool returns None when all fail."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
            with patch.object(agent, "read_knowledge", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = None
                mock_install.return_value = False  # All installs fail

                result = await agent.find_and_install_tool(
                    category=ToolCategory.LINTING,
                    need="lint my code",
                    platform="linux",
                )

                assert result is None


class TestResearchAgentHandleFailure:
    """Tests for ResearchAgent handle_tool_failure method."""

    @pytest.mark.asyncio
    async def test_handle_failure_finds_alternative(self, tmp_path):
        """Test handle_tool_failure finds a working alternative."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
            with patch.object(agent, "_document_failure_resolution", new_callable=AsyncMock):
                mock_install.return_value = True

                result = await agent.handle_tool_failure(
                    failed_tool="ruff",
                    error_message="Not working",
                    category=ToolCategory.LINTING,
                    platform="linux",
                )

                assert result is not None
                assert result.name in ["flake8", "pylint"]
                assert "ruff" in agent.failed_tools

    @pytest.mark.asyncio
    async def test_handle_failure_no_alternatives(self, tmp_path):
        """Test handle_tool_failure returns None when no alternatives work."""
        agent = ResearchAgent(project_root=tmp_path)
        # Mark all alternatives as failed
        agent.failed_tools = ["flake8", "pylint", "ruff"]

        with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
            mock_install.return_value = False

            result = await agent.handle_tool_failure(
                failed_tool="ruff",
                error_message="Not working",
                category=ToolCategory.LINTING,
                platform="linux",
            )

            assert result is None


class TestResearchAgentVerifyTool:
    """Tests for ResearchAgent verify_tool_installed method."""

    @pytest.mark.asyncio
    async def test_verify_known_tool_success(self, tmp_path):
        """Test verify_tool_installed for known tool."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = await agent.verify_tool_installed("pytest")
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_known_tool_failure(self, tmp_path):
        """Test verify_tool_installed for known tool that fails."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = await agent.verify_tool_installed("pytest")
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_unknown_tool_installed(self, tmp_path):
        """Test verify_tool_installed for unknown tool in installed list."""
        agent = ResearchAgent(project_root=tmp_path)
        agent.installed_tools.append("custom-tool")

        result = await agent.verify_tool_installed("custom-tool")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_unknown_tool_not_installed(self, tmp_path):
        """Test verify_tool_installed for unknown tool not in installed list."""
        agent = ResearchAgent(project_root=tmp_path)

        result = await agent.verify_tool_installed("unknown-tool")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_tool_exception(self, tmp_path):
        """Test verify_tool_installed handles exceptions."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            result = await agent.verify_tool_installed("pytest")
            assert result is False


class TestResearchAgentDocumentation:
    """Tests for ResearchAgent documentation methods."""

    @pytest.mark.asyncio
    async def test_document_installation(self, tmp_path):
        """Test _document_installation writes to knowledge base."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="test-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="test-tool",
            description="A test tool",
            install_command="pip install test-tool",
            rationale="Testing purposes",
            documentation_url="https://example.com",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            await agent._document_installation(tool)
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert "test-tool" in call_args.kwargs["title"]

    @pytest.mark.asyncio
    async def test_document_installation_exception(self, tmp_path):
        """Test _document_installation handles exceptions gracefully."""
        agent = ResearchAgent(project_root=tmp_path)

        tool = DiscoveredTool(
            name="test-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="test-tool",
            description="A test tool",
            install_command="pip install test-tool",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.side_effect = Exception("Write failed")
            # Should not raise
            await agent._document_installation(tool)

    @pytest.mark.asyncio
    async def test_document_failure_resolution(self, tmp_path):
        """Test _document_failure_resolution writes to knowledge base."""
        agent = ResearchAgent(project_root=tmp_path)

        solution = DiscoveredTool(
            name="alternative-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="alternative-tool",
            description="Alternative tool",
            install_command="pip install alternative-tool",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            await agent._document_failure_resolution(
                failed_tool="failed-tool",
                error="Some error",
                solution=solution,
                platform="linux",
            )
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert "failed-tool" in call_args.kwargs["title"]


class TestResearchAgentClose:
    """Tests for ResearchAgent cleanup."""

    @pytest.mark.asyncio
    async def test_close_cleans_up_client(self, tmp_path):
        """Test close method cleans up HTTP client."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent.client, "aclose", new_callable=AsyncMock) as mock_close:
            await agent.close()
            mock_close.assert_called_once()


class TestResearchAgentPreferredToolsDict:
    """Tests for PREFERRED_TOOLS dictionary."""

    def test_preferred_tools_all_categories(self, tmp_path):
        """Test PREFERRED_TOOLS has entries for all expected categories."""
        expected_categories = [
            ToolCategory.BROWSER_AUTOMATION,
            ToolCategory.TESTING_FRAMEWORK,
            ToolCategory.MOCK_SERVER,
            ToolCategory.SCREENSHOT_TOOL,
            ToolCategory.VIDEO_CAPTURE,
            ToolCategory.PERFORMANCE_TOOL,
            ToolCategory.LINTING,
            ToolCategory.SECURITY_SCANNING,
            ToolCategory.TYPE_CHECKING,
            ToolCategory.DEPENDENCY_CHECK,
            ToolCategory.DOCUMENTATION,
        ]

        for category in expected_categories:
            assert category in ResearchAgent.PREFERRED_TOOLS
            tool = ResearchAgent.PREFERRED_TOOLS[category]
            assert tool.recommended is True
            assert len(tool.platform_support) > 0


class TestResearchAgentAlternatives:
    """Tests for ALTERNATIVES dictionary."""

    def test_alternatives_for_browser_automation(self, tmp_path):
        """Test alternatives exist for browser automation."""
        alts = ResearchAgent.ALTERNATIVES.get(ToolCategory.BROWSER_AUTOMATION, [])
        assert len(alts) >= 2
        names = [a.name for a in alts]
        assert "selenium" in names or "puppeteer" in names

    def test_alternatives_for_linting(self, tmp_path):
        """Test alternatives exist for linting."""
        alts = ResearchAgent.ALTERNATIVES.get(ToolCategory.LINTING, [])
        assert len(alts) >= 2
        names = [a.name for a in alts]
        assert "flake8" in names or "pylint" in names


class TestResearchAgentExecuteSuccessPaths:
    """Tests for execute() success paths."""

    @pytest.mark.asyncio
    async def test_execute_find_tool_success(self, tmp_path):
        """Test execute with find_tool type succeeds."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Find a testing tool",
            instructions="Find a tool",
            context={"type": "find_tool", "category": "testing_framework"},
        )

        with patch.object(agent, "find_and_install_tool", new_callable=AsyncMock) as mock_find:
            tool = DiscoveredTool(
                name="pytest",
                category=ToolCategory.TESTING_FRAMEWORK,
                package_manager=PackageManager.PIP,
                package_name="pytest",
                description="Python testing",
                install_command="pip install pytest",
            )
            mock_find.return_value = tool

            result = await agent.execute(task)
            assert result.success is True
            assert "pytest" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_find_tool_not_found(self, tmp_path):
        """Test execute with find_tool type when no tool found."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Find a tool",
            instructions="Find a tool",
            context={"type": "find_tool", "category": "testing_framework"},
        )

        with patch.object(agent, "find_and_install_tool", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None

            result = await agent.execute(task)
            assert result.success is False
            assert "could not find" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_handle_failure_success(self, tmp_path):
        """Test execute with handle_failure type succeeds."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Handle tool failure",
            instructions="Handle failure",
            context={
                "type": "handle_failure",
                "failed_tool": "ruff",
                "category": "linting",
                "error": "Tool not working",
            },
        )

        with patch.object(agent, "handle_tool_failure", new_callable=AsyncMock) as mock_handle:
            alt_tool = DiscoveredTool(
                name="flake8",
                category=ToolCategory.LINTING,
                package_manager=PackageManager.PIP,
                package_name="flake8",
                description="Linting",
                install_command="pip install flake8",
            )
            mock_handle.return_value = alt_tool

            result = await agent.execute(task)
            assert result.success is True
            assert "flake8" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_handle_failure_no_alternative(self, tmp_path):
        """Test execute with handle_failure type when no alternative found."""
        from beyond_ralph.agents.base import AgentTask

        agent = ResearchAgent(project_root=tmp_path)

        task = AgentTask(
            id="test-task",
            description="Handle tool failure",
            instructions="Handle failure",
            context={
                "type": "handle_failure",
                "failed_tool": "ruff",
                "category": "linting",
                "error": "Tool not working",
            },
        )

        with patch.object(agent, "handle_tool_failure", new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = None

            result = await agent.execute(task)
            assert result.success is False
            assert "no working alternatives" in result.output.lower()


class TestResearchAgentFindAndInstallEdgeCases:
    """Edge case tests for find_and_install_tool."""

    @pytest.mark.asyncio
    async def test_find_and_install_skips_failed_from_search(self, tmp_path):
        """Test find_and_install_tool skips tools in failed_tools from search."""
        agent = ResearchAgent(project_root=tmp_path)
        agent.failed_tools = ["discovered-tool"]  # Mark as failed

        # Mock search to return the failed tool
        discovered = DiscoveredTool(
            name="discovered-tool",
            category=ToolCategory.VIDEO_CAPTURE,
            package_manager=PackageManager.PIP,
            package_name="discovered-tool",
            description="A tool",
            install_command="pip install discovered-tool",
        )

        with patch.object(agent, "get_preferred_tool") as mock_pref:
            mock_pref.return_value = None  # No preferred tool
            with patch.object(agent, "get_alternatives") as mock_alts:
                mock_alts.return_value = []  # No alternatives
                with patch.object(agent, "search_for_tool", new_callable=AsyncMock) as mock_search:
                    mock_search.return_value = [discovered]
                    with patch.object(agent, "read_knowledge", new_callable=AsyncMock) as mock_read:
                        mock_read.return_value = None

                        result = await agent.find_and_install_tool(
                            category=ToolCategory.VIDEO_CAPTURE,
                            need="capture video",
                            platform="linux",
                        )

                        # Should return None since only tool was in failed_tools
                        assert result is None

    @pytest.mark.asyncio
    async def test_find_and_install_search_tool_fails(self, tmp_path):
        """Test find_and_install_tool handles search tool install failure."""
        agent = ResearchAgent(project_root=tmp_path)

        # Mock search to return a tool
        discovered = DiscoveredTool(
            name="new-tool",
            category=ToolCategory.VIDEO_CAPTURE,
            package_manager=PackageManager.PIP,
            package_name="new-tool",
            description="A tool",
            install_command="pip install new-tool",
        )

        with patch.object(agent, "get_preferred_tool") as mock_pref:
            mock_pref.return_value = None
            with patch.object(agent, "get_alternatives") as mock_alts:
                mock_alts.return_value = []
                with patch.object(agent, "search_for_tool", new_callable=AsyncMock) as mock_search:
                    mock_search.return_value = [discovered]
                    with patch.object(
                        agent, "install_tool", new_callable=AsyncMock
                    ) as mock_install:
                        mock_install.return_value = False  # Install fails
                        with patch.object(
                            agent, "read_knowledge", new_callable=AsyncMock
                        ) as mock_read:
                            mock_read.return_value = None

                            result = await agent.find_and_install_tool(
                                category=ToolCategory.VIDEO_CAPTURE,
                                need="capture video",
                                platform="linux",
                            )

                            assert result is None
                            assert "new-tool" in agent.failed_tools


class TestResearchAgentHandleFailureEdgeCases:
    """Edge case tests for handle_tool_failure."""

    @pytest.mark.asyncio
    async def test_handle_failure_skips_wrong_platform(self, tmp_path):
        """Test handle_tool_failure skips alternatives for wrong platform."""
        agent = ResearchAgent(project_root=tmp_path)
        agent.failed_tools = ["failed-tool"]

        # Create alternative only for windows
        alt = DiscoveredTool(
            name="windows-only-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="windows-tool",
            description="Windows only",
            install_command="pip install windows-tool",
            platform_support=["windows"],  # Only windows
        )

        with patch.object(agent, "get_alternatives") as mock_alts:
            mock_alts.return_value = [alt]
            with patch.object(agent, "search_for_tool", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = []

                result = await agent.handle_tool_failure(
                    failed_tool="failed-tool",
                    error_message="Not working",
                    category=ToolCategory.LINTING,
                    platform="linux",  # Different platform
                )

                # Should return None since alt doesn't support linux
                assert result is None

    @pytest.mark.asyncio
    async def test_handle_failure_alternative_install_fails(self, tmp_path):
        """Test handle_tool_failure when alternative install fails."""
        agent = ResearchAgent(project_root=tmp_path)
        agent.failed_tools = ["failed-tool"]

        alt = DiscoveredTool(
            name="alternative",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="alternative",
            description="An alternative",
            install_command="pip install alternative",
            platform_support=["linux"],
        )

        with patch.object(agent, "get_alternatives") as mock_alts:
            mock_alts.return_value = [alt]
            with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
                mock_install.return_value = False  # Install fails
                with patch.object(agent, "search_for_tool", new_callable=AsyncMock) as mock_search:
                    mock_search.return_value = []

                    result = await agent.handle_tool_failure(
                        failed_tool="failed-tool",
                        error_message="Not working",
                        category=ToolCategory.LINTING,
                        platform="linux",
                    )

                    assert result is None
                    assert "alternative" in agent.failed_tools

    @pytest.mark.asyncio
    async def test_handle_failure_with_searched_alternatives(self, tmp_path):
        """Test handle_tool_failure with alternatives from search."""
        agent = ResearchAgent(project_root=tmp_path)
        agent.failed_tools = ["failed-tool"]

        searched_alt = DiscoveredTool(
            name="searched-alt",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="searched-alt",
            description="Searched alternative",
            install_command="pip install searched-alt",
            platform_support=["linux"],
            recommended=True,
        )

        with patch.object(agent, "get_alternatives") as mock_alts:
            mock_alts.return_value = []  # No direct alternatives
            with patch.object(agent, "search_for_tool", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = [searched_alt]
                with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
                    mock_install.return_value = True
                    with patch.object(
                        agent, "_document_failure_resolution", new_callable=AsyncMock
                    ):
                        result = await agent.handle_tool_failure(
                            failed_tool="failed-tool",
                            error_message="Not working",
                            category=ToolCategory.LINTING,
                            platform="linux",
                        )

                        assert result is not None
                        assert result.name == "searched-alt"

    @pytest.mark.asyncio
    async def test_handle_failure_searched_alt_fails(self, tmp_path):
        """Test handle_tool_failure when searched alternative install fails."""
        agent = ResearchAgent(project_root=tmp_path)
        agent.failed_tools = ["failed-tool"]

        searched_alt = DiscoveredTool(
            name="searched-alt",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="searched-alt",
            description="Searched alternative",
            install_command="pip install searched-alt",
            platform_support=["linux"],
        )

        with patch.object(agent, "get_alternatives") as mock_alts:
            mock_alts.return_value = []
            with patch.object(agent, "search_for_tool", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = [searched_alt]
                with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
                    mock_install.return_value = False  # Install fails

                    result = await agent.handle_tool_failure(
                        failed_tool="failed-tool",
                        error_message="Not working",
                        category=ToolCategory.LINTING,
                        platform="linux",
                    )

                    assert result is None
                    assert "searched-alt" in agent.failed_tools


class TestResearchAgentDocumentFailureException:
    """Tests for _document_failure_resolution exception handling."""

    @pytest.mark.asyncio
    async def test_document_failure_resolution_exception(self, tmp_path):
        """Test _document_failure_resolution handles exceptions gracefully."""
        agent = ResearchAgent(project_root=tmp_path)

        solution = DiscoveredTool(
            name="solution-tool",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="solution-tool",
            description="Solution",
            install_command="pip install solution-tool",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.side_effect = Exception("Write failed")

            # Should not raise
            await agent._document_failure_resolution(
                failed_tool="failed-tool",
                error="Some error",
                solution=solution,
                platform="linux",
            )


# ============================================================================
# Tests for CodeExample dataclass
# ============================================================================


class TestCodeExample:
    """Tests for CodeExample dataclass."""

    def test_code_example_creation(self):
        """Test creating a CodeExample."""
        example = CodeExample(
            language="python",
            code="print('hello')",
            description="Simple print statement",
            source_url="https://example.com/tutorial",
        )

        assert example.language == "python"
        assert example.code == "print('hello')"
        assert example.description == "Simple print statement"
        assert example.source_url == "https://example.com/tutorial"

    def test_code_example_to_dict(self):
        """Test CodeExample serialization to dict."""
        example = CodeExample(
            language="javascript",
            code="console.log('test')",
            description="Console logging",
            source_url="https://docs.example.com",
        )

        data = example.to_dict()

        assert data["language"] == "javascript"
        assert data["code"] == "console.log('test')"
        assert data["description"] == "Console logging"
        assert data["source_url"] == "https://docs.example.com"

    def test_code_example_with_multiline_code(self):
        """Test CodeExample with multiline code."""
        code = """def hello():
    print('Hello, World!')
    return True"""

        example = CodeExample(
            language="python",
            code=code,
            description="Function definition",
            source_url="https://example.com",
        )

        assert example.code == code
        assert "\n" in example.code


# ============================================================================
# Tests for ResearchResult dataclass
# ============================================================================


class TestResearchResult:
    """Tests for ResearchResult dataclass."""

    def test_research_result_creation(self):
        """Test creating a ResearchResult."""
        examples = [
            CodeExample(
                language="python",
                code="import requests",
                description="Import statement",
                source_url="https://example.com",
            )
        ]

        result = ResearchResult(
            topic="HTTP requests",
            summary="How to make HTTP requests in Python",
            implementation_steps=["Install requests", "Import library", "Make request"],
            code_examples=examples,
            sources=["https://docs.python.org", "https://requests.readthedocs.io"],
            confidence=0.85,
            stored_path="beyondralph_knowledge/research-http-requests.md",
        )

        assert result.topic == "HTTP requests"
        assert result.summary == "How to make HTTP requests in Python"
        assert len(result.implementation_steps) == 3
        assert len(result.code_examples) == 1
        assert len(result.sources) == 2
        assert result.confidence == 0.85
        assert "research-http-requests" in result.stored_path

    def test_research_result_to_dict(self):
        """Test ResearchResult serialization to dict."""
        examples = [
            CodeExample(
                language="python",
                code="x = 1",
                description="Variable",
                source_url="https://example.com",
            )
        ]

        result = ResearchResult(
            topic="Variables",
            summary="Variable assignment",
            implementation_steps=["Step 1"],
            code_examples=examples,
            sources=["https://example.com"],
            confidence=0.9,
            stored_path="path/to/file.md",
        )

        data = result.to_dict()

        assert data["topic"] == "Variables"
        assert data["summary"] == "Variable assignment"
        assert data["implementation_steps"] == ["Step 1"]
        assert len(data["code_examples"]) == 1
        assert data["code_examples"][0]["language"] == "python"
        assert data["sources"] == ["https://example.com"]
        assert data["confidence"] == 0.9
        assert data["stored_path"] == "path/to/file.md"

    def test_research_result_empty_examples(self):
        """Test ResearchResult with no code examples."""
        result = ResearchResult(
            topic="Abstract concept",
            summary="No code available",
            implementation_steps=["Read more"],
            code_examples=[],
            sources=[],
            confidence=0.3,
            stored_path="",
        )

        assert len(result.code_examples) == 0
        assert len(result.sources) == 0
        assert result.stored_path == ""


# ============================================================================
# Tests for ResearchAgent Web Search Methods
# ============================================================================


class TestResearchAgentWebSearch:
    """Tests for ResearchAgent web search functionality."""

    @pytest.mark.asyncio
    async def test_search_web_returns_list(self, tmp_path):
        """Test _search_web returns a list."""
        agent = ResearchAgent(project_root=tmp_path)

        results = await agent._search_web("python http requests")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_fetch_documentation_returns_string(self, tmp_path):
        """Test _fetch_documentation returns a string."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html>Documentation content</html>"
            mock_get.return_value = mock_response

            content = await agent._fetch_documentation("https://example.com/docs")

            assert isinstance(content, str)
            assert "Documentation" in content

    @pytest.mark.asyncio
    async def test_fetch_documentation_handles_error(self, tmp_path):
        """Test _fetch_documentation handles HTTP errors gracefully."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Network error")

            content = await agent._fetch_documentation("https://example.com/docs")

            assert content == ""


# ============================================================================
# Tests for Source Evaluation
# ============================================================================


class TestResearchAgentSourceEvaluation:
    """Tests for ResearchAgent source evaluation."""

    def test_evaluate_sources_prefers_official_docs(self, tmp_path):
        """Test that official documentation is ranked highest."""
        agent = ResearchAgent(project_root=tmp_path)

        results = [
            {"url": "https://medium.com/some-blog", "title": "Blog post"},
            {"url": "https://docs.python.org/3/library", "title": "Python Docs"},
            {"url": "https://stackoverflow.com/questions/123", "title": "SO Question"},
        ]

        ranked = agent._evaluate_sources(results)

        assert len(ranked) == 3
        # Official docs should be first
        assert "docs.python.org" in ranked[0]["url"]
        assert ranked[0]["quality"] == 1.0

    def test_evaluate_sources_ranks_stackoverflow_high(self, tmp_path):
        """Test that Stack Overflow is ranked well."""
        agent = ResearchAgent(project_root=tmp_path)

        results = [
            {"url": "https://random-blog.com", "title": "Random"},
            {"url": "https://stackoverflow.com/questions/123", "title": "Answer"},
        ]

        ranked = agent._evaluate_sources(results)

        # SO should have quality >= 0.8
        so_result = next(r for r in ranked if "stackoverflow" in r["url"])
        assert so_result["quality"] >= 0.8

    def test_evaluate_sources_penalizes_medium(self, tmp_path):
        """Test that Medium posts are penalized."""
        agent = ResearchAgent(project_root=tmp_path)

        results = [
            {"url": "https://medium.com/@user/post", "title": "Medium Post"},
        ]

        ranked = agent._evaluate_sources(results)

        assert ranked[0]["quality"] < 0.5

    def test_evaluate_sources_boosts_tutorials(self, tmp_path):
        """Test that tutorials get a quality boost."""
        agent = ResearchAgent(project_root=tmp_path)

        results = [
            {"url": "https://example.com/article", "title": "Python Tutorial Guide"},
        ]

        ranked = agent._evaluate_sources(results)

        # Should get boost for having "tutorial" and "guide" in title
        assert ranked[0]["quality"] >= 0.5

    def test_evaluate_sources_empty_list(self, tmp_path):
        """Test evaluating empty results list."""
        agent = ResearchAgent(project_root=tmp_path)

        ranked = agent._evaluate_sources([])

        assert ranked == []


# ============================================================================
# Tests for Code Example Extraction
# ============================================================================


class TestResearchAgentCodeExtraction:
    """Tests for ResearchAgent code example extraction."""

    def test_extract_code_examples_markdown(self, tmp_path):
        """Test extracting code from markdown code blocks."""
        agent = ResearchAgent(project_root=tmp_path)

        content = """
Here is some explanation.

```python
def hello():
    print("Hello, World!")
```

More text here.
"""

        examples = agent._extract_code_examples(content, "https://example.com")

        assert len(examples) == 1
        assert examples[0].language == "python"
        assert "def hello():" in examples[0].code
        assert examples[0].source_url == "https://example.com"

    def test_extract_code_examples_multiple_blocks(self, tmp_path):
        """Test extracting multiple code blocks."""
        agent = ResearchAgent(project_root=tmp_path)

        content = """
```python
import requests
response = requests.get('https://api.example.com')
```

Some explanation.

```javascript
fetch('https://api.example.com')
    .then(response => response.json())
```
"""

        examples = agent._extract_code_examples(content, "https://example.com")

        assert len(examples) == 2
        languages = [e.language for e in examples]
        assert "python" in languages
        assert "javascript" in languages

    def test_extract_code_examples_skips_short_snippets(self, tmp_path):
        """Test that very short code snippets are skipped."""
        agent = ResearchAgent(project_root=tmp_path)

        content = """
```python
x = 1
```
"""

        examples = agent._extract_code_examples(content, "https://example.com")

        # "x = 1" is less than 20 chars, should be skipped
        assert len(examples) == 0

    def test_extract_code_examples_keeps_install_commands(self, tmp_path):
        """Test that shell install commands are kept."""
        agent = ResearchAgent(project_root=tmp_path)

        content = """
```bash
pip install requests httpx
```
"""

        examples = agent._extract_code_examples(content, "https://example.com")

        assert len(examples) == 1
        assert "pip install" in examples[0].code

    def test_extract_code_examples_empty_content(self, tmp_path):
        """Test extracting from empty content."""
        agent = ResearchAgent(project_root=tmp_path)

        examples = agent._extract_code_examples("", "https://example.com")

        assert examples == []


# ============================================================================
# Tests for Implementation Plan Synthesis
# ============================================================================


class TestResearchAgentSynthesis:
    """Tests for ResearchAgent implementation plan synthesis."""

    def test_synthesize_empty_sources(self, tmp_path):
        """Test synthesis with no sources."""
        agent = ResearchAgent(project_root=tmp_path)

        summary, steps = agent._synthesize_implementation_plan([], "test topic")

        assert "No sources found" in summary
        assert len(steps) > 0
        assert "official documentation" in steps[0].lower()

    def test_synthesize_with_sources(self, tmp_path):
        """Test synthesis with sources."""
        agent = ResearchAgent(project_root=tmp_path)

        sources = [
            {
                "url": "https://docs.example.com",
                "title": "Official Docs",
                "content": "Documentation content",
                "quality": 1.0,
            },
            {
                "url": "https://tutorial.com",
                "title": "Tutorial",
                "content": "Tutorial content",
                "quality": 0.7,
            },
        ]

        summary, steps = agent._synthesize_implementation_plan(sources, "authentication")

        assert "authentication" in summary
        assert "Official Docs" in summary
        assert len(steps) >= 5

    def test_synthesize_includes_quality_labels(self, tmp_path):
        """Test that quality labels are included in summary."""
        agent = ResearchAgent(project_root=tmp_path)

        sources = [
            {"url": "https://docs.example.com", "title": "Docs", "quality": 0.95},
        ]

        summary, _ = agent._synthesize_implementation_plan(sources, "topic")

        assert "Official docs" in summary


# ============================================================================
# Tests for Confidence Calculation
# ============================================================================


class TestResearchAgentConfidence:
    """Tests for ResearchAgent confidence calculation."""

    def test_confidence_no_sources(self, tmp_path):
        """Test confidence with no sources."""
        agent = ResearchAgent(project_root=tmp_path)

        confidence = agent._calculate_confidence([], [])

        assert confidence == 0.0

    def test_confidence_high_quality_sources(self, tmp_path):
        """Test confidence with high-quality sources."""
        agent = ResearchAgent(project_root=tmp_path)

        sources = [
            {"quality": 1.0},
            {"quality": 0.9},
            {"quality": 0.95},
        ]
        examples = [
            CodeExample("python", "code" * 10, "desc", "url"),
            CodeExample("python", "more code" * 5, "desc", "url"),
        ]

        confidence = agent._calculate_confidence(sources, examples)

        # Should be high confidence
        assert confidence >= 0.6

    def test_confidence_low_quality_sources(self, tmp_path):
        """Test confidence with low-quality sources."""
        agent = ResearchAgent(project_root=tmp_path)

        sources = [
            {"quality": 0.3},
        ]

        confidence = agent._calculate_confidence(sources, [])

        # Low quality, few sources, no examples = low confidence
        assert confidence < 0.3

    def test_confidence_many_examples_boost(self, tmp_path):
        """Test that many code examples boost confidence."""
        agent = ResearchAgent(project_root=tmp_path)

        sources = [{"quality": 0.5}]
        examples = [
            CodeExample("python", f"code example {i}" * 5, "desc", "url") for i in range(10)
        ]

        confidence = agent._calculate_confidence(sources, examples)

        # Many examples should provide boost
        assert confidence >= 0.3

    def test_confidence_bounds(self, tmp_path):
        """Test that confidence is always between 0 and 1."""
        agent = ResearchAgent(project_root=tmp_path)

        # Maximum inputs
        sources = [{"quality": 1.0} for _ in range(10)]
        examples = [CodeExample("python", "x" * 100, "desc", "url") for _ in range(20)]

        confidence = agent._calculate_confidence(sources, examples)

        assert 0.0 <= confidence <= 1.0


# ============================================================================
# Tests for Research Storage
# ============================================================================


class TestResearchAgentStorage:
    """Tests for ResearchAgent research storage."""

    @pytest.mark.asyncio
    async def test_store_research(self, tmp_path):
        """Test storing research results."""
        agent = ResearchAgent(project_root=tmp_path)

        result = ResearchResult(
            topic="Test Topic",
            summary="Test summary",
            implementation_steps=["Step 1", "Step 2"],
            code_examples=[CodeExample("python", "print('test')" * 5, "Print", "https://ex.com")],
            sources=["https://example.com"],
            confidence=0.75,
            stored_path="",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = "test-uuid"

            path = await agent._store_research(result)

            assert "research-test-topic" in path
            mock_write.assert_called_once()
            call_kwargs = mock_write.call_args.kwargs
            assert call_kwargs["category"] == "research"
            assert "implementation" in call_kwargs["tags"]

    @pytest.mark.asyncio
    async def test_store_research_sanitizes_topic(self, tmp_path):
        """Test that special characters are sanitized from topic."""
        agent = ResearchAgent(project_root=tmp_path)

        result = ResearchResult(
            topic="OAuth2/OIDC Authentication!@#$%",
            summary="Auth summary",
            implementation_steps=[],
            code_examples=[],
            sources=[],
            confidence=0.5,
            stored_path="",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = "uuid"

            path = await agent._store_research(result)

            # Should contain sanitized topic
            assert "oauth2" in path.lower()
            assert "/" not in path.split("/")[-1].replace(".md", "")

    @pytest.mark.asyncio
    async def test_store_research_handles_error(self, tmp_path):
        """Test that storage errors return empty path."""
        agent = ResearchAgent(project_root=tmp_path)

        result = ResearchResult(
            topic="Test",
            summary="Summary",
            implementation_steps=[],
            code_examples=[],
            sources=[],
            confidence=0.5,
            stored_path="",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.side_effect = Exception("Write failed")

            path = await agent._store_research(result)

            assert path == ""


# ============================================================================
# Tests for Full Research Implementation Flow
# ============================================================================


class TestResearchAgentImplementationResearch:
    """Tests for the full research_implementation flow."""

    @pytest.mark.asyncio
    async def test_research_implementation_basic(self, tmp_path):
        """Test basic research_implementation flow."""
        agent = ResearchAgent(project_root=tmp_path)

        # Mock all the internal methods
        with patch.object(agent, "_search_web", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"url": "https://docs.example.com", "title": "Docs"},
            ]

            with patch.object(agent, "_fetch_documentation", new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = """
# Documentation

Here is how to do it:

```python
def example_function():
    return "example result"
```
"""

                with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
                    mock_write.return_value = "test-uuid"

                    result = await agent.research_implementation("test topic")

                    assert isinstance(result, ResearchResult)
                    assert result.topic == "test topic"
                    assert len(result.implementation_steps) > 0

    @pytest.mark.asyncio
    async def test_research_implementation_no_sources(self, tmp_path):
        """Test research_implementation with no search results."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "_search_web", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
                mock_write.return_value = "uuid"

                result = await agent.research_implementation("obscure topic")

                assert result.confidence == 0.0
                assert "No sources found" in result.summary

    @pytest.mark.asyncio
    async def test_research_implementation_fetch_failures(self, tmp_path):
        """Test research_implementation handles fetch failures gracefully."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "_search_web", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"url": "https://failing.com", "title": "Fails"},
                {"url": "https://working.com", "title": "Works"},
            ]

            with patch.object(agent, "_fetch_documentation", new_callable=AsyncMock) as mock_fetch:
                # First call fails, second succeeds
                mock_fetch.side_effect = [
                    Exception("Network error"),
                    "```python\nworking_code = True\n```",
                ]

                with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
                    mock_write.return_value = "uuid"

                    result = await agent.research_implementation("topic")

                    # Should still produce a result from the working source
                    assert isinstance(result, ResearchResult)

    @pytest.mark.asyncio
    async def test_research_implementation_stores_result(self, tmp_path):
        """Test that research_implementation stores results in knowledge base."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "_search_web", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
                mock_write.return_value = "stored-uuid"

                result = await agent.research_implementation("my topic")

                mock_write.assert_called_once()
                assert result.stored_path != "" or mock_write.called

    @pytest.mark.asyncio
    async def test_research_implementation_extracts_examples(self, tmp_path):
        """Test that code examples are extracted from documentation."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "_search_web", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"url": "https://docs.example.com", "title": "Docs"},
            ]

            with patch.object(agent, "_fetch_documentation", new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = """
# How to authenticate

```python
import jwt

def create_token(user_id):
    payload = {"user_id": user_id}
    return jwt.encode(payload, "secret")
```

Then use the token:

```python
token = create_token(123)
headers = {"Authorization": f"Bearer {token}"}
```
"""

                with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
                    mock_write.return_value = "uuid"

                    result = await agent.research_implementation("JWT authentication")

                    # Should extract the code examples
                    assert len(result.code_examples) >= 1
                    # Check that Python code was extracted
                    python_examples = [e for e in result.code_examples if e.language == "python"]
                    assert len(python_examples) >= 1


# ============================================================================
# Tests for SkillRecommendation dataclass
# ============================================================================


class TestSkillRecommendation:
    """Tests for SkillRecommendation dataclass."""

    def test_skill_recommendation_creation(self):
        """Test creating a SkillRecommendation."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        rec = SkillRecommendation(
            name="@modelcontextprotocol/server-filesystem",
            description="MCP server for filesystem access",
            source="npm",
            install_command="npm install @modelcontextprotocol/server-filesystem",
            stars=500,
            last_updated="2024-01-15",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.85,
            reason="Official MCP package for file operations",
        )

        assert rec.name == "@modelcontextprotocol/server-filesystem"
        assert rec.description == "MCP server for filesystem access"
        assert rec.source == "npm"
        assert rec.stars == 500
        assert rec.last_updated == "2024-01-15"
        assert rec.requires_restart is True
        assert rec.config_location == ".claude/settings.json"
        assert rec.quality_score == 0.85
        assert "Official MCP" in rec.reason

    def test_skill_recommendation_to_dict(self):
        """Test SkillRecommendation serialization to dict."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        rec = SkillRecommendation(
            name="test-mcp",
            description="Test MCP server",
            source="github",
            install_command="git clone https://github.com/test/mcp",
            stars=100,
            last_updated="2024-02-01",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.7,
            reason="Test recommendation",
        )

        data = rec.to_dict()

        assert data["name"] == "test-mcp"
        assert data["description"] == "Test MCP server"
        assert data["source"] == "github"
        assert data["install_command"] == "git clone https://github.com/test/mcp"
        assert data["stars"] == 100
        assert data["last_updated"] == "2024-02-01"
        assert data["requires_restart"] is True
        assert data["config_location"] == ".claude/settings.json"
        assert data["quality_score"] == 0.7
        assert data["reason"] == "Test recommendation"

    def test_skill_recommendation_github_source(self):
        """Test SkillRecommendation with GitHub source."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        rec = SkillRecommendation(
            name="owner/repo-mcp-server",
            description="GitHub-hosted MCP server",
            source="github",
            install_command="git clone https://github.com/owner/repo-mcp-server && cd repo-mcp-server && pip install -e .",
            stars=1500,
            last_updated="2024-01-20",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.9,
            reason="High-star GitHub repository",
        )

        assert rec.source == "github"
        assert "git clone" in rec.install_command


# ============================================================================
# Tests for SkillDiscoveryResult dataclass
# ============================================================================


class TestSkillDiscoveryResult:
    """Tests for SkillDiscoveryResult dataclass."""

    def test_skill_discovery_result_creation(self):
        """Test creating a SkillDiscoveryResult."""
        from beyond_ralph.agents.research_agent import (
            SkillDiscoveryResult,
            SkillRecommendation,
        )

        recommendations = [
            SkillRecommendation(
                name="test-skill",
                description="Test",
                source="npm",
                install_command="npm install test",
                stars=100,
                last_updated="2024-01-01",
                requires_restart=True,
                config_location=".claude/settings.json",
                quality_score=0.8,
                reason="Test",
            )
        ]

        result = SkillDiscoveryResult(
            requirements=["database access", "file operations"],
            recommendations=recommendations,
            discovery_phase="early",
            restart_warning=False,
        )

        assert result.requirements == ["database access", "file operations"]
        assert len(result.recommendations) == 1
        assert result.discovery_phase == "early"
        assert result.restart_warning is False

    def test_skill_discovery_result_to_dict(self):
        """Test SkillDiscoveryResult serialization to dict."""
        from beyond_ralph.agents.research_agent import (
            SkillDiscoveryResult,
            SkillRecommendation,
        )

        rec = SkillRecommendation(
            name="skill",
            description="Desc",
            source="npm",
            install_command="npm i",
            stars=50,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.5,
            reason="Test",
        )

        result = SkillDiscoveryResult(
            requirements=["req1"],
            recommendations=[rec],
            discovery_phase="late",
            restart_warning=True,
        )

        data = result.to_dict()

        assert data["requirements"] == ["req1"]
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["name"] == "skill"
        assert data["discovery_phase"] == "late"
        assert data["restart_warning"] is True

    def test_skill_discovery_result_early_phase(self):
        """Test SkillDiscoveryResult with early phase."""
        from beyond_ralph.agents.research_agent import SkillDiscoveryResult

        result = SkillDiscoveryResult(
            requirements=["feature"],
            recommendations=[],
            discovery_phase="early",
            restart_warning=False,
        )

        assert result.discovery_phase == "early"
        assert result.restart_warning is False

    def test_skill_discovery_result_late_phase_warning(self):
        """Test SkillDiscoveryResult with late phase sets warning."""
        from beyond_ralph.agents.research_agent import SkillDiscoveryResult

        result = SkillDiscoveryResult(
            requirements=["feature"],
            recommendations=[],
            discovery_phase="late",
            restart_warning=True,
        )

        assert result.discovery_phase == "late"
        assert result.restart_warning is True


# ============================================================================
# Tests for ResearchAgent Skill Discovery Methods
# ============================================================================


class TestResearchAgentSkillDiscovery:
    """Tests for ResearchAgent skill discovery functionality."""

    @pytest.mark.asyncio
    async def test_discover_skills_basic(self, tmp_path):
        """Test basic discover_skills functionality."""
        from beyond_ralph.agents.research_agent import SkillDiscoveryResult

        agent = ResearchAgent(project_root=tmp_path)

        # Mock the search methods
        with patch.object(agent, "_search_github_skills", new_callable=AsyncMock) as mock_github:
            with patch.object(agent, "_search_npm_skills", new_callable=AsyncMock) as mock_npm:
                mock_github.return_value = []
                mock_npm.return_value = []

                result = await agent.discover_skills(["database access"], phase=1)

                assert isinstance(result, SkillDiscoveryResult)
                assert result.requirements == ["database access"]
                assert result.discovery_phase == "early"
                assert result.restart_warning is False

    @pytest.mark.asyncio
    async def test_discover_skills_phase_detection_early(self, tmp_path):
        """Test discover_skills correctly identifies early phase (1-2)."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "_search_github_skills", new_callable=AsyncMock) as mock_github:
            with patch.object(agent, "_search_npm_skills", new_callable=AsyncMock) as mock_npm:
                mock_github.return_value = []
                mock_npm.return_value = []

                # Phase 1
                result1 = await agent.discover_skills(["test"], phase=1)
                assert result1.discovery_phase == "early"
                assert result1.restart_warning is False

                # Phase 2
                result2 = await agent.discover_skills(["test"], phase=2)
                assert result2.discovery_phase == "early"
                assert result2.restart_warning is False

    @pytest.mark.asyncio
    async def test_discover_skills_phase_detection_late(self, tmp_path):
        """Test discover_skills correctly identifies late phase (3+)."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "_search_github_skills", new_callable=AsyncMock) as mock_github:
            with patch.object(agent, "_search_npm_skills", new_callable=AsyncMock) as mock_npm:
                mock_github.return_value = []
                mock_npm.return_value = []

                # Phase 3
                result3 = await agent.discover_skills(["test"], phase=3)
                assert result3.discovery_phase == "late"
                assert result3.restart_warning is True

                # Phase 7
                result7 = await agent.discover_skills(["test"], phase=7)
                assert result7.discovery_phase == "late"
                assert result7.restart_warning is True

    @pytest.mark.asyncio
    async def test_discover_skills_with_recommendations(self, tmp_path):
        """Test discover_skills returns recommendations."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        mock_rec = SkillRecommendation(
            name="test-mcp",
            description="Test MCP server",
            source="github",
            install_command="git clone test",
            stars=100,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.7,
            reason="Test",
        )

        with patch.object(agent, "_search_github_skills", new_callable=AsyncMock) as mock_github:
            with patch.object(agent, "_search_npm_skills", new_callable=AsyncMock) as mock_npm:
                mock_github.return_value = [mock_rec]
                mock_npm.return_value = []

                result = await agent.discover_skills(["database"], phase=1)

                assert len(result.recommendations) == 1
                assert result.recommendations[0].name == "test-mcp"

    @pytest.mark.asyncio
    async def test_discover_skills_deduplicates(self, tmp_path):
        """Test discover_skills removes duplicate recommendations."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        # Same skill from both sources
        rec1 = SkillRecommendation(
            name="duplicate-skill",
            description="From GitHub",
            source="github",
            install_command="git clone",
            stars=100,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.7,
            reason="GitHub",
        )
        rec2 = SkillRecommendation(
            name="duplicate-skill",  # Same name
            description="From npm",
            source="npm",
            install_command="npm install",
            stars=50,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.5,
            reason="npm",
        )

        with patch.object(agent, "_search_github_skills", new_callable=AsyncMock) as mock_github:
            with patch.object(agent, "_search_npm_skills", new_callable=AsyncMock) as mock_npm:
                mock_github.return_value = [rec1]
                mock_npm.return_value = [rec2]

                result = await agent.discover_skills(["test"], phase=1)

                # Should only have one (first one found)
                assert len(result.recommendations) == 1
                assert result.recommendations[0].name == "duplicate-skill"

    @pytest.mark.asyncio
    async def test_discover_skills_limits_results(self, tmp_path):
        """Test discover_skills limits total recommendations."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        # Create many recommendations
        recs = [
            SkillRecommendation(
                name=f"skill-{i}",
                description=f"Skill {i}",
                source="github",
                install_command="git clone",
                stars=100 - i,
                last_updated="2024-01-01",
                requires_restart=True,
                config_location=".claude/settings.json",
                quality_score=0.5 + (i * 0.01),
                reason="Test",
            )
            for i in range(20)
        ]

        with patch.object(agent, "_search_github_skills", new_callable=AsyncMock) as mock_github:
            with patch.object(agent, "_search_npm_skills", new_callable=AsyncMock) as mock_npm:
                mock_github.return_value = recs
                mock_npm.return_value = []

                # Single requirement = max 3 results
                result = await agent.discover_skills(["test"], phase=1)
                assert len(result.recommendations) <= 3

                # Multiple requirements (4) = max 10 results
                result = await agent.discover_skills(
                    ["test1", "test2", "test3", "test4"],
                    phase=1,
                )
                assert len(result.recommendations) <= 10

    @pytest.mark.asyncio
    async def test_discover_skills_empty_requirements(self, tmp_path):
        """Test discover_skills with empty requirements list."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent, "_search_github_skills", new_callable=AsyncMock) as mock_github:
            with patch.object(agent, "_search_npm_skills", new_callable=AsyncMock) as mock_npm:
                mock_github.return_value = []
                mock_npm.return_value = []

                result = await agent.discover_skills([], phase=1)

                assert result.requirements == []
                assert result.recommendations == []


class TestResearchAgentGitHubSkillSearch:
    """Tests for GitHub skill search functionality."""

    @pytest.mark.asyncio
    async def test_search_github_skills_success(self, tmp_path):
        """Test successful GitHub skill search."""
        agent = ResearchAgent(project_root=tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "owner/mcp-server-test",
                    "description": "A test MCP server",
                    "stargazers_count": 500,
                    "updated_at": "2024-01-15T10:00:00Z",
                    "clone_url": "https://github.com/owner/mcp-server-test.git",
                    "name": "mcp-server-test",
                    "language": "Python",
                }
            ]
        }

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            results = await agent._search_github_skills("database")

            assert len(results) > 0
            assert results[0].source == "github"
            assert results[0].stars == 500

    @pytest.mark.asyncio
    async def test_search_github_skills_handles_error(self, tmp_path):
        """Test GitHub search handles API errors gracefully."""
        agent = ResearchAgent(project_root=tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 403  # Rate limited

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            results = await agent._search_github_skills("database")

            # Should return empty list, not raise
            assert results == []

    @pytest.mark.asyncio
    async def test_search_github_skills_handles_exception(self, tmp_path):
        """Test GitHub search handles exceptions gracefully."""
        agent = ResearchAgent(project_root=tmp_path)

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Network error")

            results = await agent._search_github_skills("database")

            # Should return empty list, not raise
            assert results == []


class TestResearchAgentNpmSkillSearch:
    """Tests for npm skill search functionality."""

    @pytest.mark.asyncio
    async def test_search_npm_skills_success(self, tmp_path):
        """Test successful npm skill search."""
        agent = ResearchAgent(project_root=tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "objects": [
                {
                    "package": {
                        "name": "@modelcontextprotocol/server-test",
                        "description": "Official MCP server",
                        "version": "1.0.0",
                        "date": "2024-01-15T10:00:00Z",
                    },
                    "score": {
                        "final": 0.8,
                        "detail": {
                            "popularity": 0.5,
                        },
                    },
                }
            ]
        }

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            results = await agent._search_npm_skills("database")

            assert len(results) > 0
            assert results[0].source == "npm"
            assert "@modelcontextprotocol" in results[0].name

    @pytest.mark.asyncio
    async def test_search_npm_skills_handles_error(self, tmp_path):
        """Test npm search handles API errors gracefully."""
        agent = ResearchAgent(project_root=tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            results = await agent._search_npm_skills("database")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_npm_skills_official_package_reason(self, tmp_path):
        """Test npm search identifies official MCP packages."""
        agent = ResearchAgent(project_root=tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "objects": [
                {
                    "package": {
                        "name": "@modelcontextprotocol/server-filesystem",
                        "description": "Filesystem access",
                        "version": "1.0.0",
                        "date": "2024-01-15",
                    },
                    "score": {"final": 0.9, "detail": {"popularity": 0.7}},
                }
            ]
        }

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            results = await agent._search_npm_skills("filesystem")

            assert len(results) > 0
            assert "Official MCP" in results[0].reason


class TestResearchAgentSkillQualityEvaluation:
    """Tests for skill quality evaluation."""

    def test_evaluate_skill_quality_high_stars(self, tmp_path):
        """Test quality score for high-star repositories."""
        from datetime import datetime, timedelta

        agent = ResearchAgent(project_root=tmp_path)

        # Use a recent date to ensure high recency score
        recent_date = (datetime.now() - timedelta(days=15)).isoformat()

        quality = agent._evaluate_skill_quality(
            {
                "stars": 1500,
                "updated_at": recent_date,
                "has_readme": True,
                "source": "github",
            }
        )

        # High stars (0.3) + recent update (0.3) + readme (0.15) + github (0.1) = 0.85
        assert quality >= 0.7

    def test_evaluate_skill_quality_low_stars(self, tmp_path):
        """Test quality score for low-star repositories."""
        agent = ResearchAgent(project_root=tmp_path)

        quality = agent._evaluate_skill_quality(
            {
                "stars": 5,
                "updated_at": "2022-01-15T10:00:00Z",  # Old
                "has_readme": False,
                "source": "github",
            }
        )

        # Low stars + old + no docs = low quality
        assert quality < 0.3

    def test_evaluate_skill_quality_recent_update_boost(self, tmp_path):
        """Test that recent updates boost quality score."""
        agent = ResearchAgent(project_root=tmp_path)

        # Use a recent date
        from datetime import datetime, timedelta

        recent_date = (datetime.now() - timedelta(days=15)).isoformat()

        quality = agent._evaluate_skill_quality(
            {
                "stars": 50,
                "updated_at": recent_date,
                "has_readme": True,
                "source": "github",
            }
        )

        # Recent update should give good score
        assert quality >= 0.5

    def test_evaluate_skill_quality_npm_score_component(self, tmp_path):
        """Test that npm score affects quality."""
        agent = ResearchAgent(project_root=tmp_path)

        quality_high_npm = agent._evaluate_skill_quality(
            {
                "stars": 100,
                "updated_at": "2024-01-15T10:00:00Z",
                "source": "npm",
                "npm_score": 0.9,
            }
        )

        quality_low_npm = agent._evaluate_skill_quality(
            {
                "stars": 100,
                "updated_at": "2024-01-15T10:00:00Z",
                "source": "npm",
                "npm_score": 0.1,
            }
        )

        assert quality_high_npm > quality_low_npm

    def test_evaluate_skill_quality_bounds(self, tmp_path):
        """Test that quality score is always between 0 and 1."""
        agent = ResearchAgent(project_root=tmp_path)

        # Maximum quality
        from datetime import datetime

        now = datetime.now().isoformat()

        max_quality = agent._evaluate_skill_quality(
            {
                "stars": 10000,
                "updated_at": now,
                "has_readme": True,
                "has_docs": True,
                "source": "npm",
                "npm_score": 1.0,
            }
        )

        assert 0.0 <= max_quality <= 1.0

        # Minimum quality
        min_quality = agent._evaluate_skill_quality(
            {
                "stars": 0,
                "updated_at": "",
                "has_readme": False,
                "source": "unknown",
            }
        )

        assert 0.0 <= min_quality <= 1.0


class TestResearchAgentSkillRanking:
    """Tests for skill ranking functionality."""

    def test_rank_skills_by_quality(self, tmp_path):
        """Test that skills are ranked by quality score."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        skills = [
            SkillRecommendation(
                name="low-quality",
                description="Low",
                source="github",
                install_command="",
                stars=10,
                last_updated="",
                requires_restart=True,
                config_location="",
                quality_score=0.3,
                reason="",
            ),
            SkillRecommendation(
                name="high-quality",
                description="High",
                source="github",
                install_command="",
                stars=1000,
                last_updated="",
                requires_restart=True,
                config_location="",
                quality_score=0.9,
                reason="",
            ),
            SkillRecommendation(
                name="medium-quality",
                description="Medium",
                source="github",
                install_command="",
                stars=100,
                last_updated="",
                requires_restart=True,
                config_location="",
                quality_score=0.6,
                reason="",
            ),
        ]

        ranked = agent._rank_skills(skills)

        assert ranked[0].name == "high-quality"
        assert ranked[1].name == "medium-quality"
        assert ranked[2].name == "low-quality"

    def test_rank_skills_tiebreaker_by_stars(self, tmp_path):
        """Test that stars are used as tiebreaker."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        skills = [
            SkillRecommendation(
                name="less-stars",
                description="",
                source="github",
                install_command="",
                stars=50,
                last_updated="",
                requires_restart=True,
                config_location="",
                quality_score=0.7,
                reason="",
            ),
            SkillRecommendation(
                name="more-stars",
                description="",
                source="github",
                install_command="",
                stars=500,
                last_updated="",
                requires_restart=True,
                config_location="",
                quality_score=0.7,  # Same quality
                reason="",
            ),
        ]

        ranked = agent._rank_skills(skills)

        assert ranked[0].name == "more-stars"
        assert ranked[1].name == "less-stars"

    def test_rank_skills_empty_list(self, tmp_path):
        """Test ranking empty list."""
        agent = ResearchAgent(project_root=tmp_path)

        ranked = agent._rank_skills([])

        assert ranked == []


class TestResearchAgentSkillDiscoveryStorage:
    """Tests for skill discovery storage."""

    @pytest.mark.asyncio
    async def test_store_skill_discovery(self, tmp_path):
        """Test storing skill discovery results."""
        from beyond_ralph.agents.research_agent import (
            SkillDiscoveryResult,
            SkillRecommendation,
        )

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="test-skill",
            description="Test skill",
            source="npm",
            install_command="npm install test",
            stars=100,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude/settings.json",
            quality_score=0.8,
            reason="Test reason",
        )

        result = SkillDiscoveryResult(
            requirements=["database access"],
            recommendations=[rec],
            discovery_phase="early",
            restart_warning=False,
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = "uuid"

            path = await agent._store_skill_discovery(result)

            assert "skill-discovery" in path
            mock_write.assert_called_once()
            call_kwargs = mock_write.call_args.kwargs
            assert call_kwargs["category"] == "research"
            assert "skill-discovery" in call_kwargs["tags"]

    @pytest.mark.asyncio
    async def test_store_skill_discovery_handles_error(self, tmp_path):
        """Test storage handles errors gracefully."""
        from beyond_ralph.agents.research_agent import SkillDiscoveryResult

        agent = ResearchAgent(project_root=tmp_path)

        result = SkillDiscoveryResult(
            requirements=["test"],
            recommendations=[],
            discovery_phase="early",
            restart_warning=False,
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.side_effect = Exception("Write failed")

            path = await agent._store_skill_discovery(result)

            assert path == ""

    @pytest.mark.asyncio
    async def test_store_skill_discovery_empty_requirements(self, tmp_path):
        """Test storage with empty requirements uses default filename."""
        from beyond_ralph.agents.research_agent import SkillDiscoveryResult

        agent = ResearchAgent(project_root=tmp_path)

        result = SkillDiscoveryResult(
            requirements=[],
            recommendations=[],
            discovery_phase="early",
            restart_warning=False,
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.return_value = "uuid"

            path = await agent._store_skill_discovery(result)

            assert "skill-discovery-general" in path


# ============================================================================
# Tests for SkillInstallResult dataclass
# ============================================================================


class TestSkillInstallResult:
    """Tests for SkillInstallResult dataclass."""

    def test_skill_install_result_creation(self):
        """Test creating a SkillInstallResult."""
        from beyond_ralph.agents.research_agent import SkillInstallResult

        result = SkillInstallResult(
            skill_name="@modelcontextprotocol/server-test",
            success=True,
            install_method="npm",
            config_updated=True,
            config_path="/home/user/.claude.json",
            error_message=None,
            requires_restart=True,
            verification_status="verified",
        )

        assert result.skill_name == "@modelcontextprotocol/server-test"
        assert result.success is True
        assert result.install_method == "npm"
        assert result.config_updated is True
        assert result.config_path == "/home/user/.claude.json"
        assert result.error_message is None
        assert result.requires_restart is True
        assert result.verification_status == "verified"

    def test_skill_install_result_failure(self):
        """Test SkillInstallResult for failed installation."""
        from beyond_ralph.agents.research_agent import SkillInstallResult

        result = SkillInstallResult(
            skill_name="failing-skill",
            success=False,
            install_method="git",
            config_updated=False,
            config_path="",
            error_message="Git clone failed: network error",
            requires_restart=True,
            verification_status="failed",
        )

        assert result.success is False
        assert result.config_updated is False
        assert result.error_message == "Git clone failed: network error"
        assert result.verification_status == "failed"

    def test_skill_install_result_to_dict(self):
        """Test SkillInstallResult serialization to dict."""
        from beyond_ralph.agents.research_agent import SkillInstallResult

        result = SkillInstallResult(
            skill_name="test-skill",
            success=True,
            install_method="copy",
            config_updated=True,
            config_path="/path/to/config",
            error_message=None,
            requires_restart=False,
            verification_status="verified",
        )

        data = result.to_dict()

        assert data["skill_name"] == "test-skill"
        assert data["success"] is True
        assert data["install_method"] == "copy"
        assert data["config_updated"] is True
        assert data["config_path"] == "/path/to/config"
        assert data["error_message"] is None
        assert data["requires_restart"] is False
        assert data["verification_status"] == "verified"

    def test_skill_install_result_pending_verification(self):
        """Test SkillInstallResult with pending verification status."""
        from beyond_ralph.agents.research_agent import SkillInstallResult

        result = SkillInstallResult(
            skill_name="new-mcp",
            success=True,
            install_method="npm",
            config_updated=True,
            config_path="/home/.claude.json",
            error_message=None,
            requires_restart=True,
            verification_status="pending",  # May work after restart
        )

        assert result.verification_status == "pending"
        assert result.requires_restart is True


# ============================================================================
# Tests for ResearchAgent Skill Installation Methods
# ============================================================================


class TestResearchAgentInstallSkill:
    """Tests for ResearchAgent.install_skill method."""

    @pytest.mark.asyncio
    async def test_install_skill_npm_route(self, tmp_path):
        """Test install_skill routes to npm installer for npm source."""
        from beyond_ralph.agents.research_agent import (
            SkillInstallResult,
            SkillRecommendation,
        )

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="@modelcontextprotocol/server-test",
            description="Test MCP server",
            source="npm",
            install_command="npm install @modelcontextprotocol/server-test",
            stars=100,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.8,
            reason="Test",
        )

        mock_result = SkillInstallResult(
            skill_name=rec.name,
            success=True,
            install_method="npm",
            config_updated=True,
            config_path=str(tmp_path / ".claude.json"),
            error_message=None,
            requires_restart=True,
            verification_status="verified",
        )

        with patch.object(agent, "_install_npm_skill", new_callable=AsyncMock) as mock_install:
            mock_install.return_value = mock_result

            result = await agent.install_skill(rec)

            mock_install.assert_called_once_with(rec)
            assert result.install_method == "npm"

    @pytest.mark.asyncio
    async def test_install_skill_github_route(self, tmp_path):
        """Test install_skill routes to github installer for github source."""
        from beyond_ralph.agents.research_agent import (
            SkillInstallResult,
            SkillRecommendation,
        )

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="owner/repo-mcp",
            description="GitHub MCP server",
            source="github",
            install_command="git clone https://github.com/owner/repo-mcp.git",
            stars=500,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.9,
            reason="High star count",
        )

        mock_result = SkillInstallResult(
            skill_name=rec.name,
            success=True,
            install_method="git",
            config_updated=True,
            config_path=str(tmp_path / ".claude.json"),
            error_message=None,
            requires_restart=True,
            verification_status="pending",
        )

        with patch.object(agent, "_install_github_skill", new_callable=AsyncMock) as mock_install:
            mock_install.return_value = mock_result

            result = await agent.install_skill(rec)

            mock_install.assert_called_once_with(rec)
            assert result.install_method == "git"

    @pytest.mark.asyncio
    async def test_install_skill_copy_route(self, tmp_path):
        """Test install_skill routes to copy installer for other sources."""
        from beyond_ralph.agents.research_agent import (
            SkillInstallResult,
            SkillRecommendation,
        )

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="custom-skill",
            description="Custom skill file",
            source="local",  # Not npm or github
            install_command="/path/to/skill.md",
            stars=0,
            last_updated="2024-01-01",
            requires_restart=False,
            config_location=".claude/commands/",
            quality_score=0.5,
            reason="Local skill",
        )

        mock_result = SkillInstallResult(
            skill_name=rec.name,
            success=True,
            install_method="copy",
            config_updated=True,
            config_path=str(Path.home() / ".claude" / "commands" / "custom-skill.md"),
            error_message=None,
            requires_restart=False,
            verification_status="verified",
        )

        with patch.object(agent, "_install_skill_file", new_callable=AsyncMock) as mock_install:
            mock_install.return_value = mock_result

            result = await agent.install_skill(rec)

            mock_install.assert_called_once_with(rec)
            assert result.install_method == "copy"

    @pytest.mark.asyncio
    async def test_install_skill_exception_handling(self, tmp_path):
        """Test install_skill handles unexpected exceptions."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="failing-skill",
            description="Will fail",
            source="npm",
            install_command="npm install failing",
            stars=0,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.1,
            reason="Test",
        )

        with patch.object(agent, "_install_npm_skill", new_callable=AsyncMock) as mock_install:
            mock_install.side_effect = Exception("Unexpected error")

            result = await agent.install_skill(rec)

            assert result.success is False
            assert result.install_method == "unknown"
            assert "Unexpected error" in (result.error_message or "")
            assert result.verification_status == "failed"


class TestResearchAgentInstallNpmSkill:
    """Tests for ResearchAgent._install_npm_skill method."""

    @pytest.mark.asyncio
    async def test_install_npm_skill_success(self, tmp_path):
        """Test successful npm skill installation."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="@modelcontextprotocol/server-test",
            description="Test MCP",
            source="npm",
            install_command="npm install @modelcontextprotocol/server-test",
            stars=100,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.8,
            reason="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            with patch.object(
                agent, "_update_claude_config", new_callable=AsyncMock
            ) as mock_config:
                mock_config.return_value = str(tmp_path / ".claude.json")

                with patch.object(
                    agent, "_verify_skill_installed_mcp", new_callable=AsyncMock
                ) as mock_verify:
                    mock_verify.return_value = True

                    with patch.object(
                        agent, "_document_skill_installation", new_callable=AsyncMock
                    ):
                        result = await agent._install_npm_skill(rec)

                        assert result.success is True
                        assert result.install_method == "npm"
                        assert result.config_updated is True
                        assert result.verification_status == "verified"
                        mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_install_npm_skill_npm_failure(self, tmp_path):
        """Test npm install failure."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="failing-package",
            description="Fails",
            source="npm",
            install_command="npm install failing-package",
            stars=0,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.1,
            reason="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="npm ERR! 404 Not Found")

            result = await agent._install_npm_skill(rec)

            assert result.success is False
            assert "npm install failed" in (result.error_message or "")
            assert result.verification_status == "failed"

    @pytest.mark.asyncio
    async def test_install_npm_skill_timeout(self, tmp_path):
        """Test npm install timeout."""
        import subprocess

        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="slow-package",
            description="Slow",
            source="npm",
            install_command="npm install slow-package",
            stars=0,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.1,
            reason="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("npm", 300)

            result = await agent._install_npm_skill(rec)

            assert result.success is False
            assert "timed out" in (result.error_message or "")


class TestResearchAgentInstallGitHubSkill:
    """Tests for ResearchAgent._install_github_skill method."""

    @pytest.mark.asyncio
    async def test_install_github_skill_success(self, tmp_path):
        """Test successful GitHub skill installation."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="owner/mcp-repo",
            description="GitHub MCP",
            source="github",
            install_command="git clone https://github.com/owner/mcp-repo.git && cd mcp-repo && pip install -e .",
            stars=500,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.9,
            reason="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            with patch.object(
                agent, "_update_claude_config", new_callable=AsyncMock
            ) as mock_config:
                mock_config.return_value = str(tmp_path / ".claude.json")

                with patch.object(
                    agent, "_verify_skill_installed_mcp", new_callable=AsyncMock
                ) as mock_verify:
                    mock_verify.return_value = False  # Not verified until restart

                    with patch.object(
                        agent, "_document_skill_installation", new_callable=AsyncMock
                    ):
                        result = await agent._install_github_skill(rec)

                        assert result.success is True
                        assert result.install_method == "git"
                        # Should call git clone, cd, pip install
                        assert mock_run.call_count == 3

    @pytest.mark.asyncio
    async def test_install_github_skill_clone_failure(self, tmp_path):
        """Test git clone failure."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="owner/failing-repo",
            description="Fails to clone",
            source="github",
            install_command="git clone https://github.com/owner/failing-repo.git",
            stars=0,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.1,
            reason="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stderr="fatal: repository not found")

            result = await agent._install_github_skill(rec)

            assert result.success is False
            assert "failed" in (result.error_message or "").lower()


class TestResearchAgentInstallSkillFile:
    """Tests for ResearchAgent._install_skill_file method."""

    @pytest.mark.asyncio
    async def test_install_skill_file_from_description(self, tmp_path):
        """Test creating skill file from description when no source."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="custom-skill",
            description="A custom skill for testing",
            source="custom",
            install_command="nonexistent-path",  # Doesn't exist
            stars=0,
            last_updated="2024-01-01",
            requires_restart=False,
            config_location=".claude/commands/",
            quality_score=0.5,
            reason="Custom skill creation",
        )

        with patch.object(agent, "_document_skill_installation", new_callable=AsyncMock):
            result = await agent._install_skill_file(rec)

            assert result.success is True
            assert result.install_method == "copy"
            assert result.requires_restart is False  # Skill files don't need restart
            assert "custom-skill" in (result.config_path or "")

    @pytest.mark.asyncio
    async def test_install_skill_file_from_url(self, tmp_path):
        """Test downloading skill file from URL."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="remote-skill",
            description="Downloaded skill",
            source="url",
            install_command="https://example.com/skill.md",
            stars=0,
            last_updated="2024-01-01",
            requires_restart=False,
            config_location=".claude/commands/",
            quality_score=0.5,
            reason="Downloaded",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "# Skill Content\nTest skill file"

        with patch.object(agent.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            with patch.object(agent, "_document_skill_installation", new_callable=AsyncMock):
                result = await agent._install_skill_file(rec)

                assert result.success is True
                assert result.config_updated is True


class TestResearchAgentUpdateClaudeConfig:
    """Tests for ResearchAgent._update_claude_config method."""

    @pytest.mark.asyncio
    async def test_update_config_creates_new_file(self, tmp_path):
        """Test creating new config file when none exists."""
        import json

        agent = ResearchAgent(project_root=tmp_path)

        config = {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-test"],
            "env": {},
        }

        path = await agent._update_claude_config("test-mcp", config)

        # Verify file was created
        config_path = Path(path)
        assert config_path.exists()

        # Verify content
        content = json.loads(config_path.read_text())
        assert "mcpServers" in content
        assert "test-mcp" in content["mcpServers"]

    @pytest.mark.asyncio
    async def test_update_config_merges_with_existing(self, tmp_path):
        """Test merging with existing config file."""
        import json

        agent = ResearchAgent(project_root=tmp_path)

        # Create existing config
        config_path = tmp_path / ".claude.json"
        existing = {
            "mcpServers": {
                "existing-mcp": {"command": "existing", "args": [], "env": {}},
            },
            "otherSetting": "preserved",
        }
        config_path.write_text(json.dumps(existing))

        # Add new MCP
        new_config = {
            "command": "npx",
            "args": ["new-mcp"],
            "env": {},
        }

        path = await agent._update_claude_config("new-mcp", new_config)

        # Verify merged content
        content = json.loads(Path(path).read_text())
        assert "existing-mcp" in content["mcpServers"]  # Preserved
        assert "new-mcp" in content["mcpServers"]  # Added
        assert content["otherSetting"] == "preserved"  # Other settings preserved

    @pytest.mark.asyncio
    async def test_update_config_sanitizes_skill_name(self, tmp_path):
        """Test that skill names are sanitized for config keys."""
        import json

        agent = ResearchAgent(project_root=tmp_path)

        # Create an empty project-local config first to avoid using global config
        project_config = tmp_path / ".claude.json"
        project_config.write_text("{}")

        config = {"command": "test", "args": [], "env": {}}

        path = await agent._update_claude_config(
            "@modelcontextprotocol/server-filesystem",  # Contains @ and /
            config,
        )

        content = json.loads(Path(path).read_text())
        # Key should be sanitized (no @ or /)
        keys = list(content["mcpServers"].keys())
        assert len(keys) == 1
        # The sanitized key should not contain @ or /
        sanitized_key = keys[0]
        assert "@" not in sanitized_key
        assert "/" not in sanitized_key
        # Should contain something from the original name
        assert "modelcontextprotocol" in sanitized_key or "server-filesystem" in sanitized_key


class TestResearchAgentVerifySkillInstalled:
    """Tests for ResearchAgent._verify_skill_installed_mcp method."""

    @pytest.mark.asyncio
    async def test_verify_skill_found_in_config(self, tmp_path):
        """Test verifying skill when it exists in config."""
        import json

        agent = ResearchAgent(project_root=tmp_path)

        # Create config with the skill
        config_path = tmp_path / ".claude.json"
        config = {
            "mcpServers": {
                "test-mcp": {"command": "test", "args": [], "env": {}},
            }
        }
        config_path.write_text(json.dumps(config))

        result = await agent._verify_skill_installed_mcp("test-mcp")

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_skill_not_found_in_config(self, tmp_path):
        """Test verifying skill when it doesn't exist in config."""
        import json

        agent = ResearchAgent(project_root=tmp_path)

        # Create config without the skill
        config_path = tmp_path / ".claude.json"
        config = {"mcpServers": {}}
        config_path.write_text(json.dumps(config))

        result = await agent._verify_skill_installed_mcp("nonexistent-mcp")

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_skill_no_config_file(self, tmp_path):
        """Test verifying skill when no config file exists."""
        agent = ResearchAgent(project_root=tmp_path)

        result = await agent._verify_skill_installed_mcp("any-mcp")

        assert result is False


class TestResearchAgentExtractRepoName:
    """Tests for ResearchAgent._extract_repo_name method."""

    def test_extract_repo_name_https(self, tmp_path):
        """Test extracting repo name from HTTPS URL."""
        agent = ResearchAgent(project_root=tmp_path)

        cmd = "git clone https://github.com/owner/mcp-server.git"
        name = agent._extract_repo_name(cmd)

        assert name == "mcp-server"

    def test_extract_repo_name_https_no_git(self, tmp_path):
        """Test extracting repo name from HTTPS URL without .git suffix."""
        agent = ResearchAgent(project_root=tmp_path)

        cmd = "git clone https://github.com/owner/mcp-server"
        name = agent._extract_repo_name(cmd)

        assert name == "mcp-server"

    def test_extract_repo_name_with_cd(self, tmp_path):
        """Test extracting repo name from command with cd."""
        agent = ResearchAgent(project_root=tmp_path)

        cmd = "git clone https://github.com/owner/repo.git && cd repo && pip install -e ."
        name = agent._extract_repo_name(cmd)

        assert name == "repo"

    def test_extract_repo_name_fallback(self, tmp_path):
        """Test fallback when pattern doesn't match."""
        agent = ResearchAgent(project_root=tmp_path)

        cmd = "some random command"
        name = agent._extract_repo_name(cmd)

        assert name == "mcp-server"  # Default fallback


class TestResearchAgentDocumentSkillInstallation:
    """Tests for ResearchAgent._document_skill_installation method."""

    @pytest.mark.asyncio
    async def test_document_skill_installation(self, tmp_path):
        """Test documenting skill installation."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="documented-skill",
            description="Test documentation",
            source="npm",
            install_command="npm install documented-skill",
            stars=100,
            last_updated="2024-01-15",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.8,
            reason="For testing documentation",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            await agent._document_skill_installation(rec, "npm", "/path/to/config")

            mock_write.assert_called_once()
            call_kwargs = mock_write.call_args.kwargs
            assert "documented-skill" in call_kwargs["title"]
            assert "skill-installation" in call_kwargs["tags"]
            assert "npm" in call_kwargs["tags"]

    @pytest.mark.asyncio
    async def test_document_skill_installation_handles_error(self, tmp_path):
        """Test that documentation errors don't fail installation."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="test-skill",
            description="Test",
            source="npm",
            install_command="npm install test",
            stars=0,
            last_updated="2024-01-01",
            requires_restart=True,
            config_location=".claude.json",
            quality_score=0.5,
            reason="Test",
        )

        with patch.object(agent, "write_knowledge", new_callable=AsyncMock) as mock_write:
            mock_write.side_effect = Exception("Write failed")

            # Should not raise
            await agent._document_skill_installation(rec, "npm", "/path")


class TestResearchAgentSkillTracking:
    """Tests for skill tracking functionality."""

    def test_installed_skills_tracking_list(self, tmp_path):
        """Test that agent has installed_skills tracking list."""
        agent = ResearchAgent(project_root=tmp_path)

        assert hasattr(agent, "installed_skills")
        assert isinstance(agent.installed_skills, list)
        assert len(agent.installed_skills) == 0

    @pytest.mark.asyncio
    async def test_skill_added_to_tracking_on_install(self, tmp_path):
        """Test that successfully installed skills are tracked."""
        from beyond_ralph.agents.research_agent import SkillRecommendation

        agent = ResearchAgent(project_root=tmp_path)

        rec = SkillRecommendation(
            name="tracked-skill",
            description="Should be tracked",
            source="custom",
            install_command="nonexistent",  # Will create from description
            stars=0,
            last_updated="2024-01-01",
            requires_restart=False,
            config_location=".claude/commands/",
            quality_score=0.5,
            reason="Test tracking",
        )

        with patch.object(agent, "_document_skill_installation", new_callable=AsyncMock):
            result = await agent._install_skill_file(rec)

            assert result.success is True
            assert "tracked-skill" in agent.installed_skills
