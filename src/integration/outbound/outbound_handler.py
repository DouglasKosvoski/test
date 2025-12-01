from os import getenv
from typing import AsyncGenerator
from loguru import logger
from helpers.db import get_connection, get_collection
from pathlib import Path


class OutboundHandler:
    def __init__(self):
        logger.info("OutboundHandler module initialized")


    async def sync_with_client(self, directory_path: Path):
        logger.info(f"Syncing Outbound data with client...")

        self.database = await get_connection()

        async for workorder in self.find_workorders_streamed():
            logger.debug(workorder)


    async def find_workorders_streamed(self) -> AsyncGenerator[dict, None]:
        collection = get_collection(self.database, getenv("MONGO_COLLECTION"))

        cursor = collection.find({})

        async for doc in cursor:
            yield doc


    def validate_workorder(self, workorder: dict) -> bool:
        # {
        #     '_id': ObjectId('692cf6d50b12b168f2f7cc18'),
        #     'number': 1,
        #     'status': 'completed',
        #     'title': 'Example workorder #1',
        #     'description': 'Example workorder #1 description',
        #     'createdAt': datetime.datetime(2025, 11, 2, 2, 0, 53, 670000),
        #     'updatedAt': datetime.datetime(2025, 11, 2, 3, 0, 53, 670000),
        #     'deleted': False
        # }

        return True