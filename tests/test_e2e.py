import datetime

import pytest

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection
from issues_sync.jira_connection import JiraConnection
from issues_sync.sync_engine import SyncEngine
from issues_sync.sync_strategy import GithubToJiraSyncStrategy
from test_utils import InMemoryState

CURRENT_TIME = datetime.datetime.now().isoformat()

github_id_test_ussue_1 = 954


def decorate_get_issues(github_connection, func):
    def wrapper(*args, **kwargs):
        return [github_connection.get_issue(github_id_test_ussue_1), github_connection.get_issue(1179)]

    issue = github_connection._repo.get_issue(github_id_test_ussue_1)
    issue.edit(body=f"This is a test issue 1. Time: {CURRENT_TIME}")

    return wrapper


class TestSyncEnd2End:

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def github_connection(self, config):
        github_connection = GithubConnection(config.github)
        github_connection.get_issues = decorate_get_issues(github_connection, github_connection.get_issues)
        return github_connection

    @pytest.fixture
    def sync_strategy(self, github_connection, jira_connection):
        return GithubToJiraSyncStrategy(jira_connection, github_connection)

    @pytest.fixture
    def jira_connection(self, config):
        return JiraConnection(config.jira)

    @pytest.fixture
    def state(self):
        return InMemoryState()

    @pytest.fixture
    def sync_engine(self, github_connection, jira_connection, sync_strategy, state):
        return SyncEngine(github_connection, jira_connection, sync_strategy, state)

    def test_sync(self, sync_engine, github_connection, jira_connection, sync_strategy, state):
        sync_engine.sync()

        jira_key = state.get_jira_issue(github_id_test_ussue_1)
        assert jira_key is not None
        assert f"This is a test issue 1. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).description.value
