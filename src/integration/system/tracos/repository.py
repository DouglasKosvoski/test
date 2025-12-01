# CRUD operations on TracOS (MongoDB)
from loguru import logger  # pyright: ignore[reportMissingImports]
from typing import AsyncGenerator, List, Optional
from adapters.db import get_connection, get_collection
from os import getenv
from datetime import datetime


class TracOSRepository:
    def __init__(self):
        pass

    async def save_workorder(self, workorder: dict) -> bool:
        """Save a workorder to the database."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        # Check if workorder with this number already exists
        existing = await collection.find_one({"number": workorder.get("number")})
        if existing:
            should_update = self.should_update_workorder(existing, workorder)
            if not should_update:
                logger.debug(f"Workorder with number {workorder.get('number')} already exists and no changes to update")
                return True

            # Update existing workorder, preserving the _id
            updated_workorder = {
                **existing,
                **workorder
            }

            result = await collection.update_one(
                {"number": workorder.get("number")},
                {"$set": updated_workorder}
            )

            logger.debug(f"Updated workorder with number {workorder.get('number')} (ID: {existing.get('_id')})")
            return True

        # Insert the workorder
        result = await collection.insert_one(workorder)
        logger.debug(f"Saved workorder with ID: {result.inserted_id}")

        return True

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


    async def find_all_unsynced_workorders(self) -> AsyncGenerator[dict, None]:
        """Find all unsynced workorders in the database."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        query = {
            "isSynced": { "$ne": True }
        }

        cursor = collection.find(query)
        async for doc in cursor:
            yield doc


    async def mark_workorder_as_synced(self, workorder_number: int) -> bool:
        """Mark a workorder as synced."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        query = { "number": workorder_number }
        values = { "$set": { "isSynced": True, "syncedAt": datetime.now() }}

        result = await collection.update_one(query, values)
        success = result.modified_count > 0

        if success:
            logger.debug(f"Marked workorder {workorder_number} as synced")
        else:
            logger.warning(f"Failed to mark workorder {workorder_number} as synced")

        return success
