# Beyond Ralph

Autonomous multi-agent development for Claude Code. Give it a spec, answer some questions, and watch it build your project.

## What It Does

Beyond Ralph runs **inside Claude Code** as a set of slash commands. It reads your specification, interviews you about requirements, then autonomously implements, tests, and validates the project using multiple specialized agents — each independently verifying the others' work.

### Key Principles

- **Three-agent trust model** — Separate agents for coding, testing, and code review. No agent validates its own work.
- **Adversarial spec compliance** — A dedicated agent verifies every requirement has matching code, going requirement-by-requirement with file:line evidence.
- **Zero deferral** — "Deferred to v2", "simplified version", "placeholder" = automatic FAIL. If the spec says it, it must be implemented. No exceptions.
- **Failing tests are failures** — Marking tests as `#[ignore]` / `@pytest.mark.skip` / `DISABLED_` to hide failures is caught and rejected.
- **Don't trust checkboxes** — All progress tracking is self-reported by agents. An independent adversarial audit verifies against actual source code.
- **Full autonomy** — After the interview phase, Beyond Ralph makes all decisions itself. It never stops to ask "would you like X or Y?"

## Installation

### Install Script (Recommended)

```bash
# Clone beyond-ralph
git clone https://github.com/jaymzee/beyond-ralph.git

# Run the installer
./beyond-ralph/scripts/install-to-project.sh ~/your-project
```

This copies the commands, stop hook, and settings.json, and appends Beyond Ralph rules to your CLAUDE.md.

### Python CLI Installer (Full Setup)

If you install the Beyond Ralph package, you get a richer installer with MCP server configs and SuperClaude commands:

```bash
cd beyond-ralph
uv pip install -e .

# Minimal install (just Beyond Ralph)
beyond-ralph install ~/your-project --minimal

# Full install (includes MCP servers and SuperClaude)
beyond-ralph install ~/your-project

# With free-tier MCP servers (Brave, Tavily, GitHub, Sentry)
beyond-ralph install ~/your-project --allow-free-tier-with-key
```

### Manual Install

```bash
cd ~/your-project
mkdir -p .claude/commands .claude/hooks

cp /path/to/beyond-ralph/.claude/commands/beyond-ralph*.md .claude/commands/
cp /path/to/beyond-ralph/.claude/hooks/stop_hook.py .claude/hooks/
cat /path/to/beyond-ralph/.claude/beyond-ralph-claude-section.md >> CLAUDE.md
```

You'll also need to create `.claude/settings.json` with the stop hook configured — see `scripts/install-to-project.sh` for the format.

### What Gets Installed

| File | Purpose |
|------|---------|
| `.claude/commands/beyond-ralph.md` | Main orchestrator — `/beyond-ralph SPEC.md` |
| `.claude/commands/beyond-ralph-resume.md` | Resume or re-validate — `/beyond-ralph-resume` |
| `.claude/commands/beyond-ralph-status.md` | Check progress — `/beyond-ralph-status` |
| `.claude/hooks/stop_hook.py` | Keeps the orchestrator running autonomously |
| `.claude/hooks/post_compact_hook.py` | Re-reads spec/plan/tasks after context compaction |

## Usage

```bash
cd ~/your-project
claude

# Start a new project from a spec
/beyond-ralph SPEC.md

# Check progress
/beyond-ralph-status

# Resume after pause or quota limit
/beyond-ralph-resume
```

## How It Works

### 10 Phases

| Phase | Name | What Happens |
|-------|------|--------------|
| 1 | **Spec Ingestion** | Read and analyze the specification |
| 2 | **Interview** | Ask clarifying questions *(only user input phase)* |
| 3 | **Spec Creation** | Create modular specs for each component |
| 4 | **Planning** | Build project plan with dependencies |
| 5 | **Review** | Check for gaps, loop back if needed |
| 6 | **Validation** | Separate agent validates the plan |
| 7 | **Implementation** | Build with TDD, three-agent trust model |
| 8 | **Testing** | Mock + integration tests, then live artifact testing |
| 8.5 | **Spec Compliance** | Adversarial two-pass verification against spec |
| 9 | **Audit** | Static analysis + LLM interrogation for stubs/fakes |

### Three-Agent Trust Model (Phase 7)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Coding Agent │───>│Testing Agent │───>│Review Agent  │
│ (implements) │    │ (validates)  │    │ (quality)    │
└──────────────┘    └──────────────┘    └──────────────┘
       ↑                                       │
       └───── MUST fix all review items ───────┘
