"""GitHub Integration for Beyond Ralph.

Provides PR workflows, issue tracking, and git operations.
Uses subprocess to run git and gh CLI commands.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Base exception for GitHub integration errors."""

    pass


class AuthenticationError(GitHubError):
    """Raised when GitHub authentication fails."""

    pass


class GitCommandError(GitHubError):
    """Raised when a git command fails."""

    def __init__(self, message: str, returncode: int, stderr: str):
        """Initialize GitCommandError.

        Args:
            message: Error description.
            returncode: Exit code from command.
            stderr: Standard error output.
        """
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class PRStatus(Enum):
    """Pull request status."""

    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"


@dataclass
class PullRequest:
    """Represents a GitHub Pull Request."""

    number: int
    title: str
    body: str
    branch: str
    base: str
    url: str
    status: str
    created_at: datetime

    @classmethod
    def from_gh_output(cls, data: dict[str, Any]) -> PullRequest:
        """Create PullRequest from gh CLI JSON output.

        Args:
            data: Parsed JSON from gh CLI.

        Returns:
            PullRequest instance.
        """
        # Handle created_at parsing - gh CLI returns ISO format
        created_at_str = data.get("createdAt", "")
        if created_at_str:
            try:
                # Handle ISO format with Z timezone
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.now()
        else:
            created_at = datetime.now()

        # Determine status
        status = "open"
        if data.get("merged"):
            status = "merged"
        elif data.get("closed"):
            status = "closed"
        elif data.get("isDraft"):
            status = "draft"

        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body", ""),
            branch=data.get("headRefName", ""),
            base=data.get("baseRefName", ""),
            url=data.get("url", ""),
            status=status,
            created_at=created_at,
        )


@dataclass
class Issue:
    """Represents a GitHub Issue."""

    number: int
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    url: str = ""
    assignees: list[str] = field(default_factory=list)

    @classmethod
    def from_gh_output(cls, data: dict[str, Any]) -> Issue:
        """Create Issue from gh CLI JSON output.

        Args:
            data: Parsed JSON from gh CLI.

        Returns:
            Issue instance.
        """
        # Extract label names from label objects
        labels = [label.get("name", "") for label in data.get("labels", [])]

        # Extract assignee logins from assignee objects
        assignees = [assignee.get("login", "") for assignee in data.get("assignees", [])]

        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body", ""),
            labels=labels,
            url=data.get("url", ""),
            assignees=assignees,
        )


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""

    url: str
    secret: str | None = None
    events: list[str] = field(default_factory=list)

    def should_send(self, event: str) -> bool:
        """Check if this webhook should receive the event.

        Args:
            event: Event type name.

        Returns:
            True if webhook should receive event.
        """
        if not self.events:
            return True  # No filter = all events
        return event in self.events


class WebhookEvent(Enum):
    """Webhook event types."""

    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    BLOCKED = "blocked"
    ERROR = "error"
    COMPLETE = "complete"


