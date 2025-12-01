"""
Status value mappings between Client and TracOS systems.

This module provides centralized mappings for status enum values
between the two systems.
"""

from typing import Dict, Optional
from integration.types import StatusMappingResult, ClientWorkorderFlags

# Mapping from Client status values to TracOS status values
CLIENT_TO_TRACOS_STATUS: Dict[str, str] = {
    'NEW': 'created',
    'PENDING': 'pending',
    'IN_PROGRESS': 'in_progress',
    'ON_HOLD': 'on_hold',
    'COMPLETED': 'completed',
    'CANCELLED': 'cancelled',
    'CANCELED': 'cancelled',  # Handle both spellings
    'DELETED': 'deleted',
}

# Mapping from TracOS status values to Client status values
TRACOS_TO_CLIENT_STATUS: Dict[str, str] = {
    'created': 'NEW',
    'pending': 'PENDING',
    'in_progress': 'IN_PROGRESS',
    'on_hold': 'ON_HOLD',
    'completed': 'COMPLETED',
    'cancelled': 'CANCELLED',
    'deleted': 'DELETED',
}

# Fallback mapping: when no status enum is present, use boolean flags
# This maintains backward compatibility with the existing flag-based system
CLIENT_FLAGS_TO_TRACOS_STATUS: Dict[str, str] = {
    'isDeleted': 'deleted',
    'isCanceled': 'cancelled',
    'isDone': 'completed',
    'isOnHold': 'on_hold',
    'isPending': 'pending',
    # Default when no flags are set
    'default': 'in_progress',
}


def map_client_status_to_tracos(status: Optional[str] = None, flags: Optional[Dict[str, bool]] = None) -> str:
    """
    Map client status to TracOS status.
    
    Priority:
    1. If status enum is provided, use direct mapping
    2. Otherwise, fall back to boolean flags mapping
    
    Args:
        status: Client status enum value (e.g., 'NEW', 'PENDING')
        flags: Dictionary of client boolean flags (e.g., {'isDone': True})
    
    Returns:
        TracOS status string (e.g., 'created', 'pending')
    """
    # First priority: use status enum if provided
    if status:
        status_upper = status.upper()
        if status_upper in CLIENT_TO_TRACOS_STATUS:
            return CLIENT_TO_TRACOS_STATUS[status_upper]
        # If status not found in mapping, log warning and fall through to flags
    
    # Second priority: use boolean flags (backward compatibility)
    if flags:
        # Check flags in priority order
        if flags.get('isDeleted', False):
            return 'deleted'
        elif flags.get('isCanceled', False):
            return 'cancelled'
        elif flags.get('isDone', False):
            return 'completed'
        elif flags.get('isOnHold', False):
            return 'on_hold'
        elif flags.get('isPending', False):
            return 'pending'
    
    # Default status
    return 'in_progress'


def map_tracos_status_to_client(status: Optional[str] = None) -> StatusMappingResult:
    """
    Map TracOS status to client format.
    
    Returns a dictionary with both:
    - status: Client status enum value (e.g., 'NEW', 'PENDING')
    - flags: Dictionary of client boolean flags for backward compatibility
    
    Args:
        status: TracOS status string (e.g., 'created', 'pending')
    
    Returns:
        Dictionary with 'status' and 'flags' keys
    """
    result = {
        'status': None,
        'flags': {
            'isCanceled': False,
            'isDone': False,
            'isOnHold': False,
            'isPending': False,
        }
    }
    
    if not status:
        return result
    
    status_lower = status.lower()
    
    # Map to client status enum
    if status_lower in TRACOS_TO_CLIENT_STATUS:
        result['status'] = TRACOS_TO_CLIENT_STATUS[status_lower]
    
    # Also set boolean flags for backward compatibility
    if status_lower == 'completed':
        result['flags']['isDone'] = True
    elif status_lower == 'cancelled':
        result['flags']['isCanceled'] = True
    elif status_lower == 'on_hold':
        result['flags']['isOnHold'] = True
    elif status_lower == 'pending':
        result['flags']['isPending'] = True
    # deleted flag is handled separately in the main translation function
    
    return result

