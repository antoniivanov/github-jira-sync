from unittest.mock import Mock

import pytest

from issues_sync.issue import BaseIssue, BaseIssueField
from issues_sync.sync_engine import SyncEngine
from test_utils import InMemoryState


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
        return BaseIssue(key=key, project=BaseIssueField("test"), title=BaseIssueField(title), description=BaseIssueField(""))

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