# Beyond Ralph - Installation Guide

## Prerequisites

- **Claude Code**: The Anthropic CLI tool
- **Python 3.11+**: Required for the stop hook

Optional (for the Python CLI installer):
- **uv**: Package manager (https://github.com/astral-sh/uv)

## Method 1: Install Script (Recommended)

```bash
git clone https://github.com/jaymzee/beyond-ralph.git
./beyond-ralph/scripts/install-to-project.sh ~/your-project
```

This installs:
- Beyond Ralph commands (`/beyond-ralph`, `/beyond-ralph-resume`, `/beyond-ralph-status`)
- Stop hook for autonomous operation
- `.claude/settings.json` with hook configuration
- Beyond Ralph rules appended to your CLAUDE.md

## Method 2: Python CLI Installer (Full Setup)

Install the Beyond Ralph package first, then use the CLI:

```bash
cd beyond-ralph
uv pip install -e .

# Minimal (just Beyond Ralph)
beyond-ralph install ~/your-project --minimal

# Full (includes MCP servers, SuperClaude commands)
beyond-ralph install ~/your-project

# With free-tier MCP servers
beyond-ralph install ~/your-project --allow-free-tier-with-key
```

### CLI Options

| Flag | Effect |
|------|--------|
| `--minimal` | Only Beyond Ralph commands + hook |
| `--force` | Overwrite existing files |
| `--no-superclaude` | Skip SuperClaude commands and skills |
| `--no-mcp` | Skip MCP server configuration |
| `--install-mcp-packages` | Actually install MCP packages via npm |
| `--allow-free-tier-with-key` | Include Brave, Tavily, GitHub, Sentry MCP servers |

### MCP Servers Included (no API key)

| Server | Purpose |
|--------|---------|
| sequential-thinking | Problem-solving through thought sequences |
| context7 | Library documentation lookup |
| playwright | Browser automation for testing |
| duckduckgo | Web search |
| arxiv | Academic paper search |
| wikipedia | Wikipedia search |
| filesystem | File operations |
| memory | Persistent memory |
| git | Git operations |
| fetch | Web content fetching |
| time | Timezone operations |
| sqlite | Database operations |

## Method 3: Manual Install

```bash
cd ~/your-project
mkdir -p .claude/commands .claude/hooks

# Copy commands
cp /path/to/beyond-ralph/.claude/commands/beyond-ralph*.md .claude/commands/

# Copy stop hook
cp /path/to/beyond-ralph/.claude/hooks/stop_hook.py .claude/hooks/

# Append rules to CLAUDE.md
cat /path/to/beyond-ralph/.claude/beyond-ralph-claude-section.md >> CLAUDE.md
```

Then create `.claude/settings.json`:
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/stop_hook.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## What Gets Installed

| File | Purpose |
|------|---------|
| `.claude/commands/beyond-ralph.md` | Main orchestrator — `/beyond-ralph SPEC.md` |
| `.claude/commands/beyond-ralph-resume.md` | Resume or re-validate — `/beyond-ralph-resume` |
| `.claude/commands/beyond-ralph-status.md` | Check progress — `/beyond-ralph-status` |
| `.claude/hooks/stop_hook.py` | Keeps the orchestrator running autonomously |
| `.claude/settings.json` | Hook configuration |
| `CLAUDE.md` (appended) | Beyond Ralph rules for all agents |

## Verifying Installation

```bash
cd ~/your-project
claude
```

Then type `/beyond-ralph` — you should see the command available.

## Troubleshooting

### Stop hook not firing

Check that `.claude/settings.json` exists and has the correct hook configuration. The hook type must be `"command"` and the path must point to the stop hook script.

### "Permission denied" on stop_hook.py

```bash
chmod +x .claude/hooks/stop_hook.py
```

### Quota errors

Beyond Ralph monitors Claude usage and pauses automatically. Check status with:
```bash
uv run br-quota
```

Or just wait — it will resume when quota resets.

## Next Steps

- [Quick Start](../../QUICKSTART.md) - Get started with your first project
- [Configuration](configuration.md) - Customize Beyond Ralph
- [Testing Guide](testing.md) - Testing capabilities
