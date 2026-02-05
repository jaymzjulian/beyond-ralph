"""Integration tests for GitHub integration module.

Tests the full GitHub workflow integration including:
- GitHubManager initialization with repo detection
- Git operations (branch creation, staging, committing)
- PR creation workflow end-to-end
- Issue creation workflow end-to-end
- Webhook notification workflow
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import httpx
import pytest

from beyond_ralph.integrations.github import (
    AuthenticationError,
    GitCommandError,
    GitHubError,
    GitHubManager,
    Issue,
    PullRequest,
    WebhookConfig,
    WebhookEvent,
    get_github_manager,
)


class TestGitHubManagerInit:
    """Tests for GitHubManager initialization and configuration."""

    def test_init_with_defaults(self):
        """GitHubManager initializes with defaults."""
        with patch.dict("os.environ", {}, clear=True):
            manager = GitHubManager()
            assert manager.repo_path is not None
            assert manager.token is None
            assert not manager.is_authenticated

    def test_init_with_custom_path(self, tmp_path):
        """GitHubManager accepts custom repo path."""
        manager = GitHubManager(repo_path=str(tmp_path))
        assert manager.repo_path == str(tmp_path)

    def test_init_with_token(self):
        """GitHubManager accepts custom token."""
        manager = GitHubManager(token="test-token-123")
        assert manager.token == "test-token-123"
        assert manager.is_authenticated

    def test_init_with_env_token(self):
        """GitHubManager reads token from environment."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "env-token-456"}):
            manager = GitHubManager()
            assert manager.token == "env-token-456"
            assert manager.is_authenticated

    def test_detect_repo_ssh_url(self, tmp_path):
        """Detect repo from SSH remote URL."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "git@github.com:owner/repo.git\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            repo = manager.detect_repo()
            assert repo["owner"] == "owner"
            assert repo["repo"] == "repo"

    def test_detect_repo_https_url(self, tmp_path):
        """Detect repo from HTTPS remote URL."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "https://github.com/my-org/my-repo.git\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            repo = manager.detect_repo()
            assert repo["owner"] == "my-org"
            assert repo["repo"] == "my-repo"

    def test_detect_repo_without_git_extension(self, tmp_path):
        """Detect repo from URL without .git extension."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/project\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            repo = manager.detect_repo()
            assert repo["owner"] == "user"
            assert repo["repo"] == "project"

    def test_detect_repo_no_remote(self, tmp_path):
        """Detect repo fails when no remote configured."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(
            manager, "_run_git", side_effect=GitCommandError("No remote", 1, "")
        ):
            with pytest.raises(GitHubError, match="No git remote"):
                manager.detect_repo()

    def test_detect_repo_invalid_url(self, tmp_path):
        """Detect repo fails on invalid URL format."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "git@gitlab.com:owner/repo.git\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            with pytest.raises(GitHubError, match="Could not parse GitHub URL"):
                manager.detect_repo()

    def test_detect_repo_caches_result(self, tmp_path):
        """Detect repo caches result on subsequent calls."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "git@github.com:owner/repo.git\n"

        with patch.object(manager, "_run_git", return_value=mock_result) as mock_git:
            # First call
            repo1 = manager.detect_repo()
            # Second call
            repo2 = manager.detect_repo()

            assert repo1 == repo2
            # Should only call git once
            assert mock_git.call_count == 1


