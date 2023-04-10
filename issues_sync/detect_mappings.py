from datetime import datetime, timedelta

import click

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection
from issues_sync.jira_connection import JiraConnection


@click.command()
@click.argument('output_file', type=click.File('w'))
def detect_mappings(output_file):
    config = Config()
    github = GithubConnection(config.github)
    jira = JiraConnection(config.jira)

    github_issues = github.get_issues(datetime.now() - timedelta(days=30 * 365))

    for github_issue in github_issues:
        issue_key = jira.find_issue_id_by_title(github_issue.title)
        if issue_key is not None:
            output_file.write(f"{github_issue.number}, {issue_key}\n")


if __name__ == '__main__':
    detect_mappings()
