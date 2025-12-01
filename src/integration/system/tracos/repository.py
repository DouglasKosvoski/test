# CRUD operations on TracOS (MongoDB)
from loguru import logger  # pyright: ignore[reportMissingImports]
from typing import AsyncGenerator, List, Optional
from adapters.db import get_connection, get_collection
from os import getenv


class TracOSRepository:
    def __init__(self):
        pass

    async def save_workorder(self, workorder: dict) -> None:
        """Save a workorder to the database."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        # Check if workorder with this number already exists
        existing = await collection.find_one({"number": workorder.get("number")})
        if existing:
            # Update existing workorder, preserving the _id
            workorder_copy = workorder.copy()
            workorder_copy.pop("_id", None)  # Remove _id if present to preserve existing one
            result = await collection.update_one(
                {"number": workorder.get("number")},
                {"$set": workorder_copy}
            )
            logger.debug(f"Updated workorder with number {workorder.get('number')} (ID: {existing.get('_id')})")
            return

        # Insert the workorder
        result = await collection.insert_one(workorder)
        logger.debug(f"Saved workorder with ID: {result.inserted_id}")

    async def find_workorder_by_id(self, workorder_id: str) -> Optional[dict]:
        """Find a workorder by its ID."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        return await collection.find_one({"_id": workorder_id})

    async def find_all_workorders(self) -> AsyncGenerator[dict, None]:
        """Find all workorders in the database."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        cursor = collection.find({})
        async for doc in cursor:
            yield doc

    async def update_workorder(self, workorder_id: str, updates: dict) -> bool:
        """Update a workorder with the given updates."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        result = await collection.update_one({"_id": workorder_id}, {"$set": updates})

        success = result.modified_count > 0
        if success:
            logger.debug(f"Updated workorder {workorder_id}")
        return success

    async def delete_workorder(self, workorder_id: str) -> bool:
        """Delete a workorder by its ID."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION", "workorders"))

        result = await collection.delete_one({"_id": workorder_id})

        success = result.deleted_count > 0
        if success:
            logger.debug(f"Deleted workorder {workorder_id}")

        return success
