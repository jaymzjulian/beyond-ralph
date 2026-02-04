# GitHub Integration Module Tasks

## Overview

The github-integration module provides PR workflows, issue tracking integration, and automated commit workflows. **THIS MODULE IS PLANNED BUT NOT YET STARTED.**

**Dependencies**: orchestrator, session, utils
**Required By**: PR workflows (optional)
**Location**: `src/beyond_ralph/integrations/github.py`
**Tests**: `tests/unit/test_github_integration.py`
**LOC**: 0 (not started)
**Priority**: LOW (optional for v1.0)

---

## Task: Implement GitHubManager Base Class

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Base GitHubManager class for GitHub API operations.

**Acceptance Criteria**:
1. `GitHubManager` class with repo detection
2. Support `GITHUB_TOKEN` environment variable
3. Auto-detect repo from git remote
4. `_run_git()` helper for git commands
5. `_run_gh()` helper for gh CLI commands
6. Handle authentication errors gracefully

**Data Classes Required**:
```python
@dataclass
class PullRequest:
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
    number: int
    title: str
    body: str
    labels: list[str]
    url: str
    assignees: list[str]
```

**Tests**: tests/unit/test_github_integration.py::TestGitHubManager
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/github-integration/evidence/base-class/

---

## Task: Implement PR Creation Workflow

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Automated PR creation for completed tasks.

**Acceptance Criteria**:
1. `create_pr(title, body, branch, base, draft)` method
2. Auto-generate PR title from task context
3. Auto-generate PR description with:
   - Summary of changes
   - Test results summary
   - Checklist status (6 checkboxes)
4. Use `gh pr create` CLI
5. Support draft PRs
6. Return PullRequest dataclass with URL

**PR Body Template**:
```markdown
## Summary
{summary}

## Changes
{change_list}

## Test Results
- Unit tests: {unit_status}
- Integration tests: {integration_status}

## Checklist
- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

*Created by Beyond Ralph session {session_id}*
```

**Tests**: tests/unit/test_github_integration.py::TestPRCreation
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/github-integration/evidence/pr-creation/

---

## Task: Implement Blocker Issue Creation

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Auto-create GitHub issues when Beyond Ralph is blocked.

**Acceptance Criteria**:
1. `create_issue(title, body, labels, assignees)` method
2. `create_blocker_issue()` specialized method for blockers
3. Include blocker context:
   - Current phase and module
   - Problem description
   - Attempted solutions
   - Required user action
4. Auto-label with ["blocked", "beyond-ralph"]
5. Return Issue dataclass with URL
6. Notify user via notifications module

**Blocker Issue Template**:
```markdown
## Context
Beyond Ralph is blocked during {phase} ({module}).

## Problem
{problem_description}

## Attempted Solutions
{attempted_solutions_list}

## Required Action
{required_action}

---
*This issue was created automatically by Beyond Ralph.*
*Session: {session_id}*
```

**Tests**: tests/unit/test_github_integration.py::TestBlockerIssues
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/github-integration/evidence/blocker-issues/

---

## Task: Implement Git Push Operations

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Commit and push changes to GitHub.

**Acceptance Criteria**:
1. `push_branch(branch, message, force)` method
2. Create branch if not exists
3. Stage changes with `git add`
4. Commit with conventional commit format
5. Push to origin
6. Handle merge conflicts gracefully
7. `atomic_commit(files, message, scope)` for targeted commits

**Commit Message Format**:
```
feat(scope): description

Co-Authored-By: Beyond Ralph <noreply@beyond-ralph.dev>
```

**Tests**: tests/unit/test_github_integration.py::TestGitPush
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/github-integration/evidence/git-push/

---

## Task: Implement Webhook Notifications

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Send webhook notifications for CI/CD integration.

**Acceptance Criteria**:
1. `send_webhook(event, payload)` method
2. `configure_webhooks(webhooks)` for setup
3. Support webhook events:
   - `phase_start` - Phase begins
   - `phase_complete` - Phase ends
   - `blocked` - Awaiting user input
   - `error` - Critical error
   - `complete` - Project done
4. Sign payloads with secret if configured
5. Retry on failure (3 attempts with backoff)
6. Handle rate limiting

**Webhook Payload Format**:
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

**Tests**: tests/unit/test_github_integration.py::TestWebhooks
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/github-integration/evidence/webhooks/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| GitHubManager Base Class | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| PR Creation Workflow | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Blocker Issue Creation | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Git Push Operations | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Webhook Notifications | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |

**Overall Progress**: 0/5 implemented, 0/5 mock tested, 0/5 integration tested, 0/5 live tested, 0/5 spec compliant

---

## Implementation Priority

This module is **OPTIONAL for v1.0** but provides significant value for:
- Automated PR workflows
- Blocker visibility via GitHub Issues
- CI/CD integration via webhooks

**Recommended Implementation Order**:
1. GitHubManager Base Class (foundation)
2. Git Push Operations (needed for PRs)
3. PR Creation Workflow (primary use case)
4. Blocker Issue Creation (user visibility)
5. Webhook Notifications (CI/CD integration)

**Dependencies**:
- Requires `gh` CLI installed
- Requires `GITHUB_TOKEN` for API access
- Requires git with configured remote
