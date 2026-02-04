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

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

from beyond_ralph.agents.base import AgentResult, AgentTask, BaseAgent


class ToolCategory(Enum):
    """Categories of tools the research agent can discover."""

    TESTING_FRAMEWORK = "testing_framework"
    BROWSER_AUTOMATION = "browser_automation"
    MOCK_SERVER = "mock_server"
    SCREENSHOT_TOOL = "screenshot_tool"
    VIDEO_CAPTURE = "video_capture"
    PERFORMANCE_TOOL = "performance_tool"
    LINTING = "linting"
    SECURITY_SCANNING = "security_scanning"
    DOCUMENTATION = "documentation"
    TYPE_CHECKING = "type_checking"
    DEPENDENCY_CHECK = "dependency_check"


class PackageManager(Enum):
    """Supported package managers."""

    PIP = "pip"
    NPM = "npm"
    CARGO = "cargo"
    GO = "go"
    APT = "apt"
    BREW = "brew"
    WINGET = "winget"
    CHOCOLATEY = "chocolatey"


@dataclass
class DiscoveredTool:
    """A tool discovered by the research agent."""

    name: str
    category: ToolCategory
    package_manager: PackageManager
    package_name: str
    description: str
    install_command: str
    github_stars: int | None = None
    last_updated: str | None = None
    platform_support: list[str] = field(default_factory=list)
    documentation_url: str | None = None
    recommended: bool = False
    rationale: str = ""
    version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "category": self.category.value,
            "package_manager": self.package_manager.value,
            "package_name": self.package_name,
            "description": self.description,
            "install_command": self.install_command,
            "github_stars": self.github_stars,
            "last_updated": self.last_updated,
            "platform_support": self.platform_support,
            "documentation_url": self.documentation_url,
            "recommended": self.recommended,
            "rationale": self.rationale,
            "version": self.version,
        }


