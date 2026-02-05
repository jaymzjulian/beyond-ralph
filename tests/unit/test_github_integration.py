"""Tests for GitHub integration module."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.integrations.github import (
    AuthenticationError,
    GitCommandError,
    GitHubError,
    GitHubManager,
    Issue,
    PRStatus,
    PullRequest,
    WebhookConfig,
    WebhookEvent,
    get_github_manager,
)


class TestPRStatus:
    """Tests for PRStatus enum."""

    def test_status_values(self):
        """Test all PR status values exist."""
        assert PRStatus.OPEN.value == "open"
        assert PRStatus.CLOSED.value == "closed"
        assert PRStatus.MERGED.value == "merged"
        assert PRStatus.DRAFT.value == "draft"


class TestPullRequest:
    """Tests for PullRequest dataclass."""

    def test_creation(self):
        """Test creating PullRequest directly."""
        now = datetime.now()
        pr = PullRequest(
            number=123,
            title="Test PR",
            body="PR body",
            branch="feature/test",
            base="main",
            url="https://github.com/owner/repo/pull/123",
            status="open",
            created_at=now,
        )

        assert pr.number == 123
        assert pr.title == "Test PR"
        assert pr.body == "PR body"
        assert pr.branch == "feature/test"
        assert pr.base == "main"
        assert pr.status == "open"
        assert pr.created_at == now

    def test_from_gh_output(self):
        """Test creating PullRequest from gh CLI JSON."""
        data = {
            "number": 42,
            "title": "Add feature",
            "body": "This adds a feature",
            "headRefName": "feature/add-feature",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/42",
            "createdAt": "2024-01-15T10:30:00Z",
            "merged": False,
            "closed": False,
            "isDraft": False,
        }

        pr = PullRequest.from_gh_output(data)

        assert pr.number == 42
        assert pr.title == "Add feature"
        assert pr.body == "This adds a feature"
        assert pr.branch == "feature/add-feature"
        assert pr.base == "main"
        assert pr.status == "open"

    def test_from_gh_output_merged(self):
        """Test creating merged PullRequest from gh output."""
        data = {
            "number": 50,
            "title": "Merged PR",
            "body": "",
            "headRefName": "feature/merged",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/50",
            "createdAt": "2024-01-10T08:00:00Z",
            "merged": True,
            "closed": True,
            "isDraft": False,
        }

        pr = PullRequest.from_gh_output(data)
        assert pr.status == "merged"

    def test_from_gh_output_closed(self):
        """Test creating closed PullRequest from gh output."""
        data = {
            "number": 51,
            "title": "Closed PR",
            "body": "",
            "headRefName": "feature/closed",
            "baseRefName": "main",
            "url": "",
            "createdAt": "",
            "merged": False,
            "closed": True,
            "isDraft": False,
        }

        pr = PullRequest.from_gh_output(data)
        assert pr.status == "closed"

    def test_from_gh_output_draft(self):
        """Test creating draft PullRequest from gh output."""
        data = {
            "number": 52,
            "title": "Draft PR",
            "body": "",
            "headRefName": "feature/draft",
            "baseRefName": "main",
            "url": "",
            "createdAt": "",
            "merged": False,
            "closed": False,
            "isDraft": True,
        }

        pr = PullRequest.from_gh_output(data)
        assert pr.status == "draft"

    def test_from_gh_output_invalid_date(self):
        """Test handling invalid date in gh output."""
        data = {
            "number": 1,
            "title": "Test",
            "body": "",
            "headRefName": "test",
            "baseRefName": "main",
            "url": "",
            "createdAt": "invalid-date",
            "merged": False,
            "closed": False,
            "isDraft": False,
        }

        pr = PullRequest.from_gh_output(data)
        # Should not crash, uses current time as fallback
        assert pr.created_at is not None


class TestIssue:
    """Tests for Issue dataclass."""

    def test_creation(self):
        """Test creating Issue directly."""
        issue = Issue(
            number=99,
            title="Bug report",
            body="Something is broken",
            labels=["bug", "urgent"],
            url="https://github.com/owner/repo/issues/99",
            assignees=["user1", "user2"],
        )

        assert issue.number == 99
        assert issue.title == "Bug report"
        assert issue.labels == ["bug", "urgent"]
        assert issue.assignees == ["user1", "user2"]

    def test_creation_defaults(self):
        """Test Issue with default values."""
        issue = Issue(
            number=1,
            title="Test",
            body="Body",
        )

        assert issue.labels == []
        assert issue.assignees == []
        assert issue.url == ""

    def test_from_gh_output(self):
        """Test creating Issue from gh CLI JSON."""
        data = {
            "number": 77,
            "title": "Feature request",
            "body": "Please add this",
            "url": "https://github.com/owner/repo/issues/77",
            "labels": [
                {"name": "enhancement"},
                {"name": "good-first-issue"},
            ],
            "assignees": [
                {"login": "developer1"},
                {"login": "developer2"},
            ],
        }

        issue = Issue.from_gh_output(data)

        assert issue.number == 77
        assert issue.title == "Feature request"
        assert issue.labels == ["enhancement", "good-first-issue"]
        assert issue.assignees == ["developer1", "developer2"]

    def test_from_gh_output_empty_lists(self):
        """Test creating Issue from gh output with empty lists."""
        data = {
            "number": 1,
            "title": "Test",
            "body": "",
            "url": "",
            "labels": [],
            "assignees": [],
        }

        issue = Issue.from_gh_output(data)
        assert issue.labels == []
        assert issue.assignees == []


class TestWebhookConfig:
    """Tests for WebhookConfig dataclass."""

    def test_creation(self):
        """Test creating WebhookConfig."""
        config = WebhookConfig(
            url="https://webhook.example.com/hook",
            secret="mysecret",
            events=["phase_complete", "error"],
        )

        assert config.url == "https://webhook.example.com/hook"
        assert config.secret == "mysecret"
        assert config.events == ["phase_complete", "error"]

    def test_should_send_no_filter(self):
        """Test should_send with no event filter."""
        config = WebhookConfig(url="https://example.com", events=[])
        assert config.should_send("any_event") is True
        assert config.should_send("phase_start") is True

    def test_should_send_with_filter(self):
        """Test should_send with event filter."""
        config = WebhookConfig(
            url="https://example.com",
            events=["phase_complete", "complete"],
        )
        assert config.should_send("phase_complete") is True
        assert config.should_send("complete") is True
        assert config.should_send("error") is False
        assert config.should_send("blocked") is False


class TestWebhookEvent:
    """Tests for WebhookEvent enum."""

    def test_event_values(self):
        """Test all webhook event values exist."""
        assert WebhookEvent.PHASE_START.value == "phase_start"
        assert WebhookEvent.PHASE_COMPLETE.value == "phase_complete"
        assert WebhookEvent.BLOCKED.value == "blocked"
        assert WebhookEvent.ERROR.value == "error"
        assert WebhookEvent.COMPLETE.value == "complete"


class TestGitHubManager:
    """Tests for GitHubManager base class."""

    def test_creation_defaults(self):
        """Test manager creation with defaults."""
        manager = GitHubManager()

        assert manager.repo_path is not None
        assert manager._webhooks == []

    def test_creation_with_repo_path(self):
        """Test manager creation with repo path."""
        manager = GitHubManager(repo_path="/path/to/repo")
        assert manager.repo_path == "/path/to/repo"

    def test_creation_with_token(self):
        """Test manager creation with token."""
        manager = GitHubManager(token="ghp_testtoken123")
        assert manager.token == "ghp_testtoken123"
        assert manager.is_authenticated is True

    def test_creation_from_env(self, monkeypatch):
        """Test manager gets token from environment."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_envtoken456")
        manager = GitHubManager()
        assert manager.token == "ghp_envtoken456"

    def test_is_authenticated_without_token(self):
        """Test is_authenticated without token."""
        manager = GitHubManager(token=None)
        # Clear env var
        with patch.dict("os.environ", {}, clear=True):
            manager._token = None
            assert manager.is_authenticated is False


