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

import json
import re
import shutil
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
class CodeExample:
    """A code example extracted from documentation or tutorials."""

    language: str
    code: str
    description: str
    source_url: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "language": self.language,
            "code": self.code,
            "description": self.description,
            "source_url": self.source_url,
        }


@dataclass
class ResearchResult:
    """Result of implementation research."""

    topic: str
    summary: str
    implementation_steps: list[str]
    code_examples: list[CodeExample]
    sources: list[str]  # URLs
    confidence: float  # 0.0-1.0
    stored_path: str  # knowledge base path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "topic": self.topic,
            "summary": self.summary,
            "implementation_steps": self.implementation_steps,
            "code_examples": [ex.to_dict() for ex in self.code_examples],
            "sources": self.sources,
            "confidence": self.confidence,
            "stored_path": self.stored_path,
        }


@dataclass
class SkillRecommendation:
    """A recommended Claude Code skill or MCP server.

    Used during early project phases to discover and recommend
    skills/MCPs that could enhance the development workflow.
    """

    name: str
    description: str
    source: str  # "github", "npm", "registry"
    install_command: str
    stars: int
    last_updated: str  # ISO date string
    requires_restart: bool
    config_location: str  # where to add config (e.g., ".claude/settings.json")
    quality_score: float  # 0.0-1.0
    reason: str  # why recommended

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "install_command": self.install_command,
            "stars": self.stars,
            "last_updated": self.last_updated,
            "requires_restart": self.requires_restart,
            "config_location": self.config_location,
            "quality_score": self.quality_score,
            "reason": self.reason,
        }


@dataclass
class SkillDiscoveryResult:
    """Result of skill/MCP discovery for a project.

    Contains recommendations and metadata about the discovery phase.
    """

    requirements: list[str]
    recommendations: list[SkillRecommendation]
    discovery_phase: str  # "early" (Phase 1-2) or "late" (Phase 7+)
    restart_warning: bool  # True if discovering late requires restart

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "requirements": self.requirements,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "discovery_phase": self.discovery_phase,
            "restart_warning": self.restart_warning,
        }


