# Module 2: Agents - Specification

> Agent Framework: Phase agents, trust model agents, and research capabilities.

---

## Overview

The Agents module provides all agent types used by Beyond Ralph. Agents are Claude Code sessions with specific prompts and capabilities. The module implements the **three-agent trust model** where no agent is trusted - every implementation requires validation by separate agents.

**Key Principle**: Coding agent implements, Testing agent validates, Review agent audits.

---

## Components

### 2.1 Base Agent (`base.py`)

**Purpose**: Common agent infrastructure and interfaces.

**Interfaces**:
```python
@dataclass
class AgentModel:
    """Agent capability definition."""
    agent_type: str
    can_implement: bool = False
    can_test: bool = False
    can_review: bool = False
    can_research: bool = False
    prompt_template: str = ""

@dataclass
class AgentTask:
    """Task definition for an agent."""
    task_id: str
    description: str
    module: str
    spec_path: Optional[str] = None
    context: dict = field(default_factory=dict)
    parent_session: Optional[str] = None

@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    output: str
    evidence_path: Optional[str] = None
    question: Optional[str] = None  # Return with question instead of result
    learnings: list[str] = field(default_factory=list)  # For knowledge base
    artifacts: dict[str, str] = field(default_factory=dict)  # Files created
    review_items: list["ReviewItem"] = field(default_factory=list)

class BaseAgent:
    """Base class for all agents."""

    model: AgentModel

    def __init__(self, session_manager: SessionManager):
        """Initialize agent with session manager."""

    def get_prompt(self, task: AgentTask) -> str:
        """Generate prompt for the task.

        MUST include the "never fake results" instruction from principles.py.
        """

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute task and return result.

        Flow:
            1. Generate prompt
            2. Spawn session
            3. Stream output
            4. Collect result
            5. Store learnings in knowledge base
        """

    def _include_principles(self) -> str:
        """Return agent principles to include in prompt."""
```

---

### 2.2 Phase Agents (`phase_agents.py`)

**Purpose**: Agents for each development phase.

**Agent Types**:

#### SpecAgent (Phase 1)
```python
class SpecAgent(BaseAgent):
    """Ingest and analyze project specification."""

    model = AgentModel(
        agent_type="spec_agent",
        prompt_template="""
        You are a specification analysis agent. Your task is to:
        1. Read the provided specification file
        2. Extract all requirements
        3. Identify potential ambiguities
        4. Prepare questions for the interview phase
        5. Store findings in the knowledge base

        NEVER fake results. Report exactly what you find.
        """
    )

    async def execute(self, task: AgentTask) -> AgentResult:
        """Ingest specification and prepare for interview."""
```

#### InterviewAgent (Phase 2)
```python
class InterviewAgent(BaseAgent):
    """Deep user interview for requirements clarification."""

    model = AgentModel(
        agent_type="interview_agent",
        prompt_template="""
        You are an interview agent. Your task is to:
        1. Ask thorough questions about the specification
        2. Use AskUserQuestion for EVERY question
        3. Be incredibly in-depth - this is the ONLY approval gate
        4. Do NOT take "no" for an answer on critical requirements
        5. Persist: 3 follow-ups then INSIST

        Wait indefinitely for user responses.
        Store all decisions in knowledge base.
        """
    )

    async def execute(self, task: AgentTask) -> AgentResult:
        """Conduct deep interview with user."""
```

#### SpecCreationAgent (Phase 3)
```python
class SpecCreationAgent(BaseAgent):
    """Create modular specification from interview decisions."""

    model = AgentModel(
        agent_type="spec_creation_agent",
        prompt_template="""
        You are a specification creation agent. Your task is to:
        1. Read all interview decisions from knowledge base
        2. Create a complete modular specification
        3. Split into independent modules with clear interfaces
        4. Define dependencies between modules
        5. Store in MODULAR_SPEC.md and records/*/spec.md
        """
    )
```

