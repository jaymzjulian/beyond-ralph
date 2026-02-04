# Beyond Ralph - Installation Guide

## Prerequisites

- **Python 3.11+**: Beyond Ralph requires Python 3.11 or later
- **uv**: The recommended package manager (https://github.com/astral-sh/uv)
- **Claude Code**: The Anthropic CLI tool (https://claude.ai/code)

## Quick Install

```bash
# Clone the repository
git clone https://github.com/your-org/beyond-ralph.git
cd beyond-ralph

# Install with uv
uv sync

# Verify installation
uv run python -c "import beyond_ralph; print('Beyond Ralph installed successfully')"
```

## Manual Installation

If you prefer pip:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install .

# Verify
python -c "import beyond_ralph; print('Beyond Ralph installed successfully')"
```

## Claude Code Setup

Beyond Ralph runs as a Claude Code plugin. To enable it:

1. Copy the skills to your Claude Code configuration:
   ```bash
   mkdir -p ~/.claude/skills
   cp .claude/skills/*.yaml ~/.claude/skills/
   ```

2. Copy the hooks:
   ```bash
   mkdir -p ~/.claude/hooks
   cp .claude/hooks/*.yaml ~/.claude/hooks/
   ```

3. Verify the skills are available:
   ```bash
   claude --help
   # You should see /beyond-ralph commands listed
   ```

## Dependencies

Beyond Ralph includes these core dependencies:

| Dependency | Purpose |
|-----------|---------|
| pexpect | CLI spawning and interaction |
| typer | Command-line interface |
| rich | Terminal output formatting |
| httpx | HTTP client for API testing |
| pyyaml | Configuration file parsing |
| pillow | Screenshot analysis |

Optional dependencies for extended testing:

| Dependency | Purpose |
|-----------|---------|
| playwright | Web UI testing |
| pyautogui | Desktop GUI interaction |
| opencv-python | Video/image analysis |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BEYOND_RALPH_SAFEMODE` | Enable permission prompts | `false` |
| `BEYOND_RALPH_QUOTA_CACHE` | Quota cache file location | `.beyond_ralph_quota` |
| `BEYOND_RALPH_MAX_AGENTS` | Maximum parallel agents | `7` |

## Verifying Installation

Run the test suite:

```bash
uv run pytest tests/unit -q
```

Expected output:
```
854 passed in 30s
```

## Troubleshooting

### "Claude CLI not found"

Ensure Claude Code is installed and in your PATH:
```bash
which claude
# Should output something like /usr/local/bin/claude
```

### "Permission denied" errors

Beyond Ralph may need sudo access for system package installation. Check if passwordless sudo is available:
```bash
sudo -n true && echo "Passwordless sudo available" || echo "Sudo requires password"
```

### Quota errors

If you see quota-related errors, check your Claude usage:
```bash
uv run br-quota
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Get started with your first project
- [Configuration](configuration.md) - Customize Beyond Ralph
- [Testing Guide](testing.md) - Learn about testing capabilities
