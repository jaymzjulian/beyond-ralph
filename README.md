# Beyond Ralph - True Autonomous Coding

A Claude Code plugin that implements fully autonomous multi-agent development using the "Spec and Interview Coder" methodology.

## What is Beyond Ralph?

Beyond Ralph runs **inside Claude Code** as an orchestrator that spawns child Claude Code sessions to autonomously implement projects from specifications. It's NOT a separate CLI - it's a plugin that extends Claude Code itself.

## Installation

```bash
# Install the package (makes skills and hooks available to Claude Code)
pip install -e .

# Copy skill files to your Claude Code config (optional, for user-level access)
cp -r .claude/skills/* ~/.claude/skills/
cp -r .claude/hooks/* ~/.claude/hooks/
```

## Usage

Start a Claude Code session and use the skills:

```
# In Claude Code:
> /beyond-ralph SPEC.md

# Check status:
> /beyond-ralph-status

# Resume after pause:
> /beyond-ralph-resume
```

## How It Works

### Architecture

Beyond Ralph follows a strict orchestrator pattern:

1. **You run Claude Code normally**
2. **Invoke `/beyond-ralph` with your spec**
3. **Claude Code becomes the orchestrator** and spawns child sessions
4. **Child sessions do actual work** (coding, testing, reviewing)
5. **Orchestrator validates** using the trust model

### 8-Phase Methodology

1. **SPEC_INGESTION** - Analyze the provided specification
2. **INTERVIEW** - Interview user extensively with AskUserQuestion
3. **SPEC_CREATION** - Create modular specification documents
4. **PLANNING** - Create detailed project plan with milestones
5. **REVIEW** - Review for uncertainties, loop back if needed
6. **VALIDATION** - Separate agent validates the plan
7. **IMPLEMENTATION** - Implement with test-driven development
8. **TESTING** - Validate with separate testing agents

### Trust Model

No agent validates its own work:

- **Coding Agent** implements features
- **Testing Agent** (separate session) validates implementation
- **Code Review Agent** (separate session) reviews code quality
- **Orchestrator** validates all evidence

### Quota Management

Before spawning any child agent, Beyond Ralph checks `/usage`:

- At **85% session OR weekly quota**: Pause all work
- Check every **10 minutes** while paused
- Resume automatically when quota resets

### Record Keeping

Every task has 5 checkboxes that must ALL be checked:

- [ ] **Planned** - Implementation approach defined
- [ ] **Implemented** - Code written
- [ ] **Mock Tested** - Unit tests pass
- [ ] **Integration Tested** - CI/integration tests pass
- [ ] **Live Tested** - Tested in real environment

**100% completion required** - anything less is unacceptable.

### Knowledge Sharing

All agents share knowledge via `beyondralph_knowledge/`:

- Each entry includes the session UUID that created it
- Agents check knowledge base before asking orchestrator
- Enables context persistence across sessions

## Configuration

### Safemode

By default, child agents use `--dangerously-skip-permissions`.
To require permission prompts:

```
> /beyond-ralph --safemode SPEC.md
```

### Autonomous Installation

If enabled, agents can install dependencies automatically:

```
> /beyond-ralph --auto-install SPEC.md
```

## Project Structure

```
.beyond_ralph/          # State and configuration
  state.json            # Current orchestrator state

beyondralph_knowledge/  # Shared knowledge base
  *.md                  # Knowledge entries with YAML frontmatter

records/                # Task tracking
  [module]/             # Per-module task lists
    tasks.md            # Tasks with 5 checkboxes each
```

## Utilities

Check quota directly:

```bash
br-quota
```

## Requirements

- Claude Code CLI installed and authenticated
- Python 3.11+
- pexpect (for quota checking)

## License

MIT
