"""
Translation logic from Client format to TracOS format.
"""
from datetime import datetime
from typing import Dict, Any


def translate_client_to_tracos(client_workorder: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate a workorder from Client format to TracOS format.

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

    TracOS format:
    {
        'number': 1,
        'status': 'completed',
        'title': 'Example workorder #1',
        'description': 'Example workorder #1 description',
        'createdAt': datetime.datetime(2025, 11, 2, 2, 0, 53, 670000),
        'updatedAt': datetime.datetime(2025, 11, 2, 3, 0, 53, 670000),
        'deleted': False
    }
    """
    # Map status based on client flags
    status = map_client_status_to_tracos(client_workorder)

    # Parse dates
    created_at = parse_datetime(client_workorder.get('creationDate'))
    updated_at = parse_datetime(client_workorder.get('lastUpdateDate'))

    return {
        'number': client_workorder.get('orderNo'),
        'status': status,
        'title': client_workorder.get('summary', ''),
        # Using summary as description for now
        'description': client_workorder.get('summary', ''),
        'createdAt': created_at,
        'updatedAt': updated_at,
        'deleted': client_workorder.get('isDeleted', False)
    }


def map_client_status_to_tracos(client_workorder: Dict[str, Any]) -> str:
    """Map client status flags to TracOS status string."""
    if client_workorder.get('isDeleted', False):
        return 'deleted'
    elif client_workorder.get('isCanceled', False):
        return 'cancelled'
    elif client_workorder.get('isDone', False):
        return 'completed'
    elif client_workorder.get('isOnHold', False):
        return 'on_hold'
    elif client_workorder.get('isPending', False):
        return 'pending'
    else:
        return 'in_progress'


def parse_datetime(date_string: str) -> datetime:
    """Parse ISO datetime string to datetime object."""
    if not date_string:
        return datetime.utcnow()

    try:
        # Handle different ISO formats
        if 'T' in date_string:
            # ISO format with T separator
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            # Fallback to parsing as ISO
            return datetime.fromisoformat(date_string)
    except (ValueError, AttributeError):
        # If parsing fails, return current time
        return datetime.utcnow()
