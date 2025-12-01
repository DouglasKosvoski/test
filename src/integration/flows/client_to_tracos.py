from loguru import logger  # pyright: ignore[reportMissingImports]
from pathlib import Path
from integration.system.client.repository import ClientRepository
from integration.system.tracos.repository import TracOSRepository
from integration.translators.client_to_tracos import translate_client_to_tracos


class ClientToTracOSFlow:
    def __init__(self):
        logger.info("ClientToTracOSFlow module initialized")

        self.client_repository = ClientRepository()
        self.tracos_repository = TracOSRepository()

    async def sync(self, directory_path: Path):
        logger.info("Syncing Client data with TracOS...")

        workorders = self.client_repository.find_workorders(str(directory_path))

        logger.info(f"Found {len(workorders)} workorders in '{directory_path}'")

        for workorder in workorders:
            validated_workorder = self.client_repository.validate_workorder(workorder)
            translated_workorder = translate_client_to_tracos(validated_workorder)

            await self.tracos_repository.save_workorder(translated_workorder)
