# CRUD operations on TracOS (MongoDB)
from loguru import logger  # pyright: ignore[reportMissingImports]
from typing import AsyncGenerator, Optional
from adapters.db import get_connection, get_collection
from os import getenv
from datetime import datetime, timezone
from integration.types import TracOSWorkorder
from pymongo.errors import PyMongoError


class TracOSRepository:
    def __init__(self):
        pass

    async def save_workorder(self, workorder: TracOSWorkorder) -> bool:
        """Save a workorder to the database."""
        workorder_number = workorder.get("number", "unknown")

        try:
            database = await get_connection()
            collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

            # Check if workorder with this number already exists
            existing = await collection.find_one({"number": workorder.get("number")})
            if existing:
                should_update = self.should_update_workorder(existing, workorder)
                if not should_update:
                    logger.debug(f"Workorder {workorder_number} already exists with no changes")
                    return True

                # Update existing workorder, preserving the _id
                updated_workorder = {
                    **existing,
                    **workorder
                }

                await collection.update_one(
                    {"number": workorder.get("number")},
                    {"$set": updated_workorder}
                )

                logger.debug(f"Updated workorder {workorder_number}")
                return True

            # Insert the workorder
            await collection.insert_one(workorder)
            logger.debug(f"Saved workorder {workorder_number}")

            return True
        except ConnectionError:
            # Re-raise connection errors to be handled at a higher level
            raise
        except PyMongoError:
            logger.error(f"Database error while saving workorder {workorder_number}")
            return False

    def should_update_workorder(self, existing: dict, workorder: dict) -> bool:
        """Check if a workorder should be updated.
        
        Compares all fields except _id to determine if any changes exist.
        Returns True if any field has been modified, False otherwise.
        """
        # Create copies without _id for comparison
        existing_copy = {k: v for k, v in existing.items() if k != "_id"}
        workorder_copy = {k: v for k, v in workorder.items() if k != "_id"}
        
        # Get all unique keys from both dictionaries
        all_keys = set(existing_copy.keys()) | set(workorder_copy.keys())
        
        # Compare each field
        for key in all_keys:
            existing_value = existing_copy.get(key)
            workorder_value = workorder_copy.get(key)
            
            # If values differ, update is needed
            if existing_value != workorder_value:
                return True
        
        # No differences found
        return False


    async def find_all_unsynced_workorders(self) -> AsyncGenerator[TracOSWorkorder, None]:
        """Find all unsynced workorders in the database."""
        try:
            database = await get_connection()
            collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

            query = {
                "isSynced": { "$ne": True }
            }

            cursor = collection.find(query)
            async for doc in cursor:
                yield doc
        except ConnectionError:
            # Re-raise connection errors to be handled at a higher level
            raise
        except PyMongoError:
            logger.error("Database error while fetching unsynced workorders")
            return


    async def mark_workorder_as_synced(self, workorder_number: int) -> bool:
        """Mark a workorder as synced."""
        try:
            database = await get_connection()
            collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

            query = { "number": workorder_number }
            values = { "$set": { "isSynced": True, "syncedAt": datetime.now(timezone.utc) }}

            result = await collection.update_one(query, values)
            success = result.modified_count > 0

            if success:
                logger.debug(f"Marked workorder {workorder_number} as synced")
            else:
                logger.warning(f"Workorder {workorder_number} was not marked as synced")

            return success
        except ConnectionError:
            # Re-raise connection errors to be handled at a higher level
            raise
        except PyMongoError:
            logger.error(f"Database error while marking workorder {workorder_number} as synced")
            return False