#### PlanningAgent (Phase 4)
```python
class PlanningAgent(BaseAgent):
    """Create project plan with milestones."""

    model = AgentModel(
        agent_type="planning_agent",
        prompt_template="""
        You are a planning agent. Your task is to:
        1. Create PROJECT_PLAN.md from modular spec
        2. Define milestones for each module
        3. Include testing plans
        4. Establish implementation order
        5. Create records/*/tasks.md for each module
        """
    )
```

#### UncertaintyReviewAgent (Phase 5)
```python
class UncertaintyReviewAgent(BaseAgent):
    """Review for uncertainties before implementation."""

    model = AgentModel(
        agent_type="uncertainty_review_agent",
        prompt_template="""
        You are an uncertainty review agent. Your task is to:
        1. Examine all specifications and plans
        2. Identify ANY uncertainties
        3. If uncertainties found, return should_loop=True
        4. List questions to ask in next interview phase

        Be thorough - better to ask now than discover later.
        """
    )
```

#### ValidationAgent (Phase 6)
```python
class ValidationAgent(BaseAgent):
    """Validate project plan before implementation."""

    model = AgentModel(
        agent_type="validation_agent",
        prompt_template="""
        You are a validation agent. Your task is to:
        1. Validate the project plan is implementable
        2. Check all modules have clear interfaces
        3. Verify testing plans are adequate
        4. Confirm dependencies are ordered correctly
        5. Approve or request adjustments

        You are SEPARATE from the planning agent.
        """
    )
```

#### ImplementationAgent (Phase 7)
```python
class ImplementationAgent(BaseAgent):
    """Test-driven development implementation."""

    model = AgentModel(
        agent_type="implementation_agent",
        can_implement=True,
        prompt_template="""
        You are an implementation agent. Your task is to:
        1. Read the module specification
        2. Write tests FIRST (TDD)
        3. Implement to pass the tests
        4. Commit atomic changes
        5. Update records/*/tasks.md

        You WILL be validated by a Testing Agent.
        You WILL be reviewed by a Code Review Agent.
        Action ALL review items - no dismissals.
        """
    )
```

#### TestingValidationAgent (Phase 8)
```python
class TestingValidationAgent(BaseAgent):
    """Test and validate implementation."""

    model = AgentModel(
        agent_type="testing_validation_agent",
        can_test=True,
        prompt_template="""
        You are a testing validation agent. Your task is to:
        1. Run all tests (unit, integration, live)
        2. Verify implementation meets specification
        3. Collect evidence of testing
        4. Mark checkboxes ONLY when tests pass
        5. REMOVE checkboxes if tests fail

        You did NOT implement this code.
        Provide EVIDENCE of all testing.
        """
    )
```

---

### 2.3 Trust Model Agents

#### SpecComplianceAgent
```python
class SpecComplianceAgent(BaseAgent):
    """Verify implementation matches specification."""

    model = AgentModel(
        agent_type="spec_compliance_agent",
        prompt_template="""
        You are a spec compliance agent. Your task is to:
        1. Read the module specification
        2. Read the implementation
        3. Verify EVERY spec requirement is implemented
        4. Mark Spec Compliant checkbox ONLY if compliant
        5. REMOVE Implemented checkbox if not compliant

        You are SEPARATE from implementation and testing agents.
        This is the final quality gate.
        """
    )

    async def verify_compliance(
        self,
        module: str,
        spec_path: str,
        impl_path: str
    ) -> ComplianceResult:
        """Verify implementation matches spec."""
```

---

### 2.4 Research Agent (`research_agent.py`)

**Purpose**: Discover and install tools autonomously.

