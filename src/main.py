"""Entrypoint for the application."""

import asyncio
from loguru import logger
from integration.inbound.InboundHandler import InboundHandler
from integration.outbound.OutboundHandler import OutboundHandler
from os import getenv
from pathlib import Path


INBOUND_DATA_DIR = Path(getenv("INBOUND_DATA_DIR"))
OUTBOUND_DATA_DIR = Path(getenv("OUTBOUND_DATA_DIR"))


async def main():
    logger.info("Starting TracOS ↔ Client Integration Flow")

    inbound_handler = InboundHandler()
    inbound_handler.sync_with_tracOS(INBOUND_DATA_DIR)

    outbound_handler = OutboundHandler()
    await outbound_handler.sync_with_client(OUTBOUND_DATA_DIR)

    logger.info("Finished integration!")


if __name__ == "__main__":
    asyncio.run(main())
