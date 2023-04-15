import datetime

import github.Issue
import pytest

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection
from issues_sync.jira_connection import JiraConnection
from issues_sync.sync_engine import SyncEngine
from issues_sync.sync_strategy import GithubToJiraSyncStrategy
from test_utils import InMemoryState

CURRENT_TIME = datetime.datetime.now().isoformat()

github_id_test_ussue_1 = "954"
github_id_test_ussue_2 = "1179"


def _create_or_update_comment(issue: github.Issue.Issue, comment_index: int, comment_text: str):
    comments = issue.get_comments()
    if comment_index < comments.totalCount:
        comments[comment_index].edit(comment_text)
    else:
        issue.create_comment(comment_text)
    pass


def decorate_get_issues(github_connection, func):
    def wrapper(*args, **kwargs):
        return [github_connection.get_issue(github_id_test_ussue_1),
                github_connection.get_issue(github_id_test_ussue_2)]

    issue = github_connection._repo.get_issue(int(github_id_test_ussue_1))
    issue.edit(body=f"Issue 1. Time: {CURRENT_TIME}")
    for c in issue.get_comments():
        c.delete()
    _create_or_update_comment(issue, 0, f"Issue 1 a test comment 1. Time: {CURRENT_TIME}")
    _create_or_update_comment(issue, 1, f"Issue 1 a test comment 2. Time: {CURRENT_TIME}")

    issue = github_connection._repo.get_issue(int(github_id_test_ussue_2))
    issue.edit(body=f"Issue 2. Time: {CURRENT_TIME}")

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
        assert f"Issue 1. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).description.value
        assert 2 == len(jira_connection.get_issue(jira_key).comments)
        assert f"Issue 1 a test comment 1. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[0].body.value
        assert f"Issue 1 a test comment 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[1].body.value

        jira_key = state.get_jira_issue(github_id_test_ussue_2)
        assert jira_key is not None
        assert f"Issue 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).description.value

        assert state.get_last_sync_time() is not None
        assert state.get_jira_issue(github_id_test_ussue_1) is not None
        assert state.get_jira_issue(github_id_test_ussue_2) is not None

        issue = github_connection._repo.get_issue(int(github_id_test_ussue_1))
        issue.edit(body=f"Issue 1. Updated.")
        _create_or_update_comment(issue, 0, f"Issue 1 an UPDATED test comment 1. Time: {CURRENT_TIME}")
        _create_or_update_comment(issue, 2, f"Issue 1 an NEW test comment 3. Time: {CURRENT_TIME}")

        sync_engine.sync()

        jira_key = state.get_jira_issue(github_id_test_ussue_1)
        assert jira_key is not None
        assert f"Issue 1. Updated." in jira_connection.get_issue(jira_key).description.value
        assert 3 == len(jira_connection.get_issue(jira_key).comments)
        assert f"Issue 1 an UPDATED test comment 1. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[0].body.value
        assert f"Issue 1 a test comment 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[1].body.value
        assert f"Issue 1 an NEW test comment 3. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[2].body.value

        jira_key = state.get_jira_issue(github_id_test_ussue_2)
        assert jira_key is not None
        assert f"Issue 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).description.value
