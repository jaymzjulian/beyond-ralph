"""Live tests for GitHub integration module.

These tests require:
1. GITHUB_TOKEN environment variable set
2. gh CLI installed and authenticated
3. Being run in the beyond-ralph repository

Run with: BEYOND_RALPH_LIVE_TESTS=1 uv run pytest tests/live/test_github_live.py -v -s
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

# Skip if not in the right environment
pytestmark = pytest.mark.skipif(
    os.environ.get("BEYOND_RALPH_LIVE_TESTS") != "1",
    reason="Live tests require BEYOND_RALPH_LIVE_TESTS=1",
)


def run_command(cmd: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """Run a shell command."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", 1


def is_gh_authenticated() -> bool:
    """Check if gh CLI is authenticated."""
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0 or "Logged in" in result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class TestGitHubEnvironment:
    """Test GitHub environment setup."""

    def test_gh_cli_installed(self) -> None:
        """Verify gh CLI is installed."""
        import shutil
        gh_path = shutil.which("gh")
        if gh_path:
            stdout, stderr, returncode = run_command(["gh", "--version"])
            assert returncode == 0
            print(f"gh CLI: {stdout.strip().split(chr(10))[0]}")
        else:
            pytest.skip("gh CLI not installed")

    def test_gh_cli_authenticated(self) -> None:
        """Verify gh CLI is authenticated."""
        if not is_gh_authenticated():
            pytest.skip("gh CLI not authenticated - run 'gh auth login' to enable")

    def test_in_git_repository(self) -> None:
        """Verify we're in a git repository."""
        stdout, stderr, returncode = run_command(["git", "rev-parse", "--git-dir"])
        assert returncode == 0
        assert ".git" in stdout
        print("In a valid git repository")

    def test_git_remote_github(self) -> None:
        """Verify git remote points to GitHub."""
        stdout, stderr, returncode = run_command(["git", "remote", "-v"])
        assert returncode == 0
        assert "github.com" in stdout or "github:" in stdout
        print("Git remote points to GitHub")


class TestGitHubManagerLive:
    """Live tests for GitHubManager class."""

    def test_manager_instantiation(self) -> None:
        """Test GitHubManager can be instantiated."""
        from beyond_ralph.integrations.github import GitHubManager

        manager = GitHubManager()
        assert manager is not None
        assert manager.repo_path is not None
        print(f"GitHubManager instantiated at {manager.repo_path}")

    def test_detect_repo(self) -> None:
        """Test repository detection."""
        from beyond_ralph.integrations.github import GitHubManager

        manager = GitHubManager()

        # detect_repo returns a dict with owner/repo info
        repo_info = manager.detect_repo()
        assert repo_info is not None
        print(f"Detected repo info: {repo_info}")

    def test_git_operations(self) -> None:
        """Test git operations through manager."""
        from beyond_ralph.integrations.github import GitHubManager

        manager = GitHubManager()

        # Test getting current branch
        branch = manager.get_current_branch()
        assert branch is not None
        print(f"Current branch: {branch}")

        # Test checking for uncommitted changes
        has_changes = manager.has_uncommitted_changes()
        print(f"Has uncommitted changes: {has_changes}")

    def test_gh_authenticated_operations(self) -> None:
        """Test gh CLI operations (requires authentication)."""
        if not is_gh_authenticated():
            pytest.skip("gh CLI not authenticated")

        from beyond_ralph.integrations.github import GitHubManager

        manager = GitHubManager()

        # Test listing PRs (requires gh auth)
        prs = manager.list_prs(limit=5)
        print(f"Found {len(prs)} PRs")


class TestPROperationsLive:
    """Live tests for PR operations (read-only)."""

    def test_list_prs_gh(self) -> None:
        """Test listing pull requests via gh CLI."""
        if not is_gh_authenticated():
            pytest.skip("gh CLI not authenticated")

        stdout, stderr, returncode = run_command(
            ["gh", "pr", "list", "--json", "number,title,state", "--limit", "5"]
        )
        assert returncode == 0
        print(f"PR list: {stdout[:200]}...")

    def test_get_branch_info(self) -> None:
        """Test getting current branch info."""
        stdout, stderr, returncode = run_command(["git", "branch", "--show-current"])
        assert returncode == 0
        branch = stdout.strip()
        print(f"Current branch: {branch}")


class TestIssueOperationsLive:
    """Live tests for issue operations (read-only)."""

    def test_list_issues_gh(self) -> None:
        """Test listing issues via gh CLI."""
        if not is_gh_authenticated():
            pytest.skip("gh CLI not authenticated")

        stdout, stderr, returncode = run_command(
            ["gh", "issue", "list", "--json", "number,title,state", "--limit", "5"]
        )
        assert returncode == 0
        print(f"Issue list: {stdout[:200]}...")


class TestGitOperationsLive:
    """Live tests for git operations (read-only)."""

    def test_git_log(self) -> None:
        """Test getting git log."""
        stdout, stderr, returncode = run_command(
            ["git", "log", "--oneline", "-5"]
        )
        assert returncode == 0
        commits = stdout.strip().split("\n")
        assert len(commits) >= 1
        print(f"Recent commits: {commits[0][:50]}...")

    def test_git_diff(self) -> None:
        """Test getting git diff."""
        stdout, stderr, returncode = run_command(["git", "diff", "--stat"])
        assert returncode == 0
        print(f"Git diff stat: {len(stdout.splitlines())} lines changed")


class TestWebhookStructure:
    """Test webhook data structures."""

    def test_webhook_config_structure(self) -> None:
        """Test WebhookConfig can be created."""
        from beyond_ralph.integrations.github import WebhookConfig

        config = WebhookConfig(
            url="https://example.com/webhook",
            secret="test-secret",
            events=["phase_complete", "blocked"],
        )
        assert config.url == "https://example.com/webhook"
        assert config.secret == "test-secret"
        assert len(config.events) == 2
        print("WebhookConfig structure works")

    def test_webhook_event_structure(self) -> None:
        """Test WebhookEvent enum values."""
        from beyond_ralph.integrations.github import WebhookEvent

        # WebhookEvent is an enum of event types
        assert WebhookEvent.PHASE_START.value == "phase_start"
        assert WebhookEvent.PHASE_COMPLETE.value == "phase_complete"
        assert WebhookEvent.BLOCKED.value == "blocked"
        assert WebhookEvent.ERROR.value == "error"
        assert WebhookEvent.COMPLETE.value == "complete"
        print("WebhookEvent enum has all expected values")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