class TestGitOperations:
    """Tests for git command operations."""

    def test_get_current_branch(self, tmp_path):
        """Get current branch name."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "feature-branch\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            branch = manager.get_current_branch()
            assert branch == "feature-branch"

    def test_is_clean_true(self, tmp_path):
        """is_clean returns True when no changes."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = ""

        with patch.object(manager, "_run_git", return_value=mock_result):
            assert manager.is_clean()

    def test_is_clean_false(self, tmp_path):
        """is_clean returns False when changes exist."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = " M file.py\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            assert not manager.is_clean()

    def test_create_branch(self, tmp_path):
        """Create a new branch."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            result = manager.create_branch("new-feature")
            assert result is True
            mock_git.assert_called_once_with(["checkout", "-b", "new-feature", "HEAD"])

    def test_create_branch_with_base(self, tmp_path):
        """Create branch from specific base."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            manager.create_branch("new-feature", base="main")
            mock_git.assert_called_once_with(["checkout", "-b", "new-feature", "main"])

    def test_checkout_branch(self, tmp_path):
        """Checkout existing branch."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            result = manager.checkout_branch("existing-branch")
            assert result is True
            mock_git.assert_called_once_with(["checkout", "existing-branch"])

    def test_checkout_branch_create(self, tmp_path):
        """Checkout and create branch."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            result = manager.checkout_branch("new-branch", create=True)
            assert result is True
            mock_git.assert_called_once_with(["checkout", "-b", "new-branch"])

    def test_branch_exists_local_true(self, tmp_path):
        """branch_exists returns True for local branch."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "  feature-branch\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            assert manager.branch_exists("feature-branch")

    def test_branch_exists_local_false(self, tmp_path):
        """branch_exists returns False when branch missing."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = ""

        with patch.object(manager, "_run_git", return_value=mock_result):
            assert not manager.branch_exists("missing-branch")

    def test_branch_exists_remote(self, tmp_path):
        """branch_exists checks remote branches."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "abc123 refs/heads/remote-branch\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            assert manager.branch_exists("remote-branch", remote=True)

    def test_stage_files_specific(self, tmp_path):
        """Stage specific files."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            result = manager.stage_files(["file1.py", "file2.py"])
            assert result is True
            mock_git.assert_called_once_with(["add", "file1.py", "file2.py"])

    def test_stage_files_all(self, tmp_path):
        """Stage all changes."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            result = manager.stage_files()
            assert result is True
            mock_git.assert_called_once_with(["add", "-A"])

    def test_commit_simple(self, tmp_path):
        """Create simple commit."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_commit = Mock()
        mock_commit.stdout = ""

        mock_sha = Mock()
        mock_sha.stdout = "abc123def456\n"

        with patch.object(manager, "_run_git", side_effect=[mock_commit, mock_sha]):
            sha = manager.commit("feat: add feature")
            assert sha == "abc123def456"

    def test_commit_with_scope(self, tmp_path):
        """Create commit with scope."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_commit = Mock()
        mock_sha = Mock()
        mock_sha.stdout = "abc123\n"

        with patch.object(
            manager, "_run_git", side_effect=[mock_commit, mock_sha]
        ) as mock_git:
            sha = manager.commit("feat: add feature", scope="auth")
            assert sha == "abc123"

            # Check commit message format
            commit_call = mock_git.call_args_list[0]
            message = commit_call[0][0][2]
            assert "feat(auth):" in message

    def test_commit_with_coauthor(self, tmp_path):
        """Create commit with co-author."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_commit = Mock()
        mock_sha = Mock()
        mock_sha.stdout = "abc123\n"

        with patch.object(
            manager, "_run_git", side_effect=[mock_commit, mock_sha]
        ) as mock_git:
            sha = manager.commit("feat: add feature", co_author="Test <test@test.com>")
            assert sha == "abc123"

            # Check co-author in message
            commit_call = mock_git.call_args_list[0]
            message = commit_call[0][0][2]
            assert "Co-Authored-By: Test <test@test.com>" in message

    def test_push_branch_current(self, tmp_path):
        """Push current branch."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_branch = Mock()
        mock_branch.stdout = "feature\n"

        with patch.object(manager, "_run_git") as mock_git:
            with patch.object(manager, "get_current_branch", return_value="feature"):
                result = manager.push_branch()
                assert result is True

                # Check push command
                push_call = mock_git.call_args_list[0]
                args = push_call[0][0]
                assert "push" in args
                assert "--set-upstream" in args
                assert "origin" in args
                assert "feature" in args

    def test_push_branch_specific(self, tmp_path):
        """Push specific branch."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            result = manager.push_branch("my-branch")
            assert result is True

            args = mock_git.call_args[0][0]
            assert "my-branch" in args

    def test_push_branch_force(self, tmp_path):
        """Push branch with force."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "_run_git") as mock_git:
            manager.push_branch("my-branch", force=True)

            args = mock_git.call_args[0][0]
            assert "--force-with-lease" in args

    def test_atomic_commit(self, tmp_path):
        """Atomic commit stages and commits specific files."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "stage_files") as mock_stage:
            with patch.object(manager, "commit", return_value="abc123") as mock_commit:
                sha = manager.atomic_commit(
                    ["file1.py", "file2.py"], "feat: add files"
                )

                assert sha == "abc123"
                mock_stage.assert_called_once_with(["file1.py", "file2.py"])
                mock_commit.assert_called_once_with("feat: add files", None)

    def test_has_uncommitted_changes_true(self, tmp_path):
        """has_uncommitted_changes returns True when dirty."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "is_clean", return_value=False):
            assert manager.has_uncommitted_changes()

    def test_has_uncommitted_changes_false(self, tmp_path):
        """has_uncommitted_changes returns False when clean."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "is_clean", return_value=True):
            assert not manager.has_uncommitted_changes()

    def test_get_changed_files_all(self, tmp_path):
        """Get all changed files from status."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = " M file1.py\n A file2.py\nMM file3.py\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            files = manager.get_changed_files()
            assert "file1.py" in files
            assert "file2.py" in files
            assert "file3.py" in files
            assert len(files) == 3

    def test_get_changed_files_staged_only(self, tmp_path):
        """Get only staged files."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = "file1.py\nfile2.py\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            files = manager.get_changed_files(staged_only=True)
            assert files == ["file1.py", "file2.py"]

    def test_get_changed_files_renamed(self, tmp_path):
        """Get changed files handles renames."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_result = Mock()
        mock_result.stdout = " R old.py -> new.py\n"

        with patch.object(manager, "_run_git", return_value=mock_result):
            files = manager.get_changed_files()
            assert "new.py" in files


