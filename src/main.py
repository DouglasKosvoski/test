#!/usr/bin/env python3

"""Entrypoint for the application."""

import asyncio
from loguru import logger
from integration.flows.client_to_tracos import ClientToTracOSFlow
from integration.flows.tracos_to_client import TracOSToClientFlow
from os import getenv
from pathlib import Path


INBOUND_DATA_DIR = Path(getenv("INBOUND_DATA_DIR", "data/inbound"))
OUTBOUND_DATA_DIR = Path(getenv("OUTBOUND_DATA_DIR", "data/outbound"))
LOG_LEVEL = getenv("LOG_LEVEL", "DEBUG")

def setup_logger():
    logger.remove() # Remove default handler
    logger.add(lambda msg: print(msg, end=""), level=LOG_LEVEL, format="{time:HH:mm:ss} | {level} | {message}")


async def main():
    setup_logger()

    logger.success("Starting TracOS ↔ Client Integration Flow")

    # Sync client data to TracOS
    client_to_tracos_flow = ClientToTracOSFlow()
    await client_to_tracos_flow.sync(INBOUND_DATA_DIR)

    # Sync TracOS data to client
    # tracos_to_client_flow = TracOSToClientFlow()
    # await tracos_to_client_flow.sync(OUTBOUND_DATA_DIR)

    logger.success("Finished integration!")


if __name__ == "__main__":
    asyncio.run(main())
