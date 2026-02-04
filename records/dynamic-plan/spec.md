# Module 4: Dynamic Plan Manager - Specification

> Dynamic Plan: Track inter-module requirements and project plan evolution.

---

## Overview

The Dynamic Plan Manager enables modules to add requirements to other modules and tracks discrepancies between promised and delivered functionality. The project plan is a **LIVING DOCUMENT** that evolves during implementation.

**Key Principle**: Modules can demand features from other modules, and failures MUST be reported aggressively - no silent workarounds.

---

## Location

`src/beyond_ralph/core/dynamic_plan.py`

---

## Components

### 4.1 Dynamic Plan Manager (`dynamic_plan.py`)

**Purpose**: Track inter-module requirements and discrepancies.

**Interface**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

@dataclass
class ModuleRequirement:
    """A requirement from one module to another."""
    id: str
    from_module: str
    to_module: str
    technical_spec: str  # E.g., "Provide get_user(id: str) -> User function"
    status: Literal["pending", "delivered", "failed"]
    created_at: datetime
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

@dataclass
class Discrepancy:
    """A discrepancy between promised and delivered."""
    id: str
    module: str
    expected: str
    actual: str
    severity: Literal["critical", "high", "medium"]
    reported_at: datetime
    resolved: bool = False
    resolution: Optional[str] = None

class DynamicPlanManager:
    """Manages inter-module requirements and project plan evolution."""

    def __init__(
        self,
        plan_path: str = "PROJECT_PLAN.md",
        requirements_file: str = ".beyond_ralph_requirements.json",
        discrepancies_file: str = ".beyond_ralph_discrepancies.json"
    ) -> None:
        """Initialize dynamic plan manager.

        Args:
            plan_path: Path to PROJECT_PLAN.md
            requirements_file: JSON file for requirements tracking
            discrepancies_file: JSON file for discrepancy tracking
        """

    def add_requirement(
        self,
        from_module: str,
        to_module: str,
        technical_spec: str
    ) -> str:
        """Add requirement from one module to another.

        Args:
            from_module: Module requesting the requirement.
            to_module: Module that must deliver.
            technical_spec: What is needed (technical description only).

        Returns:
            Requirement ID.

        Notes:
            - NO user input needed (only technical requirements)
            - Updates PROJECT_PLAN.md automatically
            - Orchestrator sees update and schedules work

        Example:
            dynamic_plan.add_requirement(
                from_module="auth",
                to_module="database",
                technical_spec="Provide get_user(id: str) -> User function"
            )
        """

    def mark_delivered(self, requirement_id: str) -> None:
        """Mark a requirement as successfully delivered.

        Args:
            requirement_id: ID of the requirement.
        """

    def mark_failed(
        self,
        requirement_id: str,
        reason: str
    ) -> None:
        """Mark a requirement as failed to deliver.

        Args:
            requirement_id: ID of the requirement.
            reason: Why the delivery failed.

        Note: This AGGRESSIVELY records failure for orchestrator to address.
        """

    def get_pending_requirements(self, module: str) -> list[ModuleRequirement]:
        """Get all pending requirements a module needs to receive.

        Args:
            module: Module name to check.

        Returns:
            List of requirements pending delivery TO this module.
        """

    def get_work_for_module(self, module: str) -> list[ModuleRequirement]:
        """Get requirements this module needs to deliver.

        Args:
            module: Module name to check.

        Returns:
            List of requirements this module must fulfill.
        """

    def report_discrepancy(
        self,
        module: str,
        expected: str,
        actual: str,
        severity: Literal["critical", "high", "medium"]
    ) -> str:
        """Report discrepancy between promised and delivered.

        Args:
            module: Module with the discrepancy.
            expected: What was promised/expected.
            actual: What was actually delivered.
            severity: How serious the discrepancy is.

        Returns:
            Discrepancy ID.

        Note: MUST NOT silently work around - DEMANDS fix.

        Example:
            dynamic_plan.report_discrepancy(
                module="database",
                expected="get_user() returns User object",
                actual="get_user() not implemented",
                severity="critical"
            )
        """

    def resolve_discrepancy(self, discrepancy_id: str, resolution: str) -> None:
        """Mark a discrepancy as resolved.

        Args:
            discrepancy_id: ID of the discrepancy.
            resolution: How it was resolved.
        """

    def get_discrepancies(
        self,
        unresolved_only: bool = True
    ) -> list[Discrepancy]:
        """Get all discrepancies.

        Args:
            unresolved_only: If True, only return unresolved discrepancies.

        Returns:
            List of discrepancies matching the filter.
        """

    def _update_project_plan(self) -> None:
        """Update PROJECT_PLAN.md with current requirements state.

        Adds a "Dynamic Requirements" section to the plan showing:
        - Pending requirements by module
        - Delivered requirements
        - Failed requirements
        - Unresolved discrepancies
        """
```

---

## Dynamic Requirements Rules

1. **No User Input Required**: Only technical requirements between modules
2. **Must Be Specific**: "I need function X that does Y" not "I need something"
3. **Must Update PROJECT_PLAN.md**: Formal record of the requirement
4. **Orchestrator Mediates**: Sees updates, schedules work
5. **Aggressive Accountability**: Call out failures, don't work around them
6. **Plan Is Never Static**: Expect evolution during implementation

---

## Example Flow

```python
# Module A (auth) needs something from Module B (database)
dynamic_plan.add_requirement(
    from_module="auth",
    to_module="database",
    technical_spec="Provide get_user(id: str) -> User function"
)

# Orchestrator detects new requirement
pending = dynamic_plan.get_work_for_module("database")
# -> Returns the get_user requirement

# ... Orchestrator schedules database module work ...

# If database module delivers:
dynamic_plan.mark_delivered(requirement_id)

# If database module FAILS to deliver:
dynamic_plan.report_discrepancy(
    module="database",
    expected="get_user() returns User object",
    actual="get_user() not implemented",
    severity="critical"
)

# Orchestrator returns to database module with new requirement
# Discrepancy MUST be resolved before project is complete
```

---

## File Formats

### Requirements File (`.beyond_ralph_requirements.json`)

```json
{
  "requirements": [
    {
      "id": "req-a1b2c3d4",
      "from_module": "auth",
      "to_module": "database",
      "technical_spec": "Provide get_user(id: str) -> User function",
      "status": "pending",
      "created_at": "2026-02-02T00:49:45",
      "delivered_at": null,
      "failure_reason": null
    }
  ]
}
```

### Discrepancies File (`.beyond_ralph_discrepancies.json`)

```json
{
  "discrepancies": [
    {
      "id": "disc-e5f6g7h8",
      "module": "database",
      "expected": "get_user() returns User object",
      "actual": "get_user() not implemented",
      "severity": "critical",
      "reported_at": "2026-02-02T01:00:00",
      "resolved": false,
      "resolution": null
    }
  ]
}
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 9 (Knowledge) | Storing requirement decisions |
| Module 10 (Records) | Linking to task checkboxes |
| Module 16 (Utils) | UUID generation, file I/O |

---

## Error Handling

```python
class DynamicPlanError(BeyondRalphError):
    """Dynamic plan errors."""

class RequirementNotFoundError(DynamicPlanError):
    """Requirement not found."""

class DiscrepancyNotFoundError(DynamicPlanError):
    """Discrepancy not found."""

class CircularDependencyError(DynamicPlanError):
    """Circular requirement dependency detected."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | CRUD operations, requirement tracking |
| Integration tests | Multi-module requirement flow |
| Live tests | Project plan updates |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