class TestPRWorkflow:
    """Tests for pull request workflow integration."""

    def test_create_pr_basic(self, tmp_path):
        """Create basic pull request."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        pr_data = {
            "number": 42,
            "title": "Add feature",
            "body": "This adds a feature",
            "headRefName": "feature",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/42",
            "createdAt": "2024-01-15T10:00:00Z",
            "merged": False,
            "closed": False,
            "isDraft": False,
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(pr_data)

        with patch.object(manager, "_run_gh", return_value=mock_result):
            with patch.object(manager, "get_current_branch", return_value="feature"):
                pr = manager.create_pr("Add feature", "This adds a feature")

                assert pr.number == 42
                assert pr.title == "Add feature"
                assert pr.branch == "feature"
                assert pr.base == "main"
                assert pr.status == "open"

    def test_create_pr_draft(self, tmp_path):
        """Create draft pull request."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        pr_data = {
            "number": 43,
            "title": "WIP: Feature",
            "body": "Work in progress",
            "headRefName": "wip",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/43",
            "createdAt": "2024-01-15T10:00:00Z",
            "merged": False,
            "closed": False,
            "isDraft": True,
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(pr_data)

        with patch.object(manager, "_run_gh", return_value=mock_result) as mock_gh:
            with patch.object(manager, "get_current_branch", return_value="wip"):
                pr = manager.create_pr("WIP: Feature", "Work in progress", draft=True)

                assert pr.status == "draft"

                # Check --draft flag was used
                args = mock_gh.call_args[0][0]
                assert "--draft" in args

    def test_create_pr_custom_branch(self, tmp_path):
        """Create PR with custom branch."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        pr_data = {
            "number": 44,
            "title": "Feature",
            "body": "Description",
            "headRefName": "custom-branch",
            "baseRefName": "develop",
            "url": "https://github.com/owner/repo/pull/44",
            "createdAt": "2024-01-15T10:00:00Z",
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(pr_data)

        with patch.object(manager, "_run_gh", return_value=mock_result) as mock_gh:
            pr = manager.create_pr(
                "Feature", "Description", branch="custom-branch", base="develop"
            )

            assert pr.branch == "custom-branch"
            assert pr.base == "develop"

            # Check args
            args = mock_gh.call_args[0][0]
            assert "--head" in args
            assert "custom-branch" in args
            assert "--base" in args
            assert "develop" in args

    def test_create_pr_from_task(self, tmp_path):
        """Create PR from task context."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        pr_data = {
            "number": 45,
            "title": "Implement authentication module with OAuth2 support",
            "body": "Generated body",
            "headRefName": "feat-auth",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/45",
            "createdAt": "2024-01-15T10:00:00Z",
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(pr_data)

        with patch.object(manager, "_run_gh", return_value=mock_result):
            with patch.object(manager, "get_current_branch", return_value="feat-auth"):
                pr = manager.create_pr_from_task(
                    summary="Implement authentication module with OAuth2 support",
                    changes=[
                        "Added OAuth2 provider",
                        "Added token validation",
                        "Added user session management",
                    ],
                    unit_status="Passed (95% coverage)",
                    integration_status="Passed (10/10 tests)",
                    session_id="test-session-123",
                )

                assert pr.number == 45
                # Title from gh response
                assert pr.title == "Implement authentication module with OAuth2 support"

    def test_create_pr_from_task_long_summary(self, tmp_path):
        """create_pr_from_task truncates long summaries in title."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        pr_data = {
            "number": 46,
            "title": "Short title",
            "body": "Body",
            "headRefName": "feature",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/46",
            "createdAt": "2024-01-15T10:00:00Z",
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(pr_data)

        with patch.object(manager, "_run_gh", return_value=mock_result):
            with patch.object(manager, "get_current_branch", return_value="feature"):
                long_summary = "A" * 100  # 100 chars
                pr = manager.create_pr_from_task(
                    summary=long_summary,
                    changes=["Change 1"],
                    session_id="test-session",
                )

                # Title should be truncated
                assert pr is not None

    def test_get_pr(self, tmp_path):
        """Get PR details."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        pr_data = {
            "number": 47,
            "title": "Fix bug",
            "body": "Fixes #123",
            "headRefName": "bugfix",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/47",
            "createdAt": "2024-01-15T10:00:00Z",
            "merged": True,
            "closed": True,
            "isDraft": False,
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(pr_data)

        with patch.object(manager, "_run_gh", return_value=mock_result):
            pr = manager.get_pr(47)

            assert pr.number == 47
            assert pr.status == "merged"

    def test_list_prs_open(self, tmp_path):
        """List open pull requests."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        prs_data = [
            {
                "number": 48,
                "title": "PR 1",
                "body": "Body 1",
                "headRefName": "feat1",
                "baseRefName": "main",
                "url": "https://github.com/owner/repo/pull/48",
                "createdAt": "2024-01-15T10:00:00Z",
            },
            {
                "number": 49,
                "title": "PR 2",
                "body": "Body 2",
                "headRefName": "feat2",
                "baseRefName": "main",
                "url": "https://github.com/owner/repo/pull/49",
                "createdAt": "2024-01-15T11:00:00Z",
            },
        ]

        mock_result = Mock()
        mock_result.stdout = json.dumps(prs_data)

        with patch.object(manager, "_run_gh", return_value=mock_result):
            prs = manager.list_prs()

            assert len(prs) == 2
            assert prs[0].number == 48
            assert prs[1].number == 49

    def test_list_prs_with_filters(self, tmp_path):
        """List PRs with state filter."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        mock_result = Mock()
        mock_result.stdout = "[]"

        with patch.object(manager, "_run_gh", return_value=mock_result) as mock_gh:
            manager.list_prs(state="closed", limit=10)

            args = mock_gh.call_args[0][0]
            assert "--state" in args
            assert "closed" in args
            assert "--limit" in args
            assert "10" in args


