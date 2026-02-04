"""Phase-specific agents for Beyond Ralph.

These agents handle specific phases of the Spec and Interview Coder methodology:
1. SpecAgent - Ingests and analyzes specifications
2. InterviewAgent - Conducts deep user interviews
3. SpecCreationAgent - Creates modular specifications
4. PlanningAgent - Creates project plans
5. ReviewAgent - Reviews for uncertainties
6. ValidationAgent - Validates project plans
7. ImplementationAgent - Implements features with TDD
8. TestingAgent - Runs tests and provides evidence
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beyond_ralph.agents.base import (
    AgentModel,
    AgentResult,
    AgentTask,
    PhaseAgent,
    TrustModelAgent,
)


class SpecAgent(PhaseAgent):
    """Phase 1: Specification Ingestion Agent.

    Reads and analyzes the user's specification file,
    extracts requirements, and identifies ambiguities.
    """

    name = "spec_agent"
    description = "Ingests and analyzes specification files"
    tools = ["Read", "Glob", "WebFetch", "Grep"]
    model = AgentModel.SONNET
    phase = 1

    async def execute(self, task: AgentTask) -> AgentResult:
        """Ingest and analyze specification.

        Expected context:
        - spec_path: Path to specification file
        """
        spec_path = task.context.get("spec_path")
        if not spec_path:
            return self.fail("No specification path provided")

        spec_file = Path(spec_path)
        if not spec_file.exists():
            return self.fail(f"Specification file not found: {spec_path}")

        try:
            content = spec_file.read_text()

            # Analyze the specification
            analysis = await self._analyze_spec(content)

            # Write to knowledge base
            await self.write_knowledge(
                title="spec-analysis",
                content=f"# Specification Analysis\n\n{analysis['summary']}",
                category="specification",
                tags=["spec", "analysis", "phase-1"],
            )

            return self.succeed(
                output="Specification ingested successfully",
                data={
                    "requirements": analysis["requirements"],
                    "ambiguities": analysis["ambiguities"],
                    "technologies": analysis["technologies"],
                },
            )

        except Exception as e:
            return self.fail(f"Failed to read specification: {e}")

    async def _analyze_spec(self, content: str) -> dict[str, Any]:
        """Analyze specification content."""
        # Extract sections
        lines = content.split("\n")
        requirements = []
        ambiguities = []
        technologies = []

        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                requirements.append(line[2:])
            elif "?" in line:
                ambiguities.append(line)

        return {
            "summary": f"Found {len(requirements)} requirements, {len(ambiguities)} potential ambiguities",
            "requirements": requirements,
            "ambiguities": ambiguities,
            "technologies": technologies,
        }


class InterviewAgent(PhaseAgent):
    """Phase 2: Interview Agent.

    Conducts deep user interviews to clarify requirements,
    preferences, and make decisions. Also verifies that all
    required resources are available.
    """

    name = "interview_agent"
    description = "Conducts user interviews for requirement clarification"
    tools = ["AskUserQuestion", "Read"]
    model = AgentModel.OPUS  # Use most capable for interviews
    phase = 2

    async def execute(self, task: AgentTask) -> AgentResult:
        """Conduct user interview.

        Expected context:
        - questions: List of questions to ask
        - ambiguities: Ambiguities from spec analysis
        - required_resources: Optional dict of resource requirements
        """
        questions = task.context.get("questions", [])
        ambiguities = task.context.get("ambiguities", [])
        required_resources = task.context.get("required_resources", {})

        # Check resource availability first
        resource_issues = await self._check_resources(required_resources)

        # Combine into interview questions
        all_questions = questions + [
            f"Could you clarify: {a}" for a in ambiguities
        ]

        # Add resource questions if any resources are missing
        if resource_issues:
            all_questions.extend([
                f"Resource unavailable - {issue}. Can you provide this?"
                for issue in resource_issues
            ])

        if not all_questions:
            return self.succeed(
                output="No questions needed - specification is clear",
                data={"decisions": [], "resources_verified": True},
            )

        # In real implementation, this would use AskUserQuestion
        # For now, return with questions to ask
        return self.return_with_question(
            question="\n".join(all_questions[:5]),  # Ask first 5
            output="Interview in progress",
            data={
                "pending_questions": all_questions[5:],
                "resource_issues": resource_issues,
            },
        )

    async def _check_resources(self, requirements: dict[str, Any]) -> list[str]:
        """Check if required resources are available.

        Args:
            requirements: Dict with resource requirements

        Returns:
            List of unavailable resource descriptions
        """
        issues: list[str] = []

        # Import resource checking utilities
        from beyond_ralph.utils.system import (
            check_api_endpoint,
            check_database,
            check_file_exists,
            check_tool_installed,
            check_env_var,
        )

        # Check API endpoints
        for url in requirements.get("apis", []):
            check = await check_api_endpoint(url)
            if not check.available:
                issues.append(f"API {url}: {check.details}")

        # Check databases
        for db_spec in requirements.get("databases", []):
            if isinstance(db_spec, dict):
                check = await check_database(
                    db_spec.get("type", "postgres"),
                    db_spec.get("host", "localhost"),
                    db_spec.get("port"),
                )
            else:
                check = await check_database(db_spec)
            if not check.available:
                issues.append(f"Database: {check.details}")

        # Check files
        for path in requirements.get("files", []):
            check = check_file_exists(path)
            if not check.available:
                issues.append(f"File {path}: {check.details}")

        # Check tools
        for tool in requirements.get("tools", []):
            check = check_tool_installed(tool)
            if not check.available:
                issues.append(f"Tool {tool}: {check.details}")

        # Check environment variables
        for var in requirements.get("env_vars", []):
            check = check_env_var(var)
            if not check.available:
                issues.append(f"Environment: {check.details}")

        return issues


class SpecCreationAgent(PhaseAgent):
    """Phase 3: Specification Creation Agent.

    Creates modular specifications from interview results.
    """

    name = "spec_creation_agent"
    description = "Creates modular specifications"
    tools = ["Read", "Write"]
    model = AgentModel.SONNET
    phase = 3

    async def execute(self, task: AgentTask) -> AgentResult:
        """Create modular specification.

        Expected context:
        - requirements: List of requirements
        - decisions: List of decisions from interview
        """
        requirements = task.context.get("requirements", [])
        decisions = task.context.get("decisions", [])

        # Generate modular spec
        spec_content = self._generate_modular_spec(requirements, decisions)

        # Write spec to file
        spec_file = self.project_root / "MODULAR_SPEC.md"
        spec_file.write_text(spec_content)

        return self.succeed(
            output=f"Created modular specification: {spec_file}",
            data={"spec_file": str(spec_file)},
            artifacts=[spec_file],
        )

    def _generate_modular_spec(
        self,
        requirements: list[str],
        decisions: list[str],
    ) -> str:
        """Generate modular specification content."""
        sections = ["# Modular Specification\n"]

        sections.append("## Modules\n")
        for i, req in enumerate(requirements, 1):
            sections.append(f"### Module {i}\n")
            sections.append(f"{req}\n\n")

        if decisions:
            sections.append("## Decisions\n")
            for decision in decisions:
                sections.append(f"- {decision}\n")

        return "\n".join(sections)


class PlanningAgent(PhaseAgent):
    """Phase 4: Planning Agent.

    Creates detailed project plans with task breakdowns.
    """

    name = "planning_agent"
    description = "Creates project plans"
    tools = ["Read", "Write"]
    model = AgentModel.SONNET
    phase = 4

    async def execute(self, task: AgentTask) -> AgentResult:
        """Create project plan.

        Expected context:
        - spec_file: Path to modular specification
        """
        spec_file = task.context.get("spec_file")
        if not spec_file:
            return self.fail("No specification file provided")

        spec_path = Path(spec_file)
        if not spec_path.exists():
            return self.fail(f"Specification not found: {spec_file}")

        spec_content = spec_path.read_text()

        # Generate project plan
        plan_content = self._generate_plan(spec_content)

        plan_file = self.project_root / "PROJECT_PLAN.md"
        plan_file.write_text(plan_content)

        return self.succeed(
            output=f"Created project plan: {plan_file}",
            data={"plan_file": str(plan_file)},
            artifacts=[plan_file],
        )

    def _generate_plan(self, spec_content: str) -> str:
        """Generate project plan from specification."""
        sections = ["# Project Plan\n"]
        sections.append("## Tasks\n")

        # Extract modules from spec
        lines = spec_content.split("\n")
        task_num = 1

        for line in lines:
            if line.startswith("### Module"):
                sections.append(f"### Task {task_num}\n")
                sections.append("- [ ] Planned\n")
                sections.append("- [ ] Implemented\n")
                sections.append("- [ ] Mock tested\n")
                sections.append("- [ ] Integration tested\n")
                sections.append("- [ ] Live tested\n\n")
                task_num += 1

        return "\n".join(sections)


class UncertaintyReviewAgent(PhaseAgent):
    """Phase 5: Uncertainty Review Agent.

    Reviews plans for uncertainties that need clarification.
    """

    name = "review_agent"
    description = "Reviews for uncertainties"
    tools = ["Read", "Grep"]
    model = AgentModel.SONNET
    phase = 5

    async def execute(self, task: AgentTask) -> AgentResult:
        """Review for uncertainties.

        Expected context:
        - plan_file: Path to project plan
        """
        plan_file = task.context.get("plan_file")
        if not plan_file:
            return self.fail("No plan file provided")

        plan_path = Path(plan_file)
        if not plan_path.exists():
            return self.fail(f"Plan not found: {plan_file}")

        plan_content = plan_path.read_text()

        # Check for uncertainties
        uncertainties = self._find_uncertainties(plan_content)

        if uncertainties:
            return self.succeed(
                output=f"Found {len(uncertainties)} uncertainties that need clarification",
                data={
                    "uncertainties": uncertainties,
                    "needs_interview": True,
                },
            )
        else:
            return self.succeed(
                output="No uncertainties found - ready for implementation",
                data={"needs_interview": False},
            )

    def _find_uncertainties(self, content: str) -> list[str]:
        """Find uncertainties in plan content."""
        uncertainties = []
        indicators = ["TBD", "TODO", "unclear", "unknown", "?"]

        for line in content.split("\n"):
            for indicator in indicators:
                if indicator.lower() in line.lower():
                    uncertainties.append(line.strip())
                    break

        return uncertainties


class ValidationAgent(PhaseAgent):
    """Phase 6: Validation Agent.

    Validates the project plan is complete and feasible.
    """

    name = "validation_agent"
    description = "Validates project plans"
    tools = ["Read", "Grep", "Bash"]
    model = AgentModel.SONNET
    phase = 6

    async def execute(self, task: AgentTask) -> AgentResult:
        """Validate project plan.

        Expected context:
        - plan_file: Path to project plan
        """
        plan_file = task.context.get("plan_file")
        if not plan_file:
            return self.fail("No plan file provided")

        plan_path = Path(plan_file)
        if not plan_path.exists():
            return self.fail(f"Plan not found: {plan_file}")

        plan_content = plan_path.read_text()

        # Validate the plan
        issues = self._validate_plan(plan_content)

        if issues:
            return self.succeed(
                output=f"Validation found {len(issues)} issues",
                data={"issues": issues, "valid": False},
            )
        else:
            return self.succeed(
                output="Plan validated successfully",
                data={"valid": True},
            )

    def _validate_plan(self, content: str) -> list[str]:
        """Validate plan content."""
        issues = []

        if "## Tasks" not in content:
            issues.append("Missing Tasks section")

        if "- [ ]" not in content:
            issues.append("No task checkboxes found")

        return issues


class ImplementationAgent(TrustModelAgent, PhaseAgent):
    """Phase 7: Implementation Agent.

    Implements features using TDD (Test-Driven Development).
    This agent writes code but cannot validate its own work.
    """

    name = "implementation_agent"
    description = "Implements features with TDD"
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = AgentModel.SONNET
    phase = 7

    # Trust model: can implement, cannot test/validate own work
    can_implement = True
    can_test = False
    can_review = False

    async def execute(self, task: AgentTask) -> AgentResult:
        """Implement a feature.

        Expected context:
        - feature: Feature description
        - spec: Feature specification
        """
        feature = task.context.get("feature", "Unknown feature")

        # In real implementation, this would:
        # 1. Write tests first (TDD)
        # 2. Implement the feature
        # 3. Ensure tests pass

        return self.succeed(
            output=f"Implemented feature: {feature}",
            data={
                "feature": feature,
                "files_created": [],
                "tests_written": [],
            },
        )


class TestingValidationAgent(TrustModelAgent, PhaseAgent):
    """Phase 8: Testing Agent.

    Runs tests and provides evidence of test results.
    This agent tests but cannot implement features.
    """

    name = "testing_agent"
    description = "Runs tests and provides evidence"
    tools = ["Read", "Bash"]
    model = AgentModel.SONNET
    phase = 8

    # Trust model: can test, cannot implement
    can_implement = False
    can_test = True
    can_review = False

    async def execute(self, task: AgentTask) -> AgentResult:
        """Run tests and collect evidence.

        Expected context:
        - test_path: Path to tests
        - feature: Feature being tested
        """
        test_path = task.context.get("test_path", "tests/")
        feature = task.context.get("feature", "")

        # Run tests
        from beyond_ralph.testing import TestRunner

        runner = TestRunner(self.project_root)
        results = await runner.run_pytest(test_path=test_path)

        all_passed = all(r.passed for r in results)

        return self.succeed(
            output=f"Tests {'passed' if all_passed else 'failed'} for {feature}",
            data={
                "passed": all_passed,
                "results": [r.to_dict() for r in results],
            },
        )


class SpecComplianceAgent(TrustModelAgent):
    """Spec Compliance Verification Agent.

    This agent verifies that the implementation matches the specification.
    It is SEPARATE from both the implementation agent and testing agent.

    CRITICAL: This agent catches cases where tests pass but the implementation
    doesn't actually match what was specified. This is a key integrity check.

    Trust model: can verify spec compliance, cannot implement or test.
    """

    name = "spec_compliance_agent"
    description = "Verifies implementation matches specification"
    tools = ["Read", "Grep", "Glob"]
    model = AgentModel.OPUS  # Use most capable model for spec analysis

    # Trust model: can verify spec, cannot implement or test
    can_implement = False
    can_test = False
    can_review = True  # Can review for spec compliance

    async def execute(self, task: AgentTask) -> AgentResult:
        """Verify implementation matches specification.

        Expected context:
        - spec_path: Path to the specification
        - implementation_path: Path to the implementation
        - task_description: What the task was supposed to do
        - module: Module being verified

        Returns:
        - AgentResult with compliance status and evidence
        """
        spec_path = task.context.get("spec_path")
        impl_path = task.context.get("implementation_path")
        task_desc = task.context.get("task_description", "")
        module = task.context.get("module", "unknown")

        if not spec_path or not impl_path:
            return self.fail(
                "Cannot verify spec compliance: missing spec_path or implementation_path"
            )

        # Read the specification
        spec_file = self.project_root / spec_path if self.project_root else Path(spec_path)
        if not spec_file.exists():
            return self.fail(f"Specification file not found: {spec_path}")

        spec_content = spec_file.read_text()

        # Read the implementation
        impl_file = self.project_root / impl_path if self.project_root else Path(impl_path)
        if not impl_file.exists():
            return self.fail(f"Implementation file not found: {impl_path}")

        impl_content = impl_file.read_text()

        # Analyze compliance
        compliance_result = self._verify_compliance(
            spec_content=spec_content,
            impl_content=impl_content,
            task_description=task_desc,
        )

        if compliance_result["compliant"]:
            return self.succeed(
                output=f"Implementation of '{module}' is SPEC COMPLIANT",
                data={
                    "compliant": True,
                    "module": module,
                    "evidence": compliance_result["evidence"],
                    "spec_path": str(spec_path),
                    "implementation_path": str(impl_path),
                    "verified_by": self.name,
                },
            )
        else:
            return self.fail(
                f"Implementation of '{module}' does NOT match specification. "
                f"Issues: {compliance_result['issues']}",
                data={
                    "compliant": False,
                    "module": module,
                    "issues": compliance_result["issues"],
                    "evidence": compliance_result["evidence"],
                    "spec_path": str(spec_path),
                    "implementation_path": str(impl_path),
                },
            )

    def _verify_compliance(
        self,
        spec_content: str,
        impl_content: str,
        task_description: str,
    ) -> dict:
        """Verify that implementation matches specification.

        This is a structural check - the orchestrator should spawn
        an actual LLM agent to do deep semantic analysis.

        Returns:
            dict with 'compliant', 'evidence', and 'issues' keys
        """
        evidence = []
        issues = []

        # Extract requirements from spec (lines with specific markers)
        requirements = []
        for line in spec_content.split("\n"):
            line_lower = line.lower().strip()
            if any(marker in line_lower for marker in [
                "must ", "shall ", "should ", "required",
                "- [ ]", "* [ ]", "requirement:", "req:"
            ]):
                requirements.append(line.strip())

        evidence.append(f"Found {len(requirements)} requirements in specification")

        # Check implementation has expected structure
        impl_lines = impl_content.split("\n")
        impl_has_code = any(
            line.strip() and not line.strip().startswith("#")
            for line in impl_lines
        )

        if not impl_has_code:
            issues.append("Implementation appears to be empty or only comments")

        # Check for function/class definitions
        has_definitions = any(
            line.strip().startswith(("def ", "class ", "async def "))
            for line in impl_lines
        )

        if has_definitions:
            evidence.append("Implementation contains function/class definitions")
        else:
            issues.append("No function or class definitions found in implementation")

        # Check for common completeness indicators
        has_docstrings = '"""' in impl_content or "'''" in impl_content
        has_error_handling = "except" in impl_content or "raise" in impl_content

        if has_docstrings:
            evidence.append("Implementation has documentation")
        if has_error_handling:
            evidence.append("Implementation has error handling")

        # For a real implementation, the orchestrator would spawn an LLM
        # to do deep semantic analysis of spec vs implementation

        compliant = len(issues) == 0 and len(requirements) > 0

        return {
            "compliant": compliant,
            "evidence": evidence,
            "issues": issues,
            "requirements_found": len(requirements),
        }


