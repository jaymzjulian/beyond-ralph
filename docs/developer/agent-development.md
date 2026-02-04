# Beyond Ralph - Agent Development Guide

## Overview

Beyond Ralph uses specialized agents for each development phase. This guide explains how to create new agents or extend existing ones.

## Agent Architecture

### Base Classes

```python
from beyond_ralph.agents.base import (
    AgentModel,
    AgentTask,
    AgentResult,
    BaseAgent,
)
```

### AgentModel

Configuration for an agent:

```python
@dataclass
class AgentModel:
    agent_type: str           # "spec", "interview", "implementation", etc.
    can_implement: bool = False
    can_test: bool = False
    can_review: bool = False
    max_retries: int = 3
    timeout_seconds: int = 300
```

### AgentTask

Task specification:

```python
@dataclass
class AgentTask:
    task_id: str
    description: str
    context: dict[str, Any]
    parent_task_id: str | None = None
```

### AgentResult

Execution result:

```python
@dataclass
class AgentResult:
    success: bool
    message: str
    errors: list[str] = field(default_factory=list)
    evidence_path: Path | None = None
    question: str | None = None        # For follow-up
    knowledge_entries: list[str] = field(default_factory=list)
```

## Creating a New Agent

### Step 1: Define the Agent Class

```python
from beyond_ralph.agents.base import BaseAgent, AgentModel, AgentTask, AgentResult

class MyCustomAgent(BaseAgent):
    """Custom agent for specific task."""

    def __init__(self, model: AgentModel | None = None):
        super().__init__(model or AgentModel(agent_type="custom"))

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute the agent's task."""
        try:
            # Your implementation here
            result = await self._do_work(task)

            return AgentResult(
                success=True,
                message=f"Completed: {task.description}",
                evidence_path=Path("evidence/custom/result.txt"),
            )
        except Exception as e:
            return AgentResult(
                success=False,
                message=str(e),
                errors=[str(e)],
            )

    async def _do_work(self, task: AgentTask) -> str:
        """Internal implementation."""
        # Access context
        spec = task.context.get("spec", "")

        # Do work...
        return "result"
```

### Step 2: Add Knowledge Base Integration

```python
from beyond_ralph.core.knowledge import KnowledgeBase, create_knowledge_entry

class MyCustomAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase | None = None):
        super().__init__(AgentModel(agent_type="custom"))
        self.knowledge = knowledge_base or KnowledgeBase()

    async def execute(self, task: AgentTask) -> AgentResult:
        # Check existing knowledge first
        existing = self.knowledge.search(task.description)
        if existing:
            # Use existing knowledge
            pass

        # Do work...
        result = await self._do_work(task)

        # Store new knowledge
        entry = create_knowledge_entry(
            title=f"Custom Agent: {task.task_id}",
            content=result,
            session_id=task.task_id,
            category="custom",
        )
        self.knowledge.write(entry)

        return AgentResult(
            success=True,
            message="Completed",
            knowledge_entries=[entry.title],
        )
```

### Step 3: Add Evidence Generation

```python
class MyCustomAgent(BaseAgent):
    async def execute(self, task: AgentTask) -> AgentResult:
        # Create evidence directory
        evidence_dir = Path("records") / task.context.get("module", "default") / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        # Do work...
        result = await self._do_work(task)

        # Write evidence
        evidence_file = evidence_dir / f"{task.task_id}.txt"
        evidence_file.write_text(f"Evidence for {task.task_id}:\n{result}")

        return AgentResult(
            success=True,
            message="Completed with evidence",
            evidence_path=evidence_file,
        )
```

### Step 4: Support Questions (Follow-up)

```python
class MyCustomAgent(BaseAgent):
    async def execute(self, task: AgentTask) -> AgentResult:
        # Check if we need clarification
        if self._needs_clarification(task):
            return AgentResult(
                success=True,  # Not a failure, just need info
                message="Need clarification",
                question="What format should the output be in?",
            )

        # Continue with work...
```

## Phase Agent Pattern

Phase agents follow a specific pattern:

```python
class PhaseAgent(BaseAgent):
    """Base for phase-specific agents."""

    def __init__(self, phase: Phase):
        super().__init__(AgentModel(agent_type=phase.value))
        self.phase = phase

    async def execute(self, task: AgentTask) -> AgentResult:
        # Phase-specific validation
        if not self._validate_input(task):
            return self._invalid_input_result(task)

        # Execute phase work
        return await self._execute_phase(task)

    async def _execute_phase(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError
```

Example: Spec Agent