class ResearchAgent(BaseAgent):
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

    name = "research"
    description = "Autonomous tool discovery and installation"
    tools = ["WebSearch", "WebFetch", "Bash", "Read", "Write"]

    # Preferred tools by category - used when user hasn't specified
    PREFERRED_TOOLS: dict[ToolCategory, DiscoveredTool] = {
        ToolCategory.BROWSER_AUTOMATION: DiscoveredTool(
            name="playwright",
            category=ToolCategory.BROWSER_AUTOMATION,
            package_manager=PackageManager.PIP,
            package_name="playwright",
            description="Cross-browser automation with Chromium, Firefox, WebKit",
            install_command="pip install playwright && playwright install chromium",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://playwright.dev/python/",
            recommended=True,
            rationale="Modern, reliable, maintained by Microsoft",
        ),
        ToolCategory.TESTING_FRAMEWORK: DiscoveredTool(
            name="pytest",
            category=ToolCategory.TESTING_FRAMEWORK,
            package_manager=PackageManager.PIP,
            package_name="pytest",
            description="Full-featured Python testing framework",
            install_command="pip install pytest pytest-cov pytest-asyncio",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://docs.pytest.org/",
            recommended=True,
            rationale="Industry standard, excellent plugins ecosystem",
        ),
        ToolCategory.MOCK_SERVER: DiscoveredTool(
            name="respx",
            category=ToolCategory.MOCK_SERVER,
            package_manager=PackageManager.PIP,
            package_name="respx",
            description="Mock HTTPX requests with pytest integration",
            install_command="pip install respx",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://lundberg.github.io/respx/",
            recommended=True,
            rationale="Native httpx mocking, pytest integration",
        ),
        ToolCategory.SCREENSHOT_TOOL: DiscoveredTool(
            name="pillow",
            category=ToolCategory.SCREENSHOT_TOOL,
            package_manager=PackageManager.PIP,
            package_name="pillow",
            description="Python Imaging Library for screenshots and image processing",
            install_command="pip install pillow",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://pillow.readthedocs.io/",
            recommended=True,
            rationale="Standard image library, widely used",
        ),
        ToolCategory.VIDEO_CAPTURE: DiscoveredTool(
            name="opencv-python",
            category=ToolCategory.VIDEO_CAPTURE,
            package_manager=PackageManager.PIP,
            package_name="opencv-python-headless",
            description="Computer vision library for video capture and analysis",
            install_command="pip install opencv-python-headless",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://docs.opencv.org/",
            recommended=True,
            rationale="Standard CV library, headless for CI",
        ),
        ToolCategory.PERFORMANCE_TOOL: DiscoveredTool(
            name="locust",
            category=ToolCategory.PERFORMANCE_TOOL,
            package_manager=PackageManager.PIP,
            package_name="locust",
            description="Modern load testing framework",
            install_command="pip install locust",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://docs.locust.io/",
            recommended=True,
            rationale="Python-based, easy to write load tests",
        ),
        ToolCategory.LINTING: DiscoveredTool(
            name="ruff",
            category=ToolCategory.LINTING,
            package_manager=PackageManager.PIP,
            package_name="ruff",
            description="Extremely fast Python linter, written in Rust",
            install_command="pip install ruff",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://docs.astral.sh/ruff/",
            recommended=True,
            rationale="10-100x faster than flake8, replaces many tools",
        ),
        ToolCategory.SECURITY_SCANNING: DiscoveredTool(
            name="semgrep",
            category=ToolCategory.SECURITY_SCANNING,
            package_manager=PackageManager.PIP,
            package_name="semgrep",
            description="Lightweight static analysis for security patterns",
            install_command="pip install semgrep",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://semgrep.dev/docs/",
            recommended=True,
            rationale="Multi-language, OWASP rules built-in",
        ),
        ToolCategory.TYPE_CHECKING: DiscoveredTool(
            name="mypy",
            category=ToolCategory.TYPE_CHECKING,
            package_manager=PackageManager.PIP,
            package_name="mypy",
            description="Static type checker for Python",
            install_command="pip install mypy",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://mypy.readthedocs.io/",
            recommended=True,
            rationale="Standard Python type checker",
        ),
        ToolCategory.DEPENDENCY_CHECK: DiscoveredTool(
            name="safety",
            category=ToolCategory.DEPENDENCY_CHECK,
            package_manager=PackageManager.PIP,
            package_name="safety",
            description="Check dependencies for known vulnerabilities",
            install_command="pip install safety",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://safetycli.com/",
            recommended=True,
            rationale="Simple, integrates with CI",
        ),
        ToolCategory.DOCUMENTATION: DiscoveredTool(
            name="mkdocs",
            category=ToolCategory.DOCUMENTATION,
            package_manager=PackageManager.PIP,
            package_name="mkdocs",
            description="Project documentation with Markdown",
            install_command="pip install mkdocs mkdocs-material",
            platform_support=["linux", "macos", "windows"],
            documentation_url="https://www.mkdocs.org/",
            recommended=True,
            rationale="Simple, beautiful themes with Material",
        ),
    }

    # Alternative tools when preferred fails
    ALTERNATIVES: dict[ToolCategory, list[DiscoveredTool]] = {
        ToolCategory.BROWSER_AUTOMATION: [
            DiscoveredTool(
                name="selenium",
                category=ToolCategory.BROWSER_AUTOMATION,
                package_manager=PackageManager.PIP,
                package_name="selenium",
                description="Browser automation framework",
                install_command="pip install selenium webdriver-manager",
                platform_support=["linux", "macos", "windows"],
                documentation_url="https://selenium.dev/documentation/",
                rationale="Older but widely supported",
            ),
            DiscoveredTool(
                name="puppeteer",
                category=ToolCategory.BROWSER_AUTOMATION,
                package_manager=PackageManager.NPM,
                package_name="puppeteer",
                description="Headless Chrome automation",
                install_command="npm install puppeteer",
                platform_support=["linux", "macos", "windows"],
                documentation_url="https://pptr.dev/",
                rationale="Chrome-specific, good for debugging",
            ),
        ],
        ToolCategory.TESTING_FRAMEWORK: [
            DiscoveredTool(
                name="unittest",
                category=ToolCategory.TESTING_FRAMEWORK,
                package_manager=PackageManager.PIP,
                package_name="",
                description="Python standard library testing",
                install_command="# Built-in, no install needed",
                platform_support=["linux", "macos", "windows"],
                rationale="Built-in, always available",
            ),
            DiscoveredTool(
                name="nose2",
                category=ToolCategory.TESTING_FRAMEWORK,
                package_manager=PackageManager.PIP,
                package_name="nose2",
                description="Successor to nose testing framework",
                install_command="pip install nose2",
                platform_support=["linux", "macos", "windows"],
                rationale="Alternative to pytest",
            ),
        ],
        ToolCategory.LINTING: [
            DiscoveredTool(
                name="flake8",
                category=ToolCategory.LINTING,
                package_manager=PackageManager.PIP,
                package_name="flake8",
                description="Python linting tool",
                install_command="pip install flake8",
                platform_support=["linux", "macos", "windows"],
                rationale="Classic Python linter",
            ),
            DiscoveredTool(
                name="pylint",
                category=ToolCategory.LINTING,
                package_manager=PackageManager.PIP,
                package_name="pylint",
                description="Python code analysis",
                install_command="pip install pylint",
                platform_support=["linux", "macos", "windows"],
                rationale="Comprehensive but slower",
            ),
        ],
        ToolCategory.SECURITY_SCANNING: [
            DiscoveredTool(
                name="bandit",
                category=ToolCategory.SECURITY_SCANNING,
                package_manager=PackageManager.PIP,
                package_name="bandit",
                description="Python security linter",
                install_command="pip install bandit",
                platform_support=["linux", "macos", "windows"],
                rationale="Python-specific security scanner",
            ),
        ],
    }

    def __init__(
        self,
        session_id: str | None = None,
        project_root: Path | None = None,
        knowledge_dir: Path | None = None,
    ) -> None:
        super().__init__(session_id, project_root, knowledge_dir)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.discovered_cache: dict[str, list[DiscoveredTool]] = {}
        self.failed_tools: list[str] = []
        self.installed_tools: list[str] = []

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute research task.

        Supports tasks like:
        - Find and install a tool for a category
        - Handle a tool failure and find alternative
        - Search for tools matching a need
        """
        task_type = task.context.get("type", "find_tool")

        if task_type == "find_tool":
            category_str = task.context.get("category")
            if not category_str:
                return self.fail("Missing 'category' in task context")

            try:
                category = ToolCategory(category_str)
            except ValueError:
                return self.fail(f"Unknown category: {category_str}")

            tool = await self.find_and_install_tool(
                category=category,
                need=task.description,
                platform=task.context.get("platform", self._detect_platform()),
            )

            if tool:
                return self.succeed(
                    output=f"Installed {tool.name} for {category.value}",
                    data={"tool": tool.to_dict()},
                )
            else:
                return self.fail(f"Could not find working tool for {category.value}")

        elif task_type == "handle_failure":
            failed_tool = task.context.get("failed_tool")
            error_message = task.context.get("error")
            category_str = task.context.get("category")

            if not all([failed_tool, category_str]):
                return self.fail("Missing required context for failure handling")

            try:
                category = ToolCategory(category_str)
            except ValueError:
                return self.fail(f"Unknown category: {category_str}")

            alternative = await self.handle_tool_failure(
                failed_tool=failed_tool,
                error_message=error_message or "Unknown error",
                category=category,
                platform=task.context.get("platform", self._detect_platform()),
            )

            if alternative:
                return self.succeed(
                    output=f"Replaced {failed_tool} with {alternative.name}",
                    data={
                        "failed_tool": failed_tool,
                        "alternative": alternative.to_dict(),
                    },
                )
            else:
                return self.fail(f"No working alternatives found for {failed_tool}")

        else:
            return self.fail(f"Unknown task type: {task_type}")

    def _detect_platform(self) -> str:
        """Detect current platform."""
        import platform as plt
        system = plt.system().lower()
        if system == "darwin":
            return "macos"
        return system

    def get_preferred_tool(self, category: ToolCategory) -> DiscoveredTool | None:
        """Get Beyond Ralph's preferred tool for a category.

        Used when user hasn't specified a tool. Beyond Ralph has opinions.
        """
        return self.PREFERRED_TOOLS.get(category)

    def get_alternatives(self, category: ToolCategory) -> list[DiscoveredTool]:
        """Get alternative tools for a category."""
        return self.ALTERNATIVES.get(category, [])

    async def find_and_install_tool(
        self,
        category: ToolCategory,
        need: str,
        platform: str,
    ) -> DiscoveredTool | None:
        """Find and install a tool for a specific need.

        First tries preferred tool, then alternatives if needed.

        Args:
            category: Tool category needed
            need: Description of what the tool needs to do
            platform: Target platform

        Returns:
            Installed tool, or None if all options failed
        """
        # Check if we have a cached decision
        knowledge = await self.read_knowledge(
            topic=f"tool {category.value}",
            category="research",
        )
        if knowledge:
            # Use previous decision if available
            for entry in knowledge:
                if "installed_tool" in entry.get("content", ""):
                    # TODO: Parse and return cached tool
                    pass

        # Try preferred tool first
        preferred = self.get_preferred_tool(category)
        if preferred and platform in preferred.platform_support:
            if preferred.name not in self.failed_tools:
                success = await self.install_tool(preferred)
                if success:
                    await self._document_installation(preferred)
                    return preferred
                else:
                    self.failed_tools.append(preferred.name)

        # Try alternatives
        for alt in self.get_alternatives(category):
            if alt.name in self.failed_tools:
                continue
            if platform not in alt.platform_support:
                continue

            success = await self.install_tool(alt)
            if success:
                await self._document_installation(alt)
                return alt
            else:
                self.failed_tools.append(alt.name)

        # Try web search for more options
        discovered = await self.search_for_tool(need, platform, category)
        for tool in discovered:
            if tool.name in self.failed_tools:
                continue

            success = await self.install_tool(tool)
            if success:
                await self._document_installation(tool)
                return tool
            else:
                self.failed_tools.append(tool.name)

        return None

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
        cache_key = f"{category.value}:{platform}:{need}"
        if cache_key in self.discovered_cache:
            return self.discovered_cache[cache_key]

        # For now, return empty list - web search would be implemented
        # with actual WebSearch/WebFetch tool calls in production
        discovered: list[DiscoveredTool] = []
        self.discovered_cache[cache_key] = discovered
        return discovered

    async def install_tool(self, tool: DiscoveredTool) -> bool:
        """Install a tool WITHOUT user approval.

        Post-interview, we operate autonomously in the contained environment.
        Installation happens immediately.

        Args:
            tool: The tool to install

        Returns:
            True if installation succeeded, False otherwise
        """
        if not tool.install_command or tool.install_command.startswith("#"):
            # Built-in or no install needed
            self.installed_tools.append(tool.name)
            return True

        try:
            # Split command for multi-step installs (e.g., "pip install x && x init")
            commands = tool.install_command.split(" && ")

            for cmd in commands:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=self.project_root,
                )

                if result.returncode != 0:
                    return False

            self.installed_tools.append(tool.name)
            return True

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

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

        # Try built-in alternatives first
        for alt in self.get_alternatives(category):
            if alt.name in self.failed_tools:
                continue
            if platform not in alt.platform_support:
                continue

            success = await self.install_tool(alt)
            if success:
                await self._document_failure_resolution(
                    failed_tool=failed_tool,
                    error=error_message,
                    solution=alt,
                    platform=platform,
                )
                return alt
            else:
                self.failed_tools.append(alt.name)

        # Search for alternatives
        alternatives = await self.search_for_tool(
            need=f"alternative to {failed_tool} that works on {platform}",
            platform=platform,
            category=category,
        )

        for alt in sorted(alternatives, key=lambda t: t.recommended, reverse=True):
            if alt.name in self.failed_tools:
                continue

            success = await self.install_tool(alt)
            if success:
                await self._document_failure_resolution(
                    failed_tool=failed_tool,
                    error=error_message,
                    solution=alt,
                    platform=platform,
                )
                return alt
            else:
                self.failed_tools.append(alt.name)

        return None

    async def _document_installation(self, tool: DiscoveredTool) -> None:
        """Document a tool installation in the knowledge base."""
        content = f"""# Installed Tool: {tool.name}