# Export all phase agents
PHASE_AGENTS = {
    1: SpecAgent,
    2: InterviewAgent,
    3: SpecCreationAgent,
    4: PlanningAgent,
    5: UncertaintyReviewAgent,
    6: ValidationAgent,
    7: ImplementationAgent,
    8: TestingValidationAgent,
}

# Additional specialized agents (not phase-specific)
SPECIALIZED_AGENTS = {
    "spec_compliance": SpecComplianceAgent,
}


def get_phase_agent(phase: int) -> type[PhaseAgent]:
    """Get the agent class for a specific phase.

    Args:
        phase: Phase number (1-8)

    Returns:
        Agent class for that phase

    Raises:
        ValueError: If phase is invalid
    """
    if phase not in PHASE_AGENTS:
        raise ValueError(f"Invalid phase: {phase}. Must be 1-8.")
    return PHASE_AGENTS[phase]


def get_specialized_agent(name: str) -> type[TrustModelAgent]:
    """Get a specialized agent by name.

    Args:
        name: Agent name (e.g., 'spec_compliance')

    Returns:
        Agent class

    Raises:
        ValueError: If agent name is invalid
    """
    if name not in SPECIALIZED_AGENTS:
        raise ValueError(f"Unknown specialized agent: {name}")
    return SPECIALIZED_AGENTS[name]
