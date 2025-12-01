"""Entrypoint for the application."""

import asyncio
from loguru import logger
from integration.flows.client_to_tracos import ClientToTracOSFlow
from integration.flows.tracos_to_client import TracOSToClientFlow
from os import getenv
from pathlib import Path


INBOUND_DATA_DIR = Path(getenv("INBOUND_DATA_DIR"))
OUTBOUND_DATA_DIR = Path(getenv("OUTBOUND_DATA_DIR"))


async def main():
    logger.info("Starting TracOS ↔ Client Integration Flow")

    # Sync client data to TracOS
    client_to_tracos_flow = ClientToTracOSFlow()
    await client_to_tracos_flow.sync(INBOUND_DATA_DIR)

    # Sync TracOS data to client
    tracos_to_client_flow = TracOSToClientFlow()
    await tracos_to_client_flow.sync(OUTBOUND_DATA_DIR)

    logger.info("Finished integration!")


if __name__ == "__main__":
    asyncio.run(main())