```

Each agent is a separate spawn. No agent marks its own work complete.

### Live Testing (Phase 8c)

Live testing means building and running the **actual artifact**, not writing more unit tests:

| App Type | How It's Tested |
|----------|----------------|
| Compiler | Compile a source file, run the output binary, verify results |
| API/Server | Start the server, curl endpoints, verify responses |
| CLI | Run the binary with real arguments, verify stdout |
| Android | `./gradlew assembleDebug`, `adb install`, launch activity, screencap |
| iOS | `xcodebuild`, `xcrun simctl install/launch`, screenshot |
| Desktop GUI | Build, launch, interact with xdotool, screenshot verification |

### Adversarial Spec Compliance (Phase 8.5)

Two-pass verification by agents that have **no prior context**:

1. **Requirement Extraction** — A fresh agent reads the spec and extracts every requirement (REQ-001, REQ-002, ...)
2. **Adversarial Audit** — A *different* agent searches the actual source code for each requirement, marking PASS/FAIL with file:line evidence

```
SPEC_COMPLIANCE_RESULT: FAIL
TOTAL_REQUIREMENTS: 42
PASSED: 38
FAILED: 4

CHECKLIST:
REQ-001: "Support OAuth2 authentication" -> PASS | src/auth.rs:45-120
REQ-002: "Handle refresh tokens" -> FAIL | Not found in codebase
REQ-003: "Rate limit all endpoints" -> FAIL | Only /login, missing /api/*
...
```

Any single FAIL = entire check fails. The adversarial assessment **overrides** all previous checkbox states.

### Implementation Audit (Phase 9)

Three-pronged verification:

1. **Static Analysis** — Scan for `NotImplementedError`, `TODO`, `FIXME`, empty function bodies
2. **Ignored Test Detection** — Scan for `#[ignore]`, `@pytest.mark.skip`, `DISABLED_`, commented-out tests
3. **LLM Interrogation** — Ask a separate agent point-blank: "Is this implementation real or faked?"

### Task Checkboxes (7 per task)

Every task in `records/[module]/tasks.md` needs all 7 checked:

- [ ] **Planned** — Design documented
- [ ] **Implemented** — Code written fully (no stubs, no partial, no "deferred to v2")
- [ ] **Mock Tested** — Unit tests with mocks/stubs pass
- [ ] **Integration Tested** — Module interaction tests pass
- [ ] **Live Tested** — Actual built artifact executed with correct results (by a separate agent)
- [ ] **Spec Compliant** — Adversarial agent verified every requirement has matching code
- [ ] **Audit Verified** — Static analysis + LLM interrogation passed (no stubs/fakes/TODOs)

### Quota Management

Beyond Ralph monitors Claude usage and pauses automatically:

| State | Condition | Action |
|-------|-----------|--------|
| Green | < 85% | Normal operation |
| Yellow | 85-95% | Essential only |
| Red | ≥ 95% | Pause, wait for reset |

The stop hook handles autonomous resumption after quota resets.

## Project Structure

When Beyond Ralph runs on your project, it creates:

```
your-project/
├── SPEC.md                     # Your specification
├── PROJECT_PLAN.md             # Generated project plan
├── .beyond_ralph_state         # Orchestrator state (auto-managed)
├── .claude/
│   ├── commands/               # Beyond Ralph commands
│   └── hooks/stop_hook.py      # Autonomous operation hook
├── records/                    # Task tracking
│   └── [module]/
│       ├── spec.md             # Module specification
│       └── tasks.md            # Tasks with 7 checkboxes each
└── beyondralph_knowledge/      # Shared agent knowledge base
```

## The Stop Hook

The stop hook (`.claude/hooks/stop_hook.py`) is what makes Beyond Ralph truly autonomous. When Claude finishes a response, the hook:

1. Checks if the project is still running (via `.beyond_ralph_state`)
2. If incomplete tasks remain, re-feeds the orchestrator prompt to keep working
3. Detects quota limits and pauses gracefully
4. Recognizes `AUTOMATION_COMPLETE` to allow clean exit

This implements the [ralph-wiggum pattern](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) from the Claude Code plugin ecosystem.

## Philosophy

Beyond Ralph encodes hard-won lessons about autonomous AI agent reliability:

1. **Agents lie about their own work.** Every implementation must be verified by a separate agent.
2. **"100% tests pass" is meaningless** if the agent just ignored the failing tests.
3. **"Deferred to v2" means "not implemented"** and there is no v2.
4. **Checkboxes are self-graded exams.** Only actual source code is truth.
5. **Agents will find excuses to skip verification.** Close every escape hatch explicitly.
6. **Context cost is not an excuse** when the audit runs in a separate agent with its own context.

## Requirements

- Claude Code CLI
- Python 3.11+ (for stop hook)

## License

MIT — see [LICENSE](LICENSE)
