"""Claude Code skills for Beyond Ralph.

This module provides skills that run INSIDE Claude Code sessions,
enabling the autonomous multi-agent development workflow.
"""

from pathlib import Path
from typing import Any

# Skill definitions following Claude Code skill format
SKILLS = {
    "beyond-ralph": {
        "name": "beyond-ralph",
        "description": "Start autonomous multi-agent development from a specification",
        "instructions": """You are now operating as the Beyond Ralph orchestrator.

Your role is to autonomously implement a project from a specification using the
"Spec and Interview Coder" methodology with 8 phases:

1. SPEC_INGESTION - Ingest the provided specification
2. INTERVIEW - Interview the user with AskUserQuestion for complete understanding
3. SPEC_CREATION - Create modular specification documents
4. PLANNING - Create detailed project plan with milestones
5. REVIEW - Review for uncertainties, loop back to phase 2 if needed
6. VALIDATION - Have another agent validate the plan
7. IMPLEMENTATION - Implement using test-driven development
8. TESTING - Validate implementation, loop to phase 6 if incomplete

CRITICAL RULES:
- You are the ORCHESTRATOR - spawn child Claude Code sessions for actual work
- Use `claude --dangerously-skip-permissions -p "prompt"` to spawn child agents
- Each phase should be done by a NEW agent session to preserve context
- NO agent can validate its OWN work - use separate agents for coding vs testing
- Before spawning agents, CHECK quota with /usage - pause at 85%
- Maintain knowledge in beyondralph_knowledge/ folder
- Keep detailed task records with 5 checkboxes: Planned, Implemented, Mock Tested, Integration Tested, Live Tested
- ALL 5 checkboxes must be checked for 100% completion

WORKFLOW:
1. Read the spec file provided by the user
2. Begin Phase 1: Analyze the specification
3. Phase 2: Interview user extensively with AskUserQuestion
4. Continue through all phases, spawning child agents as needed
5. Loop until ALL tasks have ALL checkboxes checked
6. Reply "AUTOMATION_COMPLETE" only when truly 100% done

Start by asking the user for the specification file path if not provided.""",
        "arguments": [
            {
                "name": "spec",
                "description": "Path to the specification file",
                "required": False,
            }
        ],
    },
    "beyond-ralph-status": {
        "name": "beyond-ralph-status",
        "description": "Check status of Beyond Ralph autonomous development",
        "instructions": """Check the status of the current Beyond Ralph project.

Read the state from .beyond_ralph/state.json and the task records from
records/ directories to report:
- Current phase
- Active agents
- Task completion status (how many have all 5 checkboxes)
- Any blocked or paused state
- Quota status

Present this as a clear status report to the user.""",
    },
    "beyond-ralph-resume": {
        "name": "beyond-ralph-resume",
        "description": "Resume a paused Beyond Ralph project",
        "instructions": """Resume a paused Beyond Ralph autonomous development project.

1. Read state from .beyond_ralph/state.json
2. Determine what phase was active when paused
3. Check quota status before resuming
4. Resume orchestration from the paused phase
5. Continue until complete or paused again

If the project was paused due to quota limits, check if quota has reset
before resuming work.""",
    },
}


def register_skills() -> dict[str, Any]:
    """Register Beyond Ralph skills with Claude Code.

    This function is called by Claude Code's plugin system via the
    entry point defined in pyproject.toml.

    Returns:
        Dictionary of skill definitions.
    """
    return SKILLS


def get_skill(name: str) -> dict[str, Any] | None:
    """Get a specific skill definition by name."""
    return SKILLS.get(name)


def list_skills() -> list[str]:
    """List all available skill names."""
    return list(SKILLS.keys())
