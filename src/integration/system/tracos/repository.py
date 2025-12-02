"""
TracOS repository for MongoDB workorder operations.

Handles CRUD-like operations for workorders stored in the TracOS MongoDB:
- Fetching unsynced workorders
- Inserting or updating entries
- Marking workorders as synced
"""
from datetime import datetime, timezone
from os import getenv
import json
from typing import AsyncGenerator, Optional

from bson import ObjectId
from loguru import logger
from pymongo.errors import PyMongoError

from adapters.db import get_connection, get_collection
from integration.types import TracOSWorkorder


class TracOSRepository:
    async def _collection(self):
        """Return the MongoDB collection safely."""
        database = await get_connection()
        return get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

    async def find_all_unsynced_workorders(self) -> AsyncGenerator[TracOSWorkorder, None]:
        """Yield every workorder where isSynced != True."""
        try:
            collection = await self._collection()
            cursor = collection.find({"isSynced": {"$ne": True}})

            async for doc in cursor:
                yield doc

        except ConnectionError:
            logger.error("Connection error fetching unsynced workorders")
            raise
        except PyMongoError as exc:
            logger.error(f"Error fetching unsynced workorders: {exc}")
            return

    async def get_workorder_by_number(self, number: int) -> Optional[TracOSWorkorder]:
        """Retrieve a workorder by its number."""
        try:
            collection = await self._collection()
            workorder = await collection.find_one({"number": number})

            if not workorder:
                logger.debug(f"Workorder {number} not found")
                return None

            return TracOSWorkorder(**workorder)

        except ConnectionError:
            logger.error("Connection error getting workorder by number")
            raise

    async def insert_workorder(self, workorder: TracOSWorkorder) -> bool:
        """Insert a new workorder."""
        number = workorder.get("number", "unknown")

        try:
            collection = await self._collection()
            await collection.insert_one(workorder)
            logger.debug(f"Inserted workorder {number}")
            return True

        except ConnectionError:
            logger.error("Connection error inserting workorder")
            raise
        except PyMongoError as exc:
            logger.error(f"Insert failed for {number}: {exc}")
            return False

    async def update_workorder(self, workorder_id: ObjectId, workorder: TracOSWorkorder) -> bool:
        """Update an existing workorder by ID."""
        try:
            collection = await self._collection()
            await collection.update_one({"_id": workorder_id}, {"$set": workorder})
            logger.debug(f"Updated workorder {workorder_id}")
            return True

        except ConnectionError:
            logger.error("Connection error updating workorder")
            raise
        except PyMongoError as exc:
            logger.error(f"Update failed ({workorder_id}): {exc}")
            return False

    async def save_workorder(self, workorder: TracOSWorkorder) -> bool:
        """Insert or update based on workorder.number."""
        number = workorder.get("number")

        try:
            existing = await self.get_workorder_by_number(number)

            if not existing:
                return await self.insert_workorder(workorder)

            if not self.should_update_workorder(existing, workorder):
                logger.debug(f"Workorder {number} is up-to-date, no changes to be made")
                return True

            merged = {**existing, **workorder}
            return await self.update_workorder(existing["_id"], merged)

        except ConnectionError:
            logger.error("Connection error saving workorder")
            raise
        except PyMongoError as exc:
            logger.error(f"Save failed for {number}: {exc}")
            return False

    async def mark_workorder_as_synced(self, number: int) -> bool:
        """Set isSynced = True and syncedAt = now."""
        try:
            collection = await self._collection()
            result = await collection.update_one(
                {"number": number},
                {"$set": {"isSynced": True, "syncedAt": datetime.now(timezone.utc)}},
            )

            if result.modified_count:
                logger.debug(f"Marked {number} as synced")
                return True

            logger.warning(f"Workorder {number} not updated as synced")
            return False

        except ConnectionError:
            raise
        except PyMongoError as exc:
            logger.error(f"Sync update failed for {number}: {exc}")
            return False

    def _normalize_datetime(self, dt: datetime) -> datetime:
        """Normalize datetime to UTC and truncate to seconds for comparison."""
        if dt is None:
            return None

        if not isinstance(dt, datetime):
            return dt

        # Treat naive datetimes as UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Truncate microseconds for comparison tolerance
        return dt.replace(microsecond=0)

    def _values_equal(self, old_value, new_value) -> bool:
        """Compare values with special handling for datetimes."""
        if isinstance(old_value, datetime) and isinstance(new_value, datetime):
            return self._normalize_datetime(old_value) == self._normalize_datetime(new_value)

        return old_value == new_value

    def diff_workorders(
        self,
        existing: TracOSWorkorder,
        incoming: TracOSWorkorder,
    ) -> dict:
        """
        Return a dict describing which fields differ between existing and incoming.
        Includes: {field: {"before": x, "after": y}}
        Ignores metadata fields.
        """
        ignored = {"_id", "isSynced", "syncedAt"}
        changes = {}

        for key, new_value in incoming.items():
            if key in ignored:
                continue

            old_value = existing.get(key)
            if not self._values_equal(old_value, new_value):
                changes[key] = {"before": old_value, "after": new_value}

        return changes

    def should_update_workorder(
        self,
        existing: TracOSWorkorder,
        incoming: TracOSWorkorder,
    ) -> bool:
        """Return True if any relevant field differs."""
        changes = self.diff_workorders(existing, incoming)

        if changes:
            logger.debug(
                f"Workorder {existing.get('number')} should be updated. Changes: {json.dumps(changes, indent=2)}"
            )
            return True

        return False

    def validate_workorder(self, workorder: dict) -> bool:
        """Validate required fields for TracOS format."""
        required = {"number", "status", "title", "description", "createdAt", "updatedAt", "deleted"}

        missing = [f for f in required if workorder.get(f) is None]

        if missing:
            logger.warning(f"Missing fields: {missing}")
            return False

        return True
