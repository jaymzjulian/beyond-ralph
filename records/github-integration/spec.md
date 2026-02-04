# Module 13: GitHub Integration - Specification

> Git Operations: Push, PR creation, issue tracking, and webhooks.

---

## Overview

The GitHub Integration module handles all interactions with GitHub for version control, pull requests, issues, and CI/CD webhook notifications. Per interview decision, Beyond Ralph can create issues automatically when blocked.

**Key Principle**: Integrate seamlessly with GitHub workflow; auto-create issues for blockers.

---

## Location

`src/beyond_ralph/integrations/github.py`

---

## Components

### 13.1 GitHub Manager

**Purpose**: Manage GitHub operations including push, PR, issue, and webhook functionality.

**Interface**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import subprocess

@dataclass
class PullRequest:
    """GitHub Pull Request."""
    number: int
    title: str
    body: str
    branch: str
    base: str
    url: str
    status: str
    created_at: datetime

@dataclass
class Issue:
    """GitHub Issue."""
    number: int
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    url: str = ""
    assignees: list[str] = field(default_factory=list)

@dataclass
class WebhookConfig:
    """Webhook configuration."""
    url: str
    events: list[str]
    secret: Optional[str] = None

class GitHubManager:
    """Manages GitHub integration."""

    def __init__(
        self,
        repo: Optional[str] = None,
        token: Optional[str] = None
    ) -> None:
        """Initialize GitHub manager.

        Args:
            repo: Repository in format 'owner/repo'. Auto-detect if None.
            token: GitHub token. Uses GITHUB_TOKEN env var if not provided.
        """

    async def create_pr(
        self,
        title: str,
        body: str,
        branch: str,
        base: str = "main",
        draft: bool = False
    ) -> PullRequest:
        """Create a pull request.

        Args:
            title: PR title.
            body: PR description (Markdown).
            branch: Source branch.
            base: Target branch.
            draft: Create as draft PR.

        Returns:
            Created PullRequest object.

        Uses `gh pr create` CLI for simplicity.
        """

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None
    ) -> Issue:
        """Create a GitHub issue.

        Args:
            title: Issue title.
            body: Issue body (Markdown).
            labels: Labels to apply.
            assignees: Users to assign.

        Returns:
            Created Issue object.

        Used for:
            - Blockers that need user attention
            - Dependency issues
            - Configuration problems
        """

    async def push_branch(
        self,
        branch: str,
        message: str,
        force: bool = False
    ) -> None:
        """Commit and push current changes to branch.

        Args:
            branch: Branch name.
            message: Commit message.
            force: Force push (use carefully).

        Flow:
            1. git checkout -b {branch} (if not exists)
            2. git add -A
            3. git commit -m "{message}"
            4. git push origin {branch}
        """

    async def send_webhook(
        self,
        event: str,
        payload: dict
    ) -> bool:
        """Send webhook notification.

        Args:
            event: Event type (e.g., "phase_complete", "blocked").
            payload: Event data.

        Returns:
            True if successfully sent.

        Used for CI/CD integration.
        """

    def configure_webhooks(
        self,
        webhooks: list[WebhookConfig]
    ) -> None:
        """Configure outgoing webhooks.

        Args:
            webhooks: List of webhook configurations.
        """

    def _run_git(self, *args: str) -> str:
        """Run git command and return output."""

    def _run_gh(self, *args: str) -> str:
        """Run GitHub CLI command and return output."""

    def _detect_repo(self) -> str:
        """Detect repository from git remote."""
```

---

## Auto-Issue Creation

When Beyond Ralph is blocked, it creates issues automatically:

### Blocker Issue Template

```python
BLOCKER_TEMPLATE = """
## Context
Beyond Ralph is blocked during {phase} ({module}).

## Problem
{problem_description}

## Attempted Solutions
{attempted_solutions}

## Required Action
{required_action}

---
*This issue was created automatically by Beyond Ralph.*
*Session: {session_id}*
"""

async def create_blocker_issue(
    phase: str,
    module: str,
    problem: str,
    attempted: list[str],
    action: str,
    session_id: str
) -> Issue:
    """Create a blocker issue."""
    body = BLOCKER_TEMPLATE.format(
        phase=phase,
        module=module,
        problem_description=problem,
        attempted_solutions="\n".join(f"- {a}" for a in attempted),
        required_action=action,
        session_id=session_id
    )
    return await github.create_issue(
        title=f"[BLOCKED] {problem[:50]}...",
        body=body,
        labels=["blocked", "beyond-ralph"]
    )
```

---

## Webhook Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `phase_start` | Phase begins | phase, module, timestamp |
| `phase_complete` | Phase ends | phase, result, duration |
| `blocked` | Awaiting user | reason, module, context |
| `error` | Critical error | error, traceback, context |
| `complete` | Project done | summary, stats |

### Webhook Payload Format

```json
{
  "event": "phase_complete",
  "project": "my-project",
  "session_id": "br-d35605c9",
  "timestamp": "2024-02-01T10:30:00Z",
  "data": {
    "phase": 3,
    "phase_name": "spec_creation",
    "result": "success",
    "duration_seconds": 120
  }
}
```

---

## Git Operations

### Atomic Commits

Per CLAUDE.md guidelines, commits are atomic:

```python
async def atomic_commit(
    files: list[str],
    message: str,
    scope: str
) -> None:
    """Create an atomic commit for specific files.

    Args:
        files: Files to include.
        message: Commit message (without type/scope).
        scope: Module scope (e.g., "orchestrator").

    Commit format: feat(scope): message
    """
    await self._run_git("add", *files)
    full_message = f"feat({scope}): {message}"
    await self._run_git("commit", "-m", full_message)
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 12 (Utils) | Logging, subprocess helpers |
| External: git | Version control |
| External: gh | GitHub CLI |

---

## Error Handling

```python
class GitHubError(BeyondRalphError):
    """GitHub-related errors."""

class GitHubAuthError(GitHubError):
    """Authentication failed."""

class GitHubRateLimitError(GitHubError):
    """Rate limit exceeded."""

class GitOperationError(GitHubError):
    """Git operation failed."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Git command generation, webhook formatting |
| Integration tests | Mock GitHub API calls |
| Live tests | Real GitHub operations (needs token) |

---

## Checkboxes

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
