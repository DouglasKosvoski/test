"""
Translation logic from TracOS format to Client format.
"""
from datetime import datetime, timezone
from integration.translators.status_mappings import map_tracos_status_to_client
from integration.types import ClientWorkorder, TracOSWorkorder


def translate_tracos_to_client(tracos_workorder: TracOSWorkorder) -> ClientWorkorder:
    """Translate a workorder from TracOS format to Client format."""

    # Map status: returns both enum value and boolean flags
    status_mapping = map_tracos_status_to_client(tracos_workorder.get("status"))
    status_enum = status_mapping.get("status")
    status_flags = status_mapping.get("flags", {})

    # Format dates as ISO strings
    created_date = _format_datetime(tracos_workorder.get("createdAt"))
    updated_date = _format_datetime(tracos_workorder.get("updatedAt"))

    # Set deletedDate if workorder is deleted
    deleted_date = (
        _format_datetime(tracos_workorder.get("updatedAt")) if tracos_workorder.get("deleted", False) else None
    )

    result = ClientWorkorder(
        orderNo=tracos_workorder.get("number"),
        isCanceled=status_flags.get("isCanceled", False),
        isDeleted=tracos_workorder.get("deleted", False),
        isDone=status_flags.get("isDone", False),
        isOnHold=status_flags.get("isOnHold", False),
        isPending=status_flags.get("isPending", False),
        summary=tracos_workorder.get("title", ""),
        creationDate=created_date,
        lastUpdateDate=updated_date,
        deletedDate=deleted_date,
    )

    # Add status enum if available
    if status_enum:
        result["status"] = status_enum

    return result


def _format_datetime(dt: datetime) -> str:
    """Format datetime object to ISO string."""
    if dt is None:
        return datetime.now(timezone.utc).isoformat()
    return dt.isoformat() if isinstance(dt, datetime) else str(dt)
