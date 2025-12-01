from loguru import logger  # pyright: ignore[reportMissingImports]
from pathlib import Path
from integration.system.tracos.repository import TracOSRepository
from integration.translators.tracos_to_client import translate_tracos_to_client
from adapters.filesystem import write_json_to_file
import os


class TracOSToClientFlow:
    def __init__(self):
        self.tracos_repository = TracOSRepository()


    async def sync(self, directory_path: Path):
        logger.info("Syncing TracOS data with Client...")

        # Ensure output directory exists
        os.makedirs(directory_path, exist_ok=True)

        workorder_count = 0
        async for workorder in self.tracos_repository.find_all_unsynced_workorders():
            if not self.validate_workorder(workorder):
                logger.warning(f"Workorder {workorder['number']} is not valid")
                continue

            translated_workorder = translate_tracos_to_client(workorder)

            filename = f"{translated_workorder['orderNo']}.json"
            filepath = directory_path / filename

            write_json_to_file(str(filepath), translated_workorder)

            await self.tracos_repository.mark_workorder_as_synced(workorder['number'])

            workorder_count += 1
            logger.info(f"Exported workorder {translated_workorder['orderNo']} to {filepath}")

        logger.success(f"Exported {workorder_count} workorders to '{directory_path}'")


    def validate_workorder(self, workorder: dict) -> bool:
        """
        Validate a workorder from TracOS format.

        Expected format:
        {
            '_id': ObjectId('692cf6d50b12b168f2f7cc18'),
            'number': 1,
            'status': 'completed',
            'title': 'Example workorder #1',
            'description': 'Example workorder #1 description',
            'createdAt': datetime.datetime(2025, 11, 2, 2, 0, 53, 670000),
            'updatedAt': datetime.datetime(2025, 11, 2, 3, 0, 53, 670000),
            'deleted': False
        }
        """
        required_fields = ['number', 'status', 'title', 'description', 'createdAt', 'updatedAt', 'deleted']

        for field in required_fields:
            if field in workorder and workorder[field] is not None:
                continue

            logger.warning(f"Workorder missing required field: {field}")

            return False

        return True
