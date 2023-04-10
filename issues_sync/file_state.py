import datetime
import json
import os
from pathlib import Path

from issues_sync.state import State


class InFileState(State):

    def __init__(self, file: str = os.path.expanduser('~/.vdk/mapping.state.json')) -> None:
        self._state_file = Path(file)
        if self._state_file.exists():
            with self._state_file.open('r') as f:
                state_data = json.load(f)
            self._mapping_github_to_jira = state_data.get('mapping_github_to_jira', {})
            self._mapping_jira_to_github = state_data.get('mapping_jira_to_github', {})
            self._mapping_status_message = state_data.get('mapping_status_message', {})
            self._last_sync_time = datetime.datetime.fromisoformat(state_data.get('last_sync_time', '2022-01-01T00:00:00'))
        else:
            self._mapping_github_to_jira = {}
            self._mapping_jira_to_github = {}
            self._mapping_status_message = {}
            self._last_sync_time = datetime.datetime.utcnow() - datetime.timedelta(days=365)

    def get_jira_issue(self, github_issue_no):
        return self._mapping_github_to_jira.get(github_issue_no, None)

    def get_github_issue(self, jira_key):
        return self._mapping_jira_to_github.get(jira_key, None)

    def update(self, github_issue_no, jira_issue_key):
        self._mapping_github_to_jira[github_issue_no] = jira_issue_key
        self._mapping_jira_to_github[jira_issue_key] = github_issue_no
        self._save_state()

    def get_last_sync_time(self) -> datetime.datetime:
        return self._last_sync_time

    def update_last_sync_time(self, sync_time: datetime.datetime):
        self._last_sync_time = sync_time
        self._save_state()

    def _save_state(self):
        state_data = {
            'mapping_github_to_jira': self._mapping_github_to_jira,
            'mapping_jira_to_github': self._mapping_jira_to_github,
            'last_sync_time': self._last_sync_time.isoformat(),
        }
        with self._state_file.open('w') as f:
            json.dump(state_data, f, indent=4)

    def update_mapping_status(self, github_issue_no, jira_issue_key, status_message):
        self._mapping_status_message[(github_issue_no, jira_issue_key)] = status_message
        self._save_state()