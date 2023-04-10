import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, TypeVar, Generic, Optional


class BaseIssueStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


T = TypeVar("T")


@dataclass
class BaseIssueField(Generic[T]):
    value: T
    updated_at: Optional[datetime.datetime] = None

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


@dataclass
class BaseIssueComment:
    body: BaseIssueField[str]
    user: BaseIssueField[str]
    updated_at: Optional[datetime.datetime] = None

    def __init__(self, body=None, user=None, updated_at=None):
        self.body = body if isinstance(body, BaseIssueField) else BaseIssueField(body)
        self.user = user if isinstance(user, BaseIssueField) else BaseIssueField(user)
        self.updated_at = updated_at


@dataclass
class BaseIssue:
    key: str
    project: BaseIssueField[str]
    title: BaseIssueField[str]
    description: BaseIssueField[str]
    status: BaseIssueField[BaseIssueStatus] = BaseIssueStatus.OPEN
    comments: List[BaseIssueComment] = field(default_factory=list)
    # labels: BaseIssueField[List[str]]
    updated_at: Optional[datetime.datetime] = None
    html_url: Optional[str] = ""
