import asyncio
from os import getenv

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


async def get_connection() -> AsyncIOMotorDatabase:
    DATABASE_DRIVER = getenv("DATABASE_DRIVER", "mongodb")

    if DATABASE_DRIVER is None:
        raise ValueError("DATABASE_DRIVER is not set")

    if DATABASE_DRIVER == "mongodb":
        return await get_mongodb_connection_with_retry()
    else:
        raise ValueError(f"Unsupported database driver: {DATABASE_DRIVER}")


async def get_mongodb_connection() -> AsyncIOMotorDatabase:
    MONGO_URI = getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DATABASE = getenv("MONGO_DATABASE", "tractian")

    if MONGO_URI is None:
        raise ValueError("MONGO_URI is not set")

    if MONGO_DATABASE is None:
        raise ValueError("MONGO_DATABASE is not set")

    client = AsyncIOMotorClient(MONGO_URI)

    if client is None:
        raise ValueError("Failed to connect to MongoDB")

    database = client[MONGO_DATABASE]

    if database is None:
        raise ValueError("Failed to connect to MongoDB")

    return database


async def get_mongodb_connection_with_retry() -> AsyncIOMotorDatabase:
    """Get MongoDB connection with retry logic."""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            database = await get_mongodb_connection()
            # Verify connection
            await database.command("ping")
            return database
        except Exception:
            logger.warning(f"MongoDB connection attempt {attempt}/{MAX_RETRIES} failed")

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)

    raise ConnectionError(f"Failed to connect to MongoDB after {MAX_RETRIES} attempts")


def get_collection(database: AsyncIOMotorDatabase, collection_name: str) -> AsyncIOMotorCollection:
    if database is None:
        raise ValueError("database is not set")

    if collection_name is None:
        raise ValueError("collection_name is not set")

    collection = database[collection_name]

    if collection is None:
        raise ValueError("Failed to get collection")

    return collection