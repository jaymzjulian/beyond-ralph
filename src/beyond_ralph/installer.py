"""Beyond Ralph Installer - Complete Development Environment Setup.

This module sets up a comprehensive development environment including:
- Beyond Ralph commands and hooks
- SuperClaude skills (no API keys required)
- Useful MCP servers (no API keys required)
- Code analysis and research tools
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

if TYPE_CHECKING:
    from collections.abc import Sequence

console = Console()

# Skills that don't require API keys and are useful for development
SUPERCLAUDE_COMMANDS = [
    # Core SuperClaude commands
    "sc/analyze.md",      # Code analysis
    "sc/research.md",     # Deep research
    "sc/troubleshoot.md", # Debugging
    "sc/test.md",         # Testing
    "sc/improve.md",      # Code improvement
    "sc/implement.md",    # Implementation
    "sc/design.md",       # Architecture design
    "sc/explain.md",      # Explanations
    "sc/cleanup.md",      # Code cleanup
    "sc/git.md",          # Git operations
    "sc/build.md",        # Build operations
    "sc/document.md",     # Documentation
    "sc/estimate.md",     # Estimation
    "sc/task.md",         # Task management
    "sc/workflow.md",     # Workflow generation
    "sc/reflect.md",      # Reflection
    "sc/brainstorm.md",   # Brainstorming
    "sc/help.md",         # Help
    "sc/README.md",       # Overview
    "sc/sc.md",           # Dispatcher
]

USEFUL_COMMANDS = [
    # General development commands
    "clarify.md",         # Requirement clarification
    "bugs.md",            # Bug hunting
    "audit.md",           # Code audit
    "unit-tests.md",      # Test generation
    "refactor.md",        # Refactoring
    "library-docs.md",    # Library documentation
    "docs.md",            # Documentation generation
]

USEFUL_SKILLS = [
    # Skills (directories)
    "confidence-check",   # Pre-implementation validation
    "task-classifier",    # Complexity routing
    "context7-usage",     # Documentation lookup
    "orchestrator",       # Workflow orchestration
    "compact",            # Context management
    "deslop",             # Output cleanup
]

# =============================================================================
# MCP SERVERS - NO API KEY REQUIRED (default installation)
# =============================================================================
# These servers work out-of-the-box without any API keys or external accounts.
# Sources: https://github.com/modelcontextprotocol/servers
#          https://github.com/punkpeye/awesome-mcp-servers

MCP_SERVERS_NO_API_KEY = {
    # --- Official MCP Reference Servers ---
    "sequential-thinking": {
        "description": "Dynamic problem-solving through thought sequences",
        "category": "reasoning",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
        }
    },
    "filesystem": {
        "description": "Secure file operations with configurable access controls",
        "category": "filesystem",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/"]
        }
    },
    "memory": {
        "description": "Knowledge graph-based persistent memory system",
        "category": "memory",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"]
        }
    },
    "git": {
        "description": "Read, search, and manipulate Git repositories",
        "category": "version-control",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-git"]
        }
    },
    "fetch": {
        "description": "Web content fetching and conversion for LLM usage",
        "category": "web",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"]
        }
    },
    "time": {
        "description": "Time and timezone conversion capabilities",
        "category": "utility",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-time"]
        }
    },

    # --- Documentation & Research ---
    "context7": {
        "description": "Library documentation lookup (npm, PyPI, etc.)",
        "category": "documentation",
        "config": {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"]
        }
    },

    # --- Browser Automation ---
    "playwright": {
        "description": "Browser automation via Microsoft Playwright",
        "category": "browser",
        "note": "Auto-installs browser binaries on first use",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-playwright"]
        }
    },

    # --- Database ---
    "sqlite": {
        "description": "SQLite database operations (local, no server needed)",
        "category": "database",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-sqlite"]
        }
    },

    # --- Code Quality ---
    "mcp-inspector": {
        "description": "MCP server testing and debugging tool",
        "category": "debugging",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/inspector"]
        }
    },

    # --- Research & Search (no API key) ---
    "duckduckgo": {
        "description": "Privacy-focused web search via DuckDuckGo (no API key)",
        "category": "search",
        "config": {
            "command": "npx",
            "args": ["-y", "mcp-duckduckgo-search"]
        }
    },
    "arxiv": {
        "description": "Search and analyze academic papers from arXiv",
        "category": "research",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-arxiv"]
        }
    },
    "wikipedia": {
        "description": "Search and retrieve Wikipedia articles",
        "category": "research",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-wikipedia"]
        }
    },
}

# =============================================================================
# MCP SERVERS - FREE TIER WITH API KEY
# =============================================================================
# These servers have free tiers but require API key registration.
# Only installed when --allow-free-tier-with-key is specified.

MCP_SERVERS_FREE_TIER = {
    "brave-search": {
        "description": "Web search via Brave Search API (free tier: 2000 queries/month)",
        "category": "search",
        "api_key_env": "BRAVE_API_KEY",
        "signup_url": "https://brave.com/search/api/",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-brave-search"],
            "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"}
        }
    },
    "tavily": {
        "description": "AI-optimized search API (free tier: 1000 queries/month)",
        "category": "search",
        "api_key_env": "TAVILY_API_KEY",
        "signup_url": "https://tavily.com/",
        "config": {
            "command": "npx",
            "args": ["-y", "tavily-mcp"],
            "env": {"TAVILY_API_KEY": "${TAVILY_API_KEY}"}
        }
    },
    "github": {
        "description": "GitHub API integration (uses personal access token)",
        "category": "version-control",
        "api_key_env": "GITHUB_TOKEN",
        "signup_url": "https://github.com/settings/tokens",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-github"],
            "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
        }
    },
    "sentry": {
        "description": "Error tracking and debugging via Sentry (free tier available)",
        "category": "debugging",
        "api_key_env": "SENTRY_AUTH_TOKEN",
        "signup_url": "https://sentry.io/",
        "config": {
            "command": "npx",
            "args": ["-y", "@sentry/mcp-server"],
            "env": {"SENTRY_AUTH_TOKEN": "${SENTRY_AUTH_TOKEN}"}
        }
    },
}

# =============================================================================
# OPTIONAL MCP SERVERS (require additional setup)
# =============================================================================
# These servers may need additional system dependencies or configuration.

MCP_SERVERS_OPTIONAL = {
    "serena": {
        "description": "Symbolic code analysis for Python/TypeScript/Go/Rust",
        "category": "code-analysis",
        "install_cmd": "pip install serena-mcp",
        "note": "Requires language servers (pyright, typescript, gopls, rust-analyzer)",
    },
    "postgres": {
        "description": "PostgreSQL database operations",
        "category": "database",
        "note": "Requires PostgreSQL server running",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-postgres"],
            "env": {"DATABASE_URL": "${DATABASE_URL}"}
        }
    },
}


def get_source_paths() -> tuple[Path, Path, Path]:
    """Get source paths for commands, skills, and hooks."""
    # Check global Claude directory first
    home = Path.home()
    global_claude = home / ".claude"

    # Also check beyond-ralph package location
    import beyond_ralph
    package_root = Path(beyond_ralph.__file__).parent.parent.parent

    return (
        global_claude / "commands",
        global_claude / "skills",
        package_root / ".claude" / "hooks",
    )


def copy_commands(
    target_commands: Path,
    source_commands: Path,
    commands: Sequence[str],
    force: bool = False,
) -> int:
    """Copy command files to target directory."""
    copied = 0
    for cmd_file in commands:
        src = source_commands / cmd_file
        dst = target_commands / cmd_file

        if not src.exists():
            console.print(f"  [dim]Skipping[/dim] {cmd_file} (not found)")
            continue

        # Create subdirectory if needed
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists() and not force:
            console.print(f"  [yellow]Exists[/yellow] {cmd_file}")
        else:
            shutil.copy2(src, dst)
            console.print(f"  [green]Copied[/green] {cmd_file}")
            copied += 1

    return copied


def copy_skills(
    target_skills: Path,
    source_skills: Path,
    skills: Sequence[str],
    force: bool = False,
) -> int:
    """Copy skill directories to target."""
    copied = 0
    for skill_name in skills:
        src = source_skills / skill_name
        dst = target_skills / skill_name

        if not src.exists():
            console.print(f"  [dim]Skipping[/dim] {skill_name} (not found)")
            continue

        if dst.exists() and not force:
            console.print(f"  [yellow]Exists[/yellow] {skill_name}/")
        else:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            console.print(f"  [green]Copied[/green] {skill_name}/")
            copied += 1

    return copied


def check_npm_available() -> bool:
    """Check if npm is available."""
    try:
        subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_mcp_servers(
    target_path: Path,
    servers: dict,
    install_packages: bool = False,
) -> dict:
    """Install and configure MCP servers."""
    installed = {}

    if install_packages and not check_npm_available():
        console.print("[yellow]npm not available, skipping MCP package installation[/yellow]")
        install_packages = False

    for name, info in servers.items():
        # Install package if requested
        if install_packages and info.get("install_cmd"):
            console.print(f"  Installing {name}...")
            try:
                subprocess.run(
                    info["install_cmd"].split(),
                    capture_output=True,
                    check=True,
                    timeout=120,
                )
                console.print(f"  [green]Installed[/green] {name}")
            except Exception as e:
                console.print(f"  [yellow]Skipped[/yellow] {name}: {e}")
                continue

        # Add to configuration
        if "config" in info:
            installed[name] = info["config"]
            console.print(f"  [green]Configured[/green] {name}")

    return installed


def create_settings_json(
    target_settings: Path,
    mcp_servers: dict | None = None,
    force: bool = False,
) -> None:
    """Create or update settings.json with hooks and MCP servers."""
    settings = {
        "hooks": {
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/stop_hook.py"',
                            "timeout": 30
                        }
                    ]
                }
            ]
        }
    }

    # Add MCP servers if provided
    if mcp_servers:
        settings["mcpServers"] = mcp_servers

    if target_settings.exists() and not force:
        console.print(f"  [yellow]Exists[/yellow] settings.json")
        return

    target_settings.write_text(json.dumps(settings, indent=2))
    console.print(f"  [green]Created[/green] settings.json")


def install_to_project(
    target: str | Path,
    force: bool = False,
    include_superclaude: bool = True,
    include_mcp: bool = True,
    install_mcp_packages: bool = False,
    minimal: bool = False,
    allow_free_tier_with_key: bool = False,
) -> None:
    """Install Beyond Ralph and development tools to a target project.

    Args:
        target: Target project directory
        force: Overwrite existing files
        include_superclaude: Include SuperClaude skills and commands
        include_mcp: Include MCP server configurations
        install_mcp_packages: Actually install MCP packages via npm
        minimal: Only install Beyond Ralph basics (no extras)
        allow_free_tier_with_key: Include MCP servers that have free tiers but need API keys
    """
    target_path = Path(target).expanduser().resolve()

    if not target_path.exists():
        console.print(f"[bold red]Error:[/bold red] Target directory not found: {target_path}")
        sys.exit(1)

    console.print(Panel(
        f"[bold green]Beyond Ralph Development Environment Setup[/bold green]\n\n"
        f"Target: {target_path}\n"
        f"Mode: {'Minimal' if minimal else 'Full'}\n"
        f"SuperClaude: {'Yes' if include_superclaude and not minimal else 'No'}\n"
        f"MCP Servers: {'Yes' if include_mcp and not minimal else 'No'}\n"
        f"Free Tier (API key): {'Yes' if allow_free_tier_with_key and not minimal else 'No'}",
        title="Beyond Ralph Installer",
        border_style="green",
    ))

    # Get source paths
    source_commands, source_skills, source_hooks = get_source_paths()

    # Target paths
    target_claude = target_path / ".claude"
    target_commands = target_claude / "commands"
    target_skills = target_claude / "skills"
    target_hooks = target_claude / "hooks"
    target_settings = target_claude / "settings.json"

    # Create directories
    target_commands.mkdir(parents=True, exist_ok=True)
    target_hooks.mkdir(parents=True, exist_ok=True)

    # === Beyond Ralph Core ===
    console.print("\n[bold]Installing Beyond Ralph commands...[/bold]")
    br_commands = [
        "beyond-ralph.md",
        "beyond-ralph-resume.md",
        "beyond-ralph-status.md",
    ]

    # Copy from package location
    import beyond_ralph
    package_root = Path(beyond_ralph.__file__).parent.parent.parent
    br_source = package_root / ".claude" / "commands"

    copy_commands(target_commands, br_source, br_commands, force)

    # Copy hooks
    console.print("\n[bold]Installing hooks...[/bold]")
    hook_src = source_hooks / "stop_hook.py"
    hook_dst = target_hooks / "stop_hook.py"
    if hook_src.exists():
        if hook_dst.exists() and not force:
            console.print("  [yellow]Exists[/yellow] stop_hook.py")
        else:
            shutil.copy2(hook_src, hook_dst)
            hook_dst.chmod(0o755)
            console.print("  [green]Copied[/green] stop_hook.py")

    if not minimal:
        # === SuperClaude Commands ===
        if include_superclaude and source_commands.exists():
            console.print("\n[bold]Installing SuperClaude commands...[/bold]")

            # Create sc subdirectory
            (target_commands / "sc").mkdir(exist_ok=True)

            copy_commands(target_commands, source_commands, SUPERCLAUDE_COMMANDS, force)
            copy_commands(target_commands, source_commands, USEFUL_COMMANDS, force)

        # === Skills ===
        if include_superclaude and source_skills.exists():
            console.print("\n[bold]Installing useful skills...[/bold]")
            target_skills.mkdir(parents=True, exist_ok=True)
            copy_skills(target_skills, source_skills, USEFUL_SKILLS, force)

        # === MCP Servers ===
        mcp_config = None
        if include_mcp:
            console.print("\n[bold]Configuring MCP servers (no API key required)...[/bold]")
            mcp_config = install_mcp_servers(
                target_path,
                MCP_SERVERS_NO_API_KEY,
                install_packages=install_mcp_packages,
            )

            # Add free tier servers if requested
            if allow_free_tier_with_key:
                console.print("\n[bold]Configuring MCP servers (free tier, API key needed)...[/bold]")
                free_tier_config = install_mcp_servers(
                    target_path,
                    MCP_SERVERS_FREE_TIER,
                    install_packages=install_mcp_packages,
                )
                if free_tier_config:
                    mcp_config.update(free_tier_config)

                # Show API key setup instructions
                console.print("\n[bold yellow]API Keys Required:[/bold yellow]")
                for name, info in MCP_SERVERS_FREE_TIER.items():
                    if "api_key_env" in info:
                        console.print(f"  {name}: Set {info['api_key_env']}")
                        if "signup_url" in info:
                            console.print(f"         Sign up: {info['signup_url']}")
    else:
        mcp_config = None

    # === Settings ===
    console.print("\n[bold]Creating configuration...[/bold]")
    create_settings_json(target_settings, mcp_config, force)

    # === Summary ===
    console.print("\n" + "=" * 60)
    console.print("[bold green]Installation complete![/bold green]")
    console.print("=" * 60)

    # Show what's installed
    table = Table(title="Installed Components")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("Beyond Ralph Commands", "✓ Installed")
    table.add_row("Stop Hook", "✓ Installed")

    if not minimal:
        if include_superclaude:
            table.add_row("SuperClaude Commands", "✓ Installed")
            table.add_row("Development Skills", "✓ Installed")
        if include_mcp:
            table.add_row("MCP Servers (no API key)", "✓ Configured")
            if allow_free_tier_with_key:
                table.add_row("MCP Servers (free tier)", "✓ Configured (needs API keys)")

    console.print(table)

    console.print(f"\n[bold]To start Beyond Ralph in {target_path.name}:[/bold]")
    console.print(f"  cd {target_path}")
    console.print("  /beyond-ralph start --spec SPEC.md")

    if not minimal and include_superclaude:
        console.print("\n[bold]Available SuperClaude commands:[/bold]")
        console.print("  /sc:analyze    - Code analysis")
        console.print("  /sc:research   - Deep research")
        console.print("  /sc:test       - Testing")
        console.print("  /sc:implement  - Implementation")
        console.print("  /sc:help       - Full command list")


def main() -> None:
    """CLI entry point for installer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install Beyond Ralph development environment"
    )
    parser.add_argument(
        "target",
        help="Target project directory",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Only install Beyond Ralph basics",
    )
    parser.add_argument(
        "--no-superclaude",
        action="store_true",
        help="Skip SuperClaude commands and skills",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Skip MCP server configuration",
    )
    parser.add_argument(
        "--install-mcp-packages",
        action="store_true",
        help="Actually install MCP packages via npm",
    )
    parser.add_argument(
        "--allow-free-tier-with-key",
        action="store_true",
        help="Include MCP servers with free tiers that require API keys",
    )

    args = parser.parse_args()

    install_to_project(
        target=args.target,
        force=args.force,
        include_superclaude=not args.no_superclaude,
        include_mcp=not args.no_mcp,
        install_mcp_packages=args.install_mcp_packages,
        minimal=args.minimal,
        allow_free_tier_with_key=args.allow_free_tier_with_key,
    )


if __name__ == "__main__":
    main()
