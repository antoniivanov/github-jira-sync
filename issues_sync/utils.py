import datetime
import typing

from issues_sync.state import State


class InMemoryState(State):

    def __init__(self) -> None:
        self._mapping_github_to_jira = {}
        self._mapping_jira_to_github = {}
        self._mapping_status_message = {}
        self._last_sync_time = datetime.datetime.utcnow() - datetime.timedelta(days=30)

    def get_jira_issue(self, github_issue_no: str):
        return self._mapping_github_to_jira.get(str(github_issue_no), None)

    def get_github_issue(self, jira_key):
        return self._mapping_jira_to_github.get(jira_key, None)

    def update(self, github_issue_no, jira_issue_key):
        self._mapping_github_to_jira[github_issue_no] = jira_issue_key
        self._mapping_jira_to_github[jira_issue_key] = github_issue_no

    def get_last_sync_time(self) -> datetime.datetime:
        return self._last_sync_time

    def update_last_sync_time(self, sync_time: datetime.datetime):
        self._last_sync_time = sync_time

    def update_mapping_status(self, github_issue_no, jira_issue_key, status_message):
        self._mapping_status_message[(github_issue_no, jira_issue_key)] = status_message


def apply_decorator(obj: typing.Any, method: typing.Callable, decorator):
    """
    Apply the given decorator to the given method of the given object.
    """
    new_method = decorator(method)
    setattr(obj, method.__name__, new_method)

