"""
Type definitions for workorder data structures.

This module provides TypedDict definitions for type-safe
workorder handling between Client and TracOS systems.
"""

from datetime import datetime
from typing import TypedDict, Optional


class ClientWorkorderFlags(TypedDict):
    """Boolean status flags used in Client workorder format."""

    isCanceled: bool
    isDeleted: bool
    isDone: bool
    isOnHold: bool
    isPending: bool


class ClientWorkorder(TypedDict):
    """
    Workorder format used by the Client system.

    Example:
    {
        'orderNo': 10,
        'status': 'NEW',
        'isCanceled': False,
        'isDeleted': False,
        'isDone': False,
        'isOnHold': False,
        'isPending': False,
        'summary': 'Example workorder #10',
        'creationDate': '2025-11-11T02:00:53.697748+00:00',
        'lastUpdateDate': '2025-11-11T03:00:53.697748+00:00',
        'deletedDate': None
    }
    """

    orderNo: int
    status: Optional[str]
    isCanceled: bool
    isDeleted: bool
    isDone: bool
    isOnHold: bool
    isPending: bool
    summary: str
    creationDate: str
    lastUpdateDate: str
    deletedDate: Optional[str]


class TracOSWorkorder(TypedDict):
    """
    Workorder format used by the TracOS system (MongoDB).

    Example:
    {
        'number': 1,
        'status': 'completed',
        'title': 'Example workorder #1',
        'description': 'Example workorder #1 description',
        'createdAt': datetime(2025, 11, 6, 17, 20, 19, 867000),
        'updatedAt': datetime(2025, 11, 6, 17, 20, 19, 867000),
        'deleted': False
    }
    """

    number: int
    status: str
    title: str
    description: str
    createdAt: datetime
    updatedAt: datetime
    deleted: bool


class StatusMappingResult(TypedDict):
    """Result of mapping TracOS status to Client format."""

    status: Optional[str]
    flags: ClientWorkorderFlags
