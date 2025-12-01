# CRUD operations on TracOS (MongoDB)
from loguru import logger  # pyright: ignore[reportMissingImports]
from typing import AsyncGenerator, List, Optional
from adapters.db import get_connection, get_collection
from os import getenv


class TracOSRepository:
    def __init__(self):
        logger.info("TracOSRepository module initialized")

    async def save_workorder(self, workorder: dict) -> None:
        """Save a workorder to the database."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION"))

        # Insert the workorder
        result = await collection.insert_one(workorder)
        logger.info(f"Saved workorder with ID: {result.inserted_id}")

    async def find_workorder_by_id(self, workorder_id: str) -> Optional[dict]:
        """Find a workorder by its ID."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION"))

        return await collection.find_one({"_id": workorder_id})

    async def find_all_workorders(self) -> AsyncGenerator[dict, None]:
        """Find all workorders in the database."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION"))

        cursor = collection.find({})
        async for doc in cursor:
            yield doc

    async def update_workorder(self, workorder_id: str, updates: dict) -> bool:
        """Update a workorder with the given updates."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION"))

        result = await collection.update_one({"_id": workorder_id}, {"$set": updates})

        success = result.modified_count > 0
        if success:
            logger.info(f"Updated workorder {workorder_id}")
        return success

    async def delete_workorder(self, workorder_id: str) -> bool:
        """Delete a workorder by its ID."""
        database = await get_connection()
        collection = get_collection(database, getenv("MONGO_COLLECTION"))

        result = await collection.delete_one({"_id": workorder_id})

        success = result.deleted_count > 0
        if success:
            logger.info(f"Deleted workorder {workorder_id}")

        return success