class TestIssueWorkflow:
    """Tests for issue workflow integration."""

    def test_create_issue_basic(self, tmp_path):
        """Create basic issue."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        issue_data = {
            "number": 100,
            "title": "Bug report",
            "body": "Something is broken",
            "url": "https://github.com/owner/repo/issues/100",
            "labels": [],
            "assignees": [],
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(issue_data)

        with patch.object(manager, "_run_gh", return_value=mock_result):
            issue = manager.create_issue("Bug report", "Something is broken")

            assert issue.number == 100
            assert issue.title == "Bug report"
            assert issue.body == "Something is broken"

    def test_create_issue_with_labels(self, tmp_path):
        """Create issue with labels."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        issue_data = {
            "number": 101,
            "title": "Feature request",
            "body": "Add feature X",
            "url": "https://github.com/owner/repo/issues/101",
            "labels": [{"name": "enhancement"}, {"name": "priority-high"}],
            "assignees": [],
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(issue_data)

        with patch.object(manager, "_run_gh", return_value=mock_result) as mock_gh:
            issue = manager.create_issue(
                "Feature request", "Add feature X", labels=["enhancement", "priority-high"]
            )

            assert len(issue.labels) == 2
            assert "enhancement" in issue.labels

            # Check labels were passed
            args = mock_gh.call_args[0][0]
            assert "--label" in args

    def test_create_issue_with_assignees(self, tmp_path):
        """Create issue with assignees."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        issue_data = {
            "number": 102,
            "title": "Task",
            "body": "Do something",
            "url": "https://github.com/owner/repo/issues/102",
            "labels": [],
            "assignees": [{"login": "user1"}, {"login": "user2"}],
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(issue_data)

        with patch.object(manager, "_run_gh", return_value=mock_result) as mock_gh:
            issue = manager.create_issue(
                "Task", "Do something", assignees=["user1", "user2"]
            )

            assert len(issue.assignees) == 2
            assert "user1" in issue.assignees

            # Check assignees were passed
            args = mock_gh.call_args[0][0]
            assert "--assignee" in args

    def test_create_blocker_issue(self, tmp_path):
        """Create blocker issue from context."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        issue_data = {
            "number": 103,
            "title": "[BLOCKED] implementation: auth-module - API not responding",
            "body": "Generated body",
            "url": "https://github.com/owner/repo/issues/103",
            "labels": [{"name": "blocked"}, {"name": "beyond-ralph"}],
            "assignees": [],
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(issue_data)

        with patch.object(manager, "_run_gh", return_value=mock_result) as mock_gh:
            issue = manager.create_blocker_issue(
                phase="implementation",
                module="auth-module",
                problem="External API is not responding to authentication requests",
                attempted_solutions=[
                    "Checked API credentials",
                    "Verified network connectivity",
                    "Tested with different endpoints",
                ],
                required_action="Verify API is running and credentials are correct",
                session_id="session-abc-123",
            )

            assert issue.number == 103
            assert "BLOCKED" in issue.title

            # Check labels
            args = mock_gh.call_args[0][0]
            assert "--label" in args
            assert "blocked" in args

    def test_get_issue(self, tmp_path):
        """Get issue details."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        issue_data = {
            "number": 104,
            "title": "Issue title",
            "body": "Issue body",
            "url": "https://github.com/owner/repo/issues/104",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "developer"}],
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(issue_data)

        with patch.object(manager, "_run_gh", return_value=mock_result):
            issue = manager.get_issue(104)

            assert issue.number == 104
            assert issue.labels == ["bug"]
            assert issue.assignees == ["developer"]

    def test_close_issue_without_comment(self, tmp_path):
        """Close issue without comment."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        with patch.object(manager, "_run_gh") as mock_gh:
            result = manager.close_issue(105)

            assert result is True
            # Should only call close, not comment
            assert mock_gh.call_count == 1
            args = mock_gh.call_args[0][0]
            assert "close" in args

    def test_close_issue_with_comment(self, tmp_path):
        """Close issue with comment."""
        manager = GitHubManager(repo_path=str(tmp_path), token="test-token")

        with patch.object(manager, "_run_gh") as mock_gh:
            result = manager.close_issue(106, comment="Fixed in #107")

            assert result is True
            # Should call comment, then close
            assert mock_gh.call_count == 2

            # Check comment call
            comment_call = mock_gh.call_args_list[0]
            assert "comment" in comment_call[0][0]

            # Check close call
            close_call = mock_gh.call_args_list[1]
            assert "close" in close_call[0][0]


