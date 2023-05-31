import abc
import copy
from typing import List

from issues_sync.github_connection import GithubConnection
from issues_sync.issue import BaseIssue, BaseIssueStatus, BaseIssueComment
from issues_sync.jira_connection import JiraConnection


class SyncStrategy(abc.ABC):
    """Base class for update strategies."""

    @abc.abstractmethod
    def update(self, jira_issue: BaseIssue, github_issue: BaseIssue) -> None:
        """
        Updates jira or github issue based on the strategy.
        """

    @abc.abstractmethod
    def create_jira_issue(self, github_issue: BaseIssue) -> str:
        """
        Creates a Jira issue based on a GitHub issue.
        :return: Jira issue key that was created
        """


class GithubToJiraSyncStrategy(SyncStrategy):
    """Sync strategy for one direction sync."""

    def __init__(self, jira_connection: JiraConnection, github_connection: GithubConnection) -> None:
        self._jira_connection = jira_connection
        self._github_connection = github_connection

    def update(self, jira_issue: BaseIssue, github_issue: BaseIssue) -> None:
        setattr(github_issue, "change_detected", False);
        self._update_issue_fields(jira_issue, github_issue)
        self._update_comments(jira_issue, github_issue)
        self._jira_connection.update_issue(jira_issue)
        if getattr(github_issue, "change_detected"):
            self._github_connection.update_issue(github_issue)

    def _update_issue_fields(self, jira_issue: BaseIssue, github_issue: BaseIssue):
        jira_issue.description.value = f"""
Issue created by automatic sync. 
Original URL: {github_issue.html_url}

Do not edit this issue manually as the sync is one direction. 
Only status and labels can be changed.
--------------------------------------------------------- ---
{github_issue.description.value}"""
        jira_issue.title = github_issue.title

        if github_issue.status.value != jira_issue.status.value:
            # when conflict we always pick latest in the cycle
            # since currently we have 2 phases (open and closed) , closed is always the latest.
            if github_issue.status.value != BaseIssueStatus.CLOSED:
                setattr(github_issue, "change_detected", True)
            jira_issue.status.value = BaseIssueStatus.CLOSED
            github_issue.status.value = BaseIssueStatus.CLOSED

    @staticmethod
    def _update_comments(jira_issue: BaseIssue, github_issue: BaseIssue):
        github_comments = github_issue.comments
        new_comments: List[BaseIssueComment] = []
        for github_comment in github_comments:
            body = f"""
{github_comment.user.value} wrote on GitHub:
{github_comment.body.value}
            """
            new_comments.append(BaseIssueComment(body, github_comment.user, github_comment.updated_at))
        jira_issue.comments = new_comments

    def create_jira_issue(self, github_issue: BaseIssue) -> str:
        jira_issue = copy.deepcopy(github_issue)
        jira_issue.key = None
        self._update_issue_fields(jira_issue, github_issue)
        self._update_comments(jira_issue, github_issue)
        return self._jira_connection.create_issue(jira_issue)
