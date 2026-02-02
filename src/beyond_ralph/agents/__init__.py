"""Beyond Ralph Agent Framework.

This module provides the agent infrastructure for the Beyond Ralph
autonomous development system.

Agent Types:
- BaseAgent: Foundation class with knowledge access
- PhaseAgent: For phase-specific work (1-8)
- TrustModelAgent: For trust model (Coding, Testing, Review)

Specialized Agents:
- ResearchAgent: Autonomous tool discovery and installation
- CodeReviewAgent: Mandatory code review with linting/security
"""

from beyond_ralph.agents.base import (
    AgentModel,
    AgentResult,
    AgentStatus,
    AgentTask,
    BaseAgent,
    PhaseAgent,
    TrustModelAgent,
)
from beyond_ralph.agents.research_agent import (
    DiscoveredTool,
    ResearchAgent,
    ToolCategory,
)
from beyond_ralph.agents.review_agent import (
    CodeReviewAgent,
    ReviewCategory,
    ReviewItem,
    ReviewResult,
    ReviewSeverity,
)

__all__ = [
    # Base classes
    "AgentModel",
    "AgentResult",
    "AgentStatus",
    "AgentTask",
    "BaseAgent",
    "PhaseAgent",
    "TrustModelAgent",
    # Research Agent
    "DiscoveredTool",
    "ResearchAgent",
    "ToolCategory",
    # Review Agent
    "CodeReviewAgent",
    "ReviewCategory",
    "ReviewItem",
    "ReviewResult",
    "ReviewSeverity",
]