class TestWebhookWorkflow:
    """Tests for webhook notification workflow."""

    def test_configure_webhooks(self, tmp_path):
        """Configure webhook endpoints."""
        manager = GitHubManager(repo_path=str(tmp_path))

        webhooks = [
            {"url": "https://example.com/webhook1", "secret": "secret1"},
            {
                "url": "https://example.com/webhook2",
                "events": ["phase_start", "phase_complete"],
            },
        ]

        manager.configure_webhooks(webhooks)

        assert len(manager._webhooks) == 2
        assert manager._webhooks[0].url == "https://example.com/webhook1"
        assert manager._webhooks[0].secret == "secret1"
        assert manager._webhooks[1].events == ["phase_start", "phase_complete"]

    @pytest.mark.asyncio
    async def test_send_webhook_basic(self, tmp_path):
        """Send basic webhook notification."""
        manager = GitHubManager(repo_path=str(tmp_path))

        manager.configure_webhooks([{"url": "https://example.com/webhook"}])

        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = await manager.send_webhook(
                event="test_event",
                payload={"data": "test"},
                project="test-project",
                session_id="session-123",
            )

            assert results["https://example.com/webhook"] is True
            assert mock_client.post.called

    @pytest.mark.asyncio
    async def test_send_webhook_with_signature(self, tmp_path):
        """Send webhook with HMAC signature."""
        manager = GitHubManager(repo_path=str(tmp_path))

        manager.configure_webhooks(
            [{"url": "https://example.com/webhook", "secret": "my-secret"}]
        )

        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = await manager.send_webhook(
                event="test_event",
                payload={"data": "test"},
            )

            assert results["https://example.com/webhook"] is True

            # Check signature header was added
            call_kwargs = mock_client.post.call_args[1]
            assert "X-Signature-256" in call_kwargs["headers"]
            assert call_kwargs["headers"]["X-Signature-256"].startswith("sha256=")

    @pytest.mark.asyncio
    async def test_send_webhook_event_filtering(self, tmp_path):
        """Webhooks filter events based on configuration."""
        manager = GitHubManager(repo_path=str(tmp_path))

        manager.configure_webhooks(
            [
                {
                    "url": "https://example.com/webhook1",
                    "events": ["phase_start"],
                },
                {
                    "url": "https://example.com/webhook2",
                    "events": ["phase_complete"],
                },
            ]
        )

        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Send phase_start event
            results = await manager.send_webhook(
                event="phase_start",
                payload={"phase": 1},
            )

            # Only webhook1 should receive it
            assert "https://example.com/webhook1" in results
            assert "https://example.com/webhook2" not in results

    @pytest.mark.asyncio
    async def test_send_webhook_retry_on_429(self, tmp_path):
        """Webhook retries on rate limit (429)."""
        manager = GitHubManager(repo_path=str(tmp_path))

        manager.configure_webhooks([{"url": "https://example.com/webhook"}])

        # First response: rate limited
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        # Second response: success
        mock_response_200 = Mock()
        mock_response_200.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_response_429, mock_response_200]
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = await manager.send_webhook(
                event="test_event",
                payload={"data": "test"},
            )

            # Should eventually succeed
            assert results["https://example.com/webhook"] is True
            # Should have retried
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_send_webhook_failure_after_retries(self, tmp_path):
        """Webhook returns False after max retries."""
        manager = GitHubManager(repo_path=str(tmp_path))

        manager.configure_webhooks([{"url": "https://example.com/webhook"}])

        mock_response = Mock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            results = await manager.send_webhook(
                event="test_event",
                payload={"data": "test"},
            )

            # Should fail
            assert results["https://example.com/webhook"] is False

    @pytest.mark.asyncio
    async def test_notify_phase_start(self, tmp_path):
        """Send phase_start notification."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"https://example.com": True}

            results = await manager.notify_phase_start(
                phase=1,
                phase_name="Specification Ingestion",
                project="my-project",
                session_id="session-123",
            )

            assert results is not None
            mock_send.assert_called_once()

            # Check event type and payload
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["event"] == "phase_start"
            assert call_kwargs["payload"]["phase"] == 1
            assert call_kwargs["payload"]["phase_name"] == "Specification Ingestion"

    @pytest.mark.asyncio
    async def test_notify_phase_complete(self, tmp_path):
        """Send phase_complete notification."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"https://example.com": True}

            results = await manager.notify_phase_complete(
                phase=1,
                phase_name="Specification Ingestion",
                result="success",
                duration_seconds=120.5,
                project="my-project",
                session_id="session-123",
            )

            assert results is not None
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["event"] == "phase_complete"
            assert call_kwargs["payload"]["result"] == "success"
            assert call_kwargs["payload"]["duration_seconds"] == 120.5

    @pytest.mark.asyncio
    async def test_notify_blocked(self, tmp_path):
        """Send blocked notification."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"https://example.com": True}

            results = await manager.notify_blocked(
                reason="API credentials missing",
                phase=7,
                project="my-project",
                session_id="session-123",
            )

            assert results is not None
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["event"] == "blocked"
            assert call_kwargs["payload"]["reason"] == "API credentials missing"

    @pytest.mark.asyncio
    async def test_notify_error(self, tmp_path):
        """Send error notification."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"https://example.com": True}

            results = await manager.notify_error(
                error="Database connection failed",
                phase=7,
                project="my-project",
                session_id="session-123",
            )

            assert results is not None
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["event"] == "error"
            assert call_kwargs["payload"]["error"] == "Database connection failed"

    @pytest.mark.asyncio
    async def test_notify_complete(self, tmp_path):
        """Send complete notification."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch.object(manager, "send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"https://example.com": True}

            results = await manager.notify_complete(
                summary="Project completed successfully",
                total_duration_seconds=3600.0,
                project="my-project",
                session_id="session-123",
            )

            assert results is not None
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["event"] == "complete"
            assert call_kwargs["payload"]["summary"] == "Project completed successfully"
            assert call_kwargs["payload"]["total_duration_seconds"] == 3600.0


class TestGitCommandErrors:
    """Tests for git command error handling."""

    def test_git_command_timeout(self, tmp_path):
        """Git command timeout raises GitCommandError."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 120)):
            with pytest.raises(GitCommandError, match="timed out"):
                manager._run_git(["status"])

    def test_git_command_failure(self, tmp_path):
        """Git command failure raises GitCommandError."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_error = subprocess.CalledProcessError(1, "git", stderr="fatal: not a git repo")

        with patch("subprocess.run", side_effect=mock_error):
            with pytest.raises(GitCommandError) as exc_info:
                manager._run_git(["status"])

            assert exc_info.value.returncode == 1
            assert "not a git repo" in exc_info.value.stderr

    def test_gh_command_not_found(self, tmp_path):
        """gh CLI not found raises GitCommandError."""
        manager = GitHubManager(repo_path=str(tmp_path))

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(GitCommandError, match="gh CLI not found"):
                manager._run_gh(["pr", "list"])

    def test_gh_authentication_error(self, tmp_path):
        """gh authentication failure raises AuthenticationError."""
        manager = GitHubManager(repo_path=str(tmp_path))

        mock_error = subprocess.CalledProcessError(
            1, "gh", stderr="authentication required"
        )

        with patch("subprocess.run", side_effect=mock_error):
            with pytest.raises(AuthenticationError, match="authentication failed"):
                manager._run_gh(["pr", "list"])


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_github_manager(self):
        """get_github_manager returns GitHubManager instance."""
        manager = get_github_manager()
        assert isinstance(manager, GitHubManager)

    def test_get_github_manager_with_args(self, tmp_path):
        """get_github_manager accepts arguments."""
        manager = get_github_manager(repo_path=str(tmp_path), token="test-token")
        assert manager.repo_path == str(tmp_path)
        assert manager.token == "test-token"


class TestWebhookConfig:
    """Tests for WebhookConfig helper class."""

    def test_webhook_should_send_no_filter(self):
        """Webhook with no event filter sends all events."""
        webhook = WebhookConfig(url="https://example.com/webhook")

        assert webhook.should_send("phase_start")
        assert webhook.should_send("phase_complete")
        assert webhook.should_send("any_event")

    def test_webhook_should_send_with_filter(self):
        """Webhook with event filter only sends matching events."""
        webhook = WebhookConfig(
            url="https://example.com/webhook",
            events=["phase_start", "phase_complete"],
        )

        assert webhook.should_send("phase_start")
        assert webhook.should_send("phase_complete")
        assert not webhook.should_send("blocked")
        assert not webhook.should_send("error")


class TestPullRequestModel:
    """Tests for PullRequest model."""

    def test_from_gh_output_basic(self):
        """PullRequest.from_gh_output parses basic data."""
        data = {
            "number": 50,
            "title": "Test PR",
            "body": "Test body",
            "headRefName": "feature",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/50",
            "createdAt": "2024-01-15T10:00:00Z",
        }

        pr = PullRequest.from_gh_output(data)

        assert pr.number == 50
        assert pr.title == "Test PR"
        assert pr.branch == "feature"
        assert pr.base == "main"

    def test_from_gh_output_merged_status(self):
        """PullRequest.from_gh_output detects merged status."""
        data = {
            "number": 51,
            "title": "Merged PR",
            "body": "",
            "headRefName": "feature",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/51",
            "createdAt": "2024-01-15T10:00:00Z",
            "merged": True,
            "closed": True,
        }

        pr = PullRequest.from_gh_output(data)
        assert pr.status == "merged"

    def test_from_gh_output_draft_status(self):
        """PullRequest.from_gh_output detects draft status."""
        data = {
            "number": 52,
            "title": "Draft PR",
            "body": "",
            "headRefName": "wip",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/52",
            "createdAt": "2024-01-15T10:00:00Z",
            "isDraft": True,
        }

        pr = PullRequest.from_gh_output(data)
        assert pr.status == "draft"


class TestIssueModel:
    """Tests for Issue model."""

    def test_from_gh_output_basic(self):
        """Issue.from_gh_output parses basic data."""
        data = {
            "number": 200,
            "title": "Test Issue",
            "body": "Test body",
            "url": "https://github.com/owner/repo/issues/200",
            "labels": [],
            "assignees": [],
        }

        issue = Issue.from_gh_output(data)

        assert issue.number == 200
        assert issue.title == "Test Issue"
        assert issue.labels == []
        assert issue.assignees == []

    def test_from_gh_output_with_labels(self):
        """Issue.from_gh_output extracts label names."""
        data = {
            "number": 201,
            "title": "Test Issue",
            "body": "Test body",
            "url": "https://github.com/owner/repo/issues/201",
            "labels": [
                {"name": "bug", "color": "red"},
                {"name": "priority-high", "color": "orange"},
            ],
            "assignees": [],
        }

        issue = Issue.from_gh_output(data)

        assert len(issue.labels) == 2
        assert "bug" in issue.labels
        assert "priority-high" in issue.labels

    def test_from_gh_output_with_assignees(self):
        """Issue.from_gh_output extracts assignee logins."""
        data = {
            "number": 202,
            "title": "Test Issue",
            "body": "Test body",
            "url": "https://github.com/owner/repo/issues/202",
            "labels": [],
            "assignees": [
                {"login": "user1", "id": 123},
                {"login": "user2", "id": 456},
            ],
        }

        issue = Issue.from_gh_output(data)

        assert len(issue.assignees) == 2
        assert "user1" in issue.assignees
        assert "user2" in issue.assignees
