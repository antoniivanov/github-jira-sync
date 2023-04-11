from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from github.Issue import Issue
from github.IssueComment import IssueComment

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection, convert_to_base_issue
from issues_sync.issue import BaseIssue, BaseIssueComment, BaseIssueStatus


@pytest.fixture
def mock_github_issue():
    issue = MagicMock(spec=Issue)
    issue.number = 1234
    issue.repository.name = "test_repo"
    issue.repository.updated_at = datetime.now()
    issue.title = "Test Issue"
    issue.updated_at = datetime.now()
    issue.body = "This is a test issue"
    issue.state = "open"
    comment = MagicMock(spec=IssueComment)
    comment.body = "Test comment"
    comment.updated_at = datetime.now()
    comment.user.login = "test_user"
    comment.user.updated_at = datetime.now()
    issue.pull_request = None
    issue.get_comments.return_value = [comment]
    return issue


@pytest.fixture
def github_connection(mock_github_issue):
    with patch('github.Github'):
        config = MagicMock(spec=Config, project="test_project", token="test_token")
        connection = GithubConnection(config)
        yield connection


def test_convert_to_base_issue(mock_github_issue):
    base_issue = convert_to_base_issue(mock_github_issue)
    assert isinstance(base_issue, BaseIssue)
    assert base_issue.key == str(mock_github_issue.number)
    assert base_issue.project == mock_github_issue.repository.name
    assert base_issue.title.value == mock_github_issue.title
    assert base_issue.title.updated_at == mock_github_issue.updated_at
    assert base_issue.description.value == mock_github_issue.body
    assert base_issue.description.updated_at == mock_github_issue.updated_at
    assert len(base_issue.comments) == 1
    assert isinstance(base_issue.comments[0], BaseIssueComment)
    assert base_issue.comments[0].body.value == mock_github_issue.get_comments()[0].body
    assert base_issue.comments[0].user.value == mock_github_issue.get_comments()[0].user.login
    assert base_issue.comments[0].updated_at == mock_github_issue.get_comments()[0].updated_at
    assert base_issue.status.value == BaseIssueStatus.OPEN
    assert base_issue.status.updated_at == mock_github_issue.updated_at
    assert base_issue.updated_at == mock_github_issue.updated_at


def test_find_issue_id_by_title(github_connection, mock_github_issue):
    github_connection._repo.get_issues.return_value = [mock_github_issue]
    issue_title = "Test Issue"
    issue_id = github_connection.find_issue_id_by_title(issue_title)
    assert issue_id == str(mock_github_issue.number)


def test_find_issue_id_by_title_no_match(github_connection):
    github_connection._repo.get_issues.return_value = []
    issue_title = "Nonexistent Issue"
    issue_id = github_connection.find_issue_id_by_title(issue_title)
    assert issue_id is None


def test_get_issues(github_connection, mock_github_issue):
    github_connection._repo.get_issues.return_value = [mock_github_issue]
    since_time = datetime.now()
    issues = github_connection.get_issues(since_time)
    assert len(issues) == 1
    assert isinstance(issues[0], BaseIssue)
    assert issues[0].key == str(mock_github_issue.number)

