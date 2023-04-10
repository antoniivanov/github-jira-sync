# GitHub-Jira Issue Sync Application

The GitHub-Jira Issue Sync can synchronize issues between a GitHub repository and a Jira project.
The application is able to retrieve issues from both platforms, compare the issues to identify which ones need to be synced,
and update issues in one platform to match changes in the other platform. 
The application can also keep track of which issues have been synced and when they were last synced.

## How it works 

The sync process in the GitHub-Jira Issue Sync Application works by comparing the issues from both platforms to identify which ones need to be synced.

The synchronization process is mostly one-directional, meaning changes made to the synced issue on Github are updated in Jira.
Currently only status is synced back to Github by this logic: 
    If the issue is closed in either Github or Jira, the issue is closed in both.  It will not be re-opened automatically.


## Installation 

To install the GitHub-Jira Issue Sync Application, you can use pip:

```bash
pip install github-jira-sync
```

## Configuration 

The GitHub-Jira Issue Sync Application can be configured using a TOML file.

```toml
[jira]
url = "https://my-jira-instance.com"
token = "my-jira-auth-token"
project = "MYPROJECT"
user = "my-jira-username"
password = "my-jira-password"

[github]
url = "https://github.com"
token = "my-github-auth-token"
project = "my-github-repo"

[system]
dry_run = true

```

## Usage 

### As a library

See main.py for example: 

```python
    config = Config("config.toml")
    github = GithubConnection(config.github)
    jira = JiraConnection(config.jira)
    update_strategy = GithubToJiraSyncStrategy(jira, github)

    sync_engine = SyncEngine(github, jira, update_strategy)
    sync_engine.sync()
```

### As a CLI 
TODO

