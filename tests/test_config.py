import os
from unittest import mock
import pytest
import tempfile

from issues_sync.config import Config

@pytest.fixture()
def config_file():
    # Create a temporary file with some config data
    config_data = '''
[jira]
url = "https://my-jira-instance.com"
token = "my-token"
project = "VDK"

[github]
url = "https://api.github.com"
token = "my-github-token"
project = "vmware/versatile-data-kit"
'''
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(config_data)
        f.flush()
        yield f.name
    # Remove the temporary file after the test is finished
    os.remove(f.name)

def test_load_config(config_file):
    # Create an instance of the Config class
    config = Config(config_file)

    # Check that the config was loaded correctly
    assert config.jira.url == 'https://my-jira-instance.com'
    assert config.jira.token == 'my-token'
    assert config.jira.project == 'VDK'
    assert config.github.url == 'https://api.github.com'
    assert config.github.token == 'my-github-token'
    assert config.github.project == 'vmware/versatile-data-kit'


def test_override_config_with_env_vars(config_file):

    with mock.patch.dict(
                os.environ,
                {
                    "JIRA_TOKEN": "my-new-jira-token",
                    "GITHUB_TOKEN": 'my-new-github-token',
                },
            ):
        config = Config(config_file)
        # Check that the config was overridden correctly
        assert config.jira.token == 'my-new-jira-token'
        assert config.github.url == 'https://api.github.com'
        assert config.github.token == 'my-new-github-token'
