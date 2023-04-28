import pytest
from unittest.mock import Mock, patch

from issues_sync.config import JiraConfig
from issues_sync.jira_connection import JiraConnection
from issues_sync.issue import BaseIssue, BaseIssueComment, BaseIssueField, BaseIssueStatus


@pytest.fixture
def jira_connection():
    config = JiraConfig(url="http://test.com", user="test_user", password="test_pass", project="Test Project")

    with patch('issues_sync.jira_connection.JIRA'):
        jira_conn = JiraConnection(config)
        yield jira_conn


def test_find_issue_id_by_title(jira_connection):
    with patch.object(jira_connection._jira, 'search_issues') as mock_search_issues:
        mock_search_issues.return_value = [Mock(key="TEST-123")]

        issue_id = jira_connection.find_issue_id_by_title("test title")
        assert issue_id == "TEST-123"

        mock_search_issues.assert_called_once_with('project = "Test Project" AND summary ~ \'"test title"\' ')


def test_get_issue(jira_connection):
    with patch.object(jira_connection._jira, 'issue') as mock_issue:
        mock_issue.return_value = _mock_issue()

        base_issue = jira_connection.get_issue("TEST-123")
        assert isinstance(base_issue, BaseIssue)
        assert base_issue.key == "TEST-123"
        assert base_issue.project == "Test Project"
        assert base_issue.title.value == "Test Issue"
        assert base_issue.description.value == "Test description"
        assert base_issue.status.value == BaseIssueStatus.OPEN
        assert len(base_issue.comments) == 0
        assert base_issue.updated_at == "2022-12-31T12:34:56.000+0000"


def _mock_issue():
    mock_issue = Mock(key="TEST-123",
                fields=Mock(project=Mock(updated="2022-12-31T12:34:56.000+0000"),
                            summary="Test Issue",
                            description="Test description",
                            status=Mock(updated="2022-12-31T12:34:56.000+0000"),
                            comment=Mock(comments=[],
                                         total=0),
                            updated="2022-12-31T12:34:56.000+0000"))

    # name is not set in the mock as it is argument of Mock constructor
    mock_issue.fields.project.name = "Test Project"
    mock_issue.fields.status.name = "New"
    return mock_issue


def test_create_issue(jira_connection):
    with patch.object(jira_connection._jira, 'create_issue') as mock_create_issue:
        mock_create_issue.return_value = Mock(key="TEST-123")

        base_issue = BaseIssue(key="",
                               project="Test Project",
                               title=BaseIssueField("Test Issue"),
                               description=BaseIssueField("Test description"),
                               status=BaseIssueField(BaseIssueStatus.OPEN))

        issue_id = jira_connection.create_issue(base_issue)
        assert issue_id == "TEST-123"

        mock_create_issue.assert_called_once_with(fields={
            "project": {"key": "Test Project"},
            "summary": "Test Issue",
            "description": "Test description",
            "status": {"name": "New"},
            "issuetype": {"name": "Story"},
        })


def test_update_issue(jira_connection):
    with patch.object(jira_connection._jira, 'issue') as mock_issue:
        mock_issue.return_value = _mock_issue()

        base_issue = BaseIssue(key="",
                               project="Test Project",
                               title=BaseIssueField("Test Issue Title Updated"),
                               description=BaseIssueField("Test description updated"),
                               status=BaseIssueField(BaseIssueStatus.CLOSED))
        jira_connection.update_issue(base_issue)

        assert mock_issue.return_value.update.call_count == 1
        assert mock_issue.return_value.update.call_args[1]['fields']['summary'] == "Test Issue Title Updated"
        assert mock_issue.return_value.update.call_args[1]['fields']['description'] == "Test description updated"

        assert jira_connection._jira.transition_issue.call_count == 1
        assert jira_connection._jira.transition_issue.call_args[0] == ("TEST-123", "Done")
