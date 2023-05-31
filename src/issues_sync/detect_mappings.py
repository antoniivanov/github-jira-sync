import logging
from datetime import datetime, timedelta

import click

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection
from issues_sync.jira_connection import JiraConnection

if not logging.root.handlers:
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

log = logging.getLogger(__name__)


@click.command()
@click.argument('output_file', type=click.File('w'), default='mappings.csv')
def detect_mappings(output_file):
    config = Config()
    github = GithubConnection(config.github)
    jira = JiraConnection(config.jira)

    github_issues = github.get_issues(datetime.now() - timedelta(days=30 * 365))
    log.info(f"Found {len(github_issues)} github issues.")

    mappings = dict()

    for github_issue in github_issues:
        issue_key = jira.find_issue_id_by_title(github_issue.title.value)
        if issue_key is not None:
            if github_issue.key in mappings:
                log.warning(f"Duplicate github issue: {github_issue.key} to {issue_key}")
                continue
            mappings[github_issue.key] = issue_key
            issue = jira.get_issue(issue_key)
            output_file.write(f"{github_issue.key}, {issue_key}, {github_issue.title}, {issue.title} \n")
        else:
            log.info(f"Jira issue not found for github issue {github_issue.key} {github_issue.title}")


if __name__ == '__main__':
    detect_mappings()