@dataclass
class SkillInstallResult:
    """Result of installing a Claude Code skill or MCP server.

    Tracks success/failure, installation method used, and whether
    configuration was updated.
    """

    skill_name: str
    success: bool
    install_method: str  # "npm", "git", "copy"
    config_updated: bool
    config_path: str
    error_message: str | None
    requires_restart: bool
    verification_status: str  # "pending", "verified", "failed"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "skill_name": self.skill_name,
            "success": self.success,
            "install_method": self.install_method,
            "config_updated": self.config_updated,
            "config_path": self.config_path,
            "error_message": self.error_message,
            "requires_restart": self.requires_restart,
            "verification_status": self.verification_status,
        }


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
        self.installed_skills: list[str] = []  # Track installed skills/MCPs

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

            # At this point we know failed_tool is not None due to the check above
            assert failed_tool is not None

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

    def _find_tool_by_name(
        self, tool_name: str, category: ToolCategory
    ) -> DiscoveredTool | None:
        """Look up a tool by name from preferred tools and alternatives."""
        preferred = self.PREFERRED_TOOLS.get(category)
        if preferred and preferred.name == tool_name:
            return preferred
        for alt in self.ALTERNATIVES.get(category, []):
            if alt.name == tool_name:
                return alt
        return None

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
                content = entry.get("content", "")
                if "installed_tool" in content:
                    # Extract cached tool name from knowledge entry
                    for line in content.split("\n"):
                        if line.strip().startswith("installed_tool:"):
                            tool_name = line.split(":", 1)[1].strip()
                            cached = self._find_tool_by_name(tool_name, category)
                            if cached:
                                return cached

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

    # =========================================================================
    # Implementation Research Methods
    # =========================================================================

    async def research_implementation(self, topic: str) -> ResearchResult:
        """Research how to implement something by searching the web.

        Searches for tutorials, documentation, and examples, then synthesizes
        findings into an actionable implementation plan.

        Args:
            topic: The implementation topic to research (e.g., "OAuth2 authentication",
                   "WebSocket server", "PDF generation")

        Returns:
            ResearchResult with summary, steps, code examples, and sources
        """
        # Build search query for implementation guidance
        search_query = f"{topic} implementation guide tutorial python"

        # Search the web for relevant sources
        search_results = await self._search_web(search_query)

        # Evaluate and rank sources (prefer official docs over blogs)
        ranked_sources = self._evaluate_sources(search_results)

        # Fetch and analyze top sources
        all_examples: list[CodeExample] = []
        source_contents: list[dict[str, Any]] = []

        for source in ranked_sources[:5]:  # Limit to top 5 sources
            url = source.get("url", "")
            if not url:
                continue

            try:
                content = await self._fetch_documentation(url)
                if content:
                    source_contents.append(
                        {
                            "url": url,
                            "content": content,
                            "title": source.get("title", ""),
                            "quality": source.get("quality", 0.5),
                        }
                    )

                    # Extract code examples
                    examples = self._extract_code_examples(content, url)
                    all_examples.extend(examples)
            except Exception:
                # Skip sources that fail to fetch
                continue

        # Synthesize implementation plan
        summary, steps = self._synthesize_implementation_plan(source_contents, topic)

        # Calculate confidence based on source quality and example coverage
        confidence = self._calculate_confidence(source_contents, all_examples)

        # Collect source URLs
        source_urls = [s.get("url", "") for s in source_contents if s.get("url")]

        # Create result
        result = ResearchResult(
            topic=topic,
            summary=summary,
            implementation_steps=steps,
            code_examples=all_examples,
            sources=source_urls,
            confidence=confidence,
            stored_path="",  # Will be set after storage
        )

        # Store in knowledge base
        stored_path = await self._store_research(result)
        result.stored_path = stored_path

        return result

    async def _search_web(self, query: str) -> list[dict[str, Any]]:
        """Search the web for relevant documentation and tutorials.

        In production, this would use Claude's WebSearch tool.
        For now, returns empty list - actual web search happens via Claude Code tools.

        Args:
            query: Search query string

        Returns:
            List of search result dicts with url, title, snippet, quality
        """
        # This is a placeholder for the actual web search integration
        # In practice, the ResearchAgent would be invoked via Claude Code
        # which has access to WebSearch and WebFetch tools
        #
        # The agent prompt would include instructions to use WebSearch:
        # "Use WebSearch to find: {query}"
        #
        # For unit testing, this can be mocked to return test data
        _ = query  # Mark as intentionally unused (placeholder method)
        return []

    async def _fetch_documentation(self, url: str) -> str:
        """Fetch and extract content from a documentation URL.

        In production, this would use Claude's WebFetch tool.
        For now, attempts HTTP fetch as fallback.

        Args:
            url: URL to fetch content from

        Returns:
            Extracted text content from the page
        """
        # This is a placeholder for the actual web fetch integration
        # In practice, the ResearchAgent would be invoked via Claude Code
        # which has access to WebFetch tool
        #
        # For direct HTTP fetch (fallback):
        try:
            response = await self.client.get(url, follow_redirects=True)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass

        return ""

    def _evaluate_sources(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Evaluate and rank search results by quality.

        Prefers:
        1. Official documentation (docs.*, readthedocs.io, etc.)
        2. GitHub repos with high stars
        3. Stack Overflow accepted answers
        4. Well-known tutorial sites
        5. Blog posts (lowest priority)

        Args:
            results: Raw search results

        Returns:
            Results sorted by quality score (highest first)
        """
        # Quality indicators for different source types
        official_domains = [
            "docs.python.org",
            "readthedocs.io",
            "readthedocs.org",
            "python.org",
            "mozilla.org",
            "developer.mozilla.org",
            "fastapi.tiangolo.com",
            "flask.palletsprojects.com",
            "django-project.com",
            "sqlalchemy.org",
            "numpy.org",
            "pandas.pydata.org",
            "pytorch.org",
            "tensorflow.org",
        ]

        high_quality_domains = [
            "github.com",
            "stackoverflow.com",
            "realpython.com",
            "geeksforgeeks.org",
            "programiz.com",
            "w3schools.com",
        ]

        ranked: list[dict[str, Any]] = []

        for result in results:
            url = result.get("url", "")
            title = result.get("title", "")

            # Calculate quality score
            quality = 0.5  # Base score

            # Boost for official documentation
            for domain in official_domains:
                if domain in url:
                    quality = 1.0
                    break

            # Boost for high-quality sites
            if quality < 1.0:
                for domain in high_quality_domains:
                    if domain in url:
                        quality = 0.8
                        break

            # Boost for titles containing "documentation" or "official"
            title_lower = title.lower()
            if "documentation" in title_lower or "official" in title_lower:
                quality = min(quality + 0.1, 1.0)

            # Boost for tutorials and guides
            if "tutorial" in title_lower or "guide" in title_lower:
                quality = min(quality + 0.05, 1.0)

            # Penalize medium/substack/personal blogs slightly
            if "medium.com" in url or "substack.com" in url:
                quality = max(quality - 0.1, 0.3)

            ranked.append(
                {
                    **result,
                    "quality": quality,
                }
            )

        # Sort by quality descending
        ranked.sort(key=lambda x: x.get("quality", 0), reverse=True)

        return ranked

    def _extract_code_examples(
        self,
        content: str,
        source_url: str,
    ) -> list[CodeExample]:
        """Extract code examples from documentation content.

        Looks for code blocks in markdown or HTML content and extracts them
        with language hints and surrounding context for descriptions.

        Args:
            content: Raw content (HTML or Markdown)
            source_url: URL the content came from (for attribution)

        Returns:
            List of CodeExample objects
        """
        examples: list[CodeExample] = []

        # Pattern for markdown code blocks: ```language\ncode\n```
        markdown_pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(markdown_pattern, content, re.DOTALL)

        for match in matches:
            language = match[0] if match[0] else "text"
            code = match[1].strip()

            # Skip very short snippets (likely not useful)
            if len(code) < 20:
                continue

            # Skip shell/command snippets unless they're installation commands
            is_shell = language in ["bash", "sh", "shell", "console"]
            is_install_cmd = any(
                cmd in code.lower()
                for cmd in ["pip install", "npm install", "uv add", "apt install"]
            )
            if is_shell and not is_install_cmd:
                continue

            # Try to extract description from surrounding context
            # Look for the code block in content and get preceding text
            code_start = content.find(f"```{language}\n{code[:50]}")
            if code_start == -1:
                code_start = content.find(f"```\n{code[:50]}")

            description = ""
            if code_start > 0:
                # Get up to 200 chars before the code block
                preceding = content[max(0, code_start - 200) : code_start]
                # Find the last sentence or heading
                sentences = re.split(r"[.!?]\s+|\n#+\s*", preceding)
                if sentences:
                    description = sentences[-1].strip()
                    # Clean up description
                    description = re.sub(r"\s+", " ", description)
                    if len(description) > 150:
                        description = description[:147] + "..."

            examples.append(
                CodeExample(
                    language=language,
                    code=code,
                    description=description or f"Code example from {source_url}",
                    source_url=source_url,
                )
            )

        # Also try to find HTML <pre><code> blocks
        html_pattern = r'<pre[^>]*><code[^>]*class="[^"]*(\w+)[^"]*"[^>]*>(.*?)</code></pre>'
        html_matches = re.findall(html_pattern, content, re.DOTALL | re.IGNORECASE)

        for match in html_matches:
            language = match[0] if match[0] else "text"
            code = match[1].strip()

            # Basic HTML entity decoding
            code = (
                code.replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
                .replace("&quot;", '"')
            )

            if len(code) < 20:
                continue

            examples.append(
                CodeExample(
                    language=language,
                    code=code,
                    description=f"Code example from {source_url}",
                    source_url=source_url,
                )
            )

        return examples

    def _synthesize_implementation_plan(
        self,
        sources: list[dict[str, Any]],
        topic: str,
    ) -> tuple[str, list[str]]:
        """Synthesize findings into a coherent implementation plan.

        Combines information from multiple sources into a summary and
        step-by-step implementation guide.

        Args:
            sources: List of source dicts with content and metadata
            topic: The original research topic

        Returns:
            Tuple of (summary, list of implementation steps)
        """
        if not sources:
            return (
                f"No sources found for '{topic}'. Manual research recommended.",
                [
                    "Search official documentation for the relevant library",
                    "Look for example implementations on GitHub",
                    "Check Stack Overflow for common patterns",
                    "Consider alternative approaches if documentation is sparse",
                ],
            )

        # Build summary from top sources
        summary_parts = [f"Research findings for: {topic}\n"]

        for source in sources[:3]:  # Top 3 sources
            title = source.get("title", "Unknown")
            url = source.get("url", "")
            quality = source.get("quality", 0.5)
            quality_label = (
                "Official docs"
                if quality >= 0.9
                else "High quality"
                if quality >= 0.7
                else "Reference"
            )
            summary_parts.append(f"- [{quality_label}] {title}: {url}")

        summary = "\n".join(summary_parts)

        # Generate implementation steps based on common patterns
        # In production, this would be done by Claude analyzing the content
        steps = [
            f"1. Review the documentation and examples for {topic}",
            "2. Install required dependencies (check pyproject.toml)",
            "3. Create the basic structure following official patterns",
            "4. Implement core functionality with proper error handling",
            "5. Add type hints and docstrings",
            "6. Write unit tests for the implementation",
            "7. Test integration with existing codebase",
            "8. Document usage and any configuration needed",
        ]

        return summary, steps

    def _calculate_confidence(
        self,
        sources: list[dict[str, Any]],
        examples: list[CodeExample],
    ) -> float:
        """Calculate confidence score for the research findings.

        Confidence is based on:
        - Number and quality of sources found
        - Presence of code examples
        - Consistency across sources

        Args:
            sources: List of source dicts with quality scores
            examples: List of extracted code examples

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not sources:
            return 0.0

        # Base confidence from number of sources (up to 0.4)
        source_count_score = min(len(sources) / 5, 1.0) * 0.4

        # Quality score from average source quality (up to 0.3)
        avg_quality = sum(s.get("quality", 0.5) for s in sources) / len(sources)
        quality_score = avg_quality * 0.3

        # Example score (up to 0.3)
        example_count = len(examples)
        if example_count == 0:
            example_score = 0.0
        elif example_count < 3:
            example_score = 0.15
        elif example_count < 6:
            example_score = 0.25
        else:
            example_score = 0.3

        total: float = source_count_score + quality_score + example_score

        # Ensure we're in valid range
        result: float = max(0.0, min(1.0, total))
        return result

    async def _store_research(self, result: ResearchResult) -> str:
        """Store research results in the knowledge base.

        Creates a markdown file with the research findings including
        summary, implementation steps, code examples, and source URLs.

        Args:
            result: The ResearchResult to store

        Returns:
            Path to the stored knowledge entry (relative to knowledge base)
        """
        # Format code examples for markdown
        examples_md = ""
        for i, example in enumerate(result.code_examples[:5], 1):  # Limit to 5 examples
            examples_md += f"\n### Example {i}: {example.description}\n"
            examples_md += f"Source: {example.source_url}\n"
            examples_md += f"```{example.language}\n{example.code}\n```\n"

        # Build implementation steps section
        steps_text = "\n".join(step for step in result.implementation_steps)

        # Build sources section
        sources_text = (
            "\n".join(f"- {url}" for url in result.sources)
            if result.sources
            else "No sources found."
        )

        # Build content
        content = f"""## Summary
{result.summary}

## Confidence Score
{result.confidence:.2f} / 1.00

## Implementation Steps
{steps_text}

## Code Examples
{examples_md if examples_md else "No code examples extracted."}

## Sources
{sources_text}

## Notes
- Research conducted by Beyond Ralph ResearchAgent
- Always verify examples against current library versions
- Check for security implications of suggested patterns
"""

        # Sanitize topic for filename
        safe_topic = re.sub(r"[^a-z0-9]+", "-", result.topic.lower())
        safe_topic = safe_topic.strip("-")[:40]
        title = f"research-{safe_topic}"

        try:
            await self.write_knowledge(
                title=title,
                content=content,
                category="research",
                tags=["implementation", "research", safe_topic],
            )
            return f"beyondralph_knowledge/{title}.md"
        except Exception:
            return ""

    # =========================================================================
    # Skill/MCP Discovery Methods
    # =========================================================================

    async def discover_skills(
        self,
        requirements: list[str],
        phase: int = 1,
    ) -> SkillDiscoveryResult:
        """Discover relevant Claude Code skills/MCPs for project requirements.

        Searches GitHub and npm for MCP servers and skills that could
        enhance the development workflow for the given requirements.

        Args:
            requirements: List of project requirements/features to find skills for
            phase: Current project phase (1-8). Phases 1-2 are "early" discovery.

        Returns:
            SkillDiscoveryResult with recommendations and phase information
        """
        discovery_phase = "early" if phase <= 2 else "late"
        all_recommendations: list[SkillRecommendation] = []

        for req in requirements:
            # Search GitHub for MCP servers
            github_results = await self._search_github_skills(req)
            all_recommendations.extend(github_results)

            # Search npm for MCP packages
            npm_results = await self._search_npm_skills(req)
            all_recommendations.extend(npm_results)

        # Deduplicate by name
        seen_names: set[str] = set()
        unique_recommendations: list[SkillRecommendation] = []
        for rec in all_recommendations:
            if rec.name not in seen_names:
                seen_names.add(rec.name)
                unique_recommendations.append(rec)

        # Rank by quality and take top recommendations
        ranked = self._rank_skills(unique_recommendations)

        # Limit to top 3 per requirement, max 10 total
        max_recommendations = min(len(requirements) * 3, 10)
        top_recommendations = ranked[:max_recommendations]

        return SkillDiscoveryResult(
            requirements=requirements,
            recommendations=top_recommendations,
            discovery_phase=discovery_phase,
            restart_warning=discovery_phase == "late",
        )

    async def _search_github_skills(self, query: str) -> list[SkillRecommendation]:
        """Search GitHub for MCP servers and Claude skills.

        Searches for repositories with topics like "claude-mcp", "claude-skill",
        "mcp-server", etc.

        Args:
            query: The search query based on project requirement

        Returns:
            List of SkillRecommendation from GitHub search
        """
        recommendations: list[SkillRecommendation] = []

        # Build search query targeting MCP/skill repositories
        search_terms = [
            f"{query} mcp-server",
            f"{query} claude-mcp",
            f"{query} claude-skill",
            f"{query} modelcontextprotocol",
        ]

        for search_term in search_terms:
            try:
                # GitHub search API URL
                url = "https://api.github.com/search/repositories"
                params: dict[str, str | int] = {
                    "q": f"{search_term} in:name,description,topics",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 5,
                }

                response = await self.client.get(
                    url,
                    params=params,
                    headers={"Accept": "application/vnd.github.v3+json"},
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                items = data.get("items", [])

                for item in items:
                    # Skip if already processed
                    name = item.get("full_name", "")
                    if any(r.name == name for r in recommendations):
                        continue

                    # Extract metadata
                    stars = item.get("stargazers_count", 0)
                    updated_at = item.get("updated_at", "")
                    description = item.get("description", "") or "No description"

                    # Calculate quality score
                    quality = self._evaluate_skill_quality(
                        {
                            "stars": stars,
                            "updated_at": updated_at,
                            "has_readme": True,  # Assume true for GitHub repos
                            "source": "github",
                        }
                    )

                    # Build install command
                    clone_url = item.get("clone_url", "")
                    install_cmd = f"git clone {clone_url}"

                    # Check if it's a Python package (has setup.py or pyproject.toml)
                    language = item.get("language", "").lower()
                    repo_name = item.get("name", "")
                    if language == "python":
                        install_cmd = f"git clone {clone_url} && cd {repo_name} && pip install -e ."
                    elif language in ["javascript", "typescript"]:
                        install_cmd = f"git clone {clone_url} && cd {repo_name} && npm install"

                    recommendations.append(
                        SkillRecommendation(
                            name=name,
                            description=description[:200],  # Truncate long descriptions
                            source="github",
                            install_command=install_cmd,
                            stars=stars,
                            last_updated=updated_at[:10] if updated_at else "",  # Date only
                            requires_restart=True,  # MCP servers require restart
                            config_location=".claude/settings.json",
                            quality_score=quality,
                            reason=f"Matches '{query}' with {stars} stars",
                        )
                    )

            except Exception:
                # Continue on errors - don't fail discovery
                continue

        return recommendations

    async def _search_npm_skills(self, query: str) -> list[SkillRecommendation]:
        """Search npm for MCP packages.

        Searches for packages matching "@modelcontextprotocol/*", "mcp-*",
        etc.

        Args:
            query: The search query based on project requirement

        Returns:
            List of SkillRecommendation from npm search
        """
        recommendations: list[SkillRecommendation] = []

        # Build search queries for npm
        search_terms = [
            f"@modelcontextprotocol {query}",
            f"mcp-server {query}",
            f"claude-mcp {query}",
        ]

        for search_term in search_terms:
            try:
                # npm registry search API
                url = "https://registry.npmjs.org/-/v1/search"
                params: dict[str, str | int] = {
                    "text": search_term,
                    "size": 5,
                }

                response = await self.client.get(url, params=params)

                if response.status_code != 200:
                    continue

                data = response.json()
                packages = data.get("objects", [])

                for pkg_data in packages:
                    package = pkg_data.get("package", {})

                    # Extract metadata
                    name = package.get("name", "")
                    if any(r.name == name for r in recommendations):
                        continue

                    description = package.get("description", "") or "No description"
                    version = package.get("version", "latest")

                    # npm doesn't have stars directly, use score metrics
                    score = pkg_data.get("score", {})
                    detail = score.get("detail", {})
                    popularity = detail.get("popularity", 0)

                    # Get last modified date
                    date = package.get("date", "")

                    # Estimate stars from popularity (rough approximation)
                    estimated_stars = int(popularity * 1000)

                    # Calculate quality score
                    quality = self._evaluate_skill_quality(
                        {
                            "stars": estimated_stars,
                            "updated_at": date,
                            "has_readme": True,  # Assume true
                            "source": "npm",
                            "npm_score": score.get("final", 0),
                        }
                    )

                    # Build install command
                    install_cmd = f"npm install {name}@{version}"

                    # Determine if this is an official MCP package
                    is_official = name.startswith("@modelcontextprotocol/")

                    recommendations.append(
                        SkillRecommendation(
                            name=name,
                            description=description[:200],
                            source="npm",
                            install_command=install_cmd,
                            stars=estimated_stars,
                            last_updated=date[:10] if date else "",
                            requires_restart=True,
                            config_location=".claude/settings.json",
                            quality_score=quality,
                            reason=(
                                f"Official MCP package for '{query}'"
                                if is_official
                                else f"MCP package for '{query}'"
                            ),
                        )
                    )

            except Exception:
                # Continue on errors
                continue

        return recommendations

    def _evaluate_skill_quality(self, metadata: dict[str, Any]) -> float:
        """Evaluate the quality of a skill/MCP based on various factors.

        Quality scoring factors:
        - Stars (more = better, normalized to 0-0.3)
        - Recent updates (last 6 months = high score, 0-0.3)
        - Has documentation (0-0.2)
        - Source reputation (official packages get bonus, 0-0.2)

        Args:
            metadata: Dict with stars, updated_at, has_readme, source, etc.

        Returns:
            Quality score between 0.0 and 1.0
        """
        quality = 0.0

        # Stars component (0-0.3)
        stars = metadata.get("stars", 0)
        if stars >= 1000:
            quality += 0.3
        elif stars >= 500:
            quality += 0.25
        elif stars >= 100:
            quality += 0.2
        elif stars >= 50:
            quality += 0.15
        elif stars >= 10:
            quality += 0.1
        elif stars > 0:
            quality += 0.05

        # Recency component (0-0.3)
        updated_at = metadata.get("updated_at", "")
        if updated_at:
            try:
                from datetime import datetime, timedelta

                # Parse ISO date
                update_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                now = datetime.now(update_date.tzinfo)
                age = now - update_date

                if age < timedelta(days=30):
                    quality += 0.3  # Updated in last month
                elif age < timedelta(days=90):
                    quality += 0.25  # Updated in last 3 months
                elif age < timedelta(days=180):
                    quality += 0.2  # Updated in last 6 months
                elif age < timedelta(days=365):
                    quality += 0.1  # Updated in last year
                # Older than a year = 0 recency score
            except (ValueError, TypeError):
                # Can't parse date, give minimal score
                quality += 0.05

        # Documentation component (0-0.2)
        if metadata.get("has_readme", False):
            quality += 0.15
        if metadata.get("has_docs", False):
            quality += 0.05

        # Source reputation component (0-0.2)
        source = metadata.get("source", "")
        if source == "npm":
            # Official MCP packages get bonus
            npm_score = metadata.get("npm_score", 0)
            quality += min(npm_score * 0.2, 0.2)
        elif source == "github":
            # GitHub repos with good metrics
            quality += 0.1

        # Ensure bounds
        return max(0.0, min(1.0, quality))

    def _rank_skills(
        self,
        skills: list[SkillRecommendation],
    ) -> list[SkillRecommendation]:
        """Rank skills by quality score and other factors.

        Args:
            skills: List of SkillRecommendation to rank

        Returns:
            Skills sorted by quality (highest first)
        """
        # Sort by quality score descending, then by stars as tiebreaker
        return sorted(
            skills,
            key=lambda s: (s.quality_score, s.stars),
            reverse=True,
        )

    async def _store_skill_discovery(
        self,
        result: SkillDiscoveryResult,
    ) -> str:
        """Store skill discovery results in the knowledge base.

        Args:
            result: The SkillDiscoveryResult to store

        Returns:
            Path to the stored knowledge entry
        """
        # Build recommendations section
        recommendations_md = ""
        for i, rec in enumerate(result.recommendations, 1):
            recommendations_md += f"""
### {i}. {rec.name}
- **Description:** {rec.description}
- **Source:** {rec.source}
- **Stars:** {rec.stars}
- **Last Updated:** {rec.last_updated}
- **Quality Score:** {rec.quality_score:.2f}
- **Install:** `{rec.install_command}`
- **Config Location:** {rec.config_location}
- **Requires Restart:** {"Yes" if rec.requires_restart else "No"}
- **Reason:** {rec.reason}
"""

        # Build restart warning text
        if result.restart_warning:
            restart_text = "Yes - installing skills late may require restarting Claude Code"
        else:
            restart_text = "No"

        # Build content
        content = f"""## Skill Discovery Results

### Requirements Analyzed
{chr(10).join(f"- {req}" for req in result.requirements)}

### Discovery Phase
- **Phase:** {result.discovery_phase}
- **Restart Warning:** {restart_text}

## Recommendations
{recommendations_md if recommendations_md else "No skills found matching the requirements."}

## Notes
- Skills discovered by Beyond Ralph ResearchAgent
- Always review skill documentation before installing
- MCP servers require Claude Code restart after installation
"""

        # Generate filename from first requirement
        if result.requirements:
            safe_req = re.sub(r"[^a-z0-9]+", "-", result.requirements[0].lower())
            safe_req = safe_req.strip("-")[:30]
        else:
            safe_req = "general"
        title = f"skill-discovery-{safe_req}"

        try:
            await self.write_knowledge(
                title=title,
                content=content,
                category="research",
                tags=["skill-discovery", "mcp", "claude-code"],
            )
            return f"beyondralph_knowledge/{title}.md"
        except Exception:
            return ""

    # =========================================================================
    # Skill/MCP Installation Methods
    # =========================================================================

    async def install_skill(
        self,
        recommendation: SkillRecommendation,
    ) -> SkillInstallResult:
        """Install a recommended skill/MCP.

        Routes to the appropriate installation method based on source type.
        Updates Claude configuration as needed.

        Args:
            recommendation: The skill recommendation to install

        Returns:
            SkillInstallResult with success status and details
        """
        try:
            if recommendation.source == "npm":
                return await self._install_npm_skill(recommendation)
            elif recommendation.source == "github":
                return await self._install_github_skill(recommendation)
            else:
                return await self._install_skill_file(recommendation)
        except Exception as e:
            return SkillInstallResult(
                skill_name=recommendation.name,
                success=False,
                install_method="unknown",
                config_updated=False,
                config_path="",
                error_message=str(e),
                requires_restart=recommendation.requires_restart,
                verification_status="failed",
            )

    async def _install_npm_skill(
        self,
        rec: SkillRecommendation,
    ) -> SkillInstallResult:
        """Install MCP via npm.

        1. Runs npm install (global or local depending on package)
        2. Updates ~/.claude.json or project settings with MCP config
        3. Verifies installation

        Args:
            rec: The skill recommendation with npm install command

        Returns:
            SkillInstallResult with installation status
        """
        error_message: str | None = None
        config_updated = False
        config_path = ""
        verification_status = "pending"

        # Run npm install
        try:
            # Parse install command (e.g., "npm install @modelcontextprotocol/server-filesystem")
            cmd_parts = rec.install_command.split()
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                error_message = f"npm install failed: {result.stderr[:500]}"
                return SkillInstallResult(
                    skill_name=rec.name,
                    success=False,
                    install_method="npm",
                    config_updated=False,
                    config_path="",
                    error_message=error_message,
                    requires_restart=rec.requires_restart,
                    verification_status="failed",
                )
        except subprocess.TimeoutExpired:
            return SkillInstallResult(
                skill_name=rec.name,
                success=False,
                install_method="npm",
                config_updated=False,
                config_path="",
                error_message="npm install timed out after 300 seconds",
                requires_restart=rec.requires_restart,
                verification_status="failed",
            )
        except Exception as e:
            return SkillInstallResult(
                skill_name=rec.name,
                success=False,
                install_method="npm",
                config_updated=False,
                config_path="",
                error_message=f"npm install error: {e}",
                requires_restart=rec.requires_restart,
                verification_status="failed",
            )

        # Build MCP server config
        # For npm packages, command is usually "npx" with the package name
        package_name = rec.name
        mcp_config = {
            "command": "npx",
            "args": [package_name],
            "env": {},
        }

        # Update Claude configuration
        try:
            config_path = await self._update_claude_config(
                skill_name=rec.name,
                config=mcp_config,
            )
            config_updated = True
        except Exception as e:
            error_message = f"Config update failed: {e}"

        # Verify installation
        if await self._verify_skill_installed_mcp(rec.name):
            verification_status = "verified"
            self.installed_skills.append(rec.name)
        else:
            verification_status = "pending"  # May work after restart

        # Document installation
        await self._document_skill_installation(rec, "npm", config_path)

        return SkillInstallResult(
            skill_name=rec.name,
            success=True,
            install_method="npm",
            config_updated=config_updated,
            config_path=config_path,
            error_message=error_message,
            requires_restart=rec.requires_restart,
            verification_status=verification_status,
        )

    async def _install_github_skill(
        self,
        rec: SkillRecommendation,
    ) -> SkillInstallResult:
        """Install MCP from GitHub repository.

        1. Git clones the repository
        2. Runs setup commands (pip install -e . or npm install)
        3. Updates Claude configuration with MCP server config
        4. Verifies installation

        Args:
            rec: The skill recommendation with git clone command

        Returns:
            SkillInstallResult with installation status
        """
        error_message: str | None = None
        config_updated = False
        config_path = ""
        verification_status = "pending"

        # Parse the install command - typically: "git clone URL && cd DIR && pip install -e ."
        commands = rec.install_command.split(" && ")

        # Execute each command in sequence
        for cmd in commands:
            try:
                cmd_parts = cmd.split()
                result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=self.project_root,
                )

                if result.returncode != 0:
                    error_message = f"Command '{cmd}' failed: {result.stderr[:500]}"
                    return SkillInstallResult(
                        skill_name=rec.name,
                        success=False,
                        install_method="git",
                        config_updated=False,
                        config_path="",
                        error_message=error_message,
                        requires_restart=rec.requires_restart,
                        verification_status="failed",
                    )
            except subprocess.TimeoutExpired:
                return SkillInstallResult(
                    skill_name=rec.name,
                    success=False,
                    install_method="git",
                    config_updated=False,
                    config_path="",
                    error_message=f"Command '{cmd}' timed out",
                    requires_restart=rec.requires_restart,
                    verification_status="failed",
                )
            except Exception as e:
                return SkillInstallResult(
                    skill_name=rec.name,
                    success=False,
                    install_method="git",
                    config_updated=False,
                    config_path="",
                    error_message=f"Command error: {e}",
                    requires_restart=rec.requires_restart,
                    verification_status="failed",
                )

        # Extract repo name from install command for config
        repo_name = self._extract_repo_name(rec.install_command)

        # Build MCP server config based on language
        # Assume Python for now; could detect from repo
        mcp_config = {
            "command": "python3",
            "args": [str(self.project_root / repo_name / "server.py")],
            "env": {},
        }

        # Update Claude configuration
        try:
            config_path = await self._update_claude_config(
                skill_name=rec.name,
                config=mcp_config,
            )
            config_updated = True
        except Exception as e:
            error_message = f"Config update failed: {e}"

        # Verify installation
        if await self._verify_skill_installed_mcp(rec.name):
            verification_status = "verified"
            self.installed_skills.append(rec.name)
        else:
            verification_status = "pending"

        # Document installation
        await self._document_skill_installation(rec, "git", config_path)

        return SkillInstallResult(
            skill_name=rec.name,
            success=True,
            install_method="git",
            config_updated=config_updated,
            config_path=config_path,
            error_message=error_message,
            requires_restart=rec.requires_restart,
            verification_status=verification_status,
        )

    async def _install_skill_file(
        self,
        rec: SkillRecommendation,
    ) -> SkillInstallResult:
        """Install a skill file (e.g., .claude/commands/*.md).

        Skill files are copied to .claude/commands/ and don't require restart.

        Args:
            rec: The skill recommendation with skill file source

        Returns:
            SkillInstallResult with installation status
        """
        error_message: str | None = None
        config_updated = False
        verification_status = "pending"

        # Skill files go to .claude/commands/
        commands_dir = Path.home() / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)

        # Build skill filename from name
        safe_name = re.sub(r"[^a-z0-9-]", "-", rec.name.lower())
        skill_path = commands_dir / f"{safe_name}.md"

        try:
            # If install_command is a URL, download it
            if rec.install_command.startswith("http"):
                response = await self.client.get(rec.install_command)
                if response.status_code == 200:
                    skill_path.write_text(response.text)
                    config_updated = True
                else:
                    error_message = f"Failed to download skill: HTTP {response.status_code}"
            # If it's a local path, copy it
            elif Path(rec.install_command).exists():
                shutil.copy(rec.install_command, skill_path)
                config_updated = True
            else:
                # Create a basic skill file from description
                skill_content = f"""---
name: {rec.name}
description: {rec.description}
---

# {rec.name}

{rec.description}

## Usage

This skill was installed by Beyond Ralph ResearchAgent.

Reason: {rec.reason}
"""
                skill_path.write_text(skill_content)
                config_updated = True

        except Exception as e:
            return SkillInstallResult(
                skill_name=rec.name,
                success=False,
                install_method="copy",
                config_updated=False,
                config_path="",
                error_message=f"Skill file installation failed: {e}",
                requires_restart=False,  # Skill files don't need restart
                verification_status="failed",
            )

        # Verify file exists
        if skill_path.exists():
            verification_status = "verified"
            self.installed_skills.append(rec.name)
        else:
            verification_status = "failed"

        # Document installation
        await self._document_skill_installation(rec, "copy", str(skill_path))

        return SkillInstallResult(
            skill_name=rec.name,
            success=True,
            install_method="copy",
            config_updated=config_updated,
            config_path=str(skill_path),
            error_message=error_message,
            requires_restart=False,  # Skill files don't need restart
            verification_status=verification_status,
        )

    async def _update_claude_config(
        self,
        skill_name: str,
        config: dict[str, Any],
    ) -> str:
        """Update Claude settings.json with MCP config.

        Merges the new MCP server config into the existing settings file.
        Creates the file if it doesn't exist.

        Args:
            skill_name: Name of the skill/MCP to add
            config: MCP server configuration dict with command, args, env

        Returns:
            Path to the updated config file
        """
        # Prefer project-local config if exists, otherwise use global
        project_config = self.project_root / ".claude.json" if self.project_root else None
        global_config = Path.home() / ".claude.json"

        # Determine which config to update
        if project_config and project_config.exists():
            config_path = project_config
        elif global_config.exists():
            config_path = global_config
        else:
            # Create project-local config
            config_path = project_config or global_config

        # Read existing config or start fresh
        existing_config: dict[str, Any] = {}
        if config_path.exists():
            try:
                existing_config = json.loads(config_path.read_text())
            except json.JSONDecodeError:
                existing_config = {}

        # Ensure mcpServers section exists
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}

        # Sanitize skill name for config key (use simple slug)
        config_key = re.sub(r"[^a-z0-9-]", "-", skill_name.lower())
        config_key = re.sub(r"-+", "-", config_key).strip("-")

        # Add the new MCP server
        existing_config["mcpServers"][config_key] = config

        # Write back
        config_path.write_text(json.dumps(existing_config, indent=2))

        return str(config_path)

    async def _verify_skill_installed_mcp(self, skill_name: str) -> bool:
        """Verify an MCP server is properly configured.

        Checks if the skill appears in Claude configuration.
        Note: Full verification may require Claude restart.

        Args:
            skill_name: Name of the skill to verify

        Returns:
            True if skill is in config, False otherwise
        """
        # Check project config first, then global
        config_paths = []
        if self.project_root:
            config_paths.append(self.project_root / ".claude.json")
        config_paths.append(Path.home() / ".claude.json")

        config_key = re.sub(r"[^a-z0-9-]", "-", skill_name.lower())
        config_key = re.sub(r"-+", "-", config_key).strip("-")

        for config_path in config_paths:
            if config_path.exists():
                try:
                    config = json.loads(config_path.read_text())
                    mcp_servers = config.get("mcpServers", {})
                    if config_key in mcp_servers:
                        return True
                except (json.JSONDecodeError, KeyError):
                    continue

        return False

    def _extract_repo_name(self, install_command: str) -> str:
        """Extract repository name from git clone command.

        Args:
            install_command: Full install command with git clone

        Returns:
            Repository directory name
        """
        # Pattern: git clone https://github.com/owner/repo.git
        # or: git clone git@github.com:owner/repo.git
        import re

        patterns = [
            r"git clone .*/([^/]+?)(?:\.git)?(?:\s|$)",  # HTTPS
            r"git clone .*:([^/]+/[^/]+?)(?:\.git)?(?:\s|$)",  # SSH
        ]

        for pattern in patterns:
            match = re.search(pattern, install_command)
            if match:
                # Return just the repo name (last part)
                return match.group(1).split("/")[-1]

        # Fallback: use a sanitized version of the skill name
        return "mcp-server"

    async def _document_skill_installation(
        self,
        rec: SkillRecommendation,
        method: str,
        config_path: str,
    ) -> None:
        """Document a skill installation in the knowledge base.

        Args:
            rec: The installed skill recommendation
            method: Installation method used (npm, git, copy)
            config_path: Path where config was written
        """
        content = f"""# Installed Skill: {rec.name}

## Installation Details
- **Method:** {method}
- **Source:** {rec.source}
- **Config Path:** {config_path}
- **Requires Restart:** {"Yes" if rec.requires_restart else "No"}

## Skill Information
- **Description:** {rec.description}
- **Stars:** {rec.stars}
- **Last Updated:** {rec.last_updated}
- **Quality Score:** {rec.quality_score:.2f}

## Install Command
```bash
{rec.install_command}
```

## Reason for Installation
{rec.reason}

## Notes
- Installed by Beyond Ralph ResearchAgent
- Check ~/.claude.json or project .claude.json for MCP config
"""
        try:
            safe_name = re.sub(r"[^a-z0-9-]", "-", rec.name.lower())[:40]
            await self.write_knowledge(
                title=f"skill-installed-{safe_name}",
                content=content,
                category="research",
                tags=["skill-installation", "mcp", rec.source, method],
            )
        except Exception:
            # Don't fail installation if knowledge write fails
            pass

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.aclose()
