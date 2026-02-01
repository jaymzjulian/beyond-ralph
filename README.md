# Beyond Ralph

> True Autonomous Coding - Multi-agent orchestration for Claude Code

## What is Beyond Ralph?

Beyond Ralph is a Claude Code plugin that enables fully autonomous multi-agent development. It implements the "Spec and Interview Coder" methodology, where:

1. **Specification Ingestion** - The system ingests your project specification
2. **Deep Interview** - Thorough questioning to eliminate ambiguity
3. **Complete Planning** - Detailed, modular project plans with milestones
4. **Autonomous Implementation** - Self-coordinating agents implement features
5. **Rigorous Validation** - Every implementation is validated by a separate agent

## Key Principles

- **No Agent Trust** - Every agent's work is validated by another agent
- **Quota Awareness** - Automatically pauses when nearing usage limits
- **Knowledge Sharing** - Agents share learnings through a knowledge base
- **Complete Records** - Every task tracked with 5 checkboxes (Planned → Live tested)
- **Self-Contained** - Ships everything it needs, no external dependencies

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/beyond-ralph.git
cd beyond-ralph

# Install with uv
uv sync

# Or install as a package
uv pip install .
```

## Quick Start

```bash
# Start a new autonomous project
beyond-ralph start --spec path/to/SPEC.md

# Check quota status
br-quota

# Resume a paused project
beyond-ralph resume
```

## Requirements

- Python 3.11+
- Claude Code CLI installed and configured
- uv package manager

## Project Structure

```
beyond-ralph/
├── src/beyond_ralph/      # Main package
│   ├── core/              # Orchestrator and session management
│   ├── agents/            # Agent definitions
│   ├── skills/            # Claude Code skills
│   ├── hooks/             # Claude Code hooks
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── docs/                  # Documentation
├── records/               # Task tracking per module
└── beyondralph_knowledge/ # Shared knowledge base
```

## Documentation

- [User Guide](docs/user/README.md)
- [Developer Guide](docs/developer/README.md)
- [API Reference](docs/developer/api.md)

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Type check
uv run mypy src

# Lint and format
uv run ruff check src tests
uv run ruff format src tests
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read the [contributing guidelines](CONTRIBUTING.md) first.

---

*Built with Claude Code, for Claude Code.*
