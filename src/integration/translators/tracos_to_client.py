"""
Translation logic from TracOS format to Client format.
"""
from datetime import datetime
from typing import Dict, Any


def translate_tracos_to_client(tracos_workorder: Dict[str, Any]) -> Dict[str, Any]:
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
    # Map status flags based on TracOS status
    status_flags = _map_tracos_status_to_client(
        tracos_workorder.get('status', ''))

    # Format dates as ISO strings
    created_date = _format_datetime(tracos_workorder.get('createdAt'))
    updated_date = _format_datetime(tracos_workorder.get('updatedAt'))

    # Set deletedDate if workorder is deleted
    deleted_date = _format_datetime(tracos_workorder.get(
        'updatedAt')) if tracos_workorder.get('deleted', False) else None

    return {
        'orderNo': tracos_workorder.get('number'),
        'isCanceled': status_flags['isCanceled'],
        'isDeleted': tracos_workorder.get('deleted', False),
        'isDone': status_flags['isDone'],
        'isOnHold': status_flags['isOnHold'],
        'isPending': status_flags['isPending'],
        'summary': tracos_workorder.get('title', ''),
        'creationDate': created_date,
        'lastUpdateDate': updated_date,
        'deletedDate': deleted_date
    }


def _map_tracos_status_to_client(status: str) -> Dict[str, bool]:
    """Map TracOS status string to client status flags."""
    # Default all flags to False
    flags = {
        'isCanceled': False,
        'isDone': False,
        'isOnHold': False,
        'isPending': False
    }

    status_lower = status.lower()

    if status_lower == 'completed':
        flags['isDone'] = True
    elif status_lower == 'cancelled':
        flags['isCanceled'] = True
    elif status_lower == 'on_hold':
        flags['isOnHold'] = True
    elif status_lower == 'pending':
        flags['isPending'] = True
    elif status_lower == 'deleted':
        # This will be handled separately in the main function
        flags['isDeleted'] = True
    # in_progress is the default, so no flags set

    return flags


def _format_datetime(dt: datetime) -> str:
    """Format datetime object to ISO string."""
    if not dt:
        return datetime.utcnow().isoformat()

    if isinstance(dt, datetime):
        return dt.isoformat()
    else:
        # If it's already a string, return as-is
        return str(dt)
