import logging

from issues_sync.file_state import InFileState
from issues_sync.finder import Finder
from issues_sync.github_connection import GithubConnection
from issues_sync.issue import BaseIssue
from issues_sync.jira_connection import JiraConnection
from issues_sync.state import State
from issues_sync.sync_strategy import SyncStrategy, GithubToJiraSyncStrategy

log = logging.getLogger(__name__)


class SyncEngine:

    def __init__(self, github: GithubConnection,
                 jira: JiraConnection,
                 sync_strategy: SyncStrategy,
                 state: State = InFileState(),
                 dry_run: bool = False) -> None:
        self._github = github
        self._jira = jira
        self._state = state
        self._finder = Finder(self._jira, self._state)
        self._sync_strategy = sync_strategy
        self._dry_run = dry_run

    def sync(self):
        log.info("Start sync ...")

        sync_time = self._state.get_last_sync_time()
        log.info(f"Last sync time: {sync_time}")
        github_issues = self._github.get_issues(sync_time)
        log.info(f"Found {len(github_issues)} github issues to sync")

        for github_issue in github_issues:
            try:
                self._sync_issue(github_issue)
            except Exception as e:
                log.error(f"Failed to sync github issue {github_issue.key}: {e}")

    def _sync_issue(self, github_issue: BaseIssue):
        log.info(f"Sync issue {github_issue.key}")
        issue_key = self._finder.find_jira_issue_key(github_issue.key, github_issue.title.value)
        if issue_key is not None:
            log.info(f"Found jira issue {issue_key} for github issue {github_issue.key}")
            self._update_jira_issue(issue_key, github_issue)
        else:
            log.info(f"Jira issue not found for github issue {github_issue.key}")
            self._create_jira_issue(github_issue)

    def _create_jira_issue(self, github_issue: BaseIssue):
        if self._dry_run:
            log.info(f"DRY RUN: Create jira issue for github issue {github_issue.key}")
            return
        try:
            issue_key = self._sync_strategy.create_jira_issue(github_issue)
            self._state.update(github_issue.key, issue_key)
        except Exception as e:
            log.error(f"Failed to create Jira issue for github issue {github_issue.key}: {e}")

    def _update_jira_issue(self, issue_key: str, github_issue: BaseIssue):
        if self._dry_run:
            log.info(f"DRY RUN: Update jira issue {issue_key} with github issue {github_issue.key}")
            return
        try:
            jira_issue = self._jira.get_issue(issue_key)
            self._sync_strategy.update(jira_issue, github_issue)
        except Exception as e:
            log.error(f"Failed to update Jira issue {issue_key} with github issue {github_issue.key}: {e}")
