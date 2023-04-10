import datetime
import logging
from typing import Optional, List

import github.Issue

from issues_sync.config import GithubConfig
from issues_sync.issue import BaseIssue, BaseIssueField, BaseIssueComment, BaseIssueStatus

log = logging.getLogger(__name__)


def convert_to_base_issue(github_issue: github.Issue.Issue) -> BaseIssue:
    id = str(github_issue.number)
    project = BaseIssueField(github_issue.repository.name, github_issue.repository.updated_at)
    title = BaseIssueField(github_issue.title, github_issue.updated_at)
    description = BaseIssueField(github_issue.body, github_issue.updated_at)
    comments = []
    for github_comment in github_issue.get_comments():
        body = BaseIssueField(github_comment.body, github_comment.updated_at)
        user = BaseIssueField(github_comment.user.login, github_comment.user.updated_at)
        comment = BaseIssueComment(body, user, github_comment.updated_at)
        comments.append(comment)
    updated_at = github_issue.updated_at
    status = BaseIssueField(BaseIssueStatus(github_issue.state.upper()), github_issue.updated_at)
    html_url = github_issue.html_url
    return BaseIssue(id, project, title, description, status, comments, updated_at, html_url)


class GithubConnection:

    def __init__(self, config: GithubConfig) -> None:
        g = github.Github(config.token)
        self._repo = g.get_repo(config.project)

    def find_issue_id_by_title(self, issue_title) -> Optional[str]:
        issues = self._repo.get_issues(state="all")
        for issue in issues:
            if issue.title == issue_title:
                return str(issue.number)
        return None

    def get_issues(self, since_time: datetime.datetime) -> List[BaseIssue]:
        github_issues = self._repo.get_issues(since=since_time)
        result = []
        for github_issue in github_issues:
            if github_issue.pull_request is not None:
                continue
            # issue = Issue(title=github_issue.title,
            #               body=github_issue.body,
            #               comments=self._get_comments(github_issue),
            #               updated_at=github_issue.updated_at)
            result.append(convert_to_base_issue(github_issue))
        log.info(f"Found {len(result)} github issues to sync")
        return result

    def get_issue(self, issue_number) -> BaseIssue:
        return convert_to_base_issue(self._repo.get_issue(int(issue_number)))

    def update_issue(self, issue: BaseIssue):
        github_issue = self._repo.get_issue(int(issue.key))
        if issue.status.value == BaseIssueStatus.OPEN and github_issue.state == "closed":
            github_issue.edit(state="open")
        if issue.status.value == BaseIssueStatus.CLOSED and github_issue.state == "open":
            github_issue.edit(state="closed")
        if issue.title.value != github_issue.title:
            github_issue.edit(title=issue.title.value)
        if issue.description.value != github_issue.body:
            github_issue.edit(body=issue.description.value)

        for index, comment in enumerate(github_issue.get_comments()):
            if comment.body != issue.comments[index].body.value:
                comment.edit(body=issue.comments[index].body.value)
        if github_issue.get_comments().totalCount < len(issue.comments):
            for comment in issue.comments[github_issue.get_comments().totalCount:]:
                github_issue.create_comment(comment.body.value)

    def create_issue(self, issue: BaseIssue) -> str:
        github_issue = self._repo.create_issue(title=issue.title.value,
                                               body=issue.description.value)
        for comment in issue.comments:
            github_issue.create_comment(comment.body.value)
        return str(github_issue.number)