**Interfaces**:
```python
class ResearchAgent(BaseAgent):
    """Autonomous tool discovery and installation."""

    # Default tool choices (Beyond Ralph's preferences)
    PREFERRED_TOOLS: dict[str, str] = {
        "web_testing": "playwright",
        "api_testing": "httpx",
        "linting_python": "ruff",
        "security_python": "bandit",
        # ... more defaults
    }

    model = AgentModel(
        agent_type="research_agent",
        can_research=True,
        prompt_template="""
        You are a research agent. Your task is to:
        1. Search the web for tools matching requirements
        2. Evaluate platform compatibility
        3. Check if actively maintained
        4. Install immediately (NO user approval needed after interview)
        5. Store discovery in knowledge base

        If a tool fails, MANDATORY: find and install alternative.
        Pick preferred tools when user hasn't specified.
        """
    )

    async def search_for_tool(
        self,
        category: str,
        platform: str,
        requirements: list[str]
    ) -> DiscoveredTool:
        """Search for appropriate tool.

        Args:
            category: Tool category (e.g., "web_testing")
            platform: Target platform
            requirements: Specific requirements

        Returns:
            DiscoveredTool with installation instructions.
        """

    async def install_tool(self, tool: DiscoveredTool) -> bool:
        """Install discovered tool.

        No user approval needed - interview was the approval gate.
        """

    async def handle_tool_failure(
        self,
        tool: str,
        error: str
    ) -> DiscoveredTool:
        """MANDATORY: Find alternative when tool fails.

        MUST NOT:
            - Ask user what to try
            - Give up without trying alternatives

        MUST:
            - Search for alternatives
            - Document failure in knowledge base
            - Install and try alternative
        """

@dataclass
class DiscoveredTool:
    name: str
    category: str
    platform_support: list[str]
    install_command: str
    version: str
    documentation_url: str
    github_stars: Optional[int]
    last_release: Optional[datetime]

@dataclass
class ToolCategory(Enum):
    WEB_TESTING = "web_testing"
    API_TESTING = "api_testing"
    CLI_TESTING = "cli_testing"
    GUI_TESTING = "gui_testing"
    LINTING = "linting"
    SECURITY = "security"
    BUILD = "build"
```

---

### 2.5 Code Review Agent (`review_agent.py`)

**Purpose**: Multi-language code review with security scanning.

**Interfaces**:
```python
class CodeReviewAgent(BaseAgent):
    """Mandatory code review with multi-language support."""

    model = AgentModel(
        agent_type="code_review_agent",
        can_review=True,
        prompt_template="""
        You are a code review agent. You MUST check:

        1. LINTING (language-specific):
           - Python: ruff, mypy (strict types)
           - JavaScript/TypeScript: eslint, tsc
           - Go: golint, go vet, staticcheck
           - Rust: cargo clippy

        2. SECURITY (OWASP/SAST):
           - Semgrep with security rulesets
           - Bandit (Python)
           - detect-secrets (hardcoded secrets)
           - Dependency audit (npm/pip/cargo)

        3. BEST PRACTICES:
           - Cyclomatic complexity (radon)
           - Dead code (vulture)
           - DRY violations
           - Error handling
           - Input validation

        ALL findings are blocking until fixed.
        """
    )

    def review(self, files: list[str]) -> ReviewResult:
        """Review files and return findings."""

    def get_linters_for_language(self, lang: str) -> list[str]:
        """Get appropriate linters for language."""

    def run_security_scan(self, files: list[str]) -> list[ReviewItem]:
        """Run security scanning tools."""

    def check_dependencies(self, project_path: str) -> list[ReviewItem]:
        """Check for vulnerable dependencies."""

@dataclass
class ReviewItem:
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal["security", "lint", "practice", "docs"]
    file: str
    line: int
    message: str
    tool: str  # Which tool found this
    fix_suggestion: Optional[str] = None

@dataclass
class ReviewResult:
    items: list[ReviewItem]
    passed: bool  # True only if 0 must-fix items
    summary: str
    tools_run: list[str]
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 1 (Core) | Session spawning, quota checks |
| Module 3 (Knowledge) | Storing learnings, reading context |
| Module 4 (Records) | Updating task checkboxes |
| Module 6 (Testing) | Using testing capabilities |
| Module 8 (System) | Installing tools |

---

## Error Handling

```python
class AgentError(BeyondRalphError):
    """Agent-specific errors."""

class AgentSpawnError(AgentError):
    """Failed to spawn agent."""

class AgentTimeoutError(AgentError):
    """Agent execution timed out."""

class ReviewFailedError(AgentError):
    """Code review found blocking issues."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Agent prompt generation, result parsing |
| Integration tests | Full agent execution flows |
| Mock tests | Agent with mocked Claude sessions |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested (99% coverage)
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
