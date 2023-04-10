from issues_sync.jira_connection import JiraConnection
from issues_sync.state import State


class Finder:

    def __init__(self, jira_connection: JiraConnection, state: State) -> None:
        self._jira_connection = jira_connection
        self._state = state

    def find_jira_issue_key(self, github_issue_no, github_issue_title):
        """
        Finds a Jira issue based on a GitHub issue number and title
        """
        jira_issue_key = self._state.get_jira_issue(github_issue_no)
        if jira_issue_key:
            return jira_issue_key

        jira_issue_key = self._jira_connection.find_issue_id_by_title(github_issue_title)
        if jira_issue_key:
            self._state.update(github_issue_no, jira_issue_key)
            return jira_issue_key

        return None

