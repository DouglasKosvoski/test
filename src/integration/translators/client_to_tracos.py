"""
Translation logic from Client format to TracOS format.
"""
from datetime import datetime, timezone
from integration.translators.status_mappings import map_client_status_to_tracos
from integration.types import ClientWorkorder, TracOSWorkorder


def translate_client_to_tracos(client_workorder: ClientWorkorder) -> TracOSWorkorder:
    """Translate a workorder from Client format to TracOS format."""

    # Map status: supports both enum values (e.g., 'NEW') and boolean flags
    status = map_client_status_to_tracos(
        status=client_workorder.get("status"),
        flags={
            "isDeleted": client_workorder.get("isDeleted", False),
            "isCanceled": client_workorder.get("isCanceled", False),
            "isDone": client_workorder.get("isDone", False),
            "isOnHold": client_workorder.get("isOnHold", False),
            "isPending": client_workorder.get("isPending", False),
        },
    )

    # Parse dates
    created_at = parse_datetime(client_workorder.get("creationDate"))
    updated_at = parse_datetime(client_workorder.get("lastUpdateDate"))

    return TracOSWorkorder(
        number=client_workorder.get("orderNo"),
        status=status,
        title=client_workorder.get("summary", ""),
        description=client_workorder.get("summary", ""),
        createdAt=created_at,
        updatedAt=updated_at,
        deleted=client_workorder.get("isDeleted", False),
    )


def parse_datetime(date_string: str) -> datetime:
    """Parse ISO datetime string to timezone-aware datetime object (UTC).

    Returns timezone-aware datetime objects that MongoDB will correctly
    store as ISODate objects.
    """

    if not date_string:
        return datetime.now(timezone.utc)

    try:
        # Handle different ISO formats
        if "T" in date_string:
            # ISO format with T separator
            dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        else:
            # Fallback to parsing as ISO
            dt = datetime.fromisoformat(date_string)

        # Ensure timezone-aware (UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except (ValueError, AttributeError):
        # If parsing fails, return current time (timezone-aware UTC)
        return datetime.now(timezone.utc)
