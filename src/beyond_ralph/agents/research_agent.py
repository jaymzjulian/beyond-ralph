"""Research Agent - Discovers and installs tools autonomously.

This agent searches the web, evaluates testing frameworks and other tools,
and installs them WITHOUT user approval once past the interview phase.

KEY BEHAVIORS:
1. Has preferred tools (Playwright for web, httpx for API, etc.)
2. Uses preferred tools when user hasn't specified
3. MANDATORY: When a tool fails, automatically find and install alternatives
4. Never asks user what alternative to try - just finds one
5. Documents all decisions in knowledge base

The interview phase is where all approval happens. After that, the system
operates autonomously in the contained environment.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
from bs4 import BeautifulSoup


class ToolCategory(Enum):
    """Categories of tools the research agent can discover."""

    TESTING_FRAMEWORK = "testing_framework"
    BROWSER_AUTOMATION = "browser_automation"
    MOCK_SERVER = "mock_server"
    SCREENSHOT_TOOL = "screenshot_tool"
    VIDEO_CAPTURE = "video_capture"
    PERFORMANCE_TOOL = "performance_tool"
    LINTING = "linting"
    DOCUMENTATION = "documentation"


@dataclass
class DiscoveredTool:
    """A tool discovered by the research agent."""

    name: str
    category: ToolCategory
    package_manager: str  # pip, npm, apt, brew, etc.
    package_name: str
    description: str
    github_stars: int | None
    last_updated: str | None
    platform_support: list[str]
    install_command: str
    documentation_url: str | None
    recommended: bool
    rationale: str


class ResearchAgent:
    """Autonomously discovers and installs tools.

    After the interview phase, this agent operates WITHOUT user approval.
    The contained environment assumption means we can install freely.

    MANDATORY BEHAVIORS:
    1. Pick preferred tools when user hasn't specified
    2. When a tool fails, automatically search for alternatives
    3. Install alternatives without asking
    4. Only give up after exhausting reasonable alternatives
    5. Document everything in knowledge base
    """

    # Preferred tools by category - used when user hasn't specified
    PREFERRED_TOOLS: dict[ToolCategory, str] = {
        ToolCategory.BROWSER_AUTOMATION: "playwright",
        ToolCategory.TESTING_FRAMEWORK: "pytest",
        ToolCategory.MOCK_SERVER: "respx",
        ToolCategory.SCREENSHOT_TOOL: "pillow",
        ToolCategory.VIDEO_CAPTURE: "opencv-python",
        ToolCategory.PERFORMANCE_TOOL: "locust",
        ToolCategory.LINTING: "ruff",
        ToolCategory.DOCUMENTATION: "mkdocs",
    }

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=30.0)
        self.discovered_cache: dict[str, list[DiscoveredTool]] = {}
        self.failed_tools: list[str] = []  # Track what's already been tried

    async def search_for_tool(
        self,
        need: str,
        platform: str,
        category: ToolCategory,
    ) -> list[DiscoveredTool]:
        """Search for tools matching a specific need.

        Args:
            need: What the tool needs to do (e.g., "test Electron apps")
            platform: Target platform (linux, windows, macos)
            category: Category of tool needed

        Returns:
            List of discovered tools, sorted by recommendation.
        """
        # TODO: Implement web search, GitHub search, package registry search
        # This is a placeholder showing the intended interface
        raise NotImplementedError("Research agent search not yet implemented")

    async def evaluate_tool(self, tool: DiscoveredTool) -> dict[str, Any]:
        """Evaluate a tool's suitability.

        Checks:
        - Is it actively maintained?
        - Does it support our platform?
        - What do users say about it?
        - How mature is the documentation?
        """
        raise NotImplementedError("Tool evaluation not yet implemented")

    async def install_tool(self, tool: DiscoveredTool) -> bool:
        """Install a tool WITHOUT user approval.

        Post-interview, we operate autonomously in the contained environment.
        Installation happens immediately.

        Args:
            tool: The tool to install

        Returns:
            True if installation succeeded, False otherwise
        """
        # TODO: Implement actual installation
        # - Use subprocess to run install commands
        # - Verify installation success
        # - Update knowledge base
        raise NotImplementedError("Tool installation not yet implemented")

    async def store_in_knowledge_base(self, tool: DiscoveredTool) -> None:
        """Store discovered tool in knowledge base for future projects."""
        raise NotImplementedError("Knowledge base storage not yet implemented")

    async def handle_tool_failure(
        self,
        failed_tool: str,
        error_message: str,
        category: ToolCategory,
        platform: str,
    ) -> DiscoveredTool | None:
        """MANDATORY: When a tool fails, find and install an alternative.

        This is NOT optional. Beyond Ralph MUST try alternatives before giving up.

        Args:
            failed_tool: Name of the tool that failed
            error_message: Why it failed
            category: What kind of tool we need
            platform: Target platform

        Returns:
            A working alternative, or None if no alternatives work
        """
        self.failed_tools.append(failed_tool)

        # Search for alternatives
        alternatives = await self.search_for_tool(
            need=f"alternative to {failed_tool} that works on {platform}",
            platform=platform,
            category=category,
        )

        # Filter out already-failed tools
        viable = [t for t in alternatives if t.name not in self.failed_tools]

        if not viable:
            return None

        # Try alternatives in order of recommendation
        for alt in sorted(viable, key=lambda t: t.recommended, reverse=True):
            success = await self.install_tool(alt)
            if success:
                # Document the failure and solution
                await self.store_failure_resolution(
                    failed_tool=failed_tool,
                    error=error_message,
                    solution=alt,
                    platform=platform,
                )
                return alt
            else:
                self.failed_tools.append(alt.name)

        return None

    async def store_failure_resolution(
        self,
        failed_tool: str,
        error: str,
        solution: DiscoveredTool,
        platform: str,
    ) -> None:
        """Document a tool failure and its resolution for future reference."""
        raise NotImplementedError("Failure resolution storage not yet implemented")

    def get_preferred_tool(self, category: ToolCategory) -> str:
        """Get Beyond Ralph's preferred tool for a category.

        Used when user hasn't specified a tool. Beyond Ralph has opinions.
        """
        return self.PREFERRED_TOOLS.get(category, "unknown")

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.aclose()
