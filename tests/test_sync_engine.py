from unittest.mock import Mock

import pytest

from issues_sync.issue import BaseIssue, BaseIssueField
from issues_sync.sync_engine import SyncEngine
from issues_sync.utils import InMemoryState


class TestSyncEngine:
    @pytest.fixture
    def github_connection(self):
        return Mock()

    @pytest.fixture
    def sync_strategy(self):
        return Mock()

    @pytest.fixture
    def jira_connection(self):
        return Mock()

    @pytest.fixture
    def state(self):
        return InMemoryState()

    @pytest.fixture
    def sync_engine(self, github_connection, jira_connection, sync_strategy, state):
        return SyncEngine(github_connection, jira_connection, sync_strategy, state)

    def _base_issue(self, key: str, title: str):
        return BaseIssue(key=key, project="test", title=BaseIssueField(title), description=BaseIssueField(""))

    def test_sync(self, sync_engine, github_connection, jira_connection, sync_strategy, state):
        github_issues = [
            self._base_issue(key="1", title='Issue 1'),
            self._base_issue(key="2", title='Issue 2'),
            self._base_issue(key="3", title='Issue 3')]
        github_connection.get_issues.return_value = github_issues
        jira_connection.find_issue_id_by_title.side_effect = [None, 'JIRA-2', None]

        sync_engine.sync()

        assert sync_strategy.create_jira_issue.call_count == 2
        assert sync_strategy.update.call_count == 1

        assert state.get_jira_issue("1") is not None
        assert state.get_jira_issue("2") is not None
        assert state.get_jira_issue("3") is not None

    def test_sync_resume_on_outages(self, sync_engine, github_connection, jira_connection, sync_strategy, state):
        # Simulate an outage for the Github platform by mocking the `get_issues()` method to raise an exception
        github_connection.get_issues.side_effect = Exception("Github platform is currently down")

        # Create a SyncEngine instance with the mocked platforms and sync strategy
        sync_engine = SyncEngine(github_connection, jira_connection, sync_strategy)

        # Call the sync method to trigger the syncing process and verify that an exception is raised
        with pytest.raises(Exception):
            sync_engine.sync()

        # Simulate the Github platform coming back online by mocking the `get_issues()` method to return an empty list
        github_connection.get_issues.side_effect = Mock(return_value=[])

        # Call the sync method again and verify that syncing resumes
        sync_engine.sync()
