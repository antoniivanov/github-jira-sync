import logging
import os
from dataclasses import dataclass, fields
from typing import List

import toml

log = logging.getLogger(__name__)


@dataclass
class JiraConfig:
    url: str
    token: str
    project: str
    user: str
    password: str


@dataclass
class GithubConfig:
    url: str
    token: str
    project: str


class Config:

    def __init__(self, file: str = 'config.toml'):
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
