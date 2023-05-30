import datetime
import time
import uuid

import github.Issue
import pytest

from issues_sync.config import Config
from issues_sync.github_connection import GithubConnection
from issues_sync.issue import BaseIssueStatus
from issues_sync.jira_connection import JiraConnection
from issues_sync.sync_engine import SyncEngine
from issues_sync.sync_strategy import GithubToJiraSyncStrategy
from issues_sync.utils import InMemoryState

CURRENT_TIME = datetime.datetime.utcnow().isoformat()
LAST_SYNC_TIME = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)


class TestSyncEnd2EndFull:

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def github_connection(self, config):
        github_connection = GithubConnection(config.github)
        yield github_connection

    @pytest.fixture
    def jira_connection(self, config):
        return JiraConnection(config.jira)

    @pytest.fixture
    def sync_strategy(self, github_connection, jira_connection):
        return GithubToJiraSyncStrategy(jira_connection, github_connection)

    @pytest.fixture
    def state(self):
        state = InMemoryState()
        state.update_last_sync_time(LAST_SYNC_TIME)
        return state

    @pytest.fixture
    def sync_engine(self, github_connection, jira_connection, sync_strategy, state):
        return SyncEngine(github_connection, jira_connection, sync_strategy, state)

    def test_issue_created(self, sync_engine, github_connection: GithubConnection, jira_connection: JiraConnection):
        # Arrange
        # Create a new issue on GitHub only
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Title for new Issue to be created ({CURRENT_TIME})",
                                                body="Github Issue Body")

        # Act
        sync_engine.sync()

        # Assert
        jira = jira_connection._jira
        jql_query = f"""project = "{jira_connection._project}" AND summary ~ '"{github_issue.title}"' """
        jira_issue = jira.search_issues(jql_query)[0]

        # Assert the issue is created in JIRA correctly
        assert jira_issue is not None, f"JIRA issue not found: {github_issue.title}"
        assert jira_issue.fields.summary == github_issue.title, f"JIRA issue title is not with correct title: {github_issue.title}"
        assert jira_issue.fields.description.strip().startswith("Issue created by automatic sync"), f"JIRA issue description is not correct: {jira_issue.fields.description}"
        assert jira_issue.fields.description.strip().endswith(github_issue.body), f"JIRA issue description is not correct: {jira_issue.fields.description}"

    def test_existing_issue_mapping_detected(self, sync_engine, github_connection: GithubConnection,
                                   jira_connection: JiraConnection):
        # Arrange
        # Create an issue with the same title in JIRA
        same_title = f"Same Title for  Issue to be Mapped ({CURRENT_TIME})"
        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project,
                                       summary=same_title,
                                       description='Testing SyncEngine', issuetype={'name': 'Story'})

        # Create a new issue with the same title in GitHub
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=same_title,
                                                body="Github Issue Body")

        # Act
        sync_engine.sync()

        # Assert
        jira_issue = jira.issue(jira_issue.key)

        # Assert that the issue in JIRA is updated, not created
        assert jira_issue.fields.summary == same_title, f"JIRA issue title is not with correct title: {github_issue.title}"
        assert jira_issue.fields.description.strip().startswith("Issue created by automatic sync"), f"JIRA issue description is not correct: {jira_issue.fields.description}"
        assert jira_issue.fields.description.strip().endswith(github_issue.body), f"JIRA issue description is not correct: {jira_issue.fields.description}"

    def test_description_change(self, sync_engine, github_connection: GithubConnection,
                                jira_connection: JiraConnection):
        # Arrange
        # Create a new issue on GitHub and JIRA
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Description change issue Title ({CURRENT_TIME})")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project, summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()

        # Change the description on GitHub
        new_description = "Updated description"
        github_issue.edit(body=new_description)

        # Act
        sync_engine.sync()

        # Assert
        jira_issue = jira.issue(jira_issue.key)

        assert jira_issue.fields.description.strip().startswith("Issue created by automatic sync"), f"JIRA issue description is not correct: {jira_issue.fields.description}"
        assert jira_issue.fields.description.strip().endswith(new_description), f"JIRA issue description is not correct: {jira_issue.fields.description}"

    def test_title_change(self, sync_engine, github_connection: GithubConnection, jira_connection: JiraConnection):
        # Arrange
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Original title to change ({CURRENT_TIME})")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project, summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()

        # Change the title on GitHub
        github_issue.edit(title=f"Updated Title ({CURRENT_TIME})");

        # Act
        sync_engine.sync()

        # Assert
        jira_issue = jira.issue(jira_issue.key)

        assert jira_issue.fields.summary == github_issue.title, f"JIRA issue title is not with correct title: {github_issue.title}"

    def test_comment_added(self, sync_engine, github_connection: GithubConnection, jira_connection: JiraConnection):
        # Arrange
        # Create a new issue on GitHub and JIRA
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Commented Added Test Issue Title ({CURRENT_TIME})")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project, summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()

        # Add a comment on GitHub
        comment_body = "New comment"
        github_issue.create_comment(body=comment_body)

        # Act
        sync_engine.sync()

        # Assert
        jira_issue = jira.issue(jira_issue.key)

        # Assert that the comment is added in JIRA
        assert len(jira_issue.fields.comment.comments) == 1, f"JIRA issue should have 1 comment, but has {len(jira_issue.fields.comment.comments)} comments"
        assert jira_issue.fields.comment.comments[0].body.strip().endswith(f"wrote on GitHub:\n{comment_body}")

    def test_comment_edited(self, sync_engine, github_connection: GithubConnection, jira_connection: JiraConnection):
        # Arrange
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Comment edited test ({CURRENT_TIME})")
        github_issue.create_comment("Previous comment 1")
        github_issue.create_comment("Previous comment 2")

        github_comment = github_issue.create_comment("Original comment")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project, summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()
        assert len(jira.issue(jira_issue.key).fields.comment.comments) == 3

        # Edit the comment on GitHub
        new_comment_body = "Updated comment"
        github_comment.edit(body=new_comment_body)

        # Act
        sync_engine.sync()

        # Assert
        jira = jira_connection._jira
        jira_issue = jira.issue(jira_issue.key)

        assert len(jira_issue.fields.comment.comments) == 3
        assert jira_issue.fields.comment.comments[2].body.strip().endswith(f"wrote on GitHub:\n{new_comment_body}")

    def test_comment_removed(self, sync_engine, github_connection: GithubConnection, jira_connection: JiraConnection):
        # Arrange
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Commented Removed Issue Title ({CURRENT_TIME})")
        github_issue.create_comment("Comment 1")
        second_comment = github_issue.create_comment("Comment 2")
        github_issue.create_comment("Comment 3")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project,
                                       summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()
        # Remove the comment on GitHub
        second_comment.delete()

        # Act
        sync_engine.sync()

        # Assert
        jira_issue = jira.issue(jira_issue.key)

        # Assert that the comment is removed in JIRA
        assert len(jira_issue.fields.comment.comments) == 2
        assert "Comment 1" in jira_issue.fields.comment.comments[0].body
        assert "Comment 3" in jira_issue.fields.comment.comments[1].body

    def test_status_closed(self, sync_engine, github_connection: GithubConnection, jira_connection: JiraConnection):
        # Arrange
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Status Closed Issue Title ({CURRENT_TIME})")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project,
                                       summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()

        github_issue.edit(state='closed')

        # Act
        sync_engine.sync()

        # Assert
        jira_issue = jira.issue(jira_issue.key)

        # Assert that the status is changed to "Done" in JIRA
        assert jira_issue.fields.status.name == 'Done'

    def test_status_reopened_in_jira_still_closed(self, sync_engine, github_connection: GithubConnection, jira_connection: JiraConnection):
        # Arrange
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Status Reopened Issue Title ({CURRENT_TIME})")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project,
                                       summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()

        github_issue.edit(state='closed')
        sync_engine.sync()
        jira_issue = jira.issue(jira_issue.key)
        assert jira_issue.fields.status.name == 'Done'

        # Change the status to open in GitHub
        github_issue.edit(state='open')

        # Act
        sync_engine.sync()

        # Assert
        jira_issue = jira.issue(jira_issue.key)

        # Assert that the status is changed and is no longer Done.
        assert jira_issue.fields.status.name == 'Done'

    def test_jira_status_changed_but_not_closed(self, sync_engine, github_connection: GithubConnection,
                                        jira_connection: JiraConnection):
        # Arrange
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Status not changed issue Title ({CURRENT_TIME})")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project,
                                       summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()

        # Change the status to "In Review" in JIRA
        jira.transition_issue(jira_issue, 'In Progress')

        # Act
        sync_engine.sync()

        # Assert
        github_issue = github_connection.get_issue(github_issue.number)

        # Assert that the status is not changed in GitHub
        assert github_issue.status.value == BaseIssueStatus.OPEN

    def test_jira_status_changed_to_closed(self, sync_engine, github_connection: GithubConnection,
                                            jira_connection: JiraConnection):
        # Arrange
        github_repo = github_connection._repo
        github_issue = github_repo.create_issue(title=f"Jira issue closed issue Title ({CURRENT_TIME})")

        jira = jira_connection._jira
        jira_issue = jira.create_issue(project=jira_connection._project,
                                       summary=github_issue.title, issuetype={'name': 'Story'})

        sync_engine.sync()

        # Change the status to "Done" in JIRA
        jira.transition_issue(jira_issue, 'Done')

        # Act
        sync_engine.sync()

        # Assert
        github_issue = github_connection.get_issue(github_issue.number)

        # Assert that the status is changed to "closed" in GitHub
        assert github_issue.status.value == BaseIssueStatus.CLOSED
