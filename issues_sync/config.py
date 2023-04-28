import logging
import os
from dataclasses import dataclass, fields
from typing import List, Optional

import toml

log = logging.getLogger(__name__)


@dataclass
class JiraConfig:
    url: str
    project: str
    token: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None


@dataclass
class GithubConfig:
    url: str
    project: str
    token: Optional[str] = None


class Config:

    def __init__(self, file: str = None):
        if file is None:
            file = self._find_config_file()
        log.info(f"Using config file {file}")
        config = self._load(file)
        self.jira = JiraConfig(**self._get_config("jira", config, [f.name for f in fields(JiraConfig)]))
        self.github = GithubConfig(**self._get_config("github", config, [f.name for f in fields(GithubConfig)]))
        self.dry_run = config.get("system", {}).get("dry_run", False)

    @staticmethod
    def _load(file: str) -> dict:
        with open(file, 'r') as f:
            return toml.load(f)

    @staticmethod
    def _get_config(section: str, file_config: dict, field_names: List[str]):

        final_config = dict(url=None, token=None, project=None)
        if section in file_config:
            for field in field_names:
                final_config[field] = file_config[section].get(field)

        for key in final_config:
            env_var = os.getenv(f"{section}_{key}".upper())
            if env_var is not None:
                final_config[key] = env_var

        return final_config

    def _find_config_file(self):
        possible_file_locations = [
            "config.toml",
            os.path.join(os.getcwd(), "config.toml"),
            os.path.join(os.path.expanduser("~"), '.github-jira-sync', "config.toml"),
            os.path.join(os.path.expanduser("~"), "config.toml"),
            "../config.toml",
        ]
        for file in possible_file_locations:
            if os.path.isfile(file):
                return file
        raise FileNotFoundError("No config file found. Please create a config.toml or config.toml.example file.")
