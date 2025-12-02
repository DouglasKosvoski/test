#!/usr/bin/env python3

"""Entrypoint for the application."""

import sys
import asyncio
from loguru import logger
from integration.flows.client_to_tracos import ClientToTracOSFlow
from integration.flows.tracos_to_client import TracOSToClientFlow
from os import getenv
from pathlib import Path


DATA_INBOUND_DIR = Path(getenv("DATA_INBOUND_DIR", "data/inbound"))
DATA_OUTBOUND_DIR = Path(getenv("DATA_OUTBOUND_DIR", "data/outbound"))
LOG_LEVEL = getenv("LOG_LEVEL", "DEBUG")


def setup_logger():
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level=LOG_LEVEL,
        format="{time:HH:mm:ss} | {level} | {message}",
    )


async def main():
    setup_logger()

    logger.success("Starting TracOS <=> Client Integration Flow")

    try:
        # Sync client data to TracOS
        client_to_tracos_flow = ClientToTracOSFlow()
        await client_to_tracos_flow.sync(DATA_INBOUND_DIR)
        logger.success("Client data synced to TracOS")
        logger.debug("--------------------------------")

        # Sync TracOS data to client
        tracos_to_client_flow = TracOSToClientFlow()
        await tracos_to_client_flow.sync(DATA_OUTBOUND_DIR)
        logger.success("TracOS data synced to Client")
        logger.debug("--------------------------------")

        logger.success("Integration flow completed successfully")
    except ConnectionError:
        logger.error("Unable to connect to the database. Please check your connection settings.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Integration interrupted by user")
        sys.exit(0)
    except Exception:
        logger.error("An unexpected error occurred during integration")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