class TestGitHubManagerGitCommands:
    """Tests for GitHubManager git command execution."""

    def test_run_git_success(self):
        """Test successful git command."""
        manager = GitHubManager(repo_path="/tmp")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["git", "-C", "/tmp", "status"],
                returncode=0,
                stdout="On branch main",
                stderr="",
            )

            result = manager._run_git(["status"])

            assert result.stdout == "On branch main"
            mock_run.assert_called_once()

    def test_run_git_failure(self):
        """Test failed git command raises error."""
        manager = GitHubManager(repo_path="/tmp")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["git", "status"],
                stderr="fatal: not a git repository",
            )

            with pytest.raises(GitCommandError) as exc_info:
                manager._run_git(["status"])

            assert exc_info.value.returncode == 1
            assert "not a git repository" in exc_info.value.stderr

    def test_run_git_timeout(self):
        """Test git command timeout."""
        manager = GitHubManager(repo_path="/tmp")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["git", "fetch"],
                timeout=120,
            )

            with pytest.raises(GitCommandError) as exc_info:
                manager._run_git(["fetch"])

            assert "timed out" in str(exc_info.value).lower()

    def test_run_gh_success(self):
        """Test successful gh command."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["gh", "pr", "list"],
                returncode=0,
                stdout='[{"number": 1}]',
                stderr="",
            )

            result = manager._run_gh(["pr", "list"])

            assert "[" in result.stdout
            mock_run.assert_called_once()

    def test_run_gh_auth_error(self):
        """Test gh command with authentication error."""
        manager = GitHubManager(repo_path="/tmp")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["gh", "pr", "list"],
                stderr="authentication required: gh auth login",
            )

            with pytest.raises(AuthenticationError):
                manager._run_gh(["pr", "list"])

    def test_run_gh_not_found(self):
        """Test gh CLI not installed."""
        manager = GitHubManager(repo_path="/tmp")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")

            with pytest.raises(GitCommandError) as exc_info:
                manager._run_gh(["pr", "list"])

            assert "gh CLI not found" in str(exc_info.value)


class TestGitHubManagerRepoDetection:
    """Tests for repository detection."""

    def test_detect_repo_ssh(self):
        """Test detecting repo from SSH remote."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="git@github.com:myorg/myrepo.git",
                stderr="",
            )

            result = manager.detect_repo()

            assert result["owner"] == "myorg"
            assert result["repo"] == "myrepo"

    def test_detect_repo_https(self):
        """Test detecting repo from HTTPS remote."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="https://github.com/testowner/testrepo.git",
                stderr="",
            )

            result = manager.detect_repo()

            assert result["owner"] == "testowner"
            assert result["repo"] == "testrepo"

    def test_detect_repo_https_no_git_suffix(self):
        """Test detecting repo from HTTPS remote without .git."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="https://github.com/owner/repo",
                stderr="",
            )

            result = manager.detect_repo()

            assert result["owner"] == "owner"
            assert result["repo"] == "repo"

    def test_detect_repo_no_remote(self):
        """Test detecting repo when no remote exists."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.side_effect = GitCommandError("No remote", 1, "")

            with pytest.raises(GitHubError) as exc_info:
                manager.detect_repo()

            assert "No git remote" in str(exc_info.value)

    def test_detect_repo_invalid_url(self):
        """Test detecting repo with non-GitHub URL."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="git@gitlab.com:org/repo.git",
                stderr="",
            )

            with pytest.raises(GitHubError) as exc_info:
                manager.detect_repo()

            assert "Could not parse" in str(exc_info.value)

    def test_detect_repo_caches_result(self):
        """Test that detect_repo caches the result."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="git@github.com:owner/repo.git",
                stderr="",
            )

            result1 = manager.detect_repo()
            result2 = manager.detect_repo()

            assert result1 == result2
            mock_git.assert_called_once()  # Only called once

    def test_get_current_branch(self):
        """Test getting current branch."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="feature/test-branch\n",
                stderr="",
            )

            branch = manager.get_current_branch()
            assert branch == "feature/test-branch"

    def test_is_clean_true(self):
        """Test is_clean when working tree is clean."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            assert manager.is_clean() is True

    def test_is_clean_false(self):
        """Test is_clean when there are changes."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=" M file.py\n",
                stderr="",
            )

            assert manager.is_clean() is False


