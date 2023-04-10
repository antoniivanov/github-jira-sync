
from abc import abstractmethod
import datetime


class State:

    @abstractmethod
    def get_jira_issue(self, github_issue_no):
        """
        Finds a Jira issue key based on a GitHub issue number
        """

    @abstractmethod
    def get_github_issue(self, jira_key):
        """
        Finds a GitHub issue num based on a Jira issue key
        """

    @abstractmethod
    def update(self, github_issue_no, jira_issue_key):
        """
        Updates the state based on a GitHub issue number and Jira issue key
        """

    @abstractmethod
    def get_last_sync_time(self) -> datetime.datetime:
        """
        Returns the last time the sync engine was run
        """

    @abstractmethod
    def update_last_sync_time(self, sync_time: datetime.datetime):
        """
        Updates the last sync time
        """

    def update_mapping_status(self, github_issue_no, jira_issue_key, status_message):
        """
        Updates the state based on a GitHub issue number and Jira issue key
        """
