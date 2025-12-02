"""
TracOS to Client synchronization flow.

Orchestrates the synchronization of workorders from the TracOS MongoDB database
to the Client file system. Fetches unsynced workorders from the database,
translates them to Client format and exports as JSON files to an outbound directory.
"""

from loguru import logger  # pyright: ignore[reportMissingImports]
from pathlib import Path
from integration.system.tracos.repository import TracOSRepository
from integration.translators.tracos_to_client import translate_tracos_to_client
from adapters.filesystem import write_json_to_file
import os


class TracOSToClientFlow:
    def __init__(self):
        self.tracos_repository = TracOSRepository()

    def validate_workorder(self, workorder: dict) -> bool:
        """Validate a TracOS workorder."""
        return self.tracos_repository.validate_workorder(workorder)

    async def sync(self, directory_path: Path):
        logger.info("Syncing TracOS data with Client...")

        # Ensure output directory exists
        try:
            os.makedirs(directory_path, exist_ok=True)
        except PermissionError:
            logger.error(f"Permission denied creating output directory: '{directory_path}'")
            return
        except OSError:
            logger.error(f"Failed to create output directory: '{directory_path}'")
            return

        workorder_count = 0
        async for workorder in self.tracos_repository.find_all_unsynced_workorders():
            workorder_number = workorder.get("number", "unknown")

            if not self.validate_workorder(workorder):
                logger.warning(f"Workorder {workorder_number} is not valid")
                continue

            try:
                translated_workorder = translate_tracos_to_client(workorder)

                filename = f"{translated_workorder['orderNo']}.json"
                filepath = directory_path / filename

                write_json_to_file(str(filepath), translated_workorder)

                await self.tracos_repository.mark_workorder_as_synced(workorder["number"])

                workorder_count += 1
                logger.debug(f"Exported workorder {translated_workorder['orderNo']} to {filepath}")
            except PermissionError:
                logger.error(f"Permission denied writing workorder {workorder_number}")
                continue
            except OSError:
                logger.error(f"Failed to write workorder {workorder_number}")
                continue
            except Exception:
                logger.error(f"Failed to process workorder {workorder_number}")
                continue