class TestPRCreation:
    """Tests for PR creation workflow."""

    def test_create_pr(self):
        """Test creating a PR."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "get_current_branch") as mock_branch:
            mock_branch.return_value = "feature/test"

            with patch.object(manager, "_run_gh") as mock_gh:
                mock_gh.return_value = subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=json.dumps({
                        "number": 123,
                        "title": "Test PR",
                        "body": "PR body",
                        "headRefName": "feature/test",
                        "baseRefName": "main",
                        "url": "https://github.com/owner/repo/pull/123",
                        "createdAt": "2024-01-15T10:00:00Z",
                    }),
                    stderr="",
                )

                pr = manager.create_pr(
                    title="Test PR",
                    body="PR body",
                    base="main",
                )

                assert pr.number == 123
                assert pr.title == "Test PR"
                assert pr.url == "https://github.com/owner/repo/pull/123"

    def test_create_pr_draft(self):
        """Test creating a draft PR."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "get_current_branch") as mock_branch:
            mock_branch.return_value = "feature/draft"

            with patch.object(manager, "_run_gh") as mock_gh:
                mock_gh.return_value = subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=json.dumps({
                        "number": 124,
                        "title": "Draft PR",
                        "body": "",
                        "headRefName": "feature/draft",
                        "baseRefName": "main",
                        "url": "",
                        "createdAt": "",
                    }),
                    stderr="",
                )

                pr = manager.create_pr(
                    title="Draft PR",
                    body="",
                    draft=True,
                )

                assert pr.status == "draft"
                # Verify --draft was passed
                call_args = mock_gh.call_args[0][0]
                assert "--draft" in call_args

    def test_create_pr_from_task(self):
        """Test creating PR from task context."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "create_pr") as mock_create:
            mock_create.return_value = PullRequest(
                number=125,
                title="Add auth module",
                body="...",
                branch="feature/auth",
                base="main",
                url="https://github.com/owner/repo/pull/125",
                status="open",
                created_at=datetime.now(),
            )

            pr = manager.create_pr_from_task(
                summary="Add authentication module with OAuth2 support",
                changes=["Added OAuth2 provider", "Added JWT validation"],
                unit_status="Passed (15/15)",
                integration_status="Pending",
                session_id="br-abc123",
            )

            assert pr.number == 125

            # Verify the body contains expected sections
            call_args = mock_create.call_args
            body = call_args.kwargs["body"]
            assert "## Summary" in body
            assert "## Changes" in body
            assert "OAuth2" in body
            assert "## Test Results" in body
            assert "Passed (15/15)" in body
            assert "## Checklist" in body
            assert "br-abc123" in body

    def test_get_pr(self):
        """Test getting PR details."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "_run_gh") as mock_gh:
            mock_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({
                    "number": 100,
                    "title": "Test",
                    "body": "Body",
                    "headRefName": "feature",
                    "baseRefName": "main",
                    "url": "https://github.com/owner/repo/pull/100",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "merged": False,
                    "closed": False,
                    "isDraft": False,
                }),
                stderr="",
            )

            pr = manager.get_pr(100)

            assert pr.number == 100
            mock_gh.assert_called_once()
            assert "100" in str(mock_gh.call_args)

    def test_list_prs(self):
        """Test listing PRs."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "_run_gh") as mock_gh:
            mock_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps([
                    {
                        "number": 1,
                        "title": "PR 1",
                        "body": "",
                        "headRefName": "f1",
                        "baseRefName": "main",
                        "url": "",
                        "createdAt": "",
                        "merged": False,
                        "closed": False,
                        "isDraft": False,
                    },
                    {
                        "number": 2,
                        "title": "PR 2",
                        "body": "",
                        "headRefName": "f2",
                        "baseRefName": "main",
                        "url": "",
                        "createdAt": "",
                        "merged": False,
                        "closed": False,
                        "isDraft": False,
                    },
                ]),
                stderr="",
            )

            prs = manager.list_prs(state="open", limit=10)

            assert len(prs) == 2
            assert prs[0].number == 1
            assert prs[1].number == 2


class TestBlockerIssues:
    """Tests for blocker issue creation."""

    def test_create_issue(self):
        """Test creating a basic issue."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "_run_gh") as mock_gh:
            mock_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({
                    "number": 50,
                    "title": "Bug report",
                    "body": "Description",
                    "url": "https://github.com/owner/repo/issues/50",
                    "labels": [{"name": "bug"}],
                    "assignees": [],
                }),
                stderr="",
            )

            issue = manager.create_issue(
                title="Bug report",
                body="Description",
                labels=["bug"],
            )

            assert issue.number == 50
            assert issue.title == "Bug report"

    def test_create_issue_with_assignees(self):
        """Test creating issue with assignees."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "_run_gh") as mock_gh:
            mock_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({
                    "number": 51,
                    "title": "Task",
                    "body": "",
                    "url": "",
                    "labels": [],
                    "assignees": [{"login": "user1"}],
                }),
                stderr="",
            )

            issue = manager.create_issue(
                title="Task",
                body="",
                assignees=["user1"],
            )

            assert issue.assignees == ["user1"]

            # Verify --assignee was passed
            call_args = mock_gh.call_args[0][0]
            assert "--assignee" in call_args

    def test_create_blocker_issue(self):
        """Test creating blocker issue."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "create_issue") as mock_create:
            mock_create.return_value = Issue(
                number=99,
                title="[BLOCKED] implementation: auth - Missing config",
                body="...",
                labels=["blocked", "beyond-ralph"],
                url="https://github.com/owner/repo/issues/99",
                assignees=[],
            )

            issue = manager.create_blocker_issue(
                phase="implementation",
                module="auth",
                problem="Missing configuration file",
                attempted_solutions=["Checked docs", "Searched codebase"],
                required_action="Please provide config.yaml",
                session_id="br-def456",
            )

            assert issue.number == 99

            # Verify body contains expected content
            call_kwargs = mock_create.call_args.kwargs
            body = call_kwargs["body"]
            assert "implementation" in body
            assert "auth" in body
            assert "Missing configuration file" in body
            assert "Checked docs" in body
            assert "Please provide config.yaml" in body
            assert "br-def456" in body

            # Verify labels
            assert call_kwargs["labels"] == ["blocked", "beyond-ralph"]

    def test_get_issue(self):
        """Test getting issue details."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "_run_gh") as mock_gh:
            mock_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({
                    "number": 75,
                    "title": "Issue",
                    "body": "Body",
                    "url": "",
                    "labels": [],
                    "assignees": [],
                }),
                stderr="",
            )

            issue = manager.get_issue(75)
            assert issue.number == 75

    def test_close_issue(self):
        """Test closing an issue."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "_run_gh") as mock_gh:
            mock_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.close_issue(75)
            assert result is True

    def test_close_issue_with_comment(self):
        """Test closing issue with comment."""
        manager = GitHubManager(repo_path="/tmp", token="ghp_test")

        with patch.object(manager, "_run_gh") as mock_gh:
            mock_gh.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.close_issue(75, comment="Fixed in PR #123")
            assert result is True

            # Should have been called twice (comment + close)
            assert mock_gh.call_count == 2