class GitHubManager:
    """Manages GitHub operations via git and gh CLI."""

    def __init__(
        self,
        repo_path: str | None = None,
        token: str | None = None,
    ):
        """Initialize GitHubManager.

        Args:
            repo_path: Path to git repository. Defaults to current directory.
            token: GitHub token. Defaults to GITHUB_TOKEN env var.
        """
        self.repo_path = repo_path or os.getcwd()
        self._token = token or os.environ.get("GITHUB_TOKEN")
        self._repo_info: dict[str, str] | None = None
        self._webhooks: list[WebhookConfig] = []

    @property
    def token(self) -> str | None:
        """Get GitHub token."""
        return self._token

    @property
    def is_authenticated(self) -> bool:
        """Check if GitHub token is available."""
        return bool(self._token)

    def _run_git(
        self,
        args: list[str],
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command.

        Args:
            args: Command arguments (without 'git' prefix).
            check: Whether to raise on non-zero exit.
            capture_output: Whether to capture stdout/stderr.

        Returns:
            CompletedProcess result.

        Raises:
            GitCommandError: If command fails and check is True.
        """
        cmd = ["git", "-C", self.repo_path] + args

        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                timeout=120,
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error("Git command failed: %s", " ".join(cmd))
            logger.error("Stderr: %s", e.stderr)
            raise GitCommandError(
                f"Git command failed: {' '.join(args)}",
                e.returncode,
                e.stderr or "",
            ) from e
        except subprocess.TimeoutExpired as e:
            raise GitCommandError(
                f"Git command timed out: {' '.join(args)}",
                -1,
                "Command timed out",
            ) from e

    def _run_gh(
        self,
        args: list[str],
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run a gh CLI command.

        Args:
            args: Command arguments (without 'gh' prefix).
            check: Whether to raise on non-zero exit.
            capture_output: Whether to capture stdout/stderr.

        Returns:
            CompletedProcess result.

        Raises:
            GitCommandError: If command fails and check is True.
            AuthenticationError: If authentication fails.
        """
        cmd = ["gh"] + args

        # Set up environment with token if available
        env = os.environ.copy()
        if self._token:
            env["GH_TOKEN"] = self._token

        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                cwd=self.repo_path,
                env=env,
                timeout=120,
            )
            return result
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            logger.error("gh command failed: %s", " ".join(cmd))
            logger.error("Stderr: %s", stderr)

            # Check for auth errors
            if "authentication" in stderr.lower() or "login" in stderr.lower():
                raise AuthenticationError(
                    "GitHub authentication failed. Set GITHUB_TOKEN or run 'gh auth login'."
                ) from e

            raise GitCommandError(
                f"gh command failed: {' '.join(args)}",
                e.returncode,
                stderr,
            ) from e
        except subprocess.TimeoutExpired as e:
            raise GitCommandError(
                f"gh command timed out: {' '.join(args)}",
                -1,
                "Command timed out",
            ) from e
        except FileNotFoundError as e:
            raise GitCommandError(
                "gh CLI not found. Install with: https://cli.github.com/",
                -1,
                "gh not found",
            ) from e

    def detect_repo(self) -> dict[str, str]:
        """Detect GitHub repository from git remote.

        Returns:
            Dict with 'owner' and 'repo' keys.

        Raises:
            GitHubError: If repo cannot be detected.
        """
        if self._repo_info:
            return self._repo_info

        try:
            result = self._run_git(["remote", "get-url", "origin"])
            remote_url = result.stdout.strip()
        except GitCommandError as e:
            raise GitHubError("No git remote 'origin' found") from e

        # Parse remote URL
        # SSH format: git@github.com:owner/repo.git
        # HTTPS format: https://github.com/owner/repo.git
        ssh_match = re.match(r"git@github\.com:(.+)/(.+?)(?:\.git)?$", remote_url)
        https_match = re.match(r"https://github\.com/(.+)/(.+?)(?:\.git)?$", remote_url)

        if ssh_match:
            owner, repo = ssh_match.groups()
        elif https_match:
            owner, repo = https_match.groups()
        else:
            raise GitHubError(f"Could not parse GitHub URL: {remote_url}")

        self._repo_info = {"owner": owner, "repo": repo}
        return self._repo_info

    def get_current_branch(self) -> str:
        """Get current git branch name.

        Returns:
            Current branch name.
        """
        result = self._run_git(["branch", "--show-current"])
        return result.stdout.strip()

    def is_clean(self) -> bool:
        """Check if working tree is clean (no uncommitted changes).

        Returns:
            True if working tree is clean.
        """
        result = self._run_git(["status", "--porcelain"])
        return not result.stdout.strip()

    # =========================================================================
    # Pull Request Operations
    # =========================================================================

    def create_pr(
        self,
        title: str,
        body: str,
        branch: str | None = None,
        base: str = "main",
        draft: bool = False,
    ) -> PullRequest:
        """Create a new pull request.

        Args:
            title: PR title.
            body: PR description/body.
            branch: Head branch. Defaults to current branch.
            base: Base branch. Defaults to 'main'.
            draft: Whether to create as draft PR.

        Returns:
            PullRequest with created PR details.
        """
        if branch is None:
            branch = self.get_current_branch()

        args = [
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--head",
            branch,
            "--base",
            base,
        ]

        if draft:
            args.append("--draft")

        # Request JSON output
        args.extend(["--json", "number,title,body,headRefName,baseRefName,url,createdAt"])

        result = self._run_gh(args)

        # Parse JSON output
        data = json.loads(result.stdout)
        pr = PullRequest.from_gh_output(data)
        pr.status = "draft" if draft else "open"

        logger.info("Created PR #%d: %s", pr.number, pr.url)
        return pr

    def create_pr_from_task(
        self,
        summary: str,
        changes: list[str],
        unit_status: str = "Pending",
        integration_status: str = "Pending",
        checklist: dict[str, bool] | None = None,
        session_id: str = "",
        branch: str | None = None,
        base: str = "main",
        draft: bool = False,
    ) -> PullRequest:
        """Create a PR with auto-generated body from task context.

        Args:
            summary: Summary of changes.
            changes: List of change descriptions.
            unit_status: Unit test status string.
            integration_status: Integration test status string.
            checklist: Dict of checklist items to checked state.
            session_id: Beyond Ralph session ID.
            branch: Head branch. Defaults to current branch.
            base: Base branch. Defaults to 'main'.
            draft: Whether to create as draft PR.

        Returns:
            PullRequest with created PR details.
        """
        # Default checklist
        if checklist is None:
            checklist = {
                "Planned": True,
                "Implemented": True,
                "Mock tested": True,
                "Integration tested": False,
                "Live tested": False,
                "Spec compliant": False,
            }

        # Build change list
        change_list = (
            "\n".join(f"- {change}" for change in changes)
            if changes
            else "- No specific changes listed"
        )

        # Build checklist markdown
        checklist_md = "\n".join(
            f"- [{'x' if checked else ' '}] {item}" for item, checked in checklist.items()
        )

        # Generate title from summary (first line, truncated)
        title = summary.split("\n")[0][:70]
        if len(summary.split("\n")[0]) > 70:
            title = title[:67] + "..."

        # Build body using template
        body = f"""## Summary
{summary}

## Changes
{change_list}

## Test Results
- Unit tests: {unit_status}
- Integration tests: {integration_status}

## Checklist
{checklist_md}

*Created by Beyond Ralph session {session_id}*
"""

        return self.create_pr(
            title=title,
            body=body,
            branch=branch,
            base=base,
            draft=draft,
        )

    def get_pr(self, number: int) -> PullRequest:
        """Get pull request details.

        Args:
            number: PR number.

        Returns:
            PullRequest with PR details.
        """
        args = [
            "pr",
            "view",
            str(number),
            "--json",
            "number,title,body,headRefName,baseRefName,url,createdAt,merged,closed,isDraft",
        ]

        result = self._run_gh(args)
        data = json.loads(result.stdout)
        return PullRequest.from_gh_output(data)

    def list_prs(
        self,
        state: str = "open",
        limit: int = 30,
    ) -> list[PullRequest]:
        """List pull requests.

        Args:
            state: Filter by state (open, closed, merged, all).
            limit: Maximum number of PRs to return.

        Returns:
            List of PullRequest objects.
        """
        args = [
            "pr",
            "list",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,body,headRefName,baseRefName,url,createdAt,merged,closed,isDraft",
        ]

        result = self._run_gh(args)
        data = json.loads(result.stdout)
        return [PullRequest.from_gh_output(pr) for pr in data]

    # =========================================================================
    # Issue Operations
    # =========================================================================

    def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> Issue:
        """Create a new GitHub issue.

        Args:
            title: Issue title.
            body: Issue description/body.
            labels: List of label names.
            assignees: List of GitHub usernames to assign.

        Returns:
            Issue with created issue details.
        """
        args = [
            "issue",
            "create",
            "--title",
            title,
            "--body",
            body,
        ]

        if labels:
            for label in labels:
                args.extend(["--label", label])

        if assignees:
            for assignee in assignees:
                args.extend(["--assignee", assignee])

        # Request JSON output
        args.extend(["--json", "number,title,body,url,labels,assignees"])

        result = self._run_gh(args)
        data = json.loads(result.stdout)
        issue = Issue.from_gh_output(data)

        logger.info("Created issue #%d: %s", issue.number, issue.url)
        return issue

    def create_blocker_issue(
        self,
        phase: str,
        module: str,
        problem: str,
        attempted_solutions: list[str],
        required_action: str,
        session_id: str = "",
    ) -> Issue:
        """Create a blocker issue when Beyond Ralph is blocked.

        Args:
            phase: Current phase (e.g., "implementation").
            module: Current module being worked on.
            problem: Description of the problem.
            attempted_solutions: List of things tried.
            required_action: What user needs to do.
            session_id: Beyond Ralph session ID.

        Returns:
            Issue with created issue details.
        """
        # Format attempted solutions
        solutions_list = (
            "\n".join(f"- {solution}" for solution in attempted_solutions)
            if attempted_solutions
            else "- None yet"
        )

        title = f"[BLOCKED] {phase}: {module} - {problem[:40]}"

        body = f"""## Context
Beyond Ralph is blocked during **{phase}** ({module}).

## Problem
{problem}

## Attempted Solutions
{solutions_list}

## Required Action
{required_action}

---
*This issue was created automatically by Beyond Ralph.*
*Session: {session_id}*
"""

        return self.create_issue(
            title=title,
            body=body,
            labels=["blocked", "beyond-ralph"],
        )

    def get_issue(self, number: int) -> Issue:
        """Get issue details.

        Args:
            number: Issue number.

        Returns:
            Issue with issue details.
        """
        args = [
            "issue",
            "view",
            str(number),
            "--json",
            "number,title,body,url,labels,assignees",
        ]

        result = self._run_gh(args)
        data = json.loads(result.stdout)
        return Issue.from_gh_output(data)

    def close_issue(self, number: int, comment: str | None = None) -> bool:
        """Close an issue.

        Args:
            number: Issue number.
            comment: Optional comment to add before closing.

        Returns:
            True if successful.
        """
        if comment:
            self._run_gh(["issue", "comment", str(number), "--body", comment])

        self._run_gh(["issue", "close", str(number)])
        logger.info("Closed issue #%d", number)
        return True

    # =========================================================================
    # Git Push Operations
    # =========================================================================

    def create_branch(self, branch: str, base: str = "HEAD") -> bool:
        """Create a new branch.

        Args:
            branch: New branch name.
            base: Base to create from. Defaults to HEAD.

        Returns:
            True if successful.
        """
        self._run_git(["checkout", "-b", branch, base])
        logger.info("Created branch: %s", branch)
        return True

    def checkout_branch(self, branch: str, create: bool = False) -> bool:
        """Checkout a branch.

        Args:
            branch: Branch name.
            create: Whether to create if doesn't exist.

        Returns:
            True if successful.
        """
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)

        self._run_git(args)
        return True

    def branch_exists(self, branch: str, remote: bool = False) -> bool:
        """Check if a branch exists.

        Args:
            branch: Branch name.
            remote: Check remote branches.

        Returns:
            True if branch exists.
        """
        if remote:
            result = self._run_git(
                ["ls-remote", "--heads", "origin", branch],
                check=False,
            )
            return branch in result.stdout
        else:
            result = self._run_git(
                ["branch", "--list", branch],
                check=False,
            )
            return bool(result.stdout.strip())

    def stage_files(self, files: list[str] | None = None) -> bool:
        """Stage files for commit.

        Args:
            files: List of file paths. None = all changes.

        Returns:
            True if successful.
        """
        if files:
            self._run_git(["add"] + files)
        else:
            self._run_git(["add", "-A"])
        return True

    def commit(
        self,
        message: str,
        scope: str | None = None,
        co_author: str = "Beyond Ralph <noreply@beyond-ralph.dev>",
    ) -> str:
        """Create a commit with conventional commit format.

        Args:
            message: Commit message (type: description).
            scope: Optional scope to add.
            co_author: Co-author to add. Set to empty string to skip.

        Returns:
            Commit SHA.
        """
        # Format message with scope if provided
        if scope and "(" not in message.split(":")[0]:
            parts = message.split(":", 1)
            if len(parts) == 2:
                message = f"{parts[0]}({scope}):{parts[1]}"

        # Add co-author
        if co_author:
            message = f"{message}\n\nCo-Authored-By: {co_author}"

        self._run_git(["commit", "-m", message])

        # Get commit SHA
        result = self._run_git(["rev-parse", "HEAD"])
        sha = result.stdout.strip()

        logger.info("Created commit: %s", sha[:8])
        return sha

    def push_branch(
        self,
        branch: str | None = None,
        force: bool = False,
        set_upstream: bool = True,
    ) -> bool:
        """Push branch to remote.

        Args:
            branch: Branch name. Defaults to current branch.
            force: Force push. Use with caution.
            set_upstream: Set upstream tracking.

        Returns:
            True if successful.
        """
        if branch is None:
            branch = self.get_current_branch()

        args = ["push"]

        if force:
            args.append("--force-with-lease")

        if set_upstream:
            args.extend(["--set-upstream", "origin", branch])
        else:
            args.extend(["origin", branch])

        self._run_git(args)
        logger.info("Pushed branch: %s", branch)
        return True

    def atomic_commit(
        self,
        files: list[str],
        message: str,
        scope: str | None = None,
    ) -> str:
        """Stage specific files and commit atomically.

        Args:
            files: List of file paths to commit.
            message: Commit message.
            scope: Optional scope for conventional commit.

        Returns:
            Commit SHA.
        """
        self.stage_files(files)
        return self.commit(message, scope)

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes.

        Returns:
            True if there are uncommitted changes.
        """
        return not self.is_clean()

    def get_changed_files(self, staged_only: bool = False) -> list[str]:
        """Get list of changed files.

        Args:
            staged_only: Only return staged files.

        Returns:
            List of changed file paths.
        """
        if staged_only:
            result = self._run_git(["diff", "--staged", "--name-only"])
        else:
            result = self._run_git(["status", "--porcelain"])

        if staged_only:
            return [f for f in result.stdout.strip().split("\n") if f]
        else:
            # Parse porcelain output format: XY PATH
            # X = index status, Y = worktree status (2 chars)
            # Then one space, then filename
            # IMPORTANT: Don't strip() the full output - it removes leading space from first line
            files = []
            for line in result.stdout.rstrip("\n").split("\n"):
                if line and len(line) > 3:
                    # Handle renamed files (old -> new)
                    # Format: XY old_path -> new_path
                    if " -> " in line:
                        # Get the new path after the arrow
                        path_part = line[3:]
                        files.append(path_part.split(" -> ")[1].strip())
                    else:
                        # Standard format: XY PATH (starts at position 3)
                        files.append(line[3:].strip())
            return files

    # =========================================================================
    # Webhook Operations
    # =========================================================================

    def configure_webhooks(self, webhooks: list[dict[str, Any]]) -> None:
        """Configure webhook endpoints.

        Args:
            webhooks: List of webhook configurations with url, secret, events.
        """
        self._webhooks = [
            WebhookConfig(
                url=w["url"],
                secret=w.get("secret"),
                events=w.get("events", []),
            )
            for w in webhooks
        ]
        logger.info("Configured %d webhooks", len(self._webhooks))

    async def send_webhook(
        self,
        event: str,
        payload: dict[str, Any],
        project: str = "",
        session_id: str = "",
    ) -> dict[str, bool]:
        """Send webhook notification to all configured endpoints.

        Args:
            event: Event type (phase_start, phase_complete, blocked, error, complete).
            payload: Event-specific data.
            project: Project name.
            session_id: Beyond Ralph session ID.

        Returns:
            Dict mapping webhook URLs to success status.
        """
        results: dict[str, bool] = {}

        # Build webhook payload
        webhook_payload = {
            "event": event,
            "project": project,
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "data": payload,
        }

        async with httpx.AsyncClient() as client:
            for webhook in self._webhooks:
                if not webhook.should_send(event):
                    continue

                success = await self._send_single_webhook(client, webhook, webhook_payload)
                results[webhook.url] = success

        return results

    async def _send_single_webhook(
        self,
        client: httpx.AsyncClient,
        webhook: WebhookConfig,
        payload: dict[str, Any],
        max_retries: int = 3,
    ) -> bool:
        """Send webhook to single endpoint with retries.

        Args:
            client: HTTP client.
            webhook: Webhook configuration.
            payload: Payload to send.
            max_retries: Maximum retry attempts.

        Returns:
            True if sent successfully.
        """
        import asyncio

        headers = {"Content-Type": "application/json"}

        # Sign payload if secret configured
        if webhook.secret:
            payload_bytes = json.dumps(payload).encode()
            signature = hmac.new(
                webhook.secret.encode(),
                payload_bytes,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Signature-256"] = f"sha256={signature}"

        for attempt in range(max_retries):
            try:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning("Webhook rate limited, waiting %ds", retry_after)
                    await asyncio.sleep(min(retry_after, 120))
                    continue

                if response.status_code in (200, 201, 202, 204):
                    logger.debug("Webhook sent: %s", webhook.url)
                    return True
                else:
                    logger.warning(
                        "Webhook failed: %s (status %d)",
                        webhook.url,
                        response.status_code,
                    )

            except Exception as e:
                logger.error("Webhook error: %s - %s", webhook.url, e)

            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2**attempt) + (attempt * 0.1)
                await asyncio.sleep(wait_time)

        return False

    async def notify_phase_start(
        self,
        phase: int,
        phase_name: str,
        project: str = "",
        session_id: str = "",
    ) -> dict[str, bool]:
        """Send phase_start webhook.

        Args:
            phase: Phase number.
            phase_name: Phase name.
            project: Project name.
            session_id: Session ID.

        Returns:
            Results dict.
        """
        return await self.send_webhook(
            event=WebhookEvent.PHASE_START.value,
            payload={
                "phase": phase,
                "phase_name": phase_name,
            },
            project=project,
            session_id=session_id,
        )

    async def notify_phase_complete(
        self,
        phase: int,
        phase_name: str,
        result: str,
        duration_seconds: float,
        project: str = "",
        session_id: str = "",
    ) -> dict[str, bool]:
        """Send phase_complete webhook.

        Args:
            phase: Phase number.
            phase_name: Phase name.
            result: Result (success, failure, etc).
            duration_seconds: Phase duration.
            project: Project name.
            session_id: Session ID.

        Returns:
            Results dict.
        """
        return await self.send_webhook(
            event=WebhookEvent.PHASE_COMPLETE.value,
            payload={
                "phase": phase,
                "phase_name": phase_name,
                "result": result,
                "duration_seconds": duration_seconds,
            },
            project=project,
            session_id=session_id,
        )

    async def notify_blocked(
        self,
        reason: str,
        phase: int | None = None,
        project: str = "",
        session_id: str = "",
    ) -> dict[str, bool]:
        """Send blocked webhook.

        Args:
            reason: Reason for blockage.
            phase: Current phase number.
            project: Project name.
            session_id: Session ID.

        Returns:
            Results dict.
        """
        return await self.send_webhook(
            event=WebhookEvent.BLOCKED.value,
            payload={
                "reason": reason,
                "phase": phase,
            },
            project=project,
            session_id=session_id,
        )

    async def notify_error(
        self,
        error: str,
        phase: int | None = None,
        project: str = "",
        session_id: str = "",
    ) -> dict[str, bool]:
        """Send error webhook.

        Args:
            error: Error description.
            phase: Current phase number.
            project: Project name.
            session_id: Session ID.

        Returns:
            Results dict.
        """
        return await self.send_webhook(
            event=WebhookEvent.ERROR.value,
            payload={
                "error": error,
                "phase": phase,
            },
            project=project,
            session_id=session_id,
        )

    async def notify_complete(
        self,
        summary: str,
        total_duration_seconds: float,
        project: str = "",
        session_id: str = "",
    ) -> dict[str, bool]:
        """Send complete webhook.

        Args:
            summary: Completion summary.
            total_duration_seconds: Total duration.
            project: Project name.
            session_id: Session ID.

        Returns:
            Results dict.
        """
        return await self.send_webhook(
            event=WebhookEvent.COMPLETE.value,
            payload={
                "summary": summary,
                "total_duration_seconds": total_duration_seconds,
            },
            project=project,
            session_id=session_id,
        )


# Convenience function for quick access
def get_github_manager(
    repo_path: str | None = None,
    token: str | None = None,
) -> GitHubManager:
    """Get a GitHubManager instance.

    Args:
        repo_path: Path to git repository.
        token: GitHub token.

    Returns:
        GitHubManager instance.
    """
    return GitHubManager(repo_path=repo_path, token=token)
