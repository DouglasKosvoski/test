from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection


async def get_connection() -> AsyncIOMotorDatabase:
    DATABASE_DRIVER = getenv("DATABASE_DRIVER")

    if DATABASE_DRIVER is None:
        raise ValueError("DATABASE_DRIVER is not set")

    if DATABASE_DRIVER == "mongodb":
        return await get_mongodb_connection()
    else:
        raise ValueError(f"Unsupported database driver: {DATABASE_DRIVER}")


async def get_mongodb_connection() -> AsyncIOMotorDatabase:
    MONGO_URI = getenv("MONGO_URI")
    MONGO_DATABASE = getenv("MONGO_DATABASE")

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


def get_collection(database: AsyncIOMotorDatabase, collection_name: str) -> AsyncIOMotorCollection:
    if database is None:
        raise ValueError("database is not set")

    if collection_name is None:
        raise ValueError("collection_name is not set")

    collection = database[collection_name]

    if collection is None:
        raise ValueError("Failed to get collection")

    return collection