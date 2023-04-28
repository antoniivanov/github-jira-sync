import datetime

import github.Issue
import pytest

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection
from issues_sync.jira_connection import JiraConnection
from issues_sync.sync_engine import SyncEngine
from issues_sync.sync_strategy import GithubToJiraSyncStrategy
from issues_sync.utils import InMemoryState

CURRENT_TIME = datetime.datetime.now().isoformat()


from contextlib import contextmanager

def _create_or_update_comment(issue: github.Issue.Issue, comment_index: int, comment_text: str):
    comments = issue.get_comments()
    if comment_index < comments.totalCount:
        comments[comment_index].edit(comment_text)
    else:
        issue.create_comment(comment_text)


def decorate_get_issues(issues_to_return):
    def wrapper(*args, **kwargs):
        return issues_to_return

    return wrapper


class TestSyncEnd2End:

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def github_connection(self, config):
        github_connection = GithubConnection(config.github)
        yield github_connection

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

    @staticmethod
    def _setup(github_connection, jira_connection):
        issue = github_connection._repo.create_issue(title="Issue 1", body=f"Issue 1. Time: {CURRENT_TIME}")
        for c in issue.get_comments():
            c.delete()
        _create_or_update_comment(issue, 0, f"Issue 1 comment 1. Time: {CURRENT_TIME}")
        _create_or_update_comment(issue, 1, f"Issue 1 comment 2. Time: {CURRENT_TIME}")

        issue_2 = github_connection._repo.create_issue(title="Issue 2", body=f"Issue 2. Time: {CURRENT_TIME}")

        github_connection._repo.get_issues = decorate_get_issues([issue, issue_2])
        return issue, issue_2

    def test_sync(self, sync_engine, github_connection, jira_connection, sync_strategy, state):
        issue_1, issue_2 = self._setup(github_connection, jira_connection)
        github_id_test_issue_1 = str(issue_1.number)
        github_id_test_issue_2 = str(issue_2.number)

        sync_engine.sync()

        jira_key = state.get_jira_issue(github_id_test_issue_1)
        assert jira_key is not None
        assert f"Issue 1. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).description.value

        assert 2 == len(jira_connection.get_issue(jira_key).comments)
        assert f"Issue 1 comment 1. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[0].body.value
        assert f"Issue 1 comment 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[1].body.value

        jira_key = state.get_jira_issue(github_id_test_issue_2)
        assert jira_key is not None
        assert f"Issue 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).description.value

        assert state.get_last_sync_time() is not None
        assert state.get_jira_issue(github_id_test_issue_1) is not None
        assert state.get_jira_issue(github_id_test_issue_2) is not None

        issue = github_connection._repo.get_issue(int(github_id_test_issue_1))
        issue.edit(body=f"Issue 1. Updated.")
        _create_or_update_comment(issue, 0, f"Issue 1 an UPDATED test comment 1. Time: {CURRENT_TIME}")
        _create_or_update_comment(issue, 2, f"Issue 1 an NEW test comment 3. Time: {CURRENT_TIME}")

        sync_engine.sync()

        jira_key = state.get_jira_issue(github_id_test_issue_1)
        assert jira_key is not None
        assert f"Issue 1. Updated." in jira_connection.get_issue(jira_key).description.value
        assert 3 == len(jira_connection.get_issue(jira_key).comments)
        assert f"Issue 1 an UPDATED test comment 1. Time: {CURRENT_TIME}" in \
               jira_connection.get_issue(jira_key).comments[0].body.value
        assert f"Issue 1 comment 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[1].body.value
        assert f"Issue 1 an NEW test comment 3. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).comments[2].body.value

        jira_key = state.get_jira_issue(github_id_test_issue_2)
        assert jira_key is not None
        assert f"Issue 2. Time: {CURRENT_TIME}" in jira_connection.get_issue(jira_key).description.value