class TestGitPush:
    """Tests for git push operations."""

    def test_create_branch(self):
        """Test creating a new branch."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.create_branch("feature/new")
            assert result is True

            call_args = mock_git.call_args[0][0]
            assert "checkout" in call_args
            assert "-b" in call_args
            assert "feature/new" in call_args

    def test_checkout_branch(self):
        """Test checking out a branch."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.checkout_branch("main")
            assert result is True

    def test_checkout_branch_create(self):
        """Test checking out and creating a branch."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.checkout_branch("feature/new", create=True)
            assert result is True

            call_args = mock_git.call_args[0][0]
            assert "-b" in call_args

    def test_branch_exists_local(self):
        """Test checking if local branch exists."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="  main\n",
                stderr="",
            )

            assert manager.branch_exists("main") is True

    def test_branch_not_exists_local(self):
        """Test checking if local branch doesn't exist."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            assert manager.branch_exists("nonexistent") is False

    def test_branch_exists_remote(self):
        """Test checking if remote branch exists."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="abc123 refs/heads/feature\n",
                stderr="",
            )

            assert manager.branch_exists("feature", remote=True) is True

    def test_stage_files_specific(self):
        """Test staging specific files."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.stage_files(["file1.py", "file2.py"])
            assert result is True

            call_args = mock_git.call_args[0][0]
            assert "add" in call_args
            assert "file1.py" in call_args

    def test_stage_files_all(self):
        """Test staging all files."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.stage_files()
            assert result is True

            call_args = mock_git.call_args[0][0]
            assert "-A" in call_args

    def test_commit(self):
        """Test creating a commit."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="abc123def456\n",
                stderr="",
            )

            sha = manager.commit("feat: add feature")

            assert sha == "abc123def456"

    def test_commit_with_scope(self):
        """Test commit with scope added."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="def456\n",
                stderr="",
            )

            sha = manager.commit("feat: add feature", scope="auth")

            # Check that scope was added to message
            call_args = mock_git.call_args_list[0][0][0]
            commit_msg = call_args[call_args.index("-m") + 1]
            assert "feat(auth)" in commit_msg

    def test_commit_no_co_author(self):
        """Test commit without co-author."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="abc123\n",
                stderr="",
            )

            manager.commit("fix: bug", co_author="")

            call_args = mock_git.call_args_list[0][0][0]
            commit_msg = call_args[call_args.index("-m") + 1]
            assert "Co-Authored-By" not in commit_msg

    def test_push_branch(self):
        """Test pushing a branch."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "get_current_branch") as mock_branch:
            mock_branch.return_value = "feature/test"

            with patch.object(manager, "_run_git") as mock_git:
                mock_git.return_value = subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="",
                    stderr="",
                )

                result = manager.push_branch()
                assert result is True

                call_args = mock_git.call_args[0][0]
                assert "push" in call_args
                assert "--set-upstream" in call_args

    def test_push_branch_force(self):
        """Test force pushing a branch."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            )

            result = manager.push_branch(branch="feature", force=True)
            assert result is True

            call_args = mock_git.call_args[0][0]
            assert "--force-with-lease" in call_args

    def test_atomic_commit(self):
        """Test atomic commit (stage + commit)."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "stage_files") as mock_stage:
            with patch.object(manager, "commit") as mock_commit:
                mock_commit.return_value = "abc123"

                sha = manager.atomic_commit(
                    files=["src/module.py"],
                    message="feat: add module",
                    scope="core",
                )

                mock_stage.assert_called_once_with(["src/module.py"])
                mock_commit.assert_called_once_with("feat: add module", "core")
                assert sha == "abc123"

    def test_has_uncommitted_changes(self):
        """Test detecting uncommitted changes."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "is_clean") as mock_clean:
            mock_clean.return_value = False
            assert manager.has_uncommitted_changes() is True

            mock_clean.return_value = True
            assert manager.has_uncommitted_changes() is False

    def test_get_changed_files(self):
        """Test getting changed files."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=" M src/file1.py\n A src/file2.py\n",
                stderr="",
            )

            files = manager.get_changed_files()

            assert "src/file1.py" in files
            assert "src/file2.py" in files

    def test_get_changed_files_staged_only(self):
        """Test getting staged files only."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="src/staged.py\n",
                stderr="",
            )

            files = manager.get_changed_files(staged_only=True)

            assert files == ["src/staged.py"]
            call_args = mock_git.call_args[0][0]
            assert "--staged" in call_args

    def test_get_changed_files_renamed(self):
        """Test getting renamed files."""
        manager = GitHubManager(repo_path="/tmp")

        with patch.object(manager, "_run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="R  old.py -> new.py\n",
                stderr="",
            )

            files = manager.get_changed_files()

            # Should return the new filename
            assert "new.py" in files


class TestWebhooks:
    """Tests for webhook notifications."""

    def test_configure_webhooks(self):
        """Test configuring webhooks."""
        manager = GitHubManager()

        manager.configure_webhooks([
            {"url": "https://webhook1.example.com", "secret": "secret1"},
            {"url": "https://webhook2.example.com", "events": ["complete"]},
        ])

        assert len(manager._webhooks) == 2
        assert manager._webhooks[0].url == "https://webhook1.example.com"
        assert manager._webhooks[0].secret == "secret1"
        assert manager._webhooks[1].events == ["complete"]

    @pytest.mark.asyncio
    async def test_send_webhook(self):
        """Test sending webhook."""
        manager = GitHubManager()
        manager.configure_webhooks([
            {"url": "https://webhook.example.com"},
        ])

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            results = await manager.send_webhook(
                event="phase_complete",
                payload={"phase": 3},
                project="test-project",
                session_id="br-123",
            )

            assert "https://webhook.example.com" in results
            assert results["https://webhook.example.com"] is True

    @pytest.mark.asyncio
    async def test_send_webhook_with_signature(self):
        """Test webhook payload signing."""
        manager = GitHubManager()
        manager.configure_webhooks([
            {"url": "https://secure.example.com", "secret": "mysecret"},
        ])

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            await manager.send_webhook(
                event="complete",
                payload={"summary": "Done"},
            )

            # Verify signature header was sent
            call_kwargs = mock_instance.post.call_args.kwargs
            headers = call_kwargs["headers"]
            assert "X-Signature-256" in headers
            assert headers["X-Signature-256"].startswith("sha256=")

    @pytest.mark.asyncio
    async def test_send_webhook_rate_limited(self):
        """Test webhook rate limiting handling."""
        manager = GitHubManager()
        manager.configure_webhooks([
            {"url": "https://ratelimited.example.com"},
        ])

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "1"}

            mock_success = MagicMock()
            mock_success.status_code = 200

            mock_instance = AsyncMock()
            # First call rate limited, second succeeds
            mock_instance.post.side_effect = [mock_response, mock_success]
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            with patch("asyncio.sleep"):
                results = await manager.send_webhook(
                    event="test",
                    payload={},
                )

            assert results["https://ratelimited.example.com"] is True

    @pytest.mark.asyncio
    async def test_send_webhook_failure(self):
        """Test webhook failure handling."""
        manager = GitHubManager()
        manager.configure_webhooks([
            {"url": "https://failing.example.com"},
        ])

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = Exception("Connection refused")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            with patch("asyncio.sleep"):
                results = await manager.send_webhook(
                    event="test",
                    payload={},
                )

            assert results["https://failing.example.com"] is False

    @pytest.mark.asyncio
    async def test_send_webhook_event_filter(self):
        """Test webhook event filtering."""
        manager = GitHubManager()
        manager.configure_webhooks([
            {"url": "https://all.example.com"},  # No filter
            {"url": "https://complete.example.com", "events": ["complete"]},
        ])

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            # Send phase_start - should only go to "all" webhook
            results = await manager.send_webhook(
                event="phase_start",
                payload={},
            )

            assert "https://all.example.com" in results
            assert "https://complete.example.com" not in results

    @pytest.mark.asyncio
    async def test_notify_phase_start(self):
        """Test notify_phase_start convenience method."""
        manager = GitHubManager()

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {}

            await manager.notify_phase_start(
                phase=2,
                phase_name="interview",
                project="myproject",
                session_id="br-123",
            )

            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["event"] == "phase_start"
            assert call_kwargs["payload"]["phase"] == 2

    @pytest.mark.asyncio
    async def test_notify_phase_complete(self):
        """Test notify_phase_complete convenience method."""
        manager = GitHubManager()

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {}

            await manager.notify_phase_complete(
                phase=3,
                phase_name="planning",
                result="success",
                duration_seconds=120.5,
            )

            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["event"] == "phase_complete"
            assert call_kwargs["payload"]["result"] == "success"
            assert call_kwargs["payload"]["duration_seconds"] == 120.5

    @pytest.mark.asyncio
    async def test_notify_blocked(self):
        """Test notify_blocked convenience method."""
        manager = GitHubManager()

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {}

            await manager.notify_blocked(
                reason="Missing configuration",
                phase=5,
            )

            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["event"] == "blocked"
            assert "Missing configuration" in call_kwargs["payload"]["reason"]

    @pytest.mark.asyncio
    async def test_notify_error(self):
        """Test notify_error convenience method."""
        manager = GitHubManager()

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {}

            await manager.notify_error(
                error="Test execution failed",
                phase=7,
            )

            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["event"] == "error"
            assert "failed" in call_kwargs["payload"]["error"]

    @pytest.mark.asyncio
    async def test_notify_complete(self):
        """Test notify_complete convenience method."""
        manager = GitHubManager()

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {}

            await manager.notify_complete(
                summary="Project completed successfully",
                total_duration_seconds=3600.0,
            )

            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["event"] == "complete"
            assert call_kwargs["payload"]["total_duration_seconds"] == 3600.0


class TestGetGitHubManager:
    """Tests for get_github_manager convenience function."""

    def test_get_github_manager(self):
        """Test getting manager instance."""
        manager = get_github_manager()
        assert isinstance(manager, GitHubManager)

    def test_get_github_manager_with_params(self):
        """Test getting manager with parameters."""
        manager = get_github_manager(
            repo_path="/custom/path",
            token="ghp_custom",
        )

        assert manager.repo_path == "/custom/path"
        assert manager.token == "ghp_custom"


class TestExceptions:
    """Tests for exception classes."""

    def test_github_error(self):
        """Test GitHubError exception."""
        error = GitHubError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError("Not authenticated")
        assert isinstance(error, GitHubError)
        assert str(error) == "Not authenticated"

    def test_git_command_error(self):
        """Test GitCommandError exception."""
        error = GitCommandError("Command failed", 128, "fatal: error")
        assert error.returncode == 128
        assert error.stderr == "fatal: error"
        assert isinstance(error, GitHubError)
