import logging

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection
from issues_sync.jira_connection import JiraConnection
from issues_sync.sync_engine import SyncEngine
from issues_sync.sync_strategy import GithubToJiraSyncStrategy

if not logging.root.handlers:
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

log = logging.getLogger(__name__)


def main():
    config = Config()
    github = GithubConnection(config.github)
    jira = JiraConnection(config.jira)
    update_strategy = GithubToJiraSyncStrategy(jira, github)

    sync_engine = SyncEngine(github, jira, update_strategy)
    sync_engine.sync()


if __name__ == '__main__':
    main()
