# Module 2: Agent Framework - Specification

**Module**: agents
**Location**: `src/beyond_ralph/agents/`
**Dependencies**: session (for spawning), knowledge (for KB access)

## Purpose

Provide the base agent infrastructure and all phase-specific agent definitions for the Spec and Interview Coder methodology.

## Requirements

### R1: Base Agent Class
- Common interface for all agents
- Knowledge base integration (read before asking orchestrator)
- Result/error handling with structured responses
- Evidence generation capability
- Return-with-question capability (agents can ask follow-ups)

### R2: Agent Definition Format
- YAML frontmatter + Markdown body
- Compatible with Claude Code subagent format
- Support for tool specification
- Model selection (sonnet, opus, haiku, inherit)
- Permission mode configuration

### R3: Phase Agents
Each phase requires a dedicated agent:

| Phase | Agent | Primary Tool | Purpose |
|-------|-------|--------------|---------|
| 1 | SpecAgent | Read, WebFetch | Ingest specification |
| 2 | InterviewAgent | AskUserQuestion | Deep user interview |
| 3 | SpecCreationAgent | Write | Create modular spec |
| 4 | PlanningAgent | Write | Create project plan |
| 5 | ReviewAgent | Read, Grep | Identify uncertainties |
| 6 | ValidationAgent | Read, Bash | Validate plans |
| 7 | ImplementationAgent | All | TDD implementation |
| 8 | TestingAgent | Bash | Test and validate |

### R4: Trust Model Agents
Three separate agents for implementation trust:

| Agent | Role | Key Constraint |
|-------|------|----------------|
| CodingAgent | Implements features | Cannot validate own work |
| TestingAgent | Runs tests, provides evidence | Cannot write feature code |
| CodeReviewAgent | Linting, security, best practices | Cannot dismiss findings |

### R5: Agent Communication
- Agents return structured results to orchestrator
- Agents can return with questions (caller follows up)
- Agents check knowledge base BEFORE asking orchestrator
- Agents write discoveries to knowledge base

## Interface

```python
class BaseAgent:
    name: str
    description: str
    tools: list[str]
    model: str

    async def execute(self, task: Task) -> AgentResult:
        """Execute agent's task."""

    async def read_knowledge(self, topic: str) -> Knowledge | None:
        """Read from knowledge base."""

    async def write_knowledge(self, entry: KnowledgeEntry) -> None:
        """Write to knowledge base."""

    async def return_with_question(self, question: str) -> AgentResult:
        """Return to caller with a question."""

@dataclass
class AgentResult:
    success: bool
    message: str
    evidence: list[Evidence] | None
    questions: list[str] | None  # For follow-up
    knowledge_written: list[str] | None  # UUIDs of KB entries
```

## Agent Definition Format

```yaml
# agents/implementation.md
---
name: implementation
description: TDD implementation agent. Implements features with tests.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
permissionMode: bypassPermissions
skills:
  - testing-skills
---

You are an implementation agent for Beyond Ralph.

Your responsibilities:
1. Implement features using TDD
2. Write tests BEFORE implementation
3. Ensure all tests pass
4. Generate evidence of completion
5. Do NOT validate your own work - that's TestingAgent's job

When you encounter something you don't know:
1. Check the knowledge base first
2. If not found, research autonomously
3. Document findings in knowledge base
4. Only return to orchestrator with question if truly blocked
```

## Testing Requirements

- Test base agent class with mock knowledge base
- Test each phase agent with mock inputs
- Test agent result handling
- Test evidence generation
- Test question-return flow
