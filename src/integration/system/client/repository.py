"""
Client repository for reading and validating Client workorders.
"""

import json
from os import path
from datetime import datetime
from typing import Optional, List

from loguru import logger  # pyright: ignore[reportMissingImports]

from adapters.filesystem import (
    list_json_files_in_directory,
    read_json_from_file,
)
from integration.types import ClientWorkorder


class ClientRepository:
    def find_workorders(self, directory_path: str) -> List[dict]:
        """Load all JSON workorders from a directory, skipping corrupted files."""
        logger.debug(f"Loading Client workorders from '{directory_path}'")

        workorders = []
        json_files = list_json_files_in_directory(directory_path)

        for filename in json_files:
            file_path = path.join(directory_path, filename)

            try:
                data = read_json_from_file(file_path)
                workorders.append(data)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in file: '{filename}'")
            except PermissionError:
                logger.error(f"Permission denied reading file: '{filename}'")

        return workorders

    def is_iso_datetime(self, value: str) -> bool:
        """Return True if the given string is a valid ISO datetime."""
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

    def validate_workorder(self, workorder: dict) -> Optional[ClientWorkorder]:
        """
        Validate a Client workorder according to the expected schema.
        Returns a dict if valid, otherwise None.
        """

        schema = {
            "orderNo": int,
            "isCanceled": bool,
            "isDeleted": bool,
            "isDone": bool,
            "isOnHold": bool,
            "isPending": bool,
            "summary": str,
            "creationDate": "iso-datetime",
            "lastUpdateDate": "iso-datetime",
            "deletedDate": "iso-datetime-or-none-when-deleted",
        }

        validated = {}

        for field, rule in schema.items():
            value = workorder.get(field)

            if field not in workorder:
                logger.warning(f"Workorder missing required field: {field}")
                return None

            if rule == "iso-datetime":
                if not (isinstance(value, str) and self.is_iso_datetime(value)):
                    logger.warning(f"Field '{field}' must be a valid ISO datetime string")
                    return None

            elif rule == "iso-datetime-or-none-when-deleted":
                is_deleted = workorder.get("isDeleted", False)

                if is_deleted:
                    if value is not None and not (isinstance(value, str) and self.is_iso_datetime(value)):
                        logger.warning(f"Field '{field}' must be ISO datetime string or None when deleted")
                        return None
                else:
                    if value is not None:
                        logger.warning(f"Field '{field}' must be None when workorder is not deleted")
                        return None

            elif not isinstance(value, rule):
                logger.warning(f"Field '{field}' must be of type {rule}")
                return None

            validated[field] = value

        return validated
