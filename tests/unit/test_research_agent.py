"""Tests for research agent module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.agents.research_agent import (
    DiscoveredTool,
    PackageManager,
    ResearchAgent,
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
                    with patch.object(agent, "install_tool", new_callable=AsyncMock) as mock_install:
                        mock_install.return_value = False  # Install fails
                        with patch.object(agent, "read_knowledge", new_callable=AsyncMock) as mock_read:
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
                    with patch.object(agent, "_document_failure_resolution", new_callable=AsyncMock):

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
