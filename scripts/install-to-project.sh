#!/bin/bash
# Beyond Ralph - Project Installer
# Usage: ./install-to-project.sh /path/to/target/project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BEYOND_RALPH_ROOT="$(dirname "$SCRIPT_DIR")"

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <target-project-path>"
    echo ""
    echo "Example: $0 ~/my-project"
    exit 1
fi

TARGET_PROJECT="$(realpath "$1")"

if [ ! -d "$TARGET_PROJECT" ]; then
    echo "Error: Target directory does not exist: $TARGET_PROJECT"
    exit 1
fi

echo "Installing Beyond Ralph to: $TARGET_PROJECT"
echo ""

# Create .claude directory structure
echo "Creating .claude directory structure..."
mkdir -p "$TARGET_PROJECT/.claude/commands"
mkdir -p "$TARGET_PROJECT/.claude/hooks"

# Copy commands (skills)
echo "Copying Beyond Ralph commands..."
cp "$BEYOND_RALPH_ROOT/.claude/commands/beyond-ralph.md" "$TARGET_PROJECT/.claude/commands/"
cp "$BEYOND_RALPH_ROOT/.claude/commands/beyond-ralph-resume.md" "$TARGET_PROJECT/.claude/commands/"
cp "$BEYOND_RALPH_ROOT/.claude/commands/beyond-ralph-status.md" "$TARGET_PROJECT/.claude/commands/"

# Copy hooks
echo "Copying stop hook..."
cp "$BEYOND_RALPH_ROOT/.claude/hooks/stop_hook.py" "$TARGET_PROJECT/.claude/hooks/"
chmod +x "$TARGET_PROJECT/.claude/hooks/stop_hook.py"

# Create or merge settings.json
SETTINGS_FILE="$TARGET_PROJECT/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    echo "Warning: settings.json exists, backing up to settings.json.bak"
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
fi

echo "Creating settings.json with stop hook..."
cat > "$SETTINGS_FILE" << 'EOF'
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
EOF

# Ensure beyond-ralph package is installed
echo ""
echo "Checking Beyond Ralph package installation..."
if python3 -c "import beyond_ralph" 2>/dev/null; then
    echo "Beyond Ralph package already installed."
else
    echo "Installing Beyond Ralph package..."
    cd "$BEYOND_RALPH_ROOT"
    uv pip install -e .
fi

echo ""
echo "============================================"
echo "Beyond Ralph installed successfully!"
echo "============================================"
echo ""
echo "Project: $TARGET_PROJECT"
echo ""
echo "Installed files:"
echo "  .claude/commands/beyond-ralph.md"
echo "  .claude/commands/beyond-ralph-resume.md"
echo "  .claude/commands/beyond-ralph-status.md"
echo "  .claude/hooks/stop_hook.py"
echo "  .claude/settings.json"
echo ""
echo "To start development, open the project in Claude Code and run:"
echo "  /beyond-ralph start --spec SPEC.md"
echo ""
