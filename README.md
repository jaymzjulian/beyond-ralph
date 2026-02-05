# Beyond Ralph

Autonomous multi-agent development for Claude Code. Give it a spec, answer some questions, and watch it build your project.

## What It Does

Beyond Ralph runs **inside Claude Code** as a plugin. It reads your specification, interviews you about requirements, then autonomously implements and tests the project using multiple specialized agents.

Key behaviors:
- Spawns separate agents for coding, testing, and code review
- No agent validates its own work (three-agent trust model)
- Pauses automatically at 85% quota, resumes when reset
- Tracks progress with 6 checkboxes per task

## Installation

### Install Into a Project

```bash
# Install Beyond Ralph
uv pip install -e /path/to/beyond-ralph

# Set up a project with all tools
beyond-ralph install ~/my-project

# Or with optional MCP servers that need API keys
beyond-ralph install ~/my-project --allow-free-tier-with-key
```

The installer adds:
- Commands: `/beyond-ralph`, `/beyond-ralph-resume`, `/beyond-ralph-status`
- Stop hooks for autonomous operation
- 13 MCP servers (no API keys needed)
- Optional: 4 more MCP servers with free tiers (need API keys)

### What Gets Installed

**MCP Servers (no API key)**:
sequential-thinking, filesystem, memory, git, fetch, time, context7, playwright, sqlite, mcp-inspector, duckduckgo, arxiv, wikipedia

**MCP Servers (free tier, opt-in)**:
brave-search, tavily, github, sentry

## Usage

```bash
cd ~/my-project

# Start a new project
/beyond-ralph start --spec SPEC.md

# Check progress
/beyond-ralph-status

# Resume after pause or spec change
/beyond-ralph-resume
```

## How It Works

### 8 Phases

1. **Spec Ingestion** - Read and analyze your specification
2. **Interview** - Ask clarifying questions (only phase requiring user input)
3. **Spec Creation** - Create modular specs for each component
4. **Planning** - Build project plan with milestones
5. **Review** - Check for gaps, loop back if needed
6. **Validation** - Separate agent validates the plan
7. **Implementation** - Build with TDD, three-agent trust model
8. **Testing** - Final validation

### Three-Agent Trust Model

During implementation:
- **Coding Agent** writes the code
- **Testing Agent** (different agent) validates it works
- **Review Agent** (different agent) checks quality

No agent marks its own work complete.

### Task Tracking

Every task needs 6 checkboxes checked:
- Planned
- Implemented
- Mock tested
- Integration tested
- Live tested
- Spec compliant (verified by separate agent)

### Code Review

Multi-language linting and security scanning:

| Language | Tools |
|----------|-------|
| Python | ruff, mypy, bandit |
| JavaScript/TypeScript | eslint, tsc |
| Go | staticcheck, go vet |
| Rust | cargo clippy |
| Kotlin | ktlint, detekt |
| Java | checkstyle |
| C/C++ | clang-tidy, cppcheck |

### Resume Behavior

`/beyond-ralph-resume` validates the spec before resuming. If the spec changed, it identifies new/removed/modified requirements and updates the plan. It never blindly trusts the state file.

## Project Structure

```
your-project/
├── SPEC.md                    # Your specification
├── .beyond_ralph_state        # Orchestrator state
├── beyondralph_knowledge/     # Shared knowledge base
└── records/                   # Task tracking
    └── [module]/
        └── tasks.md           # Tasks with 6 checkboxes each
```

## Requirements

- Python 3.11+
- uv (recommended) or pip
- Claude Code CLI

## License

MIT
