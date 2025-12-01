# Read JSON from inbound, write to outbound
from loguru import logger  # pyright: ignore[reportMissingImports]
from adapters.filesystem import list_json_files_in_directory, read_json_from_file
from os import path
from pathlib import Path
from datetime import datetime
from typing import Optional
from integration.types import ClientWorkorder


class ClientRepository:
    def __init__(self):
        pass

    def find_workorders(self, directory_path: str):
        logger.debug(f"Getting workorders from '{directory_path}'")

        workorders = []

        json_files = list_json_files_in_directory(directory_path)

        for file in json_files:
            json_file_path = path.join(directory_path, file)
            workorders.append(read_json_from_file(json_file_path))

        return workorders


    def is_iso_datetime(self, value: str) -> bool:
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

    def validate_workorder(self, workorder: dict) -> Optional[ClientWorkorder]:
        """Validate a workorder from Client format."""

        expected_format = {
            "orderNo": int,
            "isCanceled": bool,
            "isDeleted": bool,
            "isDone": bool,
            "isOnHold": bool,
            "isPending": bool,
            "summary": str,
            "creationDate": str, # Datetime fields come as ISO strings from JSON
            "lastUpdateDate": str, # Datetime fields come as ISO strings from JSON
            "deletedDate": str if workorder.get('isDeleted', False) else type(None), # Optional datetime field
        }

        validated_workorder = {}

        for field, expected_type in expected_format.items():
            if field not in workorder:
                logger.warning(f"Workorder missing required field: {field}")
                return None

            # Special validation for datetime fields
            if field in ['creationDate', 'lastUpdateDate'] and workorder[field] is not None:
                if not isinstance(workorder[field], str) or not self.is_iso_datetime(workorder[field]):
                    logger.warning(f"Workorder field {field} is not a valid ISO datetime string")
                    return None
            elif field == 'deletedDate':
                if workorder.get('isDeleted', False):
                    if workorder[field] is not None and (not isinstance(workorder[field], str) or not self.is_iso_datetime(workorder[field])):
                        logger.warning(f"Workorder field {field} is not a valid ISO datetime string or None")
                        return None
                else:
                    if workorder[field] is not None:
                        logger.warning(f"Workorder field {field} should be None when not deleted")
                        return None

            # Skip type check for datetime fields since we handled them above
            if field in ['creationDate', 'lastUpdateDate', 'deletedDate']:
                validated_workorder[field] = workorder[field]
                continue

            if not isinstance(workorder[field], expected_type):
                logger.warning(f"Workorder field {field} is not of type {expected_type}")
                return None

            validated_workorder[field] = workorder[field]

        return validated_workorder