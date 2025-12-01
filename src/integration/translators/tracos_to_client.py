"""
Translation logic from TracOS format to Client format.
"""
from datetime import datetime, timezone
from integration.translators.status_mappings import (
    map_tracos_status_to_client as map_status,
)
from integration.types import ClientWorkorder, TracOSWorkorder


def translate_tracos_to_client(tracos_workorder: TracOSWorkorder) -> ClientWorkorder:
    """
    Translate a workorder from TracOS format to Client format.

    TracOS format:
    {
        '_id': ObjectId('692cf6d50b12b168f2f7cc18'),
        'number': 1,
        'status': 'completed',
        'title': 'Example workorder #1',
        'description': 'Example workorder #1 description',
        'createdAt': datetime.datetime(2025, 11, 2, 2, 0, 53, 670000),
        'updatedAt': datetime.datetime(2025, 11, 2, 3, 0, 53, 670000),
        'deleted': False
    }

    Client format:
    {
        'orderNo': 10,
        'status': 'NEW',  # Status enum value (e.g., 'NEW', 'PENDING', 'COMPLETED')
        'isCanceled': False,  # Boolean flags (backward compatibility)
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
    # Map status: returns both enum value and boolean flags
    status_mapping = map_status(tracos_workorder.get("status"))
    status_enum = status_mapping.get("status")
    status_flags = status_mapping.get("flags", {})

    # Format dates as ISO strings
    created_date = _format_datetime(tracos_workorder.get("createdAt"))
    updated_date = _format_datetime(tracos_workorder.get("updatedAt"))

    # Set deletedDate if workorder is deleted
    deleted_date = (
        _format_datetime(tracos_workorder.get("updatedAt")) if tracos_workorder.get("deleted", False) else None
    )

    result = {
        "orderNo": tracos_workorder.get("number"),
        "isCanceled": status_flags.get("isCanceled", False),
        "isDeleted": tracos_workorder.get("deleted", False),
        "isDone": status_flags.get("isDone", False),
        "isOnHold": status_flags.get("isOnHold", False),
        "isPending": status_flags.get("isPending", False),
        "summary": tracos_workorder.get("title", ""),
        "creationDate": created_date,
        "lastUpdateDate": updated_date,
        "deletedDate": deleted_date,
    }

    # Add status enum if available
    if status_enum:
        result["status"] = status_enum

    return result


def _format_datetime(dt: datetime) -> str:
    """Format datetime object to ISO string."""
    if not dt:
        return datetime.now(timezone.utc).isoformat()

    if isinstance(dt, datetime):
        return dt.isoformat()
    else:
        # If it's already a string, return as-is
        return str(dt)
