# Changelog

All notable changes to Beyond Ralph will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-04

### 🎉 Initial Release

Beyond Ralph is a Claude Code plugin for fully autonomous multi-agent development, implementing the Spec and Interview Coder methodology.

### Added

#### Core Features
- **Orchestrator**: Multi-agent coordination with phase-based development (8 phases)
- **Session Management**: UUID-based agent spawning and tracking
- **Quota Management**: Automatic pause/resume when Claude quota limits approached
- **Knowledge Base**: Shared knowledge store in `beyondralph_knowledge/`
- **Record Keeping**: Per-module task tracking with 6-checkbox verification system

#### Agents
- **Spec Agent**: Specification ingestion and analysis
- **Interview Agent**: Interactive user interview via AskUserQuestion
- **Planning Agent**: Modular spec creation and project planning
- **Validation Agent**: Plan validation and cross-checking
- **Implementation Agent**: Code generation with TDD
- **Testing Agent**: Multi-framework test execution
- **Research Agent**: Web search, skill discovery, tool recommendations
- **Review Agent**: Multi-language linting and OWASP security scanning

#### Code Review (Multi-Language Support)
- Python: ruff, mypy, bandit
- JavaScript/TypeScript: eslint, tsc
- Go: staticcheck, go vet
- Rust: cargo clippy
- Kotlin: ktlint, detekt
- Java: checkstyle
- C/C++: clang-tidy, cppcheck

#### Installer (`beyond-ralph install`)
Sets up complete development environment with:

**Commands (27 total)**:
- Beyond Ralph: `/beyond-ralph`, `/beyond-ralph-resume`, `/beyond-ralph-status`
- SuperClaude: `/sc:analyze`, `/sc:research`, `/sc:test`, `/sc:implement`, etc.
- Utilities: `/clarify`, `/bugs`, `/audit`, `/unit-tests`, `/refactor`

**Skills (6)**:
- confidence-check, task-classifier, context7-usage
- orchestrator, compact, deslop

**MCP Servers - No API Key (13)**:
- sequential-thinking, filesystem, memory, git, fetch, time
- context7, playwright, sqlite, mcp-inspector
- duckduckgo, arxiv, wikipedia

**MCP Servers - Free Tier (4, opt-in)**:
- brave-search, tavily, github, sentry
- Use `--allow-free-tier-with-key` to include

#### Remote Access
- WSL2 environment detection
- SSH-based ADB for Windows host Android testing
- VNC session management
- Appium server integration with UiAutomator2

#### GitHub Integration
- Repository detection and cloning
- Webhook events for phase notifications
- Git operations management

#### Testing
- 429 new tests across unit, integration, and live categories
- 90%+ coverage for remote-access module
- Live tests for WSL2, Windows ADB, emulator, VNC, Appium

### Technical Details

- **Language**: Python 3.11+
- **Package Manager**: uv
- **CLI Framework**: typer + rich
- **Type Checking**: mypy (strict mode)
- **Linting**: ruff

### Installation

```bash
# Install Beyond Ralph
uv pip install -e .

# Install into a project
beyond-ralph install ~/my-project

# With free-tier MCP servers
beyond-ralph install ~/my-project --allow-free-tier-with-key
```

### Usage

```bash
cd ~/my-project
/beyond-ralph start --spec SPEC.md
```

### Contributors

- Built with Claude Opus 4.5
