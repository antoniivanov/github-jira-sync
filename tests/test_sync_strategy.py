from datetime import datetime
from unittest.mock import Mock

import pytest

from issues_sync.github_connection import GithubConnection
from issues_sync.issue import BaseIssue, BaseIssueField, BaseIssueStatus, BaseIssueComment
from issues_sync.jira_connection import JiraConnection
from issues_sync.sync_strategy import GithubToJiraSyncStrategy


@pytest.fixture
def jira_issue():
    return BaseIssue(
        key="JIRA-123",
        project="JIRA",
        title=BaseIssueField("Test Issue"),
        description=BaseIssueField("This is a test issue."),
        status=BaseIssueField(BaseIssueStatus.OPEN),
        comments=[
            BaseIssueComment("Test comment 1.", "user1", datetime(2022, 1, 1))
        ]
    )


@pytest.fixture
def github_issue():
    return BaseIssue(
        key="456",
        project="github",
        title=BaseIssueField("Test Issue"),
        description=BaseIssueField("This is a test issue."),
        status=BaseIssueField(BaseIssueStatus.OPEN),
        comments=[
            BaseIssueComment("Test comment 1.", "user1", datetime(2022, 1, 1)),
            BaseIssueComment("Test comment 2.", "user2", datetime(2022, 1, 2))
        ],
        html_url="https://github.com/testuser/testrepo/issues/123"
    )


@pytest.fixture
def jira_connection_mock():
    jira_connection_mock = Mock(spec=JiraConnection)
    jira_connection_mock.update_issue = Mock()
    return jira_connection_mock


@pytest.fixture
def github_connection_mock():
    github_connection_mock = Mock(spec=GithubConnection)
    github_connection_mock.update_issue = Mock()
    return github_connection_mock


@pytest.fixture
def sync_strategy(jira_connection_mock, github_connection_mock):
    return GithubToJiraSyncStrategy(jira_connection_mock, github_connection_mock)


def test_update_calls_jira_connection_update_issue_with_updated_issue(jira_connection_mock, jira_issue, github_issue,
                                                                      sync_strategy):
    # Act
    sync_strategy.update(jira_issue, github_issue)

    # Assert
    jira_connection_mock.update_issue.assert_called_once_with(jira_issue)


def test_update_updates_jira_issue_fields(jira_issue, github_issue, sync_strategy):
    # Arrange
    expected_description = f"""
Issue created by automatic sync. 
Original URL: {github_issue.html_url}

Do not edit this issue manually as the sync is one direction. 
Only status and labels can be changed.
--------------------------------------------------------- ---
{github_issue.description.value}"""

    # Act
    sync_strategy.update(jira_issue, github_issue)

    # Assert
    assert jira_issue.description.value == expected_description
    assert jira_issue.title == github_issue.title
    assert jira_issue.status.value == github_issue.status.value


def test_update_creates_jira_issue_comments(jira_issue, github_issue, sync_strategy):
    # Arrange

    # Act
    sync_strategy.update(jira_issue, github_issue)

    # Assert
    assert len(jira_issue.comments) == 2
    assert jira_issue.comments[0].body.value.strip() == "user1 wrote on GitHub:\nTest comment 1."
    assert jira_issue.comments[0].user.value == "user1"
    assert jira_issue.comments[1].body.value.strip() == "user2 wrote on GitHub:\nTest comment 2."
    assert jira_issue.comments[1].user.value == "user2"


def test_update_jira_issue_status_both_open(jira_issue, github_issue, sync_strategy):
    # Arrange
    github_issue.status.value = BaseIssueStatus.OPEN
    jira_issue.status.value = BaseIssueStatus.OPEN

    # Act
    sync_strategy.update(jira_issue, github_issue)

    # Assert
    assert jira_issue.status.value == BaseIssueStatus.OPEN
    assert github_issue.status.value == BaseIssueStatus.OPEN


def test_update_jira_issue_status_jira_open_github_closed(jira_issue, github_issue, sync_strategy):
    # Arrange
    github_issue.status.value = BaseIssueStatus.CLOSED
    jira_issue.status.value = BaseIssueStatus.OPEN

    # Act
    sync_strategy.update(jira_issue, github_issue)

    # Assert
    assert jira_issue.status.value == BaseIssueStatus.CLOSED
    assert github_issue.status.value == BaseIssueStatus.CLOSED

    assert sync_strategy._jira_connection.update_issue.call_count == 1
    assert sync_strategy._github_connection.update_issue.call_count == 0


def test_update_jira_issue_jire_closed_github_open(jira_issue, github_issue, sync_strategy):
    # Arrange
    github_issue.status.value = BaseIssueStatus.OPEN
    jira_issue.status.value = BaseIssueStatus.CLOSED

    # Act
    sync_strategy.update(jira_issue, github_issue)

    # Assert
    assert jira_issue.status.value == BaseIssueStatus.CLOSED
    assert github_issue.status.value == BaseIssueStatus.CLOSED

    assert sync_strategy._jira_connection.update_issue.call_count == 1
    assert sync_strategy._github_connection.update_issue.call_count == 1
