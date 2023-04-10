import logging
from typing import Optional

from jira import JIRA, JIRAError, Issue
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception

from issues_sync.config import JiraConfig
from issues_sync.issue import BaseIssue, BaseIssueComment, BaseIssueField, BaseIssueStatus

log = logging.getLogger(__name__)


def jira_retry(func):
    return retry(stop=stop_after_attempt(3),
                 wait=wait_fixed(5000),
                 retry=retry_if_exception(lambda e: isinstance(e, JIRAError) and e.status_code >= 500),
                 reraise=False)(func)


class JiraConnection:

    def __init__(self, config: JiraConfig) -> None:
        # Connect to Jira
        if config.user and config.password:
            log.info(f"Connecting to Jira with user {config.user}")
            self._jira = JIRA(config.url, basic_auth=(config.user, config.password))
        elif config.token:
            log.info("Connecting to Jira with token.")
            self._jira = JIRA(config.url, token_auth=config.token)
        else:
            log.info("Connecting to Jira without authentication.")
            self._jira = JIRA(config.url)

        self._project = config.project
        self._done_statuses = ("done", "closed", "resolved", "fixed")

    def _convert_to_base_issue(self, jira_issue: Issue) -> BaseIssue:
        id = str(jira_issue.key)
        project = BaseIssueField(jira_issue.fields.project.name, jira_issue.fields.updated)
        title = BaseIssueField(jira_issue.fields.summary, jira_issue.fields.updated)
        description = BaseIssueField(jira_issue.fields.description, jira_issue.fields.updated)
        comments = []
        for jira_comment in jira_issue.fields.comment.comments:
            body = BaseIssueField(jira_comment.body, jira_comment.updated)
            user = BaseIssueField(jira_comment.author.displayName, jira_comment.updated)
            comment = BaseIssueComment(body, user, jira_comment.updated)
            comments.append(comment)
        updated_at = jira_issue.fields.updated

        # TODO jira supports custom status, so this should be configurable
        if jira_issue.fields.status.name.lower() in self._done_statuses:
            status = BaseIssueField(BaseIssueStatus.CLOSED, jira_issue.fields.updated)
        else:
            status = BaseIssueField(BaseIssueStatus.OPEN, jira_issue.fields.updated)
        html_url = f"{self._jira._options['server']}/browse/{jira_issue.key}"
        return BaseIssue(id, project, title, description, status, comments, updated_at, html_url)

    @jira_retry
    def find_issue_id_by_title(self, issue_title: str) -> Optional[str]:
        """
        Finds a Jira issue based on a issue title
        """
        issue_title = issue_title.replace("'", "\\'")
        issue_title = issue_title.replace('"', '\\\\"')

        jql_query = f"""project = "{self._project}" AND summary ~ '"{issue_title}"' """

        log.info(f"Searching for issue with query {jql_query}")
        issues = self._jira.search_issues(jql_query)

        if issues:
            return issues[0].key

        return None

    @jira_retry
    def get_issue(self, issue_key: str) -> BaseIssue:
        issue = self._jira.issue(issue_key)
        return self._convert_to_base_issue(issue)

    @jira_retry
    def create_issue(self, issue: BaseIssue) -> str:
        log.info(f"Creating issue {issue}")

        fields = {
            "project": {"key": issue.project.value},
            "summary": issue.title.value,
            "description": issue.description.value,
            "status": {"name": "New"},
            "issuetype": {"name": "Story"},
        }

        issue = self._jira.create_issue(fields=fields)
        return issue.key

    @jira_retry
    def update_issue(self, issue: BaseIssue) -> None:
        log.info(f"Updating issue {issue.key} with {issue}")

        jira_issue = self._jira.issue(issue.key)
        fields = {
            "summary": issue.title.value,
            "description": issue.description.value,
        }
        jira_issue.update(fields=fields, jira=self._jira)

        self._update_comments(jira_issue, issue)

        status = None
        if issue.status.value == BaseIssueStatus.CLOSED and jira_issue.fields.status.name.lower() not in self._done_statuses:
            status = "Done"
        elif issue.status.value == BaseIssueStatus.OPEN and jira_issue.fields.status.name.lower() in self._done_statuses:
            status = "new"
        if status:
            self._jira.transition_issue(jira_issue.key, status)

    def _update_comments(self, jira_issue: Issue, issue: BaseIssue) -> None:
        # Get all existing comments from Jira
        jira_comments = jira_issue.fields.comment.comments
        base_comments = issue.comments

        jira_index = 0
        base_index = 0
        while jira_index < len(jira_comments) and base_index < len(base_comments):
            jira_comment = jira_comments[jira_index]
            base_comment = base_comments[base_index]

            body = self._get_comment_body(base_comment)
            fields = {
                "body": body
            }
            jira_comment.update(fields=fields, jira=self._jira)

            jira_index += 1
            base_index += 1

        if base_index < len(base_comments):
            # Add new comments
            for base_comment in base_comments[base_index:]:
                body = self._get_comment_body(base_comment)
                self._jira.add_comment(jira_issue.key, body)

        # TODO: what if we have less github comments than jira comments?
        # if jira_index < len(jira_comments):

    @staticmethod
    def _get_comment_body(base_comment):
        if base_comment.user is not None:
            body = f"{base_comment.user.value} wrote:\n{base_comment.body.value}"
        else:
            body = base_comment.body.value
        return body