```python
class SpecAgent(PhaseAgent):
    def __init__(self):
        super().__init__(Phase.SPEC_INGESTION)

    async def _execute_phase(self, task: AgentTask) -> AgentResult:
        spec_content = task.context.get("spec", "")

        # Analyze specification
        analysis = self._analyze_spec(spec_content)

        # Store in knowledge base
        self.knowledge.write(create_knowledge_entry(
            title="Spec Analysis",
            content=analysis,
            session_id=task.task_id,
            category="phase-1",
        ))

        return AgentResult(
            success=True,
            message="Specification analyzed",
            knowledge_entries=["Spec Analysis"],
        )
```

## Trust Model Agent Pattern

Agents that participate in the three-agent trust model:

```python
class TrustModelAgent(BaseAgent):
    """Agent participating in trust validation."""

    def __init__(
        self,
        agent_type: str,
        can_implement: bool = False,
        can_test: bool = False,
        can_review: bool = False,
    ):
        super().__init__(AgentModel(
            agent_type=agent_type,
            can_implement=can_implement,
            can_test=can_test,
            can_review=can_review,
        ))

    def can_validate_own_work(self) -> bool:
        """Trust model: agents don't validate their own work."""
        return False
```

Example: Code Review Agent

```python
class CodeReviewAgent(TrustModelAgent):
    def __init__(self):
        super().__init__(
            agent_type="review",
            can_review=True,
        )
        self.linters = self._detect_linters()

    async def execute(self, task: AgentTask) -> AgentResult:
        files = task.context.get("files", [])

        findings = []
        for file in files:
            findings.extend(await self._review_file(file))

        if findings:
            return AgentResult(
                success=True,
                message=f"Found {len(findings)} items to fix",
                errors=[str(f) for f in findings],
            )

        return AgentResult(
            success=True,
            message="Code review passed",
        )
```

## Testing Agents

### Unit Testing

```python
import pytest
from beyond_ralph.agents.base import AgentTask

class TestMyCustomAgent:
    def test_execute_success(self):
        agent = MyCustomAgent()
        task = AgentTask(
            task_id="test-1",
            description="Test task",
            context={"key": "value"},
        )

        result = asyncio.run(agent.execute(task))

        assert result.success
        assert "Completed" in result.message

    def test_execute_with_knowledge(self, tmp_path):
        kb = KnowledgeBase(tmp_path / "knowledge")
        agent = MyCustomAgent(knowledge_base=kb)

        task = AgentTask(
            task_id="test-2",
            description="Test with knowledge",
            context={},
        )

        result = asyncio.run(agent.execute(task))

        assert result.knowledge_entries
        assert kb.search("test-2")
```

### Integration Testing

```python
class TestMyAgentIntegration:
    def test_full_workflow(self, orchestrator):
        # Register agent
        orchestrator.register_agent("custom", MyCustomAgent)

        # Execute phase
        result = asyncio.run(orchestrator._execute_custom_phase())

        assert result.success
        assert orchestrator.records_manager.get_incomplete_tasks() == []
```

## Best Practices

### 1. Never Fake Results

```python
# WRONG
async def execute(self, task: AgentTask) -> AgentResult:
    try:
        result = await self._do_work(task)
    except Exception:
        return AgentResult(success=True, message="Done")  # FAKE!

# RIGHT
async def execute(self, task: AgentTask) -> AgentResult:
    try:
        result = await self._do_work(task)
        return AgentResult(success=True, message="Done")
    except Exception as e:
        return AgentResult(
            success=False,
            message=f"Failed: {e}",
            errors=[str(e)],
        )
```

### 2. Provide Evidence

```python
# Always provide evidence for claims
return AgentResult(
    success=True,
    message="Tests passed",
    evidence_path=Path("evidence/test-output.txt"),
)
```

### 3. Use Knowledge Base

```python
# Check knowledge before duplicating work
existing = self.knowledge.search(task.description)
if existing:
    return AgentResult(
        success=True,
        message="Already completed (from knowledge)",
    )
```

### 4. Support Questions

```python
# Return questions instead of guessing
if not self._have_enough_info(task):
    return AgentResult(
        success=True,
        question="What authentication method should be used?",
    )
```

### 5. Keep Context Lean

```python
# Don't store large data in context
# Use file references instead
task.context = {
    "spec_path": "/path/to/spec.md",  # Reference, not content
    "module": "auth",
}
```

## Agent Registry

To make an agent available to the orchestrator:

```python
# In orchestrator.py or phase handlers
from beyond_ralph.agents.my_agent import MyCustomAgent

# Use in phase handler
async def _phase_custom(self) -> PhaseResult:
    agent = MyCustomAgent()
    task = AgentTask(...)
    result = await agent.execute(task)
    # ...
```

## Next Steps

- [Plugin Structure](plugin-structure.md)
- [Contributing Guide](contributing.md)
- [Architecture Overview](architecture.md)