## Category
{tool.category.value}

## Package
{tool.package_manager.value}: {tool.package_name}

## Install Command
```bash
{tool.install_command}
```

## Rationale
{tool.rationale}

## Documentation
{tool.documentation_url or "Not available"}
"""
        try:
            await self.write_knowledge(
                title=f"tool-installed-{tool.name}",
                content=content,
                category="research",
                tags=["tool", tool.category.value, tool.name],
            )
        except Exception:
            # Don't fail installation if knowledge write fails
            pass

    async def _document_failure_resolution(
        self,
        failed_tool: str,
        error: str,
        solution: DiscoveredTool,
        platform: str,
    ) -> None:
        """Document a tool failure and its resolution for future reference."""
        content = f"""# Tool Failure Resolution

## Failed Tool
{failed_tool}

## Platform
{platform}

## Error
```
{error}
```

## Solution
Replaced with: **{solution.name}**

{solution.description}

## Install Command
```bash
{solution.install_command}
```

## Lesson Learned
When {failed_tool} fails on {platform}, use {solution.name} instead.
"""
        try:
            await self.write_knowledge(
                title=f"tool-failure-{failed_tool}-solution",
                content=content,
                category="research",
                tags=["tool-failure", failed_tool, solution.name, platform],
            )
        except Exception:
            pass

    async def verify_tool_installed(self, tool_name: str) -> bool:
        """Verify a tool is properly installed and working."""
        verification_commands = {
            "pytest": ["pytest", "--version"],
            "playwright": ["playwright", "--version"],
            "ruff": ["ruff", "--version"],
            "mypy": ["mypy", "--version"],
            "semgrep": ["semgrep", "--version"],
            "bandit": ["bandit", "--version"],
            "safety": ["safety", "--version"],
        }

        cmd = verification_commands.get(tool_name)
        if not cmd:
            # Unknown tool, assume installed if in list
            return tool_name in self.installed_tools

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.aclose()
